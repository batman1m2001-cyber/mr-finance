"""A node's money over time (docs/NODE_TIMELINE_PLAN.md T2): the family's net worth, an asset class, a holding, the
liquidity reserve — their value on each date of the simulated history (src/timeline/history.py) — and the money in
and out, by category — the sums of the transaction rows. ``change`` gives the figure an edge of the overview graph
shows: since yesterday, since the same day last month (today's value − ``prev_value``, as Tổng quan), since the same
day last year; for money in and out, the latest day with rows, the flow's month, the twelve months to it."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from operonx import op

from control.errors import BadRequest
from dashboard.ops import is_liquid
from overview.ops import CLASSES, GROUP
from people import auth
from timeline.history import Book, month_back, year_back
from wealth import fixtures

UNITS = ("day", "month", "year")
DAYS_SHOWN = 90
NOTE = "Lịch sử là dữ liệu mô phỏng cho bản demo (từ 2021), khớp với số hôm nay, tháng trước và đầu năm."
SIDE = {"in": "Tiền vào", "out": "Tiền ra"}


@op
def check_request(client_id: str = None, scope: str = None, node: str = None, unit: str = None) -> dict:
    """A known client the person may see, personal or family, a node of the graph, a unit: day, month or year."""
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise BadRequest(f"no client {client_id!r}")
    auth.require_client(client_id)
    scope = scope or "personal"
    if scope not in ("personal", "family"):
        raise BadRequest("scope is personal or family")
    unit = unit or "month"
    if unit not in UNITS:
        raise BadRequest(f"unit is one of {UNITS}")
    node = str(node or "ME")
    if not _known(node):
        raise BadRequest(f"không có diễn biến tiền cho {node!r}")
    return {"client_id": client_id, "scope": scope, "node": node, "unit": unit}


def _known(node: str) -> bool:
    return node in ("ME", "LQ:reserve", "FL:in", "FL:out") or node.startswith(("CL:", "HD:", "FC:in:", "FC:out:"))


def _flow_of(node: str) -> Optional[Tuple[str, Optional[str]]]:
    """(side, category or None) for a money-in / money-out node."""
    if node in ("FL:in", "FL:out"):
        return node[3:], None
    if node.startswith(("FC:in:", "FC:out:")):
        _, side, cat = node.split(":", 2)
        return side, cat
    return None


def _items(book: Book, node: str) -> List[Dict[str, Any]]:
    if node == "ME":
        return book.items
    if node == "LQ:reserve":
        return [x for x in book.items if x["closed"] or is_liquid(x)]
    if node.startswith("CL:"):
        return [x for x in book.items if GROUP.get(x["class"], x["class"]) == node[3:]]
    return [x for x in book.items if not x["closed"] and x["key"] == node[3:]]


def _rows(book: Book, transactions: list, side: str, cat: Optional[str]) -> List[Dict[str, Any]]:
    """The fixtures' rows and the older ones of the same people, one side (and category)."""
    return [
        t for t in list(transactions) + book.rows if t["direction"] == side and (cat is None or t["category"] == cat)
    ]


def _label(node: str, book: Book) -> str:
    if node == "ME":
        return "Tài sản ròng"
    if node == "LQ:reserve":
        return "Thanh khoản dự phòng"
    if node.startswith("CL:"):
        return CLASSES.get(node[3:], node[3:])
    f = _flow_of(node)
    if f:
        return SIDE[f[0]] + (f" · {f[1]}" if f[1] else "")
    hit = next((x for x in book.items if x["key"] == node[3:]), None)
    return hit["name"] if hit else node


def _vn_day(d: date) -> str:
    return f"{d.day:02d}/{d.month:02d}"


def _level_points(book: Book, items: list, net: bool, unit: str) -> List[Dict[str, Any]]:
    T = book.as_of
    if unit == "day":
        ds = [d for d in book.dates if d > T.fromordinal(T.toordinal() - DAYS_SHOWN)]
        marks = [(d, _vn_day(d), T.fromordinal(d.toordinal() - 1)) for d in ds]
    elif unit == "month":
        ends = [
            d
            for d in book.dates
            if d < date(T.year, T.month, 1) and (d.month != (d.fromordinal(d.toordinal() + 1)).month)
        ]
        ends = [d for d in ends if d.year >= 2021] + [T]
        marks = [(d, f"T{d.month}/{d.year % 100:02d}", None) for d in ends]
    else:
        ends = [date(y, 12, 31) for y in range(2021, T.year)] + [T]
        marks = [(d, str(d.year) if d != T else f"{d.year} (đến {d.day}/{d.month})", None) for d in ends]
    out, prev = [], None
    for d, label, before in marks:
        v = book.value(items, d, net)
        if before is not None:
            p = book.value(items, before, net)
        else:
            p = prev if prev is not None else book.value(items, date(2020, 12, 31), net)
        out.append({"t": d.isoformat(), "label": label, "value": round(v), "change": round(v - p)})
        prev = v
    return out


def _flow_points(book: Book, rows: list, side: str, unit: str, last_month: str) -> List[Dict[str, Any]]:
    sign = 1 if side == "in" else -1
    T = book.as_of
    sums: Dict[str, float] = {}
    key = {"day": lambda s: s[:10], "month": lambda s: s[:7], "year": lambda s: s[:4]}[unit]
    for r in rows:
        sums[key(r["date"])] = sums.get(key(r["date"]), 0.0) + r["amount"]
    if unit == "day":
        ks = [T.fromordinal(T.toordinal() - i) for i in range(DAYS_SHOWN - 1, -1, -1)]
        marks = [(d.isoformat(), _vn_day(d)) for d in ks]
    elif unit == "month":
        end = last_month or T.isoformat()[:7]
        marks, y, m = [], 2021, 1
        while f"{y}-{m:02d}" <= end:
            marks.append((f"{y}-{m:02d}", f"T{m}/{y % 100:02d}"))
            y, m = (y, m + 1) if m < 12 else (y + 1, 1)
    else:
        marks = [(str(y), str(y)) for y in range(2021, T.year + 1)]
    return [{"t": k, "label": lab, "value": round(sign * sums.get(k, 0.0)), "change": None} for k, lab in marks]


def _change(book: Book, node: str, transactions: list, month: str) -> Optional[Dict[str, Any]]:
    f = _flow_of(node)
    if f:
        side, cat = f
        rows = _rows(book, transactions, side, cat)
        if not rows or not month:
            return None
        sign = 1 if side == "in" else -1
        days = sorted({r["date"][:10] for r in rows if r["date"][:7] <= month})
        last = days[-1] if days else None
        y, m = int(month[:4]), int(month[5:])
        since = f"{y - 1}-{m + 1:02d}" if m < 12 else f"{y}-01"  # the twelve months to the flow's month
        return {
            "day": sign * sum(r["amount"] for r in rows if r["date"][:10] == last),
            "day_at": last,
            "month": sign * sum(r["amount"] for r in rows if r["date"][:7] == month),
            "month_at": month,
            "year": sign * sum(r["amount"] for r in rows if since <= r["date"][:7] <= month),
        }
    items = _items(book, node)
    if not items:
        return None
    net = node == "ME"
    T = book.as_of
    now = book.value(items, T, net)
    return {
        "day": round(now - book.value(items, T.fromordinal(T.toordinal() - 1), net)),
        "month": round(now - book.value(items, month_back(T), net)),
        "year": round(now - book.value(items, year_back(T), net)),
    }


def _book(holdings: list, members: list) -> Book:
    return Book(holdings, [m["id"] for m in members], fixtures.market()["as_of"])


@op
def series(client_id: str, scope: str, node: str, unit: str, holdings: list, members: list, transactions: list) -> dict:
    """One node's points by day (the last 90 days), month (since January 2021) or year (2021 to today)."""
    book = _book(holdings, members)
    f = _flow_of(node)
    if f:
        rows = _rows(book, transactions, *f)
        months = sorted({t["date"][:7] for t in transactions})
        points = _flow_points(book, rows, f[0], unit, months[-1] if months else "")
        kind = "flow"
    else:
        items = _items(book, node)
        if not items:
            raise BadRequest(f"không có {node!r} trong bức tranh này")
        points = _level_points(book, items, node == "ME", unit)
        kind = "level"
    liability = node.startswith(("CL:", "HD:")) and all(x["kind"] == "liability" for x in _items(book, node) or [{}])
    return {
        "timeline": {
            "client_id": client_id,
            "scope": scope,
            "node": node,
            "label": _label(node, book),
            "unit": unit,
            "kind": kind,
            "liability": bool(liability),
            "as_of": book.as_of.isoformat(),
            "points": points,
            "simulated": book.simulated,
            "note": NOTE,
        }
    }


@op
def changes(holdings: list, members: list, transactions: list, month: str = "") -> dict:
    """The change of every money node of the overview graph, for its edge (``{day, month, year}``)."""
    book = _book(holdings, members)
    nodes = ["ME", "LQ:reserve"] + sorted({f"CL:{GROUP.get(h['class'], h['class'])}" for h in holdings if h["value"]})
    nodes += [f"HD:{h['key']}" for h in holdings if h["value"]]
    cats = {(t["direction"], t["category"]) for t in transactions if t["date"][:7] == month}
    nodes += ["FL:in", "FL:out"] + [f"FC:{s}:{c}" for s, c in sorted(cats)]
    out = {}
    for n in nodes:
        c = _change(book, n, transactions, month)
        if c is not None:
            out[n] = c
    return {"changes": out, "simulated": book.simulated}
