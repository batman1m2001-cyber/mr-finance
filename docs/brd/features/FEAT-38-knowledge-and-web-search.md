# FEAT-38 — Knowledge base and web search

| | |
|---|---|
| Type | Proposed extension (owner request B-08) |
| Requirements | OWN-AS-02, OWN-AS-07, OWN-AS-16, OWN-AS-17 |
| Users | every signed-in role |
| Entry points | the assistant's `huong_dan`, `tai_lieu` and `tim_tren_web` tools; the “Tài liệu của bạn” panel on the Bộ nhớ page |
| Status | see [traceability](../requirements/requirements_traceability.md) — built in ASSISTANT_PLAN A5 (2026-10-17) |

## Purpose
Let the assistant answer about the product itself and about documents a person gives it, citing the passage, and
answer outside topics from the web with sources and a stated certainty.

## Preconditions and permissions
`product` is readable by every role (a person reads their role's pages and the shared ones); a document in
`materials` by its owner and, for a client, their assigned RM. Web search needs the copilot model configured and is
capped per person and per day.

## Inputs → outputs
A question → passages (KB) with the page to open, or web results with URLs → an answer citing them.

## Behaviour
1. The product guide (`docs/huong-dan/`, Vietnamese, a section per page and role), the “Cách tính” formulas and the
   glossary are synced into `product` on the first question of a process; an unchanged file is skipped.
2. A person adds a document on the Bộ nhớ page (“Tài liệu của bạn”); it is read into `materials` with their ACL.
   *Changed from the A0 design*, which put the upload in the panel: the page already lists what the assistant keeps
   about the person, and deleting a document belongs beside it.
3. `huong_dan` searches the role's pages (3) and, apart, the formulas and terms (1); the first page's route is the
   step's link. `tai_lieu` searches the person's documents (4 passages). Both lexical (FTS5, accents folded).
4. `tim_tren_web` sends the scrubbed question to OpenRouter's `web` plugin (3 results) and returns the cited text.

## States
A document is new, replaced when added again under the same name, or deleted (purged) by its owner.

## Rules and validation
Only text, Markdown, HTML, Word, PowerPoint, Excel and PDF files, ≤ 5 MB. Nothing goes to an embedding service. Web
results are never stored. The query sent out carries no names, numbers or codes. Adding and deleting a document are
audited without its content; the Bộ nhớ service is not traced.

## Errors
A file of another kind or over 5 MB: refused with the reason. No model, over the cap, or a provider failure: the
tool says web search is unavailable.

## API and data
`POST /api/assistant/memory` actions `materials`, `material_add` (`file_name`, base64 `data`), `material_delete`
(`key`). `data/kb/` (operonx-kb catalog, blobs, lexical index). See
[assistant.md §6](../architecture/assistant.md#6-knowledge-built-in-a5-2026-10-17--adr-0029-adr-0030).

## Implementation
`src/assistant/knowledge.py` (collections, sync, guide, materials, tools), `src/assistant/web.py`,
`src/assistant/ops.py::memory_page`, `web/pages/memory.js`, `docs/huong-dan/`.

## Dependencies
operonx-kb 0.2.6 (ADR-0029), operonx 1.30.1, OpenRouter (ADR-0030), FEAT-32, FEAT-37.

## Acceptance and tests
`tests/test_assistant_knowledge.py`: role pages with the page to open; sync skips an unchanged file; 24/24 product
questions find their page in the first three (≥ 20 first); 10/10 formula and term questions; a document read by its
owner and their RM only; only the owner deletes and nothing is left; refused kinds and sizes; the web gets only the
scrubbed question, with the plugin, and answers with sources; caps and the unavailable path.
`tests/ui/test_memory_ui.py::test_a_document_is_added_found_and_deleted`.

## Limitations
Lexical search: a question in words the guide does not use can miss (hybrid with embeddings measured one more first
place out of 24, for a second more per question). Scanned PDFs without a text layer are not read (no OCR).
