# FEAT-03 — Exclusive research and regulation notes

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-BR-01, BRD-BR-03, BRD-FR-201, BRD-FR-202, BRD-FR-203, BRD-FR-204, BRD-FR-604, BRD-RULE-LC-03, BRD-RULE-SEC-04 (releaser ≠ uploader), BRD-RULE-SEC-06, BRD-RULE-CONTENT-03 |
| Users | CIO / research side uploads; Compliance releases or rejects |
| Entry points | [SCR-CIO-06](../ux/screens/cio.md#scr-cio-06--nghiên-cứu-research-cio), [SCR-CMP-02](../ux/screens/compliance.md#scr-cmp-02--nghiên-cứu-research-release) |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
Bring TCB's own analysis into the process only after it is officially released, by someone other than its
author, and route regulation notes to the goal branch (FEAT-10) instead of the price engine.

## Preconditions and permissions
Upload: role `cio`. Release/reject: role `compliance`, a different user from the uploader.

## Inputs → outputs
- **Upload** `POST /api/research {item, by}`: `kind` (`research`, `house_view`, `regulation`), `report_no`,
  `title`, `summary`, `release_at`, `conflict`; for `regulation` also `regulation{document, status
  (draft|issued), effective_date, purposes[], countries[], prep_weeks, documents[], client_message, rm_hint}`.
- **Decide** `POST /api/research/release {item_id, decision: release|reject, by, note}`.
- **Out:** `research_items` row `RS-nnnn`, status `PENDING_RELEASE` → `RELEASED` | `REJECTED`.

## Behaviour and rules
1. Upload checks the fields; a regulation note whose client message or RM hint contains a forbidden term (PEP,
   risk rating, suspicious transaction, enhanced monitoring, transaction reporting, money laundering, watch list)
   is **refused** (FR-604, `procedural.goals.forbidden_words`).
2. Release requires: a note of ≥ 20 characters; releaser ≠ uploader; the release time has passed; no
   restricted-list name in the title or summary.
3. A released research report or house view enters the news inbox labelled **“Độc quyền”** with its release
   time as published time. A released **regulation note never enters the inbox**: it feeds the goal branch.
4. Every step is audited.

## Implementation
`src/research/store.py` (`upload`, `decide`, `_to_inbox`), `src/research/ops.py`, `src/research/graph.py`
(`research_upload_flow`, `research_release_flow`); read `GET /api/research` in `app/web.py`.

## Acceptance and tests
`tests/test_research.py::test_a_report_waits_for_another_cio_and_then_reaches_the_inbox`,
`::test_the_uploader_cannot_release_and_nothing_goes_out_before_its_time`,
`::test_a_report_naming_the_restricted_list_is_not_released`, `::test_a_regulation_note_with_aml_wording_is_refused`,
`::test_the_brd_example_draft_aml_rule_and_a_study_abroad_goal` (a released note stays out of the inbox).

## Limitations
- Conflicts of interest are a free-text field; there is no list of TCB/TCBS-related organisations to check
  against (BRD-RULE-CONTENT-03).
- No connection to a research repository (BRD §11.1, pilot).

## Conflict of interest (BRD completion F8; CONTENT-02, CONTENT-03)
`conflict` is a structured field: `{related, parties, statement}` (`src/research/conflict.py`). Compliance keeps
the list of related parties (configuration `related_parties`, one person: Techcombank, TCB, TCBS, Techcom
Securities, Techcom Capital, Techcom Life by default). A report whose title or summary names one of them is refused
unless it is declared (`related: true`, the parties, a statement of at least 20 characters). The disclosure travels
with the item into the inbox and every event that uses it, and the client reads it on Tác động thị trường
([FEAT-13](FEAT-13-impact-delivery-by-role.md)) and in the newsletter ([FEAT-17](FEAT-17-cio-newsletter.md)).
Items kept before F8 with a free-text `conflicts` are read as that statement.
