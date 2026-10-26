"""The assistant's steps (A2): check → turn (operonx-agents, or the Copilot's path as the fallback) → answer."""

from __future__ import annotations

import base64
import binascii
import time
from typing import Any, Dict, List, Optional

from operonx import op
from operonx.core.loggings import LOGGER

from assistant import conversations as conv
from assistant import knowledge, memory, progress, registry, sessions, stream
from assistant import turn as turns
from assistant.base import Ctx
from control import audit, db, roles
from copilot import router
from copilot.ops import HELP, run_tool
from copilot.scrub import scrub
from people import auth

START = {
    **HELP,
    "cio": [
        "Có gì chờ tôi duyệt?",
        "Tác động lớn nhất tới tài sản ở đâu?",
        "Độ chính xác của mô hình?",
        "Hộp tin có bao nhiêu tin?",
    ],
    "rm": ["Tổng quan có gì cần làm?", *HELP["rm"][:3]],
    "admin": [
        "Hệ thống có gì bất thường?",
        "Chuỗi nhật ký còn nguyên không?",
        "Có cảnh báo hệ thống nào?",
        "Cấu hình nào chờ duyệt?",
    ],
}


@op
def check_request(
    message: str = None,
    role: str = None,
    client_id: str = None,
    scope: str = None,
    route: str = None,
    goals: list = None,
    turn_id: str = None,
    approvals: dict = None,
    conversation_id: str = None,
    graph: dict = None,
) -> dict:
    """Who asks (a customer always as client), what (≤ 2,000 characters), in which conversation (none: a new one),
    or which parked writes they answer; what the workspace shows them (``graph``)."""
    return {"request": request_of(message, role, client_id, scope, route, goals, turn_id, approvals, conversation_id,
                                  graph)}  # fmt: skip


LENSES = {"tong-quan", "tai-san", "dong-tien", "muc-tieu", "tin", "rui-ro"}


def graph_of(g: Any) -> Dict[str, Any]:
    """The workspace's context, checked (UNIFIED_FLOWS_PLAN F10): a known lens; what is picked (an id, its kind, its
    label — the label reaches a model only in model mode); the active stress tests, known ids only, the person's
    what-if only with inputs inside the server's bounds. Anything else is dropped, never an error."""
    if not isinstance(g, dict):
        return {}
    from scenarios import _sim
    from scenarios.combine import MAX

    out: Dict[str, Any] = {}
    if g.get("lens") in LENSES:
        out["lens"] = g["lens"]
    sel = g.get("selected")
    if isinstance(sel, dict) and isinstance(sel.get("id"), str) and 0 < len(sel["id"]) <= 200:
        kind, label = str(sel.get("kind") or "")[:20], str(sel.get("label") or "")[:120]
        out["selected"] = {"id": sel["id"], "kind": kind, "label": label}
    named = g.get("active") if isinstance(g.get("active"), list) else []
    active = list(dict.fromkeys(s for s in named if isinstance(s, str) and s in _sim.SHOCKS))[:MAX]
    prm = g.get("params") if isinstance(g.get("params"), dict) else {}
    if "custom" in active:
        mine = prm.get("custom") if isinstance(prm.get("custom"), dict) else {}
        try:
            out["params"] = {"custom": _sim.custom_params(mine)}
        except ValueError:
            active.remove("custom")
    if active:
        out["active"] = active
    return out


def request_of(message=None, role=None, client_id=None, scope=None, route=None, goals=None, turn_id=None,
               approvals=None, conversation_id=None, graph=None, voice=None) -> dict:  # fmt: skip
    message = str(message or "").strip()
    if len(message) > 2000:
        raise ValueError("Câu hỏi dài quá 2.000 ký tự")
    answers = {str(k): str(v) for k, v in (approvals or {}).items()}
    if any(v not in ("approve", "deny") for v in answers.values()):
        raise ValueError("Trả lời là approve hoặc deny")
    if answers and not turn_id:
        raise ValueError("Thiếu turn_id của việc đang chờ")
    if not message and not answers:
        raise ValueError("Hãy nhập câu hỏi")
    return {
        **who(role, client_id, scope),
        "message": message,
        "route": str(route or ""),
        "followed": None if goals is None else [str(g) for g in goals][:50],
        "turn_id": str(turn_id or "") or None,
        "approvals": answers,
        "conversation_id": str(conversation_id or "") or None,
        "graph": graph_of(graph),
        "voice": voice is True,
    }


def who(role: Optional[str], client_id: Optional[str], scope: Optional[str] = None) -> Dict[str, Any]:
    role = auth.role_for(str(role or "client"))
    if role not in registry.DEMO_USER:
        raise roles.Forbidden(f"vai trò {role!r} không có")
    client_id = auth.client_for(client_id)  # a customer is always themselves; staff only their families (D13)
    return {"role": role, "client_id": client_id or None, "scope": scope or "personal"}


def context(r: Dict[str, Any]) -> Ctx:
    return Ctx(
        role=r["role"],
        client_id=r["client_id"],
        scope=r["scope"],
        question=r["message"],
        followed=r["followed"],
        user=auth.acting_id(registry.DEMO_USER.get(r["role"])),
        reads=turns.model_reads(),
        route=r["route"],
        graph=r.get("graph") or {},
        voice=bool(r.get("voice")),
    )


async def fallback_events(r: Dict[str, Any], why: str):
    """The Copilot's path: the keyword router picks one tool, our code runs it; a write waits as there. Yields the
    call's start and end (the workspace draws them), then ``{"type": "result", ...}``."""
    if r["approvals"]:
        yield {"type": "result", "result": {"status": "failed", "mode": "fallback", "why": why, "steps": [],
               "text": "Không còn việc nào chờ xác nhận: trợ lý đang chạy chế độ dự phòng, hãy hỏi lại."}}  # fmt: skip
        return
    seen = scrub(r["message"])
    got = router.keyword(seen, r["route"], r["role"])
    known = got["tool"] in registry.REGISTRY
    if known:
        label, nodes = registry.LABELS.get(got["tool"], got["tool"]), stream.nodes_for(got["tool"], got["args"])
        yield {
            "type": "step",
            "phase": "start",
            "call_id": "fallback",
            "tool": got["tool"],
            "label": label,
            "nodes": nodes,
            **progress.says(got["tool"], got["args"]),
        }
    t0 = time.monotonic()
    step = await run_tool(
        got["tool"], got["args"], False, r["role"], r["client_id"], r["scope"], r["message"], r["followed"]
    )
    if known:
        yield stream.step_end(got["tool"], "fallback", step["status"] == "ok", (time.monotonic() - t0) * 1000, step)
    text = step["text"]
    if step["status"] == "unknown":  # not the person's wording: the model is what is missing (stress test D04)
        text = ("Trợ lý AI hiện không trả lời được, nên tôi chỉ làm được các việc có sẵn dưới đây. Câu này cần trợ lý "
                "AI: bạn thử lại sau ít phút nhé.")  # fmt: skip
    out = {"status": step["status"], "mode": "fallback", "why": why, "seen": seen, "text": text}
    if step["status"] == "pending":  # the Copilot's own confirm (POST /api/copilot) runs it
        out["confirm"] = step["confirm"]
    out["steps"] = [] if step["status"] in ("pending", "unknown") else [step]
    out["suggest"] = step.get("suggest")
    yield {"type": "result", "result": out}


async def fallback(r: Dict[str, Any], why: str) -> Dict[str, Any]:
    async for e in fallback_events(r, why):
        if e["type"] == "result":
            return e["result"]
    raise RuntimeError("the fallback ended without a result")


def conversation(r: Dict[str, Any], ctx: Ctx) -> str:
    """The conversation a message goes to: the one named, when it is this person's (else ValueError), or a new one."""
    if r["conversation_id"]:
        return conv.own(ctx, r["conversation_id"])["id"]
    return conv.start(ctx, r["message"])


async def turn_events(r: Dict[str, Any]):
    """One turn: the agent when a model is configured; else, or when the model fails before any tool ran, the
    fallback. A parked write is answered only by the person who asked, within ten minutes. Every turn belongs to a
    conversation (A3): the one asked in, the one the parked write came from, or a new one.

    Yields the turn's events as they happen (FEAT-40: ``step``, ``text``, ``wait``), then ``{"type": "result"}``."""
    ctx = context(r)
    seq: Optional[int] = None  # the turn's row, written now (OWN-SS-03)
    ran: List[Dict[str, Any]] = []  # its steps as they end
    labels: Dict[str, str] = {}
    ended = False
    clock = stream.Clock()

    def done(result: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal ended
        ended = True
        result = {**result, "timing": clock.summary()}
        return {"type": "result", "result": {**result, "turn_seq": seq} if seq is not None else result}

    async def fall(why: str, cid: Optional[str]):
        async for e in fallback_events(r, why):
            yield done({**e["result"], "conversation_id": cid}) if e["type"] == "result" else e

    try:
        cid = None if r["approvals"] else conversation(r, ctx)
    except ValueError as exc:  # someone else's conversation, or one deleted
        yield done({"status": "failed", "mode": "model", "steps": [], "text": str(exc)})
        return
    if cid is None:  # a confirm: the conversation the parked write came from, when it is this person's
        try:
            cid = turns.parked(r["turn_id"], ctx)["conversation_id"]
        except ValueError:
            cid = None  # said below, by resume_events
    if cid is not None:
        seq = conv.begin(cid, r["message"] or None)
    try:
        async for e in _turn(r, ctx, cid, done, fall, clock):
            if seq is not None and e.get("type") == "step":
                if e.get("phase") == "start":
                    labels[e["call_id"]] = e.get("label") or e["tool"]
                elif e.get("phase") == "end":
                    ran.append({"tool": e["tool"], "label": labels.get(e["call_id"], e["tool"]),
                                "status": "ok" if e.get("ok") else "failed"})  # fmt: skip
                    conv.progress(cid, seq, ran)
            yield e
    finally:  # the stream closed before the answer (a refresh, a closed tab): what ran stays, said so
        if seq is not None and not ended:
            conv.interrupt(cid, seq, ran)


async def _turn(r: Dict[str, Any], ctx: Ctx, cid: Optional[str], done, fall, clock: stream.Clock):
    if not turns.live():
        async for e in fall("chưa cấu hình mô hình cho trợ lý", cid):
            yield e
        return
    redo = None
    try:
        events = (
            turns.resume_events(ctx, r["turn_id"], r["approvals"])
            if r["approvals"]
            else turns.run_events(ctx, r["message"], cid)
        )
        async for ev in events:
            if isinstance(ev, dict):
                got = ev["reply"]
                if not r["approvals"] and got.get("model_error") and not ctx.trail:  # failed before any tool: NFR-03
                    LOGGER.warning("assistant: the model failed (%s)", got["model_error"])
                    redo = f"mô hình lỗi ({got['model_error'].split(':')[0]})"
                else:
                    yield done(got)
                continue
            clock.see(ev)
            if (e := stream.translate(ev, ctx)) is not None:
                yield e
    except ValueError as exc:  # nothing waiting for this person, or too late
        yield done({"status": "failed", "mode": "model", "steps": [], "text": str(exc), "conversation_id": cid})
        return
    except Exception as exc:  # noqa: BLE001 - the model failed: NFR-03, the product keeps answering
        LOGGER.warning("assistant: the model failed (%s: %s)", type(exc).__name__, exc)
        if ctx.trail or r["approvals"]:
            text = f"Trợ lý gặp lỗi giữa chừng ({type(exc).__name__}); hãy kiểm tra trên trang trước khi làm lại."
            yield done({"status": "failed", "mode": "model", "steps": [], "conversation_id": cid, "text": text})
            return
        redo = f"mô hình lỗi ({type(exc).__name__})"
    if redo:
        async for e in fall(redo, cid):
            yield e


@op
async def turn(request: dict) -> dict:
    """One turn (``turn_events``), its answer only."""
    result = None
    async for e in turn_events(request):
        if e["type"] == "result":
            result = e["result"]
    return {"result": result}


def _latest(dates: List[str]) -> str | None:
    return max((d for d in dates if d), default=None)


@op
def answer(request: dict, result: dict) -> dict:
    """The answer with what it rests on (each step's page, sources and date), stamped and audited: who, the mode,
    the tools and their statuses, the model and its usage — not the conversation's text."""
    return {"assistant": finish(request, result)}


def finish(r: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(result)
    turn_seq = result.pop("turn_seq", None)
    steps = result.get("steps") or []
    seen_pages = set()
    citations = []
    for s in steps:
        ev = s.get("evidence")
        if ev and ev["route"] not in seen_pages:
            seen_pages.add(ev["route"])
            citations.append(ev)
    sources = list(dict.fromkeys(x for s in steps for x in s.get("sources") or [] if x))
    last = next((registry.REGISTRY.get(s["tool"]) for s in reversed(steps) if s.get("tool")), None)
    at = time.time()
    actor = auth.acting_id(registry.DEMO_USER.get(r["role"])) or f"client:{r['client_id'] or '-'}"
    usage = result.get("usage") or {}
    with db.tx() as con:
        seq = audit.append(
            con,
            actor,
            "assistant.turn",
            ",".join(s["tool"] for s in steps if s.get("tool")) or "-",
            {
                "role": r["role"],
                "client_id": r["client_id"],
                "status": result.get("status"),
                "mode": result.get("mode"),
                "model": result.get("model"),
                "steps": [[s.get("tool"), s.get("status")] for s in steps],
                "confirm": bool(r["approvals"]),
                "tokens": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0),
                "cost_usd": usage.get("cost_usd"),
                "timing": result.get("timing"),  # ms, no words: where a slow turn's time went (stream.Clock)
            },
        )
    out = {
        **result,
        "citations": citations,
        "sources": sources,
        "as_of": _latest([s.get("as_of") for s in steps]),
        "focus": next((s.get("focus") for s in reversed(steps) if s.get("focus")), []),
        "navigate": next((s.get("navigate") for s in reversed(steps) if s.get("navigate")), None),
        "suggest": result.get("suggest") or (last and last.follow) or START.get(r["role"], []),
        "answered_at": at,
        "audit_seq": seq,
    }
    if out.get("conversation_id"):  # the turn as the panel shows it, to draw again on any device (A3)
        conv.record(out["conversation_id"], r["message"] or None, out, seq=turn_seq)
        try:  # the session as the panel names it; it asks for the title and goal once this answer is drawn (S2)
            c = conv.own(context(r), out["conversation_id"])
            out["session"] = {k: c.get(k) for k in ("id", "title", "goal", "summary", "title_auto", "turns")}
            out["describe"] = sessions.due(c["turns"], bool(out.get("compacted"))) and c.get("described") != c["turns"]
        except ValueError:
            pass
    return out


FIELDS = ("message", "role", "client_id", "scope", "route", "goals", "turn_id", "approvals", "conversation_id", "graph",
          "voice")


@op
async def stream_turn(item: dict = None):
    """POST /api/assistant/stream (FEAT-40): the same turn as POST /api/assistant, said as it happens — one event per
    yield: ``step`` (a tool starting, with the graph nodes it reads; ending, with what its result names), ``text``
    (the model's words, model mode only), ``wait`` (a write for the person to confirm), then ``answer`` (the same
    answer as the JSON door, audited and kept) or ``error``."""
    try:
        body = item if isinstance(item, dict) else {}
        r = request_of(**{k: body.get(k) for k in FIELDS})
    except Exception as exc:  # noqa: BLE001 - a bad request: said on the stream, nothing runs
        yield {"event": {"type": "error", "text": str(exc)}}
        return
    yield {"event": {"type": "start"}}
    try:
        async for e in turn_events(r):
            if e["type"] == "result":
                yield {"event": {"type": "answer", "assistant": finish(r, e["result"])}}
            else:
                yield {"event": e}
    except Exception as exc:  # noqa: BLE001 - said on the stream; the JSON door's caller would have got a 500
        LOGGER.warning("assistant stream: %s: %s", type(exc).__name__, exc)
        yield {"event": {"type": "error", "text": f"Trợ lý gặp lỗi ({type(exc).__name__})"}}


# -- the conversations (A3): list, open, delete ------------------------------------------------------------------


@op
async def conversations(action: str = None, conversation_id: str = None, role: str = None, client_id: str = None,
                  title: str = None) -> dict:  # fmt: skip
    """The person's sessions in this role: ``list`` (newest first) or ``list_archived``, ``open`` one (its turns as
    shown, and the writes still waiting in it), ``rename``, ``archive``, ``restore``, ``describe`` (the title and
    goal written by the model when due, S2), ``delete`` one (its turns and the model's side; audited without its
    text)."""
    r = {**who(role, client_id), "message": "", "route": "", "followed": None}
    ctx = context(r)
    action = str(action or "list")
    if action in ("list", "list_archived"):
        return {"conversations": {"items": conv.listing(ctx, archived=action == "list_archived")}}
    if action == "rename":
        return {"conversations": {"conversation": conv.rename(ctx, conversation_id, title)}}
    if action == "describe":
        c = conv.own(ctx, conversation_id)
        return {"conversations": {"conversation": await sessions.after_turn(ctx, c["id"]) or c}}
    if action in ("archive", "restore"):
        return {"conversations": {"conversation": conv.set_archived(ctx, conversation_id, action == "archive")}}
    if action == "open":
        c = conv.own(ctx, conversation_id)
        with conv.db() as con:
            rows = con.execute(
                "select run_id from parked where conversation_id = ? and created > ?",
                (c["id"], time.time() - turns.APPROVAL_TTL),
            ).fetchall()
        return {"conversations": {"conversation": c, "turns": conv.turns_of(c["id"]), "waiting": [x[0] for x in rows]}}
    if action == "delete":
        n = conv.delete(ctx, conversation_id)
        actor = auth.acting_id(registry.DEMO_USER.get(r["role"])) or f"client:{r['client_id'] or '-'}"
        with db.tx() as con:
            audit.append(
                con, actor, "assistant.conversation.delete", str(conversation_id), {"role": r["role"], "turns": n}
            )
        return {"conversations": {"deleted": conversation_id, "turns": n}}
    raise ValueError("action là list, list_archived, open, rename, archive, restore, describe hoặc delete")


# -- the Bộ nhớ page (A4): list, correct, forget, forget all, search the archive ---------------------------------


@op
async def memory_page(
    action: str = None,
    item_id: str = None,
    text: str = None,
    kind: str = None,
    query: str = None,
    role: str = None,
    client_id: str = None,
    file_name: str = None,
    data: str = None,
    key: str = None,
) -> dict:
    """The person's long-term items, archive and documents in this role. Changes are audited with what changed, not
    the text. A document arrives base64-encoded (``file_name``, ``data``; not ``name``: the serve layer passes
    ``name`` to every graph)."""
    r = {**who(role, client_id), "message": "", "route": "", "followed": None}
    ctx = context(r)
    action = str(action or "list")
    actor = auth.acting_id(registry.DEMO_USER.get(r["role"])) or f"client:{r['client_id'] or '-'}"

    def audited(what: str, obj: str, data: dict) -> None:
        with db.tx() as con:
            audit.append(con, actor, f"assistant.memory.{what}", obj, {"role": r["role"], **data})

    if action == "list":
        return {"memory": {"items": await memory.items(ctx), "kinds": memory.KINDS}}
    if action == "search":
        return {"memory": {"hits": memory.search_history(ctx, str(query or ""))}}
    if action == "update":
        item = await memory.correct(ctx, str(item_id or ""), str(text or ""), kind or None)
        audited("update", item.id, {"kind": item.kind})
        return {"memory": {"item": memory.view(item)}}
    if action == "delete":
        n = int(await memory.forget(ctx, str(item_id or "")))
        if n:
            conv.scrub()
            audited("delete", str(item_id), {})
        return {"memory": {"deleted": n}}
    if action == "clear":
        n = await memory.forget_all(ctx)
        conv.scrub()
        audited("clear", "-", {"deleted": n})
        return {"memory": {"deleted": n}}
    if action == "materials":
        return {"memory": {"materials": knowledge.materials(ctx)}}
    if action == "material_add":
        try:
            raw = base64.b64decode(str(data or ""), validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("Tệp không đọc được") from None
        got = await knowledge.add_material(ctx, str(file_name or ""), raw)
        audited("material_add", got["key"], {"bytes": len(raw), "action": got["action"]})
        return {"memory": {"material": got}}
    if action == "material_delete":
        ok = await knowledge.delete_material(ctx, str(key or ""))
        if ok:
            audited("material_delete", str(key), {})
        return {"memory": {"deleted": int(ok)}}
    if action == "follow_ups":  # the person's follow-ups (A6): open, fired; what the bell shows
        from assistant import followups

        return {"memory": {"follow_ups": followups.listing(ctx), "unseen": followups.unseen(ctx)}}
    if action == "follow_up_cancel":
        from assistant import followups

        ok = followups.cancel(ctx, str(key or ""))
        if ok:
            audited("follow_up_cancel", str(key), {})
        return {"memory": {"cancelled": int(ok)}}
    if action == "follow_up_seen":
        from assistant import followups

        return {"memory": {"seen": int(followups.seen(ctx, str(key or "")))}}
    raise ValueError(
        "action là list, search, update, delete, clear, materials, material_add, material_delete, follow_ups, "
        "follow_up_cancel hoặc follow_up_seen"
    )


@op
async def retention_sweep() -> dict:
    """The CIO's retention: conversations past ``assistant_retention`` and expired items deleted (A4)."""
    from assistant.retention import sweep

    return {"swept": await sweep()}


@op
async def consolidate_due(tick: str = None, at: str = None) -> dict:
    """The memory consolidator's tick (A6): every conversation idle 15 minutes whose turns changed, distilled."""
    from assistant.consolidate import run_due

    return {"consolidated": await run_due()}


@op
def follow_ups_market(job: str = None, after: dict = None) -> dict:
    """After a market job: the open follow-ups on the series it loads, against their latest close (A6, no model)."""
    from assistant import followups

    return {"follow_ups": followups.check_market(followups.job_series(job) if job else None)}


@op
def follow_ups_topics(after: dict = None) -> dict:
    """After the news job: the open topic follow-ups against the events made effective since (A6, no model)."""
    from assistant import followups

    return {"follow_ups": followups.check_topics()}
