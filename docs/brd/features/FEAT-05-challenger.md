# FEAT-05 — The independent challenger

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-BR-06, BRD-FR-303, BRD-RULE-AI-01, BRD-RULE-AI-10, BRD-RULE-WF-04 |
| Users | Runs automatically after the CIO agent and after every CIO edit; CIO answers findings |
| Entry points | Findings panel of [SCR-CIO-03](../ux/screens/cio.md#scr-cio-03--nhận-định-view-detail); `POST /api/views/decide {action: "challenge"}` to re-run after a failure |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
Check a view before the CIO can approve it, with a different model (or rules), so that drafting and checking
do not share the same mistakes. Findings are Critical, Medium or Low; every Critical one must be answered.

## Behaviour
1. After `save_view`, `review` runs the challenger on the view as it stands: in live mode the `llm:challenger`
   model (capped at 8 findings), in mock mode the rule checks R1–R7 of `src/views/challenger.py`.
2. The challenge is stored with the view's **content hash** and `independent = (challenger model ≠ CIO model)`.
3. The view moves to `PENDING_APPROVAL`.
4. A CIO **edit** changes the content hash and sends the view back to `PENDING_CHALLENGE`; the challenger runs
   again on the new content (F12).
5. If the challenger fails, the draft is kept and the CIO can run it again (`challenge` action).

## Rules
Approval conditions that depend on it (FEAT-06): *b* a challenge exists on the current content hash; *c* every
Critical finding of that challenge is answered; *f* the challenge is independent.

## Implementation
`src/views/ops.py::review` (`_challenge_or_note`), `src/views/agents.py::challenge`, `src/views/challenger.py`,
`src/views/store.py` (`challenges`).

## Acceptance and tests
`tests/test_views.py::test_an_edit_goes_back_to_the_challenger_and_a_critical_finding_blocks_approval_until_answered`,
`::test_a_failed_challenger_keeps_the_draft_and_can_run_again`. Live run 2026-10-15: 13 s, 8 findings of which 3
critical.

## Limitations
- In mock mode the “independent” challenger is a rule set (Q-05).
- The post-check summary that FR-501 assigns to the challenger is a template instead (Q-12).
