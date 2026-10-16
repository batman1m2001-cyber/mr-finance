# ADR-0022 — The AI zone is a second process with its own database, reaching the bank through a signed inbox

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** BRD §5 and §7.1 (BRD-RULE-ZONE-01…06, LC-04, SEC-07, FR-307, AI-13); docs/BRD_COMPLETION_PLAN.md
  F-D7, F6
- **Supersedes in part:** [ADR-0009](ADR-0009-ai-barrier-by-graph-inputs-in-one-process.md) (its “one process” and
  “inbox planned”; the graph-input barrier stays)

## Context

ADR-0009 kept the AI in the bank's process and made the barrier a tested property of the agent graphs' inputs. The
BRD asks for more: the AI runs in a zone of its own, holding only public news, released research and approved
catalogues, and writes its results into a write-only inbox the bank imports through the same checks.

## Decision

- **Three modes, chosen by Admin** (configuration `ai_mode`, FR-307): `live` (the agent runs in the bank's
  process, queued), `inbox` (nothing runs in the bank; the zone's packages are imported), `mock` (the keyword agent,
  never a model).
- **Live runs are queued** (AI-13): “Chạy Agent CIO” writes an `agent_jobs` row and answers at once; the
  `agent_worker` job (every 5 s, one run at a time) runs `cio_agent_flow`; the event page follows the job.
- **The zone is `app/zone.py`**, served with `operonx serve -f operonx.zone.toml`, with its own `MF_STATE` file and a
  data folder holding only the catalogue files (`scripts/make_zone_data.py`). `MF_ZONE=on` makes any read of the
  people table raise (ZONE-01). It runs the bank's own graphs: `ingest_flow` on the white-listed feeds and
  `cio_agent_flow` on its events, as the actor `agent:zone`, which exists only there.
- **Bank → zone** (ZONE-06): the `zone_sync` job pushes the approved `factor_model`, `restricted`,
  `forbidden_phrases`, `news_sources`, `prompts` and `models` versions and the released research, signed with
  `MF_ZONE_KEY`, only when they changed. The zone puts each in force as the bank approved it (`config.mirror`, the
  zone only).
- **Zone → bank** (ZONE-02, SEC-07): one door, `POST /api/inbox`, open only in inbox mode, answering `202 {"id"}`
  and nothing else; at most 512 KB a package and 200 waiting. Packages are signed HMAC-SHA256 with `MF_INBOX_KEY`;
  with the key set, an unsigned or wrongly signed package is rejected (LC-04).
- **The import** (ZONE-03, `inbox_import` every 10 minutes) passes each package through the checks a live run
  passes, before anything is written: signature, form, every news item matched by its address to one the bank
  fetched itself (never taken from the package), not held, the view's format check, the findings' form. Then the
  event, the view, the zone's trace and the challenge (the rules run again) are written and the view waits for the
  CIO. A rejected package changes nothing and keeps its error.

## Consequences

- The barrier is now both: the agent graphs still take only market inputs (ADR-0009's test stays), and in inbox
  mode the process that calls a model has no customer data to leak. On one demo host the two processes share a
  machine, not a database.
- The zone reads nothing back from the bank: an imported, rejected or approved view is never told to it.
- The live demo stays in `live` mode; inbox mode needs the zone process and the two keys set.
