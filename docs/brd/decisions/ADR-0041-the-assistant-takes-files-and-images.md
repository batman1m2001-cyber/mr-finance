# ADR-0041 — The assistant takes files and images, reads them once, and saves what they show behind Xác nhận

- **Status:** accepted
- **Date:** 2026-10-26
- **Sources:** plan [`docs/OCR_PLAN.md`](../../OCR_PLAN.md); the owner's request
  ([`2026-10-26_documents_to_the_assistant.md`](../sources/owner_requests/2026-10-26_documents_to_the_assistant.md))
- **Amends:** the rule in `src/assistant/actions.py`'s header that the client's own uploads stay on their page
- **Keeps:** BRD-NFR-08 (client data reaches only the client model), [ADR-0012](ADR-0012-the-copilot-routes-and-never-reads-client-data.md)
  (no data in the prompt beyond the turn's own), the confirm-then-verify rule of every write

## Context

The client's documents reach the app through one page, Tải sao kê, which reads a PDF, Excel or CSV file and nothing
else: a scanned PDF has no text and gives no item, and a photo of a receipt, a bill or a valuation certificate has no
door at all. The owner asked for the assistant to take them — pasted, attached or photographed — and for an image
sent with no words to find its own flow. The assistant's writes left the client's uploads to their page, because the
person had to see what would be saved before it was.

## Decision

1. **One door, read once.** `POST /api/assistant/attach` takes images, statements and documents (5 MB). The file is
   read when it arrives — a table by the statement reader, an image or a scan by one vision call on the client model
   (reasoning off, temperature 0, one shape of items) — and that first reading is kept with it. What the person
   confirms is what is saved; a write's two plans never read the file again.
2. **The turn reads text, never the image.** The reading enters the message as one block (kind, institution, summary,
   items, transcription). The image is paid for once; history and plans carry text; the keyword path works without a
   model.
3. **A file alone is a question.** An empty message with a file asks the model to say what the document is, with its
   key numbers, and to offer the write that fits it, or Tài liệu.
4. **Two writes behind Xác nhận.** `them_tu_tep` saves the reading's items (statement holdings through
   `save_holdings`, the others through the declare writers, so each is recorded once); `luu_tai_lieu` keeps the file
   in Tài liệu. **The confirm line lists every item and the total**: that line is the evidence the page used to give,
   so the client's uploads no longer need their page. Each write is read back before it is said done.
5. **Kept briefly, sealed, owned.** The file and reading are sealed with `MF_DATA_KEYS`, belong to the person and the
   client they were attached for, and expire after 24 hours. With no client model an image is refused with the
   reason; text files are still read by the rules.

## Consequences

- A savings receipt photo becomes a deposit in two clicks; a bill is answered from its transcription.
- A model reading can be wrong; the confirm line and its total are where the person catches it, and nothing is
  saved without them.
- The on-prem model reads images only when `LLM_ONPREM_VISION=1` (no on-prem vision model has been measured).
