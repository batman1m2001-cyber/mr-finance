# ADR-0027 — Conversations and memory in their own SQLite file, in WAL mode

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** OWN-AS-10; brief §2 (“Evaluate whether SQLite is appropriate…”); docs/ASSISTANT_PLAN.md A-D2;
  measurement in [assistant.md §8](../architecture/assistant.md#8-storage-measurement-a0-2026-10-16--adr-0027)

## Context

Chats write often, in small turns, beside the product's business writes. The product's `state.db` runs SQLite in
rollback-journal mode with a connection per transaction (`control/db.py`), one server process. The brief asks for a
measured choice: neither SQLite by habit nor a new database without reason.

## Decision

- `data/assistant.db`, SQLite in **WAL** mode, one shared connection per process, holding the `operonx-agents`
  session items and run state and OneWealth's `conversations`, `memory_items` and `follow_ups`.
- Not in `state.db`: measured, the same chat load there gives 52–71 turns/s with p99 of 2.6–8.4 s and lock errors,
  and would delay business writes. The separate WAL file sustains ~127 turns/s on the demo host; the BRD's busy-hour
  load is ~10 turns/s.
- No new database for the demo. The stores sit behind the `Session` / `StateStore` interfaces (PostgreSQL or Redis at
  the bank; `RedisSession` exists) and the file joins the PostgreSQL export (ADR-0025).
- Backups: SQLite's online backup, hourly, beside the state file's.

## Consequences

Two SQLite files to back up and export. One writer at a time on the chat file (fine at the measured headroom). The
library's connection-per-session use failed under load (4 lock errors in 1,000 turns); it is fixed upstream before
A3 relies on it.
