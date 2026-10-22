# The assistant takes a file: "dùng file này add vào tài sản cho tôi" (2026-10-22)

**Asked** (owner, 2026-10-22). Some pages take a file (Dữ liệu chi tiết tài sản's *Tải sao kê*: PDF, Excel, CSV).
The owner wants to give the same file to the assistant: attach it in the panel and say "dùng file này add vào tài sản
cho tôi". It answers with what it read, and adds it only after the person confirms.

## Today

- **Tải sao kê** (`POST /api/statement`, `statement_flow`): `read_flow` reads the file (the client-AI model when
  configured, else the rules), then `save_holdings` keeps the items as the client's `statement` holdings, by key.
- **Bộ nhớ** (`POST /api/assistant/memory`, `material_add`): a document goes into the person's knowledge base. The
  assistant searches it with `tai_lieu`.
- **The panel has no file.** The assistant's actions (`src/assistant/actions.py`) leave "the client's own uploads"
  to their page *deliberately*: the person reads the evidence there.

## Decisions

- **A file is attached once and read once.** `POST /api/assistant/attach` takes it, checks it with the page's limits
  (5 MB; a statement is `.pdf .xlsx .xlsm .csv .txt`; a document can also be `.docx .pptx .md .html .htm`), and keeps
  it on the server for 24 hours. It is sealed with `MF_DATA_KEYS` like the conversation, and it belongs to the person
  and the client it was attached for. The first read is kept with it, so the items the person confirms are the items
  saved. A write's plan runs twice (the line to confirm, then the run), and a model's second reading could differ.
- **Three tools** (client, RM: as the page, `auth.require_client`):
  - `doc_tep` (read): what the file holds. A statement gives its items and total; anything else, its kind and that
    it can go to Tài liệu.
  - `them_tai_san_tu_tep` (write): the confirm line lists the items and the total. Approved, it saves them as the
    page does (`save_holdings`); verified by reading the holdings back by their keys.
  - `luu_tai_lieu` (write): the file into Tài liệu, as Bộ nhớ does; verified by finding it listed.
- **The deliberate rule changes, and is recorded** (ADR-0038). Leaving uploads to the page was about reading the
  evidence first. The confirm line now *is* that evidence: every item and the total before anything is written, and
  nothing is written without Xác nhận.
- **What the model sees**: the file's name and its id (scrubbed in template mode, like the message), and in model
  mode the tool's result (the items). Never the file itself. In template mode the answer is the tools' own texts.
- **Nothing read, nothing saved**: a file whose items cannot be read (a scan, an unknown layout) is said so, and the
  write refuses; a file that is not a statement is offered to Tài liệu.
- **Without a model** (the keyword path): a message with a file goes to the same tools. Words about assets
  ("tài sản", "thêm", "add", "nhập") lead to `them_tai_san_tu_tep`, words about keeping it ("lưu", "tài liệu") to
  `luu_tai_lieu`, anything else to `doc_tep`. The Copilot's confirm runs the write, with the file's id as its only
  argument.
- **The panel**: a paperclip beside Gửi, and a file dropped on the panel attaches too. Each file shows as a chip
  (name, ×) until the message is sent; the person's bubble names the files. At most three files a message.

## Steps

- **T1 The file.** `src/assistant/attachments.py`: the table (in the assistant's database), put / get / read-once /
  expire; `assistant_attach_flow` at `POST /api/assistant/attach`; expiry in `assistant_retention`; the access decision.
- **T2 The tools.** `doc_tep`, `them_tai_san_tu_tep`, `luu_tai_lieu` in the registry; their labels and progress
  sentences. The request takes `attachments` (ids, the person's own), the turn's message names them, and the
  instructions say how to use them.
- **T3 Without a model.** The fallback's routing for a message with a file; the Copilot's confirm passes the file's
  id.
- **T4 The panel.** Paperclip, drop, chips, the bubble's file names, both themes and a phone.
- **T5 The BRD.** OWN-AT-01…, ADR-0038 (amends ADR-0032's note on uploads), FEAT-22 and FEAT-32, the user guide,
  CHANGELOG; the `actions.py` note.
- **T6 Tests and the gate.**

**Gate.** In the browser, on a client's workspace: attach `vps_C01.csv`, type "dùng file này add vào tài sản cho
tôi". The confirm line lists its holdings and total; Xác nhận saves them (they show on Dữ liệu chi tiết tài sản,
the net worth moves) and Huỷ saves nothing. This works with the model and with the keyword path. An unreadable file
is said so and saves nothing. Another person's attachment id is refused. At rest the file is sealed. In template
mode no file content reaches the model. Desktop and phone, light and dark.
