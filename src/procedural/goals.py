"""The goal branch (BRD §10, FR-601…604): a regulation that does not move prices but can delay a goal
that sends money abroad. The result is a date, papers and an urgency — never money.

Inputs: regulation notes Compliance released, and each family's active goals (their dated outflows).
Nothing else: no AML data, no risk rating (§13.2).

- A goal's purpose and destination come from what the RM declared (FR-601). Undeclared, they are
  inferred from the goal's name — but an inferred match only makes an RM task ("xác nhận mục
  tiêu"), never a message to the client, because names mislead ("Nhật Minh", "Mỹ Linh"). A country
  word counts only with context ("du học Úc", "(Mỹ)", "sang Canada"), so a person's name does not.
- Milestone = the first day of the month the money is needed − (extra preparation weeks + 4).
- Levels: contact now (milestone ≤ 3 months away and the text is issued) · remind (spending within
  104 weeks, or the text is still a draft) · note (further out, or before the effective date).
- Past and closed goals are skipped. A note whose client message or RM hint mentions PEP, a risk
  rating, suspicious transactions or enhanced monitoring is refused (FR-604).
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

PURPOSES = {
    "study_abroad": "Du học",
    "emigrate": "Định cư hoặc nghỉ hưu ở nước ngoài",
    "invest_abroad": "Đầu tư ra nước ngoài",
    "property_abroad": "Mua bất động sản nước ngoài",
    "support_abroad": "Chu cấp người thân ở nước ngoài",
    "other_transfer": "Chuyển tiền khác",
}
LEVELS = {
    "contact_now": "RM liên hệ ngay",
    "remind": "Nhắc trên thẻ mục tiêu",
    "note": "Ghi chú",
    "confirm_goal": "RM xác nhận mục tiêu",
}
COUNTRIES = {
    "úc": "Úc",
    "australia": "Úc",
    "mỹ": "Mỹ",
    "hoa kỳ": "Mỹ",
    "anh": "Anh",
    "canada": "Canada",
    "nhật": "Nhật Bản",
    "nhật bản": "Nhật Bản",
    "hàn quốc": "Hàn Quốc",
    "singapore": "Singapore",
    "đức": "Đức",
    "pháp": "Pháp",
    "new zealand": "New Zealand",
    "phần lan": "Phần Lan",
    "hà lan": "Hà Lan",
    "đài loan": "Đài Loan",
}
PURPOSE_WORDS = [
    ("study_abroad", ["du học", "học phí đại học", "học phí", "đại học", "trường"]),
    ("emigrate", ["định cư", "nghỉ hưu ở nước ngoài", "nghỉ hưu tại", "di trú"]),
    ("invest_abroad", ["đầu tư ra nước ngoài", "đầu tư nước ngoài"]),
    ("property_abroad", ["mua nhà ở", "mua nhà tại", "bất động sản nước ngoài", "căn hộ ở"]),
    ("support_abroad", ["chu cấp", "gửi tiền cho", "trợ cấp"]),
]
# a country word counts only right after one of these, or in parentheses
_CONTEXT = r"(?:du học|ở|tại|sang|đi|qua|định cư|nghỉ hưu ở|\()\s*"
FORBIDDEN = [
    "pep",
    "người có ảnh hưởng chính trị",
    "xếp hạng rủi ro",
    "giao dịch đáng ngờ",
    "giám sát tăng cường",
    "báo cáo giao dịch",
    "rửa tiền",
    "danh sách theo dõi",
]


def forbidden_words(*texts: str) -> List[str]:
    """Words a client-facing regulation note must not use (FR-604): the ``compliance`` list of the
    forbidden_phrases configuration in force (``FORBIDDEN`` above is its version 1)."""
    from views import schema

    pat = schema.phrases_pattern("compliance")
    return sorted({m.group(0).lower() for t in texts for m in pat.finditer(t or "")})


def infer(label: str) -> Optional[Dict[str, str]]:
    """Purpose and country from a goal's name, or None. Needs a purpose word AND a country in context."""
    low = (label or "").lower()
    country = None
    for word in sorted(COUNTRIES, key=len, reverse=True):
        if re.search(_CONTEXT + rf"{re.escape(word)}(?!\w)", low):
            country = COUNTRIES[word]
            break
    if not country:
        return None
    for purpose, words in PURPOSE_WORDS:
        if any(re.search(rf"(?<!\w){re.escape(w)}(?!\w)", low) for w in words):
            return {"purpose": purpose, "country": country}
    return {"purpose": "other_transfer", "country": country}


def milestone(need: date, prep_weeks: int) -> date:
    first = need.replace(day=1)
    return first - timedelta(weeks=int(prep_weeks) + 4)


def level(today: date, need: date, mile: date, note: Dict[str, Any]) -> str:
    issued = note.get("status") == "issued"
    effective = date.fromisoformat(note["effective_date"]) if note.get("effective_date") else None
    if effective and need < effective:
        return "note"  # the money goes out before the rule applies
    if issued and (mile - today).days <= 92:
        return "contact_now"
    if (need - today).days <= 104 * 7 or not issued:
        return "remind"
    return "note"


def goals_of(client: Dict[str, Any], today: date) -> List[Dict[str, Any]]:
    """A family's active goals: its dated outflows not yet past (fixtures ``events``)."""
    out = []
    for i, e in enumerate(sorted(client.get("events", []), key=lambda e: e["date"]), start=1):
        if e.get("direction") != "out" or e.get("closed"):
            continue
        need = date.fromisoformat(e["date"])
        if need < today:
            continue
        out.append(
            {
                "goal_id": f"GL-{client['id']}-{i:02d}",
                "label": e["label"],
                "date": e["date"],
                "amount": e.get("amount"),
                "category": e.get("category"),
            }
        )
    return out


def match(
    notes: List[Dict[str, Any]], families: Dict[str, Dict[str, Any]], declared: Dict[str, Dict[str, Any]], today: date
) -> List[Dict[str, Any]]:
    """Every (goal, released regulation note) pair that applies, with milestone and level.

    ``families``: family id → client fixture; ``declared``: goal id → {purpose, country, by, at}."""
    out = []
    for fid, client in sorted(families.items()):
        for g in goals_of(client, today):
            dec = declared.get(g["goal_id"])
            got = dec or infer(g["label"])
            if not got:
                continue
            need = date.fromisoformat(g["date"])
            for n in notes:
                reg = n["regulation"]
                if got["purpose"] not in reg["purposes"]:
                    continue
                countries = reg.get("countries") or []
                if countries and got.get("country") not in countries:
                    continue
                mile = milestone(need, reg.get("prep_weeks", 0))
                lv = level(today, need, mile, reg) if dec else "confirm_goal"
                out.append(
                    {
                        "family_id": fid,
                        "family_name": client["name"],
                        "goal_id": g["goal_id"],
                        "goal": g["label"],
                        "need_date": g["date"],
                        "purpose": got["purpose"],
                        "purpose_label": PURPOSES[got["purpose"]],
                        "country": got.get("country"),
                        "declared": bool(dec),
                        "note_id": n["id"],
                        "note_title": reg.get("document") or n["title"],
                        "note_status": reg.get("status"),
                        "milestone": mile.isoformat(),
                        "level": lv,
                        "level_label": LEVELS[lv],
                        "documents": reg.get("documents", []),
                        # the client reads a message only for a declared goal at remind or contact level
                        "client_message": reg.get("client_message")
                        if dec and lv in ("remind", "contact_now")
                        else None,
                        "rm_hint": reg.get("rm_hint")
                        if lv != "confirm_goal"
                        else "Mục tiêu suy từ tên: xác nhận với khách mục đích và nước đến trước khi nhắc.",
                    }
                )
    order = {"contact_now": 0, "confirm_goal": 1, "remind": 2, "note": 3}
    return sorted(out, key=lambda x: (order[x["level"]], x["milestone"], x["family_id"]))
