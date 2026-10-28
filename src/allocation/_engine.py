"""Three buckets, their targets, and the actions that move a client toward them (ASSET_ALLOCATION_BRD §5–§9).

``allocate(case, method, assumptions)`` is formulas only: the same case gives the same answer. A case is
``{as_of, profile, risk, holdings, tilts, excluded, overrides?}`` — the household's consolidated holdings, its profile (income,
the certain part of it, spending, dated events, dependents, age, retirement age, the legacy it wants to leave), the
risk level (from the test, or simulated from the drawdown the file states), the CIO's tilts in force (read as ±2-point tilts or as Black–Litterman views, ``model_method``) and the RM's
bucket overrides ({holding key: {bucket, reason, …}}, §5).

Order (§8.1): fill Liquidity to its target, then rebalance what is left of Growth to the tilted model.
"""

from __future__ import annotations

import math
import re
from datetime import date
from typing import Any, Dict, List, Optional

from allocation import _cashflow, _model
from wealth.money import TY, pct, vnd

BUCKETS = {"liquidity": "Thanh khoản", "legacy": "Di sản", "growth": "Tăng trưởng"}
LIQUID = ("cash", "deposit")
LEGACY = ("real_estate", "business", "insurance")
GROWTH = ("stock", "fund", "bond", "gold", "crypto")
DEBT = ("loan", "card")

ASSUMPTIONS = {
    "horizon_years": 3,
    "buffer_months": 6,
    "inflation": 0.04,
    "retirement_age": 60,
    "legacy_wish": None,
    "survivor_share": 2 / 3,
    "child_until": 22,
    "university_per_year": 0.5 * TY,
    "university_years": 4,
    "university_from": 18,
    "withdraw_multiple": 25,
    "rate_shock": 0.01,
}
LABELS = {
    "horizon_years": "Số năm dòng tiền (H)",
    "buffer_months": "Đệm (tháng chi)",
    "inflation": "Lạm phát mỗi năm",
    "retirement_age": "Tuổi nghỉ hưu",
    "legacy_wish": "Mong muốn để lại",
    "survivor_share": "Chi tiêu khi không còn chủ hộ (phần chi hiện tại)",
}


def settings(profile: Dict[str, Any], given: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """The defaults, the profile's own answers over them, the RM's edits over both (only known keys)."""
    out = dict(ASSUMPTIONS)
    for key in ("retirement_age", "legacy_wish"):
        if profile.get(key) is not None:
            out[key] = profile[key]
    for key, value in (given or {}).items():
        if key in ASSUMPTIONS and value is not None and value != "":
            out[key] = value if key == "legacy_wish" else type(ASSUMPTIONS[key] if ASSUMPTIONS[key] is not None else 0.0)(float(value))
    out["horizon_years"] = max(3, min(5, int(out["horizon_years"])))
    out["buffer_months"] = max(0, min(24, int(out["buffer_months"])))
    if out["legacy_wish"] is not None:
        out["legacy_wish"] = float(out["legacy_wish"])
    return out


def bucket_of(holding: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """The bucket a holding counts in: the RM's override for it when there is one (§5), else by its class."""
    cls = holding["class"]
    if holding["kind"] != "asset":
        return None
    moved = (overrides or {}).get(holding.get("key"))
    if moved:
        return moved["bucket"]
    if cls in LIQUID:
        return "liquidity"
    if cls in LEGACY:
        return "legacy"
    return "growth"


def _collateral(loan: Dict[str, Any], holdings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    ident = (loan.get("detail") or {}).get("collateral")
    if not ident:
        return None
    return next((h for h in holdings if h["kind"] == "asset" and str(h.get("key", "")).endswith(f":{ident}")), None)


# ── Legacy (§6.2) ───────────────────────────────────────────────────────


def _given_name(name: str) -> str:
    words = (name or "").split()
    return " ".join(words[-2:]) if len(words) >= 3 else (words[-1] if words else "")


def legacy(case: Dict[str, Any], s: Dict[str, Any], cash: Dict[str, Any], loans: List[Dict[str, Any]]) -> Dict[str, Any]:
    p, as_of = case["profile"], _date(case["as_of"])
    holdings = case["holdings"]
    debt = sum(h["value"] for h in loans)
    yearly = cash["recurring_monthly"] * 12
    family = yearly * s["survivor_share"]
    kids = [d for d in p.get("dependents") or [] if d.get("birth_year")]
    youngest = max((d["birth_year"] for d in kids), default=None)
    years = max(0, youngest + s["child_until"] - as_of.year) if youngest else 0
    school_events = [
        e for e in p.get("events") or [] if e.get("direction") == "out" and e.get("category") == "school" and str(e["date"]) >= str(as_of)
    ]
    school = sum(float(e["amount"]) for e in school_events)
    university = 0.0
    uni_kids = []
    for d in kids:
        age = as_of.year - d["birth_year"]
        name = _given_name(d.get("name", ""))
        planned = name and any(re.search(rf"(?<!\w){re.escape(name)}(?!\w)", e.get("label", "")) for e in school_events)
        if age < s["university_from"] and not planned:
            university += s["university_per_year"] * s["university_years"]
            uni_kids.append(d.get("name") or "Con")
    floor_rows = [
        {"label": "Nợ còn lại", "how": "", "amount": debt},
        {
            "label": f"Chi tiêu gia đình đến khi con nhỏ {s['child_until']} tuổi" + (f" ({youngest + s['child_until']})" if youngest else ""),
            "how": f"{vnd(yearly)} × {_frac(s['survivor_share'])} = {vnd(family)}/năm × {years} năm",
            "amount": family * years,
        },
        {
            "label": "Học phí còn lại",
            "how": " + ".join(
                x
                for x in (
                    f"đã lên lịch {vnd(school)}" if school else "",
                    f"đại học {len(uni_kids)} con × {s['university_years']} × {vnd(s['university_per_year'])}" if uni_kids else "",
                )
                if x
            ),
            "amount": school + university,
        },
    ]
    floor = sum(r["amount"] for r in floor_rows)
    wish = s["legacy_wish"]
    target = max(wish or 0.0, floor)
    moved = case.get("overrides")
    assets = [h for h in holdings if bucket_of(h, moved) == "legacy"]
    secured = sum(h["value"] for h in loans if (c := _collateral(h, holdings)) and bucket_of(c, moved) == "legacy")
    insured = sum(
        float((h.get("detail") or {}).get("sum_assured") or h["value"])
        for h in assets
        if h["class"] == "insurance" and (h.get("detail") or {}).get("beneficiary")
    )
    held = sum(h["value"] for h in assets if h["class"] != "insurance")
    estate = sum(h["value"] for h in assets if h["class"] == "real_estate")
    drop = _model.data().get("real_estate_drop")
    have = held - secured + insured
    low = have - estate * drop["drop"] if drop else None
    return {
        "floor": floor,
        "floor_rows": floor_rows,
        "wish": wish,
        "target": target,
        "have": have,
        "have_low": low,
        "drop": drop,
        "insured": insured,
        "secured": secured,
        "gap": max(0.0, target - have),
        "gap_high": max(0.0, target - low) if low is not None else None,
        "fill_with": "Bảo hiểm có người thụ hưởng hoặc tiết kiệm; không bán tài sản Di sản",
    }


# ── Growth target: the return the long-term goal needs (§6.3) ────────────


def _annuity(r: float, m: int) -> float:
    return m if r == 0 else ((1 + r) ** m - 1) / r


def _savings(case: Dict[str, Any], cash: Dict[str, Any], s: Dict[str, Any], n: int) -> float:
    """The average yearly saving of years H+1..n: all income − recurring costs − that year's dated outflows."""
    H = s["horizon_years"]
    if n <= H:
        return 0.0
    months = _cashflow.months_after(_date(case["as_of"]), 12 * n)
    out = {m: 0.0 for m in months}
    for e in case["profile"].get("events") or []:
        m = str(e.get("date") or "")[:7]
        if e.get("direction") == "out" and m in out:
            out[m] += float(e["amount"])
    net = (cash["income_monthly"] - cash["recurring_monthly"]) * 12
    years = [net - sum(out[m] for m in months[12 * y : 12 * (y + 1)]) for y in range(H, n)]
    return sum(years) / len(years)


def _reach(g1: float, saving: float, r: float, n: int, m: int) -> float:
    return g1 * (1 + r) ** n + saving * _annuity(r, m)


def retirement(case: Dict[str, Any], s: Dict[str, Any], cash: Dict[str, Any], g1: float, expected: float) -> Dict[str, Any]:
    age = int(case["profile"].get("age") or 0)
    spend = cash["recurring_monthly"] * 12
    H = s["horizon_years"]

    def need(n: int) -> float:
        return spend * (1 + s["inflation"]) ** n * s["withdraw_multiple"]

    def at(n: int, r: float) -> float:
        return _reach(g1, _savings(case, cash, s, n), r, n, max(0, n - H))

    n = int(s["retirement_age"]) - age
    if n <= 0:
        return {"years": 0, "status": "retired", "need": 0.0}
    saving = _savings(case, cash, s, n)
    required = next((k / 1000 for k in range(0, 301) if at(n, k / 1000) >= need(n)), None)
    reach = at(n, expected)
    short = max(0.0, need(n) - reach)
    m = max(0, n - H)
    out = {
        "years": n,
        "year": _date(case["as_of"]).year + n,
        "spend_now": spend,
        "need": need(n),
        "saving_yearly": saving,
        "saving_years": m,
        "required": required,
        "expected": expected,
        "reach": reach,
        "short": short,
        "status": "enough" if required is not None and required <= expected + 1e-9 else "short",
    }
    if out["status"] == "short":
        af = _annuity(expected, m)
        out["extra_monthly"] = short / af / 12 if af else None
        cover = [(d, at(n + d, expected) / need(n + d)) for d in range(1, 11)]
        enough = next((d for d, c in cover if c >= 1), None)
        near = next(((d, c) for d, c in cover if c >= 0.98), None)
        out["delay"] = {"enough": enough, "near": {"years": near[0], "cover": near[1]} if near else None}
    elif required is not None and required < expected - 0.03:
        out["note"] = "Đang chịu rủi ro nhiều hơn mức cần"
    return out


# ── Filling Liquidity (§8.2, §8.3) ───────────────────────────────────────


def ladder(cash: Dict[str, Any], target: float) -> List[Dict[str, Any]]:
    """The Liquidity money laid out by when it is needed, up to the target."""
    rungs = []
    years = cash["years"]
    first = [d for d in cash["dated"] if years[0]["from"] <= d["month"] <= years[0]["to"]]
    rungs.append({"what": "Tiền gửi không kỳ hạn", "when": "Chi 12 tháng tới", "amount": cash["recurring_monthly"] * 12})
    for d in first:
        rungs.append({"what": f"Tiền gửi đáo hạn {_month_before(d['month'])}", "when": d["label"], "amount": d["amount"]})
    for y in years[1:]:
        total = y["recurring"] + y["dated"]
        what = "Tiền gửi 12–18 tháng" if y["year"] == 2 else f"Trái phiếu chính phủ đáo hạn {y['to'][:4]}"
        rungs.append({"what": what, "when": f"Năm {y['year']}", "amount": total})
    left, out = target, []
    for r in rungs:
        take = min(r["amount"], left)
        if take > 0:
            out.append({**r, "amount": take})
        left -= take
    return out


def fill(
    case: Dict[str, Any],
    cash: Dict[str, Any],
    target: float,
    have: float,
    growth: Dict[str, float],
    model: Dict[str, Any],
    loans: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Wait, sell or borrow to bring Liquidity to its target; the sells come from the most overweight class first."""
    cfg = _model.data()
    shortfall = max(0.0, target - have)
    excess = max(0.0, have - target)
    g0 = sum(growth.values())  # the excess is already in it, as cash waiting to be invested
    surplus = cash["income_monthly"] - cash["recurring_monthly"]
    first = _cashflow.next_outflow(cash)
    months_left = _months_between(case["as_of"], first["month"]) if first else 12
    wait_months = math.ceil(shortfall / surplus) if surplus > 0 and shortfall > 0 else None
    wait_ok = bool(shortfall) and wait_months is not None and wait_months <= months_left
    after = g0 - shortfall
    over = {
        c: growth.get(c, 0.0) - model["classes"][c]["target"] * after
        for c in model["classes"]
        if growth.get(c, 0.0) - model["classes"][c]["target"] * after > 0
    }
    sells: Dict[str, float] = {}
    borrow = 0.0
    remaining = 0.0 if wait_ok else shortfall
    for c in sorted(over, key=lambda c: -over[c]):
        take = min(over[c], remaining)
        if take > 0:
            sells[c] = take
            remaining -= take
    rate = cfg["borrow"]["rate"]
    assets = sum(h["value"] for h in case["holdings"] if h["kind"] == "asset")
    debts = sum(h["value"] for h in loans)

    def borrow_passes(amount: float) -> Dict[str, Any]:
        ratio = (debts + amount) / (assets + amount) if assets else 1.0
        service = (_cashflow.debt_service(loans) + amount * rate / 12) / cash["income_certain_monthly"] if cash["income_certain_monthly"] else math.inf
        return {
            "debt_to_assets": ratio,
            "service_to_certain": service,
            "ok": ratio <= cfg["borrow"]["debt_to_assets"] and service <= cfg["borrow"]["service_to_certain_income"],
        }

    if remaining > 0:
        test = borrow_passes(remaining)
        if test["ok"]:
            borrow, remaining = remaining, 0.0
        else:
            left = {c: growth.get(c, 0.0) - sells.get(c, 0.0) for c in growth}
            pool = sum(left.values())
            for c, v in left.items():
                take = min(v, remaining * v / pool) if pool else 0.0
                sells[c] = sells.get(c, 0.0) + take
            remaining = max(0.0, remaining - min(pool, remaining))
    sold = sum(sells.values())
    chosen = "wait" if wait_ok else "borrow" if borrow and not sold else "sell" if sold else "none"
    test = borrow_passes(shortfall) if shortfall else None
    sell_cost = shortfall * cfg["sell_tax"]
    options = [
        {
            "id": "wait",
            "label": "Chờ thu nhập",
            "cost": f"{wait_months} tháng" if wait_months else "—",
            "ok": wait_ok,
            "why": (
                f"Kịp: {wait_months} tháng tích lũy trước khoản chi gần nhất"
                if wait_ok
                else (f"Không kịp: {first['month'][5:]}/{first['month'][:4]} cần {vnd(first['amount'])}" if first else "Không có thu nhập dư")
            ),
        },
        {
            "id": "sell",
            "label": "Bán tài sản Tăng trưởng" + (f" ({', '.join(_model.LABELS[c].lower() for c in sells)})" if sells else ""),
            "cost": f"Thuế {pct(cfg['sell_tax'])} ≈ {vnd(sell_cost)}",
            "ok": chosen == "sell",
            "why": (
                "Có loại tài sản đang vượt mục tiêu" if over else "Không loại nào vượt mục tiêu: bán đều theo tỷ trọng"
            )
            if sold
            else "Không cần",
        },
        {
            "id": "borrow",
            "label": "Vay cầm cố danh mục",
            "cost": f"{pct(rate, digits=0)} ≈ {vnd(shortfall * rate)}/năm",
            "ok": bool(borrow),
            "why": (
                "Không: có loại tài sản vượt mục tiêu để bán"
                if over and sold
                else ("Vay vẫn qua các ngưỡng" if borrow else "Không: vượt ngưỡng nợ" if test and not test["ok"] else "Không cần")
            ),
            "test": test,
        },
    ]
    return {
        "shortfall": shortfall,
        "excess": excess,
        "growth_before": g0,
        "sells": sells,
        "borrow": borrow,
        "wait_months": wait_months if wait_ok else None,
        "still_short": remaining,
        "chosen": chosen,
        "options": options,
    }


# ── Rebalancing Growth (§8.4) ────────────────────────────────────────────


def rebalance(g1: Dict[str, float], model: Dict[str, Any]) -> Dict[str, Any]:
    """Each class to its tilted target on the Growth that is left; a gap under the band is no trade; what the trades
    leave over is cash waiting to be invested."""
    band = _model.data()["band"]
    total = sum(g1.values())
    rows, after = [], {}
    for c, m in model["classes"].items():
        if c == "cash":
            continue
        now = g1.get(c, 0.0)
        goal = m["target"] * total
        gap = (now / total - m["target"]) if total else 0.0
        after[c] = goal if abs(gap) >= band else now
    after["cash"] = total - sum(after.values())
    for c, m in model["classes"].items():
        now = g1.get(c, 0.0)
        if not now and not after[c] and not m["target"]:
            continue
        rows.append(
            {
                "class": c,
                "label": m["label"],
                "now": now,
                "now_pct": now / total if total else 0.0,
                "target_pct": m["target"],
                "base_pct": m["base"],
                "tilt": m["tilt"],
                "low": m["low"],
                "high": m["high"],
                "target": m["target"] * total,
                "after": after[c],
                "trade": after[c] - now,
                "views": m["views"],
            }
        )
    return {"total": total, "rows": rows, "after": after}


def worst(amounts: Dict[str, float]) -> Dict[str, float]:
    shock = _model.data()["worst_case"]
    total = sum(amounts.values())
    loss = sum(v * -shock.get(c, shock["equity"]) for c, v in amounts.items())
    return {"loss": loss, "total": total, "share": loss / total if total else 0.0}


# ── Existing loans (§8.2) ────────────────────────────────────────────────


def existing_loans(case, loans, s, expected, liquidity_before, liquidity_after, target) -> List[Dict[str, Any]]:
    out = []
    for loan in loans:
        d = loan.get("detail") or {}
        rate = float(d.get("rate") or 0)
        floating = d.get("rate_type") == "floating"
        coll = _collateral(loan, case["holdings"])
        can_prepay = liquidity_after - loan["value"] >= target and rate > expected
        if can_prepay:
            advice = "Có thể trả trước: Thanh khoản vẫn đủ và lãi vay cao hơn lợi nhuận kỳ vọng"
        elif liquidity_before < target:
            advice = "Chưa trả trước: giỏ Thanh khoản đang thiếu"
        elif liquidity_after - loan["value"] < target:
            advice = "Chưa trả trước: trả xong thì Thanh khoản thiếu"
        else:
            advice = "Chưa trả trước: lãi vay thấp hơn lợi nhuận kỳ vọng"
        out.append(
            {
                "name": loan.get("name"),
                "class": loan["class"],
                "value": loan["value"],
                "rate": rate,
                "floating": floating,
                "shock_monthly": loan["value"] * s["rate_shock"] / 12 if floating else 0.0,
                "ltv": loan["value"] / coll["value"] if coll and coll["value"] else None,
                "collateral": coll.get("name") if coll else None,
                "prepay": can_prepay,
                "advice": advice + ("; xem chuyển sang lãi cố định" if floating else ""),
            }
        )
    return out


# ── the whole picture ────────────────────────────────────────────────────


def allocate(case: Dict[str, Any], method: str = "A", assumptions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if method not in _cashflow.METHODS:
        raise ValueError(f"method is one of {', '.join(_cashflow.METHODS)}, not {method!r}")
    p, risk, holdings = case["profile"], case["risk"], case["holdings"]
    s = settings(p, assumptions)
    level = int(risk["level"])
    as_of = _date(case["as_of"])
    loans = [h for h in holdings if h["kind"] == "liability" and h["class"] in DEBT]
    cash = _cashflow.table(p, loans, as_of, s["horizon_years"], s["buffer_months"], s["rate_shock"])
    target = cash["targets"][method]

    buckets = {b: [] for b in BUCKETS}
    for h in holdings:
        b = bucket_of(h, case.get("overrides"))
        if b:
            buckets[b].append(h)
    sums = {b: sum(h["value"] for h in hs) for b, hs in buckets.items()}
    have = sums["liquidity"]
    growth: Dict[str, float] = {}
    for h in buckets["growth"]:
        c = _model.model_class(h, level)
        growth[c] = growth.get(c, 0.0) + h["value"]
    model = _model.model_for(level, case.get("tilts") or [], case.get("model_method") or "tilt")
    excess = max(0.0, have - target)
    if excess:
        growth["cash"] = growth.get("cash", 0.0) + excess
    filled = fill(case, cash, target, have, growth, model, loans)
    g1 = {c: growth.get(c, 0.0) - filled["sells"].get(c, 0.0) for c in set(growth) | set(model["classes"])}
    re_ = rebalance(g1, model)
    expected = _model.expected_return(model["classes"])
    worst_before = worst({c: v for c, v in growth.items()})
    worst_after = worst({c: re_["after"][c] for c in re_["after"]})
    liquidity_after = have - excess + filled["shortfall"] - filled["still_short"]
    goal = retirement(case, s, cash, re_["total"], expected)
    leg = legacy(case, s, cash, loans)
    loan_rows = existing_loans(case, loans, s, expected, have, liquidity_after, target)

    assets = sum(h["value"] for h in holdings if h["kind"] == "asset")
    debts = sum(h["value"] for h in holdings if h["kind"] == "liability")
    concentrated = [h for h in holdings if h["kind"] == "asset" and assets and h["value"] / assets > _model.data()["concentration"]]
    out = {
        "as_of": case["as_of"],
        "client": {k: p.get(k) for k in ("client_id", "name", "age", "occupation")},
        "risk": {**risk, "drawdown_limit": p.get("drawdown_limit")},
        "method": method,
        "method_label": _cashflow.METHOD_LABELS[method],
        "methods": _cashflow.METHOD_LABELS,
        "assumptions": s,
        "assumption_labels": LABELS,
        "buckets": {
            b: {
                "label": BUCKETS[b],
                "value": sums[b],
                "holdings": [
                    {
                        "key": h.get("key"),
                        "name": h.get("name"),
                        "class": h["class"],
                        "value": h["value"],
                        "owner_name": h.get("owner_name"),
                        "moved": (case.get("overrides") or {}).get(h.get("key")),
                    }
                    for h in hs
                ],
            }
            for b, hs in buckets.items()
        },
        "loans": {"value": debts, "items": [{"name": h.get("name"), "class": h["class"], "value": h["value"]} for h in loans]},
        "reconcile": {"assets": assets, "debts": debts, "net_worth": assets - debts, "buckets": sum(sums.values())},
        "cashflow": cash,
        "liquidity": {
            "target": target,
            "have": have,
            "short": max(0.0, target - have),
            "excess": excess,
            "targets": cash["targets"],
            "ladder": ladder(cash, target),
            "after": liquidity_after,
        },
        "fill": filled,
        "model": model,
        "growth": {
            "before": growth,
            "total_before": sum(growth.values()),
            "rebalance": re_,
            "expected": expected,
            "worst_before": worst_before,
            "worst_after": worst_after,
        },
        "legacy": leg,
        "retirement": goal,
        "existing_loans": loan_rows,
        "concentrated": [{"name": h.get("name"), "share": h["value"] / assets} for h in concentrated],
    }
    out["eleven"] = _model.eleven(holdings, buckets["growth"], model, re_["total"])
    out["actions"] = actions(case, out)
    return out


def actions(case: Dict[str, Any], a: Dict[str, Any]) -> List[Dict[str, Any]]:
    from allocation import _checks

    rows: List[Dict[str, Any]] = []
    liq, filled, H = a["liquidity"], a["fill"], a["assumptions"]["horizon_years"]
    views = sorted({v for c in a["model"]["classes"].values() for v in c["views"]})
    if filled["shortfall"]:
        if filled["chosen"] == "wait":
            what = f"Giữ thu nhập dư {filled['wait_months']} tháng vào tiền gửi theo bậc thang"
        elif filled["chosen"] == "borrow":
            what = "Vay cầm cố danh mục, xếp bậc thang tiền gửi và trái phiếu chính phủ"
        else:
            # cash waiting in Growth (a money fund, the excess) is moved, not sold
            sold = ", ".join(_model.LABELS[c].lower() for c in filled["sells"] if c != "cash")
            parts = ([f"Bán {sold}"] if sold else []) + (["dùng tiền chờ đầu tư"] if "cash" in filled["sells"] else [])
            what = ", ".join(parts)[:1].upper() + ", ".join(parts)[1:] + ", xếp bậc thang tiền gửi và trái phiếu chính phủ"
        income_note = "; thu nhập chủ yếu không chắc chắn" if a["cashflow"]["income_certain_monthly"] < a["cashflow"]["income_monthly"] / 2 else ""
        rows.append(
            {
                "bucket": "liquidity",
                "kind": filled["chosen"],
                "what": what,
                "amount": filled["shortfall"],
                "why": f"Dòng tiền {H} năm cần {vnd(liq['target'])}, có {vnd(liq['have'])}{income_note}",
                "moves": {c: -v for c, v in filled["sells"].items()},
            }
        )
    elif liq["excess"]:
        rows.append(
            {
                "bucket": "liquidity",
                "kind": "move",
                "what": "Chuyển tiền dư sang giỏ Tăng trưởng (tiền chờ đầu tư)",
                "amount": liq["excess"],
                "why": f"Dòng tiền {H} năm cần {vnd(liq['target'])}, có {vnd(liq['have'])}",
                "moves": {"cash": liq["excess"]},
            }
        )
    order = {"equity": 0, "bond": 1, "gold": 2, "crypto": 3}
    for r in sorted(a["growth"]["rebalance"]["rows"], key=lambda r: order.get(r["class"], 9)):
        if r["class"] == "cash" or abs(r["trade"]) < 1:
            continue
        gap = round((r["now_pct"] - r["target_pct"]) * 100)
        sell = r["trade"] < 0
        verb = ("Bán thêm " if sell and r["class"] in filled["sells"] else "Bán " if sell else "Mua thêm ") + r["label"].lower()
        if r["class"] == "gold" and sell:
            verb = "Giảm vàng"
        if r["class"] == "bond" and not sell:
            verb = "Mua trái phiếu kỳ hạn ngắn"
        view = ", ".join(r["views"])
        rows.append(
            {
                "bucket": "growth",
                "kind": "sell" if sell else "buy",
                "class": r["class"],
                "what": verb,
                "amount": abs(r["trade"]),
                "why": (f"Lệch {gap:+d} điểm so với mô hình đã nghiêng" if r["tilt"] else f"{'Vượt' if gap > 0 else 'Thiếu'} {abs(gap)} điểm")
                + (f" ({view})" if view else ""),
                "view": view or None,
                "moves": {r["class"]: r["trade"]},
            }
        )
    for loan in a["existing_loans"]:
        if loan["class"] != "loan":
            continue
        shock = f"Lãi +1 điểm: +{vnd(loan['shock_monthly'])}/tháng" if loan["floating"] else ""
        rows.append(
            {
                "bucket": "loans",
                "kind": "prepay" if loan["prepay"] else "hold",
                "what": ("Trả trước khoản vay" if loan["prepay"] else "Không vay thêm, chưa trả trước")
                + (", xem lãi cố định" if loan["floating"] else ""),
                "amount": loan["value"] if loan["prepay"] else None,
                "why": "; ".join(x for x in (shock, loan["advice"].split(";")[0]) if x),
                "moves": {"liquidity": -loan["value"]} if loan["prepay"] else {},
            }
        )
    leg = a["legacy"]
    if leg["gap"] or leg.get("gap_high"):
        rows.append(
            {
                "bucket": "legacy",
                "kind": "talk",
                "what": "Trao đổi bảo hiểm có người thụ hưởng",
                "amount": leg["gap"],
                "amount_high": leg.get("gap_high"),
                "why": f"Mục tiêu {vnd(leg['target'])}, có "
                + (f"{vnd(leg['have_low'])}–{vnd(leg['have'])}" if leg.get("have_low") is not None else vnd(leg["have"])),
                "moves": {},
            }
        )
    goal = a["retirement"]
    if goal.get("status") == "short":
        delay = goal["delay"]
        later = (
            f"lùi hưu {delay['near']['years']} năm (đạt {pct(delay['near']['cover'])})"
            if delay.get("near") and delay["near"]["years"] != delay.get("enough")
            else f"lùi hưu {delay['enough']} năm" if delay.get("enough") else None
        )
        rows.append(
            {
                "bucket": "retirement",
                "kind": "talk",
                # saving more is offered only when it fits the income (half of it at most): else the goal is talked over
                "what": f"Trao đổi tiết kiệm thêm {vnd(goal['extra_monthly'])}/tháng" + (f" hoặc {later}" if later else "")
                if goal.get("extra_monthly") and goal["extra_monthly"] <= a["cashflow"]["income_monthly"] / 2
                else "Trao đổi lại mục tiêu hưu: " + (f"{later} hoặc " if later else "") + "giảm chi tiêu khi nghỉ",
                "amount": None,
                "why": f"Thiếu khoảng {vnd(goal['short'])} năm {goal['year']}; lợi nhuận cần {pct(goal['required'] or 0)} > kỳ vọng {pct(goal['expected'])}"
                if goal["required"] is not None
                else f"Thiếu khoảng {vnd(goal['short'])} năm {goal['year']}",
                "moves": {},
            }
        )
    for i, r in enumerate(rows, 1):
        r["n"] = i
        r["bucket_label"] = {**BUCKETS, "loans": "Khoản vay", "retirement": "Mục tiêu hưu"}[r["bucket"]]
        r["check"] = _checks.check(case, a, r)
    a["views_in_force"] = views
    return rows


# ── helpers ──────────────────────────────────────────────────────────────


def _date(x: Any) -> date:
    return x if isinstance(x, date) else date.fromisoformat(str(x)[:10])


def _months_between(as_of: Any, month: str) -> int:
    d = _date(as_of)
    y, m = int(month[:4]), int(month[5:7])
    return (y - d.year) * 12 + (m - d.month) - 1


def _month_before(month: str) -> str:
    y, m = int(month[:4]), int(month[5:7]) - 1
    if m == 0:
        y, m = y - 1, 12
    return f"{m:02d}/{y}"


def _frac(x: float) -> str:
    return "2/3" if abs(x - 2 / 3) < 1e-9 else pct(x, digits=0)
