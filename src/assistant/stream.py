"""The assistant's turn as it happens (FEAT-40, OWN-GW-06…10): each event of the run, said once, for the workspace
to draw — a tool starting (the graph nodes it reads), a tool ending (ok or not, how long, what its result names),
the answer's text as the model writes it, a write waiting for the person, then the answer itself.

Nothing here is invented: a ``step`` is an operonx-agents ``ToolCallStarted`` / ``ToolCallFinished`` (or, on the
fallback path, our own call of the one tool the keyword router chose); ``focus`` is what the tool's result names;
``text`` is the model's own delta, sent only when the model may read client data (in template mode its words are not
the answer). The graph lights a node only for these."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from operonx_agents.run.events import (
    ApprovalRequired,
    TextDelta,
    ToolCallFinished,
    ToolCallStarted,
    TurnFinished,
    TurnStarted,
)

from assistant import progress, registry
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
    "lien_ket": [],
    "so_sanh_kich_ban": ["scenario"],
    "gia_dinh": ["scenario"],
    # a staff desk's elements (data-node, FEAT-41): the CIO's pipeline stages and panels
    "hop_tin": ["stage:news"],
    "lay_tin": ["stage:news"],
    "su_kien": ["stage:events", "events"],
    "danh_dau_khan": ["stage:events"],
    "ban_quyet_dinh": ["decide", "stage:views", "stage:runs"],
    "phoi_nhiem": ["exposure", "stage:families"],
    "lan_ap_dung": ["stage:runs"],
    "do_chinh_xac": ["model"],
    # the RM's book: the map, the call list, goal tasks, proposals, contacts
    "so_khach_hang": ["book", "calls", "proposals"],
    "hom_nay": ["calls", "tasks"],
    "de_xuat": ["proposals", "queue"],  # the RM's proposals; the Expert's queue
    "lien_he": ["contacts"],
    "ghi_lien_he": ["contacts"],
    # Admin's operations map; the chain and configuration (Compliance's desk too)
    "van_hanh": ["ops", "alerts", "jobs"],
    "canh_bao_he_thong": ["alerts"],
    "chuoi_nhat_ky": ["chain", "node:chain"],
    "cau_hinh_cho_duyet": ["config", "node:config"],
    # the Expert's queue and the family's picture beside it
    "ban_chuyen_gia": ["queue"],
    "chuyen_gia_duyet": ["queue"],
    "ho_so_khach": ["evidence"],
}


def nodes_for(tool: str, args: Optional[Dict[str, Any]], graph: Optional[Dict[str, Any]] = None) -> List[str]:
    """The graph nodes a call reads: the stress test its one scenario; the links tool the node (both ends of an edge)
    it reads, else what is picked; the comparison its scenarios, else the active ones (F10)."""
    graph = graph or {}
    if tool == "lien_ket":
        target = str((args or {}).get("node") or (graph.get("selected") or {}).get("id") or "")
        return [x for x in target.split(">") if x and x != "ME"] if target else []
    if tool == "so_sanh_kich_ban":
        from assistant.graphtools import COMPARE

        ids = [COMPARE[w] for w in (args or {}).get("scenarios") or [] if w in COMPARE] or graph.get("active") or []
        return [f"SC:{s}" for s in ids] or NODES[tool]
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


class Clock:
    """A turn's time, without its words (the latency report, 2026-10-18; the assistant's traces are off because its
    ops hold what people say). Milliseconds: ``start`` the first model call, from the turn's start; ``calls`` each
    model call as [its first output, its end] from the call's start (the end: its tool calls begin, or its answer is
    written); ``tools`` the tools' own time; ``first_text`` the first words the person sees, from the turn's start
    (a model that writes before its tool call shows them early); ``total`` the turn."""

    def __init__(self) -> None:
        self.t0 = time.monotonic()
        self.start: Optional[float] = None
        self.calls: List[List[Optional[float]]] = []
        self.tools = 0.0
        self.first_text: Optional[float] = None
        self._call: Optional[List[Optional[float]]] = None  # [its start, its first output]

    def _now(self) -> float:
        return (time.monotonic() - self.t0) * 1000

    def _close(self) -> None:
        if self._call is not None:
            began, first = self._call
            self.calls.append([None if first is None else first - began, self._now() - began])
            self._call = None

    def see(self, ev: Any) -> None:
        if isinstance(ev, TurnStarted):
            self._close()
            self._call = [self._now(), None]
            self.start = self._call[0] if self.start is None else self.start
            return
        words = isinstance(ev, TextDelta) and bool(ev.text)
        if (words or isinstance(ev, ToolCallStarted)) and self._call is not None and self._call[1] is None:
            self._call[1] = self._now()
        if words and self.first_text is None:
            self.first_text = self._now()
        if isinstance(ev, (ToolCallStarted, TurnFinished)):
            self._close()
        if isinstance(ev, ToolCallFinished):
            self.tools += ev.ms or 0

    def summary(self) -> Dict[str, Any]:
        self._close()

        def r(v: Optional[float]) -> Optional[int]:
            return None if v is None else round(v)

        return {"start": r(self.start), "calls": [[r(a), r(b)] for a, b in self.calls], "tools": round(self.tools),
                "first_text": r(self.first_text), "total": round(self._now())}  # fmt: skip


def translate(ev: Any, ctx: Ctx) -> Optional[Dict[str, Any]]:
    """One agent event → one stream event (or None: not something the person sees)."""
    if isinstance(ev, ToolCallStarted):
        nodes = nodes_for(ev.tool, ev.args, ctx.graph)
        return {"type": "step", "phase": "start", "call_id": ev.call_id, "tool": ev.tool,
                "label": registry.LABELS.get(ev.tool, ev.tool), "nodes": nodes,
                **progress.says(ev.tool, ev.args)}  # fmt: skip
    if isinstance(ev, ToolCallFinished):
        queue = ctx.trail.get(ev.call_id) or []
        return step_end(ev.tool, ev.call_id, ev.ok, ev.ms, queue[-1] if queue else None)
    if isinstance(ev, TextDelta):
        return {"type": "text", "text": ev.text} if ctx.reads and ev.text else None
    if isinstance(ev, ApprovalRequired):
        return {"type": "wait", "call_id": ev.call_id, "tool": ev.tool, "label": registry.LABELS.get(ev.tool, ev.tool)}
    return None
