# ADR-0029 — The knowledge base on operonx-kb, product and personal collections apart

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** OWN-AS-02, OWN-AS-16, OWN-AS-17; brief §2 (“knowledge base / second brain”); docs/ASSISTANT_PLAN.md A-D4

## Context

The assistant must answer about the app and about material a person provides, citing it, while keeping shared
knowledge, personal material and web content apart. `operonx-kb` (published, 0.2.5) has versioned documents, lexical
(FTS5) and dense search, per-document ACLs closed by default, and answers whose quotes are checked against the text.

## Decision

- Add `operonx-kb` as a dependency, catalog `data/kb.db`, lexical search (no embedding service is configured).
- Collection **`product`**: a Vietnamese user guide per page and role, the glossary, the “Cách tính” catalogue; ACL
  every role.
- Collection **`materials`**: documents a person uploads; ACL the owner (and a client's assigned RM); deleted with
  their data.
- Web content is never stored (ADR-0030).

## Consequences

One new dependency, justified by citations checked against the text and ACLs we would otherwise rebuild. Without
embeddings, paraphrased questions rely on the guide's wording; A5 measures recall on the product questions.
