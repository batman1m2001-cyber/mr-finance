# OneWealth: measuring the news agents (plan)

**Status: in progress.** Started 2026-10-24 by the owner's request “Refactor and Implement News & Portfolio Impact
Agent Evaluation”.

Two questions to answer:
- How much news comes in each day?
- Are the agents (Agent CIO, which writes the scenarios, and Agent Phản biện, which checks them) right, and what
  is that worth in VND on the simulated portfolio?

Every number is shown with its count. Where data is missing, the page says the number is unavailable; it never
shows zero instead.

## 1. What already exists (audit, 2026-10-24)

| Need | Already there | Missing |
|---|---|---|
| A record of each news run | `news_runs`: every 10-minute run, with fetched, accepted, refused and skipped per source, the source's error, and the run's duplicates, added and held (`news/ops.py::keep`) | start, end and duration; status; configured vs attempted sources; counts by category; relevant count; missing metadata. The 1,278 runs before this plan cannot have these fields: they show as unavailable |
| Collection time vs publication time | `news_items.ingested` and `news_items.published` | a report that keeps the two apart |
| Categories | `rules.classify` gives the event type; `trial/segments.py` maps it to macro, policy or sector | the business's four groups (real estate, stocks, policy/macro, other) |
| Independent ground truth for news | `news/reference.py` (KPI-02). Google News VN Business stories that ≥ 2 outlets carry and that name an engine factor are *important*. Each is judged collected or not, and the judgement keeps the matched item | whether a collected important story reached a trial event (the agents' recall of events) |
| Predictions | `shadow_forecasts`: 450 rows, every factor × 3d / 1w / 3m for each trial draft. Each row keeps the origin (the close before the run), due date, expected value, P10/P50/P90, the branches, the call, the event and the segment. The news ids are in `trial_events` | a portfolio snapshot frozen with the prediction; deduplication when several drafts from one morning predict the same move |
| Scoring | `forecasts.judge`, run by `trial_score` every 15 min. It records realised, inside the band, and direction hit; otherwise `no_data` or waiting | materiality; precision, recall, missed; estimation error; a record per scored move that keeps its reason; excluded (no series) kept apart from failed (data never came) |
| VND impact | `engine.loadings.exposures(holdings, model, months)`: each holding's VND per unit of each factor. `apply.run.family_holdings()` reads every family the way the dashboard does | VND for a realised or predicted move. The trial's drafts are never applied, so no `family_impacts` rows exist for them |
| Cost | `agent_runs.nodes[]` records tokens in/out, ms, attempt, model and error for each model call | cost; cached tokens; the grouping call (only its token total is kept). See §3 |
| Dashboard | `web/pages/trial.js` (CIO · Mô hình · Thử nghiệm hằng ngày), `/api/trial`, the “Cách tính” metric registry (`explain/metrics.py`) | View A, View B, drill-down |

**Found during the audit.** This morning's trial (2026-10-24 08:30) failed:
- The job record says `AgentError: Không gọi được mô hình anthropic/claude-sonnet-5.5: InternalServerError`.
- The bridge (`scripts/claude_bridge.py`) found the `claude` binary once, when it started on 2026-10-21, in the VS Code
  extension's versioned folder. An extension update removed that folder, so `create_subprocess_exec` raises
  `FileNotFoundError` and the bridge answers 500.
- Nothing reached `logs/claude_bridge.jsonl`, and the trial page shows no failure.

Today's run is not repeated. Run at 16:30, the agents could have read today's market session, which is later than
their origin (the close of 10-23); that is future leakage. The day is reported as *failed*, with the reason.

## 2. Definitions (settled here)

### 2.1 Collection

Each run records a funnel:
1. **fetched**: items in the feeds.
2. **too old** (skipped) and **refused** by the gates.
3. **duplicates**: already kept, by link or source + title.
4. **unique**: new rows.
5. **retained**: new in the inbox.
6. **relevant**: retained and of medium or high relevance. This is the agents' own candidate rule
   (`trial/daily.py::candidates`). The definition is shown on the page.

Status:
- **ok** when every attempted source answered;
- **partial** when some failed;
- **failed** when none answered.

**Missing metadata:**
- no publication time (refused by the gate, reason kept);
- no summary;
- no category.

**The four groups:**

| Group | From the event type | From the source, when there is no event type |
|---|---|---|
| real estate | real_estate | — |
| stocks | equity | the stock sections (`*_ck`, `vietstock_cp`) |
| policy/macro | monetary, fx, credit, commodity, geopolitics, regulation | the macro sections |
| other | gold, crypto | — |

Anything else is *chưa xếp*. Factors map the same way:
- real estate: VN_HOUSE, RE_SPREAD;
- stocks: VNINDEX, GLOBAL_EQ, FOREIGN_FLOW, FIN_SPREAD;
- policy/macro: VN_RATE, VN_GOV, USDVND, US10Y, DXY;
- other: GOLD, BTC, BRENT, SJC_GAP.

Daily trends are by **collection day** (Vietnam time). The trial's existing collection block stays by
**publication day**. Both are labelled.

### 2.2 The unit scored, and deduplication

The unit is a **market move**: one factor, one horizon, from one origin (the close before a trial morning).
- A move is scored once, however many drafts that morning predicted it. Drafts from overlapping news are one
  claim, not several.
- The drafts' claims on a move are merged:
  - all material ones in the same direction → one claim in that direction;
  - material ones in opposite directions → *conflicting*: excluded from precision, with that reason, and never
    counted incorrect;
  - none material → a *hold*.
- The claim's expected value is the mean of the drafts' expected values. Each draft's own value stays in the
  record, so the drill-down shows them.

### 2.3 Materiality (configurable)

`data/evaluation.json` holds the settings, and each scoring record keeps the values it was scored with:
- `material_sigma` (default 1.0);
- `claim_share` (default 0.25).

Rules:
- A **realised move is material** when |realised| ≥ `material_sigma` × vol_month × √months. That is a one-sigma
  move at the horizon, from the factor model in force.
- A **claim is material** when |expected| ≥ `claim_share` × vol_month × √months. This is the same edge that turns
  a forecast into mua/bán rather than giữ in the trial (`shadow.CALL_SHARE`).

Ground truth comes from the market, not from the agent:
- `market_series` through `measure.realised.Series.move`, the same path FEAT-18 scores with;
- for news events, the reference stories (§2.5).

### 2.4 Verdict of a move

| Verdict | When |
|---|---|
| `pending` | not yet due, or due but its data has not come (`waiting`) |
| `excluded` | the factor has no series (assumed); the claim is conflicting; or a 3d horizon is reported separately as *uncalibrated* |
| `failed` | due 30 days ago and still no data (`no_data`) |
| `correct` | material claim, material move, same direction |
| `incorrect` | material claim, and either the opposite direction or a move that was not material |
| `missed` | material move, and that morning's drafts claimed nothing material for it |
| `quiet` | no material claim and no material move (a correct hold; it adds nothing to precision or recall) |
| `no_run` | a trial morning with no draft (the run failed, as on 2026-10-24): its material moves are listed as missed *with no run*, kept apart from the agents' own misses |

Rates:
- **Precision** = correct ÷ (correct + incorrect).
- **Recall** = correct ÷ (correct + missed). It is shown twice: with and without the no-run mornings.
- **Direction hit** = same sign ÷ scored moves where expected ≠ 0.
- **Estimation error** = |expected − realised|. It is shown in the factor's unit and in typical moves
  (÷ vol_month √months), so factors can be averaged.

These are computed for 3d, 1w and 3m (3m shows pending until January 2027). 3d is labelled *uncalibrated*, as
the trial already says.

Coverage counts the moves at each verdict: due, scored, pending, failed and excluded.

Pending, excluded and conflicting moves are never counted as incorrect.

### 2.5 Event recall from the reference

Of the important reference stories on trial days that were collected (their match has a `news_id`), how many
were in a trial event's `news_ids`.
- This is the agents' choice of events, measured against an outside list.
- Each miss is listed with its title.

### 2.6 Financial impact (simulated, never causal)

At each trial morning the families' holdings are frozen once, through `apply.run.family_holdings()` (the
dashboard's read), as each family's **exposure** E[f, h]:
- the VND per unit of factor f at horizon h;
- computed with `engine.loadings.exposures`, the engine's own loadings, not a new model.

Mornings before this plan (10-22, 10-23) are frozen late, from today's holdings, and labelled *late*. The demo
holdings did not change in between, so `wealth_store` is checked for writes in that window.

For a scored move with realised x:
- **The move's effect on the book** = Σ families E × x (realised); and Σ E × expected (predicted).
- **The value of acting on a claim**, with d the claimed direction: a position the size of the family's exposure,
  in direction d, is worth `d × x × |E|`.
  - correct claim → **value of correct calls**, +|E x|;
  - incorrect claim → **loss from incorrect calls**, −|E x|. When the move was not material, the loss is the
    small x actually realised.
  - **Correct negative warnings**: the correct claims where E × x < 0 (the move hurt the family and the agent
    called it).
- **Missed opportunity** = |E x| of the missed moves. It is shown beside the net, not subtracted from it.
- **Net** = value of correct calls − loss from incorrect calls.

Every VND figure:
- is labelled *mô phỏng: nếu gia đình làm theo toàn bộ*;
- carries n (moves);
- is broken down by the four groups (via the factor);
- is never shown for a pending or excluded move.

It is a counterfactual on the simulated book. It never says the agent caused a gain or a loss.

## 3. Cost: why it is 0, and the fix

Root cause, from the code and the logs:
1. `views/agents.py::call_model` keeps `usage.prompt_tokens` and `completion_tokens`, and never reads a cost.
2. `llm:cio` and `llm:challenger` point at the Claude Code bridge (`LLM_AGENT_BASE_URL=127.0.0.1:8091`). The bridge
   gets `total_cost_usd` from `claude -p` and writes it to `logs/claude_bridge.jsonl` (257 calls, US$10.84
   notional), but its reply drops it. It also folds cached input into `prompt_tokens`.
3. The grouping call keeps only a token total in `trial_events.group_tokens`.

The fix:
- **The bridge** returns `usage.cost` = `total_cost_usd`, with `usage.cost_kind: "notional"` (the subscription
  bills nothing per call) and `prompt_tokens_details.cached_tokens`. It finds `claude` on each call (§1). A start
  failure becomes a logged 502 with its reason.
- **`call_model`** keeps `cost_usd` (None when the provider sent none, never 0), `cost_kind` (provider |
  notional | None), `tokens_cached`, `latency_ms`, the provider (the endpoint's host) and the status. These go
  into the node records already written.
- **The grouping call** and a failed morning go into a `trial_days` record. The record keeps the morning's
  status, its error, its candidates and the grouping call's meta.
- **Past runs:** a node's notional cost is filled in from the bridge's log when exactly one log line has the same
  model and tokens within its run's time window. Those are labelled *từ nhật ký cầu nối*. A node with no match
  stays unavailable.

## 4. Phases

Branch `feat/agent-eval` in `/home/thanglq/mr-finance-eval`; merged into main and deployed on :8030 after each
phase's gate.

| # | What | Gate |
|---|---|---|
| E0 | This plan; the bridge fix (§1, §3 bridge part) | bridge restarted, a live call returns cost and cached tokens |
| E1 | **Collection:** the run funnel, status, sources and groups in `news_runs` (`news/ops.py`); `news/monitor.py` for runs → days (trends), with old runs' missing fields as unavailable | tests: funnel sums, a failed source, partial/failed status, duplicates counted once, old run shape, groups |
| E2 | **Accuracy:** `trial/evaluate.py` with moves, merged claims, verdicts, precision, recall, missed, direction, error, coverage, and the reference event recall; `eval_scores` written by `trial_score`; `trial_days` | tests: each verdict, conflicting drafts, a pending move never incorrect, no-data vs excluded, no-run mornings, no future leakage (origin < the run's day), the threshold read from config |
| E3 | **Financial:** exposures frozen per morning (`eval_snapshots`); VND per move and family; the totals by group, with n | tests: E × x by hand, correct/incorrect/missed/negative-warning sums, a pending move adds nothing, a late snapshot labelled |
| E4 | **Cost:** `call_model` meta; the backfill from the bridge log; `trial/costs.py` per agent (calls, tokens, cost, p50/p95 latency, retries, errors) | tests: missing cost stays None; the backfill matches exactly one line or none |
| E5 | **Dashboard:** the trial page in two views, A Thu thập tin and B Hiệu quả agent, with a drill-down per move (news → claim → outcome → verdict → VND by family); metrics registered in `explain/metrics.py`; screenshots on desktop and phone | page test; every rate shows its denominator; BRD checker green |

Docs: OWN-EV-01…08 in `docs/brd/requirements/owner_requirements.md` and the matrix, plus a changelog line.

## 5. Not done (per the request)

- No new agent.
- No new engine or simulation; the engine's loadings are used as they are.
- No backtesting platform. The July replay stays as it is.
- No reruns that would leak the future.
- No numbers for moves not yet due: 3m stays pending until 2027-01-20, and the page says so.
