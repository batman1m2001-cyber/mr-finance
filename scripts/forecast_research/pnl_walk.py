"""Long-period money test, walk-forward: for each year Y in 2023..2026, the odds trained 2020-04 .. the end of Y-1,
then every Monday of Y each tradable factor is held one week long (P(up) > 0.5) or short; P&L in % (bp-free, no
costs) against always-long and 1w momentum. Run from the fi worktree."""
import os, sys
from collections import defaultdict
from datetime import date, timedelta
os.environ["MF_STATE"] = "out/lab/market.db"
sys.path[:0] = ["src", "."]
from measure import realised
from trial import odds, shadow

S = realised.series()
TRADE = ["VNINDEX", "GOLD", "USDVND", "BTC", "GLOBAL_EQ", "BRENT", "DXY"]
pct = lambda s, a, b: (s.level(b) / s.level(a) - 1) * 100 if s.level(a) and s.level(b) else None  # noqa: E731
tot = defaultdict(lambda: defaultdict(float))
for Y in (2023, 2024, 2025, 2026):
    O = odds.Odds(S, last=f"{Y - 1}-12-31")
    d = date(Y, 1, 2)
    while d.weekday() != 0:
        d += timedelta(days=1)
    end = date(2026, 9, 21) if Y == 2026 else date(Y, 12, 31)
    year = defaultdict(lambda: defaultdict(float)); n = 0
    while d + timedelta(days=7) <= end:
        o, due = (d - timedelta(days=1)).isoformat(), (d + timedelta(days=6)).isoformat()
        for f in TRADE:
            r = pct(S[f], o, due)
            got = O.of(f, o, "1w")
            if r is None or not got:
                continue
            mom = S[f].move((d - timedelta(days=8)).isoformat(), o) or 0
            for name, pos in (("odds", 1 if got["p_up"] > .5 else -1),
                              ("odds_sure", (1 if got["p_up"] > .5 else -1) if abs(got["p_up"] - .5) >= .05 else 0),
                              ("always_long", 1), ("momentum", 1 if mom > 0 else -1)):
                year[name][f] += pos * r
        n += 1
        d += timedelta(days=7)
    print(f"\n{Y} ({n} weeks), % summed over weekly holds")
    for name, by in year.items():
        print(f"  {name:12} total {sum(by.values()):7.1f}   " + "  ".join(f"{f} {v:6.1f}" for f, v in by.items()))
        for f, v in by.items():
            tot[name][f] += v
print("\nALL 2023 → 2026-09")
for name, by in tot.items():
    print(f"  {name:12} total {sum(by.values()):7.1f}   " + "  ".join(f"{f} {v:6.1f}" for f, v in by.items()))
