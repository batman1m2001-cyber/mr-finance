# Forecast desk plan — better calls than a guess (2026-10-25)

**Why.** The replays (REPLAY_PLAN) scored the agents. Direction is right on 59–67% of their calls, about as often
as "always the month's commoner direction" (September 1 week: 63% against 72% always down). Amount is worse:
not one big move (≥ 1σ) was forecast big — the forecasts are a fifth of the moves they precede. The owner asked
for precision and recall well above a guess, by any means: more features, more information, reasoning learned from
the past, a knowledge base. The scoring definitions do not change (AGENT_EVALUATION_PLAN).

**What we know (2026-10-25, July and September replays, offline).**

| | July 1w | Sep 1w | Sep 3d |
|---|---|---|---|
| AI signed IC (rank correlation forecast vs move, in σ) | 0.11 | 0.19 | 0.08 |
| Momentum (the move over the same horizon before) | 0.11 | 0.16 | −0.09 |
| AI size ranking (\|forecast\| vs \|move\|) | 0.11 | 0.13 | 0.07 |
| Forecast ÷ move, median | 0.26 | 0.18 | 0.21 |

The AI's signal is real but weak and the same size as momentum; its sizes rank the moves hardly at all. Two causes
in the design: (1) each event is forecast alone — the effect of that event — and the morning's forecasts are
averaged (`evaluate.judge_move`), while the market moves on everything; (2) the agents read no market data: not
the trend, the volatility, what is priced in (REPLAY_PLAN, "Fairness"), and they never see how their past calls
went.

## Decisions

| | Decision | Why |
|---|---|---|
| The design | a **morning desk**: one call after the morning's events that reads every draft of the morning, a market snapshot, a statistical model's odds, past headlines like today's with what followed, and its own record — and forecasts each factor at 3 days and 1 week | what is missing is the morning's whole picture and the market; one call a morning is cheap to iterate; the per-event agents (the BRD flow) stay as they are |
| Scored | as its own track by the same rules (`judge_move`: claim at 0.25σ, material at 1σ, the same verdicts) | no definition changes; the per-event track stays beside it |
| No leak | everything the desk reads is dated before the morning's origin close: market data to the origin, the knowledge base and its own record only for moves due before the origin | the replays play the past; a feature that saw the move is cheating |
| Model knowledge | LLM experiments only on July onward (the models know the world to about June 2026); the statistical model trains on 2020-01 → 2026-06 market data | an LLM run on a month it remembers measures memory |
| Dev / test | **dev** = July replay + an August replay (01/08 → 21/09, run now, the agents unchanged); **test** = 22/09 → 21/10, run **once**, frozen, after dev; then the live trial from 22/10 confirms | September's figures are already known as a baseline; nothing is tuned on them |
| Fair baselines | beside "always the period's commoner direction" (hindsight, kept as the hard bar): the trailing 60-day majority and momentum — both knowable in the morning | a bar that knows the month's outcome is not a forecaster |
| Statistics | p-values and intervals by week-block bootstrap | the fifteen factors of a morning move together and 1-week windows overlap: moves are not independent coin tosses |
| Feature gate | each source (market snapshot, statistical model, knowledge base, own record) earns its place on dev by evidence — IC or accuracy above without it — or is dropped | evidence before any step |
| Models | the desk on Sonnet 5.5 (the CIO's model), through the bridge :8091; Opus 5.5 tried once on dev | as live |
| Knowledge base | headlines of the four outlets per day, 2024-01 → 2026-06 (Google News, as the replay), each day with the factor moves after it; lexical search (BM25, `data/kb` style) — no embeddings, no model call to build | cheap, dated, auditable |

## Gate (on the test period, decided now)

At **1 week** (3 days reported beside it):

1. Direction accuracy on the desk's calls ≥ 65%, the week-block 95% interval's low end above the best fair baseline,
   and at or above the hindsight bar.
2. Recall of big moves (claimed the right way) ≥ 50%.
3. Amount: of the big moves, ≥ 40% forecast big (\|forecast\| ≥ 1σ); of the forecasts big, ≥ 30% were big (the
   base rate is ~13%).

If the gate fails, the report says so with the numbers, and the desk does not reach the live trial.

## Steps

1. **Yardstick** — `trial/lab.py`: the moves of a replay with their features, the fair baselines, the week-block
   bootstrap, the amount metrics; `scripts/forecast_lab.py` prints a track's table for dev or test.
2. **Dev data** — the August replay (`scripts/replay.py --name 2026-08 --first 2026-08-01 --last 2026-09-21`),
   background, agents unchanged.
3. **Market snapshot + statistical model** — per factor at the origin: moves over 3d/1w/1m/3m in σ, volatility
   against its year, 60-day up share, distance from the 1-year high and low. Logistic models (numpy) for P(up)
   and P(big) per horizon, trained 2020 → 2026-06, walk-forward. Kept if dev IC beats momentum.
4. **Knowledge base** — the headlines 2024 → 2026-06 fetched once (out/replay/feeds), each day's factor moves after
   it; for an event, the most similar past days and their moves. Kept if the analogs' mean move has dev IC > 0.
5. **The desk** — `trial/desk.py`: the prompt, the packet (the morning's drafts, the kept sources, its record), the
   output (per factor and horizon: direction, P(direction), expected move in σ); stored as shadow forecasts of
   kind `desk`, scored by `judge_move`. Run over dev; at most three prompt iterations on dev, each written down.
6. **Test** — frozen; run once over 22/09 → 21/10; the gate.
7. **Ship** (gate passed) — the desk after the live morning run; View B's track toggle `Từng sự kiện · Buổi sáng`.

## Status

- 2026-10-25: plan written.
- 2026-10-25, dev evidence on the calendar (every factor, every origin 01/07 → due by 21/09; overlapping
  windows, so about 11 independent weeks):
  - **Odds** (step 3): P(up) IC 0.06 (3d) / 0.04 (1w) against momentum 0.03 / −0.14: kept, weak; an edge only on
    a few factors (USDVND 1w 72%, FOREIGN_FLOW 3d 71%). P(big) AUC 0.65 / 0.73 against |momentum| 0.52 / 0.66:
    kept. Within one factor the AUC is mostly under 0.6: the size signal is which factors are wild now.
  - **Knowledge base** (step 4): 41,963 headlines 2024-01 → 2026-09. Analogs' mean move IC −0.09 (3d) / −0.10
    (1w), and −0.08 / −0.09 with the last 30 days left out: **dropped** (the rule: dev IC > 0).

## Backlog (outside advice, 2026-10-25)

An outside review (ChatGPT) proposed a broad audit-and-benchmark programme. What it adds, and where it stands:

| Item | Status |
|---|---|
| Chronological split, origin-only features, test untouched, fair baselines, honest reporting | already the plan (Decisions, Gate) |
| Configurations A existing / B quant-only / C news + quant | already the plan: agents track, odds and momentum tracks, the desk |
| Gradient boosting (LightGBM) against the logistic odds | **done**, dev calendar, settings fixed before looking: P(up) IC 0.07 vs 0.04 (1w), 0.07 vs 0.06 (3d); P(big) AUC 0.73 = 0.73 (1w), 0.67 vs 0.65 (3d). No gain worth a dependency: not kept |
| Candlesticks, ATR, OHLCV indicators | **not possible on stored data**: `market_series` holds one close per day. Needs new provider fields (open/high/low/volume) for VNINDEX and the world markets; deferred |
| Deep learning (N-BEATS, N-HiTS, TFT) | deferred: 12 series of about 1,600 trading days, and a GBM on the same inputs finds no nonlinear direction signal; no torch in the app's venv |
| D: learned fusion (a meta-model over the agents' drafts, the odds and the desk) | after the August replay: fit on July, test on August (walk-forward), once; logistic, numpy |
| Calibration (Brier, reliability) of P(up), P(big) and the desk's p | with the dev runs, in the lab's table |
| Purging / embargo for overlapping windows | the week-block bootstrap already blocks by ISO week; the training rows stop at origins whose move is due by the last training day |
- 2026-10-25, July (12 mornings with views; ~3 week blocks, CIs wide), the lab's table:
  - **desk1** (odds + record): 36% (3d) / 48% (1w) on its calls, no big call. It set the analysts' sides aside
    and reasoned from the trend.
  - **desk2** (`--prompt 2`: start from the analysts' consensus, size by p_big): 55% / 56%, recall 50% / 28%,
    said-big→big 11% / 12%. No better than the plain rule "the agents' side × the odds' size" over every move
    (55% / 53%, recall 56% / 50%).
  - The frontier in July: calling only the agents' claims holds 62–67% direction at 19–28% recall; calling every
    move reaches ~50% recall at 53–55%. No source gives the direction of the big moves the agents do not claim.
- 2026-10-26, August (01/08 → 21/08 mornings, moves due by 21/09; ~4 week blocks), each month on its own
  (direction on calls · recall of big moves):

  | Track | Jul 3d | Jul 1w | Aug 3d | Aug 1w |
  |---|---|---|---|---|
  | agents | 67% 32/48 · 19% | 62% 24/39 · 29% | 52% 130/250 · 33% | 53% 130/245 · 24% |
  | odds_all (odds' side, odds' size) | 40% · 44% | 42% · 33% | 59% · 60% | 59% · 63% |
  | odds_sel0.1 (only when \|P(up) − ½\| ≥ 0.1) | 47% 9/19 · 0% | 50% 14/28 · 0% | 66% 47/71 · 7% | 64% 67/104 · 12% |
  | fuse_all (agents' side, odds' size) | 55% · 56% | 53% · 50% | 52% · 54% | 54% · 52% |

  The months flip: the agents lead in July, the odds in August. With 3–4 week blocks a month, that is a regime
  swing, not a skill; on the two months together nothing passes 56% direction at ≥ 50% recall (odds_all 55% / 56%
  at 57% / 59%), and 65% is reached only by odds_sel0.1 on August alone, at 7–12% recall.
  - **D, learned fusion** (ridge logistic over the agents' z, the claim × share, the drafts' count, the odds' P(up)
    and P(big), the trailing move and the 60-day majority; fitted on July's 144 moves per horizon, rules fixed
    before): August 43% (3d) / 48% (1w) when sure, 44% / 54% on every move: **dropped**. July is too few weeks to
    learn weights from; the agents' weight changes sign between the horizons.
  - **desk1 / desk2 on August**: desk1 55% 36/65 (3d) / 66% 64/97 (1w) at 8% / 14% recall (in July 36% / 48%);
    desk2 50% / 53% at 41% / 40% recall. Neither holds across the months.
  - **desk3** (the third and last iteration, written from the two months): the market model's side by default,
    the analysts' only on a strong consensus with the odds near even, always a direction; sizes from P(big). Run
    on Sonnet (desk3) and once on Opus (desk3o), over July and August.
  - **Pick for the test, fixed before desk3's numbers**: the track with the highest 1w direction on calls over
    July + August together (the lab's dev table) among those with 1w recall ≥ 50%; a tie (within 1 point) goes to
    the one without a model call. odds_sel0.1 runs beside it as the selective line (high direction, low recall).
- 2026-10-26, **desk3 on dev** (July + August): 56% 341/605 (3d) / 56% 419/744 (1w) at 58% / 59% recall; Opus
  (desk3o) 56% / 56% at 58% / 60%. odds_all on the same moves: 55% / 56% at 57% / 59%. The desk reproduces the
  market model; the model call adds nothing. By the pick rule (a tie goes to the track without a model call):
  **odds_all frozen**, odds_sel0.1 beside it.
- 2026-10-26, **the test, run once** (2026-09 replay, mornings 22/09 → 21/10, scored to 26/10; 403 moves still
  pending, the rest come in after 28/10):

  | Track | 3d direction · recall · big→big | 1w direction · recall · big→big |
  |---|---|---|
  | agents | 59% 92/157 · 37% · 0% (hindsight 62%) | 63% 78/123 · 38% · 0% (hindsight 72%) |
  | odds_all (frozen) | 48% 148/308 · 60% · 14% (hindsight 58%) | 43% 132/310 · 54% · 10% (hindsight 60%) |
  | odds_sel0.1 | 50% 26/52 · 14% | 38% 32/84 · 13% |

  **The gate fails**: direction 43% against ≥ 65%, under the hindsight bar; only the recall reaches 50%, by calling
  every move. The odds' August edge did not carry into September (the months flip, as on dev). Nothing ships;
  the desk does not reach the live trial.
- Conclusion: on the data held (closes only, the outlets' headlines, the agents' drafts), no source tried gives a
  direction that holds from one month to the next at 3 days or a week: the agents, the odds (logistic and
  LightGBM), the headline analogs, a learned fusion and three desk prompts on Sonnet and Opus. What does hold is
  the size signal (P(big) AUC 0.73 at 1w: which factors are wild now). The next data worth trying is intraday
  OHLCV and flows, not another prompt.
