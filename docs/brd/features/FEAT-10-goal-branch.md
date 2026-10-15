# FEAT-10 — The goal branch (regulation → goals abroad)

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-BR-10, BRD-FR-204, BRD-FR-601, BRD-FR-602, BRD-FR-603, BRD-FR-604, BRD-RULE-GOAL-01…08 |
| Users | RM (declares outflows, gets tasks); client (sees remind/contact messages for declared goals); CIO and Compliance (see matches on the research page) |
| Entry points | [SCR-RM-01 Hôm nay](../ux/screens/rm.md#scr-rm-01--hôm-nay-today) “Việc theo mục tiêu”; goal panel of [SCR-CL-05](../ux/screens/client.md#scr-cl-05--tác-động-thị-trường-family-impact-client) / [SCR-RM-02](../ux/screens/rm.md#scr-rm-02--tác-động-tin-family-impact-staff); [SCR-CIO-06](../ux/screens/cio.md#scr-cio-06--nghiên-cứu-research-cio); `GET /api/goals/regulation`, `POST /api/goals/outflow` |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
A regulation that moves no price can still delay a goal that sends money abroad (study, emigration, investment,
property, support). The branch turns released regulation notes into a **date, documents and an urgency** —
never money — for the right families, without AML data.

## Inputs → outputs
- **In:** released regulation notes (FEAT-03); each family's active goals = its dated outflows not yet past
  (fixtures `events`); RM declarations (`goal_outflows`). Nothing else.
- **Out:** matches `{family, goal_id GL-<family>-nn, goal, need_date, purpose, country, declared, note, milestone,
  level, documents, client_message|null, rm_hint}`, sorted contact_now → confirm_goal → remind → note.

## Rules (`src/procedural/goals.py`)
- **Purpose and country:** declared by the RM (`POST /api/goals/outflow`, role `rm`) or inferred from the
  goal's name. Inference needs a purpose word **and** a country in context (“du học Úc”, “(Mỹ)”, “sang
  Canada”), so “Mỹ Linh”, “Nhật Minh”, “Minh Đức” do not match.
- **Inferred only → level `confirm_goal`**: an RM task, no client message.
- **Milestone** = first day of the month needed − (prep weeks + 4).
- **Level** (declared goals): money leaves before the effective date → `note`; issued and milestone ≤ 92 days
  away → `contact_now`; need within 104 weeks or the text a draft → `remind`; else `note`.
- **Client message** only for declared goals at `remind` or `contact_now`; one generic text per note.
- Notes with AML wording are refused at upload (FR-604). Country limits on a note restrict the match.

## Implementation
`src/procedural/goals.py` (`infer`, `milestone`, `level`, `goals_of`, `match`), `src/research/store.py`
(`declare`, `declared`, `released_notes`), `src/research/ops.py::declare_outflow`, `src/research/graph.py::goal_outflow_flow`,
reads `app/web.py::goal_regulation` (`?role=client` keeps declared remind/contact items only) and
`src/apply/reads.py::rm_today` (`goal_tasks`).

## Acceptance and tests
`tests/test_research.py::test_the_brd_example_draft_aml_rule_and_a_study_abroad_goal` (milestone 2026-12-07,
`confirm_goal` → after declaring, `remind` with a client message), `::test_inference_from_a_goals_name` (7 cases),
`::test_an_issued_rule_close_to_the_milestone_means_contact_now_and_late_rules_are_a_note`,
`::test_country_limits_and_past_goals`, `::test_the_reads_and_the_rm_list`.

## Limitations
- Goals are the fixtures' dated outflows; goals planning (FEAT-26) has its own goal list, not yet unified.
- Not shown on the client's “Kế hoạch” goal cards (Q-20).
- No “closed” goal flag is set by any screen (supported in the data: `closed`).
