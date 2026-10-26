"""The chat's steps: the request, the rule reader, and the answer either way; and the same turn as a stream."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List

from operonx import op
from operonx.core.loggings import LOGGER

from control.errors import BadRequest
from declare import _rules
from people import auth
from wealth import ai, fixtures, store
from wealth.money import vnd

KINDS = {"asset", "dependent", "income"}


@op
def check_request(client_id: str = None, message: str = None, session_id: str = None) -> dict:
    """What a caller sent, checked: a known client, a message (at most 2000 characters), and the
    chat's session (the client's own by default)."""
    return checked(client_id, message, session_id)


def checked(client_id: str = None, message: str = None, session_id: str = None) -> dict:
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise BadRequest(f"no client {client_id!r}")
    auth.require_client(client_id)  # their family, their RM, or the desk (ROLE-02)
    message = str(message or "").strip()
    if not message:
        raise BadRequest("an empty message")
    return {
        "client_id": client_id,
        "message": message[:2000],
        "session_id": str(session_id or f"{client_id}-chat"),
    }


@op
def ai_mode() -> dict:
    """Whether an agent answers and on which model (wealth/ai.client_model: the ``client_ai`` configuration), and
    when this turn began."""
    use = ai.client_model()
    return {"assistant": use == "assistant", "onprem": use == "onprem", "since": time.time()}


def _line(kind: str, d: Dict[str, Any]) -> str:
    if kind == "dependent":
        return f"Người phụ thuộc: {d['name']} ({d['relation']})" + (
            f", sinh {d['birth_year']}" if d.get("birth_year") else ""
        )
    if kind == "income":
        return f"Thu nhập: {d['label']}, {vnd(d['amount'])}/tháng"
    if d["class"] == "gold":
        return f"Vàng: {d['qty']:g} lượng"
    if d["class"] == "loan":
        return f"Khoản nợ: {vnd(d['value'])}" + (
            f", trả {vnd(d['monthly_payment'])}/tháng" if d.get("monthly_payment") else ""
        )
    value = d.get("value")
    if not value and d.get("class") == "real_estate" and d.get("area") and d.get("sqm"):
        area = fixtures.market()["areas"][d["area"]]
        return f"{d['name']}: ước tính {vnd(d['sqm'] * area['price_sqm'])} theo giá khu vực {area['name']}"
    return f"{d['name']}" + (f": {vnd(value)}" if value else "")


def by_rules(client_id: str, message: str) -> str:
    """Read the message with the rules, record what they found, and say what was recorded."""
    found = _rules.parse(message)
    if not found:
        return (
            "Tôi chưa nhận ra tài sản nào trong câu này. Anh/chị có thể nói như: "
            "“Tôi có 1 căn ở Thảo Điền mua 2019 giá 8 tỷ” hoặc “Nhà tôi có 10 lượng vàng”."
        )
    known = [r for r in found if store.same_profile(client_id, r["kind"], r["data"])]  # said in an earlier turn
    new = [r for r in found if r not in known]
    for rec in new:
        store.add_profile(client_id, rec["kind"], {**rec["data"], "via": "chat"})
    lines = lambda rs: "\n".join(f"• {_line(r['kind'], r['data'])}" for r in rs)  # noqa: E731
    reply = "\n".join(
        part
        for part in (
            f"Tôi đã ghi nhận:\n{lines(new)}" if new else "",
            f"Đã có trong hồ sơ từ trước, tôi không ghi lại:\n{lines(known)}" if known else "",
        )
        if part
    )
    if any(
        r["data"].get("class") == "real_estate" and not r["data"].get("value") and not r["data"].get("sqm")
        for r in new
    ):
        reply += "\nAnh/chị cho biết thêm diện tích hoặc giá trị hiện tại để định giá chính xác hơn nhé."
    return reply


def chat_session(session_id: str):
    """Each chat's conversation, kept beside the state (so the agent remembers the last turns), sealed when column
    keys are set (BRD-NFR-07, control/crypto.py)."""
    from operonx.agents import SQLiteSession

    from control.crypto import SealedSession
    from wealth.paths import state_path

    return SealedSession(SQLiteSession(session_id, state_path().with_name("chat.db")), session_id)


@op
def rule_declare(client_id: str, message: str) -> dict:
    """No model: the rules read the message."""
    return {"reply": by_rules(client_id, message), "method": "rules"}


@op
def agent_answer(
    client_id: str,
    message: str,
    output: str = None,
    status: str = None,
    error: str = None,
    onprem_output: str = None,
    onprem_status: str = None,
    onprem_error: str = None,
) -> dict:
    """The agent's reply (on llm:assistant or llm:onprem, whichever ran); when it could not answer (no network, a
    bad key, the client-data barrier), the rules read the message instead, so what the client said is still
    recorded."""
    if status is None and onprem_status is not None:
        output, status, error = onprem_output, onprem_status, onprem_error
    if status == "completed" and output:
        return {"reply": output, "method": "ai"}
    reply = by_rules(client_id, message)
    return {"reply": reply, "method": "rules", "error": error or status}


@op
def recorded(
    client_id: str,
    since: float,
    ai_reply: str = None,
    rule_reply: str = None,
    ai_method: str = None,
    rule_method: str = None,
) -> dict:
    """What this turn added to the client's profile, beside the reply."""
    return {"turn": turn_of(client_id, since, ai_reply or rule_reply or "", ai_method or rule_method or "rules")}


def turn_of(client_id: str, since: float, reply: str, method: str) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for kind in sorted(KINDS):
        for d in store.profile(client_id, kind):
            if d.get("via") == "chat" and store.created(d["id"]) >= since:
                items.append({"kind": kind, "line": _line(kind, d), "data": d})
    return {"client_id": client_id, "reply": reply, "method": method, "recorded": items}


#: what a step says while its tool runs (the stream's ``step``)
STEP = {
    "declare_property": "Đang ghi nhà đất",
    "declare_gold": "Đang ghi vàng",
    "declare_holding": "Đang ghi tài sản",
    "declare_loan": "Đang ghi khoản nợ",
    "declare_dependent": "Đang ghi người phụ thuộc",
    "declare_income": "Đang ghi thu nhập",
    "hoi_them": "Đang soạn câu hỏi",
}


@op
async def stream_declare(item: dict = None):
    """POST /api/declare/stream: the same turn as POST /api/declare, said as it happens — ``start``, then ``step`` (a
    tool starting and ending), ``text`` (the agent's words), ``form`` (what ``hoi_them`` asks), and ``answer`` (the
    turn, as the JSON door returns it) or ``error``. Without a model, or when it fails before writing anything, the
    rules read the message."""
    try:
        body = item if isinstance(item, dict) else {}
        ask = checked(body.get("client_id"), body.get("message"), body.get("session_id"))
    except Exception as exc:  # noqa: BLE001 - a bad request: said on the stream, nothing runs
        yield {"event": {"type": "error", "text": str(exc)}}
        return
    client_id, message = ask["client_id"], ask["message"]
    since, use = time.time(), ai.client_model()
    yield {"event": {"type": "start"}}
    reply, method = None, "rules"
    if use in ("assistant", "onprem"):
        from operonx_agents import Runner
        from operonx_agents.run.events import RunFinished, TextDelta, ToolCallFinished, ToolCallStarted

        from declare.agent import DECLARER, DECLARER_ONPREM

        s, res, wrote = chat_session(ask["session_id"]), None, False
        try:
            async with asyncio.timeout(60):
                agent = DECLARER if use == "assistant" else DECLARER_ONPREM
                async for ev in Runner.stream(agent, message, deps=client_id, session=s):
                    if isinstance(ev, TextDelta) and ev.text:
                        yield {"event": {"type": "text", "text": ev.text}}
                    elif isinstance(ev, ToolCallStarted):
                        if ev.tool == "hoi_them" and isinstance(ev.args, dict):
                            yield {"event": {"type": "form", "form": form_of(ev.args)}}
                        wrote = wrote or ev.tool != "hoi_them"
                        yield {"event": {"type": "step", "phase": "start", "tool": ev.tool,
                                         "label": STEP.get(ev.tool, ev.tool)}}  # fmt: skip
                    elif isinstance(ev, ToolCallFinished):
                        yield {"event": {"type": "step", "phase": "end", "tool": ev.tool, "ok": ev.ok}}
                    elif isinstance(ev, RunFinished):
                        res = ev.result
        except Exception as exc:  # noqa: BLE001 - the rules answer below, unless a tool already wrote
            LOGGER.warning("declare stream: %s: %s", type(exc).__name__, exc)
        finally:
            s.inner.close()
        if res is not None and res.status == "completed" and res.output:
            reply, method = str(res.output), "ai"
        elif wrote:  # the model failed after writing: say what it wrote, not the rules' second reading
            reply, method = "Dạ, em đã ghi những mục dưới đây; anh/chị kiểm tra lại giúp em nhé.", "ai"
    if reply is None:
        reply = by_rules(client_id, message)
    yield {"event": {"type": "answer", "turn": turn_of(client_id, since, reply, method)}}


KINDS_OF_FIELD = {"text", "number", "money", "year", "choice"}


def form_of(args: Dict[str, Any]) -> Dict[str, Any]:
    """``hoi_them``'s arguments as the page draws them: a title and at most 4 blanks, each of a known kind."""
    fields = []
    for f in args.get("fields") or []:
        if len(fields) == 4:
            break
        if not isinstance(f, dict) or not str(f.get("label") or "").strip():
            continue
        kind = f.get("kind") if f.get("kind") in KINDS_OF_FIELD else "text"
        options = [str(o) for o in (f.get("options") or []) if str(o).strip()][:6]
        if kind == "choice" and not options:
            kind = "text"
        fields.append({"label": str(f["label"]).strip()[:80], "kind": kind, "options": options,
                       "unit": str(f.get("unit") or "")[:20]})  # fmt: skip
    return {"title": str(args.get("title") or "")[:120], "fields": fields}
