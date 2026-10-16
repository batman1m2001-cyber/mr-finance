# FEAT-08 — Application runs: snapshot, compute, post-check, ranking, exposure

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-BR-07, BRD-BR-08, BRD-BR-09, BRD-BR-13, BRD-BR-14, BRD-FR-401, BRD-FR-402, BRD-FR-403, BRD-FR-404, BRD-FR-405, BRD-FR-501, BRD-FR-503, BRD-RULE-DATA-02, BRD-RULE-DATA-03, BRD-RULE-DATA-07, BRD-RULE-LC-02, BRD-RULE-WF-06, BRD-NFR-01, BRD-NFR-04 |
| Users | Started by the CIO's approval; CIO manages runs; RMs and clients read the results (FEAT-13) |
| Entry points | [SCR-CIO-05 Lần áp dụng](../ux/screens/cio.md#scr-cio-05--lần-áp-dụng-application-runs), [SCR-CIO-04 Phơi nhiễm](../ux/screens/cio.md#scr-cio-04--phơi-nhiễm-exposure); `POST /api/runs/recompute`, `POST /api/runs/decide`, `GET /api/runs[/{id}[/verify]]` |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
When the CIO approves a view, apply it to every family on a frozen, hashed snapshot; check the results by rule
before anyone else sees them; rank families and flag those the RM must look at first.

## Behaviour
1. **Start** (`apply_view`, on approval): only an APPROVED view; one run per approval (`idem_key` unique) →
   `AR-nnnn-vN-k` in `COMPUTING`.
2. **Snapshot** (`make_snapshot`): every family's holdings (household scope, via the consolidation of
   FEAT-20), the market hash and date, the **whole** factor model, the branches; SHA-256 over all of it,
   stored in `run_snapshots`.
3. **Compute** (`compute`, pure): the engine per family → net worth, three-horizon bands, contributions by
   class, factor and holding, `loan_interest_3m`, `modelled_share`, `pre_review` (3-month P10 ≤ −5 % of net
   worth), and per goal (BR-08) the VND impact: the goals' pool (cash, deposits, funds, bonds, shares, gold,
   savings) runs through the same engine and each goal takes its share of the pool's bands at every horizon,
   the rest kept as `unallocated`.
4. **Post-check** (`postcheck`, rules, summary by template) → `POST_CHECKING`:
   P1 a holding > 40 % of net worth (medium) · P2 price date older than 3 days (low; > 14 medium; > 45 critical) ·
   P3 > 50 % of assets model-valued (medium) · P4 |3-month expected| > 25 % of net worth (critical) ·
   P5 no family moved at all (low).
5. **Outcome:** `EFFECTIVE`, or `NEEDS_CIO_REVIEW` if any Critical finding, or `FAILED` on an error. A new
   effective run of the same event makes the older one `SUPERSEDED`.
6. **Ranking** (worst 3-month expected first) and **exposure** (all families × factors, BR-13).
7. **CIO actions:** `make_effective` (from NEEDS_CIO_REVIEW, with a reason) or `withdraw`
   (`POST /api/runs/decide`); withdrawing the view withdraws its runs (BR-14).
8. **Recompute** (`POST /api/runs/recompute`): re-apply the view on today's data → a new run, compared with
   the old (FR-405). **Verify** (`GET /api/runs/{id}/verify`): recompute from the stored snapshot and compare to
   the dong (NFR-04).
Every status change is an audit row in the same transaction as the change.

## Implementation
`src/apply/run.py` (`family_holdings`, `make_snapshot`, `compute`, `postcheck`, `ranking`, `exposure`,
`apply_view`, `_insert_run`/`_compute_run`, `decide_run`, `withdraw_view`, `verify`), `src/apply/ops.py`,
`src/apply/graph.py` (`recompute_flow`, `run_decide_flow`); tables `application_runs`, `run_snapshots`,
`family_impacts`.

## Acceptance and tests
`tests/test_apply.py::test_approval_applies_the_view_to_every_family`, `::test_the_same_approval_applied_twice_is_one_run`,
`::test_a_run_recomputes_to_the_dong_and_tampering_is_found`, `::test_recompute_makes_a_new_run_and_supersedes_the_old`,
`::test_a_held_run_is_hidden_from_rms_until_the_cio_makes_it_effective`,
`::test_withdrawing_the_view_withdraws_its_runs_and_rms_see_the_label`,
`::test_the_rm_today_list_holds_the_flagged_families_worst_first`, `::test_the_endpoints`.
`::test_br08_each_goal_gets_its_vnd_share_of_the_pools_impact_at_every_horizon`,
`::test_br08_a_run_sums_the_vnd_impact_by_goal_from_the_same_engine_and_old_runs_still_verify`,
`::test_nfr01_one_familys_page_reads_its_row_and_the_snapshot_head_only`,
`::test_nfr01_one_read_reads_each_client_from_the_database_once_and_still_hands_out_copies`.

**NFR-01, measured** (`scripts/scale_test.py --families 6500`, 2026-10-16, 24 CPUs, SQLite): the demo households
cloned to 6,500 families with their amounts scaled ×0.5–×2; one approval applied to all of them in **167.3 s**
(BRD ≤ 300 s); with them all stored, a family's impact read 0.26 s, cách tính 0.28 s, trace 0.29 s, graph 0.29 s
(BRD ≤ 2 s). What it took: a family read decodes its own result row and the snapshot without its families
(`family_result`, `snapshot_head`; the snapshot is 27 MB at 6,500), the consolidation reads each client from the
database once per run (`people.store.one_read`), and the stores create their tables once per file
(`wealth.paths.ensure_schema`).

## Limitations
- **FR-404 on our definition ([ADR-0017](../decisions/ADR-0017-goal-impact-rule.md), Q-11 resolved):** each run stores `goal_impact` per family (`src/apply/goals.py`): the
  dated goals draw in date order on the financial assets; before = snapshot values, after = + the 3-month
  expected change; level by the goals-planning rule (≤ 0.6 Đạt, ≤ 1 Theo dõi, else Thiếu). `verify` checks it;
  runs computed before 2026-10-15 have none. Shown on SCR-CL-05 and SCR-RM-02 for the selected event, with
  the VND column (runs from 2026-10-16; older runs show the levels only).
- `loan_interest_3m` is the loans' 3-month contribution, not the extra annual interest cost (Q-10).
- Scale is measured on one machine with SQLite; the bank's database and hardware are a deployment matter.
