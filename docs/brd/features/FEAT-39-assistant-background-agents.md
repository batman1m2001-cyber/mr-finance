# FEAT-39 — The assistant's background agents: memory consolidator and follow-ups

| | |
|---|---|
| Type | Proposed extension (owner request B-08) |
| Requirements | OWN-AS-12, OWN-AS-18, OWN-AS-19 |
| Users | every signed-in role (their own follow-ups and memory) |
| Entry points | the tools `theo_doi`, `theo_doi_cua_toi`, `huy_theo_doi`; the job `assistant_consolidate`; the market and news jobs; the bell; the “Việc theo dõi” panel of the Bộ nhớ page |
| Status | see [traceability](../requirements/requirements_traceability.md) — built in ASSISTANT_PLAN A6 (2026-10-17) |

## Purpose
Do the few background tasks worth doing for the assistant: distil finished conversations into long-term memory, and
watch conditions a person asked to be told about.

## Preconditions and permissions
Each runs for one owner, with only that owner's data. The consolidator runs only where the model may read the
conversation (`client_ai = demo`, or the model inside the bank).

## Inputs → outputs
Idle conversation → ≤ 5 long-term items. A follow-up's condition met → one notification in the person's bell.

## Behaviour
1. **Consolidator**: the `assistant_consolidate` job (every 5 minutes) finds conversations idle for 15 minutes whose
   turns changed since their last consolidation (≤ 20 a tick), reads each (questions and answers, newest first,
   within 8,000 tokens), keeps ≤ 5 items — each checked like a person's own “hãy nhớ…”, repeats merged — and records
   tokens and the provider's cost. A failure is retried on the next two ticks.
2. **Follow-up**: `theo_doi` (a write the person confirms) stores a market series above or below a level, or a topic,
   for 30 days (≤ 180); the market jobs (their own series) and the news job (events made effective since) check the
   open ones with no model call; a hit fires once and shows in the bell until opened. `theo_doi_cua_toi` lists them,
   `huy_theo_doi` cancels one; the Bộ nhớ page lists and cancels too.
   *Changed from the A0 design*: the bell, for every role, rather than “the bell and the feed” — a client's bell is
   the feed's list, and staff have no feed; one tool became three (list and cancel are their own steps, as for
   memory).

## States
Follow-up: `open` → `fired` | `expired` | `cancelled`. Consolidation run: `done` | `skipped` | `failed` (attempts).

## Rules and validation
Consolidator ≤ 8,000 tokens per conversation (estimated at 1.6 characters a token, measured 1.64–1.70); items never
hold an amount, an account or someone outside the family; new items have confidence 0.7 and say “trợ lý tự rút
ra”. Follow-ups ≤ 20 open per person; only the 31 market series and topics; a topic's words are sealed.

## Errors
A failed run keeps its error (never the text) and is retried twice; a follow-up the tool cannot express is refused
before anything is written.

## API and data
`data/assistant.db`: `operonx_agents_memory`, `follow_ups`, `consolidations`. `POST /api/assistant/memory` actions
`follow_ups` (with `unseen`), `follow_up_cancel`, `follow_up_seen` (`key`). See
[assistant.md §7](../architecture/assistant.md#7-agents-built-in-a6-2026-10-17-the-map-in-a7--adr-0031-adr-0033).

## Implementation
`src/assistant/consolidate.py`, `src/assistant/followups.py`, `src/assistant/ops.py` (`consolidate_due`,
`follow_ups_market`, `follow_ups_topics`, `memory_page`), `src/assistant/graph.py::assistant_consolidate_flow`,
`src/market/graph.py`, `src/news/graph.py`, `app/main.py` (the job), `web/header.js` (the bell),
`web/pages/memory.js`.

## Dependencies
FEAT-35 (market data jobs), FEAT-01 (news), FEAT-37.

## Acceptance and tests
`tests/test_assistant_agents.py`: an idle conversation distilled once and again only when it changes; what a
person could not keep is not kept, repeats merged; a confirmed item keeps its wording; nothing sent where the model
may not read; retried twice then left; the budget kept, newest first; cost per day; follow-ups fire once for their
owner only, on their job's series, on an event approved after them; caps and expiry; refusals before writing; the
page's actions. `tests/test_assistant_tools.py` (the two writes: plan, confirm, read back).
`tests/ui/test_memory_ui.py::test_a_fired_follow_up_rings_once_and_an_open_one_is_cancelled`. Real model:
docs/brd/testing/assistant_eval.md (A6).

## Limitations
Follow-ups cannot express free-form conditions. In template mode the model sees the question scrubbed of numbers,
so a market follow-up's level cannot be set by asking (the topic kind still works).
