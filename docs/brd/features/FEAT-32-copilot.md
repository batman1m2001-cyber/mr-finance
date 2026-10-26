# FEAT-32 — OneWealth Copilot

| | |
|---|---|
| Type | Extension (redesign kit), built 2026-10-16 (plan phase K5); Copilot 2.0 in UI redesign R5 (2026-10-16) |
| Requirements | KIT-COPILOT-01…06, OWN-UI-05; keeps BRD-BR-11, BRD-NFR-08, BRD-RULE-ZONE-04 |
| Users | Every role |
| Entry points | “✦ Hỏi OneWealth” on every page → [SCR-CL-10](../ux/screens/client.md#scr-cl-10--onewealth-copilot-panel-all-roles); `POST /api/copilot {question, role, client_id, scope, route, confirm, goals}` |
| Plan | [docs/REDESIGN_KIT_PLAN.md](../../REDESIGN_KIT_PLAN.md) phase **K5**, D1–D3; [ADR-0012](../decisions/ADR-0012-the-copilot-routes-and-never-reads-client-data.md) |
| Status | see [traceability](../requirements/requirements_traceability.md) §4 |

## Behaviour
`copilot_flow`: check → **scrub** → **route** → **act** → **answer**.
- **Scrub** (`src/copilot/scrub.py`): digit runs, upper-case codes, every fixture person's full name and its last
  two words (accent-insensitive) become `<số>`, `<mã>`, `<người>`. Example: “Dòng tiền tháng 8 của Nguyễn Minh
  Khoa?” → “Dòng tiền tháng <số> của <người>?”.
- **Route** (`router.py`): the keyword router (default, labelled “bộ định tuyến từ khóa (mô phỏng)”) or, when
  `LLM_MODEL_COPILOT` is set and AI is on, `llm:copilot`, which receives only the scrubbed question, the route's
  section names (ids dropped), the role and the catalogue (`router.prompt`). Stricter than ADR-0012: no entity id
  reaches the model; our code takes the client from the page and parses the month from the original question.
  A reply outside the catalogue falls back to keywords, said so.
- **Act** (`tools.py`): 13 tools. Read — tong_quan (dashboard), dong_tien (flows), chu_y (feed), muc_tieu (goals,
  the ones followed in the browser when `goals` is sent), tac_dong (role-filtered impact), **dieu_tra** (an approved
  event's path from the impact graph: news, scenarios, factors, assets with this event's share, goals), **kich_ban**
  (a stress test through the planning page's `scenario_flow`: stock market, corporate bonds, property freeze, rates,
  USD — the router chooses among plain words, never an id with digits), hom_nay (RM), hop_tin (CIO), tin_bi_giu
  (Compliance), mo_trang (navigate).
  Write — duyet_de_xuat (RM; review_flow with the RM's id), lay_tin (CIO; ingest). A tool outside the role is
  refused; a write first returns what it will do and waits for **Xác nhận**; the confirmed call runs through the
  same served graph, whose own role checks apply; failures are reported as failures.
- **Answer**: fixed templates over the tool's result; each answer links to the page that holds its evidence,
  shows “Mô hình thấy gì” (the scrubbed text and the router), and follow-up suggestions (“Bạn có thể muốn:”).
  Since R5 an ok answer also carries `as_of` (the data's own date, when the tool has one), `answered_at`, `sources`
  (what it read: records, outlets, counts) and a `card` the panel draws — `figures`, `list` (chips, progress, a row
  marks its page element), `bars` or `chain`. Every call — answered, refused, unknown or confirmed — is one row in the
  audit chain (`copilot.ask`: the demo user, the tool, the status, the router and the question as the router saw it,
  scrubbed); the answer names its `audit_seq`.
- **Panel** (`web/copilot.js`): page context, progress, confirm / cancel. Docked in every role's Trợ lý tab since
  2026-10-18 (the floating button and its Esc-to-close are removed, owner's word); conversations live on the server
  (FEAT-37).
- **States and evidence highlight** ([FEAT-33](FEAT-33-living-interface.md), 2026-10-16): the panel shows
  idle / busy / ok / error / pending from the request itself; an ok answer carries `focus`, the keys of the page
  elements it was read from, which the page marks for 2.6 s (“Chỉ trên trang” shows them again).

- **One tool registry** (ASSISTANT_PLAN A1, 2026-10-17, ADR-0032): the thirteen tools moved into
  `src/assistant/` unchanged and 12 more wrapped from served graphs (six reads, six writes; 25 in all, by role).
  Every write has a plan (the line confirmed, arguments resolved on the server; it writes nothing) and a verifier
  that reads the state back: a write that answered but did not land is said as “Đã gửi nhưng chưa xác nhận được
  kết quả: …”, never as done — in the Copilot too. Each tool has a timeout. `agent_tools(role)` gives the role's
  tools to an operonx-agents agent: writes park the run until the person approves (assistant.md §4).

- **The assistant behind the panel** (A2, 2026-10-17): the panel posts to `POST /api/assistant`.
  - An operonx-agents run over the role's registry tools takes as many steps as the question needs. A write waits
    with its plan and a Xác nhận / Huỷ pair; the answer resumes the parked run.
  - The answer comes as the model's prose (bold and lists only, escaped), each step's card and label ("Các bước"),
    every page it read ("Mở … →"), the sources and the data's date.
  - The badge says how it was written: `mô hình <model>`, `mẫu cố định` (the barrier keeps client data from the
    model) or `dự phòng: từ khóa` (no model answered: the Copilot's path).
  - Switching role with the panel open now shows that role's conversation.

## Next (ASSISTANT_PLAN A3–A5)

The Copilot becomes the assistant's front end ([assistant.md](../architecture/assistant.md), ADR-0026, ADR-0032):
one tool registry by role, multi-step turns on `operonx-agents`, writes confirmed (the run parks) and verified,
answers citing tools, pages, passages and web sources; `POST /api/copilot` stays as the template path and the
fallback. Conversations: FEAT-37; knowledge and web: FEAT-38.

## Implementation
`src/copilot/{scrub,tools,router,ops,graph}.py` (`tools.py` now names its thirteen in the registry);
`src/assistant/{base,tools,actions,registry}.py` (A1); `src/assistant/{turn,ops,graph}.py`, service `assistant`,
`scripts/eval_assistant.py`, `data/assistant_eval.json` (A2); service `copilot` in `app/main.py`; resource `llm:copilot`
(`resources.yaml`), `LLM_MODEL_COPILOT` in `.env.example`; `web/copilot.js`, mounted by `web/shell.js`;
`.cp-*` styles in `web/core/tokens.css`.

## Acceptance and tests
`tests/test_copilot.py`: the router prompt carries no fixture name, digit or market code for every person in
the fixtures (control: the unscrubbed prompt does); the live router (fake model) receives only scrubbed text;
an off-catalogue reply falls back, labelled; a client cannot run a CIO tool, even by sending a confirm; no write
before confirm, the confirmed write changes the record, a repeated decision is reported as failed; a failing
tool and an unknown question; the endpoint. R5: an answer's as-of, sources and card; dieu_tra equals the impact
graph (event type for the client, headline for staff); kich_ban equals scenario_flow and picks the scenario by
words; every call is in the audit chain, which verifies, with the scrubbed question; the followed goals.
`tests/ui/test_copilot_ui.py::test_answers_show_their_card_their_time_and_sources_and_offer_next_steps`.
A2: `tests/test_assistant.py` (scripted model): two tools in one turn and their citations; the turn audited
without its text; a write waits for the person who asked, runs once and is checked; a declined write runs nothing;
the barrier off; no model and a failing model fall back; a tool the role lacks is not offered; the endpoint;
`tests/ui/test_copilot_ui.py::test_the_assistant_asks_before_a_write_and_shows_its_steps`; the real-model eval
(docs/brd/testing/assistant_eval.md, 10/10).
A1: `tests/test_assistant_tools.py` — the catalogue is whole (every write has a setup in the test, a plan and a
verifier); every tool refused to every role it is not for (not offered, and refused when its function is called
with that person); every read answers or says why not; every write: planning writes nothing, the confirmed write
changes the records and its verifier confirms, and the same answer without its effect is NotConfirmed; the Copilot
reports an unconfirmed write as failed; an agent's write parks, Approve runs it verified and Deny runs nothing; with
the barrier off the model reads only statuses.

## Limitations
- **One live run recorded (2026-10-16)** with the model configured for the live demo (`anthropic/claude-haiku-5.5`
  through the configured OpenAI-compatible endpoint), three client questions in one process: “Dòng tiền tháng 8 của
  Nguyễn Minh Khoa thế nào?” → seen as “Dòng tiền tháng <số> của <người> thế nào?” → `dong_tien` (router: llm);
  “Có gì đáng lo với tài sản của tôi không?” → `chu_y` (llm); “Cho tôi xem đồ thị tin tác động” → a reply outside
  the catalogue, fallen back to keywords and labelled (→ `tac_dong`; an earlier call chose `mo_trang`, page
  `do-thi`). The prompts held no name and no digit. `LLM_MODEL_COPILOT` is not set on the live server, so it
  still routes by keywords.
- Answers are template-shaped, not free prose; Investigate (dieu_tra) and Analyze (kich_ban) read existing graphs —
  no new analysis is invented.
- Writes cover two tasks; research release, news dismiss/release and declarations are not Copilot tools yet.
- Files (2026-10-26, FEAT-42, ADR-0041): the panel takes up to 3 files a message — paperclip, paste, drop; each is
  read once when attached and enters the turn as text; a file alone routes itself; `them_tu_tep` and `luu_tai_lieu`
  save it behind Xác nhận.
- Voice (2026-10-27, FEAT-43): the microphone button talks to the panel — the question asked after 1.2 s of
  quiet goes through the same `send`, flagged `voice`; the answer is read aloud sentence by sentence.
