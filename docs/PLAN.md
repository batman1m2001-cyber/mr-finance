# Mr. Finance — build plan

The brief: [`mr_finance_idea_final.md`](../mr_finance_idea_final.md) (plan v2, "Consolidate + Dashboard tổng thể"). Its message:
*a client holds assets across many products, channels and platforms, and nobody shows them the
whole picture. We do, and we say what is moving it.*

This repo builds that product as a working demo on **operonx** (graphs, services, jobs) and
**operonx-agents** (the chat that takes a client's own declarations). Every computation is an
operonx graph the studio can draw and trace; the web UI only calls them.

## 1. Decisions

| # | Decision | Why |
|---|---|---|
| D1 | **Mock data, real logic.** The bank, broker, fund and property sources are fixtures for 5 sample clients; every number on screen is computed by the graphs from them. | A demo must run anywhere; the logic is what we show. |
| D2 | **AI where the brief says AI, with a rule fallback.** Statement reading and the chat declaration use `llm:assistant` when `LLM_API_KEY` is set (`MF_AI=auto`), and deterministic parsers otherwise (`MF_AI=off`, or no key). The choice is an `if_` branch in the graph, so both paths are visible. | The demo never depends on a network; the AI path is real when a key exists. |
| D3 | **The risk test is rules, not a model.** An adaptive question tree with situational questions; tolerance from answers, capacity from the client's own data. | Explainable and auditable (compliance); the brief's "AI" is the adaptivity and the capacity check. |
| D4 | **Advice is a simulation until an RM approves it.** Scenario and alert suggestions go to an RM queue; the client sees "chờ RM duyệt" until a decision. | The brief's compliance step. |
| D5 | **Money in VND integers**, shown as tỷ / triệu. UI text in Vietnamese; code and docs in English. | The audience is Vietnamese; the code follows operonx conventions. |
| D6 | **State in SQLite** (`data/state.db`, gitignored, made on demand): what a client added (statements, declarations, dependents), risk results, alerts, the RM queue. Fixtures stay read-only; `reset` empties the state. | One file, no server, works with pip or uv. |
| D7 | **One Application, one port.** JSON APIs are `http` services on graphs; the web UI and plain reads (client list, RM queue list) are one `asgi` service mounted last at `/`. | `operonx serve` runs the whole product. |
| D8 | **Policy facts are dated fixtures with a status** (dự thảo / lấy ý kiến / đã thông qua) and a source line. The UI says they must be checked before a real demo. | The brief warns that their legal status moves fast. |

## 2. Layout

```text
mr-finance/
├── app/main.py            # APP: every service and job, with the graph it runs
├── app/web.py             # the asgi app: the UI (web/) and plain reads
├── src/wealth/            # shared domain: models, fixtures, store, money, market maths (no graphs)
├── src/consolidate/       # tier 1/2/3 sources → one holdings list with trust labels; family scope
├── src/statements/        # an uploaded statement (PDF/Excel/CSV) → holdings (AI or rules)
├── src/declare/           # chat → declared assets, income, dependents (agent or rules)
├── src/dashboard/         # net worth, allocation, P&L vs benchmark, drawdown, concentration,
│                          # liquidity months, 12–36 month cash-flow calendar
├── src/risk/              # the adaptive risk test, tolerance vs capacity, the 5 personas
├── src/impact/            # impact = exposure × sensitivity × probability; policy & macro alerts
├── src/scenarios/         # life-event simulations and market stress tests (heavy / light)
├── src/review/            # the RM queue: propose, approve, reject
├── data/                  # fixtures: clients, market, policies, infrastructure, sample statements
├── web/                   # the UI: one page app, Vietnamese, no build step
└── tests/
```

## 3. The features (each an operonx graph)

1. **consolidate_flow(client_id, scope)** — tier 1 (Techcombank, TCBS, Techcom Capital,
   OneHousing; automatic), tier 2 (other banks and brokers: Open API mock, or a stored statement),
   tier 3 (declared). Fetches run in parallel, are normalised to one holding shape, labelled
   `verified` / `statement` / `declared`, de-duplicated, and widened to the household when
   `scope="family"` (only members who consented).
2. **dashboard_flow(client_id, scope)** — on top of consolidation: net worth and its month change,
   allocation by class, realised / unrealised P&L against the client's benchmark, the drawdown
   threshold against an estimated current drawdown, concentration (sector, area, issuer),
   liquidity reserve in months of spending, the cash-flow calendar (recurring items detected from
   transactions, plus known future payments) and the count of open alerts.
3. **statement_flow(client_id, filename, content)** — read the file (PDF text, Excel/CSV rows),
   extract holdings with the model or the rules, validate, store as `statement` holdings.
4. **declare_flow(client_id, message, session_id)** — an operonx-agents `Agent` with tools
   (`declare_property`, `declare_gold`, `declare_dependent`, `declare_income`, …) that write to the
   client's profile; rules when there is no model.
5. **risk_flow(client_id, answers)** — the next question (8–12, adaptive) or the result:
   tolerance, capacity, the mismatch warning, one of 5 personas.
6. **alerts_flow(client_id)** — every policy, macro factor and infrastructure project matched to
   the client's holdings; impact in VND and % of net worth, 🔴/🟡/🟢, with its source. Also a job,
   `policy_sweep`, over every client, on a daily schedule.
7. **scenario_flow(client_id, scenario, params)** — 9 life-event scenarios and 5 stress tests;
   each answers with numbers and a heavy / light option, sent to the RM queue.
8. **review_flow(item_id, decision, note)** — an RM approves or rejects a proposal.

## 4. Phases

Each phase is a branch, merged when its gate passes (tests green; UI phases with desktop and
phone screenshots).

| Phase | What | Gate |
|---|---|---|
| P1 | domain, fixtures for 5 clients, consolidate + dashboard graphs and their services | unit tests on every op; graph tests on all 5 clients |
| P2 | the web UI: client picker, Kết nối dữ liệu, Dashboard (cá nhân / gia đình) | screens, desktop + phone |
| P3 | statements (AI + rules) and the chat declaration (agent + rules) | tests with a scripted model; sample statements read |
| P4 | the risk test | tree tests; personas for the 5 clients |
| P5 | impact, alerts, the policy sweep job and schedule | impact maths tests; the job over all clients |
| P6 | scenarios, stress tests, the RM queue | scenario maths tests; approve / reject end to end |
| P7 | the 5-minute demo flow, README (agent-first, uv and pip), evals | the demo script runs clean |

## 5. Status

- P0 (scaffold, public repo): done.
