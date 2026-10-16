# ADR-0030 — Web search through the existing OpenRouter key, scrubbed and cited

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** OWN-AS-07; brief §1 (“using web search… with sources and clear uncertainty”); docs/ASSISTANT_PLAN.md A-D5

## Context

The plan expected to ask the owner for a search provider key. The models already run through OpenRouter, whose `web`
plugin searches and returns URL citations. Measured on 2026-10-16 with the existing key: a question on the State Bank's
policy rate answered in 8 s for US$0.012 with three dated Vietnamese sources.

## Decision

- One `web_search` tool calling the OpenRouter `web` plugin (≤ 3 results) behind an adapter.
- The query is the person's question scrubbed as for the router (no names, numbers, codes): nothing about a client
  leaves.
- Answers cite each URL, say “theo các nguồn tìm được”, and state certainty; results are not stored.
- Caps: 20 searches per person per day, 500 in total; over the cap, or without the key, the tool says web search is
  unavailable.

## Consequences

No new vendor or key. Search quality is OpenRouter's (Exa); the eval suite measures it on outside-scope questions.

## Notes (A5, 2026-10-17)

- Built as `tim_tren_web` (`src/assistant/web.py`). Two faults found only on the real model, both fixed: operonx
  sends a provider's extra keywords as the request's `extra_body`, so `plugins=` is passed as a keyword (an
  `extra_body=` keyword arrived nested and the search never ran); and the model thinks before it answers, so 500
  tokens ended in thinking with no answer (`finish_reason: length`): now 1,500 with low reasoning effort.
- Measured after the fixes: 9.1 s, US$0.012 (one search request), two dated sources whose disagreement the answer
  named, certainty “trung bình”. Five real calls in all while building it, about US$0.06.
