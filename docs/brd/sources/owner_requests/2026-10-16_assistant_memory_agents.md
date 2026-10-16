# OneWealth — Assistant, Memory & Agent Ecosystem Upgrade

The existing OneWealth system has already progressed significantly. This is a new enhancement phase, not a
greenfield rewrite. Inspect the entire codebase, existing BRD under `docs/brd/`, current assistant implementation,
CIO agents, data flows, and OperonX capabilities before making architectural decisions. Reuse what works, identify
real gaps, and update the existing architecture rather than creating unnecessary parallel systems.

**1. Make the Assistant the Primary User Entry Point.** The assistant will become the main conversational interface
for accessing OneWealth features and supporting users in production. It must be able to: answer questions about the
application, the user's authorized financial data, and relevant external topics; discover and invoke existing
application features through real tools and APIs; execute supported user tasks, verify outcomes, and report failures
honestly; answer questions outside OneWealth's direct scope using web search and reliable external knowledge when
appropriate, with sources and clear uncertainty; gracefully handle unsupported requests instead of pretending
capabilities exist. Design a clear tool registry and orchestration strategy. Give the assistant broad capabilities
through controlled, discoverable tools—not unrestricted access to every internal service.

**2. Conversation Storage, Knowledge Base & Layered Memory.** Inspect the existing persistence and memory
infrastructure before choosing storage technologies. Evaluate whether SQLite is appropriate for chat history in the
current deployment; consider concurrency, multi-user isolation, persistence, backups, and the expected production
workload. Do not adopt SQLite blindly or introduce a new database without justification. Design three complementary
memory layers: short-term memory (current conversation context, recent messages, and active task state); long-term
memory (concise, durable user preferences, goals, relevant context, and learned facts extracted from conversations);
archive memory (searchable raw conversation history, retaining appropriate provenance and timestamps). Provide tools
to search, retrieve, update, summarize, and selectively forget memory. Use OperonX's existing memory management
capabilities where suitable. Also evaluate a knowledge base / second brain for product documentation, user-provided
materials, and other authorized knowledge. Keep user-specific memories logically isolated from shared product
knowledge and external web content. Memory must be permission-aware, privacy-conscious, inspectable, and correctable.
Do not save every conversation detail as permanent memory. Support retention policies, user control, deletion, and
safeguards against cross-user data leakage.

**3. Build a Small, Purposeful Family of Background Agents.** Inspect the existing CIO agents and other workflows
before defining new agents. Design a coordinated agent ecosystem with clear responsibilities, shared context where
appropriate, and explicit tool permissions. Automate only high-value activities that materially improve user
experience—for example, essential monitoring, memory consolidation, or user-requested follow-ups where justified.
Avoid spawning agents for every task or running expensive background loops. Prefer event-driven execution, scheduled
jobs only when necessary, token budgets, deduplication, retries, observability, and clear ownership of each
responsibility. Reuse OperonX for orchestration and memory management where it fits the existing architecture. Do not
rebuild its capabilities unnecessarily.

**4. Make the Agent Ecosystem Visually Understandable.** The existing CIO agents need a substantially better visual
presentation aligned with the UI references already documented in `docs/brd/assets/` and the UX specifications.
Create a clear, attractive Agent Ecosystem Map showing: the user and the main assistant; specialized agents,
including existing CIO agents; their responsibilities and available tools; connections, handoffs, and relevant data
flows; which agents are active, waiting, completed, or failed, based on real execution state; the overall main
workflow from user request to execution and final response. Use an overview-first visualization with progressive
disclosure, readable labels, meaningful grouping, and interactive drill-down into individual agent runs and traces.
Avoid a cluttered graph or decorative connections that do not reflect actual architecture. Integrate this
visualization into the existing UI rather than creating a disconnected monitoring page.

**5. Test for Production Readiness.** The assistant is a critical entry point, so testing must go well beyond a few
happy-path conversations. Inspect existing tests, then build a systematic evaluation suite covering: question
answering, grounding, citations, and uncertainty; tool discovery, selection, execution, and result verification;
multi-step tasks, failures, retries, timeouts, and recovery; in-scope and out-of-scope questions, including web
research; memory extraction, retrieval, correction, isolation, and deletion; long conversations, context limits, and
archived-history retrieval; authentication, authorization, prompt injection, data leakage, and unsafe tool
execution; concurrent sessions, persistence, latency, token consumption, and background-agent costs; CIO agent
visualization and consistency between displayed states and real execution traces. Use realistic test cases and
available real integrations wherever possible. Do not rely on mock responses to claim production readiness. Where
external services or credentials are unavailable, isolate those limitations and report them explicitly. Track
measurable quality, reliability, latency, and cost indicators. Fix the most consequential issues before declaring
the assistant production-ready.

**Execution rules.** 1. Audit the current system and BRD before changing the architecture. 2. Document the target
architecture, key decisions, and migration strategy. 3. Implement incrementally, preserving existing features and
APIs where practical. 4. Update `docs/brd/` with the new requirements, memory model, agent responsibilities,
workflows, UI references, and acceptance tests. 5. Run the available tests and report verified results, remaining
gaps, risks, and cost implications. Do not rewrite working components merely for architectural elegance. Do not add
agents, databases, memory layers, or dependencies without a clear purpose.

**The goal is a reliable, cost-conscious, privacy-safe OneWealth assistant that serves as the primary interface to
the product, supported by layered memory, a small family of useful agents, and a clear visualization of how the
entire system works.**
