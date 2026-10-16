# FEAT-39 — The assistant's background agents: memory consolidator and follow-ups

| | |
|---|---|
| Type | Proposed extension (owner request B-08) |
| Requirements | OWN-AS-12, OWN-AS-18, OWN-AS-19 |
| Users | every signed-in role (their own follow-ups and memory) |
| Entry points | the `follow_up` tool; jobs `assistant_consolidate`, the market and news jobs |
| Status | see [traceability](../requirements/requirements_traceability.md) — built in ASSISTANT_PLAN A6 |

## Purpose
Do the few background tasks worth doing for the assistant: distil finished conversations into long-term memory, and
watch conditions a person asked to be told about.

## Preconditions and permissions
Each runs for one owner, with only that owner's data and the tools listed below.

## Inputs → outputs
Idle conversation → ≤ 5 long-term items. A follow-up's condition met → one notification in the bell and the feed.

## Behaviour
1. **Consolidator**: a job every 5 minutes finds conversations idle for 15 minutes whose content hash changed since
   their last consolidation, queues one run each (2 retries), reads the conversation, writes items (deduplicated
   against the owner's), records tokens and cost.
2. **Follow-up**: the assistant's tool stores a structured condition (series, comparison, level; or an approved event
   on a topic) with an expiry; the market and news jobs evaluate open conditions after they load data, with no model
   call; a hit notifies once and closes the follow-up.

## States
Follow-up: `open` → `fired` | `expired` | `cancelled`. Consolidation run: `queued` → `done` | `failed`.

## Rules and validation
Consolidator ≤ 8,000 tokens per conversation; follow-ups ≤ 20 open per person; supported conditions listed by the
tool.

## Errors
A failed run stays visible on the map with its trace; retries are bounded.

## API and data
`data/assistant.db`: `memory_items`, `follow_ups`, consolidation runs. See
[assistant.md §7](../architecture/assistant.md#7-agents-target-a6a7--adr-0031-adr-0033).

## Implementation
*(A6)* `src/assistant/consolidate.py`, `src/assistant/followups.py`.

## Dependencies
FEAT-35 (market data jobs), FEAT-01 (news), FEAT-37.

## Acceptance and tests
*(A6)* deduplication, budget, retries, a follow-up firing once, cost per day measured.

## Limitations
Follow-ups cannot express free-form conditions.
