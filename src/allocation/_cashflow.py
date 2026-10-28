"""The cash-flow table of the next H years and the three liquidity targets (ASSET_ALLOCATION_BRD §6.1).

Month by month from the month after ``as_of``: income (all of it, and the certain part), living costs, debt
service, and every dated outflow of the client's ``events``. Three targets come out of it:

- A (no income): every recurring cost + every dated outflow of the H years;
- C (certain income only): |the cumulative line's trough| with certain income + a buffer of N months of costs;
- B (full income): |the trough| with all income + the same buffer.

Formulas only; the same input gives the same table.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

METHODS = ("A", "B", "C")
METHOD_LABELS = {
    "A": "Không tính thu nhập",
    "B": "Tính đủ thu nhập",
    "C": "Chỉ tính thu nhập chắc chắn",
}


def months_after(as_of: date, n: int) -> List[str]:
    """The ``n`` months after ``as_of``'s month, as ``YYYY-MM``."""
    out, y, m = [], as_of.year, as_of.month
    for _ in range(n):
        m += 1
        if m > 12:
            y, m = y + 1, 1
        out.append(f"{y}-{m:02d}")
    return out


def debt_service(loans: List[Dict[str, Any]]) -> float:
    """What the loans cost a month: the contract's payment, or the interest when it has none (interest only)."""
    total = 0.0
    for loan in loans:
        d = loan.get("detail") or {}
        pay = float(d.get("monthly_payment") or 0)
        total += pay if pay > 0 else loan["value"] * float(d.get("rate") or 0) / 12
    return total


def principal_due(loans: List[Dict[str, Any]], months: List[str]) -> List[Dict[str, Any]]:
    """An interest-only loan's balance, due in its end month when that month is in the table."""
    out = []
    for loan in loans:
        d = loan.get("detail") or {}
        end = str(d.get("end") or "")[:7]
        if not (d.get("monthly_payment") or 0) and end in months:
            out.append({"month": end, "amount": loan["value"], "label": f"Trả gốc {loan.get('name') or 'khoản vay'}"})
    return out


def table(
    profile: Dict[str, Any],
    loans: List[Dict[str, Any]],
    as_of: date,
    years: int = 3,
    buffer_months: int = 6,
    rate_shock: float = 0.01,
) -> Dict[str, Any]:
    """The H-year table, by month and by year, and the targets A, B, C."""
    months = months_after(as_of, 12 * years)
    income = float(profile.get("income_monthly") or 0)
    certain = float(profile.get("income_certain_monthly") if profile.get("income_certain_monthly") is not None else income)
    living = float(profile.get("spending_monthly") or 0)
    service = debt_service(loans)
    recurring = living + service
    dated: List[Dict[str, Any]] = []
    for e in profile.get("events") or []:
        month = str(e.get("date") or "")[:7]
        if e.get("direction") == "out" and month in months:
            dated.append({"month": month, "date": e["date"], "amount": float(e["amount"]), "label": e.get("label", "")})
    dated += [{**p, "date": f"{p['month']}-28"} for p in principal_due(loans, months)]
    dated.sort(key=lambda d: d["date"])
    by_month = {m: sum(d["amount"] for d in dated if d["month"] == m) for m in months}

    rows, cum_full, cum_certain = [], 0.0, 0.0
    for i, m in enumerate(months):
        out = by_month[m]
        cum_full += income - recurring - out
        cum_certain += certain - recurring - out
        rows.append({"month": m, "dated": out, "cum": cum_full, "cum_certain": cum_certain, "i": i})
    trough = min(rows, key=lambda r: r["cum"])
    trough_c = min(rows, key=lambda r: r["cum_certain"])
    buffer = buffer_months * recurring
    total_dated = sum(d["amount"] for d in dated)
    targets = {
        "A": recurring * len(months) + total_dated,
        "B": max(0.0, -trough["cum"]) + buffer,
        "C": max(0.0, -trough_c["cum_certain"]) + buffer,
    }
    yearly = []
    for y in range(years):
        part = months[12 * y : 12 * (y + 1)]
        out = sum(by_month[m] for m in part)
        yearly.append(
            {
                "year": y + 1,
                "from": part[0],
                "to": part[-1],
                "income": income * 12,
                "recurring": recurring * 12,
                "dated": out,
                "net": (income - recurring) * 12 - out,
            }
        )
    floating = [loan for loan in loans if (loan.get("detail") or {}).get("rate_type") == "floating"]
    shock_month = sum(loan["value"] for loan in floating) * rate_shock / 12
    return {
        "months": [{"month": r["month"], "cum": r["cum"], "cum_certain": r["cum_certain"], "dated": r["dated"]} for r in rows],
        "years": yearly,
        "dated": dated,
        "income_monthly": income,
        "income_certain_monthly": certain,
        "living_monthly": living,
        "debt_service_monthly": service,
        "recurring_monthly": recurring,
        "buffer": buffer,
        "buffer_months": buffer_months,
        "trough": {"month": trough["month"], "cum": trough["cum"]},
        "trough_certain": {"month": trough_c["month"], "cum": trough_c["cum_certain"]},
        "targets": targets,
        "rate_shock": {"pp": rate_shock, "monthly": shock_month, "total": shock_month * len(months)},
        "horizon_years": years,
    }


def next_outflow(cash: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The first dated outflow of the table."""
    return cash["dated"][0] if cash["dated"] else None
