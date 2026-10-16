# FEAT-36 — Alerts and the central log

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-NFR-12 (central logs; alerts on feed, agent and chain failures), BRD-NFR-03 (an AI failure does not stop computing or viewing) |
| Users | CIO, Compliance, Admin (each the kinds they look after) |
| Entry points | the bell ([FEAT-34](FEAT-34-header-search-and-notifications.md)); [SCR-ADM-01](../ux/screens/admin.md) “Cảnh báo” and “Nhật ký hệ thống”; `GET /api/system/alerts`, `POST /api/system/alerts/ack` |
| Screenshots | [the CIO's bell](../assets/current_ui/FEAT-36-bell-cio_desktop-light.jpg) · [the Admin's bell, phone](../assets/current_ui/FEAT-36-bell-admin_phone-light.jpg) |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
A failure reaches someone without their having to look for it, and the record of what failed is in one place.

## Alerts (`src/control/alerts.py`, table `alerts`)
| Kind | Raised when | Resolved when | For |
|---|---|---|---|
| `news_feed` | a white-listed feed's fetch fails (`news.ops.keep`) | the feed answers again | CIO, Admin |
| `market_job` | every source of a market series fails, and it is not just a quiet weekend (`market.fetch.run_job`) | the series gets points again | CIO, Admin |
| `agent` | an agent run ends in error (`views.store.finish_run`), a queued run fails or is left running by a dead worker (`views.queue`) | the agent's next run is ok | CIO, Admin |
| `audit_chain` | the hourly `audit_check` job finds the chain broken | the chain verifies again | Compliance, Admin |
| `inbox` | a package from the AI zone is rejected (`inbox.importer`) | — (each rejection is its own) | CIO, Admin |
| `zone_sync` | the catalogues could not be sent to the AI zone | the next sync is ok | Admin |

One alert per thing (`kind` + `key`, e.g. `news_feed` + `vietstock_vm`): failing again counts up on the open one
(`count`, `last_at`); working again resolves it. Status: open → acked (“Đã xem”, by a role it is for, with a note;
it stays listed until resolved) → resolved. Raising, acknowledging and resolving are audit rows (`alert.raise`,
`alert.ack`, `alert.resolve`). The bell of CIO, Compliance and Admin lists their open alerts first, each with
“Đã xem” and a link to where its cause is seen; Hệ thống lists the last 30 of every kind.

## The central log (`src/control/log.py`)
One JSON object a line — `at`, `level` (info, warning, error), `process` (bank or zone), `event` and its fields —
beside the state file (`mr-finance-log.jsonl`, or `MF_LOG`), 5 MB then rotated once. Written: every alert step,
the chain check, and every 5xx the server answers on a read. Never a customer's record: ids and error texts only.
Hệ thống shows the last 30 warnings and errors.

## An AI outage (NFR-03)
A provider that cannot be reached is an `AgentError` for the run (`views.agents.call_model`): the view goes to
`AGENT_ERROR` with why, no run is left running, an `agent` alert is raised. The engine, application runs and every
read take no model and keep working. Availability itself (99.5 %) is a deployment matter.

## Acceptance and tests
`tests/test_alerts.py::test_a_feed_that_fails_raises_one_alert_counts_up_and_resolves_when_it_answers`,
`::test_a_market_series_no_source_answers_raises_an_alert`,
`::test_a_broken_audit_chain_alerts_compliance_and_admin_and_resolves_when_whole`,
`::test_acknowledging_is_for_the_roles_it_is_for_and_is_audited`,
`::test_with_the_ai_provider_down_computing_runs_and_reads_still_work` (a real refused connection: live mode with
the provider's address where nothing listens); `tests/test_access.py` (the two routes).
Recorded 2026-10-16 on the dev server: an unsigned package posted to the inbox was rejected by `inbox_import` and
raised `AL-000001` for CIO and Admin; the CIO's “Đã xem” in the bell acknowledged it (audited as `cio`).
