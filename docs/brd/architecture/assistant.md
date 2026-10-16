# The assistant, its memory and the agent ecosystem — target architecture

Owner request [OWN-AS-01…25](../requirements/owner_requirements.md#as--assistant-memory-and-agent-ecosystem-2026-10-16-backlog-b-08)
(source [`2026-10-16_assistant_memory_agents.md`](../sources/owner_requests/2026-10-16_assistant_memory_agents.md));
build plan [`docs/ASSISTANT_PLAN.md`](../../ASSISTANT_PLAN.md) phases A1–A8; decisions ADR-0026…ADR-0034. Written in
A0 (2026-10-16) from the audit in §1 and the measurements in §8. Sections marked *(target)* describe what A1–A8 build;
the rest is what exists.

## 1. What exists (audit, 2026-10-16)

| Area | Today | Kept / changed |
|---|---|---|
| Copilot (FEAT-32, `src/copilot/`) | `POST /api/copilot` → `copilot_flow`: check → scrub (`scrub.py`, names/numbers/codes out) → route (keyword rules, or `llm:copilot` seeing only the scrubbed question, the page path and the catalogue, ADR-0012) → **one** tool → answer from a fixed template; writes return `pending` + `confirm` and run on the second call; every call audited (`copilot.ask`); cards, `as_of`, sources, `focus` marks (FEAT-33) | Kept as the template path and the fallback; its 13 tools move into the registry (A1); the panel (`web/copilot.js`) becomes the assistant's front end (A2) |
| Conversation | `sessionStorage` per role and tab, in the browser | Moves to the server (A3) |
| Client-data barrier | `control/barrier.py` guards every `llm:` call (G2); `client_ai` = `demo` / `onprem` / `off` (live: `demo`, ADR-0018/0023) | The assistant goes through it unchanged (ADR-0026) |
| Agents | CIO agent + challenger (FEAT-04/05; queued `agent_jobs`, `agent_runs`, the AI zone ADR-0022), policy agent (FEAT-16), newsletter intro (FEAT-17), market and news jobs, alert jobs (FEAT-36, no LLM). Catalogue page (FEAT-15) with each agent's runs and trace drawers | All kept; two agents added (ADR-0031); the catalogue becomes the ecosystem map (ADR-0033) |
| Storage | `data/state.db`, SQLite in rollback-journal mode, `begin immediate` per write, one server process; client columns sealed (G3); PostgreSQL proven by export (G4, ADR-0025) | Chat in its own WAL file (ADR-0027, §8) |
| OperonX | operonx 1.30; `operonx-agents` 0.2 (in use by the CIO agent): `Agent` + `Runner` tool loop, tools with `approval` (a call parks as an `Interruption`, resumed with `Approve`/`Deny`), `ToolPolicy`, hooks, `UsageLimits` (turns, tool calls, tokens, cost, wall), `SQLiteSession` + `SQLiteStateStore`, `ContextPolicy` compaction, redaction, evals. `operonx-kb` 0.2.5 (PyPI): versioned documents, FTS5 lexical search, per-document ACL, answers with checked quotes | Used as they are; what is missing and generic is added upstream (§9) |
| Models | OpenRouter (`.env`): Haiku 5.5 for the client steps and the router, Sonnet 5.5 the CIO agent, Gemini 3.8 Flash the challenger | The assistant thinks with `llm:copilot` (Haiku 5.5) |

Gaps the brief names, confirmed by the audit: one tool per question; no multi-step task; answers only from
templates; nothing about the app itself or outside topics; no server-side history; no long-term or archive memory; no
knowledge base in the app; no web search; agent catalogue is a table, not a map; no assistant evals beyond routing.

## 2. The shape *(target)*

```
 person ─▶ panel (web/copilot.js) ─▶ POST /api/assistant {conversation, message | approvals}
                                        │
                                        ▼
                 assistant_flow: check ─▶ turn (operonx-agents Runner, one op) ─▶ answer
                                        │            │  model: llm:copilot, through the barrier (ADR-0026)
                                        │            │  tools: the registry, filtered by role (ADR-0032)
                                        │            │  session: assistant.db (ADR-0027) · state: parked approvals
                                        │            ▼
           ┌──────────────── tools ─────┴─────────────────────────────────────────────┐
           │ app reads (dashboard, flows, feed, goals, impact, investigate, scenario…) │
           │ app writes, confirmed + verified (review, propose, contact log, fetch…)   │
           │ help (operonx-kb “product”) · materials (operonx-kb “materials”, ACL)     │
           │ memory (search / recall / remember / forget) · web_search · follow_up     │
           └───────────────────────────────────────────────────────────────────────────┘
        events ─▶ memory consolidator (conversation idle) · follow-up checks (market job)
        ecosystem map (Agent page + panel) ◀─ agent_runs, agent_jobs, conversations, follow-ups, traces
```

One front door: the assistant. It never reaches a service except through a registered tool, and every tool runs the
same graph or read the page uses, so the server's role, family and separation-of-duty checks apply unchanged.

## 3. The turn *(target, A2)*

1. **Check** the person (signed-in user or demo role), the conversation (theirs), the message (≤ 2,000 characters).
2. **Turn**: `Runner.run(assistant, message, session=…, store=…, limits=…)` inside one op, so each model call and
   tool call is a child execution in the run's trace. Limits per turn: 8 model calls, 12 tool calls, 60,000 tokens,
   US$0.05, 60 s wall (ADR-0034 measures them). Instructions: Vietnamese; answer from tool results only; cite the
   tool, page or source; say how sure; decline what no tool supports and list what it can do.
3. **Writes park.** A write tool has `approval="always"`: the run ends `interrupted`; the panel shows the plan
   (the tool's own summary, as today's `PLANS`) and the person confirms or declines; `POST /api/assistant` with the
   approvals resumes the same run (`Runner.resume`). Declined or expired (10 min), nothing runs.
4. **Verify.** Every write tool has a verifier that reads the state back (the review item's status, the new contact
   row…). The tool's message says “done and checked” or “sent but not confirmed: …”; never success on a failure.
5. **Answer**: the text, the citations (tool → page route, KB passage, web URL), `as_of`, cards and `focus` marks
   from the tools, the run's usage and cost. Audited as `assistant.turn` (who, conversation, tools, statuses, model,
   tokens), the content itself not in the audit row.

With `client_ai = off` the same loop runs in **template mode** (ADR-0026): the model sees the scrubbed message and
tool *statuses* (never their data), chains tools, and the answer is the tools' own templated texts in order —
today's Copilot quality, multi-step.

## 4. Tools *(target, A1)* — ADR-0032

`src/assistant/registry.py`: one `Tool` record per capability, turned into `operonx_agents` tools per request:

| Field | Meaning |
|---|---|
| `name`, `description` | What the model reads to choose; Vietnamese, no data |
| `roles` | Who may see and call it; the registry given to a turn is filtered by role (an unseen tool cannot be called) |
| `kind` | `read` / `write` / `external` (web) / `memory` |
| `args` | A pydantic model: enumerations and ids the server resolves, never free SQL or URLs |
| `run` | The served graph or read the page uses (the Copilot's `_graph` helper), with the person's context |
| `plan` | For writes: the one-line summary the person confirms |
| `verify` | For writes: re-read after the call; failing verification is reported |
| `timeout`, `cost` | Seconds; `free` / `llm` / `paid` (web search, the CIO agent) — paid tools count against a daily cap |

Families: today's 13 Copilot tools; app reads (dashboard, flows, feed, goals, alerts, impact, investigate,
scenario, overview, search, RM today, advisory track record, measurement); app writes (approve/reject a review,
specialist decision, client proposal, RM recommendation, RM contact log, CIO news fetch, policy note, configuration
proposal — each only for its roles); `help` (product KB); `materials` (user KB); memory tools; `web_search`;
`follow_up` (create, list, cancel); `navigate`. No tool takes a raw path, query or URL.

## 5. Conversations and memory *(target, A3–A4)* — ADR-0027, ADR-0028

**Store.** `data/assistant.db`, SQLite in WAL mode, separate from `state.db` (§8). Tables: the `operonx-agents`
session items (`operonx_agents_items`) and state store, plus OneWealth's own: `conversations` (id, owner, role,
title, created, updated, status), `memory_items`, `follow_ups`. Sealed like the rest when `MF_DATA_KEYS` is set
(message content and memory text). Backed up hourly with SQLite's online backup; included in the PostgreSQL export.

| Layer | What | Written by | Read by | Kept |
|---|---|---|---|---|
| Short-term | the conversation's items + the active task (parked approvals, the run state) | each turn, at its end (`Runner` commits a whole turn) | the next turn; `ContextPolicy(window=…)` compacts older exchanges into a summary item, never drops silently | while the conversation lives |
| Long-term | typed items: `preference`, `goal`, `fact`, `constraint`; text ≤ 200 chars, source (conversation, item seq), created, confidence, expires, status | the **consolidator** after a conversation goes idle (A6), or the person saying “hãy nhớ…” (tool `remember`, confidence 1) | `recall` tool (the turn's instructions list the active items' texts, ≤ 15) | until expiry (fact 180 days, preference/goal/constraint none) or forgotten |
| Archive | every message, with conversation, seq, time, author | the session itself (no copy) | `search_history` tool; the Bộ nhớ page | Compliance's retention (`assistant_retention`, default 365 days), then deleted |

Rules: a memory item never holds an amount, an account or a third person's data beyond the family's own names; the
consolidator keeps at most 5 new items per conversation and merges duplicates; every item shows its source message;
forgetting deletes the row (and, asked, the conversation). Isolation: every read and write is keyed by the owner the
server resolved; no tool takes an owner argument.

**Bộ nhớ page** (client and staff): long-term items with source and expiry — correct, forget one, forget all;
conversations — open, search, delete.

## 6. Knowledge *(target, A5)* — ADR-0029, ADR-0030

`operonx-kb` with its catalog in `data/kb.db` (lexical FTS5; no embedding service is configured, so `hybrid` is not
available — measured in A5 on the product questions):

| Collection | Holds | ACL | Answering |
|---|---|---|---|
| `product` | A Vietnamese user guide per page and role (written in A5 from the screen specs), the glossary, the “Cách tính” catalogue (`src/explain/catalogue.py`) | every signed-in role | `help` tool → passages with quotes checked against the text |
| `materials` | Documents a person uploads in the panel (PDF/DOCX/MD) | the owner and, for a client, their assigned RM | `materials` tool; deleted with the owner's data |
| — (web) | Never stored | — | `web_search` results are cited and dropped |

**Web search** (ADR-0030): OpenRouter's `web` plugin on the existing key (measured 2026-10-16: 8 s, US$0.012, three
cited Vietnamese sources for a policy-rate question). The query sent is the person's question scrubbed as for the
router (no names, numbers, codes); results are cited by URL with “theo các nguồn tìm được” and a certainty line; daily
cap per person (20) and in total (500).

## 7. Agents *(target, A6–A7)* — ADR-0031, ADR-0033

| Agent | Responsibility | Trigger | Tools | Budget |
|---|---|---|---|---|
| **Assistant** (new front door) | Answer and act for the person | each message | the registry, by role | per turn (§3) |
| **Memory consolidator** (new) | Distil a finished conversation into ≤ 5 long-term items; dedupe; expire | event: conversation idle 15 min (checked by a job every 5 min over `conversations.updated`), once per new content (hash) | read the conversation, read/write the owner's items | ≤ 8,000 tokens per conversation; queued with retries (2) |
| **Follow-up** (new, mostly rules) | Watch a condition the person asked for (“nhắc tôi khi VN-Index dưới 1.200”, “khi có tin về lãi suất”) and notify once | created by the assistant's `follow_up` tool; checked by the existing market and news jobs — **no model call per check** | read market series, read approved events | 0 tokens per check |
| CIO agent, challenger | Draft and challenge views (FEAT-04/05) | queued jobs | unchanged | unchanged |
| Policy agent, newsletter intro | FEAT-16/17 | on demand | unchanged | unchanged |
| Alerts (no model) | Health of jobs, chains, feeds (FEAT-36) | scheduled | — | — |

Shared context: agents share data only through the stores they already read (runs, events, conversations); no agent
reads another's prompt. The **ecosystem map** (Agent page, and a link from the panel): person → assistant → tools and
agents → data, grouped (front door · background · CIO desk · rules), each node's state from real records
(`agent_runs`, `agent_jobs`, conversation runs, consolidator and follow-up rows) — active / waiting / done / failed —
and a click opens that run's trace drawer.

## 8. Storage measurement (A0, 2026-10-16) — ADR-0027

`scripts/bench_chat_store.py` on the demo host (24 cores, SQLite 3.50.4), with `operonx-agents`' own `SQLiteSession`
(WAL, synchronous=FULL), each turn reading the last 40 items and appending a turn (question, tool call, tool result,
answer: ~2 KB), all conversations at once with no pause between turns:

| Store | Conversations | Turns/s | Storage per turn p50 / p95 / p99 | Errors |
|---|---|---|---|---|
| Separate WAL file, one shared connection | 10 | 124 | 80 / 93 / 98 ms | 0 |
| | 100 | 130 | 753 / 989 / 1,179 ms | 0 |
| | 500 | 127 | 3,912 / 4,280 / 4,541 ms | 0 |
| Separate WAL file, a connection per session (the library's documented use) | 50 × 20 turns | — | p95 1,393 ms | 4 “database is locked” |
| The app's state file (rollback journal, a connection per write, a business writer beside) | 10 | 52 | 19 / 549 / 2,550 ms | 0 |
| | 100 | 71 | 99 / 5,759 / 8,363 ms | “database is locked” |
| Archive: FTS5 over 40,000 messages, one person's | — | — | search p95 70 ms (index built in 1.5 s) | — |

Reading: the WAL file saturates at ~127 turns/s on this host (two fully synced transactions per turn); latencies at
100 and 500 are queueing in a test with no think time. The BRD's scale (6,500 families) at a busy hour — 5 % of
~9,000 people chatting a turn a minute plus ~100 staff — is ~10 turns/s, 8 % of that. Inside `state.db` the same load
gives multi-second tails and lock errors, and would slow the business writes: rejected. The connection-per-session
failure is fixed upstream (§9) before A3 uses it. PostgreSQL stays the bank path (the session and memory stores sit
behind interfaces; `RedisSession` exists); a new database for the demo is not justified by these numbers.

## 9. Upstream into OperonX *(target)*

| Need | Where | Phase |
|---|---|---|
| Sessions and stores on one SQLite file share one connection (the lock errors in §8); reads without a write lock | `operonx-agents` `_storage.py` | A3 |
| Long-term memory items (typed, sourced, expiring) with a store protocol and SQLite store; archive search over a session store; memory tools (search, recall, remember, forget) | `operonx-agents` `memory/` | A4 |
| Tool verifiers: a check run after a tool, its verdict in the tool message and the trace | `operonx-agents` tools | A1 |
| Anything the KB needs for per-owner collections (if A5 finds a gap) | `operonx-kb` | A5 |

OneWealth keeps only its rules: which tools, which roles, the barrier, what a memory item may hold, retention values.

## 10. Migration *(target)*

1. A1: the registry beside the Copilot; `copilot_flow` reads its tools from it (no behaviour change; its tests pass).
2. A2: `POST /api/assistant` and the agent; the panel switches to it; `POST /api/copilot` kept (the template path,
   and the fallback when the model is unavailable — NFR-03: an AI failure must not stop the product).
3. A3: conversations move from `sessionStorage` to the server; the panel lists them; the old storage is read once and
   dropped.
4. A4–A7 add memory, knowledge, agents and the map without changing earlier contracts.
5. A8: the eval gate decides readiness; the report states what passed, what failed and what it costs.

## 11. Costs *(to be measured in A8)*

Inputs known now: Haiku 5.5 through OpenRouter; a web search ~US$0.012; the consolidator ≤ 8,000 tokens per
conversation; follow-up checks 0 tokens. A8 measures tokens and cost per conversation and per day from the runs'
usage records (`operonx-agents` `Usage` carries the provider's own counts and cost).
