"""The assistant's tool registry (A1, ADR-0032): one record per capability — the Copilot's thirteen and the served
graphs wrapped since — each with its roles, kind, arguments, a plan and a verifier for writes, a timeout and a cost
class. ``agent_tools(role)`` turns the role's share into ``operonx_agents`` tools: a tool the role may not use is
never offered, so it cannot be called; a write asks the person first (``approval="always"``) and is read back after
(``verify=``); the person is ``RunContext.deps`` (a :class:`Ctx`)."""

from __future__ import annotations

import functools
import inspect
from typing import Any, Dict, List, Literal, Optional

import pydantic
from operonx_agents import RunContext
from operonx_agents import tool as agent_tool

from assistant import actions, tools
from assistant.base import Ctx, Tool, allowed

REGISTRY: Dict[str, Tool] = {**tools.CATALOGUE}
for _name, _t in actions.CATALOGUE.items():
    assert _name not in REGISTRY, f"two tools named {_name!r}"
    REGISTRY[_name] = _t
DEMO_USER = {**tools.USER, "admin": "admin", "specialist": "sp_global"}  # who acts when sign-in is off


def for_role(role: str) -> List[Tool]:
    return [t for t in REGISTRY.values() if role in t.roles]


async def plan(tool: Tool, ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """A write's plan: {"summary": the line the person confirms, "args": the arguments resolved on the server}."""
    allowed(tool, ctx.role)
    out = tool.plan(ctx, args)
    return await out if inspect.isawaitable(out) else out


class Seen(pydantic.BaseModel):
    """What the model reads of a tool's result. With ``ctx.reads`` off (the barrier's ``client_ai = off``) only
    the status, the tool and the page: the answer is then the tools' own texts, not the model's (ADR-0026)."""

    status: str
    tool: str
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    as_of: Optional[str] = None
    sources: Optional[List[str]] = None
    page: Optional[str] = None
    _out: Dict[str, Any] = pydantic.PrivateAttr(default_factory=dict)

    def model_dump_json(self, **kw) -> str:
        kw.setdefault("exclude_none", True)
        return super().model_dump_json(**kw)


def _seen(tool: Tool, ctx: Ctx, out: Dict[str, Any]) -> Seen:
    page = tools.PAGES.get(tool.page or "")
    link = page and page[1].get(ctx.role)
    if ctx.reads:
        s = Seen(
            status="ok",
            tool=tool.name,
            text=out.get("text"),
            data=out.get("data"),
            as_of=out.get("as_of"),
            sources=[x for x in out.get("sources") or [] if x] or None,
            page=link or None,
        )
    else:
        s = Seen(status="ok", tool=tool.name, page=link or None)
    s._out = out
    return s


def _signature(tool: Tool):
    """The tool's arguments as a Python signature (RunContext first), so operonx-agents types and validates them:
    enumerations as ``Literal`` (optional: the tool has a default), free arguments as declared."""
    required, optional, docs = [], [], []
    hints: Dict[str, Any] = {"rctx": RunContext}
    for name, choices in tool.args.items():
        hints[name] = Optional[Literal[tuple(choices)]]
        optional.append(inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, default=None))
        docs.append(f"    {name}: một trong {', '.join(choices)}")
    for name, p in tool.params.items():
        hints[name] = p.type
        if p.default is ...:
            required.append(inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY))
        else:
            optional.append(inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, default=p.default))
        docs.append(f"    {name}: {p.description}")
    first = inspect.Parameter("rctx", inspect.Parameter.POSITIONAL_OR_KEYWORD)
    doc = tool.description + ("\n\nArgs:\n" + "\n".join(docs) if docs else "")
    return inspect.Signature([first, *required, *optional]), hints, doc


def _agent_tool(tool: Tool):
    async def call(rctx: RunContext, **kwargs) -> Seen:
        ctx: Ctx = rctx.deps
        allowed(tool, ctx.role)  # the role's toolset holds only its tools; checked again on the person given
        args = {k: v for k, v in kwargs.items() if v is not None}
        if tool.write:
            args = (await plan(tool, ctx, args))["args"]
        return _seen(tool, ctx, await tool.run(ctx, args))

    def verify(rctx: RunContext, args: Dict[str, Any], result: Seen):
        return tool.verify(rctx.deps, result._out)

    call.__signature__, call.__annotations__, call.__doc__ = _signature(tool)
    call.__name__ = call.__qualname__ = tool.name
    return agent_tool(
        call,
        approval="always" if tool.write else "never",
        idempotent=not tool.write,
        readonly=not tool.write,
        timeout=tool.timeout,
        verify=verify if tool.verify else None,
    )


@functools.lru_cache(maxsize=None)
def agent_tools(role: str) -> tuple:
    """The role's tools for an operonx-agents ``Agent``; the person rides in ``RunContext.deps``."""
    return tuple(_agent_tool(t) for t in for_role(role))
