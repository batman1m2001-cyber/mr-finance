# FEAT-13 — Delivering the impact: RM list, family impact by role

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-BR-09, BRD-BR-14, BRD-FR-502, BRD-FR-503, BRD-RULE-ROLE-02, BRD-RULE-ROLE-06, BRD-RULE-CONTENT-01, BRD-RULE-CONTENT-02, BRD-RULE-WF-07, BRD-RULE-LC-02 |
| Users | RM, client (demo), CIO |
| Entry points | [SCR-RM-01 Hôm nay](../ux/screens/rm.md#scr-rm-01--hôm-nay-today), [SCR-RM-02](../ux/screens/rm.md#scr-rm-02--tác-động-tin-family-impact-staff), [SCR-CL-05](../ux/screens/client.md#scr-cl-05--tác-động-thị-trường-family-impact-client); `GET /api/rm/today`, `GET /api/families/{id}/impact?role=` |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
Put the results in front of the right people, in the right form: the RM sees which families to call first;
each family's impact is shown to staff in full and to the client at asset-class level, labelled as AI-assisted
and not a recommendation.

## Behaviour
- **RM “Hôm nay”**: the server (`rm_today`) returns, from EFFECTIVE runs only, one case per (run, family)
  flagged `pre_review`, sorted by 3-month P10 as a share of net worth, worst first; plus `goal_tasks` from the
  goal branch (FEAT-10) at levels contact_now, confirm_goal and remind (not `note`). The page groups the cases
  into one row per family (an RM calls a family once, whatever the number of events), ordered by its worst P10.
- **Family impact** (`family_impact(family_id, role)`): the runs the role may see (CIO/Compliance/Admin: all;
  RM: EFFECTIVE, SUPERSEDED, WITHDRAWN with their labels; client: EFFECTIVE only), each with the 3-month
  expected change, its band, contributions by asset class, and the approval.
- **Client form** (flow 2): asset classes only (no holding, no ticker), the event's **type** label instead of its
  headline, the approver's name and title, the price date, “tham số mô hình là giả định”, and the note
  `CLIENT_NOTE` (“Nội dung có sự hỗ trợ của AI, do CIO duyệt kịch bản; … không phải khuyến nghị đầu tư. Liên
  hệ chuyên viên quan hệ khách hàng …”).

## Implementation
`src/apply/reads.py` (`VISIBLE`, `family_impact`, `rm_today`, `CLIENT_NOTE`); `app/web.py` (`family_impact`,
`rm_today`); `web/pages/today.js`, `web/pages/impact.js`.

## Acceptance and tests
`tests/test_apply.py::test_the_client_reads_asset_classes_only_with_the_labels`,
`::test_the_rm_today_list_holds_the_flagged_families_worst_first`,
`::test_a_held_run_is_hidden_from_rms_until_the_cio_makes_it_effective`,
`::test_withdrawing_the_view_withdraws_its_runs_and_rms_see_the_label`.

## Limitations
- Nothing is sent to a client (BRD-RULE-SCOPE-05); the client view is an in-app page.
- Client content does not name each news source (BRD-RULE-CONTENT-02 asks for “nguồn cho từng tin”): showing
  outlets could reveal the headline; open with Compliance (Q-14 family).
- The internal-explanation stamp “Nội bộ” (BRD-RULE-SEC-03) exists only on the pre-BRD advisory page banner.
