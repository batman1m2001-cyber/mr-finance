"""The chat's steps: the request, the rule reader, and the answer either way."""

from __future__ import annotations

import time
from typing import Any, Dict, List

from operonx import op

from declare import _rules
from wealth import ai, fixtures, store
from wealth.money import vnd

KINDS = {"asset", "dependent", "income"}


@op
def check_request(client_id: str = None, message: str = None, session_id: str = None) -> dict:
    """What a caller sent, checked: a known client, a message (at most 2000 characters), and the
    chat's session (the client's own by default)."""
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise ValueError(f"no client {client_id!r}")
    message = str(message or "").strip()
    if not message:
        raise ValueError("an empty message")
    return {
        "client_id": client_id,
        "message": message[:2000],
        "session_id": str(session_id or f"{client_id}-chat"),
    }


@op
def ai_mode() -> dict:
    """Whether the agent answers (wealth/ai.py), and when this turn began."""
    return {"ai": ai.enabled(), "since": time.time()}


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
    for rec in found:
        store.add_profile(client_id, rec["kind"], {**rec["data"], "via": "chat"})
    if not found:
        return (
            "Tôi chưa nhận ra tài sản nào trong câu này. Anh/chị có thể nói như: "
            "“Tôi có 1 căn ở Thảo Điền mua 2019 giá 8 tỷ” hoặc “Nhà tôi có 10 lượng vàng”."
        )
    reply = "Tôi đã ghi nhận:\n" + "\n".join(f"• {_line(r['kind'], r['data'])}" for r in found)
    if any(
        r["data"].get("class") == "real_estate" and not r["data"].get("value") and not r["data"].get("sqm")
        for r in found
    ):
        reply += "\nAnh/chị cho biết thêm diện tích hoặc giá trị hiện tại để định giá chính xác hơn nhé."
    return reply


def chat_session(session_id: str):
    """Each chat's conversation, kept beside the state (so the agent remembers the last turns)."""
    from operonx.agents import SQLiteSession

    from wealth.paths import state_path

    return SQLiteSession(session_id, state_path().with_name("chat.db"))


@op
def rule_declare(client_id: str, message: str) -> dict:
    """No model: the rules read the message."""
    return {"reply": by_rules(client_id, message), "method": "rules"}


@op
def agent_answer(client_id: str, message: str, output: str = None, status: str = None, error: str = None) -> dict:
    """The agent's reply; when it could not answer (no network, a bad key), the rules read the
    message instead, so what the client said is still recorded."""
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
    items: List[Dict[str, Any]] = []
    for kind in sorted(KINDS):
        for d in store.profile(client_id, kind):
            if d.get("via") == "chat" and store.created(d["id"]) >= since:
                items.append({"kind": kind, "line": _line(kind, d), "data": d})
    return {
        "turn": {
            "client_id": client_id,
            "reply": ai_reply or rule_reply or "",
            "method": ai_method or rule_method or "rules",
            "recorded": items,
        }
    }
