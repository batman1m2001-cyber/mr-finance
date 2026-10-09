"""VND amounts as a Vietnamese reader says them: 45,2 tỷ, 850 triệu."""

from __future__ import annotations

TY = 1_000_000_000
TR = 1_000_000


def _vn(x: float, digits: int) -> str:
    s = f"{x:,.{digits}f}".replace(",", "\0").replace(".", ",").replace("\0", ".")
    return s.rstrip("0").rstrip(",") if "," in s else s


def vnd(amount: float, signed: bool = False) -> str:
    """``45_200_000_000`` → ``45,2 tỷ``; ``850_000_000`` → ``850 triệu``."""
    sign = "+" if signed and amount > 0 else "-" if amount < 0 else ""
    a = abs(amount)
    if a >= TY:
        body = f"{_vn(a / TY, 2 if a < 10 * TY else 1)} tỷ"
    elif a >= TR:
        body = f"{_vn(a / TR, 0 if a >= 100 * TR else 1)} triệu"
    else:
        body = f"{_vn(a, 0)} đ"
    return sign + body


def pct(x: float, signed: bool = False, digits: int = 1) -> str:
    """``0.031`` → ``3,1%`` (``+3,1%`` when signed)."""
    sign = "+" if signed and x > 0 else "-" if x < 0 else ""
    return f"{sign}{_vn(abs(x) * 100, digits)}%"


def months_text(months: float) -> str:
    """How long a reserve lasts: ``14 tháng``; past three years, in years (``29 năm``)."""
    if months >= 36:
        return f"{_vn(months / 12, 0)} năm"
    return f"{_vn(months, 0 if months >= 10 else 1)} tháng"
