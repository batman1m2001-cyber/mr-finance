# FEAT-31 — Intelligence Feed

| | |
|---|---|
| Type | Extension (redesign kit), built 2026-10-16 (plan phase K4) |
| Requirements | KIT-UX-05; respects BRD-RULE-CONTENT-01 (flow 2) |
| Users | Client, RM |
| Entry points | “Điều đáng chú ý” on [SCR-CL-08](../ux/screens/client.md#scr-cl-08--toàn-cảnh-pulse-wealth-map-money-flow) (client and RM); `POST /api/feed {client_id, scope, role}` |
| Plan | [docs/REDESIGN_KIT_PLAN.md](../../REDESIGN_KIT_PLAN.md) phase **K4** |
| Status | see [traceability](../requirements/requirements_traceability.md) §4 |

## Behaviour
`feed_flow` (`src/feed/`) returns items, most important first; each has a type, a severity (Cần xem / Đáng chú ý /
Thông tin), a title, **why** it is shown, its **evidence** (a stored record or a returned number) and the page
that shows it:

| Type | Shown when (our thresholds) | Evidence | Page |
|---|---|---|---|
| impact | an EFFECTIVE run moves the family ≥ 0.5 % of net worth in 3 months, or flags RM pre-review (BR-09) | run id | Tác động |
| goal | FR-404 level changed by a run; a released regulation note matches a goal (FEAT-10; the client only when it has a client message) | run + goal, or note + goal | Tác động |
| risk | stress-loss estimate near / over the accepted limit; liquidity under 6 months | dashboard part | Chi tiết |
| change | a spending category up ≥ 30 % and ≥ 5 triệu month on month; net worth moved ≥ 3 % | category + month; dashboard | Dòng tiền (same page, month set) |

The client reads event types, never headlines (reuses `apply.reads.family_impact` per role). The rules are
printed under the list. Empty: “Không có điều gì cần chú ý lúc này.”

## Implementation
`src/feed/{ops,graph}.py` (pure `ops.build`), service `feed` in `app/main.py`; panel in `web/pages/pulse.js`.

## Acceptance and tests
`tests/test_feed.py`: impact items name an EFFECTIVE run and carry its exact value; the client sees no headline;
risk and spending items carry their numbers and links; regulation items, and the client filter; empty list;
endpoint. UI: desktop, phone, dark, link opens the evidence page (2026-10-16).

## Limitations
The thresholds are ours (not in the BRD or kit). The old overview's “Headline News” card (point rules, Q-03)
is still on “Chi tiết”; the feed does not replace it there.
