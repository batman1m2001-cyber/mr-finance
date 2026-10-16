# ADR-0028 — Three memory layers: the conversation, a few long-term items, the archive

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** OWN-AS-11…16; brief §2; docs/ASSISTANT_PLAN.md A-D3

## Context

The brief asks for short-term, long-term and archive memory that is permission-aware, inspectable, correctable and
deletable, and warns against keeping every detail. `operonx-agents` has sessions and compaction (short-term), nothing
for the other two.

## Decision

- **Short-term**: the conversation in its session, compacted by `ContextPolicy` into a summary item when it passes the
  window (never dropped silently), plus the parked task state.
- **Long-term**: typed items (`preference`, `goal`, `fact`, `constraint`), ≤ 200 characters, each with its source
  message, time, confidence and expiry; written only by the consolidator after a conversation (≤ 5 per conversation,
  deduplicated) or when the person asks “hãy nhớ…”; never amounts, accounts or other people's data; listed on the
  **Bộ nhớ** page to correct or forget.
- **Archive**: the stored messages themselves, searched per owner; Compliance's retention (`assistant_retention`,
  two-person, default 365 days) deletes older ones.
- Every read and write is keyed by the owner the server resolved; no tool accepts an owner.
- The generic parts (item model, store, archive search, memory tools) are built in `operonx-agents`; OneWealth keeps
  its rules (kinds, limits, what may not be stored, retention values).

## Consequences

Long-term memory stays small and visible; what the assistant "knows" about a person is a page they can read. Archive
search is a scan of one person's messages (sealed content cannot use a plain FTS index), measured in A4.
