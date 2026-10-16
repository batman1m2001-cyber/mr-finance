# OneWealth — The BRD's original features: completion report

For the owner. What the plan [BRD_COMPLETION_PLAN.md](BRD_COMPLETION_PLAN.md) set out to finish, what is now
built and proven, and what is still open and why. The single source of each requirement's status remains the
[traceability matrix](brd/requirements/requirements_traceability.md); this report is a reading of it on
2026-10-16, after phase F10.

## 1. In one paragraph

The BRD has 165 rows: 61 numbered requirements, 7 success metrics and 97 rules. At the start of the plan 108 were
verified and 40 were open. Now **163 are implemented and verified by tests** (150 after F10; NFR-11, NFR-08,
NFR-07, RULE-DATA-10, NFR-03, the success metrics' last five, ROLE-05, WF-08 and MEAS-06 after G1–G9 of
[BRD_REMAINING_PLAN.md](BRD_REMAINING_PLAN.md)). The other 2 do not apply to this product. What a test cannot show —
the bank's systems, real people's behaviour — is listed in §4.
**Nothing is partial**, blocked, planned or unbuilt.

| Set | Rows | Verified | Partial | Out of scope (demo) | Not applicable |
|---|---|---|---|---|---|
| BRD numbered (BR, FR, NFR) | 61 | 61 | 0 | 0 | 0 |
| BRD success metrics (KPI) | 7 | 7 | 0 | 0 | 0 |
| BRD rules (RULE) | 97 | 95 | 0 | 0 | 2 |
| **Total** | **165** | **163** | **0** | **0** | **2** |

“Verified” means a test in `tests/` exercises the requirement and passed in the latest full run; the documentation
checker (`scripts/check_brd_docs.py`) refuses a verified row whose test does not exist, and recomputes the counts.

## 2. What each phase delivered

| Phase | What | PR |
|---|---|---|
| F1 | Every person in SQLite; everyone signs in with their own account; market sources on scheduled jobs | #41, #42 |
| F2 | The factor model estimated from that market history | #42 |
| F3 | Accuracy over time; the monthly measurement reports | #43 |
| F4 | Assumptions, forbidden phrases, consent, prompts and models as versioned configuration; the eval set gates prompt and model changes | #44 |
| F5 | Every served route walked as every person; refusals answer 403/401; RM assignment as configuration | #45 |
| F6 | Agent runs queued and run by a worker; the AI zone as a second process; the signed inbox | #46 |
| F7 | Alerts and the central log | #47 |
| F8 | The CIO newsletter; conflict of interest as a structured, enforced field | #48 |
| F9 | The policy agent (quotes checked word for word inside their article) and the policy radar | #49, #50 |
| F10 | Per-goal VND impact; the client's “Cách tính”; agent time limits; schedule and browser tests; the 6,500-family scale test | #51 |
| G1 | “Cách tính” on every number (NFR-11) | #54 |
| G2 | The client-data barrier, by configuration (NFR-08) | #55 |
| G3 | Client data sealed at rest, keys from a secret store, security headers, the attack suite (NFR-07) | #56 |
| G4 | The PostgreSQL export checked row for row against a real PostgreSQL; the audit log on write-once segments; the migration guide (RULE-DATA-10) | #57 |
| G5 | Availability in business hours measured from a heartbeat, in Hệ thống and the monthly report, an alert below 99.5 % (NFR-03) | #58 |
| G6 | Urgent news: the CIO's flag, the product's proposals, measured against 30 min (KPI-01); important news collected, against an independent reference read every 2 h (KPI-02) | #59 |
| G7 | Recommendations reviewed and logged, from the records (KPI-05); the RM's contact log and the share from a signal (KPI-06); client opens of high-level items (KPI-07) | #60 |
| G8 | The certified specialist: specialists sign in; certificates as configuration; an approved action recommendation waits for the family's certified specialist, if any; the RM's own recommendation through the same gate (ROLE-05, WF-08) | #61 |
| G9 | The control group: seeded and stratified (Compliance, two people), its RM gets no signal, the quarterly comparison with 90 % intervals (MEAS-06) | #62 |

## 3. The scale requirement, measured (NFR-01)

`scripts/scale_test.py --families 6500` clones the demo households to 6,500 families (amounts scaled ×0.5–×2), in
a fresh database, approves one view and times it; then reads one family's pages with all 6,500 stored.

| Measure | BRD | Measured (2026-10-16, one machine, 24 CPUs, SQLite) |
|---|---|---|
| One approval applied to every family | ≤ 5 min | **167.3 s** |
| Family impact (client / RM) | ≤ 2 s | 0.26 s / 0.23 s |
| Client “Cách tính” | ≤ 2 s | 0.28 s |
| Staff trace | ≤ 2 s | 0.29 s |
| Impact graph | ≤ 2 s | 0.29 s |
| Dashboard | ≤ 2 s | 0.04 s |

The first full run took 166 s to apply but 2.5–3.6 s to read a family: a family's page decoded every family's
result to show one, and the 27 MB snapshot to read its model. Both now read only what the page needs; the reads
fell tenfold. The bank's own database and hardware will give other numbers: this proves the design holds at the
BRD's size, not the bank's servers.

## 4. What is verified, and what only a pilot or the bank can show

Nothing is partial. Not applicable: RULE-SCOPE-03 (the product keeps its pre-BRD connectors, ADR-0003) and
RULE-SCOPE-05 (nothing is sent; the client view is in-app, ADR-0008).

“Verified” means the product does it and a test proves it. For some rows the BRD's target is a number about the
bank's systems or about people; the product measures it, and only the bank or a pilot can make it true:

| Row | Verified here | Only the bank or a pilot can show |
|---|---|---|
| NFR-03 | Availability measured from a heartbeat in business hours; an alert below 99.5 % | The bank's hosting reaching 99.5 % |
| NFR-07 | Client data sealed per column, keys from a secret store, headers, the attack suite | A third-party penetration test; TLS on the bank's hosts |
| NFR-08 | The barrier at every model call, by configuration | Hosting in Vietnam; the provider's contract |
| RULE-DATA-10 | The PostgreSQL export checked row for row; the audit log on write-once segments | The bank's database and WORM storage |
| KPI-01, KPI-02 | “Urgent” and “important” by our reading (G-D6, “Đề xuất”), measured | The bank's definitions; 95 % on the bank's own sources (dev copy: 57 %) |
| KPI-06, KPI-07 | The RM's contact log and the client's opens, measured | The 50 % and 70 %: RM and client behaviour |
| MEAS-06 | A seeded, stratified control group, its signals withheld, the quarterly comparison with intervals | The effect: the demo's five families cannot show one (the default 10 % draws none of them) |

## 5. Decisions still with the owner

- **Q-09, the policy radar's reading.** The radar shows each policy document's status path (draft → consultation
  → issued → effective) and what changed; it is our reading of the BRD's “radar”, labelled “Đề xuất” on screen.
- **Q-03, engine presets.** The overview card is now labelled as the policies' own rules and links to the engine's
  impact; turning the price-moving rules into engine presets (news plan N5) is a later phase.
- **Optional data.** A FRED API key would give the US series an official fallback; a paid source would let the
  three assumed factors (credit spreads, house prices) be estimated rather than labelled assumed.

## 6. Every numbered requirement

Generated from the matrix on 2026-10-16; the matrix has each row's code, screens, tests and evidence.

| ID | Requirement (short) | Status | Tests cited |
|---|---|---|---|
| BRD-BR-01 | Three news sources, each labelled | verified | 2 |
| BRD-BR-02 | White-listed public sources; published ≤ ingested | verified | 1 |
| BRD-BR-03 | Research enters only when released by another person after its time | verified | 2 |
| BRD-BR-04 | Restricted-list mentions held for Compliance | verified | 2 |
| BRD-BR-05 | 2–4 scenarios with probability, shocks, sources; AI gives no numbers | verified | 2 |
| BRD-BR-06 | Independent challenge before approval; critical findings answered | verified | 1 |
| BRD-BR-07 | CIO approves scenarios and model parameters; nothing computed before | verified | 2 |
| BRD-BR-08 | VND per position and loan, 3 horizons, E and P5/P10/P50/P90; summed by class, factor, family, goal; one engine for ranking, alerts, goals, explanation | verified | 5 |
| BRD-BR-09 | RM pre-review at a 3-month bad case ≤ −5 % | verified | 1 |
| BRD-BR-10 | Regulations delaying goals abroad reach the right families, no AML data | verified | 2 |
| BRD-BR-11 | AI drafting reads no client data, goals, RM notes | verified | 1 |
| BRD-BR-12 | Every number traceable; immutable log | verified | 2 |
| BRD-BR-13 | CIO sees all clients' exposure by factor | verified | 1 |
| BRD-BR-14 | CIO withdraws a view; RMs see “Đã thu hồi” | verified | 1 |
| BRD-BR-15 | Accuracy over time vs the forecast band | verified | 2 |
| BRD-FR-101 | RSS every 10 minutes | verified | 3 |
| BRD-FR-102 | Classify, score relevance, suggest event type | verified | 1 |
| BRD-FR-103 | CIO inbox: filter, dismiss, group | verified | 2 |
| BRD-FR-104 | Public source and timestamps checked before an event | verified | 1 |
| BRD-FR-105 | Hold events naming the restricted list until Compliance allows | verified | 2 |
| BRD-FR-201 | Upload a report with its fields | verified | 1 |
| BRD-FR-202 | Compliance releases/rejects, note ≥ 20, restricted list, releaser ≠ uploader | verified | 2 |
| BRD-FR-203 | Unreleased or early research not in the inbox, not attachable | verified | 1 |
| BRD-FR-204 | Regulation-note fields; goal branch, not price events | verified | 1 |
| BRD-FR-301 | CIO agent: 4 groups, ≤ 2 debate rounds, synthesis, ≤ 2 retries | verified | 2 |
| BRD-FR-302 | View: impact rows −3…+3 and 2–4 branches | verified | 1 |
| BRD-FR-303 | Challenger before approval and on edits; 3 severities | verified | 1 |
| BRD-FR-304 | CIO edits, answers, approves/returns/rejects/withdraws with reasons | verified | 2 |
| BRD-FR-305 | Market-level preview per branch before approval | verified | 1 |
| BRD-FR-306 | Policy agent and policy radar | verified | 4 |
| BRD-FR-307 | Three run modes: live, inbox, mock | verified | 3 |
| BRD-FR-401 | On approval: snapshot, compute all, hashed run | verified | 2 |
| BRD-FR-402 | Family result: bands, contributions to each position, loan interest, modelled share | verified | 1 |
| BRD-FR-403 | Rank all families; all-client summary by factor | verified | 2 |
| BRD-FR-404 | Goal impact: funding before/after, Đạt / Theo dõi / Thiếu | verified | 3 |
| BRD-FR-405 | Recompute and compare; withdraw a run | verified | 2 |
| BRD-FR-406 | “Cách tính” and trace to the news | verified | 1 |
| BRD-FR-501 | Post-check rules; summary | verified | 1 |
| BRD-FR-502 | RMs see only post-checked runs, labelled | verified | 2 |
| BRD-FR-503 | Flag “RM xem trước” at 3-month P10 ≤ −5 % | verified | 1 |
| BRD-FR-601 | RM declares outflow purpose/country; inference otherwise | verified | 2 |
| BRD-FR-602 | Match notes to goals; milestone and level | verified | 2 |
| BRD-FR-603 | Shown on RM home, Goals tab, Research page | verified | 2 |
| BRD-FR-604 | Refuse AML wording | verified | 1 |
| BRD-FR-701 | Versioned, owned configuration; propose then approve | verified | 6 |
| BRD-FR-702 | Hash-chained log; integrity check; export | verified | 3 |
| BRD-FR-703 | Agent catalogue | verified | 2 |
| BRD-FR-704 | Per-step trace of the CIO agent | verified | 1 |
| BRD-FR-801 | CIO newsletter | verified | 3 |
| BRD-NFR-01 | 6,500 families ≤ 5 min; family page ≤ 2 s | verified | 2 |
| BRD-NFR-02 | News to inbox ≤ 10 min; CIO agent ≤ 15 min | verified | 3 |
| BRD-NFR-03 | 99.5 %; AI failure does not stop computing or viewing | verified (G5) | 5 |
| BRD-NFR-04 | Same snapshot → same result to the dong | verified | 2 |
| BRD-NFR-05 | Exact money; no floats for balances | verified | 1 |
| BRD-NFR-06 | New factors, classes, agents by configuration; provider change without architecture change | verified | 3 |
| BRD-NFR-07 | Encryption, secret store, pen and prompt-injection tests | verified (G3) | 7 |
| BRD-NFR-08 | Client data in Vietnam; never to an AI provider | verified (G2) | 2 |
| BRD-NFR-09 | Immutable log; retention per bank rules | verified | 1 |
| BRD-NFR-10 | Token limits, daily budget, cost per event | verified | 2 |
| BRD-NFR-11 | Vietnamese; “cách tính” on every number; desktop and phone | verified (G1) | 2 |
| BRD-NFR-12 | Central logs; alerts on feed, agent, chain failures | verified | 3 |

## 7. How to check this yourself

```bash
uv run pytest -q                                  # or: pip install -e . && pytest -q
.venv/bin/python scripts/check_brd_docs.py        # the matrix against the tests and the counts
.venv/bin/python scripts/scale_test.py --families 6500 --json nfr01.json
```
