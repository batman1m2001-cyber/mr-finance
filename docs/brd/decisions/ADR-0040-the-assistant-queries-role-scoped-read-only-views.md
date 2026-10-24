# ADR-0040 — The assistant queries role-scoped, read-only views with SQL (`truy_van`)

- **Status:** accepted
- **Date:** 2026-10-24
- **Sources:** plan [`docs/ASSISTANT_DATA_PLAN.md`](../../ASSISTANT_DATA_PLAN.md); the owner's request
  ([`2026-10-24_assistant_data_access.md`](../sources/owner_requests/2026-10-24_assistant_data_access.md)); the CIO
  chat of 2026-10-24 (the assistant said 200 news items when the inbox held 1,415)
- **Amends:** the rule in `src/assistant/base.py::Param` ("never a path, a query language or a URL"), for one tool
- **Keeps:** [ADR-0012](ADR-0012-the-copilot-routes-and-never-reads-client-data.md) (no data in the prompt), the client-data barrier

## Context

Every assistant tool takes typed, bounded arguments (`Param`), never a query language, so the model can only ask
what a tool foresees. On 2026-10-24 the CIO asked how many news items had been fetched; the only tool returned the
length of a list capped at 200, the model repeated the cap and argued when corrected. A hotfix counts the inbox in
the database, but the owner's point is the questions no fixed tool foresees ("tin nào về lãi suất tuần này", "bao
nhiêu nhận định bị bác tháng 10"). Each one ends today as a wrong number or as "không có công cụ".

The same audit found that several pages and tools show the length of a page of rows as a total (the inbox page
says 300 for 1,415; alerts stop at 50; search says "6 kết quả").

## Decision

1. **Totals are counts.** A number shown or said as a total comes from a count in the database, one function shared
   by the page and the assistant; a page of rows says "50 / 1.415".
2. **One tool, `truy_van`, takes a SQL `select`** — the single exception to `Param`'s rule, bounded as follows:
   - **Views, never tables.** One connection per call to `state.db`, opened `mode=ro` with `PRAGMA query_only = ON`.
     The model sees only TEMP views (or TEMP tables filled from the same Python reads the pages use) built for the
     person signed in, from the pages' access rules (`people.auth.visible`, `desk.reads.book_of`). Never exposed:
     `accounts`, e-mail addresses, passwords, the audit chain's hashes, another family's rows, held news.
   - **SQLite's authorizer** allows `SELECT`, `READ` of those views and a short list of functions; everything else is
     denied (any real table, `ATTACH`, `PRAGMA`, writes, transactions, `load_extension`, recursive CTEs).
   - **Limits:** 2 s per query (a progress handler), 200 rows returned with the total always counted, one statement
     per call, at most 3 calls per turn.
3. **A catalog per role** (views, columns, units, allowed values, the business's definitions and example questions)
   is what the model reads; a test fails on an undocumented column. No data values enter the prompt (ADR-0012).
4. **The person sees how it was counted:** the SQL, the row count and `as_of` under "Cách tính" (collapsed); each
   query is audited (who, role, SQL, rows, time). With `client_ai` off the model writes the SQL but never reads the
   rows; a template assembles the answer.
5. **When a number is contradicted, the assistant counts again** and shows how; it does not argue.
6. **The fixed tools stay;** `truy_van` is the fallback for what they do not cover.
7. **The model is chosen by an eval** (~30 questions per role, gold answers from the database): Haiku first, Sonnet
   for the SQL step only if Haiku is below the gate (accuracy ≥ 90 %, p95 ≤ 6 s, ≤ US$0.01 a turn).

## Consequences

- The assistant answers questions no tool foresaw, and every number it says can be checked from its SQL.
- The security boundary moves from "the model cannot express a query" to "the connection cannot see or do anything
  but the person's views": the adversarial tests (real table, `ATTACH`, a write, another family's row, held news, a
  slow query, `PRAGMA`, `load_extension`, a recursive CTE, several statements) are the gate.
- No new database or service. On PostgreSQL (DATA-10) the same views become a read-only role with row-level security.
- Data from fixtures (a family's holdings, flows, goals) is copied into TEMP tables per call, so a query that names
  them costs a valuation; views are built only when the SQL names them.
