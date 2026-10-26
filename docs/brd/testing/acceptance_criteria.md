# Acceptance criteria

Where acceptance is defined, and how the BRD's own test plan maps to this product's tests.

- **Per requirement:** the *Acceptance* line of each requirement in [`../requirements/`](../requirements/) states
  what must be true, in the BRD's terms.
- **Per feature:** the *Acceptance and tests* section of each feature file names the tests that prove it.
- **Per requirement, status:** the traceability matrix cites the test(s) and the evidence; a requirement is
  `implemented_verified` only if a cited test exists and passed in the latest recorded run
  ([regression_coverage.md](regression_coverage.md)).
- **Per screen:** screenshots illustrate; they never verify (KIT-DOC-04).

## The BRD's test groups (§16.1) against this product

| BRD group (§16.1) | BRD content | Here | Gap |
|---|---|---|---|
| Kiểm soát | public source, timestamps, restricted list, research release gate, releaser ≠ uploader | `test_news.py::test_the_gates`, `::test_an_item_naming_the_restricted_list_is_held_until_the_cio_releases_it`; `test_research.py::test_a_report_waits_for_another_cio_and_then_reaches_the_inbox`, `::test_the_uploader_cannot_release_and_nothing_goes_out_before_its_time` | — (restricted-list release role-tested since 2026-10-15) |
| Quyền | an RM cannot open another family; a wrong role is refused | `test_views.py::test_only_the_cio_runs_the_agent_and_decides`; `test_research.py::test_a_report_waits_for_another_cio_and_then_reaches_the_inbox` | no RM-family assignment exists to test (Q-17) |
| Agent | scenario format, wrong probability refused, factor outside the catalogue refused, sources must belong to the event | `test_views.py::test_the_schema_refuses`, `::test_a_bad_draft_is_sent_back_twice_then_the_run_fails`; `test_engine.py::test_wrong_branches_are_refused` | — |
| Động cơ | propagation, mixture, duration, loans, recompute equal | `test_engine.py` (20 functions); `test_apply.py::test_a_run_recomputes_to_the_dong_and_tampering_is_found` | — |
| Nhánh mục tiêu | inference from names, no person-name confusion, urgency, a draft never “contact now”, PEP wording refused | `test_research.py` (all 9 functions) | — |
| Nhật ký | hash chain intact | `test_apply.py::test_every_step_is_in_the_audit_chain_and_it_verifies`, `::test_the_database_refuses_to_edit_the_log_and_a_forced_edit_is_found`, `::test_hmac_chain_and_no_downgrade` | — |
| Sửa theo phản biện độc lập | bands widen with horizon, P5, three-part variance; wrong factor model refused; edits re-challenged; same-session challenge cannot approve; signed channel; HMAC log; future-dated news refused; no fallback model | `test_engine.py::test_bands_are_ordered_and_widen_with_the_horizon`, `::test_the_band_has_the_three_parts`, `::test_a_wrong_factor_model_is_refused`; `test_views.py::test_an_edit_goes_back_to_the_challenger_and_a_critical_finding_blocks_approval_until_answered`, `::test_live_mode_refuses_same_models_a_cut_reply_and_another_model`; `test_apply.py::test_hmac_chain_and_no_downgrade`; `test_news.py::test_the_gates` | signed channel not built (FEAT-19) |

## The BRD's model validation (§16.2) and operating metrics (§16.3)

Not reproducible here: the back-tests need history series and the operating metrics need time and real prices
(FEAT-18, Q-22). They are requirements (BRD-RULE-MEAS-*) with status `blocked` in the matrix.

## Acceptance of a redesign

From the redesign kit (KIT-DOC-*) and the plans' gates, applied to every UI change:

1. Every capability of a replaced screen is listed with its new location (a checklist in the screen document).
2. Screenshots at desktop and phone width, light and dark, registered in `assets/README.md`.
3. No horizontal page scroll, no console error, on every touched route.
4. The legacy-sections test and the page-module test pass (`tests/test_web.py`).
5. The traceability rows of the touched requirements are updated in the same change.
