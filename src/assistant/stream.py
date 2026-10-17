"""The assistant's turn as it happens (FEAT-40, OWN-GW-06…10): each event of the run, said once, for the workspace
to draw — a tool starting (the graph nodes it reads), a tool ending (ok or not, how long, what its result names),
the answer's text as the model writes it, a write waiting for the person, then the answer itself.

Nothing here is invented: a ``step`` is an operonx-agents ``ToolCallStarted`` / ``ToolCallFinished`` (or, on the
fallback path, our own call of the one tool the keyword router chose); ``focus`` is what the tool's result names;
``text`` is the model's own delta, sent only when the model may read client data (in template mode its words are not
the answer). The graph lights a node only for these."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from operonx_agents.run.events import ApprovalRequired, TextDelta, ToolCallFinished, ToolCallStarted

from assistant import registry
from assistant.base import Ctx

# what each tool reads, as graph node ids (``ME``, ``FL:in``…) or kinds (``goal``, ``event``…): where its work shows
NODES: Dict[str, List[str]] = {
    "tong_quan": ["ME", "class", "LQ:reserve", "RK:drawdown"],
    "dong_tien": ["FL:in", "FL:out"],
    "chu_y": ["alert", "event", "risk"],
    "muc_tieu": ["goal"],
    "tac_dong": ["event"],
    "dieu_tra": ["event"],
    "kich_ban": ["scenario"],
    "dong_luc": ["alert"],
}


def nodes_for(tool: str, args: Optional[Dict[str, Any]]) -> List[str]:
    """The graph nodes a call reads; the stress test names its one scenario."""
    if tool == "kich_ban":
        from assistant.tools import STRESS

        sid = STRESS.get((args or {}).get("scenario"))
        return [f"SC:{sid}"] if sid else NODES["kich_ban"]
    return list(NODES.get(tool, []))


def _keys(focus: Any) -> List[str]:
    return [focus] if isinstance(focus, str) else [k for k in focus or [] if isinstance(k, str)]


def step_end(tool: str, call_id: str, ok: bool, ms: float, got: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """A call ended: what its result names lights on the graph; a stress test's effect goes on its scenario node."""
    got = got or {}
    out: Dict[str, Any] = {"type": "step", "phase": "end", "call_id": call_id, "tool": tool, "ok": ok,
                           "ms": round(ms or 0), "focus": _keys(got.get("focus")) if ok else []}  # fmt: skip
    data = got.get("data") or {}
    if (
        ok
        and tool == "kich_ban"
        and isinstance(data.get("before"), (int, float))
        and isinstance(data.get("after"), (int, float))
    ):
        out["scenario"] = {"id": data["scenario"], "effect": data["after"] - data["before"]}
        out["focus"].append(f"scenario:{data['scenario']}")
    return out


def translate(ev: Any, ctx: Ctx) -> Optional[Dict[str, Any]]:
    """One agent event → one stream event (or None: not something the person sees)."""
    if isinstance(ev, ToolCallStarted):
        return {"type": "step", "phase": "start", "call_id": ev.call_id, "tool": ev.tool,
                "label": registry.LABELS.get(ev.tool, ev.tool), "nodes": nodes_for(ev.tool, ev.args)}  # fmt: skip
    if isinstance(ev, ToolCallFinished):
        queue = ctx.trail.get(ev.call_id) or []
        return step_end(ev.tool, ev.call_id, ev.ok, ev.ms, queue[-1] if queue else None)
    if isinstance(ev, TextDelta):
        return {"type": "text", "text": ev.text} if ctx.reads and ev.text else None
    if isinstance(ev, ApprovalRequired):
        return {"type": "wait", "call_id": ev.call_id, "tool": ev.tool, "label": registry.LABELS.get(ev.tool, ev.tool)}
    return None
