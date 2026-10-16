# OneWealth — Assistant, memory and agent ecosystem: backlog plan

**Status: in progress** (owner's go, 2026-10-16: “go, don't stop until you finished the assistant plan”). The brief
is kept verbatim in the [appendix](#appendix--the-owners-brief-2026-10-16) and as source
[`2026-10-16_assistant_memory_agents.md`](brd/sources/owner_requests/2026-10-16_assistant_memory_agents.md).
**A0 done** (2026-10-16): the target architecture is [`docs/brd/architecture/assistant.md`](brd/architecture/assistant.md);
the decisions below are recorded as ADR-0026…ADR-0034; the requirements are OWN-AS-01…25.

## 1. What exists today (first audit, 2026-10-16)

| Area | What is there | Gap against the brief |
|---|---|---|
| Assistant | **Copilot** (FEAT-32, `src/copilot/`): scrub → route → act → answer; 13 tools in a role-checked catalogue (`tools.py::TOOLS`), writes confirmed first, failures reported; keyword router, or `llm:copilot` that sees only the scrubbed question and the catalogue (ADR-0012); fixed-template answers with sources, `as_of`, focus marks, audit row per call | One tool per question; no multi-step tasks; answers only from templates; no questions about the app itself, no outside topics, no web search; the model may not read client data (BR-11, NFR-08, ADR-0012) |
| Conversations | Kept in the browser's `sessionStorage`, per role, per tab | Nothing on the server: no history, no resume, no search |
| Memory | None for users. OperonX agents (`operonx-agents` 0.2): `SQLiteSession`, `RedisSession`, `InMemorySession`, `ContextPolicy` with compaction, `StateStore` | Short-term memory exists in the library, unused here. There is no long-term or archive memory in the library or the app |
| Knowledge | Product docs in `docs/brd/` (markdown). `operonx-kb` (Operonx/packages): versioned documents, hybrid search (SQLite FTS5 or Postgres FTS + dense), per-document ACL, answers whose quotes are checked against the text | Not used by the app |
| Web search | — | No provider and no key in `.env` |
| Agents | CIO agent and challenger (FEAT-04/05, queued jobs, the AI zone), policy agent (FEAT-16), newsletter intro (FEAT-17); catalogue page (FEAT-15) with each agent's runs; trace drawers per run | No assistant-side agents; the catalogue is a table, not a map of how agents connect; no live state across the ecosystem |
| Storage | One SQLite file (`data/state.db`), `begin immediate` transactions, one server process, one Docker-free host. DATA-10 (G4) proves the move to PostgreSQL | Chat, at production volume, has not been measured on it |
| Evals | Agent eval set gates prompt and model changes (F4); golden sets for the CIO agent; `operonx-agents` evals | Nothing for the assistant beyond routing tests |

## 2. Decisions to settle in A0 (with the current proposal)

| # | Question | Proposal | Why |
|---|---|---|---|
| A-D1 | The assistant must answer about the user's own financial data; BR-11 / NFR-08 forbid client data reaching an AI provider | The assistant's model reads tool results **only where `client_ai` allows it** (built in G2): `demo` (the live demo, ADR-0018), `onprem` (the bank's own model). With `off` it keeps today's behaviour: the model routes and plans, and the answer is assembled from tool results by templates. ADR-0012 is amended, not dropped | One barrier for every model call; the bank's rule holds by configuration, not by trust |
| A-D2 | Where chat history and memory live | **Settled in A0 (ADR-0027), measured (assistant.md §8):** `data/assistant.db`, SQLite WAL, behind the `Session` / `StateStore` interfaces: ~127 turns/s on the demo host against ~10 at the BRD's busy hour; inside `state.db` the same load gave p99 2.6–8.4 s and lock errors. The library's connection-per-session use failed under load (fixed upstream in A3). PostgreSQL stays the bank path | The brief asks not to adopt SQLite blindly nor add a database without reason |
| A-D3 | Three memory layers | **Short-term**: the session (messages + active task state) with `ContextPolicy` compaction. **Long-term**: a few typed items per user (preference, goal, fact, constraint), each with its source message, time, confidence and expiry, written only by the consolidation step, shown and editable on a “Bộ nhớ” page, forgettable one by one or all. **Archive**: every message, searchable (full-text), with provenance; retention per policy. Generic parts (memory items, extraction, search) go upstream into `operonx-agents` | OperonX is upstream; the app keeps only OneWealth's rules |
| A-D4 | Knowledge base | `operonx-kb` with three separated collections: product (docs/brd, user guide; shared), user (materials a user uploads; ACL to that user and their RM), and none for the web (web results are cited, never stored) | Isolation by collection and ACL; citations checked against the text |
| A-D5 | Web search | **Settled in A0 (ADR-0030):** OpenRouter's `web` plugin on the existing key — measured 8 s, US$0.012, three cited sources; no new provider. The query is scrubbed; results cited, never stored; daily caps. Without the key the tool reports it is unavailable | No new vendor; reported as a limitation when missing, not faked |
| A-D6 | Which agents | Keep: CIO agent, challenger, policy agent, newsletter intro. Add only: **the assistant** (front door), **memory consolidator** (event-driven at the end of a session, token budget, deduplicated), **follow-up agent** (only for a follow-up the user asked for: “nhắc tôi khi…”, run by event or a scheduled job the request creates). Monitoring stays the existing alert jobs (no LLM) | The brief asks for a small family; most monitoring needs rules, not models |
| A-D7 | Tools | One registry: today's Copilot tools plus wrappers of the app's served graphs, each with roles, read/write, a confirmation rule for writes, a verifier (re-read after a write), a timeout and a cost class; discoverable by the model through descriptions. No raw access to internal services | Broad but controlled, as the brief asks |
| A-D8 | Ecosystem map | Built into the existing Agent page (FEAT-15) and the Copilot panel: overview (user → assistant → agents → tools → data), live states from `agent_runs`, `agent_jobs` and sessions, drill-down into the existing run traces. Drawn to the kit's visual language (docs/brd/assets) | No parallel monitoring page |
| A-D9 | Production readiness | An eval suite on real models (OpenRouter keys exist), realistic Vietnamese conversations, tracked metrics (accuracy, grounding, tool success, refusals, leakage, latency p50/p95, tokens and cost per conversation, background-agent cost per day), a gate the assistant must pass; external services without credentials isolated and reported | The brief forbids claiming readiness on mocks |

**Upstream is allowed (owner, 2026-10-16):** “you can update the kg and knowledge of operonx core”. Where a
need is generic — long-term and archive memory, memory tools, the knowledge base's collections and ACLs, tool
registries with verifiers — it is built in OperonX (core, `operonx-agents`, `operonx-kb`) with its own tests and
release, and OneWealth pins the new version; only OneWealth's rules stay in this repository.

## 3. Phases (after G9)

| Phase | What | Done when |
|---|---|---|
| A0 | Full audit; the architecture document `docs/brd/architecture/assistant.md`; ADRs for A-D1…A-D9; the storage measurement; BRD requirements for the assistant (new requirement rows, owner source = this brief) | Decisions recorded with evidence — **done** 2026-10-16 (assistant.md, ADR-0026…0034, OWN-AS-01…25, FEAT-37…39, `scripts/bench_chat_store.py`) |
| A1 | The tool registry: today's 13 tools moved in, served graphs wrapped, permissions, confirmations, verifiers, timeouts | Every tool tested for role refusal, confirmation and verification |
| A2 | The assistant: multi-step orchestration on `operonx-agents` (plan → call → verify → answer), grounding and citations, uncertainty, honest refusal of unsupported requests; the Copilot panel becomes its front end | Multi-step tasks pass the eval subset |
| A3 | Conversations on the server: sessions, resume across devices, short-term memory with compaction, task state | Long-conversation tests pass |
| A4 | Long-term and archive memory: extraction rules, the “Bộ nhớ” page (see, correct, forget), retention, isolation tests | Isolation and deletion tests pass |
| A5 | Knowledge base (product + user materials) and web search with citations | Grounding tests pass; web search measured or reported unavailable |
| A6 | Background agents: memory consolidator, follow-up agent; budgets, dedup, retries, traces | Costs per day measured |
| A7 | The Agent Ecosystem Map, with live states and drill-down; desktop and phone | States on the map match the traces in a test |
| A8 | The eval suite in full; the most consequential failures fixed; the readiness report with metrics, gaps, risks and costs | The gate passes, or the report says why not |

## 4. What the owner may be asked

- ~~A web-search provider key (A-D5)~~ — not needed: the existing OpenRouter key searches (ADR-0030).
- Whether the bank's assistant runs on an on-premise model (A-D1, `client_ai = onprem`), or answers from templates.

## Appendix — the owner's brief (2026-10-16)

> **OneWealth — Assistant, Memory & Agent Ecosystem Upgrade**
>
> The existing OneWealth system has already progressed significantly. This is a new enhancement phase, not a
> greenfield rewrite. Inspect the entire codebase, existing BRD under `docs/brd/`, current assistant implementation,
> CIO agents, data flows, and OperonX capabilities before making architectural decisions. Reuse what works, identify
> real gaps, and update the existing architecture rather than creating unnecessary parallel systems.
>
> **1. Make the Assistant the Primary User Entry Point.** The assistant will become the main conversational interface
> for accessing OneWealth features and supporting users in production. It must be able to: answer questions about the
> application, the user's authorized financial data, and relevant external topics; discover and invoke existing
> application features through real tools and APIs; execute supported user tasks, verify outcomes, and report failures
> honestly; answer questions outside OneWealth's direct scope using web search and reliable external knowledge when
> appropriate, with sources and clear uncertainty; gracefully handle unsupported requests instead of pretending
> capabilities exist. Design a clear tool registry and orchestration strategy. Give the assistant broad capabilities
> through controlled, discoverable tools—not unrestricted access to every internal service.
>
> **2. Conversation Storage, Knowledge Base & Layered Memory.** Inspect the existing persistence and memory
> infrastructure before choosing storage technologies. Evaluate whether SQLite is appropriate for chat history in the
> current deployment; consider concurrency, multi-user isolation, persistence, backups, and the expected production
> workload. Do not adopt SQLite blindly or introduce a new database without justification. Design three complementary
> memory layers: short-term memory (current conversation context, recent messages, and active task state); long-term
> memory (concise, durable user preferences, goals, relevant context, and learned facts extracted from conversations);
> archive memory (searchable raw conversation history, retaining appropriate provenance and timestamps). Provide tools
> to search, retrieve, update, summarize, and selectively forget memory. Use OperonX's existing memory management
> capabilities where suitable. Also evaluate a knowledge base / second brain for product documentation, user-provided
> materials, and other authorized knowledge. Keep user-specific memories logically isolated from shared product
> knowledge and external web content. Memory must be permission-aware, privacy-conscious, inspectable, and correctable.
> Do not save every conversation detail as permanent memory. Support retention policies, user control, deletion, and
> safeguards against cross-user data leakage.
>
> **3. Build a Small, Purposeful Family of Background Agents.** Inspect the existing CIO agents and other workflows
> before defining new agents. Design a coordinated agent ecosystem with clear responsibilities, shared context where
> appropriate, and explicit tool permissions. Automate only high-value activities that materially improve user
> experience—for example, essential monitoring, memory consolidation, or user-requested follow-ups where justified.
> Avoid spawning agents for every task or running expensive background loops. Prefer event-driven execution, scheduled
> jobs only when necessary, token budgets, deduplication, retries, observability, and clear ownership of each
> responsibility. Reuse OperonX for orchestration and memory management where it fits the existing architecture. Do not
> rebuild its capabilities unnecessarily.
>
> **4. Make the Agent Ecosystem Visually Understandable.** The existing CIO agents need a substantially better visual
> presentation aligned with the UI references already documented in `docs/brd/assets/` and the UX specifications.
> Create a clear, attractive Agent Ecosystem Map showing: the user and the main assistant; specialized agents,
> including existing CIO agents; their responsibilities and available tools; connections, handoffs, and relevant data
> flows; which agents are active, waiting, completed, or failed, based on real execution state; the overall main
> workflow from user request to execution and final response. Use an overview-first visualization with progressive
> disclosure, readable labels, meaningful grouping, and interactive drill-down into individual agent runs and traces.
> Avoid a cluttered graph or decorative connections that do not reflect actual architecture. Integrate this
> visualization into the existing UI rather than creating a disconnected monitoring page.
>
> **5. Test for Production Readiness.** The assistant is a critical entry point, so testing must go well beyond a few
> happy-path conversations. Inspect existing tests, then build a systematic evaluation suite covering: question
> answering, grounding, citations, and uncertainty; tool discovery, selection, execution, and result verification;
> multi-step tasks, failures, retries, timeouts, and recovery; in-scope and out-of-scope questions, including web
> research; memory extraction, retrieval, correction, isolation, and deletion; long conversations, context limits, and
> archived-history retrieval; authentication, authorization, prompt injection, data leakage, and unsafe tool
> execution; concurrent sessions, persistence, latency, token consumption, and background-agent costs; CIO agent
> visualization and consistency between displayed states and real execution traces. Use realistic test cases and
> available real integrations wherever possible. Do not rely on mock responses to claim production readiness. Where
> external services or credentials are unavailable, isolate those limitations and report them explicitly. Track
> measurable quality, reliability, latency, and cost indicators. Fix the most consequential issues before declaring
> the assistant production-ready.
>
> **Execution rules.** 1. Audit the current system and BRD before changing the architecture. 2. Document the target
> architecture, key decisions, and migration strategy. 3. Implement incrementally, preserving existing features and
> APIs where practical. 4. Update `docs/brd/` with the new requirements, memory model, agent responsibilities,
> workflows, UI references, and acceptance tests. 5. Run the available tests and report verified results, remaining
> gaps, risks, and cost implications. Do not rewrite working components merely for architectural elegance. Do not add
> agents, databases, memory layers, or dependencies without a clear purpose.
>
> **The goal is a reliable, cost-conscious, privacy-safe OneWealth assistant that serves as the primary interface to
> the product, supported by layered memory, a small family of useful agents, and a clear visualization of how the
> entire system works.**
