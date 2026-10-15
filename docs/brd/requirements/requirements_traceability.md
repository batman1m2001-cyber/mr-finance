# Requirements traceability matrix

The **only** place where a requirement's implementation status is stated. Chain: requirement → feature → screen →
code / API → test → evidence. Status vocabulary: [README §4](../README.md#4-status-vocabulary). Every test cited
for an `implemented_verified` row exists in `tests/` (checked by `scripts/check_brd_docs.py`) and passed in the
latest recorded run ([regression_coverage.md](../testing/regression_coverage.md#latest-recorded-run): 2026-10-16,
195 passed).

Last full review: **2026-10-15**, against commit b5e1cb1 and the BRD with SHA-256 `5ea9d8da…de1e3`.

## 0. Summary

| Set | Rows | implemented_verified | implemented_unverified | partially_implemented | planned | not_implemented | blocked | out_of_scope_demo | not_applicable |
|---|---|---|---|---|---|---|---|---|---|
| BRD numbered (BR, FR, NFR) | 61 | 47 | 3 | 9 | 2 | 0 | 0 | 0 | 0 |
| BRD success metrics (KPI) | 7 | 2 | 0 | 1 | 0 | 0 | 0 | 4 | 0 |
| BRD rules (RULE) | 97 | 71 | 4 | 10 | 2 | 1 | 0 | 7 | 2 |
| Original brief (BRIEF) | 29 | 28 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| Redesign kit (KIT) | 19 | 9 | 2 | 1 | 0 | 0 | 0 | 0 | 7 |
| Owner requests (OWN) | 14 | 10 | 3 | 0 | 0 | 0 | 0 | 0 | 1 |

**Traceability completeness:** every one of the BRD's 61 numbered requirements, its 7 success metrics and the 97
rules extracted from its text has a row, a source location, and a status (100 % inventoried). **Implementation
completion is not 100 %:** of the 61 numbered requirements, 47 are implemented and verified by tests; the rest are
partial, unverified, planned, not implemented or blocked, each with its reason below. (The `not_applicable` KIT rows
are the documentation rules this repository itself follows.) Counts are recomputed by the checker.

## 1. BRD numbered requirements

| ID | BRD § | Requirement (short) | Features | Screens | Code / API | Tests | Status | Evidence, gaps |
|---|---|---|---|---|---|---|---|---|
| BRD-BR-01 | §4 | Three news sources, each labelled | FEAT-01, 03 | SCR-CIO-01 | `src/news/rules.py::classify`; `src/research/store.py::_to_inbox` | `tests/test_news.py::test_classification_by_source_then_words`, `tests/test_research.py::test_a_report_waits_for_compliance_and_then_reaches_the_inbox` | implemented_verified | “Quốc tế / Trong nước / Độc quyền” labels |
| BRD-BR-02 | §4 | White-listed public sources; published ≤ ingested | FEAT-01 | SCR-CIO-01 | `src/news/rules.py::gate` | `tests/test_news.py::test_the_gates` | implemented_verified | The white list is a generated file, not a Compliance-approved config version (BRD-FR-701) |
| BRD-BR-03 | §4 | Research enters only when released by another person after its time | FEAT-03 | SCR-CIO-06, SCR-CMP-02 | `src/research/store.py::decide` | `tests/test_research.py::test_the_uploader_cannot_release_and_nothing_goes_out_before_its_time`, `tests/test_research.py::test_a_report_waits_for_compliance_and_then_reaches_the_inbox` | implemented_verified | |
| BRD-BR-04 | §4 | Restricted-list mentions held for Compliance | FEAT-01, 02 | SCR-CMP-01 | `src/news/rules.py`, `src/news/ops.py::release`, `src/views/decide.py` (check g) | `tests/test_news.py::test_an_item_naming_the_restricted_list_is_held_until_compliance_releases_it`, `tests/test_views.py::test_an_event_groups_news_and_a_restricted_mention_holds_it` | implemented_verified | Holding blocks approval; only Compliance may release, with a reason (DEF-03 fixed 2026-10-15) |
| BRD-BR-05 | §4 | 2–4 scenarios with probability, shocks, sources; AI gives no numbers | FEAT-04, 07 | SCR-CIO-03 | `src/views/schema.py`, `src/engine` | `tests/test_views.py::test_the_schema_refuses`, `tests/test_views.py::test_the_mock_agent_writes_a_valid_view_and_records_every_node` | implemented_verified | |
| BRD-BR-06 | §4 | Independent challenge before approval; critical findings answered | FEAT-05, 06 | SCR-CIO-03 | `src/views/ops.py::review`, `src/views/decide.py::checks` (b, c, f) | `tests/test_views.py::test_an_edit_goes_back_to_the_challenger_and_a_critical_finding_blocks_approval_until_answered` | implemented_verified | “2nd line” = different model / rules (Q-05) |
| BRD-BR-07 | §4 | CIO approves scenarios and model parameters; nothing computed before | FEAT-06, 08, 14 | SCR-CIO-03 | `src/views/decide.py`, `src/apply/run.py::apply_view` | `tests/test_views.py::test_approval_is_idempotent_and_once_only`, `tests/test_apply.py::test_approval_applies_the_view_to_every_family` | implemented_verified | Scenario approval; model parameters through FR-701 (CIO proposes, a second CIO approves): `tests/test_config.py::test_a_run_freezes_the_thresholds_and_the_model_in_force` |
| BRD-BR-08 | §4 | VND per position and loan, 3 horizons, E and P5/P10/P50/P90; summed by class, factor, family, goal; one engine for ranking, alerts, goals, explanation | FEAT-07, 08 | SCR-CL-05, SCR-RM-02 | `src/engine/scenario.py::evaluate`, `src/apply/run.py::compute` | `tests/test_engine.py::test_the_contributions_add_up_to_the_expected_change`, `tests/test_engine.py::test_bands_are_ordered_and_widen_with_the_horizon`, `tests/test_apply.py::test_approval_applies_the_view_to_every_family` | partially_implemented | Goals: funding before/after per run (FR-404), not a VND sum per goal; the pre-BRD alerts and stress tests use other methods (Q-03, ADR-0007) |
| BRD-BR-09 | §4 | RM pre-review at a 3-month bad case ≤ −5 % | FEAT-08, 13 | SCR-RM-01 | `src/apply/run.py` (`PRE_REVIEW_PCT`), `src/apply/reads.py::rm_today` | `tests/test_apply.py::test_the_rm_today_list_holds_the_flagged_families_worst_first` | implemented_verified | |
| BRD-BR-10 | §4 | Regulations delaying goals abroad reach the right families, no AML data | FEAT-10 | SCR-RM-01, SCR-CL-05 | `src/procedural/goals.py` | `tests/test_research.py::test_the_brd_example_draft_aml_rule_and_a_study_abroad_goal`, `tests/test_research.py::test_inference_from_a_goals_name` | implemented_verified | |
| BRD-BR-11 | §4 | AI drafting reads no client data, goals, RM notes | FEAT-04 | — | `src/views/ops.py::gather`, `src/views/agents.py` | `tests/test_views.py::test_live_mode_uses_two_models_and_no_client_data_reaches_them` | implemented_verified | Code-level barrier in one process (ADR-0009) |
| BRD-BR-12 | §4 | Every number traceable; immutable log | FEAT-09, 11 | SCR-RM-03, SCR-CMP-03 | `src/apply/trace.py`, `src/control/audit.py` | `tests/test_apply.py::test_the_trace_goes_from_a_number_back_to_the_news`, `tests/test_apply.py::test_the_database_refuses_to_edit_the_log_and_a_forced_edit_is_found` | implemented_verified | Log covers news-impact writes only (FEAT-11) |
| BRD-BR-13 | §4 | CIO sees all clients' exposure by factor | FEAT-08 | SCR-CIO-04 | `src/apply/run.py::exposure` | `tests/test_apply.py::test_approval_applies_the_view_to_every_family` | implemented_verified | |
| BRD-BR-14 | §4 | CIO withdraws a view; RMs see “Đã thu hồi” | FEAT-06, 08, 13 | SCR-CIO-03, SCR-RM-02 | `src/apply/run.py::withdraw_view` | `tests/test_apply.py::test_withdrawing_the_view_withdraws_its_runs_and_rms_see_the_label` | implemented_verified | |
| BRD-BR-15 | §4 | Accuracy over time vs the forecast band | FEAT-18, 35 | SCR-CIO-12 | `src/measure/backtest.py::run`, `src/measure/forecasts.py` (`record` at approval, `score` by job `accuracy_score` 18:30); `GET /api/accuracy` | `tests/test_accuracy.py::test_walking_forward_on_history_that_follows_the_model_covers_about_80_percent`, `tests/test_accuracy.py::test_an_approved_view_keeps_its_forecasts_and_they_are_scored_when_due` | implemented_verified | The model walked forward over 2022–2026 market history, and every approved view's 15 factors × 3 horizons scored as each horizon passes. Not the mock advisory record (Q-19) |
| BRD-FR-101 | §6.1 | RSS every 10 minutes | FEAT-01 | SCR-CIO-01 | `app/main.py` Job `news_ingest` (`every="10m"`), `src/news/ops.py::fetch` | `tests/test_news.py::test_one_run_counts_each_source_keeps_refusals_aside_and_survives_a_broken_feed` | implemented_unverified | Fetching is tested; the 10-minute schedule is declared and runs on the live demo, but no test asserts it |
| BRD-FR-102 | §6.1 | Classify, score relevance, suggest event type | FEAT-01 | SCR-CIO-01 | `src/news/rules.py::classify` | `tests/test_news.py::test_classification_by_source_then_words` | implemented_verified | |
| BRD-FR-103 | §6.1 | CIO inbox: filter, dismiss, group | FEAT-02 | SCR-CIO-01 | `app/web.py::news_inbox`, `dismiss_flow`, `event_flow` | `tests/test_news.py::test_the_inbox_filters_and_dismiss`, `tests/test_views.py::test_an_event_groups_news_and_a_restricted_mention_holds_it` | implemented_verified | Dismiss: CIO only (DEF-03 fixed) |
| BRD-FR-104 | §6.1 | Public source and timestamps checked before an event | FEAT-01, 02 | — | `src/news/rules.py::gate`, `src/events/store.py` | `tests/test_news.py::test_the_gates` | implemented_verified | The event step's refusal of non-new items is not tested on its own |
| BRD-FR-105 | §6.1 | Hold events naming the restricted list until Compliance allows | FEAT-02 | SCR-CMP-01, SCR-CIO-03 | `src/events/store.py`, `src/views/decide.py` (g) | `tests/test_views.py::test_an_event_groups_news_and_a_restricted_mention_holds_it`, `tests/test_news.py::test_an_item_naming_the_restricted_list_is_held_until_compliance_releases_it` | implemented_verified | Only Compliance may allow (DEF-03 fixed) |
| BRD-FR-201 | §6.2 | Upload a report with its fields | FEAT-03 | SCR-CIO-06 | `src/research/store.py::upload` | `tests/test_research.py::test_a_report_waits_for_compliance_and_then_reaches_the_inbox` | implemented_verified | |
| BRD-FR-202 | §6.2 | Compliance releases/rejects, note ≥ 20, restricted list, releaser ≠ uploader | FEAT-03 | SCR-CMP-02 | `src/research/store.py::decide` | `tests/test_research.py::test_a_report_naming_the_restricted_list_is_not_released`, `tests/test_research.py::test_the_uploader_cannot_release_and_nothing_goes_out_before_its_time` | implemented_verified | |
| BRD-FR-203 | §6.2 | Unreleased or early research not in the inbox, not attachable | FEAT-03 | SCR-CIO-01 | `src/research/store.py` | `tests/test_research.py::test_a_report_waits_for_compliance_and_then_reaches_the_inbox` | implemented_verified | |
| BRD-FR-204 | §6.2 | Regulation-note fields; goal branch, not price events | FEAT-03, 10 | SCR-CIO-06 | `src/research/store.py` | `tests/test_research.py::test_the_brd_example_draft_aml_rule_and_a_study_abroad_goal` | implemented_verified | |
| BRD-FR-301 | §6.3 | CIO agent: 4 groups, ≤ 2 debate rounds, synthesis, ≤ 2 retries | FEAT-04 | SCR-CIO-02, 03 | `src/views/graph.py::cio_agent_flow` | `tests/test_views.py::test_the_mock_agent_writes_a_valid_view_and_records_every_node`, `tests/test_views.py::test_a_bad_draft_is_sent_back_twice_then_the_run_fails` | implemented_verified | |
| BRD-FR-302 | §6.3 | View: impact rows −3…+3 and 2–4 branches | FEAT-04 | SCR-CIO-03 | `src/views/schema.py` | `tests/test_views.py::test_the_schema_refuses` | implemented_verified | |
| BRD-FR-303 | §6.3 | Challenger before approval and on edits; 3 severities | FEAT-05 | SCR-CIO-03 | `src/views/ops.py::review`, `src/views/challenger.py` | `tests/test_views.py::test_an_edit_goes_back_to_the_challenger_and_a_critical_finding_blocks_approval_until_answered` | implemented_verified | |
| BRD-FR-304 | §6.3 | CIO edits, answers, approves/returns/rejects/withdraws with reasons | FEAT-06 | SCR-CIO-03 | `src/views/decide.py` | `tests/test_views.py::test_return_withdraw_and_supersede`, `tests/test_views.py::test_an_invalid_edit_is_refused_and_changes_nothing` | implemented_verified | |
| BRD-FR-305 | §6.3 | Market-level preview per branch before approval | FEAT-06 | SCR-CIO-03 | `src/views/preview.py` | `tests/test_views.py::test_the_reads` | implemented_verified | |
| BRD-FR-306 | §6.3 | Policy agent and policy radar | FEAT-16 | — | — | — | planned | News plan N5 (optional); “radar” undefined (Q-09) |
| BRD-FR-307 | §6.3 | Three run modes: live, inbox, mock | FEAT-04, 19 | SCR-CIO-02 | `src/views/agents.py::resolve_mode` | `tests/test_views.py::test_live_mode_uses_two_models_and_no_client_data_reaches_them`, `tests/test_views.py::test_the_mock_agent_writes_a_valid_view_and_records_every_node` | partially_implemented | Live and mock built; inbox mode not (FEAT-19, N5) |
| BRD-FR-401 | §6.4 | On approval: snapshot, compute all, hashed run | FEAT-08 | SCR-CIO-05 | `src/apply/run.py::apply_view`, `make_snapshot` | `tests/test_apply.py::test_approval_applies_the_view_to_every_family`, `tests/test_apply.py::test_the_same_approval_applied_twice_is_one_run` | implemented_verified | |
| BRD-FR-402 | §6.4 | Family result: bands, contributions to each position, loan interest, modelled share | FEAT-08 | SCR-RM-02 | `src/apply/run.py::compute` | `tests/test_apply.py::test_approval_applies_the_view_to_every_family` | implemented_verified | “Loan interest cost” interpreted as the loans' 3-month contribution (Q-10) |
| BRD-FR-403 | §6.4 | Rank all families; all-client summary by factor | FEAT-08 | SCR-CIO-04 | `src/apply/run.py::ranking`, `exposure` | `tests/test_apply.py::test_approval_applies_the_view_to_every_family`, `tests/test_apply.py::test_the_rm_today_list_holds_the_flagged_families_worst_first` | implemented_verified | |
| BRD-FR-404 | §6.4 | Goal impact: funding before/after, Đạt / Theo dõi / Thiếu | FEAT-08, 26 | SCR-CL-05, SCR-RM-02 | `src/apply/goals.py::goal_impacts`, `src/apply/run.py::compute` (`goal_impact` in `family_impacts`) | `tests/test_apply.py::test_a_run_gives_each_goal_its_funding_before_and_after_with_a_level`, `tests/test_apply.py::test_goal_levels_follow_the_funding_and_the_surplus`, `tests/test_apply.py::test_a_run_recomputes_to_the_dong_and_tampering_is_found` | implemented_verified | Built 2026-10-15 on our definition, decided in ADR-0017 (Q-11 resolved); runs computed before then have none |
| BRD-FR-405 | §6.4 | Recompute and compare; withdraw a run | FEAT-08 | SCR-CIO-05 | `src/apply/graph.py::recompute_flow`, `run_decide_flow` | `tests/test_apply.py::test_recompute_makes_a_new_run_and_supersedes_the_old`, `tests/test_apply.py::test_a_held_run_is_hidden_from_rms_until_the_cio_makes_it_effective` | implemented_verified | |
| BRD-FR-406 | §6.4 | “Cách tính” and trace to the news | FEAT-09 | SCR-RM-03 | `src/apply/trace.py` | `tests/test_apply.py::test_the_trace_goes_from_a_number_back_to_the_news` | implemented_verified | Staff only (Q-14) |
| BRD-FR-501 | §6.5 | Post-check rules; summary | FEAT-08 | SCR-CIO-05 | `src/apply/run.py::postcheck` | `tests/test_apply.py::test_a_held_run_is_hidden_from_rms_until_the_cio_makes_it_effective` | implemented_verified | Summary by template, not the challenger (Q-12) |
| BRD-FR-502 | §6.5 | RMs see only post-checked runs, labelled | FEAT-13 | SCR-RM-02 | `src/apply/reads.py` (`VISIBLE`) | `tests/test_apply.py::test_a_held_run_is_hidden_from_rms_until_the_cio_makes_it_effective`, `tests/test_apply.py::test_withdrawing_the_view_withdraws_its_runs_and_rms_see_the_label` | implemented_verified | |
| BRD-FR-503 | §6.5 | Flag “RM xem trước” at 3-month P10 ≤ −5 % | FEAT-08 | SCR-RM-01 | `src/apply/run.py::compute` (`pre_review`) | `tests/test_apply.py::test_the_rm_today_list_holds_the_flagged_families_worst_first` | implemented_verified | |
| BRD-FR-601 | §6.6 | RM declares outflow purpose/country; inference otherwise | FEAT-10 | SCR-RM-02 | `src/procedural/goals.py::infer`, `goal_outflow_flow` | `tests/test_research.py::test_inference_from_a_goals_name`, `tests/test_research.py::test_the_brd_example_draft_aml_rule_and_a_study_abroad_goal` | implemented_verified | |
| BRD-FR-602 | §6.6 | Match notes to goals; milestone and level | FEAT-10 | SCR-RM-01 | `src/procedural/goals.py::match` | `tests/test_research.py::test_the_brd_example_draft_aml_rule_and_a_study_abroad_goal`, `tests/test_research.py::test_an_issued_rule_close_to_the_milestone_means_contact_now_and_late_rules_are_a_note` | implemented_verified | BRD §10 example reproduced (2026-12-07, remind) |
| BRD-FR-603 | §6.6 | Shown on RM home, Goals tab, Research page | FEAT-10 | SCR-RM-01, SCR-CIO-06, SCR-CL-05 | `src/apply/reads.py::rm_today`, `app/web.py::goal_regulation` | `tests/test_research.py::test_the_reads_and_the_rm_list` | implemented_unverified | Also on the planning tab since 2026-10-16 (SCR-CL-03, Q-20): browser-checked, no automated UI test |
| BRD-FR-604 | §6.6 | Refuse AML wording | FEAT-03, 10 | SCR-CIO-06 | `src/procedural/goals.py::forbidden_words` | `tests/test_research.py::test_a_regulation_note_with_aml_wording_is_refused` | implemented_verified | |
| BRD-FR-701 | §6.7 | Versioned, owned configuration; propose then approve | FEAT-14 | SCR-CIO-09 | `src/control/config.py`, `POST /api/config/propose`, `POST /api/config/decide` | `tests/test_config.py::test_a_proposal_changes_nothing_until_a_second_owner_approves_it`, `tests/test_config.py::test_one_person_kinds_and_rejection`, `tests/test_config.py::test_the_restricted_list_in_force_holds_the_news`, `tests/test_config.py::test_a_run_freezes_the_thresholds_and_the_model_in_force` | partially_implemented | Factor model, thresholds, restricted list, news sources versioned with owners and approval (2026-10-16); return assumptions and forbidden phrases not yet configuration |
| BRD-FR-702 | §6.7 | Hash-chained log; integrity check; export | FEAT-11 | SCR-CMP-03 | `src/control/audit.py` | `tests/test_apply.py::test_every_step_is_in_the_audit_chain_and_it_verifies`, `tests/test_apply.py::test_hmac_chain_and_no_downgrade`, `tests/test_brd_gaps.py::test_the_audit_export_is_the_whole_chain_and_reverifies` | implemented_verified | Export `GET /api/audit/export` (JSON with the check, or CSV) since 2026-10-16 |
| BRD-FR-703 | §6.7 | Agent catalogue | FEAT-15 | SCR-CIO-08 | `src/views/catalogue.py::catalogue`, `GET /api/agents/catalogue` | `tests/test_catalogue.py::test_one_entry_per_agent_with_the_six_fields`, `tests/test_catalogue.py::test_the_latest_run_and_the_quality_figures_come_from_the_store` | implemented_verified | Five entries (the BRD §8 four + Copilot) with purpose, owner, risk, model (BRD default and configured), latest run, open-source references (2026-10-16) |
| BRD-FR-704 | §6.7 | Per-step trace of the CIO agent | FEAT-04 | SCR-CIO-03 | `src/views/agents.py::_record` | `tests/test_views.py::test_the_mock_agent_writes_a_valid_view_and_records_every_node` | implemented_verified | |
| BRD-FR-801 | §6.8 | CIO newsletter | FEAT-17 | — | — | — | planned | News plan N5 (optional) |
| BRD-NFR-01 | §15 | 6,500 families ≤ 5 min; family page ≤ 2 s | FEAT-08 | — | `src/apply/run.py` | — | implemented_unverified | Measured 0.44 s for 5 families (news plan §9); never run at scale |
| BRD-NFR-02 | §15 | News to inbox ≤ 10 min; CIO agent ≤ 15 min | FEAT-01, 04 | SCR-CIO-13 | Job `news_ingest` (every 10 min); `src/measure/reports.py::timing`; `GET /api/measure` | `tests/test_accuracy.py::test_the_reports_read_approval_time_edits_and_news_to_rm_time` | implemented_verified | Measured monthly: on the demo 41 % of news reached the inbox within 10 min (median 35 min — the feeds publish late); CIO agent runs 0.4–1.1 min |
| BRD-NFR-03 | §15 | 99.5 %; AI failure does not stop computing or viewing | FEAT-05, 07 | — | engine has no AI dependency | `tests/test_views.py::test_a_failed_challenger_keeps_the_draft_and_can_run_again` | partially_implemented | Availability is a deployment matter (not measured) |
| BRD-NFR-04 | §15 | Same snapshot → same result to the dong | FEAT-07, 08 | SCR-CIO-05 | `src/apply/run.py::verify` | `tests/test_engine.py::test_the_same_inputs_give_the_same_numbers_to_the_dong`, `tests/test_apply.py::test_a_run_recomputes_to_the_dong_and_tampering_is_found` | implemented_verified | |
| BRD-NFR-05 | §15 | Exact money; no floats for balances | FEAT-07 | — | integer balances; one rounding place in `src/engine` | `tests/test_engine.py::test_the_contributions_add_up_to_the_expected_change` | implemented_verified | Interpretation of ADR-0011 (Q-13) |
| BRD-NFR-06 | §15 | New factors, classes, agents by configuration; provider change without architecture change | FEAT-07, 14 | — | `data/factor_model.json`; `resources.yaml` | `tests/test_engine.py::test_a_wrong_factor_model_is_refused` | partially_implemented | Factors and providers by configuration; agents and asset classes are code |
| BRD-NFR-07 | §15 | Encryption, secret store, pen and prompt-injection tests | — | — | `.env` secrets | `tests/test_views.py::test_an_injection_in_the_news_stays_data` | partially_implemented | Prompt-injection test only; the rest is the bank deployment's |
| BRD-NFR-08 | §15 | Client data in Vietnam; never to an AI provider | FEAT-04, 22, 23 | — | barrier in `gather` | `tests/test_views.py::test_live_mode_uses_two_models_and_no_client_data_reaches_them` | partially_implemented | News-impact AI verified; the pre-BRD statement and chat steps send client text when AI is on — accepted for the mock demo by the owner (ADR-0018), still required for a bank deployment |
| BRD-NFR-09 | §15 | Immutable log; retention per bank rules | FEAT-11 | SCR-CMP-03 | `src/control/audit.py` | `tests/test_apply.py::test_the_database_refuses_to_edit_the_log_and_a_forced_edit_is_found` | implemented_verified | Retention is a bank policy; demo reset drops the log |
| BRD-NFR-10 | §15 | Token limits, daily budget, cost per event | FEAT-04 | — | `MAX_TOKENS`, `budget()` in `src/views/agents.py`; `src/views/store.py::tokens` | `tests/test_views.py::test_live_mode_refuses_same_models_a_cut_reply_and_another_model`, `tests/test_brd_gaps.py::test_the_daily_token_budget_stops_a_live_call_and_cost_is_kept_per_event` | implemented_verified | Per-call caps; daily budget (`AGENT_DAILY_TOKENS`, default 300 000) refuses a call over it; tokens per event in `/api/agents` (no money cost: no price per token configured) |
| BRD-NFR-11 | §15 | Vietnamese; “cách tính” on every number; desktop and phone | FEAT-09 | all | `web/` | `tests/test_web.py::test_every_routed_page_module_exists_and_is_served` | partially_implemented | Phone/desktop checked by screenshots; trace on news-impact numbers for staff only (Q-14) |
| BRD-NFR-12 | §15 | Central logs; alerts on feed, agent, chain failures | FEAT-01, 11 | SCR-CIO-01, SCR-CMP-03 | feed-health strip; `GET /api/audit/verify` | `tests/test_news.py::test_the_inbox_endpoint_returns_items_and_feed_health` | partially_implemented | Failures are visible on demand; nothing alerts |

## 1b. BRD success metrics

| ID | Metric | Status | Evidence, gaps |
|---|---|---|---|
| BRD-KPI-01 | News → RM ready ≤ 2 h | partially_implemented | Measured per event, monthly (`src/measure/reports.py::speed`, SCR-CIO-13); “urgent ≤ 30 min” not measured: nothing defines urgent news |
| BRD-KPI-02 | Important news collected ≥ 95 % | out_of_scope_demo | Pilot measurement; “important” undefined (Q-07) |
| BRD-KPI-03 | Direction right ≥ 70 % | implemented_verified | `src/measure/backtest.py`, `src/measure/forecasts.py`, SCR-CIO-12, `tests/test_accuracy.py::test_walking_forward_on_history_that_follows_the_model_covers_about_80_percent`. History (engine step 2 given the other factors, walk-forward 2022–2026): VN-Index 72 % at 3 months, 96 % at 12 months, 57 % at 1 week. Views: scored as horizons pass, < 24 so far |
| BRD-KPI-04 | Band coverage 70–90 % | implemented_verified | `tests/test_accuracy.py::test_walking_forward_on_history_that_follows_the_model_covers_about_80_percent`; history walk-forward pooled 72 % (1 week), 77 % (3 months), 75 % (12 months); per factor on SCR-CIO-12 (gold and the VN yields too narrow) |
| BRD-KPI-05 | Recommendations reviewed and logged 100 % | out_of_scope_demo | No recommendation is sent; views and runs are reviewed and logged (FEAT-06, 11) |
| BRD-KPI-06 | RM contacts from system signals ≥ 50 % | out_of_scope_demo | Pilot measurement (no CRM) |
| BRD-KPI-07 | High alerts opened ≥ 70 % | out_of_scope_demo | Pilot measurement (no client app) |

## 2. BRD rules (`BRD-RULE-*`)

| ID | Features | Status | Tests / evidence | Notes |
|---|---|---|---|---|
| BRD-RULE-SCOPE-01 | — | implemented_verified | `tests/test_views.py::test_the_schema_refuses` | No order, transfer or transaction capability exists; views refuse buy/sell words |
| BRD-RULE-SCOPE-02 | FEAT-13 | implemented_verified | `tests/test_apply.py::test_the_client_reads_asset_classes_only_with_the_labels` | Client reads carry no ticker |
| BRD-RULE-SCOPE-03 | FEAT-20, 22 | not_applicable | — | The product keeps its pre-BRD connectors (Q-04, ADR-0003) |
| BRD-RULE-SCOPE-04 | FEAT-07 | implemented_verified | `tests/test_engine.py::test_proxies_are_labelled_and_cash_has_no_load` | Property by a house-price proxy, labelled |
| BRD-RULE-SCOPE-05 | FEAT-13 | not_applicable | — | Nothing is sent; the client view exists in-app (ADR-0008, Q-21) |
| BRD-RULE-ROLE-01 | FEAT-12 | implemented_verified | `tests/test_views.py::test_only_the_cio_runs_the_agent_and_decides` | |
| BRD-RULE-ROLE-02 | FEAT-12, 13 | implemented_verified | `tests/test_apply.py::test_a_held_run_is_hidden_from_rms_until_the_cio_makes_it_effective`, `tests/test_auth.py::test_an_rm_sees_only_the_families_assigned_to_them`, `tests/test_auth.py::test_lists_over_every_family_show_only_the_families_the_person_may_see` | Post-checked only; own families only (people.rm_id, ADR-0020) |
| BRD-RULE-ROLE-03 | FEAT-12 | implemented_verified | `tests/test_research.py::test_the_uploader_cannot_release_and_nothing_goes_out_before_its_time`, `tests/test_news.py::test_an_item_naming_the_restricted_list_is_held_until_compliance_releases_it` | Research release and restricted-list release both Compliance only |
| BRD-RULE-ROLE-04 | FEAT-12 | partially_implemented | `tests/ui/test_routes.py::test_every_route_renders_without_errors` | Admin signs in and sees configuration, agents and the audit log; sources and data-loading screens are F5 |
| BRD-RULE-ROLE-05 | — | out_of_scope_demo | — | Later phase in the BRD |
| BRD-RULE-ROLE-06 | FEAT-13 | implemented_verified | `tests/test_apply.py::test_the_client_reads_asset_classes_only_with_the_labels` | Demo client view |
| BRD-RULE-WF-01 | FEAT-01 | implemented_unverified | live demo first fetch 2 s | Schedule not asserted |
| BRD-RULE-WF-02 | FEAT-02, 04 | implemented_verified | `tests/test_views.py::test_an_event_groups_news_and_a_restricted_mention_holds_it` | |
| BRD-RULE-WF-03 | FEAT-04 | implemented_unverified | one live run: 26 s | |
| BRD-RULE-WF-04 | FEAT-05 | implemented_unverified | one live run: 13 s | |
| BRD-RULE-WF-05 | FEAT-06 | implemented_verified | `tests/test_views.py::test_return_withdraw_and_supersede` | SLA is organisational |
| BRD-RULE-WF-06 | FEAT-08 | implemented_verified | `tests/test_apply.py::test_approval_applies_the_view_to_every_family` | 0.44 s for 5 families |
| BRD-RULE-WF-07 | FEAT-13 | implemented_verified | `tests/test_apply.py::test_the_rm_today_list_holds_the_flagged_families_worst_first` | |
| BRD-RULE-WF-08 | — | out_of_scope_demo | — | Specialist process is a later phase |
| BRD-RULE-WF-09 | FEAT-04, 08 | implemented_verified | `tests/test_views.py::test_live_mode_uses_two_models_and_no_client_data_reaches_them`, `tests/test_accuracy.py::test_the_reports_read_approval_time_edits_and_news_to_rm_time` | Barrier verified; end-to-end time measured per event (KPI-01) |
| BRD-RULE-ZONE-01 | FEAT-19 | out_of_scope_demo | — | One process (ADR-0009) |
| BRD-RULE-ZONE-02 | FEAT-19 | planned | — | Signed inbox, news plan N5 |
| BRD-RULE-ZONE-03 | FEAT-04 | implemented_verified | `tests/test_views.py::test_the_schema_refuses` | Same checks applied to live and mock output |
| BRD-RULE-ZONE-04 | FEAT-08, 09 | implemented_verified | `tests/test_apply.py::test_the_trace_goes_from_a_number_back_to_the_news` | Templates only; no AI on family data |
| BRD-RULE-ZONE-05 | FEAT-04, 08, 11 | implemented_verified | `tests/test_apply.py::test_every_step_is_in_the_audit_chain_and_it_verifies` | |
| BRD-RULE-ZONE-06 | FEAT-19 | out_of_scope_demo | — | |
| BRD-RULE-AI-01 | FEAT-04, 05, 16 | partially_implemented | `tests/test_views.py::test_live_mode_uses_two_models_and_no_client_data_reaches_them` | CIO agent, challenger, templates built; policy agent not |
| BRD-RULE-AI-02 | FEAT-14 | not_implemented | — | Models from env, prompt version constant; no two-person change |
| BRD-RULE-AI-03 | FEAT-04 | implemented_verified | `tests/test_views.py::test_live_mode_refuses_same_models_a_cut_reply_and_another_model` | |
| BRD-RULE-AI-04 | FEAT-04 | implemented_verified | `tests/test_views.py::test_a_bad_draft_is_sent_back_twice_then_the_run_fails` | |
| BRD-RULE-AI-05 | FEAT-04 | implemented_verified | `tests/test_estimate.py::test_a_stressed_branch_without_vnindex_and_re_spread_is_refused` | Asked in the prompt and enforced on every agent answer by the format check (`src/views/schema.py`), all modes; a CIO edit that drops one is a critical challenger finding (R2) the CIO must answer before approving |
| BRD-RULE-AI-06 | FEAT-04 | implemented_verified | `tests/test_views.py::test_the_schema_refuses` | |
| BRD-RULE-AI-07 | FEAT-04 | implemented_verified | `tests/test_views.py::test_an_injection_in_the_news_stays_data` | |
| BRD-RULE-AI-08 | FEAT-04, 07 | implemented_verified | `tests/test_views.py::test_the_schema_refuses` | |
| BRD-RULE-AI-09 | FEAT-04 | implemented_verified | `tests/test_views.py::test_an_invalid_edit_is_refused_and_changes_nothing` | Inbox mode does not exist yet |
| BRD-RULE-AI-10 | FEAT-04, 05 | implemented_verified | `tests/test_views.py::test_live_mode_refuses_same_models_a_cut_reply_and_another_model` | |
| BRD-RULE-AI-11 | FEAT-04 | implemented_verified | `tests/test_views.py::test_the_mock_agent_writes_a_valid_view_and_records_every_node` | |
| BRD-RULE-AI-12 | FEAT-04 | implemented_verified | `tests/test_views.py::test_live_mode_refuses_same_models_a_cut_reply_and_another_model` | |
| BRD-RULE-AI-13 | FEAT-04, 19 | partially_implemented | `tests/test_views.py::test_the_mock_agent_writes_a_valid_view_and_records_every_node` | Live runs synchronously in the request; no job queue; no inbox |
| BRD-RULE-AI-14 | FEAT-04 | implemented_verified | `tests/test_views.py::test_live_mode_uses_two_models_and_no_client_data_reaches_them` | Pre-BRD AI steps are outside the BRD's agents (NFR-08 row) |
| BRD-RULE-ENG-01 | FEAT-07 | implemented_verified | `tests/test_engine.py::test_the_same_inputs_give_the_same_numbers_to_the_dong` | |
| BRD-RULE-ENG-02 | FEAT-07 | implemented_verified | `tests/test_engine.py::test_priced_in_multipliers_scale_the_move_and_its_uncertainty` | |
| BRD-RULE-ENG-03 | FEAT-07 | implemented_verified | `tests/test_engine.py::test_the_core_moves_as_given_and_the_rest_by_conditional_expectation`, `tests/test_engine.py::test_two_core_shocks_follow_the_solved_system` | |
| BRD-RULE-ENG-04 | FEAT-07 | implemented_verified | `tests/test_engine.py::test_the_band_has_the_three_parts` | |
| BRD-RULE-ENG-05 | FEAT-07 | implemented_verified | `tests/test_engine.py::test_bands_are_ordered_and_widen_with_the_horizon` | |
| BRD-RULE-ENG-06 | FEAT-07 | implemented_verified | `tests/test_engine.py::test_the_expected_change_is_the_probability_weighted_branch_mean` | |
| BRD-RULE-ENG-07 | FEAT-07, 08 | implemented_verified | `tests/test_engine.py::test_the_contributions_add_up_to_the_expected_change` | |
| BRD-RULE-ENG-08 | FEAT-07 | implemented_verified | `tests/test_engine.py::test_the_model_has_the_brds_fifteen_factors_and_both_regimes_are_valid_covariances` | Stressed volatilities assumed, not from 2022 data (ADR-0004) |
| BRD-RULE-ENG-09 | FEAT-07 | implemented_verified | `tests/test_engine.py::test_a_wrong_factor_model_is_refused` | |
| BRD-RULE-ENG-10 | FEAT-07 | implemented_verified | `tests/test_engine.py::test_the_model_has_the_brds_fifteen_factors_and_both_regimes_are_valid_covariances` | |
| BRD-RULE-ENG-11 | FEAT-07, 35 | implemented_verified | `tests/test_estimate.py::test_volatility_and_shrunk_correlation_come_from_55_months_and_the_rest_stays_assumed`, `tests/test_market.py::test_each_factor_says_where_it_comes_from` | “Ước lượng” from 55 months with 20 % shrinkage, else “Giả định”; per-factor source (FEAT-35); the estimate becomes the model once a second CIO approves it |
| BRD-RULE-ENG-12 | FEAT-07 | implemented_verified | `tests/test_engine.py::test_bonds_lose_when_yields_and_their_sector_spread_rise`, `tests/test_engine.py::test_fpt_also_moves_with_the_dollar`, `tests/test_engine.py::test_loans_move_net_worth_the_right_way` | Betas are assumed, not estimated from TCBS prices |
| BRD-RULE-ENG-13 | FEAT-07 | implemented_verified | `tests/test_engine.py::test_the_brd_gold_example_has_its_structure` | Structure reproduced; the example's numbers are illustrative in the BRD |
| BRD-RULE-GOAL-01 | FEAT-10 | implemented_verified | `tests/test_research.py::test_the_brd_example_draft_aml_rule_and_a_study_abroad_goal` | |
| BRD-RULE-GOAL-02 | FEAT-10 | implemented_verified | `tests/test_research.py::test_inference_from_a_goals_name` | |
| BRD-RULE-GOAL-03 | FEAT-10 | implemented_verified | `tests/test_research.py::test_inference_from_a_goals_name`, `tests/test_research.py::test_the_brd_example_draft_aml_rule_and_a_study_abroad_goal` | |
| BRD-RULE-GOAL-04 | FEAT-10 | implemented_verified | `tests/test_research.py::test_the_brd_example_draft_aml_rule_and_a_study_abroad_goal` | |
| BRD-RULE-GOAL-05 | FEAT-10 | implemented_verified | `tests/test_research.py::test_country_limits_and_past_goals` | |
| BRD-RULE-GOAL-06 | FEAT-10 | implemented_verified | `tests/test_research.py::test_an_issued_rule_close_to_the_milestone_means_contact_now_and_late_rules_are_a_note` | |
| BRD-RULE-GOAL-07 | FEAT-10 | implemented_verified | `tests/test_research.py::test_a_regulation_note_with_aml_wording_is_refused` | |
| BRD-RULE-GOAL-08 | FEAT-10 | implemented_verified | `tests/test_research.py::test_the_brd_example_draft_aml_rule_and_a_study_abroad_goal` | |
| BRD-RULE-DATA-01 | FEAT-20, 08 | implemented_verified | `tests/test_consolidate.py::test_every_client_consolidates_from_every_tier` | Trust labels (pre-BRD) and modelled share |
| BRD-RULE-DATA-02 | FEAT-08 | implemented_verified | `tests/test_apply.py::test_a_held_run_is_hidden_from_rms_until_the_cio_makes_it_effective` | P2 rule |
| BRD-RULE-DATA-03 | FEAT-08 | implemented_verified | `tests/test_apply.py::test_a_run_recomputes_to_the_dong_and_tampering_is_found` | |
| BRD-RULE-DATA-04 | FEAT-01 | implemented_verified | `tests/test_news.py::test_the_gates` | |
| BRD-RULE-DATA-05 | FEAT-11 | implemented_verified | `tests/test_apply.py::test_every_step_is_in_the_audit_chain_and_it_verifies` | News-impact writes only |
| BRD-RULE-DATA-06 | FEAT-11 | implemented_verified | `tests/test_apply.py::test_the_database_refuses_to_edit_the_log_and_a_forced_edit_is_found` | |
| BRD-RULE-DATA-07 | FEAT-06, 08 | implemented_verified | `tests/test_apply.py::test_the_same_approval_applied_twice_is_one_run` | |
| BRD-RULE-DATA-08 | — | implemented_verified | `tests/test_apply.py::test_the_endpoints` | Formats in [domain_model.md](../architecture/domain_model.md#4-identifiers) |
| BRD-RULE-DATA-09 | FEAT-04 | implemented_verified | `tests/test_views.py::test_live_mode_uses_two_models_and_no_client_data_reaches_them` | By graph inputs, not DB permissions |
| BRD-RULE-DATA-10 | — | out_of_scope_demo | — | Bank migration guidance |
| BRD-RULE-LC-01 | FEAT-06 | implemented_verified | `tests/test_views.py::test_return_withdraw_and_supersede` | |
| BRD-RULE-LC-02 | FEAT-08 | implemented_verified | `tests/test_apply.py::test_a_held_run_is_hidden_from_rms_until_the_cio_makes_it_effective`, `tests/test_apply.py::test_recompute_makes_a_new_run_and_supersedes_the_old` | |
| BRD-RULE-LC-03 | FEAT-03 | implemented_verified | `tests/test_research.py::test_a_report_naming_the_restricted_list_is_not_released` | |
| BRD-RULE-LC-04 | FEAT-19 | planned | — | News plan N5 |
| BRD-RULE-SEC-01 | FEAT-12 | implemented_verified | `tests/test_auth.py::test_a_session_is_signed_and_expires`, `tests/test_auth.py::test_nothing_under_api_opens_without_a_session`, `tests/ui/test_signin.py::test_sign_in_with_the_form_and_with_a_demo_account_then_sign_out` | Own accounts, signed session (ADR-0020); a bank swaps the form for SSO |
| BRD-RULE-SEC-02 | FEAT-12 | partially_implemented | `tests/test_views.py::test_only_the_cio_runs_the_agent_and_decides`, `tests/test_auth.py::test_a_customer_sees_only_their_own_family`, `tests/test_auth.py::test_nobody_acts_in_someone_elses_name` | Every read checks the session, role and family (ADR-0020); writes check the acting person; a refused `POST` answers 500, not 403 |
| BRD-RULE-SEC-03 | FEAT-13, 28 | implemented_unverified | — | “Nội bộ” on the advisory pages and, since 2026-10-16, on the staff views of impact, trace, graph, Toàn cảnh and Hôm nay; browser-checked |
| BRD-RULE-SEC-04 | FEAT-03, 14 | partially_implemented | `tests/test_research.py::test_the_uploader_cannot_release_and_nothing_goes_out_before_its_time`, `tests/test_config.py::test_a_proposal_changes_nothing_until_a_second_owner_approves_it` | Research SoD and the configuration two-person rule (factor model, thresholds, restricted list; ADR-0016); newsletter (not built) and prompts/models (not configuration) not covered |
| BRD-RULE-SEC-05 | FEAT-14 | partially_implemented | `tests/test_config.py::test_wrong_owner_wrong_content_and_a_second_pending_are_refused`, `tests/test_config.py::test_one_person_kinds_and_rejection` | Owners enforced: CIO (factor model, thresholds), Compliance (restricted list), Admin (news sources); return assumptions, forbidden phrases, consent, prompts, models, price sources, ticker mapping not yet configuration |
| BRD-RULE-SEC-06 | FEAT-03, 04 | implemented_verified | `tests/test_research.py::test_a_report_waits_for_compliance_and_then_reaches_the_inbox` | |
| BRD-RULE-SEC-07 | FEAT-19 | out_of_scope_demo | — | No inbox mode |
| BRD-RULE-SEC-08 | FEAT-11 | implemented_verified | `tests/test_apply.py::test_hmac_chain_and_no_downgrade` | WORM anchoring is the bank's |
| BRD-RULE-SEC-09 | FEAT-09, 11 | implemented_verified | `tests/test_apply.py::test_the_trace_goes_from_a_number_back_to_the_news` | |
| BRD-RULE-SEC-10 | FEAT-11, 12 | implemented_verified | `tests/test_brd_gaps.py::test_health_lists_the_protections_that_are_off` | `/healthz` lists each protection and which are off (HMAC, two models, client text kept from AI, Copilot router, sign-in) |
| BRD-RULE-CONTENT-01 | FEAT-13, 17 | partially_implemented | `tests/test_apply.py::test_the_client_reads_asset_classes_only_with_the_labels` | Flow 2 in-app; flow 1 (newsletter) not built; flow 3 out of scope |
| BRD-RULE-CONTENT-02 | FEAT-13 | partially_implemented | `tests/test_apply.py::test_the_client_reads_asset_classes_only_with_the_labels` | AI label, responsible person, time, “không phải khuyến nghị”, RM path, per-item sources (outlets and count, no headline: `tests/test_brd_gaps.py::test_the_client_sees_outlets_not_headlines`): yes; COI disclosure: no |
| BRD-RULE-CONTENT-03 | FEAT-03 | partially_implemented | `tests/test_research.py::test_the_uploader_cannot_release_and_nothing_goes_out_before_its_time` | Release-time rule enforced; COI is free text |
| BRD-RULE-CONTENT-04 | FEAT-13 | implemented_verified | `tests/test_apply.py::test_the_client_reads_asset_classes_only_with_the_labels` | |
| BRD-RULE-MEAS-01 | FEAT-18, 35 | implemented_verified | `tests/test_accuracy.py::test_walking_forward_on_history_that_follows_the_model_covers_about_80_percent`, `tests/test_accuracy.py::test_fewer_than_24_observations_is_not_a_conclusion` | Per factor and horizon (1 week, 3, 12 months), 70–90 % accepted, < 24 observations “chưa đủ 24 quan sát” |
| BRD-RULE-MEAS-02 | FEAT-18, 35 | implemented_verified | `tests/test_accuracy.py::test_walking_forward_on_history_that_follows_the_model_covers_about_80_percent`, `tests/test_accuracy.py::test_an_approved_view_keeps_its_forecasts_and_they_are_scored_when_due` | History: engine step 2 out of sample; views: the sign of the expected move against the realised one |
| BRD-RULE-MEAS-03 | FEAT-18 | implemented_verified | `tests/test_accuracy.py::test_an_event_without_an_approved_view_is_a_miss_after_a_day` | `src/measure/reports.py::misses` on SCR-CIO-13: high-relevance news not grouped (dismissed, held, > 1 day in the inbox) and events with no effective run, by cause and month. “Important” = relevance high (Q-07) |
| BRD-RULE-MEAS-04 | FEAT-04, 06, 15 | implemented_verified | `tests/test_catalogue.py::test_the_latest_run_and_the_quality_figures_come_from_the_store` | `catalogue.quality`: share of decided views the CIO edited, findings and critical ones, agent runs and errors, format retries — 7 days and all time, on SCR-CIO-08 |
| BRD-RULE-MEAS-05 | FEAT-06, 18 | implemented_verified | `tests/test_accuracy.py::test_the_reports_read_approval_time_edits_and_news_to_rm_time` | `src/measure/reports.py::rubber_stamp` on SCR-CIO-13: CIO minutes from ready to approved, share without edits, approvals under 2 min (our signal) |
| BRD-RULE-MEAS-06 | — | out_of_scope_demo | — | Pilot control group |
| BRD-RULE-MEAS-07 | FEAT-04 | partially_implemented | — | No news-agent eval set; only the pre-BRD `statement_reading` eval exists |
| BRD-RULE-MEAS-08 | FEAT-07 | implemented_verified | `tests/test_estimate.py::test_out_of_sample_coverage_is_near_80_percent_when_the_history_is_what_the_model_says`, `tests/test_estimate.py::test_a_band_too_narrow_is_said_to_be` | Out of sample 2/2024–8/2026 on real history: [model_validation.md](../testing/model_validation.md) (85 % inside P10–P90); Model Risk's conclusion is theirs |

## 3. Original brief (`BRIEF-*`)

| ID | Features | Screens | Status | Tests / evidence | Notes |
|---|---|---|---|---|---|
| BRIEF-DATA-01 | FEAT-20 | SCR-CL-02 | implemented_verified | `tests/test_consolidate.py::test_every_client_consolidates_from_every_tier` | Mock sources |
| BRIEF-DATA-02 | FEAT-20, 22 | SCR-CL-02 | implemented_verified | `tests/test_wealth.py::test_open_api_reads_only_what_the_client_consented_to`, `tests/test_statements.py::test_the_rules_read_every_sample` | |
| BRIEF-DATA-03 | FEAT-23 | SCR-CL-02 | implemented_verified | `tests/test_declare.py::test_the_agent_records_through_its_tools`, `tests/test_declare.py::test_the_rules_read_the_sentences_the_demo_needs` | |
| BRIEF-DATA-04 | FEAT-20, 21 | SCR-CL-01, 02 | implemented_verified | `tests/test_dashboard.py::test_net_worth_is_assets_less_debt_with_its_month_change_and_confidence` | |
| BRIEF-DATA-05 | FEAT-20 | shell | implemented_verified | `tests/test_consolidate.py::test_the_family_view_holds_only_members_who_consented` | |
| BRIEF-RISK-01 | FEAT-24 | SCR-CL-04 | implemented_verified | `tests/test_risk.py::test_every_path_asks_8_to_12_questions` | |
| BRIEF-RISK-02 | FEAT-24 | SCR-CL-04 | implemented_verified | `tests/test_risk.py::test_the_drop_question_uses_the_client_s_own_portfolio` | |
| BRIEF-RISK-03 | FEAT-24 | SCR-CL-04 | implemented_verified | `tests/test_risk.py::test_wanting_more_than_one_can_bear_is_said_out_loud` | |
| BRIEF-RISK-04 | FEAT-24 | SCR-CL-04 | partially_implemented | `tests/test_risk.py::test_who_says_bold_but_sold_in_the_dip_is_stepped_down` | Say-vs-do built; re-ask triggers not (Q-16) |
| BRIEF-RISK-05 | FEAT-24 | SCR-CL-04 | implemented_verified | `tests/test_risk.py::test_a_cautious_retiree_gets_a_cautious_profile` | |
| BRIEF-DASH-01 | FEAT-21 | SCR-CL-01 | implemented_verified | `tests/test_dashboard.py::test_the_family_view_is_the_household_sum` | |
| BRIEF-DASH-02 | FEAT-21 | SCR-CL-01 | implemented_verified | `tests/test_dashboard.py::test_every_client_s_dashboard_builds_in_both_views` | |
| BRIEF-DASH-03 | FEAT-21 | SCR-CL-01 | implemented_verified | `tests/test_dashboard.py::test_a_holding_carries_when_and_at_what_it_was_bought` | |
| BRIEF-DASH-04 | FEAT-21 | SCR-CL-01 | implemented_verified | `tests/test_dashboard.py::test_drawdown_compares_a_stress_with_the_limit`, `tests/test_dashboard.py::test_concentration_flags_one_area_over_its_share` | |
| BRIEF-DASH-05 | FEAT-21 | SCR-CL-01 | implemented_verified | `tests/test_dashboard.py::test_liquidity_counts_cash_deposits_and_liquid_funds_not_stocks` | |
| BRIEF-DASH-06 | FEAT-21 | SCR-CL-01 | implemented_verified | `tests/test_dashboard.py::test_recurring_items_are_found_monthly_and_by_school_term`, `tests/test_dashboard.py::test_the_calendar_places_maturities_coupons_instalments_and_flags_a_large_payment` | |
| BRIEF-DASH-07 | FEAT-21, 25 | SCR-CL-01 | implemented_verified | `tests/test_impact.py::test_every_client_gets_alerts_largest_first_and_the_latest_is_kept` | The card shows point-rule numbers (Q-03) |
| BRIEF-SCEN-01 | FEAT-26 | SCR-CL-03 | implemented_verified | `tests/test_scenarios.py::test_every_scenario_runs_for_every_client_in_both_views` | 9 life events |
| BRIEF-SCEN-02 | FEAT-26 | SCR-CL-03 | implemented_verified | `tests/test_scenarios.py::test_a_stress_test_measures_against_the_drawdown_limit` | 5 stress tests (not on the BRD engine) |
| BRIEF-SCEN-03 | FEAT-26, 27 | SCR-CL-03, 07 | implemented_verified | `tests/test_scenarios.py::test_an_option_waits_for_the_rm_and_is_decided_once` | Only an RM decides (DEF-02 fixed) |
| BRIEF-IMPACT-01 | FEAT-25 | SCR-CL-06 | implemented_verified | `tests/test_impact.py::test_impact_is_exposure_times_sensitivity_times_probability` | |
| BRIEF-IMPACT-02 | FEAT-25 | SCR-CL-06 | implemented_verified | `tests/test_impact.py::test_a_rate_rise_costs_a_floating_loan_and_bonds_by_duration` | |
| BRIEF-IMPACT-03 | FEAT-25 | SCR-CL-06 | implemented_verified | `tests/test_impact.py::test_impact_is_exposure_times_sensitivity_times_probability` | |
| BRIEF-IMPACT-04 | FEAT-25 | SCR-CL-06 | implemented_verified | `tests/test_impact.py::test_severity_follows_the_share_of_net_worth` | |
| BRIEF-IMPACT-05 | FEAT-25 | SCR-CL-06 | implemented_verified | `tests/test_impact.py::test_a_second_property_is_taxed_and_the_home_lived_in_is_spared` | 3 infrastructure projects; province mergers/zoning not modelled |
| BRIEF-ALERT-01 | FEAT-25 | SCR-CL-06 | implemented_verified | `tests/test_impact.py::test_the_transfer_tax_change_compares_both_ways_of_counting`, `tests/test_impact.py::test_every_client_gets_alerts_largest_first_and_the_latest_is_kept` | 14 policies |
| BRIEF-ALERT-02 | FEAT-25 | SCR-CL-06 | implemented_verified | `tests/test_impact.py::test_every_client_gets_alerts_largest_first_and_the_latest_is_kept` | Every alert carries its status and the “check before use” note |
| BRIEF-FLOW-01 | — | J6 | implemented_verified | `tests/test_demo.py::test_the_five_minute_demo` | HTTP path; DEMO.md names outdated (J6 mapping) |
| BRIEF-FLOW-02 | FEAT-27 | SCR-CL-07, SCR-RM-06 | implemented_verified | `tests/test_scenarios.py::test_an_option_waits_for_the_rm_and_is_decided_once` | RM: Khách hàng → Duyệt đề xuất; the client sees the queue read-only (DEF-02 fixed) |

## 4. Redesign kit (`KIT-*`)

| ID | Features | Status | Notes |
|---|---|---|---|
| KIT-UX-01 | FEAT-29 | implemented_verified | `tests/ui/test_pulse.py::test_the_figures_are_the_apis` — four Pulse cards (board look, R2) whose figures and small charts are the dashboard's, flows' and goals' fields; the class split sums to the month change |
| KIT-UX-02 | FEAT-29 | implemented_verified | `tests/test_flows.py::test_the_bands_are_the_transactions_of_the_month_to_the_dong`, `tests/test_flows.py::test_the_latest_month_by_default_and_the_family_adds_the_spouse` — transaction rows only; a band opens to its rows |
| KIT-UX-03 | FEAT-29 | implemented_verified | `tests/ui/test_pulse.py::test_the_figures_are_the_apis` — donut by class with values, shares, price date and drill-down to holdings (R2) |
| KIT-UX-04 | FEAT-30 | implemented_verified | `tests/test_graph.py::test_every_edge_comes_from_a_stored_record_and_the_columns_chain`, `tests/test_graph.py::test_the_client_sees_no_headline_and_no_holding` — columns, filters, path highlight, detail panel, list view (built 2026-10-16) |
| KIT-UX-05 | FEAT-31 | implemented_verified | `tests/test_feed.py::test_a_news_impact_shows_with_its_run_and_its_reason`, `tests/test_feed.py::test_thresholds_and_a_spending_jump_carry_their_numbers`, `tests/test_feed.py::test_the_client_reads_the_event_type_not_the_headline` — on SCR-CL-08 (built 2026-10-16) |
| KIT-UX-06 | FEAT-29…33 | implemented_unverified | Motion only for a state change (FEAT-33, 2026-10-16): request in flight, outcome, the evidence an answer read, a chosen graph path; transform/opacity only, all off under reduced motion (`tests/test_living_interface.py::test_hidden_tabs_pause_reduced_motion_stops_and_no_js_loop`); every chart has a table or list view (Sankey table, graph list); the static alternative is checked by screenshots only |
| KIT-UX-07 | all | implemented_unverified | No horizontal scroll at 390 and 1440 px on every route (`tests/ui/test_routes.py::test_every_route_renders_without_errors`); Sankey bands, map segments and graph nodes are focusable (Enter/Space); responsive at 390 px; progressive disclosure (band → rows, node → path); K6 sweep, no automated UI test |
| KIT-COPILOT-01 | FEAT-32 | implemented_verified | `tests/ui/test_routes.py::test_every_route_renders_without_errors` (the button on every route of every role, desktop and phone), `tests/ui/test_copilot_ui.py::test_an_answer_marks_what_it_read_and_the_states_follow` (panel opens with the page's context) — SCR-CL-10 |
| KIT-COPILOT-02 | FEAT-32 | partially_implemented | Ask (13 tools), Act (2 writes, confirmed), Navigate, Continue (tab session); Investigate (`dieu_tra`, `tests/test_copilot.py::test_investigate_reads_the_events_path_from_the_impact_graph`) and Analyze (`kich_ban`, `tests/test_copilot.py::test_a_stress_scenario_is_the_planning_pages_and_picked_by_words`) built on existing graphs (R5); under ADR-0012 the model reads no data; other writes not tools yet |
| KIT-COPILOT-03 | FEAT-32 | implemented_verified | `tests/test_copilot.py::test_no_write_without_confirm_and_the_result_is_the_real_one`, `tests/test_copilot.py::test_a_client_cannot_run_a_cio_tool_even_by_confirm` — typed catalogue, role check, confirm, server checks unchanged |
| KIT-COPILOT-04 | FEAT-32 | implemented_verified | `tests/test_copilot.py::test_the_router_prompt_carries_no_name_number_or_code`, `tests/test_copilot.py::test_the_live_router_receives_only_the_scrubbed_question` — the router gets no news, record or client data; reads are role-filtered |
| KIT-COPILOT-05 | FEAT-32 | implemented_verified | `tests/test_copilot.py::test_a_failing_tool_is_reported_as_failed_and_unknown_questions_get_help`, `tests/test_copilot.py::test_an_answer_outside_the_catalogue_falls_back_to_keywords_said_so` |
| KIT-COPILOT-06 | FEAT-32 | not_applicable | A test requirement; part of KIT-COPILOT-01…05's gates |
| KIT-DOC-01 | — | not_applicable | Met by this repository (requirements/ + this matrix) |
| KIT-DOC-02 | — | not_applicable | Met: brief_requirements.md, FEAT-20…28 |
| KIT-DOC-03 | — | not_applicable | Met: open_questions.md |
| KIT-DOC-04 | — | not_applicable | Met: status rules (README §4) |
| KIT-DOC-05 | — | not_applicable | Met: §0 above |
| KIT-DOC-06 | — | not_applicable | Applies to each future change (testing/acceptance_criteria.md) |

## 5. Owner requests (`OWN-*`)

| ID | Features | Status | Notes |
|---|---|---|---|
| OWN-MOTION-01 | FEAT-33 | implemented_unverified | A slow ripple from the panel's status dot while the panel is open and idle; nothing when closed (display:none), paused when the tab is hidden, none under reduced motion. Browser run and screenshots (2026-10-16); cost measured: +9 ms main thread per 5 s, no layout |
| OWN-MOTION-02 | FEAT-33 | implemented_verified | `tests/ui/test_copilot_ui.py::test_busy_lasts_exactly_as_long_as_the_request` — busy (✦ breathes, three dots, `aria-busy`) from the request sent until its answer, held answer included; no step-by-step progress because the server does not report steps |
| OWN-MOTION-03 | FEAT-33 | implemented_verified | `tests/test_living_interface.py::test_an_answer_names_the_elements_it_was_read_from`, `tests/test_living_interface.py::test_an_impact_answer_points_at_the_largest_event_and_the_feed_at_its_items`, `tests/test_living_interface.py::test_failures_mark_nothing`, `tests/test_living_interface.py::test_every_focus_key_has_a_page_that_renders_it` — the answer's `focus` keys come from the tool's result; KPIs, flow panel/rows/bands, feed items, events, families and the graph path are marked (browser run). Goals on Kế hoạch are not marked |
| OWN-MOTION-04 | FEAT-33 | implemented_verified | `tests/ui/test_copilot_ui.py::test_an_answer_marks_what_it_read_and_the_states_follow` — ok then idle after 1.6 s, refusal shown as error; ✓ 1.6 s, red dot and edge, amber while pending (pending checked by screenshots) |
| OWN-MOTION-05 | FEAT-33 | implemented_unverified | Nothing moves at rest with the panel closed (0 animations, 0 style/layout work in 5 s, measured); one accent colour; durations 160 ms / 240 ms / 2.6 s; screenshots |
| OWN-MOTION-06 | FEAT-33 | implemented_verified | `tests/test_living_interface.py::test_only_transform_and_opacity_animate`, `tests/test_living_interface.py::test_hidden_tabs_pause_reduced_motion_stops_and_no_js_loop` — no library added; measured before/after in FEAT-33 (no long task; one question 57 → 144 ms main thread over 3.5 s, 80 ms under reduced motion) |
| OWN-MOTION-07 | FEAT-33 | not_applicable | Met by this change: business logic unchanged (the answer gains `focus`, a feed item gains `key`), full suite green, docs updated (CHANGELOG 2026-10-16) |
| OWN-UI-01 | all | implemented_verified | R1 (2026-10-16): board tokens, header, icons, controls; R2: Toàn cảnh as on the board (`tests/ui/test_pulse.py::test_the_figures_are_the_apis`); R3: the eight pre-redesign pages rebuilt in the same look, one stylesheet (`tests/test_web.py::test_every_page_is_a_module_page`); desktop/phone, light/dark screenshots |
| OWN-UI-02 | FEAT-20…28 | implemented_verified | R3 (2026-10-16, ADR-0019): `tests/ui/test_pages.py::test_a_statement_and_a_declaration_reach_the_book`, `tests/ui/test_pages.py::test_the_risk_test_goes_back_and_sets_the_limit`, `tests/ui/test_pages.py::test_a_proposal_is_approved_by_the_rm_and_the_client_sees_it`, `tests/ui/test_pages.py::test_the_policy_filter_keeps_one_side`, `tests/ui/test_pages.py::test_a_row_of_all_clients_opens_that_client`, `tests/ui/test_routes.py::test_every_route_renders_without_errors` |
| OWN-UI-03 | FEAT-34 | implemented_verified | `tests/test_search.py::test_the_client_never_matches_a_headline_staff_do`, `tests/test_search.py::test_news_and_research_stay_with_staff`, `tests/ui/test_header.py::test_search_opens_a_holding_a_page_and_a_client`, `tests/ui/test_header.py::test_the_bell_counts_the_feed_and_opens_the_evidence` |
| OWN-UI-04 | FEAT-30 | implemented_verified | R4 (2026-10-16): `tests/test_overview.py::test_every_edge_comes_from_a_record_it_names`, `tests/test_graph.py::test_an_events_share_of_each_asset_adds_up_to_its_expected_change`, `tests/test_graph.py::test_the_cio_run_graph_reaches_every_family_from_the_stored_results`, `tests/test_graph.py::test_the_timeline_reads_each_step_from_its_record`, `tests/ui/test_pages.py::test_the_overview_graph_selects_expands_and_opens_pages`, `tests/ui/test_pages.py::test_the_timeline_the_news_impact_card_and_the_cio_run_graph` — overview with sources, risks, goals, policy and news, expand/collapse, node → page; News Impact panel; timeline; CIO whole-run graph |
| OWN-UI-05 | FEAT-32 | implemented_verified | R5 (2026-10-16): `tests/test_copilot.py::test_an_answer_says_when_its_data_is_from_what_it_read_and_carries_its_card`, `tests/test_copilot.py::test_investigate_reads_the_events_path_from_the_impact_graph`, `tests/test_copilot.py::test_a_stress_scenario_is_the_planning_pages_and_picked_by_words`, `tests/test_copilot.py::test_every_call_is_in_the_audit_chain_with_the_question_as_the_router_saw_it`, `tests/ui/test_copilot_ui.py::test_answers_show_their_card_their_time_and_sources_and_offer_next_steps` — as-of and sources, cards, two tools, audited calls; the live router is R6 |
| OWN-UI-06 | FEAT-04, FEAT-32 | implemented_unverified | R6 (2026-10-16): the live demo runs the two models (`GET /api/agents` mode `live`) and the Copilot router (`router.kind` `llm`); `scripts/demo_walkthrough.py` made three live views from fetched news, two approved and applied (FEAT-04 “Live demo”); checked on the public URL by screenshots — a run against live models is not a suite test |
| OWN-UI-07 | — | implemented_verified | `tests/ui/test_routes.py::test_every_route_renders_without_errors` (R0) |
