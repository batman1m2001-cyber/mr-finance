"""The allocation's steps: the request checked, the case built (profile, certain income, risk level, the CIO's tilts),
the three buckets allocated; the worked example K-7F3A; the CIO's tilt; an RM sending the actions to the review queue."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from operonx import op

from allocation import _cashflow, _engine, _model
from control.errors import BadRequest
from wealth import fixtures, profile, store
from wealth.money import vnd

EXAMPLE = Path(__file__).resolve().parents[2] / "data" / "allocation_example.json"
CERTAIN = ("salary", "pension", "rent")  # income that keeps coming without a market: wages, a pension, rent
TILTS = ("_cio", "allocation_tilts")  # where the CIO's tilts in force are kept (wealth.store results)


def _method(method: Optional[str]) -> str:
    m = str(method or "A").upper()
    if m not in _cashflow.METHODS:
        raise BadRequest(f"method là một trong {', '.join(_cashflow.METHODS)}, không phải {method!r}")
    return m


def _assumptions(assumptions: Any) -> Dict[str, Any]:
    if assumptions in (None, ""):
        return {}
    if not isinstance(assumptions, dict):
        raise BadRequest("assumptions là một object {tên: giá trị}")
    unknown = sorted(set(assumptions) - set(_engine.ASSUMPTIONS))
    if unknown:
        raise BadRequest(f"không có giả định {', '.join(unknown)}")
    return assumptions


@op
def check_request(client_id: str = None, scope: str = None, method: str = None, assumptions: dict = None) -> dict:
    """What a caller sent, checked: a family they may see, a method A/B/C, known assumptions."""
    from people import auth

    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise BadRequest(f"no client {client_id!r}")
    auth.require_client(client_id)
    return {
        "client_id": client_id,
        "scope": scope or "family",
        "method": _method(method),
        "assumptions": _assumptions(assumptions),
    }


def certain_income(transactions: List[Dict[str, Any]], income_monthly: float) -> float:
    """The month's average of the last 12 months' wages, pensions and rent in, never above the income on file."""
    if not transactions:
        return 0.0
    last = max(t["date"] for t in transactions)[:7]
    y, m = int(last[:4]), int(last[5:7])
    first = f"{y - 1}-{m:02d}" if m < 12 else f"{y}-01"
    window = [t for t in transactions if first < t["date"][:7] <= last]
    total = sum(t["amount"] for t in window if t.get("direction") == "in" and t.get("category") in CERTAIN)
    return min(float(income_monthly), total / 12)


def risk_of(client_id: str, drawdown_limit: float) -> Dict[str, Any]:
    """The level from the client's last risk test; without one, the level whose drawdown limit is nearest the
    file's (simulated: every action then carries a warning, §9)."""
    from risk import _bank

    test = store.result(client_id, "risk")
    if test and (test.get("profile") or {}).get("level"):
        p = test["profile"]
        return {"level": int(p["level"]), "name": p["name"], "source": "test", "at": test.get("taken")}
    p = min(_bank.PROFILES, key=lambda x: (abs(x["drawdown_limit"] - float(drawdown_limit or 0.15)), x["level"]))
    return {"level": p["level"], "name": p["name"], "source": "simulated", "at": None}


def tilts() -> List[Dict[str, Any]]:
    """The CIO's tilts in force, oldest first."""
    return list(store.result(*TILTS) or [])


@op
def case_of(client_id: str, members: list, holdings: list, transactions: list) -> dict:
    """The case the engine reads: the household's holdings and profile, its certain income, risk level and the tilts."""
    me = fixtures.client(client_id)
    who = profile.build(client_id, members)
    who["income_certain_monthly"] = certain_income(transactions, who["income_monthly"])
    return {
        "case": {
            "as_of": fixtures.market()["as_of"],
            "profile": who,
            "risk": risk_of(client_id, who["drawdown_limit"]),
            "holdings": holdings,
            "tilts": tilts(),
            "excluded": list(me.get("excluded_classes") or []),
        }
    }


def _for(role: Optional[str], out: Dict[str, Any]) -> Dict[str, Any]:
    """A client never sees a blocked action (its reason stays with the RM, §9)."""
    from people import auth

    seen = auth.role_for(role)
    if seen == "client":
        out = {**out, "actions": [a for a in out["actions"] if a["check"]["status"] != "BLOCK"]}
    return {**out, "role": seen or "rm"}


@op
def allocate(case: dict, method: str = "A", assumptions: dict = None, role: str = None) -> dict:
    """The three buckets, their targets and gaps, the fill, the rebalance, the goals and the checked actions."""
    return {"allocation": _for(role, _engine.allocate(case, method, assumptions))}


@op
def example(method: str = None, assumptions: dict = None, role: str = None) -> dict:
    """The worked example of the BRD (§11, K-7F3A): the same numbers every time, from data/allocation_example.json."""
    case = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    out = _engine.allocate(case, _method(method), _assumptions(assumptions))
    return {"allocation": {**_for(role, out), "example": {"id": case["id"], "note": case["note"]}}}


@op
def tilt(asset_class: str = None, stance: str = None, view_id: str = None, reason: str = "", by: str = None) -> dict:
    """A CIO's Tăng / Trung lập / Giảm on a class, from an approved view: it replaces that view's earlier tilt on the
    class; neutral takes it away. The model moves ±2 points per tilt, ±5 at most (allocation._model)."""
    from control import audit, db, roles
    from views import store as views

    u = roles.require(by, "cio")
    if asset_class not in _model.CLASSES or asset_class == "crypto":
        raise BadRequest(f"asset_class là một trong {', '.join(c for c in _model.CLASSES if c != 'crypto')}")
    if stance not in _model.STANCES:
        raise BadRequest(f"stance là một trong {', '.join(_model.STANCES)}")
    view = next((v for v in views.approved() if v["id"] == view_id), None)
    if view is None:
        raise BadRequest("Nghiêng mô hình cần một nhận định đã duyệt (view_id)")
    kept = [t for t in tilts() if not (t["view_id"] == view_id and t["asset_class"] == asset_class)]
    if stance != "neutral":
        kept.append(
            {
                "asset_class": asset_class,
                "stance": stance,
                "view_id": view_id,
                "view": str((view.get("current") or {}).get("summary") or view_id)[:160],
                "reason": str(reason or "")[:300],
                "by": u["id"],
                "at": date.fromisoformat(fixtures.market()["as_of"]).isoformat(),
            }
        )
    store.put_result(*TILTS, kept)
    with db.tx() as con:
        audit.append(con, u["id"], "allocation.tilt", view_id, {"asset_class": asset_class, "stance": stance})
    return {"tilts": kept, "model": {lv: _model.tilted(lv, kept) for lv in range(1, 6)}}


@op
def tilt_list() -> dict:
    """The tilts in force, the classes a CIO may tilt and the model each level gets from them."""
    kept = tilts()
    classes = [{"id": c, "label": _model.LABELS[c]} for c in _model.CLASSES if c != "crypto"]
    stances = [{"id": k, "label": v} for k, v in _model.STANCE_LABELS.items()]
    model = {lv: _model.tilted(lv, kept) for lv in range(1, 6)}
    return {"tilts": kept, "classes": classes, "stances": stances, "model": model}


@op
def send(client_id: str, allocation: dict, by: str = None) -> dict:
    """The actions an RM sends to the review queue: the ones a client may see (never a blocked one), with the summary
    of the three buckets."""
    from control import roles

    u = roles.require(by, "rm", "cio")
    shown = [a for a in allocation["actions"] if a["check"]["status"] != "BLOCK"]
    if not shown:
        raise BadRequest("Không có hành động nào để gửi")
    liq, leg, ret = allocation["liquidity"], allocation["legacy"], allocation["retirement"]
    summary = [
        {"label": "Thanh khoản", "value": f"cần {vnd(liq['target'])}, đang có {vnd(liq['have'])}"},
        {"label": "Di sản", "value": f"thiếu {vnd(leg['gap'])}–{vnd(leg['gap_high'])}" if leg["gap"] else "đủ"},
        {"label": "Tăng trưởng", "value": f"cần {ret['required']:.1%}/năm, mô hình {allocation['growth']['expected']:.1%}"},
        {"label": "Cách tính", "value": allocation["method_label"]},
    ]
    title = f"Phân bổ ba giỏ – {allocation['client']['name']}"
    item = store.propose(
        client_id,
        "allocation",
        title,
        {
            "option": {
                "id": "allocation",
                "title": title,
                "actions": [f"{a['what']}" + (f" ({_amount(a)})" if a.get("amount") else "") for a in shown],
            },
            "summary": summary,
            "warnings": sorted({r for a in shown if a["check"]["status"] == "WARN" for r in a["check"]["reasons"]}),
            "by": u["id"],
        },
    )
    return {"review_id": item, "actions": len(shown)}


def _amount(a: Dict[str, Any]) -> str:
    return f"{vnd(a['amount'])}–{vnd(a['amount_high'])}" if a.get("amount_high") else vnd(a["amount"])
