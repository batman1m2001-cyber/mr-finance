"""The assistant's tool record (ADR-0032): what a capability is, who may use it, how a write is confirmed and
checked. The tools themselves are in ``assistant.tools`` (the Copilot's thirteen) and ``assistant.actions`` (the
served graphs wrapped since A1); ``assistant.registry`` puts them together."""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from operonx import Operon

from control import roles

KINDS = ("read", "write", "external", "memory")
COSTS = ("free", "llm", "paid")  # paid: counts against a daily cap (web search, the CIO agent)


class ToolFailed(RuntimeError):
    """The tool ran and did not succeed: said as such, never as a success."""


class NotConfirmed(ToolFailed):
    """A write answered, but reading the state back did not find its effect."""

    def __init__(self, reason: str):
        super().__init__(f"Đã gửi nhưng chưa xác nhận được kết quả: {reason}")
        self.reason = reason


@dataclass
class Ctx:
    role: str
    client_id: Optional[str]
    scope: str
    question: str  # the original question: read only by our code (month parsing), never sent to a model
    followed: Optional[List[str]] = None  # goal ids the client follows in this browser (None: the persona's)
    user: Optional[str] = None  # who acts: the person signed in, else the role's demo user; writes name them
    reads: bool = True  # the model may read tool results (the barrier's client_ai allows it; ADR-0026)
    route: str = ""  # the page asked from (its sections only reach the model)
    conversation: str = ""  # the conversation the turn is in (A3): what a memory item names as its source
    remembered: List[str] = field(default_factory=list)  # the person's active memory items (A4), for the prompt
    trail: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)  # this request's tool results, by call id
    asked: set = field(default_factory=set)  # call ids of the writes a resumed request answers
    graph: Dict[str, Any] = field(default_factory=dict)  # the workspace: lens, what is picked, active scenarios (F10)


@dataclass
class Param:
    """A free argument the model fills: typed and bounded by the tool, never a path, a query language or a URL."""

    type: Any
    description: str
    default: Any = ...  # ... : required


Run = Callable[[Ctx, Dict[str, Any]], Awaitable[Dict[str, Any]]]
Plan = Callable[[Ctx, Dict[str, Any]], Dict[str, Any]]  # → {"summary": what the person confirms, "args": resolved}
Verify = Callable[[Ctx, Dict[str, Any]], Any]  # (ctx, the run's output) → True, or what is not there


@dataclass
class Tool:
    name: str
    description: str  # what the model reads: no data, no digits
    roles: tuple
    run: Run
    write: bool = False
    args: Dict[str, List[str]] = field(default_factory=dict)  # enumerations the model chooses from
    page: Optional[str] = None
    follow: List[str] = field(default_factory=list)
    params: Dict[str, Param] = field(default_factory=dict)  # free, typed arguments (see Param)
    plan: Optional[Plan] = None  # writes: the one line the person confirms, and the server-resolved arguments
    verify: Optional[Verify] = None  # writes: the state read back after the call
    timeout: float = 30.0
    cost: str = "free"
    kind: str = "read"

    def __post_init__(self):
        if self.write:
            self.kind = "write"
        if self.kind not in KINDS or self.cost not in COSTS:
            raise ValueError(f"{self.name}: kind {self.kind!r} / cost {self.cost!r}")
        if self.kind == "write" and not (self.plan and self.verify):
            raise ValueError(f"{self.name}: a write needs a plan (what is confirmed) and a verifier (read back)")


def allowed(tool: Tool, role: str) -> None:
    if role not in tool.roles:
        names = ", ".join(roles.ROLE_LABELS[r] for r in tool.roles)
        raise roles.Forbidden(f"Vai trò {roles.ROLE_LABELS.get(role, role)} không dùng được việc này; cần: {names}")


async def run_graph(graph, **inputs) -> Dict[str, Any]:
    """A served graph run with the person's request around it: its role, family and duty checks apply."""
    out = await Operon(graph, params={k: None for k in inputs}).run(inputs=inputs)
    if "$errors" in out:
        err = next(iter(out["$errors"].values()))
        raise ToolFailed(str(err.get("message") or err.get("type") or err))
    return out


async def checked(tool: Tool, ctx: Ctx, out: Dict[str, Any]) -> None:
    """The write's verifier on its output; NotConfirmed unless it answers True. A verifier that fails or forgets
    to answer confirms nothing."""
    try:
        verdict = tool.verify(ctx, out)
        if inspect.isawaitable(verdict):
            verdict = await asyncio.wait_for(verdict, tool.timeout)
    except Exception as exc:  # noqa: BLE001 - a check that fails confirms nothing
        raise NotConfirmed(f"không đọc lại được ({type(exc).__name__}: {exc})") from exc
    if verdict is not True:
        raise NotConfirmed(verdict if isinstance(verdict, str) and verdict else "không thấy thay đổi")


async def execute(tool: Tool, ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Run a tool (a write: already confirmed, its arguments the plan's) within its timeout, then verify a write."""
    try:
        out = await asyncio.wait_for(tool.run(ctx, args), tool.timeout)
    except asyncio.TimeoutError:
        raise ToolFailed(f"quá {tool.timeout:.0f} giây chưa xong") from None
    if tool.verify is not None:
        await checked(tool, ctx, out)
    return out
