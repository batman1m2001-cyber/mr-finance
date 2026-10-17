# FEAT-37 — Conversations and memory

| | |
|---|---|
| Type | Proposed extension (owner request B-08) |
| Requirements | OWN-AS-10, OWN-AS-11, OWN-AS-12, OWN-AS-13, OWN-AS-14, OWN-AS-15, OWN-AS-16; sessions OWN-SS-01…08 |
| Users | every signed-in role |
| Entry points | the assistant panel (conversation list); the **Bộ nhớ** page; `/api/assistant/conversations`, `/api/assistant/memory` |
| Status | see [traceability](../requirements/requirements_traceability.md) — built in ASSISTANT_PLAN A3–A4 |

## Purpose
Keep a person's conversations with the assistant on the server, let the assistant remember a few durable things about
them, and let them see, correct and delete all of it.

## Preconditions and permissions
Signed in. Everything is keyed by the person the server resolved; no request names another owner.

## Inputs → outputs
A turn's items → the conversation (short-term). A finished conversation → at most five long-term items (consolidator,
FEAT-39). Any stored message → archive search results with conversation, time and author.

## Behaviour
1. A conversation is created on the first message, titled from it, listed in the panel, resumable on any device.
2. Each turn's items are committed when the turn ends; a cut turn writes nothing.
3. When the prompt passes the context window, older exchanges become a summary item (`ContextPolicy`); the panel
   says so.
4. The assistant's instructions carry the person's active long-term items (≤ 15; reading mode only); the tools
   `nho_lai`, `tim_lich_su`, `ghi_nho` and `quen` read and change them (writes confirmed in the panel).
5. The Bộ nhớ page lists the items with their source message and expiry, and the conversations; each can be
   corrected or deleted, or all at once.
6. Compliance's `assistant_retention` (two-person) deletes archived messages past their age (default 365 days) and
   expired facts.

### Sessions (OWN-SS-01…08, built in [SESSIONS_PLAN.md](../../SESSIONS_PLAN.md) S1–S4, 2026-10-17)
7. A conversation is a **session**: it can be renamed, archived (hidden, brought back) or deleted. Its title is generated
   (≤ 7 words) after the first answer and refined later; a title the person set is kept. Template mode never sends the
   question to a model for a title.
8. A turn is written when it starts and completed when it ends. The server keeps answering when the page goes
   away, so after a reload the panel shows the steps so far and follows the turn to its answer. A turn the server
   never finished (it stopped) shows what ran, marked “Bị ngắt”.
9. Each session keeps a goal and a context summary. Compaction writes the summary in seven fixed sections (goal,
   decisions, preferences, open tasks, entities, tool results, references); the session keeps every message, and
   `doc_lai_phien` reads them back.
10. New Chat starts an empty session: global memory and earlier sessions stay.

## States
Conversation: `active` → `idle` (15 min without a turn) → consolidated (A6); deleted. Item: `active` → `expired` |
deleted.

## Rules and validation
Items are ≤ 200 characters, typed (`preference`, `goal`, `fact`, `constraint`), never an amount, an account number
or another person's data. Content and item text sealed when data keys are set.

## Errors
A storage failure fails the turn visibly; nothing is half-written.

## API and data
`data/assistant.db` (WAL): `conversations`, `turns` (what the panel showed), `operonx_agents_items` (the model's side,
one session per mode), `assistant_runs` (parked runs, with their session), `parked`, `operonx_agents_memory` (items,
A4). See
[assistant.md §5](../architecture/assistant.md#5-conversations-and-memory-built-in-a3a4-2026-10-17--adr-0027-adr-0028).

## Implementation
A3 (2026-10-17): `src/assistant/conversations.py` (the store, sealed), `src/assistant/turn.py` (`ContextPolicy`, a
session per mode), `assistant_conversations_flow` (`POST /api/assistant/conversations`: list, open, delete), the
panel's history (`web/copilot.js`). operonx-agents 0.2.4 (one SQLite connection per file) and 0.2.5 (compaction
across runs). A4 (2026-10-17): `src/assistant/memory.py` (the rules, the tools, the archive search),
`src/assistant/retention.py` (the daily sweep), `assistant_memory_flow` (`POST /api/assistant/memory`), the Bộ nhớ
page (`web/pages/memory.js`); the generic store and tools are operonx-agents 0.3.0 `memory` (Operonx #189).

Sessions (2026-10-17): `src/assistant/conversations.py` (columns `title_auto`, `archived`, `goal`, `summary`,
`summary_at`, `described`; `turns.status`; `begin` / `progress` / `interrupt` / `record`; `rename`, `set_archived`,
`describe`), `src/assistant/sessions.py` (titles and goals), `src/assistant/turn.py` (`Summarizer`, the summary kept),
`src/assistant/memory.py` (`doc_lai_phien`), `assistant_conversations_flow` (actions `list_archived`, `rename`,
`archive`, `restore`, `describe`), the panel's session bar and history (`web/copilot.js`), Bộ nhớ lists archived
sessions too.

## Dependencies
FEAT-32 (the assistant), FEAT-39 (the consolidator), FEAT-14 (retention configuration).

## Acceptance and tests
A3: `tests/test_assistant_conversations.py` — carry-on and reopen as shown, owner-only list/open/continue/delete,
deletion removes turns and the model's side (audited without text), a parked write inside its conversation, a
30-turn conversation compacting twice with every turn kept, sealing and key rotation, the barrier closing
mid-conversation; `tests/ui/test_copilot_ui.py::test_a_conversation_is_picked_up_on_another_device_listed_and_deleted`.
A4: `tests/test_assistant_memory.py` — what is never kept, kept only when asked and confirmed then carried into the
next conversation, template mode never sends items, the page's corrections audited without text, one person's
memory never another's, the archive searched with conversation, time and author, nothing readable on disk after
forgetting, sealing, retention; `tests/ui/test_memory_ui.py` (the page: correct, forget, forget all; find a past
conversation and open it in the panel, phone).

Sessions: `tests/test_assistant_sessions.py` — rename, archive and restore by the owner only; a turn kept from its
start, cut and stale turns; one row per finished turn; two signed-in customers over HTTP; titles and goals written
once, again at the fourth turn, never over the person's name, nothing sent in template mode, a broken answer
ignored; compaction in seven sections kept on the session, the next turn continuing from it, the read-back limited
to the session, upstream's prompt shape guarded. `tests/ui/test_sessions_ui.py` — named, kept on reload, renamed,
started anew, searched, archived and restored; a running turn followed to its answer after a reload and a dead one
marked cut (phone).

## Limitations
Archive search scans one person's messages (sealed content has no plain index): 0.5 s for a year of daily 10-turn
conversations. Items are kept only on request until the consolidator (FEAT-39, A6).
