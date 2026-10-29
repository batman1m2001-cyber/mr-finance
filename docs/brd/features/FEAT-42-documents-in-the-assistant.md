# FEAT-42 — Documents in the assistant (attach, paste, photograph)

| | |
|---|---|
| Type | Extension (owner request, 2026-10-26) |
| Requirements | OWN-DOC-01…07 |
| Users | Customer and RM (for the client they serve) |
| Entry points | the assistant panel's paperclip, paste into its box, drop on it; `POST /api/assistant/attach`; the tools `them_tu_tep`, `luu_tai_lieu` |
| Plan | [docs/OCR_PLAN.md](../../OCR_PLAN.md) O1–O7; decision [ADR-0041](../decisions/ADR-0041-the-assistant-takes-files-and-images.md) |
| Status | see [traceability](../requirements/requirements_traceability.md) §5 |

## Purpose

A client holds their wealth on paper and in screenshots: a broker's statement, a savings receipt, a bill, a
valuation certificate. They give it to the assistant as they would to a person — paste it, attach it, photograph
it — with a question or with none, and the assistant says what it is and offers to put it where it belongs.

## Preconditions and permissions

Signed in as the client, or as an RM with the client in their book (`auth.require_client`, as Tải sao kê). The file
belongs to the person and that client; another person's id is refused. An image needs a client model (BRD-NFR-08);
with none, it is refused with the reason and a text file is read by the rules.

## Behaviour

1. **Attach.** Paperclip (on a phone the picker offers the camera), paste or drop; at most 3 files a message. The
   browser shrinks a photo to 2000 px, JPEG. Each file is a chip — a thumbnail or a name — that says *đang đọc…*
   until its reading lands, then its kind ("Biên lai · Vietcombank"). Gửi waits for readings in progress.
2. **Read once** (`src/assistant/attachments.py`). A table → the statement reader; an image or a scanned PDF (text
   under 50 characters, first 10 pages; a longer scan's summary says "Đọc 10/14 trang đầu.") → one vision call: kind (`sao_ke`, `bien_lai`, `hoa_don`, `tai_san`,
   `hop_dong_vay`, `khac`), title, institution, summary, fields, items in one shape, transcription. Amounts written
   in words ("8,5 tỷ") are kept in VND; an item without its amount is dropped.
3. **Ask.** The turn's message carries each reading as text. With no words, the assistant says what the document is
   with its key numbers and offers the write that fits, or Tài liệu.
4. **Save.** `them_tu_tep` — the confirm line lists every item ("cổ phiếu MWG 6.000 cp, giá 68.000") and the total;
   Xác nhận saves them once, however often the file was attached; Huỷ saves nothing. `luu_tai_lieu` keeps the file in
   Tài liệu. Both are read back before "đã xong".
5. **Kept 24 hours, sealed.** After that the file is said to have expired.

## Measured (gate, 2026-10-26)

Five documents made as pages and roughened as phone photos (turned 1–3°, blurred, JPEG 60): a VPS statement, a
Vietcombank receipt, an EVN bill, a valuation certificate, the statement as a scanned PDF. 5/5 read as written with
the right kind (5 requests, US$0.0034, ~4 s each). In the browser on C01, desktop and phone, light and dark: the
receipt pasted alone was named and its deposit offered; Huỷ moved the net worth by 0, Xác nhận by +500,000,000; the
bill's due date answered; the statement's confirm line listed the 3 items and the total; no horizontal scroll. Turns
about US$0.002 each.

A 12-page scanned statement (holdings on pages 1, 6, 10 and 12): pages 1–10 in one call, the three holdings on them
read as written, page 12's FPT not read; 10 s, US$0.0024 (2026-10-26).
