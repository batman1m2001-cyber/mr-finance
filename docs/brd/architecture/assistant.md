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

## 3. The turn *(built in A2, 2026-10-17)*

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

**As built (A2):** `src/assistant/{turn,ops,graph}.py`, service `assistant` (`POST /api/assistant`).
- Request and answer:
  - The request carries `{message}`, or `{turn_id, approvals: {id: approve|deny}}`. `run_id` is a name operonx's
    HTTP door reads itself.
  - The answer carries `mode` (`model` / `template` / `fallback`), `steps` (each tool: label, status, text, card,
    page), `waits` (the writes and their one-line plans), `citations`, `sources`, `as_of` and `usage`.
- Without a model (AI off, or `LLM_MODEL_COPILOT` unset), or when the model fails before any tool ran, the turn takes
  the Copilot's keyword path (`fallback`, NFR-03). Its confirm still goes to `POST /api/copilot`.
- A parked write is answered only by the person who asked, in the same role, once, within 10 minutes. The table
  `parked` in `assistant.db` holds who, and the call ids. operonx-agents' `SQLiteStateStore` in the same file holds
  the run.
- Limits are 8 model calls, 12 tool calls, 60,000 tokens and 60 s. The US$ cap waits for declared prices (A8).
- The instructions say to call a write directly and let the panel ask. The first real-model eval found the model
  asking in prose instead (docs/brd/testing/assistant_eval.md).
- The real-model eval subset passed 10/10, twice: p50 ≈ 5.4 s, ~6,000 tokens a turn.

## 4. Tools *(built in A1, 2026-10-17)* — ADR-0032

`src/assistant/registry.py`: one `Tool` record per capability (`src/assistant/base.py`), turned into `operonx_agents`
tools per role (`agent_tools(role)`, the person in `RunContext.deps`):

| Field | Meaning |
|---|---|
| `name`, `description` | What the model reads to choose; Vietnamese, no data |
| `roles` | Who may see and call it; the registry given to a turn is filtered by role (an unseen tool cannot be called) |
| `kind` | `read` / `write` / `external` (web) / `memory` |
| `args`, `params` | Enumerations the model picks from, and typed free arguments (a title, a note, an id a read tool listed); operonx-agents validates them from the generated signature. Never a path, a query language or a URL |
| `run` | The served graph or read the page uses (the Copilot's `_graph` helper), with the person's context |
| `plan` | For writes: the one-line summary the person confirms, and the arguments resolved on the server (which pending item, which family); it writes nothing |
| `verify` | For writes: reads the state back after the call (`True`, or what is not there); operonx-agents 0.2.3 `@tool(verify=)` turns anything else into an error the model reads — “ran, but its effect could not be confirmed” — and the Copilot into a failed answer |
| `timeout`, `cost` | Seconds; `free` / `llm` / `paid` (web search, the CIO agent) — paid tools count against a daily cap |

Built in A1 (25 tools): the Copilot's 13 (`src/assistant/tools.py`: tong_quan, dong_tien, chu_y, muc_tieu,
tac_dong, dieu_tra, kich_ban, hom_nay, hop_tin, tin_bi_giu, mo_trang; writes duyet_de_xuat, lay_tin) and the served
graphs wrapped (`src/assistant/actions.py`) — reads `dong_luc` (alerts_flow: policies, macro, projects in VND),
`tim_kiem` (search_flow), `de_xuat` (the review queue; the specialist's waiting items), `su_kien` (events),
`canh_bao_he_thong` (the bell's alerts), `lien_he` (the RM's contacts); writes `gui_de_xuat` (propose_flow, client
and RM), `ghi_lien_he` (contact_flow), `khuyen_nghi` (recommend_flow), `chuyen_gia_duyet` (specialist_flow),
`danh_dau_khan` (event_urgent_flow), `da_xem_canh_bao` (alert_ack_flow). The dashboard, flows, feed, goals, impact,
investigate, scenario and RM-today reads are the Copilot's tools.

Left to their pages, deliberately: the four-eyes governance decisions (configuration versions, CIO views and runs,
newsletters, policy documents, research release, the market model), grouping news into events, releasing held news,
the client's own uploads and risk test, the advisory track record (mock data) and the measurement reports (tables,
not sentences). Each needs the person to read evidence there; the assistant opens the page (`mo_trang`).

Role desks (FEAT-41, OWN-MR-10; `src/assistant/desktools.py`, M1 2026-10-18): each staff role's own reads over
the composition its desk draws (`src/desk/reads.py`), so the assistant says the screen's numbers — CIO:
`ban_quyet_dinh` (what waits, the flow), `phoi_nhiem` (the newest effective run by factor, worst families),
`lan_ap_dung` (runs by status), `do_chinh_xac` (history coverage, VN-Index direction, forecasts waiting). They are in
the map's `tools_app` family; `stream.NODES` maps each to the desk's `data-node` it lights.

To come: `help` (product KB) and `materials` (user KB) in A5; memory tools in A4; `web_search` in A5;
`follow_up` (create, list, cancel) in A6.

With the barrier off (`ctx.reads` false) the model reads only a tool's status and page, never its text or data
(`registry.Seen`); the answer is then the tools' own templated texts (ADR-0026).

## 5. Conversations and memory *(built in A3–A4, 2026-10-17)* — ADR-0027, ADR-0028

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

### As built (A3, 2026-10-17)

- **A conversation** is created by the first message (titled from it, 80 characters) and named by
  `conversation_id` on every later turn; `POST /api/assistant/conversations` lists (newest first), opens (the turns
  as the panel showed them, and any write still waiting) and deletes one. Owner and role are the server's
  (`conversations.owner`): another person's id answers “Không có cuộc trò chuyện này”, never its content.
- **Two records of a turn.** `turns` keeps what the panel showed (the question, the answer with its steps, cards
  and citations) so another device draws the same thing; `operonx_agents_items` keeps what the model was sent and
  said. They differ in template mode, where the model saw only the scrubbed question and statuses — so the plan's
  “the archive is the session, no copy” did not hold, and the panel's record is its own table.
- **One session per mode** (`conv:<id>:read`, `conv:<id>:template`): if the barrier closes mid-conversation, the
  template-mode model starts from its own scrubbed history and never receives what a reading model was sent
  (`test_closing_the_barrier_mid_conversation_sends_none_of_what_was_read_before`).
- **Compaction**: `ContextPolicy(window=24_000, compact_at=0.75, keep_recent=8)`, the same model writing the summary.
  The budget is far below the model's window, so the request that finds it passed still fits. A turn that compacted
  says so in the panel. Upstream fix: a run of one request never compacted (the flag was per run) — operonx-agents
  0.2.5 compacts before that run commits (Operonx #188).
- **Storage**: `SQLiteSession` over one shared connection per file (operonx-agents 0.2.4, Operonx #187: 50
  concurrent sessions raised “database is locked” before). Titles, turns, session items and parked run states are
  sealed with `MF_DATA_KEYS` (`crypto.SealedSession`, `conversations.Runs`); `scripts/rotate_keys.py` re-seals
  `assistant.db` too.
- **The panel** resumes the latest conversation of the role when it moved within a day (on any device), lists them
  (clock button), starts another (“+ Mới”). The old `sessionStorage` copy is removed, not uploaded: it held one tab's
  messages and the server could not tell whose they were.

### As built (A4, 2026-10-17)

- **Items** are operonx-agents 0.3.0's `MemoryItem` in its `SQLiteMemoryStore` (table `operonx_agents_memory` in
  `assistant.db`), text sealed with the data keys bound to the row. Kinds: Sở thích, Mục tiêu, Thông tin (expires
  after 180 days), Giới hạn; the source is the conversation. Until the consolidator (A6), an item is kept only when
  the person asks (“hãy nhớ…”): `ghi_nho` is a write, so the panel shows “Ghi nhớ (Sở thích): “…”?” and nothing is
  kept before Xác nhận; the write is read back.
- **What is never kept** (`memory.refused`, every write, the page's corrections too): an amount or percentage, an
  account, card or document number, or a client's name or id outside the person's own family (the barrier's
  identifier list; the family read is limited to what the person may see). Staff keep no client's name.
- **In the prompt**: the reading model's instructions carry the person's ≤ 15 active items (“Điều người dùng đã nhờ
  ghi nhớ”); template mode never does — the items are the person's words, as private as the question.
- **Tools** (all roles, 29 in the registry): `nho_lai` (recall, with ids), `ghi_nho`, `quen` (confirmed, read back,
  and the file scrubbed), `tim_lich_su` (the archive).
- **The archive** is the `turns` table (what the panel showed): `conversations.archive` reads the person's turns in
  one query and `search_history` folds each message (Vietnamese accents, case, spacing) and keeps those holding
  every word of the query, newest first, with conversation, time and author. Measured on a year of one
  conversation a day, 10 turns each, sealed (3,650 turns): 1.1 s first; 0.5 s after reading in one query and folding
  in one regex pass (`fast_fold`, equal to the upstream `fold` on Vietnamese — the per-character fold was half the
  time). Linear in the person's own archive only; no plain-text index exists because the text is sealed.
- **Bộ nhớ page** (`#/<role>/bo-nho`, every role; from the panel's history and the header): items with kind, when,
  expiry and a link to their conversation — Sửa, Quên, Quên tất cả; conversations — Mở (in the panel), Xoá, and the
  archive search. `POST /api/assistant/memory` (list, search, update, delete, clear): the owner is the server's;
  writes are audited (`assistant.memory.*`) without the text.
- **Deletion is real.** Forgetting an item, clearing, deleting a conversation and the retention sweep end with
  `conversations.scrub()` (WAL checkpoint, VACUUM, checkpoint), so the deleted text is not left in free pages or the
  log; a finished run's state is deleted at the end of its turn and a conversation's run states with it (they held
  its text). Measured: 0.7 s on a 25 MB `assistant.db` (21 people, 2,365 conversations) — once per deletion, never
  on a turn.
- **Retention**: Compliance's `assistant_retention` (two-person, `archive_days` 30–3650, default 365); the
  `assistant_retention` job (02:30 daily) deletes conversations whose last turn is older, with their turns, model
  items and run states, purges expired items, scrubs, and audits the counts.

### As built (sessions, 2026-10-17) — OWN-SS-01…08, [SESSIONS_PLAN.md](../../SESSIONS_PLAN.md)

- **Storage kept.** The owner asked to check the deployment before choosing a store. The app is one `operonx serve`
  process on one host; `assistant.db` (WAL) was measured at ~127 turns/s against a busy hour of ~10 (§8,
  ADR-0027). The sessions are new columns on `conversations` and `turns`, added in place.
- **A session** is a conversation with a name, a goal and a summary. It can be renamed (kept from then on), archived
  (out of the panel's list and the resume, still on Bộ nhớ and in search) and restored. All of these are keyed by
  the owner the server resolved.
- **A turn is written when it starts** (`running`) and updated as each step ends. Measured on the experiment
  server: when the browser closes the stream, operonx serve does not cancel the run. Both tools ran, and the answer
  was recorded about 3 s later. So the panel follows a `running` turn after a reload, re-opening the session every
  2 s. Only a turn still `running` 80 s after it started (the run's wall clock is 65 s) reads as interrupted.
- **Titles and goals** come from the copilot model in one small request (≤ 400 tokens; it thinks first). It runs
  after the 1st and 4th answers and after a compaction. The answer says `describe: true` and the panel asks once
  it has drawn the answer, so no reply waits for it. Live: US$0.0001 and 1.3–2.4 s a title. In template mode no
  model is asked; the title is the question's first clause.
- **Compaction** stays operonx-agents' `ContextPolicy`. Our `Summarizer` swaps upstream's “notes” preamble for seven
  fixed sections: goal, decisions, the person's preferences and limits, open tasks, entities, tool results with
  their dates, and references. A test guards the preamble's shape. The summary is copied to the session and shown
  as “Tóm tắt phiên”. Every item and turn is kept, and `doc_lai_phien` reads the session's own turns back.
- **Two levels.** The A4 items are unchanged and go into every session's instructions. A session's model side, its
  summary and the read-back tool see that session only.

## 6. Knowledge *(built in A5, 2026-10-17)* — ADR-0029, ADR-0030

`operonx-kb` (0.2.6) in `data/kb/` beside the state file: catalog, blobs and a lexical index (FTS5, Vietnamese
bigrams with accents folded). Both collections are **lexical only**, so nothing is sent to an embedding service:

| Collection | Holds | Who reads | Tool |
|---|---|---|---|
| `product` | The Vietnamese guide `docs/huong-dan/` (a file per role and `chung.md` for everyone, a section per page with its route), the “Cách tính” formulas (`src/explain`, 103) and the glossary (16 terms), a section each | the person's role's pages and the shared ones | `huong_dan` (every role): the 3 best pages plus the best formula or term; the first page's route becomes the step's link |
| `materials` | Documents a person adds on the Bộ nhớ page (text, Markdown, HTML, Word, PowerPoint, Excel, PDF; ≤ 5 MB) | the owner and, for a client, the RM assigned to them | `tai_lieu` (on the Bộ nhớ page's roles); deleted by the owner only, for good (purge) |
| — (web) | Never stored | — | `tim_tren_web` |

### As built (A5, 2026-10-17)

- **Embeddings exist; we chose not to use them.** A0 said no embedding service was configured. OpenRouter does
  serve them (33 models; `baai/bge-m3`, 1024-d, US$0.01 per million tokens). Measured on 24 product questions
  (`data/assistant_guide_questions.json`, paraphrased, some without accents): lexical finds the right page in the
  first three 24/24, first 20/24, MRR 0.91, 35 ms; hybrid with bge-m3 24/24, 21/24, MRR 0.93, 1,040 ms (31 embedding
  requests for the measurement). One more first place is not worth a second per question, and lexical-only means a
  client's document never leaves the server.
- **Two searches for `huong_dan`.** With the 103 short formulas in the same ranking the right page fell to 22/24 in
  the first three and 17/24 first; pages and references are searched apart (pages: 24/24, 20/24, unchanged; the
  reference asked about: 10/10 on `data/assistant_reference_questions.json`).
- **Sync**: on the first question of a process the guide files are added; an unchanged file is skipped (first sync
  1.4 s, unchanged 0.27 s), a removed one deleted. The resources are registered for the process only
  (`ResourceHub.register(..., persist=False)`, operonx 1.30.1), never written to `resources.yaml`.
- **Materials**: key `<owner>/<file name>`, tags `owner:` and `client:`, ACL `owner:<owner>` (+ `rm:<assigned RM>` for
  a client). An RM reads the picked client's documents and their own. Adding and deleting are audited with the size
  and the action, never the content. The Bộ nhớ service is not traced (`operonx.toml`: documents and item text would
  be in the trace in clear).
- **Web search** (ADR-0030): OpenRouter's `web` plugin on the copilot model, 3 results. Only the question leaves,
  scrubbed as for the router, its placeholders dropped. URLs are cited, “Theo các nguồn tìm được,” opens the answer
  and a “Mức độ chắc chắn” line closes it. Caps: 20 per person and 500 in total per day, counted before the call.
  Measured on the real model 2026-10-17: 9.1 s, US$0.012, two dated sources whose disagreement the answer named.

## 7. Agents *(built in A6, 2026-10-17; the map in A7)* — ADR-0031, ADR-0033

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

### As built (A6, 2026-10-17)

- **Consolidator** (`src/assistant/consolidate.py`, job `assistant_consolidate` every 5 minutes): conversations idle
  15 minutes whose turns changed (a hash of the turns' numbers and times) — at most 20 a tick, each once per content.
  Only where the model may read the conversation (`turn.model_reads`: `demo`, or the model inside the bank);
  otherwise the run is `skipped` and nothing is sent. Sent: the questions and the answers (600 characters each),
  newest first within 8,000 tokens (1,500 of them the model's), and the owner's items to merge with. Kept: ≤ 5
  items, each through `memory.refused` like a person's own; a repeat (the model's `same_as`, or ≥ 60 % shared words
  of the same kind) is merged — a confirmed item keeps the person's wording, a consolidator's takes the newer one;
  new items have confidence 0.7, the conversation as source, and show “trợ lý tự rút ra” on the Bộ nhớ page.
  Runs (`consolidations`): status, attempts, tokens, the provider's cost, counts — never text; a failure is retried
  on the next two ticks, then left until the conversation changes.
- **Measured** on the real model (`anthropic/claude-haiku-5.5`), five client conversations of 2–11 turns: 531–2,372
  prompt tokens, US$0.00007–0.00037 each, **US$0.00024 a conversation on average**, 4.5 s each; 11 items kept, none
  refused; a “cảm ơn” conversation kept nothing; an 11-turn one kept only the standing request. The token estimate
  was first 3 characters a token; the model counted **1.64–1.70** on Vietnamese, so the budget would have been
  passed by 1.8×: the estimate is now 1.6 (a little high, never low).
- **Follow-ups** (`src/assistant/followups.py`, table `follow_ups`): tools `theo_doi` (a write: “Báo cho bạn một
  lần khi VN-Index dưới 1.200 điểm (theo dõi 30 ngày)?”), `theo_doi_cua_toi`, `huy_theo_doi` (35 tools in all). A
  market series (the 31 of `data/market_sources.json`) above or below a level, or a topic matched in the title of an
  event whose run became effective after the follow-up was made. Checked by an op at the end of each market job (its
  own series) and of `news_ingest`, no model; ≤ 20 open a person, 30 days by default (≤ 180); a hit fires once.
  Shown in the bell for every role until opened (“Theo dõi: …”, with the close or the event), and in a “Việc theo
  dõi” panel on the Bộ nhớ page (Huỷ). On the real model both kinds were asked for correctly in one request each.
- **Cost per day** = conversations consolidated × ~US$0.00024: 1,000 a day would cost about US$0.24.
  `consolidate.costs()` reads it from the runs per day; the map shows the last day's on the consolidator.

### As built (A7, 2026-10-17) — the map

- **Where**: the Agent page (CIO, Compliance, Admin) opens on it; the catalogue and AI quality stay below. The
  panel's conversation list links to it for those roles. One endpoint, `GET /api/agents/map`
  (`src/views/ecosystem.py`), and `GET /api/agents/map/<part>` for a part's runs (`?run=<id>` for one run's steps).
- **Parts** (21, in six groups): the person; the front door (the assistant, the keyword fallback, its 35 tools in
  four families by the module that holds them — app, memory, follow-ups, guide/documents/web); the data (news,
  application data, market, conversations and memory, knowledge, web); the CIO desk (queue, CIO agent, challenger,
  policy agent); the rules (follow-up checks, the 07:00 policy sweep); the background (consolidator, retention).
- **Lines** (27) are only what the code does: each names a file and a symbol (`app/main.py::assistant_flow`,
  `src/views/ops.py::review`, …), listed in the part's drawer; a test fails if one is missing, if a part has no
  line, or if a registry tool is in no family.
- **States** come from what each part recorded, never from guesses: the assistant's turns from the audit log
  (`assistant.turn`: role, mode, tools and their statuses, tokens, cost — no text) and the writes waiting on a
  person (`parked`); the queue (`agent_jobs`); the agents' runs (`agent_runs`); the consolidator's runs
  (`consolidations`) over its job; the follow-ups (`follow_ups`); every scheduled job's own run records
  (`.operonx/jobs/<job>/<run>/run.json`). *Đang chạy* — a run not finished; *Đang chờ* — queued, or waiting on a
  person or a condition; *Hoàn tất* / *Lỗi* — the last run; *Chưa chạy* — none yet. A part with several jobs (the
  market) is as well as the worst of their last runs.
- **Drill-down**: a part's last 20 runs; a run's steps — for a job, each item's ops with status and time read from
  its trace (`nodes.jsonl`), the error's last line; for an agent run, its nodes (model, tokens, attempts); for a
  turn, its tools. Never a prompt, a question, an answer, an input or an output.
- **States match the traces** (`tests/test_agent_map.py`): the real jobs run into a folder of the test's own; the
  policy sweep's state follows its traces (a failing client → *Lỗi*, the failed op in the drawer is the one the trace
  names); the consolidator shows *Lỗi* when its trace reports a failed conversation though the job itself ended
  well, and *Hoàn tất* after the retry; the CIO desk's states follow the worker's trace.
- **Privacy fix**: the `assistant`, `copilot` and `assistant_conversations` services no longer write traces
  (`[tracing.services.*] sinks = []`, like `assistant_memory` in A5): their ops' inputs held the person's question in
  clear under `.operonx/runs`. The map reads turns from the audit log instead. Traces already written on the server
  (six, all test questions from this work) were left in place.
- **Speed**: a day of job runs is ~500 small run records; the map takes 19 ms warm (a finished run's record is read once per
  process).
- **Found by the map**: the server's 07:00 policy sweep of 16/10 failed for all five clients (“Cần đăng nhập”): it
  ran code from before scheduled runs were exempted from sign-in (0cc1c83); the current code passes
  `tests/test_auth.py`; the next morning's run confirms it on the server.

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

## 9. Upstream into OperonX *(built A1–A8)*

| Need | Where | Phase |
|---|---|---|
| Sessions and stores on one SQLite file share one connection (the lock errors in §8); reads without a write lock | `operonx-agents` `_storage.py` — **done**, 0.2.4 (Operonx #187) | A3 |
| A conversation whose runs are one request each compacts (the flag was per run) | `operonx-agents` runner — **done**, 0.2.5 (Operonx #188) | A3 |
| Long-term memory items (typed, sourced, expiring) with a store protocol and SQLite store (sealing codec); search; memory tools (recall, remember, forget, with verifiers) | `operonx-agents` `memory/` — **done**, 0.3.0 (Operonx #189). The archive search stays in OneWealth: its archive is the panel's `turns`, not a session store | A4 |
| Tool verifiers: a check run after a tool, its verdict in the tool message and the trace | `operonx-agents` tools — **done**, 0.2.3 (`@tool(verify=)`, Operonx #186) | A1 |
| A lexical-only collection (no embedder) that can add, delete and collect garbage; documents with key, tags, ACL, metadata | `operonx-kb` — **done**, 0.2.6 (Operonx #193) | A5 |
| Register a resource for this process only, without rewriting `resources.yaml` | `operonx` `ResourceHub.register(persist=False)` — **done**, 1.30.1 (Operonx #194) | A5 |
| A model's cost where the provider reports it (OpenRouter's `usage.cost`) and no prices are declared — `Usage.cost_usd` was empty, so no cost per turn and no cost cap | `operonx-agents` `Usage.from_completion` — **done**, 0.3.1 (Operonx #199) | A8 |
| A served graph with an input called `name` gets that input (the serve layer named the run with it) | `operonx` serve `compile_graph` — **done** (Operonx #200, unreleased; OneWealth's flow input is `message`, so not affected) | A8 |
| `operonx_kb.__version__` reported 0.2.3 through 0.2.6 | `operonx-kb` 0.2.7 (Operonx #200) | A8 |

OneWealth keeps only its rules: which tools, which roles, the barrier, what a memory item may hold, retention values.

## 9b. Streaming to the graph workspace *(target, FEAT-40, ADR-0035)*

`POST /api/assistant/stream` takes the body of `POST /api/assistant` and answers with server-sent events while the
turn runs. It is a served graph with doors — `ingress` (the body) → `stream_turn`, a generator op over operonx-agents'
`Runner.stream` / the resume path → `egress` per event — so operonx numbers the events and a reader that dropped can
resume (`?run_id=&after_seq=`). Events: `step` (running · ok · failed, with the tool's graph `nodes` and, when it
ends, its `focus` keys), `text` (model mode only), `wait`, `answer` (the JSON door's object, kept in the
conversation and audited the same way) and `error`. The barrier is unchanged: in template mode no model text is
streamed. The service has `sinks = []` like `assistant` (its items are the person's words). The JSON door stays.

## 10. Migration *(target)*

1. A1: the registry beside the Copilot; `copilot_flow` reads its tools from it (no behaviour change; its tests pass).
2. A2: `POST /api/assistant` and the agent; the panel switches to it; `POST /api/copilot` kept (the template path,
   and the fallback when the model is unavailable — NFR-03: an AI failure must not stop the product).
3. A3: conversations move from `sessionStorage` to the server; the panel lists them; the old storage is dropped
   (not uploaded: one tab's messages, nobody's to claim) — done.
4. A4–A7 add memory, knowledge, agents and the map without changing earlier contracts.
5. A8: the eval gate decides readiness; the report states what passed, what failed and what it costs.

## 11. Costs *(measured in A8, 2026-10-17)*

The provider's own `usage.cost`, per turn (operonx-agents 0.3.1). A turn's cost includes the cost of its tools that call a
model (the web search); it is in the turn's `usage.cost_usd` and the audit record.

| What | Cost |
|---|---|
| An assistant turn (42 eval turns, Haiku 5.5) | US$0.00196, 9,462 tokens |
| A turn with a web search | US$0.012–0.024 |
| The consolidator, one conversation | ~US$0.00024 |
| Follow-up checks, the guide and materials search | 0 |

A modelled day for 100 clients asking 5 questions each (1 in 20 on the web) is about US$1.5. The full figures
and the gate are in [assistant_readiness.md](../testing/assistant_readiness.md).
