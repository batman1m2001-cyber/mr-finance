# Requests of the product owner — `OWN-<area>-nn` (approved extensions)

Layer A, fourth source: requests the product owner gives directly, kept verbatim in
[`../sources/owner_requests/`](../sources/owner_requests/) (SRC-05). They are **not in the BRD**; the owner asked for
them, so they are approved for building. Each request is split into testable requirements below, in the owner's
words where possible.

Status: [`requirements_traceability.md`](requirements_traceability.md) §5.

## AS — Assistant, memory and agent ecosystem (2026-10-16, backlog B-08)

Source: [`2026-10-16_assistant_memory_agents.md`](../sources/owner_requests/2026-10-16_assistant_memory_agents.md);
plan [`docs/ASSISTANT_PLAN.md`](../../ASSISTANT_PLAN.md); architecture [`assistant.md`](../architecture/assistant.md);
decisions ADR-0026…ADR-0034.

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-AS-01 | The assistant is the main conversational entry point: the Copilot panel becomes its front end, on every page and role | §1 first paragraph | documented |
| OWN-AS-02 | It answers about the application itself (what a page shows, how a number is computed, how to do a task) from the product's own documentation, with the page or document cited | §1 “answer questions about the application” | documented |
| OWN-AS-03 | It answers about the user's **authorized** financial data only: every read goes through the same role, family and separation-of-duty checks as the pages | §1 “the user's authorized financial data” | documented |
| OWN-AS-04 | It discovers and calls application features through one registry of tools, each with roles, read/write, a confirmation rule for writes, a timeout and a cost class; no unrestricted access to internal services | §1 “discover and invoke… controlled, discoverable tools” | documented |
| OWN-AS-05 | It runs multi-step tasks (several tool calls in order), verifies a write by reading the state back, and reports a failure as a failure | §1 “execute supported user tasks, verify outcomes, and report failures honestly” | documented |
| OWN-AS-06 | A write never runs without the user's confirmation in the panel; a refused or expired confirmation runs nothing | §1 “controlled”; Copilot ADR-0012 kept | documented |
| OWN-AS-07 | Questions outside OneWealth are answered with web search and reliable external knowledge, with sources and a stated level of certainty; without a provider, the assistant says web search is unavailable | §1 “outside OneWealth's direct scope” | documented |
| OWN-AS-08 | An unsupported request is declined plainly, saying what it can do instead; it never pretends a capability exists | §1 “gracefully handle unsupported requests” | documented |
| OWN-AS-09 | The client-data barrier holds for the assistant: a model reads client data only where Admin's `client_ai` allows it (demo, on-premise); otherwise the model plans and the answer is assembled from tool results | §2 “privacy-conscious”; BRD-BR-11, NFR-08 | documented |
| OWN-AS-10 | Conversations are kept on the server per user: listed, resumed on another device, searchable; the store chosen by a measurement of the deployment's workload | §2 first paragraph | documented |
| OWN-AS-11 | Short-term memory: the current conversation, its recent messages and the active task's state, compacted when it grows past the context budget, never silently dropped | §2 “short-term memory” | documented |
| OWN-AS-12 | Long-term memory: a few concise items per user (preferences, goals, facts, constraints), each with its source message, time and confidence; not every detail is kept | §2 “long-term memory”; “Do not save every conversation detail” | documented |
| OWN-AS-13 | Archive memory: every message searchable with its conversation, time and author | §2 “archive memory” | documented |
| OWN-AS-14 | Tools to search, retrieve, update, summarise and forget memory, for the assistant and on a page the user sees (“Bộ nhớ”): see, correct, forget one item or all | §2 “Provide tools…”; “inspectable, and correctable” | documented |
| OWN-AS-15 | Retention policies for the archive and the long-term items, set by Compliance; deletion is real | §2 “retention policies, user control, deletion” | documented |
| OWN-AS-16 | Isolation: a user's memories and materials are never read for another user; shared product knowledge, user material and web content are kept apart | §2 “logically isolated”; “safeguards against cross-user data leakage” | documented |
| OWN-AS-17 | A knowledge base for product documentation and the materials a user provides, with answers that cite the passage | §2 “knowledge base / second brain” | documented |
| OWN-AS-18 | A small family of background agents, each with one responsibility and its own tools: memory consolidation and user-requested follow-ups added to the existing CIO agent, challenger, policy agent and newsletter step | §3 | documented |
| OWN-AS-19 | Background work is event-driven where it can be, scheduled only where needed, with token budgets, deduplication, retries, traces and a measured cost per day | §3 “Prefer event-driven execution…” | documented |
| OWN-AS-20 | An Agent Ecosystem Map in the existing UI: the user, the assistant, the agents with their responsibilities and tools, the connections and data flows that exist, overview first with drill-down into runs and traces | §4 | documented |
| OWN-AS-21 | The map shows each agent active, waiting, completed or failed from real execution state, and the states match the traces | §4 “based on real execution state”; §5 last bullet | documented |
| OWN-AS-22 | The map follows the kit's visual language, readable on desktop and phone, with no decorative connections | §4 “aligned with the UI references”; “Avoid a cluttered graph” | documented |
| OWN-AS-23 | A systematic evaluation suite on real models and realistic Vietnamese conversations: answers, grounding, citations, uncertainty, tools, multi-step tasks, failures, out-of-scope, memory, long conversations, security (authorisation, prompt injection, leakage, unsafe tools), concurrency, latency, tokens and cost | §5 | documented |
| OWN-AS-24 | Production readiness is declared only against measured quality, reliability, latency and cost indicators and a gate; missing credentials or services are reported as limitations | §5 “Do not rely on mock responses…” | documented |
| OWN-AS-25 | Built incrementally on what exists (Copilot, CIO agents, OperonX), working features and APIs kept; `docs/brd/` updated with requirements, memory model, agent responsibilities, workflows, UI references and acceptance tests | Execution rules 1–5 | documented |

## MOTION — Living Interface & Smart Animations (2026-10-16, backlog B-01)

Source: [`2026-10-16_living_interface.md`](../sources/owner_requests/2026-10-16_living_interface.md).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-MOTION-01 | **Idle presence**: subtle ambient motion around the assistant, to create a sense of presence | §1 “Idle” | documented |
| OWN-MOTION-02 | **Thinking**: gentle pulses or flowing highlights while the assistant is processing a request or executing tools | §1 “Thinking” | documented |
| OWN-MOTION-03 | **Responding**: briefly highlight the charts, assets, news or graph connections the assistant references, so the page feels connected to the assistant | §1 “Responding”, second paragraph | documented |
| OWN-MOTION-04 | **Completed / error**: clear, elegant visual feedback | §1 “Completed / Error” | documented |
| OWN-MOTION-05 | Premium, minimal, calm; no excessive glow, distracting movement, heavy 3D or whole-page animation; motion communicates a meaningful state change, never decoration | §1 last paragraph | documented |
| OWN-MOTION-06 | Performance: CSS transitions, transforms, opacity and simple SVG; no heavy animation library, no continuous JS loop, no needless re-render or layout; driven by real assistant and app events, never fabricated progress; suspended when the tab is hidden or the interface inactive; `prefers-reduced-motion` respected; usable on low-end devices; measured before and after | §2 | documented |
| OWN-MOTION-07 | Incremental: no redesign, business logic unchanged, every documented feature preserved; feature specs, UX docs, design system, traceability and changelog updated | §3 | documented |

## UI — redesign to the kit (2026-10-16, backlog B-00)

Source: [`2026-10-16_ui_redesign.md`](../sources/owner_requests/2026-10-16_ui_redesign.md); the gaps it names are
G1–G9 of [`docs/UI_REDESIGN_PLAN.md`](../../UI_REDESIGN_PLAN.md).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-UI-01 | Every page wears the kit's concept-board look (R-D1): light first, dark kept | request; plan G1, G2 | documented |
| OWN-UI-02 | The pages that predate the BRD are rebuilt in the new design with every block and action kept | plan G1, G7 | documented |
| OWN-UI-03 | Header search over what the role may open, and a notifications bell, as on the board | plan G2, R-D5 | documented |
| OWN-UI-04 | Graph overview with data sources, risks and goals, expand/collapse, node → page; an event timeline; the CIO's whole-run graph | plan G3, G5 | documented |
| OWN-UI-05 | Copilot answers with as-of time and sources, structured cards, investigate and stress-scenario tools, audited calls | plan G6 | documented |
| OWN-UI-06 | The live demo runs the real models (owner D-03) and shows real runs from fetched news | plan G8 | documented |
| OWN-UI-07 | Browser tests in the suite for every route and the main interactions | plan G9 | documented |
