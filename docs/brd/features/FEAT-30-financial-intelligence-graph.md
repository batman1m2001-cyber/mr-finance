# FEAT-30 — Financial Intelligence Graph

| | |
|---|---|
| Type | Proposed extension (redesign kit), approved for planning 2026-10-15 — **not built** |
| Requirements | KIT-UX-04, KIT-UX-06; must respect BRD-RULE-CONTENT-01 (flow 2) |
| Users | Client (asset-class level), RM, CIO |
| Plan | [docs/REDESIGN_KIT_PLAN.md](../../REDESIGN_KIT_PLAN.md) phase **K3**, decision D5 |
| Status | see [traceability](../requirements/requirements_traceability.md) §4 |

## Intended behaviour
`GET /api/graph?family_id` (and `?run_id` for the CIO): nodes news → event → view branch → factor → asset
class/holding → family → goal, built from stored records (FEAT-02, 04, 08, 10); every edge carries the id of
the record it came from; wording “có thể ảnh hưởng”, never causal. Client role: event type instead of headline,
asset class instead of ticker. Laid out in columns, not a force-directed hairball; filters by node type; select a
node to highlight its path and open a detail panel; keyboard navigation; a list view as the static alternative.
No graph database.

## Acceptance (plan gate)
Every edge resolves to a stored record (test); no ticker or headline for the client (test); no console error,
no horizontal scroll.
