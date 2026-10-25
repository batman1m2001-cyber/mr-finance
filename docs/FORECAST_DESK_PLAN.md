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
