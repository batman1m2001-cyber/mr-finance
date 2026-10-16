# ADR-0031 — Two new background agents: the memory consolidator and the follow-up watcher

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** OWN-AS-18, OWN-AS-19; brief §3; docs/ASSISTANT_PLAN.md A-D6

## Context

The brief asks for a small family of purposeful agents, event-driven where possible, with budgets, deduplication,
retries and observability. The CIO agent, challenger, policy agent and newsletter step exist; monitoring is done by
rule-based alert jobs.

## Decision

- Keep the existing agents unchanged.
- **Memory consolidator**: runs once per idle conversation (15 min without a turn, found by a job every 5 min), only
  when its content changed since the last run (hash); ≤ 8,000 tokens; queued with 2 retries; traced.
- **Follow-up watcher**: only for a follow-up the person asked for. The assistant's `follow_up` tool stores a
  structured condition (a market series crossing a level, an approved event on a topic); the existing market and news
  jobs check the conditions with no model call; a hit notifies once in the bell and the feed.
- No monitoring agent: the alert jobs stay rules.

## Consequences

Background model spend is the consolidator only, bounded per conversation and measured per day (A6). Follow-ups
cannot express free-form conditions; the tool says which kinds it supports.

## Notes (A6, 2026-10-17)

- Built as decided. Measured on the real model: the consolidator costs ~US$0.00024 a conversation (five
  conversations, 531–2,372 prompt tokens, 4.5 s each); about US$0.24 a day for 1,000 conversations. Follow-up checks
  cost nothing.
- The token budget's estimate was wrong by 1.8× (3 characters a token assumed; 1.64–1.70 counted on Vietnamese) and
  was corrected before release: an estimate that is low lets a run pass its budget.
- A follow-up shows in the bell for every role (a client's bell is the feed's list; staff have no feed).
- The consolidator writes only where the model may read the conversation; elsewhere its run is `skipped`.
