# Assistant sessions, history and compaction — plan

Owner request: [`2026-10-17_assistant_sessions.md`](brd/sources/owner_requests/2026-10-17_assistant_sessions.md)
→ OWN-SS-01…08 ([owner_requirements.md](brd/requirements/owner_requirements.md)), feature FEAT-37. Experiment
branch `exp/graph-workspace` (with the graph workspace); no PR to main.

**Status (2026-10-17): S0 done.**

## 1. Audit — what exists (read 2026-10-17)

| Asked | What exists | Gap |
|---|---|---|
| Create, switch | A3: a conversation per first message; the panel's clock button lists and opens them; “+ Mới” | the list is a bare list, the New Chat is a small link |
| Rename, archive | delete only (`conv.delete`, scrubbed from the disk, audited) | no rename, no archive |
| Titles | the first 80 characters of the first question | not concise, never refined |
| Persistence | `turns` keeps the question and the answer as shown (steps, cards, citations, mode, usage) with its time; the latest conversation reopens within a day, on any device | a turn is recorded only when it ends (`ops.finish`): a refresh mid-answer loses the question and the tools that ran |
| Storage | `data/assistant.db`, SQLite WAL, measured for this deployment (ADR-0027): one `operonx serve` process on one host, ~127 turns/s against a busy hour of ~10; behind `Session`/`StateStore` for the bank (PostgreSQL export, ADR-0025) | none: keep it, add columns |
| Two memory levels | global: A4 items (`operonx_agents_memory`) in the reading model's instructions (≤ 15) and the `nho_lai` / `ghi_nho` / `quen` / `tim_lich_su` tools; per session: the model's side `conv:<id>:<mode>` | `tim_lich_su` searches every conversation; nothing reads back the current one |
| Isolation | every read and write keyed by the owner the server resolved (`auth.acting_id`) and the role; another person's id answers “Không có cuộc trò chuyện này” | multi-user tested with one signed-in person only |
| Compaction | `ContextPolicy(window=24_000, compact_at=0.75, keep_recent=8)`; a `summary` item in the session; every item kept; the panel says a turn compacted | the summary is upstream's free-form “notes” (`compaction.summary_prompt`); it is not shown, not structured, not readable by the person |
| Goal and summary per session | — | none |

## 2. Decisions

1. **Storage stays `assistant.db`.** New columns on `conversations`: `title_auto` (1 while the title is generated),
   `archived` (time or null), `goal`, `summary`, `summary_at`. Added by the same idempotent `alter table` as A3's
   `session_id`. Text columns sealed like the title.
2. **A turn is written when it starts.** `turns` gets `status` (`running`, then the answer's status). The question
   is stored at the start; each finished step updates the row; `finish` completes it. A stream cut by the client
   (refresh, closed tab) marks it `interrupted` with the steps that ran. A `running` row older than the run's wall
   clock (+15 s) is shown as interrupted too (the server died). The model's session is not changed: the cut
   exchange never reached it, and the panel says so.
3. **Titles and goals by the copilot model, after the answer.** One small request (≤ 120 output tokens) returns
   `{title ≤ 7 words, goal ≤ 1 sentence}` after the first answer, again after the 4th turn and after every compaction.
   It runs after the answer is sent, so it adds nothing to the reply latency. Stream: a `session` event updates the
   panel. **Template mode never sends anything**: the model may not read the question. The title is then the first
   clause of the question, cut at a word boundary (≤ 48 characters), and no goal is written. A title the person set
   (`title_auto = 0`) is never replaced. With no model configured, the same local title.
4. **Structured compaction, through our own summariser.** `turn.Summarizer(Model)` replaces upstream's preamble with
   a fixed structure: Mục tiêu · Quyết định · Sở thích và giới hạn người dùng nêu · Việc còn dở · Thực thể (mã, tên
   tài sản, mục tiêu, tin) · Kết quả công cụ (công cụ, ngày số liệu) · Tham chiếu (trang, id để đọc lại). No change
   upstream (the Operon tree is not ours to edit now). The summary is copied to `conversations.summary` (sealed);
   its goal line becomes the session's goal when none is set.
5. **Recoverable.** Nothing is deleted by compaction: the session keeps every item and `turns` keeps every message.
   A new read tool, `doc_lai_phien` (all roles), returns the current conversation's turns, by keyword or the last n.
   With it, the model reads back what the summary left out. In template mode it returns the tools' statuses only, as
   the rest of template mode does. The panel shows the summary under the session's title (“Tóm tắt phiên”).
6. **Archive hides, delete erases.** Archived sessions leave the list and the resume, stay searchable on Bộ nhớ, and
   come back with one click. Retention treats them like the rest.
7. **New Chat** clears the panel's conversation only: the next message starts a new session. Global items stay in
   the instructions; earlier sessions stay listed.
8. **The panel** (docked in the workspace and floating for staff): a session bar shows the title (rename in place),
   the goal and “Tóm tắt phiên”. A prominent **Cuộc trò chuyện mới** button sits beside it. The history view is a
   compact list with search, grouped Hôm nay / Hôm qua / 7 ngày qua / Cũ hơn, each row showing title, goal, time and
   turns, with Đổi tên / Lưu trữ / Xoá. An “Đã lưu trữ (n)” view has Khôi phục.
9. **Paid calls**: titles only, about US$0.0002 each at the copilot model's price, at most three per session; tests
   use the scripted model; one live check, counted and reported.

## 3. Phases

| Phase | What | Gate |
|---|---|---|
| S0 | BRD: source, OWN-SS-01…08, FEAT-37 section, this plan | `scripts/check_brd_docs.py` 0 errors |
| S1 | Store: columns; rename, archive, restore; turns written at start, steps as they end, interrupted on a cut stream or a stale run; `open` returns them; owner and role on every new action | tests: rename/archive/restore owner-only; a stream cut after a tool shows the question and the step after reopening; two signed-in clients never see each other's sessions |
| S2 | Titles and goals: the post-answer request, the template-mode local title, refinement at turn 4 and after compaction, the `session` event, rename protection | tests: generated title and goal (scripted), template mode sends nothing, a renamed title is kept, refined later |
| S3 | Structured compaction (`Summarizer`), the summary kept on the conversation, `doc_lai_phien`, continuation | tests: a long session compacts into the seven sections, the next turn continues from it, the read-back tool returns a turn the summary dropped, owner-only |
| S4 | The panel: session bar, New Chat, history with search, groups, rename, archive, restore, delete; docked and floating; desktop and phone screenshots | UI tests: refresh restores the session and an interrupted turn; switch; rename; archive and restore; New Chat keeps global memory |
| S5 | Verification: the full suite; one live title on the real model (cost reported); FEAT-37, assistant.md §5, traceability, CHANGELOG, report | OWN-SS-01…08 implemented_verified |

## 4. Out of scope

- Moving conversations between roles, or sharing a session with another person.
- Resuming a run cut mid-stream: the person asks again. The panel says what had run.
- A plain-text index for history search (the text is sealed; see FEAT-37 Limitations).
