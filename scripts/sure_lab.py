"""The sure-calls lab (SURE_CALLS_PLAN S1/S2): every price signal family's vote at monthly checkpoints since 2021, and
how often a call is right when at least k families agree and none is against.

    python scripts/sure_lab.py --db data/state.db            # dev + validation table; freezes data/sure_rules.json
    python scripts/sure_lab.py --db data/state.db --test     # the test, once: out/sure/test.json

- **Checkpoints**: the first of each month; each series read as of its last close on or before that day; the call is
  for the next 1 month (30 days) or 3 months (91 days), right when the price (the yield, for rates) moved that way.
- **Periods** (plan §3 D2): dev 2021-01 → 2023-12, validation 2024-01 → 2025-06, test 2025-07 → 2026-07. A checkpoint
  belongs to a period only if its outcome is known before the next period starts, so no period peeks at the next one.
- **Families** (plan D4), each one vote, up / down / nothing, thresholds fixed here before any number was read:
  trend, stretch, breakout, quiet-break, breadth and flows (VN stocks), links (dollar, US 10Y, world stocks, USD/VND).
  Whether a family reads "with" or "against" the move (a stretch that tends back) is set on dev only.
- **The rule** (plan D5): call up when at least k families vote up and none votes down. k is chosen on validation as
  the smallest that clears the gate (plan D3); the interval resamples months, as calls on one month move together.
- **The test** runs once: it refuses to run without frozen rules, or a second time.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import os
import random
import sqlite3
import statistics as st
import sys
from datetime import date, timedelta

GROUPS = {
    "vn_stocks": ["VNINDEX", "FPT", "TCB", "VCB", "MBB", "VNM", "HPG", "VHM", "MWG", "DGC", "SSI"],
    "gold": ["XAUUSD", "SJC"],
    "crypto": ["BTCUSD", "ETHUSD"],
    "usd_vnd": ["USDVND"],
    "vn_rates": ["VN_GOV_10Y", "VN_GOV_5Y"],
    "world_stocks": ["SPX", "ACWI"],
}
LEVELS = {"US10Y", "VN_GOV_10Y", "VN_GOV_5Y", "VN_GOV_1Y", "VN_GOV_3M"}  # yields: moves are differences
VN_TEN = GROUPS["vn_stocks"][1:]
LINKS = {  # per group, the other markets read as one family
    "vn_stocks": ["world", "dollar", "usdvnd"],
    "gold": ["dollar", "us10y"],
    "crypto": ["world", "dollar"],
    "usd_vnd": ["dollar", "us10y"],
    "vn_rates": ["us10y", "usdvnd"],
    "world_stocks": ["dollar", "us10y"],
}
HORIZONS = {"1m": 30, "3m": 91}
PERIODS = {"dev": ("2021-01-01", "2024-01-01"), "val": ("2024-01-01", "2025-07-01"), "test": ("2025-07-01", "2026-08-01")}
GATE = {"hit": 0.70, "n": 15, "level": 0.90}
ORIENTED = ("stretch", "breakout", "quiet", "flows")  # with or against the move: set on dev
D = date.fromisoformat


class Series:
    def __init__(self, name, rows):
        self.name, self.level = name, name in LEVELS
        self.d = [D(r[0]) for r in rows]
        self.v = [r[1] for r in rows]

    def at(self, t, stale=12):
        """The last value on or before t, if it is at most ``stale`` days old."""
        i = bisect.bisect_right(self.d, t) - 1
        return self.v[i] if i >= 0 and (t - self.d[i]).days <= stale else None

    def window(self, a, b):
        return self.v[bisect.bisect_right(self.d, a): bisect.bisect_right(self.d, b)]

    def move(self, a, b):
        x, y = self.at(a), self.at(b)
        if x is None or y is None or (not self.level and (x <= 0 or y <= 0)):
            return None
        return y - x if self.level else math.log(y / x)

    def swing(self, t, days):
        """The usual move over ``days``, from the year before t (observations may be daily or weekly)."""
        i, j = bisect.bisect_right(self.d, t - timedelta(365)), bisect.bisect_right(self.d, t)
        if j - i < 30:
            return None
        rs = [(self.v[k] - self.v[k - 1]) if self.level else math.log(self.v[k] / self.v[k - 1])
              for k in range(i + 1, j) if self.level or self.v[k - 1] > 0]
        gap = (self.d[j - 1] - self.d[i]).days / max(1, j - i - 1)
        return (st.pstdev(rs) / math.sqrt(gap)) * math.sqrt(days) or None

    def z(self, t, days):
        m, s = self.move(t - timedelta(days), t), self.swing(t, days)
        return None if m is None or not s else m / s


def sign(x):
    return (x > 0) - (x < 0)


def load(db):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    out = {}
    for name in {n for g in GROUPS.values() for n in g} | {"EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "USDSEK",
                                                            "US10Y", "FOREIGN_NET_HOSE"}:
        rows = c.execute("select date, value from market_series where series=? and value is not null order by date",
                         (name,)).fetchall()
        out[name] = Series(name, rows)
    return out


# -- the families: each returns +1, -1 or 0 for one series (or its group) at t ---------------------------------------

def trend(s, t):
    zs = [s.z(t, d) for d in (30, 91, 182, 365)]
    v, avg50, avg200 = s.at(t), s.window(t - timedelta(70), t), s.window(t - timedelta(280), t)
    if None in zs or v is None or len(avg200) < 30:
        return 0
    m, a50, a200 = sum(zs) / 4, sum(avg50) / len(avg50), sum(avg200) / len(avg200)
    if m >= 0.5 and v > a50 and v > a200:
        return 1
    if m <= -0.5 and v < a50 and v < a200:
        return -1
    return 0


def stretch(s, t):
    year, v, sw = s.window(t - timedelta(365), t), s.at(t), s.swing(t, 182)
    if len(year) < 30 or v is None or not sw:
        return 0
    avg = sum(year) / len(year)
    gap = (v - avg) if s.level else (math.log(v / avg) if v > 0 and avg > 0 else 0)
    return sign(gap) if abs(gap / sw) >= 1.5 else 0


def breakout(s, t):
    before, v = s.window(t - timedelta(182), t - timedelta(30)), s.at(t)
    if len(before) < 10 or v is None:
        return 0
    return 1 if v > max(before) else -1 if v < min(before) else 0


def quiet(s, t):
    """A quiet spell that breaks: the 3 months before the last one swung under 0.7 of the usual, then the last month
    moved more than one usual monthly swing."""
    seg, z1, usual = s.window(t - timedelta(121), t - timedelta(30)), s.z(t, 30), s.swing(t - timedelta(30), 91)
    if z1 is None or not usual or len(seg) < 8:
        return 0
    rs = [(seg[k] - seg[k - 1]) if s.level else math.log(seg[k] / seg[k - 1]) for k in range(1, len(seg)) if seg[k - 1] > 0]
    calm = st.pstdev(rs) * math.sqrt(len(rs)) < 0.7 * usual
    return sign(z1) if calm and abs(z1) >= 1.0 else 0


def breadth(S, t):
    up = n = 0
    for name in VN_TEN:
        s = S[name]
        v, w = s.at(t), s.window(t - timedelta(280), t)
        if v is None or len(w) < 30:
            continue
        n += 1
        up += v > sum(w) / len(w)
    if n < 6:
        return 0
    return 1 if up / n >= 0.7 else -1 if up / n <= 0.3 else 0


def flows(S, t):
    f = S["FOREIGN_NET_HOSE"]
    f1, f3 = sum(f.window(t - timedelta(30), t)), sum(f.window(t - timedelta(91), t))
    past = [abs(sum(f.window(u - timedelta(91), u))) for u in (t - timedelta(30 * k) for k in range(1, 25))]
    past = [p for p in past if p]
    if len(past) < 6 or not f3:
        return 0
    return sign(f3) if sign(f1) == sign(f3) and abs(f3) >= st.median(past) else 0


def link(S, name, t):
    """One outside market's 3-month direction, in its own usual-swing units."""
    if name == "dollar":
        zs = [S[p].z(t, 91) for p in ("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "USDSEK")]
        if None in zs:
            return 0
        m = (-zs[0] - zs[1] + zs[2] + zs[3] + zs[4] + zs[5]) / 6
    else:
        z = S[{"world": "ACWI", "us10y": "US10Y", "usdvnd": "USDVND"}[name]].z(t, 91)
        if z is None:
            return 0
        m = z
    return sign(m) if abs(m) >= 0.5 else 0


def families(S, group, name, t):
    s = S[name]
    out = {"trend": trend(s, t), "stretch": stretch(s, t), "breakout": breakout(s, t), "quiet": quiet(s, t)}
    if group == "vn_stocks":
        out["breadth"], out["flows"] = breadth(S, t), flows(S, t)
    out["links"] = {k: link(S, k, t) for k in LINKS[group]}
    return out


# -- checkpoints, orientation, the rule ------------------------------------------------------------------------------

def months(a, b):
    t = D(a)
    while t < D(b):
        yield t
        t = date(t.year + (t.month == 12), t.month % 12 + 1, 1)


def rows_for(S, period):
    a, b = PERIODS[period]
    out = []
    for t in months(a, b):
        for g, names in GROUPS.items():
            for name in names:
                fam = None
                for h, days in HORIZONS.items():
                    if t + timedelta(days) >= D(b):  # the outcome must be known before the next period
                        continue
                    m, sw = S[name].move(t, t + timedelta(days)), S[name].swing(t, days)
                    if m is None or not sw or S[name].at(t) is None:
                        continue
                    fam = fam or families(S, g, name, t)
                    out.append({"t": t.isoformat(), "group": g, "series": name, "h": h, "move": m, "swing": sw, "fam": fam})
    return out


def orient(dev):
    """Per group × horizon, each oriented family and each link: +1 when its vote went with the move on dev, else -1."""
    o = {}
    for g in GROUPS:
        for h in HORIZONS:
            rs = [r for r in dev if r["group"] == g and r["h"] == h]
            keys = [k for k in ORIENTED if any(k in r["fam"] for r in rs)] + [f"links.{k}" for k in LINKS[g]]
            for k in keys:
                votes = [(r["fam"][k] if "." not in k else r["fam"]["links"][k[6:]], r["move"]) for r in rs]
                votes = [(v, m) for v, m in votes if v and m]
                right = sum(sign(m) == v for v, m in votes)
                o[f"{g}:{h}:{k}"] = 1 if not votes or right >= len(votes) / 2 else -1
    return o


def votes(r, o):
    """The families' votes, oriented; the links count once: the side all voting links agree on."""
    g, h, f = r["group"], r["h"], r["fam"]
    out = {}
    for k, v in f.items():
        if k == "links":
            ls = {sign(x * o[f"{g}:{h}:links.{n}"]) for n, x in v.items() if x}
            out["links"] = ls.pop() if len(ls) == 1 else 0
        else:
            out[k] = v * o.get(f"{g}:{h}:{k}", 1)
    return out


def call(vs, k):
    up, down = sum(v > 0 for v in vs.values()), sum(v < 0 for v in vs.values())
    return 1 if up >= k and not down else -1 if down >= k and not up else 0


def score(calls, h, seed=7):
    """Hit rate, the more-common side on the same calls, and a 90% interval that resamples months (3-month blocks at 3m)."""
    if not calls:
        return {"n": 0}
    hit = [c["dir"] == sign(c["move"]) for c in calls]
    up = sum(sign(c["move"]) > 0 for c in calls) / len(calls)
    by = {}
    for c, x in zip(calls, hit):
        by.setdefault(c["t"][:7], []).append(x)
    keys = sorted(by)
    block = 3 if h == "3m" else 1
    blocks = [sum((by[k] for k in keys[i:i + block]), []) for i in range(0, len(keys), block)]
    rnd, rates = random.Random(seed), []
    for _ in range(2000):
        pick = [x for b in (rnd.choice(blocks) for _ in blocks) for x in b]
        rates.append(sum(pick) / len(pick))
    rates.sort()
    lo, hi = rates[int(0.05 * len(rates))], rates[int(0.95 * len(rates)) - 1]
    gain = st.mean(c["dir"] * c["move"] / c["swing"] for c in calls)
    return {"n": len(calls), "months": len(by), "hit": sum(hit) / len(hit), "lo": lo, "hi": hi,
            "majority": max(up, 1 - up), "gain_swings": gain,
            "big": sum(c["dir"] * c["move"] >= 0.5 * c["swing"] for c in calls) / len(calls)}


def passes(sc):
    return sc.get("n", 0) >= GATE["n"] and sc["hit"] >= GATE["hit"] and sc["lo"] > 0.5 and sc["lo"] > sc["majority"]


def run(rows, o, g, h, k):
    out = []
    for r in rows:
        if r["group"] == g and r["h"] == h:
            d = call(votes(r, o), k)
            if d:
                out.append({**r, "dir": d})
    return out


def fmt(sc):
    if not sc.get("n"):
        return "—"
    return (f"n={sc['n']:3} ({sc['months']:2} mo) right {sc['hit']:4.0%} [{sc['lo']:.0%}–{sc['hi']:.0%}] "
            f"majority {sc['majority']:4.0%} gain {sc['gain_swings']:+.2f} big {sc['big']:.0%}")


def lab(S, path):
    dev, val = rows_for(S, "dev"), rows_for(S, "val")
    o = orient(dev)
    report, rules = {}, {}
    for g in GROUPS:
        nf = len(votes(next(r for r in dev if r["group"] == g), o))
        for h in HORIZONS:
            print(f"\n== {g} · {h}   ({nf} families)")
            chosen = None
            for k in range(1, nf + 1):
                sd, sv = score(run(dev, o, g, h, k), h), score(run(val, o, g, h, k), h)
                ok = passes(sv)
                print(f"  k≥{k}  dev {fmt(sd):<78} val {fmt(sv)}{'  ✓' if ok else ''}")
                report[f"{g}:{h}:{k}"] = {"dev": sd, "val": sv, "passes": ok}
                if ok and chosen is None:
                    chosen = k
            rules[f"{g}:{h}"] = {"k": chosen, "families": nf}
            print(f"  → {'k=' + str(chosen) if chosen else 'no rule: No strong signal'}")
    frozen = {"frozen": date.today().isoformat(), "plan": "docs/SURE_CALLS_PLAN.md S1", "gate": GATE,
              "periods": PERIODS, "horizons": HORIZONS, "groups": GROUPS, "links": LINKS, "orientation": o,
              "rules": rules}
    with open(path, "w") as f:
        json.dump(frozen, f, indent=1, ensure_ascii=False)
    os.makedirs("out/sure", exist_ok=True)
    with open("out/sure/lab.json", "w") as f:
        json.dump(report, f, indent=1)
    print(f"\nfrozen: {path}")


def test(S, path, out="out/sure/test.json"):
    if not os.path.exists(path):
        sys.exit(f"no frozen rules at {path}: run the lab first")
    if os.path.exists(out):
        sys.exit(f"the test already ran: {out}")
    fr = json.load(open(path))
    rows, o, res = rows_for(S, "test"), fr["orientation"], {}
    for key, rule in fr["rules"].items():
        g, h = key.split(":")
        if not rule["k"]:
            res[key] = {"k": None, "result": "no rule"}
            print(f"{key:<16} no rule")
            continue
        sc = score(run(rows, o, g, h, rule["k"]), h)
        res[key] = {"k": rule["k"], "test": sc, "passes": passes(sc)}
        print(f"{key:<16} k={rule['k']}  {fmt(sc)}{'  ✓ PASS' if passes(sc) else '  ✗ fail'}")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({"ran": date.today().isoformat(), "rules": path, "results": res}, f, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.environ.get("MF_STATE", "data/state.db"))
    ap.add_argument("--rules", default="data/sure_rules.json")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    S = load(a.db)
    test(S, a.rules) if a.test else lab(S, a.rules)
