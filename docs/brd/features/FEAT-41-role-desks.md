# FEAT-41 — Role desks (every staff role's own workspace)

| | |
|---|---|
| Type | Extension (owner request, 2026-10-18), **experiment**: branch `exp/graph-workspace` |
| Requirements | OWN-MR-01…12; keeps every requirement the staff screens carry today (the map in [ux/role_desks.md](../ux/role_desks.md)) |
| Users | CIO, RM, Admin, Expert (`specialist`), Compliance. The Customer keeps FEAT-40 |
| Entry points | `#/<role>` and `#/<role>/ban` (the desk); every older staff address opens its page as a sheet over the desk; `GET /api/desk` |
| Plan | [docs/MULTI_ROLE_UX_PLAN.md](../../MULTI_ROLE_UX_PLAN.md) M0–M6; decision [ADR-0036](../decisions/ADR-0036-every-staff-role-works-at-its-own-desk.md) |
| Status | see [traceability](../requirements/requirements_traceability.md) §5 |

## Purpose

Each staff role starts its day on one screen built for its job — what waits for it, where the work stands, what to
do next — instead of a row of tabs; every page it had stays, one click away, unchanged; and its own assistant sits
beside it, reading the same numbers the screen shows.

## Preconditions and permissions

Signed in as a staff role. The desk reads only `GET /api/desk`, which takes the role from the session (sign-in on;
`?role=` only when sign-in is off) and returns that role's desk alone; a client gets 403. The desk is built from the
stores the existing reads use, with their filters (`people.auth.may_see` for families). Nothing on a desk writes
except through an existing, already-checked write.

## Behaviour

1. **The frame** (shared with the Customer's workspace, FEAT-40): the rail on the left (the role's groups of pages,
   with tooltips), the centre, the dock on the right (Trợ lý · Thông tin, divider and fold as FEAT-40), sheets over
   the centre. A phone stacks them: rail on top, centre, dock.
2. **Addresses:** `#/<role>` and `#/<role>/ban` show the desk; every menu address of `web/shell.js` is unchanged and
   opens its page module, unchanged, as a sheet; the sheet's header shows the group's pages as tabs and closes back
   to the desk (✕, ← or Escape).
3. **The centre** is the role's own (§ Desks below). A pick fills Thông tin with the item and its links.
4. **The assistant** docks in Trợ lý, streams, shows the progress list, and lights on the centre what each step reads.

## Desks

Filled in as each phase is built (plan §3): CIO (M1), RM (M2), Admin (M3), Expert (M4), Compliance (M5).

## API and data

`GET /api/desk` → `{role, as_of, …the role's sections}`; see [api_reference.md](../architecture/api_reference.md).

## Implementation

`src/desk/reads.py` (the composed reads), `app/web.py` (`/api/desk`), `web/desk/` (the frame and one module per
role), `web/workspace/dock.js` (divider and fold, shared with FEAT-40).

## Acceptance and tests

Listed per phase in the plan §4 and in the traceability rows OWN-MR-01…12.

## Limitations

See [Q-24](../requirements/open_questions.md#q-24--which-roles-the-multi-role-request-covers),
[Q-25](../requirements/open_questions.md#q-25--admins-user-and-role-management),
[Q-26](../requirements/open_questions.md#q-26--how-much-of-a-family-a-specialist-sees).
