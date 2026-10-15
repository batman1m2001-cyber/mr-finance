# FEAT-32 — OneWealth Copilot

| | |
|---|---|
| Type | Extension (redesign kit), built 2026-10-16 (plan phase K5) |
| Requirements | KIT-COPILOT-01…06; keeps BRD-BR-11, BRD-NFR-08, BRD-RULE-ZONE-04 |
| Users | Every role |
| Entry points | “✦ Hỏi OneWealth” on every page → [SCR-CL-10](../ux/screens/client.md#scr-cl-10--onewealth-copilot-panel-all-roles); `POST /api/copilot {question, role, client_id, scope, route, confirm}` |
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
- **Act** (`tools.py`): 11 tools. Read — tong_quan (dashboard), dong_tien (flows), chu_y (feed), muc_tieu (goals),
  tac_dong (role-filtered impact), hom_nay (RM), hop_tin (CIO), tin_bi_giu (Compliance), mo_trang (navigate).
  Write — duyet_de_xuat (RM; review_flow with the RM's id), lay_tin (CIO; ingest). A tool outside the role is
  refused; a write first returns what it will do and waits for **Xác nhận**; the confirmed call runs through the
  same served graph, whose own role checks apply; failures are reported as failures.
- **Answer**: fixed templates over the tool's result; each answer links to the page that holds its evidence,
  shows “Mô hình thấy gì” (the scrubbed text and the router), and follow-up suggestions.
- **Panel** (`web/copilot.js`): floating button, side panel (full width on phones), page context, progress,
  confirm / cancel, Esc closes; the conversation is kept in `sessionStorage` per role for this tab only.

## Implementation
`src/copilot/{scrub,tools,router,ops,graph}.py`; service `copilot` in `app/main.py`; resource `llm:copilot`
(`resources.yaml`), `LLM_MODEL_COPILOT` in `.env.example`; `web/copilot.js`, mounted by `web/shell.js`;
`.cp-*` styles in `web/core/tokens.css`.

## Acceptance and tests
`tests/test_copilot.py`: the router prompt carries no fixture name, digit or market code for every person in
the fixtures (control: the unscrubbed prompt does); the live router (fake model) receives only scrubbed text;
an off-catalogue reply falls back, labelled; a client cannot run a CIO tool, even by sending a confirm; no write
before confirm, the confirmed write changes the record, a repeated decision is reported as failed; a failing
tool and an unknown question; the endpoint. UI driven in a browser: ask, forbidden badge, RM confirm → record
approved, navigate (2026-10-16).

## Limitations
- **One live run recorded (2026-10-16)** with the model configured for the live demo (`anthropic/claude-haiku-5.5`
  through the configured OpenAI-compatible endpoint), three client questions in one process: “Dòng tiền tháng 8 của
  Nguyễn Minh Khoa thế nào?” → seen as “Dòng tiền tháng <số> của <người> thế nào?” → `dong_tien` (router: llm);
  “Có gì đáng lo với tài sản của tôi không?” → `chu_y` (llm); “Cho tôi xem đồ thị tin tác động” → a reply outside
  the catalogue, fallen back to keywords and labelled (→ `tac_dong`; an earlier call chose `mo_trang`, page
  `do-thi`). The prompts held no name and no digit. `LLM_MODEL_COPILOT` is not set on the live server, so it
  still routes by keywords.
- Answers are template-shaped, not free prose; Investigate/Analyze are the existing reads, not new analysis.
- Writes cover two tasks; research release, news dismiss/release and declarations are not Copilot tools yet.
