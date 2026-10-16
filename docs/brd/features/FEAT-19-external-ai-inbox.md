# FEAT-19 — External AI zone and signed inbox

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-FR-307 (inbox mode), BRD-RULE-AI-13, BRD-RULE-ZONE-01…03, BRD-RULE-ZONE-06, BRD-RULE-LC-04, BRD-RULE-SEC-07 |
| Users | Admin (mode, operations), CIO (decides the imported views) |
| Entry points | `POST /api/inbox` (the zone's one way in); [SCR-ADM-01](../ux/screens/admin.md) “Vùng AI và hộp chờ”; configuration `ai_mode` (Cấu hình); the zone: `operonx serve -f operonx.zone.toml` |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
In inbox mode the AI runs outside the bank, in a process that holds no customer and no member of staff, and its
results come in only as signed packages, checked like a live run's before the CIO sees them
([ADR-0022](../decisions/ADR-0022-the-ai-zone-is-a-second-process.md)).

## The two processes
| | The bank (`app/main.py`, `MF_STATE` = state.db) | The AI zone (`app/zone.py`, its own `MF_STATE` and `MF_DATA`, `MF_ZONE=on`) |
|---|---|---|
| Holds | everything | its own fetched news, the released research and the approved catalogues — the data folder has only `market.json`, `factors.json`, `factor_model.json`, `news_config.json` (`scripts/make_zone_data.py`) |
| Jobs | `zone_sync` (10 min, inbox mode): catalogues and research out, signed `MF_ZONE_KEY`, when changed · `inbox_import` (10 min) | `zone_news` (10 min): `ingest_flow` on the bank's approved feeds · `zone_agent` (15 min): one event under the day's cap |
| Doors | `POST /api/inbox` → `202 {"id"}` | `POST /api/zone/sync` (the bank's push) · `GET /api/zone/status` |

## The zone's agent (`src/zone/agent.py`)
Each tick: packages TCB has not taken are sent again (for a day, then `failed`); then, under `MF_ZONE_DAILY`
events a day (6), the most-covered event type among the last two days' news (not held, relevance medium or high, at
most 8 items) becomes an event; `cio_agent_flow` runs on it as `agent:zone` with the bank's approved prompts and
models (mock when none are set); the view becomes a package, signed `MF_INBOX_KEY`, posted to `MF_TCB_INBOX`. The
outbox (`zone_outbox`) keeps each package and what happened to it.

## The package (version 1)
`{version, zone_run, created, event {title, type}, news [{ref, url, title, source}], view, challenge {findings},
run {mode live|mock, models {cio, challenger}, prompt_version, nodes}}` — the view's `source_ids` use the package's
`ref`s (Z1…); research is `source: "research"`, `url: "research://RS-…"`. Over 460 KB the trace drops its prompts
and inputs.

## The door and the import (`app/web.py::inbox_receive`, `src/inbox/`)
The door is open only in inbox mode (409), takes at most 512 KB (413) and 200 waiting packages (429), keeps the
bytes with whether the signature is valid, and answers the id. `inbox_import`, oldest first, READY → PROCESSING →
IMPORTED | REJECTED (with the error), in order:
1. signed, when `MF_INBOX_KEY` is set (LC-04);
2. the form: version 1, an event title, 1–8 news, view, challenge, run mode and two model names;
3. each news item: a white-listed, approved source (or research the bank released); the item the bank fetched
   itself at that address and source — never the package's text (FR-104); not held for the restricted list
   (FR-105); not dismissed. A news item the bank has not fetched yet keeps the package READY for an hour;
4. the view's references mapped to the bank's ids, then the format check of a live run (§8.2, AI-05, sources
   belong to the event);
5. each finding has a severity and a title; the zone's rule findings are dropped (the rules run again here).

Then the event (`agent:zone`), the view in mode `inbox`, the zone's trace (each node with `zone_mode`), the
challenge (the bank's rules plus the zone's model findings, source `zone`), and `PENDING_APPROVAL`. Audited:
`inbox.receive`, `inbox.imported`, `inbox.rejected`, `zone.sync`; in the zone `config.mirror`.

## Acceptance and tests
`tests/test_inbox.py` (import, each check's rejection, signatures, news not fetched yet, restricted news, the
door's 409/413/429), `tests/test_zone.py::test_the_round_trip_tcb_to_the_zone_and_back_through_the_inbox` (both
processes' code over their own files: sync, the zone's ingest and agent, the push reading back only an id, no
people table in the zone, the import), `::test_the_zone_takes_one_event_a_tick_under_the_days_cap`,
`::test_a_package_tcb_does_not_take_is_sent_again_and_dropped_after_a_day`,
`::test_the_zones_door_takes_only_a_signed_bundle_of_the_catalogues`,
`::test_only_the_zone_mirrors_a_catalogue_and_only_the_zone_has_its_actor`.
Recorded 2026-10-16, two processes on one host (:8031 bank, :8041 zone, real feeds, zone in mock): `zone_sync` put
the bank's `CF-factor_model-v2` in force in the zone; the zone fetched the feeds, grouped 8 equity news into an
event and pushed `IN-000001`; the bank imported it as `VW-0004-v1`, waiting for the CIO.

## Limits
One host in the demo; the live demo stays in `live` mode (inbox mode needs the zone process and both keys). The
zone is never told what became of a package.
