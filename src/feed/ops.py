"""Intelligence Feed items (redesign kit K4). Every item says why it is shown and names its evidence: a stored
record (run, regulation note, goal) or a number the dashboard or the transactions returned, with the page that
shows it (``link``: impact, graph, detail, flow — the UI maps it to the role's route). Nothing is inferred.

Thresholds (ours, FEAT-31): a news impact shows when its 3-month expected change is at least 0.5 % of net worth
or the family is flagged for RM pre-review (BR-09); a spending category shows when it moved by 30 % and 5 triệu
or more month on month; net worth when it moved 3 % or more in the month.
"""

from __future__ import annotations

from typing import Any, Dict, List

from operonx import op

from apply import reads
from flows.ops import LABELS
from people import auth
from research import ops as research
from wealth import fixtures

IMPACT_SHARE = 0.005
SPEND_RISE, SPEND_MIN = 0.30, 5_000_000
NW_MOVE = 0.03
RANK = {"high": 0, "medium": 1, "info": 2}


def _vnd(x: float) -> str:
    a = abs(x)
    s = f"{a / 1e9:.2f} tỷ".replace(".", ",") if a >= 1e9 else f"{a / 1e6:.1f} triệu".replace(".", ",")
    return ("+" if x > 0 else "−" if x < 0 else "") + s


@op
def check_request(client_id: str = None, scope: str = None, role: str = None) -> dict:
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise ValueError(f"no client {client_id!r}")
    role = auth.role_for(role or "client")
    if role not in ("client", "rm"):
        raise ValueError("role is client or rm")
    return {"client_id": client_id, "scope": scope or "personal", "role": role}


def _impacts(family_id: str, role: str, net_worth: float) -> List[Dict[str, Any]]:
    out = []
    data = reads.family_impact(family_id, role)
    for it in data["items"]:
        if it["status"] != "EFFECTIVE":
            continue
        e3 = it["horizons"]["3m"]["expected"]
        flagged = bool(it.get("pre_review"))
        big = net_worth > 0 and abs(e3) >= IMPACT_SHARE * net_worth
        if not (big or flagged):
            continue
        why = (
            "Gia đình chạm ngưỡng RM xem trước: trường hợp xấu 3 tháng (P10) ≤ −5% tài sản ròng"
            if flagged
            else f"Tác động kỳ vọng {abs(e3) / net_worth:.1%} tài sản ròng, trên ngưỡng 0,5%".replace(".", ",")
        )
        out.append(
            {
                "type": "impact",
                "severity": "high" if flagged else "medium",
                "title": f"{it['event']['title']}: có thể ảnh hưởng {_vnd(e3)} trong 3 tháng",
                "why": why,
                "value": e3,
                "evidence": {"kind": "run", "id": it["run_id"]},
                "link": "impact",
            }
        )
        for g in (it.get("goal_impact") or {}).get("goals", []):
            if g["changed"]:
                out.append(
                    {
                        "type": "goal",
                        "severity": "high" if g["after"]["level"] == "Thiếu" else "medium",
                        "title": f"{g['label']}: {g['before']['level']} → {g['after']['level']}",
                        "why": f"Sau tin “{it['event']['title']}”, mức đáp ứng mục tiêu đổi (hạn {g['date']})",
                        "evidence": {"kind": "goal", "id": g["goal_id"], "run": it["run_id"]},
                        "link": "impact",
                    }
                )
    return out


def _regulation(family_id: str, role: str) -> List[Dict[str, Any]]:
    out = []
    for m in research.matches(family_id):
        if role == "client" and not m["client_message"]:
            continue
        out.append(
            {
                "type": "goal",
                "severity": "high" if m["level"] == "contact_now" else "medium" if m["level"] != "note" else "info",
                "title": f"{m['goal']}: {m['client_message'] if role == 'client' else m['level_label']}",
                "why": f"{m['note_title']} áp dụng cho mục tiêu này; mốc chuẩn bị {m['milestone']}"
                + ("" if role == "client" else f". {m['rm_hint'] or ''}".rstrip(". ")),
                "evidence": {"kind": "regulation", "id": m["note_id"], "goal": m["goal_id"]},
                "link": "impact",
            }
        )
    return out


def _thresholds(d: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    rk, lq, nw = d["risk"], d["liquidity"], d["net_worth"]
    if rk["status"] in ("near", "over"):
        out.append(
            {
                "type": "risk",
                "severity": "high" if rk["status"] == "over" else "medium",
                "title": f"Mức sụt giảm ước tính {rk['current']:.1%} khi thị trường xấu".replace(".", ","),
                "why": f"{'Vượt' if rk['status'] == 'over' else 'Gần'} ngưỡng chấp nhận {rk['limit']:.0%}",
                "value": -rk["stress_loss"],
                "evidence": {"kind": "dashboard", "id": "risk"},
                "link": "detail",
            }
        )
    if lq["status"] in ("low", "critical"):
        out.append(
            {
                "type": "risk",
                "severity": "high" if lq["status"] == "critical" else "medium",
                "title": f"Thanh khoản dự phòng đủ chi {lq['months']:.0f} tháng",
                "why": "Dưới mốc an toàn 6 tháng chi tiêu",
                "value": lq["value"],
                "evidence": {"kind": "dashboard", "id": "liquidity"},
                "link": "detail",
            }
        )
    if abs(nw["month_change_pct"]) >= NW_MOVE:
        out.append(
            {
                "type": "change",
                "severity": "info",
                "title": f"Tài sản ròng {_vnd(nw['month_change'])} so với tháng trước",
                "why": f"Thay đổi {abs(nw['month_change_pct']):.1%} trong tháng, từ 3% trở lên".replace(".", ","),
                "value": nw["month_change"],
                "evidence": {"kind": "dashboard", "id": "net_worth"},
                "link": "detail",
            }
        )
    return out


def _spending(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    months = sorted({t["date"][:7] for t in transactions})
    if len(months) < 2:
        return []
    last, prev = months[-1], months[-2]
    out = []
    for cat in sorted({t["category"] for t in transactions if t["direction"] == "out"}):
        a = sum(
            t["amount"]
            for t in transactions
            if t["direction"] == "out" and t["category"] == cat and t["date"][:7] == prev
        )
        b = sum(
            t["amount"]
            for t in transactions
            if t["direction"] == "out" and t["category"] == cat and t["date"][:7] == last
        )
        if b - a >= SPEND_MIN and (a == 0 or (b - a) / a >= SPEND_RISE):
            label = LABELS.get(cat, cat)
            out.append(
                {
                    "type": "change",
                    "severity": "info",
                    "title": f"{label} tháng {last[5:]}/{last[:4]}: {_vnd(b)[1:]}, {_vnd(b - a)} so với tháng trước",
                    "why": "Chi một nhóm tăng từ 30% và 5 triệu trở lên so với tháng trước",
                    "value": -(b - a),
                    "evidence": {"kind": "transactions", "id": f"{cat}:{last}", "month": last, "category": cat},
                    "link": "flow",
                }
            )
    return out


@op
def feed(client_id: str, scope: str, role: str, dashboard: dict, transactions: list) -> dict:
    """The items, most important first, each with why and its evidence."""
    return {"feed": build(client_id, scope, role, dashboard, transactions)}


def build(client_id: str, scope: str, role: str, dashboard: Dict[str, Any], transactions: list) -> Dict[str, Any]:
    family_id = fixtures.client(client_id).get("member_of") or client_id
    nw = dashboard["net_worth"]["value"]
    items = (
        _impacts(family_id, role, nw) + _regulation(family_id, role) + _thresholds(dashboard) + _spending(transactions)
    )
    items.sort(key=lambda x: (RANK[x["severity"]], -abs(x.get("value") or 0)))
    for i in items:  # a stable handle for the page and the Copilot's highlight
        i["key"] = "feed:" + ":".join(str(v) for v in i["evidence"].values())
    return {
        "client_id": client_id,
        "family_id": family_id,
        "scope": scope,
        "role": role,
        "as_of": dashboard["as_of"],
        "items": items,
        "rules": "Tác động ≥ 0,5% tài sản ròng hoặc RM xem trước; mục tiêu đổi mức hoặc có quy định áp dụng; "
        "rủi ro, thanh khoản qua ngưỡng; chi tiêu tăng ≥ 30% và 5 triệu; tài sản ròng đổi ≥ 3%.",
    }
