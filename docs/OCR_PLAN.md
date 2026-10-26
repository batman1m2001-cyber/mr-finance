# Any document to the assistant: attach, paste, photograph (2026-10-26)

**Status: done** (O1–O7, 2026-10-26). Gate: 5/5 documents read as written with the right kind (5 requests,
US$0.0034, ~4 s each); in the browser on C01, desktop and phone, light and dark: the receipt pasted alone named and
offered, Huỷ 0, Xác nhận +500,000,000 on the net worth, the bill's date answered, the statement's confirm line with
its 3 items and the total, no horizontal scroll; turns ~US$0.002. Recorded in ADR-0041, FEAT-42, OWN-DOC-01…07.

**Asked** (owner, 2026-10-26). "Copy paste the image, or attach the image into the assistant: the image scan of a
document (hoá đơn, biên lai, mô tả tài sản, sao kê…) for processing." And: "people can ask anything with any image;
it does not even need a text, only the image, and the assistant routes it to the correct flow."

This plan builds on [ASSISTANT_ATTACH_PLAN.md](ASSISTANT_ATTACH_PLAN.md) (2026-10-22, never built) and replaces it
where the two differ: that plan took statement files and never let a model see the file. This one also takes images
and scans, so a model has to read them.

## Today

- **Tải sao kê** (`POST /api/statement`, `statement_flow`): `read_flow` reads a PDF, Excel, CSV or text file, with
  the client model (`ai.client_model()`) or the rules. `save_holdings` then keeps the items as the client's
  `statement` holdings, by key. A scanned PDF has no text, and nothing is read from it.
- **Khai báo qua chat** (`declare_flow`, `src/declare/tools.py`): writers for a property, gold, a holding, a loan, a
  dependent or an income, which write into the client's profile.
- **Bộ nhớ / Tài liệu** (`material_add`): a document kept in the person's knowledge base, searched with `tai_lieu`.
- **The panel takes only text.** The runner already takes a list of messages (`operonx_agents/run/runner.py`), and
  operonx records image blocks in traces as `Media`.
- **Measured 2026-10-26.** A synthetic, slightly rotated Vietcombank savings receipt was sent as a JPEG to
  `llm:copilot` (claude-haiku-5.5): it named the document and bank correctly in 3.4 s. 687 prompt tokens, US$0.0002.
  Reasoning took 237 of the 300 output tokens; the reader switches it off.

## Decisions

- **O-D1 One door for every file.** `POST /api/assistant/attach {client_id, filename, content}`.
  - The same 5 MB limit as the page.
  - Accepted: images (`.jpg .jpeg .png .webp`), statements (`.pdf .xlsx .xlsm .csv .txt`) and documents
    (`.docx .pptx .md .html .htm`).
  - The browser shrinks a photo before sending it: at most 2000 px on the long side, JPEG at 0.85, about 0.3–0.6 MB.
    A 12 MP phone photo therefore fits. The canvas also turns an iPhone's HEIC into JPEG, so the server never sees
    HEIC.
- **O-D2 Read once, when attached.** `attach_flow` reads the file as soon as it arrives. The panel uploads on
  paste, drop or pick, so the reading runs while the person types.
  - The first reading is kept with the file (the old plan's rule). What the person confirms is exactly what is
    saved, because a write's plan runs twice and a second model reading could differ.
  - A table file goes through `read_flow`, unchanged.
  - An image, or a PDF whose text is under 50 characters (a scan), goes to the vision reader. For a scanned PDF,
    pypdf takes the page images (at most the first 3 pages), so no new dependency is needed.
- **O-D3 The vision reader is one model call per file** (`read_image`, an `LLMOp` on the client model).
  - **Resource:** the client model, as for statements (BRD-NFR-08: client data reaches only the client model).
  - **Settings:** reasoning off, `temperature=0`, JSON out.
  - **It returns:**
    - `kind`: `sao_ke | bien_lai | hoa_don | tai_san | hop_dong_vay | khac`;
    - `title` and `institution`;
    - `summary` (2–3 lines);
    - `fields` (amounts, dates, rates, parties);
    - `items`, each in one shared shape with a `type`:
      - `stock`, `cash` and `deposit`: the statements' types;
      - `property`, `gold`, `holding` and `loan`: the declare writers' types;
    - `text`: the transcription, at most 4,000 characters.
  - An image that is not a document (a chart screenshot, a photo) is `khac`, with a description in `summary`.
  - Amounts are in VND, as the statements prompt asks today.
  - **Checks after the read** (`model_read`'s checks, widened): an item without its amount is dropped, and a kind
    outside the list becomes `khac`.
- **O-D4 The turn reads the text, never the image.** The reading goes into the turn's message as one block,
  `[Tệp đính kèm f1 · biên lai · Vietcombank] summary · items · text`.
  - The image is paid for once, at attach. Later turns, the history and the write's two plans carry only text.
  - The keyword path also works with no model.
  - "Ask anything about the image" is answered from the transcription and description.
- **O-D5 An image with no text is still a question.** When the message is empty, the turn's question becomes
  "Người dùng gửi tệp này, không kèm câu hỏi." The instructions then tell the model to:
  - say what the document is, with its key numbers, in 2–3 lines;
  - offer the write that fits it, or Tài liệu when nothing fits.

  This is the routing: the model picks the tool, as it does for a typed question. For a savings receipt it offers
  "ghi làm khoản tiền gửi?"; for an electricity bill, the amount, the due date and "lưu vào Tài liệu?".
- **O-D6 Two writes, both behind Xác nhận** (client, RM: `auth.require_client`, as the page).
  - **`them_tu_tep(file, items?)`** saves the reading's items:
    - `stock`, `cash` and `deposit` as the page does (`save_holdings`, statement holdings by institution);
    - `property`, `gold`, `holding` and `loan` through the declare writers, so a declared item is recorded once
      (`fix/declared-once`).

    The confirm line lists every item and the total. The write is verified by reading the items back by their keys.
  - **`luu_tai_lieu(file)`** keeps the file in Tài liệu, as Bộ nhớ does. It is verified by finding the file listed.

  A reading with no items cannot be saved; the tool says so and offers Tài liệu. The old plan's `doc_tep` is not
  needed, because the reading is already in the message (O-D4).
- **O-D7 What the model may see.**
  - With no client model (template mode, or AI off), text files are read by the rules as today.
  - An image is refused at attach, with the reason: "Ảnh cần mô hình AI đọc; chế độ hiện tại không gửi dữ liệu khách
    hàng cho mô hình."
  - In onprem mode the on-prem model reads images only when `LLM_ONPREM_VISION=1`. We have not measured an on-prem
    vision model, so it is off by default.
- **O-D8 Kept briefly, sealed, owned.**
  - The file and its reading are sealed with `MF_DATA_KEYS`, like the conversation, and kept for 24 hours
    (`assistant_retention`).
  - They belong to the person and to the client they were attached for. Another person's id is refused.
  - Anything older than 24 hours is said to have expired.
- **O-D9 The panel.**
  - Three ways to attach:
    - a paperclip beside Gửi; on a phone the picker also offers the camera;
    - pasting into the text box (a screenshot, or a copied image);
    - dropping a file on the panel.
  - Each file shows as a chip: a thumbnail for an image, otherwise a name. The chip shows *đang đọc…* until the
    reading lands, then the kind ("Biên lai · Vietcombank"), and has ×.
  - At most 3 files per message. Gửi waits for readings still in progress.
  - The person's bubble shows the thumbnails and names.
  - The large type and contrast of the rest of the panel; both themes; phone width.
- **O-D10 Recorded.**
  - **ADR-0041:** the assistant takes files and images. It changes the rule in `src/assistant/actions.py`'s header that the
    client's own uploads stay on their page: the confirm line, which shows every item and the total, is now that evidence.
  - **FEAT-42:** documents in the assistant.
  - **OWN-DOC-01…:** the owner's asks above.

## Steps

- **O1 The file.** `src/assistant/attachments.py` holds the table in the assistant's database (put / get / expire,
  sealed). It also holds `assistant_attach_flow` at `POST /api/assistant/attach` (check → read → keep), the access
  decision and the expiry in retention.
- **O2 The reader.** `read_image`, the vision `LLMOp`, and its checks; scanned PDF to page images; the router (table
  → `read_flow`, image or scan → `read_image`, document → its text).
- **O3 The turn.** The request takes `attachments` (ids, the person's own). The message carries their readings
  (O-D4), an empty message becomes the image-only question (O-D5), and the instructions say how to use a file.
- **O4 The writes.** `them_tu_tep` and `luu_tai_lieu` in the registry, with labels, progress sentences, plan and
  verify; the keyword path's routing for a message with a file.
- **O5 The panel.** Paperclip, paste, drop, chips with thumbnails and *đang đọc…*, the browser's shrinking, the
  bubble; both themes, desktop and phone.
- **O6 The BRD.** ADR-0041, FEAT-42, OWN-DOC rows, FEAT-22/32 notes, the user guide, CHANGELOG.
- **O7 Tests and the gate.**

**Gate.**
- **Five sample documents**, each made as a page, screenshotted and then roughened (turned 1–3°, blurred,
  JPEG 60%) as a phone photo would be:
  1. a VPS holdings statement (the `vps_C01.csv` holdings);
  2. a Vietcombank savings receipt;
  3. an EVN electricity bill;
  4. an apartment valuation certificate (mô tả tài sản);
  5. a scanned PDF statement.
- **Reading:** every holding, balance, rate and date is read as written, on all five, and the kind is right on all
  five.
- **In the browser, on C01's workspace:**
  - Paste the receipt with no text: the answer names it, gives its amount, rate and maturity, and offers the
    deposit.
  - Xác nhận puts it on Dữ liệu chi tiết tài sản and the net worth moves. Huỷ saves nothing.
  - Attach the bill with "hạn trả khi nào?": the date is answered.
  - Attach the statement with "thêm vào tài sản": the confirm line lists the holdings and the total.
- **Refusals:** another person's id is refused; in template mode an image is refused with its reason; at rest the
  file is sealed.
- **Screens:** desktop and phone, light and dark, with no horizontal scroll.
- **Cost:** model requests and `usage.cost` are reported for the whole gate.
