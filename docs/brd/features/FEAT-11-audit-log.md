# FEAT-11 — The audit log

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-BR-12, BRD-FR-702, BRD-NFR-09, BRD-RULE-DATA-05, BRD-RULE-DATA-06, BRD-RULE-SEC-08, BRD-RULE-SEC-09 |
| Users | Compliance reads and verifies; every news-impact write appends |
| Entry points | [SCR-CMP-03 Nhật ký](../ux/screens/compliance.md#scr-cmp-03--nhật-ký-audit-log); `GET /api/audit?limit=`, `GET /api/audit/verify` |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
A record of every action that cannot be edited quietly: each row chains to the one before, the database refuses
edits, and a check names the first broken row.

## Behaviour
- `append(con, actor, action, object, data)` is called **inside the transaction of the write it records**, so
  the change and its row commit together or not at all.
- Row: `seq, ts, actor, action, object, alg, prev_hash, hash, data`. `hash` covers `prev_hash` and the row.
- Triggers refuse UPDATE and DELETE on `audit_log`.
- Plain SHA-256 by default; with `AUDIT_HMAC_KEY` set, HMAC-SHA-256, and a chain that has HMAC rows refuses to
  go back to plain SHA-256.
- `verify()` walks the chain and reports the first row whose hash does not match.

## Coverage
Writes of `src/news`, `src/events`, `src/views`, `src/apply`, `src/research` (news, holds, events, views,
decisions, agent runs, runs and their statuses, research, goal declarations). **Not** the pre-BRD state in
`src/wealth/store.py` (statements, declarations, risk results, alerts, the RM queue).

## Implementation
`src/control/audit.py`, `src/control/db.py` (`tx()`); reads in `app/web.py` (`audit_list`, `audit_verify`);
`web/pages/audit.js`.

## Acceptance and tests
`tests/test_apply.py::test_every_step_is_in_the_audit_chain_and_it_verifies`,
`::test_the_database_refuses_to_edit_the_log_and_a_forced_edit_is_found`, `::test_hmac_chain_and_no_downgrade`.

## Limitations
- No export (FR-702 “xuất”): the read returns up to 1,000 rows as JSON.
- No periodic anchoring of the chain head to WORM storage (bank deployment).
- `POST /api/reset` (demo reset) drops the log with the rest of the demo state.
- No alert when the chain breaks (NFR-12).
