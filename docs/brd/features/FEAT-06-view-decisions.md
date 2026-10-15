# FEAT-06 — CIO decisions on a view

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-BR-06, BRD-BR-07, BRD-BR-14, BRD-FR-304, BRD-FR-305, BRD-RULE-DATA-07, BRD-RULE-LC-01, BRD-RULE-WF-05 |
| Users | CIO |
| Entry points | [SCR-CIO-03](../ux/screens/cio.md#scr-cio-03--nhận-định-view-detail); `POST /api/views/decide {view_id, action, by, reason, idem_key?, edits?, responses?}` |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
The human gate: the CIO edits, answers findings, previews the market effect, then approves, returns, rejects
or withdraws — each with a reason, each recorded once. Nothing is computed for any family before approval.

## Actions and when they are allowed

| Action | Allowed from | Result |
|---|---|---|
| `edit` (summary, impacts, scenarios) | PENDING_CHALLENGE, PENDING_APPROVAL | schema-checked; kept with reason and before/after hashes; back to PENDING_CHALLENGE |
| `respond` (accept/reject each finding, with reason) | PENDING_APPROVAL | answers stored per challenge |
| `challenge` (re-run after a failure) | PENDING_CHALLENGE | FEAT-05 |
| `approve` | PENDING_APPROVAL, all checks pass | APPROVED → one application run (FEAT-08) |
| `return` | PENDING_CHALLENGE, PENDING_APPROVAL | REWORK_REQUESTED; running the agent again on the event makes a new version (`VW-nnnn-v2`) |
| `reject` | PENDING_CHALLENGE, PENDING_APPROVAL | REJECTED |
| `withdraw` | APPROVED | WITHDRAWN; its runs are withdrawn (BR-14) |

Every action needs a reason of ≥ 5 characters, and each answer to a finding ≥ 10; `idem_key` makes a repeated
request a no-op (one decision, one run). When a newer version of the same event is approved, the previously
approved one becomes SUPERSEDED (`supersede_older`).

## Approval checks (`src/views/decide.py::checks`, shown in the UI as a checklist)

| | Check | Source |
|---|---|---|
| a | status is PENDING_APPROVAL | BRD-RULE-LC-01 |
| b | a challenge exists on the current content hash | BR-06, F12 |
| c | every Critical finding of it is answered | BR-06 |
| d | at least 2 scenario branches | BR-05, BRD F04 |
| e | the engine accepts the branches | §8.3 |
| f | the challenge is independent (different model) | BRD F11 |
| g | the event holds no restricted-list item | BR-04, FR-105 |

## Preview (FR-305)
`src/views/preview.py`: for each branch, every factor's move as the engine propagates it, realised at 1 week,
3 months and 12 months. Market level only, no client data. Shown under each branch (“Lan truyền ra thị trường”).

## Implementation
`src/views/decide.py`, `src/views/ops.py::decide_view`, `src/views/graph.py::decide_flow`,
`src/views/preview.py`; approval calls `apply.run.apply_view`, withdrawal calls `apply.run.withdraw_view`.

## Acceptance and tests
`tests/test_views.py::test_approval_is_idempotent_and_once_only`, `::test_return_withdraw_and_supersede`,
`::test_an_invalid_edit_is_refused_and_changes_nothing`,
`::test_an_edit_goes_back_to_the_challenger_and_a_critical_finding_blocks_approval_until_answered`,
`::test_the_reads`; `tests/test_apply.py::test_the_same_approval_applied_twice_is_one_run`,
`::test_withdrawing_the_view_withdraws_its_runs_and_rms_see_the_label`.

## Limitations
- CIO approval of model parameters (BR-07 “tham số mô hình”) has no flow: the model file is versioned but not
  approved in the product (FEAT-14).
- No anti-rubber-stamp metrics (time before approval, share approved unedited; BRD-RULE-MEAS-05).
