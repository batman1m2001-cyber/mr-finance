# ADR-0025 — The move to the bank proven by export; the audit log on write-once segments

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** BRD §11.4 (BRD-RULE-DATA-10: keep the entities; move to PostgreSQL or the bank's standard database;
  split frequently queried JSON fields into tables; encrypt client columns; put `audit_log` on WORM storage);
  docs/BRD_REMAINING_PLAN.md G-D4, G4

## Context

The demo keeps everything in one SQLite file, much of it in JSON `data` columns, and its audit log is hash-chained
in that same file: anyone who can write the file and has no HMAC key can change a row and recompute every hash
after it. The BRD asks for guidance on moving to the bank, not for the demo to run on PostgreSQL.

## Decision

- **Proven by export, not by running on PostgreSQL** (G-D4). `src/control/pgexport.py` maps every table to
  PostgreSQL, splits the JSON fields the product reads by field into columns (3 tables) and child tables (15), and
  `scripts/export_postgres.py` loads a real PostgreSQL (Docker, or the bank's) and checks it: counts, sums, and
  every row read back, rebuilt and compared with SQLite. The application stays on SQLite; the port is the bank's
  project, its places listed in [bank_migration.md](../architecture/bank_migration.md).
- **Lossless before tidy.** A value is split only when it has the expected shape; anything else stays in `data`.
  The rebuild is the proof, so the mapping cannot silently drop a field.
- **Encryption carries over.** Sealed values are bound to table, primary key and column, so those not split are
  copied as they are; split ones are opened with the keys and sealed again at the child's own place. A sealed
  database is not split without the keys.
- **The audit log on write-once segments** (`src/control/worm.py`). The hourly `audit_check` writes the rows added
  since the last segment to a new file, written once (published by hard link, read-only), chained to the previous
  segment by its hash, and checks every segment against the database row by row. A rewritten history that passes
  the database's own chain check is caught. On the demo the folder is beside the state file (`MF_AUDIT_WORM`); at
  the bank it is a bucket under S3 Object Lock in compliance mode.

## Consequences

- The schema of the bank's database exists as code (`export_postgres.py --schema`) and is tested against
  PostgreSQL 16 in the suite when Docker and the image are present (`tests/test_bank_move.py`).
- A broken segment raises the same high “audit chain” alert as a broken chain; no segment is written on top of a
  broken record.
- Not done here: running the application on PostgreSQL, and the bank's WORM storage itself.
