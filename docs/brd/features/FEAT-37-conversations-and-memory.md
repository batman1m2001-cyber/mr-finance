# FEAT-37 — Conversations and memory

| | |
|---|---|
| Type | Proposed extension (owner request B-08) |
| Requirements | OWN-AS-10, OWN-AS-11, OWN-AS-12, OWN-AS-13, OWN-AS-14, OWN-AS-15, OWN-AS-16 |
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
4. The assistant's instructions carry the person's active long-term items (≤ 15); the `recall`, `search_history`,
   `remember` and `forget` tools read and change them.
5. The Bộ nhớ page lists the items with their source message and expiry, and the conversations; each can be
   corrected or deleted, or all at once.
6. Compliance's `assistant_retention` (two-person) deletes archived messages past their age (default 365 days) and
   expired facts.

## States
Conversation: `active` → `idle` (15 min without a turn) → consolidated; deleted. Item: `active` → `expired` | deleted.

## Rules and validation
Items are ≤ 200 characters, typed (`preference`, `goal`, `fact`, `constraint`), never an amount, an account number
or another person's data. Content and item text sealed when data keys are set.

## Errors
A storage failure fails the turn visibly; nothing is half-written.

## API and data
`data/assistant.db` (WAL): `operonx_agents_items`, the run state store, `conversations`, `memory_items`. See
[assistant.md §5](../architecture/assistant.md#5-conversations-and-memory-target-a3a4--adr-0027-adr-0028).

## Implementation
*(A3–A4)* `src/assistant/` with the generic parts in `operonx-agents` (`memory/`).

## Dependencies
FEAT-32 (the assistant), FEAT-39 (the consolidator), FEAT-14 (retention configuration).

## Acceptance and tests
*(A3–A4)* long conversations and compaction, resume, isolation between two people, deletion really deletes,
retention.

## Limitations
Archive search scans one person's messages (sealed content has no plain index).
