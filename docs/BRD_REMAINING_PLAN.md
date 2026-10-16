# OneWealth — The BRD's last 15 rows: audit and plan

After [BRD_COMPLETION_PLAN.md](BRD_COMPLETION_PLAN.md) (F1–F10), 150 of the BRD's 165 rows are verified
([BRD_COMPLETION_REPORT.md](BRD_COMPLETION_REPORT.md)). The owner asked (2026-10-16) about the other 15. This plan
says, row by row, what can still be built and proven here, builds it, and names exactly what only a bank or a
pilot can supply.

## 1. The 15 rows, audited

| Row | BRD asks | What exists | What this plan builds | What stays outside |
|---|---|---|---|---|
| NFR-11 | Every number has a “cách tính” control | News-impact numbers (staff trace, client drawer) | **G1**: one `how` contract on every derived number of every page, one drawer, a browser test that fails on any number without it | — |
| NFR-08 | Client data never to an AI provider; stored in Vietnam; provider neither stores nor trains | News-impact barrier (BR-11); statement reader and chat send client text when AI is on (ADR-0018, demo) | **G2**: a `client_ai` setting (off / on-premise / demo) with one barrier at every model call; on-premise model route for the two steps; a recorded-provider test proving no client text leaves in `off` and `onprem` | Hosting in Vietnam and the provider contract |
| NFR-07 | Encryption in transit and at rest; keys in a secret store; penetration and prompt-injection tests | Prompt-injection test; HMAC sessions | **G3**: client-data columns encrypted (AES-GCM), keys from a secret-store interface with rotation, security headers and Secure cookies, an automated attack suite | A third-party penetration test; TLS is the host's (ngrok on the demo) |
| DATA-10 | Moving to the bank: PostgreSQL, JSON fields split into tables, client columns encrypted, `audit_log` on WORM | SQLite; hash-chained audit log | **G4**: export to PostgreSQL with the split schema, proven against a real PostgreSQL in Docker; the audit log exported to write-once segments that `audit_check` verifies; the migration guide | The bank's database and WORM storage themselves |
| NFR-03 | 99.5 % in business hours; AI failure stops nothing | AI-outage test (verified) | **G5**: a heartbeat job and the availability measured in business hours, in Hệ thống and the monthly report, an alert below 99.5 % | The bank's hosting reaching 99.5 % |
| KPI-01 | News → RM ≤ 2 h; **urgent** ≤ 30 min | 2 h measured monthly | **G6**: “urgent” defined (our reading, labelled), the CIO's urgent flag, measured ≤ 30 min | — |
| KPI-02 | **Important** news collected ≥ 95 % | — (Q-07) | **G6**: “important” defined as news an independent reference (Google News, ≥ 2 outlets) carries on our topics; coverage measured daily | The 95 % itself on bank sources |
| KPI-05 | Recommendations with a reviewer and a log: 100 % | Views, runs, letters, summaries reviewed and audited | **G7**: the rate computed from the records, in the monthly report | — |
| KPI-06 | RM contacts that start from a system signal ≥ 50 % | — | **G7**: an RM contact log (from a signal or not) and the share | Real RM behaviour (pilot) |
| KPI-07 | High-level alerts opened by clients ≥ 70 % | Staff alert acks | **G7**: client opens of high-level items recorded; the rate | Real client behaviour (pilot) |
| ROLE-05, WF-08 | A certified specialist approves action recommendations for assigned families | Specialists on teams; RM approval queue (FEAT-27) | **G8**: certifications as configuration; action recommendations need a certified, assigned specialist's approval before the RM delivers | — |
| MEAS-06 | Business effect: with vs without the tool, quarterly | — | **G9**: a Compliance-approved control group (stratified, seeded), the tool's signals withheld from it, the quarterly comparison with intervals | The effect on real clients (pilot) |
| SCOPE-03, SCOPE-05 | Out of the BRD's module | — | Nothing: they do not apply (ADR-0003, ADR-0008) | — |

## 2. Decisions

| # | Decision | Why |
|---|---|---|
| G-D1 | **A number's “cách tính” comes from the server with the number** (`how`: formula in words, inputs with their sources), never rebuilt in the browser. A page marks each derived number `data-num`; the shared drawer opens its `how`. A browser test walks every route as each role and fails on a `data-num` without `how`. Raw inputs (a holding's value from a statement) carry their source instead of a formula | NFR-11 says every number; only a test can keep it true |
| G-D2 | **`client_ai` is configuration** (owner Admin, two people): `off` (rules only), `onprem` (the two steps call `llm:onprem`, whose host must be on an allow-list), `demo` (today's behaviour, ADR-0018). Every model call passes one barrier: in `off` and `onprem` a prompt bound for an outside provider that contains any client's name, id or account number is refused before sending. The live demo stays `demo` | NFR-08 for a bank without breaking the owner's demo decision |
| G-D3 | **Encryption at rest is per column** for client data (people records, sources, holdings, profile, family results), AES-256-GCM with the row id as associated data, keys versioned (`k1`, `k2`…) so rotation re-encrypts in place. Keys come from `control.secrets`: environment, a file, or a Vault-compatible HTTP store | DATA-10 names column encryption; SQLite has no built-in encryption |
| G-D4 | **PostgreSQL is proven by export, not by running the app on it**: a script maps every table to PostgreSQL DDL, splits the JSON fields the pages filter on into tables, loads a real PostgreSQL (Docker) and checks counts and sums against SQLite. The app keeps SQLite (a full port is the bank's migration project) | DATA-10 is guidance for moving; proving the mapping is what can be proven here |
| G-D5 | **Availability = minutes with a heartbeat / business minutes** (Mon–Fri 08:00–17:30, Vietnam time), from a 1-minute heartbeat job. A deploy restart counts as downtime | Measured, not claimed |
| G-D6 | **“Urgent” (KPI-01)**: an event the CIO flags urgent (with a reason), proposed automatically for SBV rate or FX-band decisions and moves past the factor's 3-sigma day. **“Important” (KPI-02)**: a story on our topics that the independent reference carries from ≥ 2 outlets within a day. Both labelled “Đề xuất” until the owner defines them | Resolve rather than defer (Q-07); the label keeps it honest |
| G-D7 | **A recommendation for action** is an RM queue item with actions (FEAT-27) or a family-specific note from the RM. It needs a certified specialist assigned to that family to approve before delivery, when the family has one; the RM approves alone otherwise, as the BRD's “if any” allows | ROLE-05 and WF-08 on the product's existing queue |
| G-D8 | **The control group is a Compliance configuration**: share (default 10 %), stratified by segment and RM, seeded so it is reproducible; control families still get every run (computing is unchanged) but their RM sees no Hôm nay case and no proactive alert for them. The quarterly report compares contact rate, goal levels and alert-driven actions with 90 % intervals | MEAS-06; withholding signals, never data or service |

## 3. Phases

One branch and PR per phase, in this order; each merged, deployed and its docs and matrix rows updated before
the next.

- **G1 — Cách tính everywhere (NFR-11).** The `how` contract; the drawer; every page; the route test. **Done**
  (2026-10-16): about 95 metrics in `src/explain/metrics.py`; 1,171 unexplained figures on the dev data → 0;
  `tests/ui/test_how.py`, `tests/test_explain.py`. G-D1 as built: the formula is the server's (the catalogue), the
  inputs come with the number from the same answer; the attribute is `data-metric`, not `data-num`.
- **G2 — The client-data barrier (NFR-08).** `client_ai`; the barrier; `llm:onprem`; the recorded-provider test.
  **Done** (2026-10-16, ADR-0023): operonx 1.28.0 adds `ResourceHub.guard` (a check before every call of a resource,
  whichever op makes it); `src/control/barrier.py` guards every `llm:` resource; `tests/test_barrier.py` proves it at
  the wire against a recording server. Found on the way: the CIO agent's client for another model name was built
  outside the hub, so it is guarded too. The live demo stays `demo`.
- **G3 — Encryption and secrets (NFR-07).** `control.secrets`; column encryption and rotation; headers and
  cookies; the attack suite. **Done** (2026-10-16, ADR-0024): what to seal was found by scanning a populated database
  — beyond G-D3's list, the run snapshots, rankings and exposures, RM proposals and the chat history hold client
  names too; inside runs only those fields are sealed, so the snapshot-head SQL (NFR-01) is unchanged. operonx 1.29.0
  adds `Application(middleware=…)` so the headers cover the graph services. Found on the way: an unknown client id
  answered 500 (now 400). NFR-01 with keys on, 6,500 families, same machine: apply 165.6 s (167.3 s plain), the
  slowest family read 0.43 s (0.31 s plain) — BRD ≤ 300 s and ≤ 2 s.
- **G4 — Moving to the bank (DATA-10).** PostgreSQL export proven in Docker; WORM audit segments; the guide.
- **G5 — Availability (NFR-03).** Heartbeat, the business-hours measure, the alert.
- **G6 — Urgent and important news (KPI-01, KPI-02).** The flag, the reference feed job, the two measures.
- **G7 — Control and behaviour measures (KPI-05, KPI-06, KPI-07).** The review rate, the RM contact log, client
  opens.
- **G8 — The certified specialist (ROLE-05, WF-08).**
- **G9 — The control group (MEAS-06).** Then the report updated: what is verified, what only a pilot or the bank
  can show.

## 4. What the owner may be asked

Nothing blocks the plan. G-D6's two definitions are ours until the owner gives the bank's.
