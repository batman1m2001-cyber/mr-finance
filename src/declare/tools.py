"""The agent's tools: each writes one thing the client told us into their profile (wealth/store).

Amounts are in tỷ or triệu, as people say them; the tools turn them into VND. The client is the
run's ``deps`` (declare/graph.py), so a tool can only ever write for the client in the chat.
"""

from __future__ import annotations

from typing import Optional

from operonx.agents import RunContext, tool

from declare import _rules
from wealth import store
from wealth.money import TR, TY, vnd


def _add(ctx: RunContext, kind: str, data: dict) -> None:
    store.add_profile(ctx.deps, kind, {**data, "via": "chat"})


@tool(idempotent=False)
def declare_property(
    ctx: RunContext,
    name: str,
    location: str,
    value_ty: Optional[float] = None,
    sqm: Optional[float] = None,
    purchase_year: Optional[int] = None,
    purchase_price_ty: Optional[float] = None,
    rental_million_per_month: Optional[float] = None,
) -> str:
    """Record a property the client owns outside our data (a house, an apartment, land).

    Args:
        name: What it is, as the client says it (e.g. "Căn hộ Thảo Điền").
        location: Where it is (district, area, city).
        value_ty: What it is worth today, in tỷ, if the client said.
        sqm: Its size in m², if said.
        purchase_year: The year it was bought, if said.
        purchase_price_ty: What was paid, in tỷ, if said.
        rental_million_per_month: Rent it earns, in triệu per month, if any.
    """
    area = _rules.area_of(location)
    value = value_ty * TY if value_ty else (purchase_price_ty * TY if purchase_price_ty and not sqm else None)
    _add(
        ctx,
        "asset",
        {
            "class": "real_estate",
            "name": f"{name} (tự khai)",
            "area": area,
            "location": location,
            "sqm": sqm,
            "purchase_year": purchase_year,
            "purchase_price": purchase_price_ty * TY if purchase_price_ty else None,
            "value": value,
            "rental_monthly": (rental_million_per_month or 0) * TR,
        },
    )
    return f"Đã ghi: {name} ở {location}" + (f", {vnd(value)}" if value else "")


@tool(idempotent=False)
def declare_gold(ctx: RunContext, luong: float) -> str:
    """Record gold the client holds, in lượng (cây).

    Args:
        luong: How many lượng.
    """
    _add(ctx, "asset", {"class": "gold", "name": "Vàng (tự khai)", "qty": luong})
    return f"Đã ghi: {luong:g} lượng vàng"


@tool(idempotent=False)
def declare_holding(ctx: RunContext, kind: str, name: str, value_ty: float) -> str:
    """Record another asset: shares in a company, an insurance policy's cash value, crypto, other.

    Args:
        kind: One of business, insurance, crypto, other.
        name: What it is (e.g. "30% cổ phần Công ty ABC").
        value_ty: What it is worth, in tỷ.
    """
    cls = kind if kind in ("business", "insurance", "crypto") else "other"
    _add(ctx, "asset", {"class": cls, "name": f"{name} (tự khai)", "value": value_ty * TY})
    return f"Đã ghi: {name}, {vnd(value_ty * TY)}"


@tool(idempotent=False)
def declare_loan(ctx: RunContext, name: str, outstanding_ty: float, monthly_payment_million: float = 0) -> str:
    """Record a debt the client has outside our bank.

    Args:
        name: What it is (e.g. "Vay mua xe").
        outstanding_ty: What is still owed, in tỷ.
        monthly_payment_million: The monthly instalment, in triệu.
    """
    _add(
        ctx,
        "asset",
        {
            "class": "loan",
            "name": f"{name} (tự khai)",
            "value": outstanding_ty * TY,
            "monthly_payment": monthly_payment_million * TR,
            "rate_type": "fixed",
        },
    )
    return f"Đã ghi: khoản nợ {name}, {vnd(outstanding_ty * TY)}"


@tool(idempotent=False)
def declare_dependent(ctx: RunContext, name: str, relation: str, birth_year: Optional[int] = None) -> str:
    """Record someone the client supports (a child, a parent).

    Args:
        name: Their name, or "Con 1" when not given.
        relation: Con, Bố, Mẹ, ...
        birth_year: Their year of birth, if known (from their age: 2026 − age).
    """
    _add(ctx, "dependent", {"name": name, "relation": relation, "birth_year": birth_year})
    return f"Đã ghi người phụ thuộc: {name} ({relation})"


@tool(idempotent=False)
def declare_income(ctx: RunContext, label: str, million_per_month: float) -> str:
    """Record a monthly income our data does not see (rent received, a second salary).

    Args:
        label: What it is.
        million_per_month: How much, in triệu per month.
    """
    _add(ctx, "income", {"label": f"{label} (tự khai)", "amount": million_per_month * TR})
    return f"Đã ghi thu nhập: {label}, {million_per_month:g} triệu/tháng"


TOOLS = [
    declare_property,
    declare_gold,
    declare_holding,
    declare_loan,
    declare_dependent,
    declare_income,
]
