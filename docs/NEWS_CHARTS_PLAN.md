# Charts on Thử nghiệm hằng ngày (2026-10-25) — plan

**Status: done (C1–C3), 2026-10-25.** OWN-NO-04…06 implemented_verified (tests/test_agent_eval.py,
tests/ui/test_trial_eval_ui.py).

After NEWS_OPS the owner asked whether the agent news and the portfolio should have a dashboard or charts. The answer
was three charts on the page that already holds the numbers (Thử nghiệm hằng ngày), not a new dashboard: the tables
stay as each chart's table view. The owner said "go". Branch `feat/news-charts`, merged into `main`, :8030 restarted.

## C1 · View A: news kept per day, by group

- Stacked columns, one per collection day (`monitor.days`, oldest left), the four groups in their fixed colours
  (`--s1`…`--s4`) and Chưa xếp in the grey of “other”. A legend under it; the tooltip on a column gives the day's
  total and each group's count.

## C2 · View B: precision and recall by scoring day

- `evaluate.timeline(rows)` per horizon: for each due day, the rates over the moves scored by then (cumulative), with
  their hits and n. Pending, excluded and failed moves are never on it. One axis 0–100 %; a point with no denominator
  is a gap, never 0 %. The tooltip carries the k/n.

## C3 · View B: the simulated net VND by group

- `finance.timeline(rows)` per horizon: for each due day, the net (right − wrong) added up per group, over the scored
  moves that have a portfolio snapshot (a missed move counts 0 to the net). The chart says “mô phỏng” beside its
  title and under it: a calculation on the simulated families, not a real gain or loss, and not proof that the agent
  caused one.
- Before the first scoring day at a horizon the panel says so, with the first due date, and draws nothing.

## Gate

- The two timelines on synthetic rows (cumulative, pending left out, no snapshot left out); the three charts and the
  empty state in the browser, desktop and phone, no error, no sideways scroll; `check_brd_docs` green.
- Screenshots light and dark, desktop and phone; merged into `main`, :8030 restarted, both views checked as Admin.
