# OneWealth — speak only when sure: plan

**Status: started 2026-10-28** (owner's request that day: "we should hold back when we do not have enough evidence to
decide, focus on the big wave, long and mid term, and be quite sure about our prediction"; "in the case of unsure, we
should still have a way to keep our client's money safe"; "not only strong trends … focus on the sure"; "when we have so
many signals to trigger a wave, that's sure").

## 1. What exists

- The agents call every factor, every morning, at 3 days, 1 week and 3 months. Over July–October 2026 the 1-week
  direction was right 54% of the time against 50% for a coin (docs: the vs-random report). The forecast desk tried to
  lift that with odds, analogs and learned fusion and failed its gate (43% on September, `forecast/desk`, not merged).
- The agents' "firm" calls (P10 and P90 on the same side) were not reliably better at 1 week: 62%, 51%, 65% by month.
  At 3 months July's firm calls were 15/18, but 11 of those are two calls repeated on different mornings.
- `market_series` holds daily closes from 2020 for 24 series (VN-Index, 10 VN stocks, SPX, ACWI, gold, Brent, BTC, ETH,
  US 10Y, six FX pairs) and weekly ones for SJC, USD/VND and the VN government curve.
- A first test on those closes (2026-10-28, `scratch wave1.py`): calling the next 3 months only on a strong 6-month
  trend lifts the hit rate from 49% to 62% in 2024–2026, but "always up" scores 59% on the same months. Being picky
  alone is not enough; the trend adds little over drift.
- The client already has the pieces a safety plan needs: the risk test's loss limit (`src/risk`), the reserve in months
  of spending (dashboard liquidity), the target mix from the risk profile, and the payments ahead (`_calendar.py`).

## 2. What we build

1. **Sure calls.** For each asset group a client holds, at 1 month and 3 months: either a call ("VN-Index likely down
   over 3 months · right 7 of 10 times before") or **"No strong signal"**. A call is made only by a rule that passed
   the gate in §3 on years it was not built on. No 3-day or 1-week direction on client screens.
2. **Safety plan.** Always shown, needs no prediction: the mix against its target, the reserve, the loss limit, money
   for payments ahead. Each a check with a status and one line on what keeps it safe.
3. **Track record.** Every sure call is kept and scored when due, and the screen shows the rule's record.

## 3. Decisions

**D1. Horizons: 1 month (21 trading days) and 3 months (63).** The big wave, not the week.

**D2. The data split, fixed now.** Build on 2020-01 → 2023-12 (dev). Choose between candidates on 2024-01 → 2025-06
(validation). Test **once** on 2025-07 → the last checkpoint whose 3 months are known (2026-07). Checkpoints are monthly
(every 21 trading days), so the calls in a period do not overlap.

**D3. The gate (per asset group and horizon), fixed now.** On the test period a rule may speak for a group only if:
- it is right **≥ 70%** of the times it speaks;
- the low end of its 90% interval is above both 50% and "always say the more common side" over the same calls;
- it spoke **≥ 15 times** (fewer is not evidence).

A group that fails says "No strong signal" until a later test passes. A rule's record shown on screen is its test-period
record, then its live record as calls come due.

**D4. Sure means many signals agree.** Not one rule, and not trends only: a wave is called when many separate signals,
read from different things, point the same way at once. Each signal votes up, down or nothing, from prices only, with
no model calls. The candidates, one family each:
- **trend**: the 1-, 3-, 6- and 12-month moves against the asset's usual swing; the price against its 50- and 200-day
  averages;
- **stretch**: how far it sits from its 1-year average and from its 1-year high or low (a stretched move tends back);
- **pressure**: a quiet spell that breaks (the usual swing narrowing, then a move past the range);
- **breadth**: for VN stocks, how many of the ten move with the index;
- **flows and links**: foreign net buying on HOSE for VN stocks; the dollar and US 10Y for gold, FX and world stocks;
  the VN government curve for rates;
- **the big-move odds**: the desk's P(big) (AUC 0.73, the one signal that held), rebuilt from prices; it says a wave is
  likely, the others say which way.
Signals in one family count once together (three trend lengths are not three proofs). The agents' firm calls have
three months of history, too little to test over years, so they are not a signal; they stay the CIO's scenarios.

**D5. How many must agree is what the test decides.** For each group and horizon the lab counts the agreeing families
at every checkpoint and reads the hit rate at "at least k of n agree, none against". The smallest k whose validation
record clears §3 D3 is frozen; the test then checks it once. No learned model: the desk's learned fusion flipped from
month to month, and a count of agreeing families is easy to test and to explain ("trend, breadth and foreign flows
agree; nothing against").

**D6. Safety needs no forecast and never says buy or sell.** It reads the client's own numbers and states the check
("Reserve covers 4 months of spending, target 6"), in the words the views already allow (no "nên mua", §8.2).

**D7. Where it shows.** A "Market calls" block on News and Prediction (client and RM) and one line on the dashboard
news card; the assistant reads the same calls, with the no-guess line in its tool result. English goes into `en.js`.

## 4. Phases and gates

| Phase | What | Gate |
|---|---|---|
| S1 | `scripts/sure_lab.py`: checkpoints, every signal family's vote, the agreement count; dev and validation per group × horizon × k | Table in §5; k per group chosen on validation, frozen in `data/sure_rules.json` |
| S2 | The test, run once | §3 D3 per group × horizon; the result written in §5 whatever it is |
| S3 | `src/sure/`: today's calls from `market_series` with the frozen rules, the record, a daily job, `/api/sure-calls` | Tests; the calls match the lab's for the same day |
| S4 | The safety plan per client and scope | Tests on C01–C05; every check has a number and a status |
| S5 | Screens: Market calls, the dashboard line, EN phrases | Screenshots EN/VI, desktop + phone; no Vietnamese left that is not data |
| S6 | The assistant reads both; merge, :8030 restarted, the iPhone app checked | A real question answered from the calls, cost counted |

## 5. Status

- Plan written 2026-10-28.
- **S1 done 2026-10-28** (`scripts/sure_lab.py`, frozen in `data/sure_rules.json`, full table in out/sure/lab.json):
  **no group passes at any k.** Six groups × two horizons, 5–7 families each. More families agreeing looked better on
  dev (2021–2023, the 2022 fall and the 2023 rebound trended cleanly) and did not hold on validation (2024–mid 2025):

  | Group · horizon, best k on validation | Dev right / majority | Validation right / majority | Calls (months) |
  |---|---|---|---|
  | VN stocks · 3m, k≥3 | 71% / 55% | 57% / 57% | 76 (13) |
  | VN stocks · 1m, k≥4 | 65% / 64% | 75% / 50% | 8 (3) |
  | Gold · 3m, k≥2 | 50% / 50% | 69% / 69% | 13 (7) |
  | World stocks · 3m, k≥2 | 65% / 54% | 83% / 83% | 18 (10) |
  | VN rates · 3m, k≥2 | 80% / 57% | 27% / 64% | 11 (7) |
  | USD/VND · 1m, k≥2 | 88% / 50% | 64% / 64% | 11 (11) |

  Where validation reads high it only matches "always the common side" (world stocks rose; gold rose). Where many
  families agree the calls get too few to be evidence (≤ 14). So every group says **No strong signal**.
- **S2 not run**: there is no frozen rule to test, and the test period stays unread for one.
- Gate note: a group with one series (USD/VND) can speak at most 13 times in the test period, under D3's 15.
