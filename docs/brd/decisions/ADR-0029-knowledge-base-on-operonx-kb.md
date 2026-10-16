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

## Amendment (A5, 2026-10-17)

- **The premise “no embedding service is configured” was wrong**: OpenRouter, on the key we already use, serves 33
  embedding models. Measured on 24 product questions: lexical 24/24 in the first three, 20/24 first, MRR 0.91,
  35 ms; hybrid with `baai/bge-m3` 24/24, 21/24, MRR 0.93, 1,040 ms. **The decision stands, now for a reason**:
  lexical only, because one more first place does not pay for a second per question, and a person's document never
  leaves the server.
- The catalog is `data/kb/` (catalog, blobs, lexical index), not `data/kb.db`; its resources are registered for the
  process only (operonx 1.30.1 `persist=False`). A lexical-only collection needed operonx-kb 0.2.6 (Operonx #193).
- `product` also holds the “Cách tính” formulas and the glossary, searched apart from the pages (they outranked the
  right page on 5 of 24 questions in one ranking).
- Documents are added on the Bộ nhớ page, not in the panel (FEAT-38).
