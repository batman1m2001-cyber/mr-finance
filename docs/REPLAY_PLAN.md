# Replay plan — View B on past news (2026-10-25)

**Why.** The business presents the agents' metrics on 30/10. The live trial began on 22/10: its 1-week moves are
first due on 28/10 and its 3-month moves in January. Precision, recall and the simulated VND need scored moves now.

**What.** Past news played back morning by morning through the trial's own steps (`scripts/replay.py`, the July
replay of B1.5 generalised), then scored by the live evaluation (AGENT_EVALUATION_PLAN: `evaluate.score`,
`finance`), shown on the trial page's View B beside the live trial with the same renderer.

## Decisions

| | Decision | Why |
|---|---|---|
| Range | 22/09 → 21/10 (30 mornings), every day as live runs | 3-day and 1-week moves all due by 28/10; extend backwards week by week if time and quota allow |
| Events | 5 a morning (`MF_TRIAL_EVENTS` default) | the live setting |
| Models | as live: CIO and grouping Sonnet 5.5, challenger Opus 5.5, through the Claude Code bridge | the numbers describe the agents the bank would run; subscription, notional cost |
| CIO review | left out | nobody approves a trial draft; approval changes no score (`shadow.RECORDED` takes pending drafts) |
| News | Google News search by outlet and day, titles and times, the four whitelisted outlets | the outlets' feeds have rotated September out; the live collection began 08/10 |
| Book | today's families frozen per morning, `late` | the holdings of a past morning were never kept |
| Event recall | not measured | the reference source began 08/10 and matches the live items |
| 3 months | the July replay (01/07 → 20/07, 12 weekday mornings, 2 events) scored again by the new evaluation | its 3-month moves are due 01/10 → 17/10; no model call |
| Fairness | the models' knowledge ends around June 2026; the agents read no market level | as B1.5 |

## Steps

1. `scripts/replay.py`: `--name`, its own state `out/replay/<name>/state.db` (the live copy without news or trial),
   the live window rule (since the morning before, at most 36 h), the morning's record (`trial_days`), the market
   data copied from live before scoring, `finance.keep(late=True)` per morning, `evaluate.score` over the mornings
   played, the report `out/trial/replays/<name>.json` and each move's drill-down beside it; `--score-only`.
2. `/api/trial` lists the replays; `/api/trial/replay/<name>` gives one's View B; `/api/trial/move/<id>?replay=`.
3. The trial page: View B's source toggle `Trực tiếp · Chạy lại <dates>`; a replay says how it differs from live.
4. Run 2026-09 through the bridge (about 90 s an event, ~4 h); score again after 28/10 for the last 1-week moves.

## Status

- 2026-10-25: steps 1–3 built; July scored again (12 mornings, 540 moves); 2026-09 running.
- 2026-10-25: the first 2026-09 run found no news from 22/09 to 06/10 — `daily.candidates` took the newest 2,000
  items of the window before dropping those published after the morning, and a replay's store holds the month ahead.
  It now reads the whole window (live, at most 36 h). Run again from a clean state.
