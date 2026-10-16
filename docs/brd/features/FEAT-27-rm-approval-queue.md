# FEAT-27 — The RM approval queue

| | |
|---|---|
| Type | Existing capability (original brief, docs/PLAN.md); outside the BRD — kept by [ADR-0003](../decisions/ADR-0003-keep-the-capabilities-that-predate-the-brd.md) |
| Requirements | BRIEF-SCEN-03, BRIEF-FLOW-02; related BRD-RULE-CONTENT-01 flow 3 |
| Users | Client proposes (from a scenario option); RM / specialist decides |
| Entry points | Option buttons on [SCR-CL-03](../ux/screens/client.md#scr-cl-03--kế-hoạch-wealth-planning-advisor); queue read-only on [SCR-CL-07](../ux/screens/client.md#scr-cl-07--chuyên-gia-specialist-team), decided on [SCR-RM-06](../ux/screens/rm.md#scr-rm-06--duyệt-đề-xuất-approval-queue); `POST /api/review/propose`, `POST /api/review/decide`, `GET /api/review` |
| Status | see [traceability](../requirements/requirements_traceability.md) §3 |

## Behaviour
`propose_flow` puts a scenario option in the queue (`pending`); `review_flow` records an RM's decision once (role `rm`, sent as `by`)
(`approved` / `rejected`, with a note); a second decision is refused. The client sees “chờ RM duyệt” until then.

**The certified specialist (G8, BRD-RULE-ROLE-05, WF-08).** When the family has a specialist on its team holding a
certificate in force (configuration `certifications`, Compliance), the RM's approval moves the item to
`pending_specialist`; that specialist approves or rejects it (with a reason) on Chuyên gia · Duyệt khuyến nghị
(`POST /api/review/specialist`, `src/review/specialist.py`). A family with none: the RM's approval stands. The RM can
also write a recommendation for the family (`POST /api/review/recommend`, kind `rm_note`), which goes through the
same gate and reaches the client only once approved.

## Implementation
`src/review/{graph,ops,specialist}.py`, `web/pages/specialist.js`; `src/wealth/store.py` (`reviews`); reads `app/web.py::reviews`.

## Acceptance and tests
`tests/test_scenarios.py::test_an_option_waits_for_the_rm_and_is_decided_once`, `::test_review_flow_refuses_an_unknown_item`.
`tests/test_specialist.py` (7): the specialist step, a family without one, a lapsed certificate, the configuration, the
RM's own recommendation, sign-in and what a specialist sees.

## Limitations
Since G7 (2026-10-16) the item keeps who decided (`decided_by`) and the decision is in the audit chain
(`review.decide`, counted by BRD-KPI-05); decisions made before name no one.
