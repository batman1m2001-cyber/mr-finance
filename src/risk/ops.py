"""The risk test's steps: what the client's data says, the next question or the result."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict

from operonx import op

from risk import _bank
from wealth import fixtures, store

RISKY = ("stock", "crypto")


@op
def read_request(item: dict = None) -> dict:
    """``{"client_id", "answers": {question: option}}``."""
    item = item or {}
    client_id = str(item.get("client_id") or "")
    if client_id not in fixtures.client_ids(members=True):
        raise ValueError(f"no client {client_id!r}")
    answers = item.get("answers") or {}
    if not isinstance(answers, dict):
        raise ValueError("answers is an object: {question: option}")
    return {"client_id": client_id, "answers": {str(k): str(v) for k, v in answers.items()}}


@op
def context(client_id: str, holdings: list, transactions: list) -> dict:
    """What the client's own data says about how much risk they can carry."""
    c = fixtures.client(client_id)
    assets = sum(h["value"] for h in holdings if h["kind"] == "asset")
    debt = sum(h["value"] for h in holdings if h["kind"] == "liability")
    invested = sum(
        h["value"] for h in holdings if h["kind"] == "asset" and h["class"] in ("stock", "fund", "bond", "crypto")
    )
    liquid = sum(
        h["value"]
        for h in holdings
        if h["kind"] == "asset" and (h["class"] in ("cash", "deposit") or (h["class"] == "fund" and h["liquid"]))
    )
    risky = sum(
        h["value"]
        for h in holdings
        if h["kind"] == "asset"
        and (h["class"] in RISKY or (h["class"] == "fund" and h["detail"].get("fund_type") == "equity"))
    )
    payments = sum(h["detail"].get("monthly_payment") or 0 for h in holdings if h["kind"] == "liability")
    extra_income = sum(i.get("amount", 0) for i in store.profile(client_id, "income"))
    income = (c.get("income_monthly") or 0) + extra_income
    dependents = len(c.get("dependents", [])) + len(store.profile(client_id, "dependent"))
    ctx: Dict[str, Any] = {
        "age": c["age"],
        "net_worth": assets - debt,
        "portfolio": invested or assets * 0.2,
        "liquidity_months": liquid / (c.get("spending_monthly") or 1),
        "debt_service_ratio": payments / income if income else 0.0,
        "leverage": debt / assets if assets else 0.0,
        "dependents": dependents,
        "owns_business": any(h["class"] == "business" for h in holdings),
        "pension": any(t.get("category") == "pension" for t in transactions),
        "risky_share": risky / assets if assets else 0.0,
        "behaviour": c.get("behaviour", []),
    }
    return {"ctx": ctx}


@op
def next_step(answers: dict, ctx: dict) -> dict:
    """The next question on this client's path, or done."""
    qid = _bank.next_id(answers, ctx)
    return {"done": qid is None, "qid": qid or ""}


@op
def ask(qid: str, answers: dict, ctx: dict) -> dict:
    """The question, as this client sees it (their own portfolio in the drop question)."""
    answered = len(_bank.path(answers, ctx))
    return {"reply": {"question": _bank.question(qid, ctx, answered), "answered": answered}}


@op
def result(client_id: str, answers: dict, ctx: dict) -> dict:
    """Tolerance and capacity, the profile (the lower of the two), the persona, what does not add
    up, and when to take the test again. Kept: the dashboard measures risk against it."""
    tol = _bank.tolerance(answers, ctx)
    cap, why = _bank.capacity(ctx, answers)
    tol_level, cap_level = _bank.level_of(tol), _bank.level_of(cap)
    gap = _bank.says_vs_does(tol_level, ctx.get("behaviour", []))
    # what the client did weighs more than what they say: a gap lowers the tolerance one level
    acts = max(1, tol_level - 1) if gap else tol_level
    profile = _bank.PROFILES[min(acts, cap_level) - 1]
    warnings = []
    if tol_level > cap_level:
        warnings.append(
            f"Anh/chị muốn rủi ro mức {_bank.PROFILES[tol_level - 1]['name']}, nhưng khả năng chịu rủi ro chỉ ở "
            f"mức {_bank.PROFILES[cap_level - 1]['name']}: hồ sơ được đặt theo mức thấp hơn."
        )
    elif cap_level > tol_level + 1:
        warnings.append(
            f"Khả năng chịu rủi ro ({_bank.PROFILES[cap_level - 1]['name']}) cao hơn nhiều so với mức anh/chị "
            f"chọn: có thể đang để quá nhiều tiền nhàn rỗi."
        )
    if gap:
        warnings.append(gap + " Hồ sơ được hạ một mức.")
    today = date.fromisoformat(fixtures.market()["as_of"])
    again = date(today.year + (today.month + 5) // 12, (today.month + 5) % 12 + 1, min(today.day, 28))
    persona = _bank.persona(ctx)
    out = {
        "client_id": client_id,
        "taken": today.isoformat(),
        "questions": len(_bank.path(answers, ctx)),
        "tolerance": tol,
        "capacity": cap,
        "tolerance_level": tol_level,
        "capacity_level": cap_level,
        "tolerance_name": _bank.PROFILES[tol_level - 1]["name"],
        "capacity_name": _bank.PROFILES[cap_level - 1]["name"],
        "profile": profile,
        "drawdown_limit": profile["drawdown_limit"],
        "persona": persona,
        "persona_text": _bank.PERSONAS[persona],
        "capacity_reasons": why,
        "warnings": warnings,
        "retest": {
            "date": again.isoformat(),
            "when": [
                "Sau 6 tháng",
                "Khi có thay đổi lớn: sinh con, nghỉ hưu, bán nhà",
                "Khi thị trường biến động mạnh (VN-Index ±10% trong một tháng)",
            ],
        },
    }
    store.put_result(client_id, "risk", out)
    return {"reply": {"result": out}}


@op
def reply(asked: dict = None, done: dict = None) -> dict:
    """Whichever came out: a question to answer, or the result."""
    return {"reply": asked or done}
