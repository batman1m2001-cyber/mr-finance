# FEAT-38 — Knowledge base and web search

| | |
|---|---|
| Type | Proposed extension (owner request B-08) |
| Requirements | OWN-AS-02, OWN-AS-07, OWN-AS-16, OWN-AS-17 |
| Users | every signed-in role |
| Entry points | the assistant's `help`, `materials` and `web_search` tools; uploading a document in the panel |
| Status | see [traceability](../requirements/requirements_traceability.md) — built in ASSISTANT_PLAN A5 |

## Purpose
Let the assistant answer about the product itself and about documents a person gives it, citing the passage, and
answer outside topics from the web with sources and a stated certainty.

## Preconditions and permissions
`product` is readable by every role; a document in `materials` by its owner and, for a client, their assigned RM.
Web search needs the OpenRouter key and is capped per person and per day.

## Inputs → outputs
A question → passages (KB) with checked quotes, or web results with URLs → an answer citing them.

## Behaviour
1. The product guide (Vietnamese, per page and role), the glossary and the “Cách tính” catalogue are ingested into
   `product` at start-up when they changed.
2. A person uploads a document in the panel; it is ingested into `materials` with their ACL.
3. `help` / `materials` search lexically (FTS5) and return passages whose quotes are found in the text.
4. `web_search` sends the scrubbed question to OpenRouter's `web` plugin (≤ 3 results) and returns the cited text.

## States
Document versions as `operonx-kb` keeps them; deleted with the owner's data.

## Rules and validation
Web results are never stored. The query sent out carries no names, numbers or codes.

## Errors
No key, over the cap, or a provider failure: the tool says web search is unavailable.

## API and data
`data/kb.db` (operonx-kb catalog), blobs beside it. See
[assistant.md §6](../architecture/assistant.md#6-knowledge-target-a5--adr-0029-adr-0030).

## Implementation
*(A5)* `src/assistant/knowledge.py`, `src/assistant/web.py`.

## Dependencies
operonx-kb (ADR-0029), OpenRouter (ADR-0030), FEAT-32.

## Acceptance and tests
*(A5)* grounding on product questions, ACL isolation of materials, web citations, unavailable path.

## Limitations
Lexical search only (no embedding service): recall on paraphrased questions is measured, not assumed.
