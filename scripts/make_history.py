"""Write each person's simulated money history under data/history/ (NODE_TIMELINE_PLAN.md T1).

From January 2021 to the demo date, every holding the fixtures give (data/clients/*.json valued at data/market.json),
the money that was elsewhere before it bought them, and the transactions before the fixtures' twelve months. Every
series ends at today's value and passes through the anchors the app already uses (a holding's ``prev_value`` a month
before the demo date, its ``ytd_value`` on 1 January). Stocks, gold and crypto follow the real prices stored by the
market job (data/state.db, read only), corrected to the demo's mock prices; the rest is drawn (seeded).

    uv run python scripts/make_history.py

Deterministic: run it again with the same stored series and nothing changes. The files are committed, so the app
never needs the store. The script stops when a cash account or the earlier deposit would go below zero.
"""

from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from bisect import bisect_right
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src")]
from wealth import valuation  # noqa: E402  (pure: today's holdings, keyed as the app keys them)

DATA = ROOT / "data"
OUT = DATA / "history"
START = date(2020, 12, 31)
DAILY_FROM = date(2025, 10, 1)  # the fixtures' first transaction month: every day from here
NOTE = (
    "Dữ liệu mô phỏng: lịch sử từ 2021 được tạo cho bản demo (scripts/make_history.py), khớp với số hôm nay, "
    "tháng trước và đầu năm; giá cổ phiếu, vàng, tiền số theo diễn biến thật, chỉnh về giá demo."
)
SALARY_GROWTH, PRICE_GROWTH = 0.06, 0.035  # a year, going back: income lower, spending lower
FUND_RATE = {"bond": 0.065, "money": 0.045}
CLOSED_NAME = "Tiền gửi đã tất toán"
FLOOR = -50e6  # going back, the least a person's cash may come to (a few days a little under zero are shown as zero)


class Short(Exception):
    """The cash account would go below FLOOR going back: the person saved more than their cash could have held."""


def day(s: str) -> date:
    return date.fromisoformat(s[:10])


def month_back(d: date) -> date:
    y, m = (d.year, d.month - 1) if d.month > 1 else (d.year - 1, 12)
    return date(y, m, min(d.day, 28 if m == 2 else 30))


# ── the stored market series (read only) ───────────────────────────────────────────────────────────────────────────
def stored(series: str, until: date) -> Optional[Callable[[date], float]]:
    path = DATA / "state.db"
    if not path.is_file():
        return None
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "select date, value from market_series where series = ? and date <= ? order by date",
            (series, until.isoformat()),
        ).fetchall()
    finally:
        con.close()
    if len(rows) < 50:
        return None
    xs = [day(d).toordinal() for d, _ in rows]
    vs = [float(v) for _, v in rows]

    def at(d: date) -> float:  # the last close on or before d (linear between sparse points, e.g. weekly SJC)
        o = d.toordinal()
        i = bisect_right(xs, o) - 1
        if i < 0:
            return vs[0]
        if i + 1 < len(xs) and xs[i + 1] - xs[i] > 4:
            f = (o - xs[i]) / (xs[i + 1] - xs[i])
            return vs[i] * (vs[i + 1] / vs[i]) ** f
        return vs[i]

    return at


def walk(rng: random.Random, days: List[date], drift: float, vol: float) -> Callable[[date], float]:
    """A seeded random walk (when a series is not stored): a year's drift and volatility."""
    v, out = 1.0, {}
    for d in days:
        out[d] = v
        v *= math.exp(drift / 365 + vol / math.sqrt(365) * rng.gauss(0, 1))
    return lambda d: out[d]


def anchored(real: Callable[[date], float], anchors: Dict[date, float]) -> Callable[[date], float]:
    """The real shape, corrected to the demo's prices: a factor constant before the first anchor, log-linear
    between anchors, so the result equals each anchor on its day."""
    pts = sorted((d, math.log(p / real(d))) for d, p in anchors.items() if p)

    def at(d: date) -> float:
        if d <= pts[0][0]:
            c = pts[0][1]
        elif d >= pts[-1][0]:
            c = pts[-1][1]
        else:
            i = max(k for k in range(len(pts)) if pts[k][0] <= d)
            (d0, c0), (d1, c1) = pts[i], pts[i + 1]
            c = c0 + (c1 - c0) * (d - d0).days / (d1 - d0).days
        return real(d) * math.exp(c)

    return at


def bridge(
    rng: random.Random, days: List[date], t0: date, v0: float, t1: date, v1: float, wobble: float
) -> Dict[date, float]:
    """From v0 on t0 to v1 on t1, compounding evenly, with a small monthly wobble that is zero at both ends."""
    n = max(1, (t1 - t0).days)
    marks, w = {}, 0.0
    for d in days:
        if t0 <= d <= t1 and d.day == 1:
            w = 0.7 * w + rng.gauss(0, wobble)
        marks[d] = w
    out = {}
    for d in days:
        if d < t0 or d > t1:
            continue
        f = (d - t0).days / n
        out[d] = v0 * (v1 / v0) ** f * math.exp(marks[d] * math.sin(math.pi * f))
    return out


# ── a person ───────────────────────────────────────────────────────────────────────────────────────────────────────
def holdings_of(c: dict, market: dict) -> List[dict]:
    s, pid = c["sources"], c["id"]
    out = valuation.techcombank(pid, s["techcombank"], market) + valuation.tcbs(pid, s["tcbs"], market)
    out += valuation.techcom_capital(pid, s["techcom_capital"], market) + valuation.onehousing(
        pid, s["onehousing"], market
    )
    for inst in s.get("open_api") or []:  # as valuation.open_api, without the consent configuration (a stored read)
        name = inst["institution"]
        for a in inst.get("accounts", []):
            out.append(
                valuation.holding(
                    pid,
                    "open_api",
                    f"{name}:{a['id']}",
                    trust="verified",
                    cls="cash",
                    name=a["name"],
                    value=a["balance"],
                    liquid=True,
                    account_type=a["type"],
                )
            )
        for st in inst.get("stocks", []):
            out.append(valuation.stock(pid, "open_api", st, market, "verified", ident=f"{name}:stock:{st['ticker']}"))
    return out + valuation.declared(pid, c.get("declared", []), market)


def older_rows(rng: random.Random, rows: List[dict], first: date, k: float = 1.0) -> List[dict]:
    """2021-01 … the month before ``first``: each month the same month of the fixtures' year, its rows on the same
    days and categories, income 6 % and spending 3,5 % a year lower going back, jittered; income times ``k`` (a person
    who saves more today than their cash could have held earned less before)."""
    by_month: Dict[int, List[dict]] = {}
    for r in rows:
        by_month.setdefault(day(r["date"]).month, []).append(r)
    out = []
    y, m = 2021, 1
    while date(y, m, 1) < date(first.year, first.month, 1):
        tpl = by_month.get(m, [])
        for r in tpl:
            back = (day(r["date"]).year - y) + (day(r["date"]).month - m) / 12
            g = SALARY_GROWTH if r["direction"] == "in" else PRICE_GROWTH
            jitter = 0.01 if r["category"] in ("salary", "pension", "rent", "loan") else 0.12
            amount = r["amount"] / (1 + g) ** back * rng.uniform(1 - jitter, 1 + jitter)
            if r["category"] == "loan":
                amount = r["amount"]  # an instalment does not change
            elif r["direction"] == "in":
                amount *= k
            desc = r["desc"]
            for tag in (f"T{day(r['date']).month}/{day(r['date']).year}",):
                desc = desc.replace(tag, f"T{m}/{y}")
            out.append(
                {
                    "date": date(y, m, day(r["date"]).day).isoformat(),
                    "amount": round(amount, -3),
                    "direction": r["direction"],
                    "desc": desc,
                    "category": r["category"],
                }
            )
        y, m = (y, m + 1) if m < 12 else (y + 1, 1)
    return sorted(out, key=lambda r: r["date"])


def person(c: dict, market: dict, as_of: date, days: List[date], k: float = 1.0) -> dict:
    rng = random.Random(f"history:{c['id']}")
    t1 = month_back(as_of)  # the month-ago anchor (prev_value)
    ytd = date(as_of.year, 1, 1)
    hs = holdings_of(c, market)
    tb = c["sources"]["techcombank"]
    rows = sorted(tb.get("transactions", []), key=lambda r: r["date"])
    first = day(rows[0]["date"]) if rows else DAILY_FROM
    old = older_rows(rng, rows, first, k) if rows else []
    series: Dict[str, Dict[date, float]] = {}
    buys: Dict[date, float] = {}  # the money a purchase took, on its day (from the cash account, going back)

    def purchased(h: dict) -> date:  # a property's purchase year gives a month from a seeded draw
        return date(h["detail"].get("purchase_year") or 2015, random.Random(f"bought:{h['key']}").randint(2, 11), 15)

    def bought(h: dict, at: Optional[date], v: Dict[date, float]) -> None:
        if at and at > START:
            for d in days:
                if d < at:
                    v[d] = 0.0
            buys[at] = buys.get(at, 0.0) + v[min(d for d in days if d >= at)]
        series[h["key"]] = v

    for h in hs:
        cls, det, key = h["class"], h["detail"], h["key"]
        hr = random.Random(f"history:{key}")
        flat = {d: float(h["value"]) for d in days}
        if cls in ("stock", "gold", "crypto") or (cls == "fund"):
            qty = det.get("qty") or det.get("units")
            if cls == "stock":
                m, real = market["stocks"][det["ticker"]], stored(det["ticker"], as_of)
                anchors = {as_of: m["price"], t1: m["prev_month"], ytd: m["ytd_base"]}
            elif cls == "gold":
                m, real = market["gold"], stored("SJC", as_of)
                anchors = {as_of: m["price_per_luong"], t1: m["prev_month"], ytd: m["ytd_base"]}
            elif cls == "crypto":
                m = market["crypto"][det["symbol"]]
                usd, fx = stored(f"{det['symbol']}USD", as_of), stored("USDVND", as_of)
                real = (lambda d, u=usd, f=fx: u(d) * f(d)) if usd and fx else None
                anchors = {as_of: m["price"], t1: m["prev_month"], ytd: m["ytd_base"]}
            else:
                m = market["funds"][det["code"]]
                real = stored("VNINDEX", as_of) if m["type"] == "equity" else None
                if real is None and m["type"] in FUND_RATE:
                    real = walk(hr, days, FUND_RATE[m["type"]], 0.01)
                anchors = {as_of: m["nav"], t1: m["prev_month"], ytd: m["ytd_base"]}
            real = real or walk(hr, days, 0.08, 0.3)
            price = anchored(real, anchors)
            v = {d: qty * price(d) for d in days}
            bought(h, day(det["bought"]) if det.get("bought") else None, v)
        elif cls == "bond":
            at = day(det["bought"]) if det.get("bought") else START
            v = {}
            for d in days:
                f = min(1.0, max(0.0, (d - at).days / max(1, (t1 - at).days)))
                v[d] = det["qty"] * ((det.get("avg_price") or det["price"]) * (1 - f) + det["price"] * f)
            bought(h, at if det.get("bought") else None, v)
        elif cls == "real_estate":
            at = purchased(h)
            cost = h["cost"] or h["value"] * 0.6
            v = bridge(
                hr,
                days,
                min(at, START),
                cost
                if at >= START
                else cost * (h["prev_value"] / cost) ** ((START - at).days / max(1, (t1 - at).days)),
                t1,
                h["prev_value"],
                0.012,
            )
            v = {d: v.get(d, h["prev_value"]) for d in days}
            for d in days:  # the last month: from the month-ago value to today's
                if d > t1:
                    v[d] = h["prev_value"] + (h["value"] - h["prev_value"]) * (d - t1).days / (as_of - t1).days
            bought(h, at if at > START else None, v)
        elif cls == "deposit":
            opened = day(det["opened"]) if det.get("opened") else None
            bought(h, opened, dict(flat))
        elif cls == "insurance":
            prem, pm = det.get("premium_annual") or h["value"] * 0.1, det.get("premium_month") or 1
            v = {}
            for d in days:
                n = sum(1 for y in range(d.year, as_of.year + 1) if d < date(y, pm, 1) <= t1)
                v[d] = max(0.0, h["value"] - 0.9 * prem * n)
            series[key] = v
        elif cls == "loan" and h["kind"] == "liability":
            pay, r = det.get("monthly_payment") or 0, (det.get("rate") or 0) / 12
            # going back from the month-ago anchor, each instalment (the 20th) undone: before it, owed more
            b, v = float(h["value"]), {}
            pays = (
                [
                    x
                    for x in (date(y, mo, 20) for y in range(START.year, as_of.year + 1) for mo in range(1, 13))
                    if START < x <= t1
                ]
                if pay
                else []
            )
            for d in sorted(days, reverse=True):
                while pays and pays[-1] > d:
                    b = (b + pay) / (1 + r)
                    pays.pop()
                v[d] = b
            home = next((x for x in hs if x["key"] == f"{c['id']}:onehousing:{det.get('collateral')}"), None)
            at = purchased(home) if home else START
            if at > START:  # taken out with the home it bought: none before, and it paid part of the price
                first_day = min(d for d in days if d >= at)
                buys[at] = buys.get(at, 0.0) - v[first_day]
                v = {d: (0.0 if d < at else x) for d, x in v.items()}
            series[key] = v
        elif cls == "card":

            def phase(d: date) -> float:
                last = (
                    date(d.year, d.month, 25)
                    if d.day >= 25
                    else date(*((d.year, d.month - 1) if d.month > 1 else (d.year - 1, 12)), 25)
                )
                return (d - last).days / 30

            base = h["value"] / (0.3 + 0.7 * phase(t1))
            series[key] = {
                d: h["value"] if d >= t1 else base * (0.3 + 0.7 * phase(d)) for d in days
            }  # flat since the month-ago anchor
        elif cls in ("business",) or h["source"] == "declared" and cls not in ("cash",):
            v, f = {}, 1.0
            steps = {y: hr.uniform(0.95, 1.05) for y in range(START.year + 1, as_of.year + 1)}
            for d in days:
                f = math.prod(1 / steps[y] for y in steps if d < date(y, 1, 1) <= t1)
                v[d] = h["value"] * f
            series[key] = v
        else:  # a cash account: filled below
            series[key] = dict(flat)

    # the cash account that pays and receives (the person's first Techcombank account; else their first cash),
    # going back from the month-ago anchor: each day's rows undone, each purchase's money put back
    cash = [h for h in hs if h["class"] == "cash"]
    main = next((h for h in cash if h["source"] == "techcombank"), cash[0] if cash else None)
    closed = {d: 0.0 for d in days}
    flows: Dict[date, float] = {}
    for r in old + rows:
        d = day(r["date"])
        flows[d] = flows.get(d, 0.0) + (r["amount"] if r["direction"] == "in" else -r["amount"])
    if main is not None or buys:
        top = float(main["value"]) if main else 0.0
        cap = max(top * 1.5, 3 * (c.get("spending_monthly") or 0), 200e6)
        bal, ds = top, sorted(days, reverse=True)
        events = sorted(set(flows) | set(buys))
        j = len(events) - 1
        mv, cv = {}, {}
        for d in ds:
            while j >= 0 and events[j] > d:
                e = events[j]
                if e <= t1:  # the last month stays as today (Tổng quan's month-ago value is today's)
                    bal += buys.get(e, 0.0) - flows.get(e, 0.0)
                j -= 1
            over = max(0.0, bal - cap) if main else max(0.0, bal)
            mv[d], cv[d] = bal - over, over
        low = min(mv.values()) if main else min(cv.values())
        if low < FLOOR:
            raise Short(low)
        if main is not None:
            series[main["key"]] = {d: max(0.0, x) for d, x in mv.items()}
        closed = cv
    out = {"holdings": {}, "closed": {}, "transactions": old}
    for h in hs:
        out["holdings"][h["key"]] = {
            "class": h["class"],
            "kind": h["kind"],
            "values": [round(series[h["key"]][d], -3) for d in days],
        }
    if any(closed.values()):
        out["closed"][f"{c['id']}:history:closed_deposit"] = {
            "class": "deposit",
            "kind": "asset",
            "name": CLOSED_NAME,
            "values": [round(closed[d], -3) for d in days],
        }
    return out


def grid(as_of: date) -> List[date]:
    """Month-ends from 2020-12-31 until the daily window, then every day to the demo date."""
    out, y, m = [], START.year, START.month
    while True:
        nxt = date(y + (m == 12), m % 12 + 1, 1)
        end = nxt - timedelta(days=1)
        if end >= DAILY_FROM:
            break
        out.append(end)
        y, m = nxt.year, nxt.month
    d = DAILY_FROM
    while d <= as_of:
        out.append(d)
        d += timedelta(days=1)
    return out


def main() -> None:
    market = json.loads((DATA / "market.json").read_text(encoding="utf-8"))
    as_of = day(market["as_of"])
    days = grid(as_of)
    OUT.mkdir(exist_ok=True)
    for f in sorted((DATA / "clients").glob("*.json")):
        c = json.loads(f.read_text(encoding="utf-8"))
        k = 1.0
        while True:
            try:
                p = person(c, market, as_of, days, k)
                break
            except Short as e:
                if k <= 0.3:
                    raise SystemExit(
                        f"{c['id']}: the cash account would be {e.args[0] / 1e6:,.0f} triệu even at 30 % of the income"
                    )
                k = round(k - 0.05, 2)
        p["income_scale"] = k
        doc = {"as_of": as_of.isoformat(), "person": c["id"], "note": NOTE, "dates": [d.isoformat() for d in days], **p}
        (OUT / f"{c['id']}.json").write_text(
            json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
        )
        print(
            f"{c['id']}: {len(p['holdings'])} holdings, {len(p['closed'])} closed, "
            f"{len(p['transactions'])} older rows, income ×{k}"
        )


if __name__ == "__main__":
    main()
