# Requirements of the redesign kit — `KIT-<area>-nn` (proposed extensions)

Layer A, third source: the OneWealth Redesign & Product Evolution Kit, kept verbatim in
[`../sources/redesign_kit_2026-10-15/`](../sources/redesign_kit_2026-10-15/). Its capabilities are **not in the
BRD** (no assistant, Sankey or relationship graph is mentioned there — see Q-06) and are therefore **proposed
extensions**. The product owner accepted the plan built from them on 2026-10-15 (“do as you like”,
[`docs/REDESIGN_KIT_PLAN.md`](../../REDESIGN_KIT_PLAN.md)), so they are *approved for planning*, not built.

The kit's concept board ([KIT-01](../assets/proposed_ui/KIT-01_concept-board_illustrative.png)) is illustrative:
its figures (e.g. “90 yêu cầu / 84 đã triển khai”, “Thu nhập 180,2 tr”, “Mua nhà 10 tỷ, 68 %”) are not the
product's data and must never be cited as evidence.

Status: [`requirements_traceability.md`](requirements_traceability.md) §4.

## UX — the experience (CHANGE_PROPOSAL “Proposed experience changes”, PROMPT_MASTER §2–§3)

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| KIT-UX-01 | **Financial Pulse**: a compact summary of net worth, meaningful changes, liquidity and key signals; no large empty panels or repeated labels; details stay available | CHANGE_PROPOSAL §1 | documented |
| KIT-UX-02 | **Money Flow**: a Sankey of real aggregated cash flows when source, destination, period and amount exist; width = value; selecting a path opens the figures and their source; never infer flows from static allocations | CHANGE_PROPOSAL §2; PROMPT_FIG “Visual experiences” 2 | documented |
| KIT-UX-03 | **Wealth Map**: an allocation chart or treemap with values, percentages, timestamps and drill-down | CHANGE_PROPOSAL §3 | documented |
| KIT-UX-04 | **Financial Intelligence Graph**: news events, entities, assets, exposures, risks and goals connected only where grounded in data or business logic; filters, grouping, progressive disclosure, detail panels; no implied causation; no unreadable hairball | CHANGE_PROPOSAL §4; PROMPT_FIG “Graph model” | documented |
| KIT-UX-05 | **Intelligence Feed**: verified threshold breaches, notable portfolio changes, supported news impacts and goals needing attention, each saying why it is shown and linking to evidence | CHANGE_PROPOSAL §5 | documented |
| KIT-UX-06 | Motion only to show direction, magnitude, change or a selected relationship; respect reduced-motion; a static alternative | PROMPT_MASTER §3; PROMPT_FIG “Motion rules” | documented |
| KIT-UX-07 | Calm, restrained styling; strong hierarchy; progressive disclosure; keyboard-accessible, responsive charts | PROMPT_MASTER §2 | documented |

## COPILOT — the assistant (PROMPT_ONEWEALTH_COPILOT)

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| KIT-COPILOT-01 | A persistent, unobtrusive entry point opening a side panel without leaving the page; inherits page/entity context only when authorised | Experience | documented |
| KIT-COPILOT-02 | Capabilities: Ask (authorised data, timestamps, references), Investigate (relationships), Analyze (existing analyses, with assumptions), Act (only supported tasks through real tool/API contracts), Navigate (deep links), Continue (context within retention rules) | Capability categories | needs_clarification (Q-06: “authorised data” to an AI conflicts with BRD-BR-11 / NFR-08; resolved by [ADR-0012](../decisions/ADR-0012-the-copilot-routes-and-never-reads-client-data.md)) |
| KIT-COPILOT-03 | Typed tool contracts, validation, permission checks, confirmation for persistent changes, execution status, error handling, observability; read-only questions never mutate | Architecture and safety | documented |
| KIT-COPILOT-04 | Retrieved news and documents are untrusted content, not instructions; never expose secrets or data the user cannot access | Architecture and safety | documented |
| KIT-COPILOT-05 | Never fabricate sources, figures, capabilities or success; unsupported or failed tasks are reported truthfully | Architecture and safety | documented |
| KIT-COPILOT-06 | Tests cover authorisation, tool failures, confirmation, state changes and reporting | Acceptance | documented |

## DOC — documentation and acceptance rules (BRD_COVERAGE_AND_ACCEPTANCE, PROMPT_MASTER §5–§8)

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| KIT-DOC-01 | Every BRD requirement inventoried with a stable ID, source location, current path, target, UI entry, dependencies, acceptance test, evidence and status | BRD_COVERAGE “Required workflow” | documented |
| KIT-DOC-02 | Existing capabilities outside the BRD are inventoried and kept unless a documented decision changes them | idem 5 | documented |
| KIT-DOC-03 | Ambiguity, contradiction and missing decisions recorded; documented requirement kept apart from proposed interpretation | idem 6 | documented |
| KIT-DOC-04 | A visible component is not evidence; behaviour must be tested; final report lists tests actually run | “Completion criteria” | documented |
| KIT-DOC-05 | Traceability completeness reported separately from implementation completion; never claim 100 % implementation while anything is blocked, partial or unverified | “Completion criteria” | documented |
| KIT-DOC-06 | Regression scope: core journeys, data correctness, API contracts, authorisation, error/empty/loading states, responsive behaviour, graph interactions, assistant tool execution | “Regression scope” | documented |
