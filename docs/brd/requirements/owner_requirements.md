# Requests of the product owner — `OWN-<area>-nn` (approved extensions)

Layer A, fourth source: requests the product owner gives directly, kept verbatim in
[`../sources/owner_requests/`](../sources/owner_requests/) (SRC-05). They are **not in the BRD**; the owner asked for
them, so they are approved for building. Each request is split into testable requirements below, in the owner's
words where possible.

Status: [`requirements_traceability.md`](requirements_traceability.md) §5.

## NE — News as evidence, not forecast (2026-10-28)

Source: [`2026-10-28_news_evidence.md`](../sources/owner_requests/2026-10-28_news_evidence.md); the BRD verbatim at
[`docs/NEWS_EVIDENCE_BRD.md`](../../NEWS_EVIDENCE_BRD.md) (§ below are its sections); feature
[FEAT-45](../features/FEAT-45-news-evidence.md); screen [SCR-CIO-16](../ux/screens/cio.md#scr-cio-16--bằng-chứng-tin-news-evidence). Extends FEAT-25 (alerts) and FEAT-04 (the CIO agent); questions [Q-30](open_questions.md#q-30--the-news-evidence-thresholds-and-who-sees-what).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-NE-01 | A news item's effect on a price is shown as direction · time · evidence, never as a forecast figure; every other figure traces to known data (loan terms, tax rules, drift, liquidity, LTV) | BRD N1, N2, §8.2, §13.1 | documented |
| OWN-NE-02 | Statistics when there are at least 8 precedents and the same-way rate beats the base rate by 10 points; the statistics always say n and the base rate; with fewer the item goes qualitative | BRD N3, §5, §13.2 | documented |
| OWN-NE-03 | With statistics, the direction shown is the computed one, not the agent's; the agent's is kept as a note for the CIO | BRD N5, §9 rule 7, §13.3 | documented |
| OWN-NE-04 | A qualitative frame has every required field: event type, channels, mechanism, targets, direction, what changes, timeframe, what to watch, precedents — each precedent with event, outcome and difference | BRD §6, §13.4 | documented |
| OWN-NE-05 | The checks of §9 send a frame back with the reasons, at most twice: values from the fixed catalogue, required fields, no forecast figure, no FR-604 words | BRD §9 | documented |
| OWN-NE-06 | A precedent without a source never shows “Nguồn”; the “chưa có nguồn” mark appears to the CIO only | BRD §6, §13.5, Q6 | documented |
| OWN-NE-07 | The agent reads the news item (title, summary, outlet, date) and the catalogue, never a client's data; matching news to clients is a rule | BRD N4, §4, §13.6 | documented |
| OWN-NE-08 | News is matched to a client by rule, on the labels the client has (assets, loans, plans), the same way every run; each alert names the labels it matched | BRD §7, §13.7 | documented |
| OWN-NE-09 | A plan label read from a goal's name is marked inferred; the RM confirms the goal before the client reads anything; the client's message has no FR-604 or AML wording (Example 4: news → plan label → a study-abroad goal → an RM task) | BRD §7, §10 ex. 4, §13.8, §13.9 | documented |
| OWN-NE-10 | What each role sees: the client and the RM read approved frames without the CIO's marks; the CIO reads every frame, the branch, the review and the thresholds on Bằng chứng tin | BRD §8.2 | documented |
| OWN-NE-11 | Every frame passes the CIO: approve, return to the agent, reject; a returned or rejected frame leaves the chart until approved again; each decision is in the audit log | BRD N6, §4 | documented |
| OWN-NE-12 | The agent reads a real news item, picks its event type from the catalogue and drafts the frame (a new type goes qualitative, direction Chưa rõ); the draft waits for the CIO and a draft that failed the checks cannot be approved | BRD §4, §15 P1 | documented |
| OWN-NE-13 | The full event-type catalogue: the CIO adds a type or precedent dates to one; with enough precedents the type gets the statistics branch on VN-Index, SJC gold, USD/VND and the 10-year yield | BRD §5, §15 P2 | documented |
| OWN-NE-14 | AI suggests a plan label (purpose, country) for a goal the RM has not declared and the rule cannot read; nothing is kept until the RM saves it | BRD §7, §15 P2 | documented |
| OWN-NE-15 | The changes to *Luồng end-to-end mới* are written down section by section | BRD §11, §15 P2 | documented |

## AA — Asset allocation in Wealth Planning Advisor (2026-10-28)

Source: [`2026-10-28_asset_allocation.md`](../sources/owner_requests/2026-10-28_asset_allocation.md); the BRD verbatim at
[`docs/ASSET_ALLOCATION_BRD.md`](../../ASSET_ALLOCATION_BRD.md) (§ below are its sections); feature
[FEAT-44](../features/FEAT-44-asset-allocation.md); screen [SCR-CL-13](../ux/screens/client.md#scr-cl-13--phân-bổ-tài-sản-asset-allocation). Extends FEAT-26 (plan) and FEAT-27 (review queue); questions [Q-28](open_questions.md#q-28--which-liquidity-target-is-the-default), [Q-29](open_questions.md#q-29--who-approves-an-allocation-action).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-AA-01 | Every asset of the client sits in exactly one of three buckets — Thanh khoản, Di sản, Tăng trưởng; the buckets plus the loans equal the net worth of Tổng quan | BRD §5, §13.1 | documented |
| OWN-AA-02 | A cash-flow table over H years: certain income only (wages, pensions, rent), spending, dated events, loan payments; its lowest point; a line for a +1 point loan rate | BRD §6.1 | documented |
| OWN-AA-03 | The Liquidity target is computed three ways (A, B, C) from the table shown, all three on screen; the default is the owner's to choose | BRD §6.1, §13.2, Q-28 | documented |
| OWN-AA-04 | A model portfolio per risk level, tilted by the CIO from an approved view: 2 points a tilt, at most ±5, inside the level's range, summing to 100 % | BRD §7, §13.4 | documented |
| OWN-AA-05 | Liquidity is filled first; Growth is rebalanced to the tilted model on what is left; buys equal sells plus the cash waiting | BRD AA-N2, §8.1, §13.3 | documented |
| OWN-AA-06 | Wait, sell or borrow are compared to fill Liquidity, each with why; borrowing only when §8.2's conditions hold; the loans the client has are read (prepay, keep, rate shock) | BRD §8.2, §13.6, §15 P1 | documented |
| OWN-AA-07 | Liquidity is laddered in deposits and government bonds by when the money is needed | BRD §6.1, §15 P1 | documented |
| OWN-AA-08 | The Legacy floor, target and gap; a Legacy asset is never sold — a gap is talked over (insurance with a beneficiary, savings) | BRD AA-N3, §6.2, §13.5 | documented |
| OWN-AA-09 | The return a goal needs against the model's expected one; when it needs more, the choices are said (save more, retire later, retake the test) and the risk level is never raised | BRD AA-N4, §6.3, §13.5 | documented |
| OWN-AA-10 | Each action is checked PASS, WARN or BLOCK (the level's range, excluded classes, concentration, Liquidity left short, an old or a simulated risk test); a BLOCK never reaches the client; each action says why and the view behind it | BRD §9, §13.7 | documented |
| OWN-AA-11 | Actions are at asset-class level, no ticker, no target price, no FR-604 words; every number from a formula, the same answer for the same input | BRD AA-N1, AA-N5, AA-N6, §13.8, §13.10 | documented |
| OWN-AA-12 | SCR-CL-13 shows the three buckets with targets and gaps, the cash-flow table, the model and its tilts, the actions with their checks and how each number is worked out; the RM sends the actions to the specialist review queue (FEAT-27) | BRD AA-N7, §10, §4 | documented |
| OWN-AA-13 | The worked example K-7F3A gives the BRD's numbers: 19 / 11; 40,5 / 60 / 16–24; 31; 3,7 / 2,9 / 2,9 / 3,7; 8,3 % / 9,2 % | BRD §11, §13.9 | documented |
| OWN-AA-14 | The CIO approves or rejects each action of a sent allocation; the client sees only the approved ones | BRD §14 Q2, §15 P2 | documented |
| OWN-AA-15 | An RM moves a holding to another bucket with a reason; the CIO sees every move | BRD §15 P2 | documented |
| OWN-AA-16 | Black–Litterman as a second model method beside the ±2-point tilts, inside the same guards; the CIO picks the one in force | BRD §5, §15 P2 | documented |
| OWN-AA-17 | The household and the Growth model read by the 11 asset classes the news labels use | BRD §15 P2 | documented |

## DOC — Any document to the assistant (2026-10-26)

Source: [`2026-10-26_documents_to_the_assistant.md`](../sources/owner_requests/2026-10-26_documents_to_the_assistant.md); plan
[`docs/OCR_PLAN.md`](../../OCR_PLAN.md); decision
[ADR-0041](../decisions/ADR-0041-the-assistant-takes-files-and-images.md); feature [FEAT-42](../features/FEAT-42-documents-in-the-assistant.md).
Extends AS (FEAT-32) and statement reading (FEAT-22).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-DOC-01 | The assistant takes a file three ways — the paperclip (the camera on a phone), pasting into its box, dropping on the panel — images, statements and documents up to 5 MB, at most 3 a message; each a chip that says it is being read, then its kind | request 1, plan O-D1, O-D9 | documented |
| OWN-DOC-02 | A photo or a scan of a document (statement, receipt, bill, asset description, loan) is read once, when attached, on the client model: its kind, institution, summary, fields, items in one shape and its text; that first reading is what is saved | request 1, plan O-D2, O-D3 | documented |
| OWN-DOC-03 | Any question about any file is answered from its reading; the image itself is never sent again | request 2, plan O-D4 | documented |
| OWN-DOC-04 | A file sent with no words routes itself: the assistant says what it is, with its key numbers, and offers the write that fits it, or Tài liệu | request 2, plan O-D5 | documented |
| OWN-DOC-05 | What a file shows is saved only on Xác nhận, the confirm line listing every item and the total, once however often the file is attached, and read back before it is said done; or the file is kept in Tài liệu | request 1, plan O-D6 | documented |
| OWN-DOC-06 | With no client model an image is refused with its reason (client data reaches only the client model); a text file is read by the rules and described | plan O-D7, BRD-NFR-08 | documented |
| OWN-DOC-07 | A file and its reading are sealed at rest, belong to the person and the client they were attached for, and expire after 24 hours | plan O-D8 | documented |

## NO — The news sources and the collection figures (2026-10-25)

Source: [`2026-10-25_news_ops.md`](../sources/owner_requests/2026-10-25_news_ops.md); plan
[`docs/NEWS_OPS_PLAN.md`](../../NEWS_OPS_PLAN.md). Extends news ingestion (FEAT-01), the versioned configuration
(FR-701) and View A (OWN-EV-01).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-NO-01 | Admin's Nguồn tin page: each source with its last 7 days; add, edit, switch off, delete and test one (https and a public address only, nothing kept); the changes are proposed as a new version of `news_sources` and approved before the next run reads them | request 1, plan N1 | documented |
| OWN-NO-02 | View A says each day's collection time (the runs' total, over the runs that kept it, with their count) and its first and last run | request 2, plan N2 | documented |
| OWN-NO-03 | View A counts by collection day the news that reached a portfolio (its event has an application run the RMs see with a family whose expected 3-month change is not zero) and the families reached | request 2, plan N3 | documented |
| OWN-NO-04 | View A charts the news kept each collection day, stacked by the four groups and Chưa xếp, with a legend and a tooltip per day | request 4, charts plan C1 | documented |
| OWN-NO-05 | View B charts precision and recall by scoring day, cumulative, per horizon; pending moves are never on it and a day with no denominator is a gap, never 0 % | request 4, charts plan C2 | documented |
| OWN-NO-06 | View B charts the simulated net VND (right − wrong) by group, cumulative by scoring day, labelled simulated and not proof the agent caused it; before the first scoring day it says when that is and draws nothing | request 4, charts plan C3 | documented |

## FB — Business feedback 6: the staff desks (2026-10-24)

Source: [`2026-10-24_business_feedback_6.md`](../sources/owner_requests/2026-10-24_business_feedback_6.md); plan
[`docs/BUSINESS_FEEDBACK_6_PLAN.md`](../../BUSINESS_FEEDBACK_6_PLAN.md). Amends MR (the desks, FEAT-41), WN-10 for the
RM, and the roles of the BRD: Compliance's and the Expert's duties are the CIO's (note 18).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-FB-01 | RM · Sổ khách hàng has no drawing of the families around the RM; its cards stay, a card lists the families to pick | note 1, plan F2 | documented |
| OWN-FB-02 | RM · Khách hàng has no tab Tác động tin, Toàn cảnh, Bản đồ tài chính or Duyệt đề xuất; their addresses open the page that replaced them, or still open for the links that lead there | notes 2 and 6, plan F2 | documented |
| OWN-FB-03 | RM · Khách hàng: Headline news, two inner tabs News and prediction and Đồ thị tác động (was Chi phí chính sách) | note 3, plan F2 | documented |
| OWN-FB-04 | RM · Khách hàng: Wealth planning advisor (was Kế hoạch) | note 4, plan F2 | documented |
| OWN-FB-05 | RM · Khách hàng: Wealth view, two inner tabs Tổng quan and Dữ liệu chi tiết tài sản | note 5, plan F2 | documented |
| OWN-FB-06 | RM: Advisory performance (was Hiệu quả tư vấn), two inner tabs Khách hàng này and Tất cả khách hàng, in the client's view and on the rail; laid out as the owner's mock (Nội bộ, six figures, the AI pipeline of four agents with arrows, the log, the news missed), its sample data marked | note 6, plan F2 | documented |
| OWN-FB-07 | CIO: the desk is called Decision board everywhere (rail, title, heading, hint, back link, the assistant's guide) | note 7, plan F3 | documented |
| OWN-FB-08 | CIO · Decision board: the flow has no Sự kiện stage; Gia đình and RM sit in their own tinted frame | note 8, plan F3 | documented |
| OWN-FB-09 | CIO · Decision board: each decision row shows its impact level (cao, vừa, thấp) and its news group | note 9, plan F3 | documented |
| OWN-FB-10 | CIO · Decision board: the decisions filter by source, domestic or international, relevance and words; 20 rows, then Xem thêm | note 10, plan F3 | documented |
| OWN-FB-11 | CIO · Decision board holds the inbox (source health, filters, Lấy tin ngay, Bỏ tin, Gom thành sự kiện); the Tin tức group is gone, its addresses still open | note 11, plan F3 | documented |
| OWN-FB-12 | CIO · Decision board: Tổng quan tác động tới tài sản, full width, in plain words with no raw ids, a picker of the scenario and the families ranked (Gia đình, Kỳ vọng, % tài sản ròng, P10); no Sự kiện gần đây | note 12, plan F3 | documented |
| OWN-FB-13 | CIO · Decision board has no card Mô hình và dữ liệu or Agent dưới bàn | note 13, plan F3 | documented |
| OWN-FB-14 | CIO · Tác động: a sheet with tabs shows no title or labelled back link above them; Tác động danh mục (was Phơi nhiễm) and Đồ thị lần áp dụng; Lần áp dụng no tab; plain words, P10 explained | note 14, plan F1, F4 | documented |
| OWN-FB-15 | CIO · Nội dung is one tab Bài viết: the CIO writes their own news or policy article, or a letter from approved views, for Private clients only; Nghiên cứu and Chính sách no tab | note 15, plan F4 | documented |
| OWN-FB-16 | CIO: Mô hình and AI & cấu hình move to Admin; the CIO has one plain Hiệu quả page (news collected, forecasts right and wrong, each with its count) | note 16, plan F4 | documented |
| OWN-FB-17 | Customer · Headline News: each row of Tác động lên tài sản ròng is a bar stacked by asset class, each part named with its amount on hover, the parts adding to the row | note 17, plan F5 | documented |
| OWN-FB-18 | No Compliance or Expert account: the roles leave the sign-in, menus and desks; their duties are the CIO's with the four-eyes rule kept (a second CIO approves); a recommendation is the RM's alone | note 18, plan F6 | documented |
| OWN-FB-19 | RM · the desk's list is “Khách hàng đang quản lý” and the desk counts khách hàng, not gia đình | feedback 7 p.1, plan G1 | documented |
| OWN-FB-20 | RM · the net worth on the desk's list is coloured, and shown as a net worth (no “+”) | feedback 7 p.1, plan G1 | documented |
| OWN-FB-21 | RM · no Hôm nay page or rail item; its call list and goal tasks are on the desk, its contact log in the desk's Thông tin (Ghi liên hệ); the old address opens the desk | feedback 7 p.1, plan G2 | documented |
| OWN-FB-22 | RM · the client picker sits in the Khách hàng sheet beside its tabs, not in the top bar; none on “Tất cả khách hàng” | feedback 7 p.2, plan G3 | documented |
| OWN-FB-23 | RM · no “Nội bộ” line on the Khách hàng tabs (the CIO's graph and the Cách tính drawer keep it) | feedback 7 p.3, plan G4 | documented |
| OWN-FB-24 | RM · the client picker in the Advisory performance sheet too, so “Khách hàng này” says which | feedback 7 p.4, plan G3 | documented |
| OWN-FB-25 | RM · the rail's “Sổ khách” is “Tổng quan” | feedback 7 p.1, plan G1 | documented |

## EV — Measuring the news agents (2026-10-24)

Source: [`2026-10-24_agent_evaluation.md`](../sources/owner_requests/2026-10-24_agent_evaluation.md); plan
[`docs/AGENT_EVALUATION_PLAN.md`](../../AGENT_EVALUATION_PLAN.md). Extends news ingestion (FEAT-01) and accuracy
tracking (FEAT-18); no new agent, engine or backtest.

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-EV-01 | Each ingest run keeps its funnel (fetched, too old, duplicates, unique, retained, relevant), start, end, duration, status (ok, partial, failed) and sources; the days' trends count items by collection time, never publication time; a field an old run did not keep is unavailable, never 0 | task §1, plan E1 | documented |
| OWN-EV-02 | The scenario agents' moves at 3d and 1w are scored against the market: precision, recall, missed, direction and error, each with its n, and coverage (due, scored, pending, failed, excluded); the materiality threshold is read from `data/evaluation.json` | task §2.1, plan E2 | documented |
| OWN-EV-03 | Recall against independent material events: each important story of the reference set is followed to where it was lost (not grouped, not a candidate, an earlier or later run, beyond the limit) | task §2.1, plan E2 | documented |
| OWN-EV-04 | The scored moves in VND on the simulated book, through the engine's loadings and the families' holdings frozen each morning: correct, incorrect, missed opportunity, correct negative warnings, the net, by group, each with its n; labelled simulated; a move without a snapshot is unavailable | task §2.2, plan E3 | documented |
| OWN-EV-05 | A verdict once final is kept as scored; a draft made on or before its origin close is excluded; duplicate drafts of one move count once; a pending move is never incorrect; a failed morning or call keeps its reason | task §2.3, plan E2 | documented |
| OWN-EV-06 | Each model call keeps its agent, run, provider, model, tokens in, out and cached, cost, latency, attempt and error; a cost not reported is None, counted apart, never 0; earlier calls are backfilled from the bridge's log only where exactly one line matches | task §4, plan E0, E4 | documented |
| OWN-EV-07 | The trial page has View A Thu thập tin and View B Hiệu quả agent, and each move opens to its news, claim, market, verdict and VND by family; no rate without its denominator | task §3, plan E5 | documented |
| OWN-EV-08 | No market move is read as the agents' gain or loss: every VND figure says it is simulated, "nếu gia đình làm theo toàn bộ" | task §5, plan §2.6 | documented |

## DA — The assistant reads the data itself (2026-10-24)

Source: [`2026-10-24_assistant_data_access.md`](../sources/owner_requests/2026-10-24_assistant_data_access.md); plan
[`docs/ASSISTANT_DATA_PLAN.md`](../../ASSISTANT_DATA_PLAN.md); decision
[ADR-0040](../decisions/ADR-0040-the-assistant-queries-role-scoped-read-only-views.md). Extends AS (FEAT-32).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-DA-01 | A number shown or said as a total comes from a count in the database, one function shared by the page and the assistant (news, alerts, search, reviews); a page of rows says "40 / 1.415" | plan §2, D1 | documented |
| OWN-DA-02 | The assistant has one tool, `truy_van`, that runs a SQL `select` on views built for the role and person signed in (CIO, RM, client, Compliance/Admin), never on a real table; another family's rows, held news, accounts, e-mail addresses and the audit chain's hashes are never visible | plan §3.1, D2 | documented |
| OWN-DA-03 | The query runs read-only under SQLite's authorizer: real tables, `ATTACH`, `PRAGMA`, writes, `load_extension`, recursive CTEs and several statements are refused; 2 s per query, 200 rows with the total, 3 calls a turn | plan §3.2, D2 | documented |
| OWN-DA-04 | A catalog per role documents every view and column (meaning, unit, allowed values), the business's definitions and example questions; an undocumented column fails a test | plan §3.3, D3 | documented |
| OWN-DA-05 | The answer shows its SQL, row count and `as_of` under "Cách tính", collapsed; each query is audited (who, role, SQL, rows, time) | plan §3.4, D4 | documented |
| OWN-DA-06 | With `client_ai` off the model writes the SQL but never reads the rows; a template assembles the answer | plan §3.4, D4 | documented |
| OWN-DA-07 | When the person contradicts a number, the assistant counts again and shows how; it does not argue | plan §3.5, D4 | documented |
| OWN-DA-08 | An eval on real models, ~30 questions per role with gold answers from the database: accuracy ≥ 90 %, p95 ≤ 6 s, ≤ US$0.01 a turn; Haiku and Sonnet measured for the SQL step and the model chosen | plan §3.6, D5 | documented |

## WN — The client's menu by the bank's names (2026-10-22, business feedback 2)

Source: [`2026-10-22_business_feedback_2.md`](../sources/owner_requests/2026-10-22_business_feedback_2.md) (the
business's nine annotated screenshots, relayed by the owner); plan [`docs/WEALTH_NAMES_PLAN.md`](../../WEALTH_NAMES_PLAN.md);
decision [ADR-0037](../decisions/ADR-0037-the-clients-four-sections-carry-the-banks-names.md). "Chỉ là tên, còn sắp
xếp layout dọc theo bản mới": the names, not the old look.

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-WN-01 | The client's vertical menu is four sections named Wealth View, Wealth Planning Advisor, Headline News, Relationship specialist | items 2, 9 | documented |
| OWN-WN-02 | Wealth View's tabs are Wealth view and Dữ liệu chi tiết tài sản (the Tài sản page, unchanged) | items 2, 3 | documented |
| OWN-WN-03 | No Dòng tiền menu item: it is on Wealth view (its address opens Wealth view at its cash flow) | item 4 | documented |
| OWN-WN-04 | No Đồ thị tài chính tab: nothing a client clicks, searches or asks leads to the graph | items 1, 7 | documented |
| OWN-WN-05 | Wealth Planning Advisor's tabs are Wealth planning advisor (Kế hoạch, unchanged) and Risk profile test (the risk test) | items 5, 8 | documented |
| OWN-WN-06 | Tin tức is named Headline News; its Wealth Check reads green when ahead of the benchmark, red when behind, as the old one | item 6 | documented |
| OWN-WN-07 | Wealth view opens on the overview (net worth and its sources, allocation, P&L); cash flow second | item 0 | documented |
| OWN-WN-08 | Every old client address still opens its page, under its new section | ADR-0037 §2 | documented |
| OWN-WN-09 | The assistant and the user guide use the same names | ADR-0037 §5 | documented |
| OWN-WN-10 | Headline News has two tabs: News and Prediction (Chi phí chính sách, renamed) first, then Đồ thị tác động; Tác động tin is no tab, its address kept for the bell's and the feed's evidence | [feedback 3](../sources/owner_requests/2026-10-22_business_feedback_3.md) | documented |
| OWN-WN-11 | The colour tone of Techcombank Private, its palette (gold #C8A45D, deep gold #B08D47, champagne #D4B26A, sand #E1D1BB, light grey #F1F1F1, brown #59392C): gold only on the main action (a primary button, Hỏi trợ lý, the bell's count) with dark words at 4.5:1; tabs, links and selections brown; first read as black and red (feedback 4), replaced by feedback 5 | [feedback 4](../sources/owner_requests/2026-10-22_business_feedback_4.md), [feedback 5](../sources/owner_requests/2026-10-23_business_feedback_5.md) | documented |

## MR — A desk for every staff role (2026-10-18, experiment)

Source: [`2026-10-18_multi_role_ux.md`](../sources/owner_requests/2026-10-18_multi_role_ux.md); plan
[`docs/MULTI_ROLE_UX_PLAN.md`](../../MULTI_ROLE_UX_PLAN.md); decision
[ADR-0036](../decisions/ADR-0036-every-staff-role-works-at-its-own-desk.md); built on branch `exp/graph-workspace`.
The request names CIO, RM, Admin and Expert; "Expert" is the `specialist` role and Compliance is added under "every
role" ([Q-24](open_questions.md#q-24--which-roles-the-multi-role-request-covers)).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-MR-01 | Every staff role works in a purpose-built experience in the Customer workspace's frame (a rail, a centre, the dock with the assistant and an inspector, pages as sheets), its centre designed for the role's responsibilities rather than a copy of the Customer's graph | intro; §2 "not a template to copy blindly"; §4 "do not force every role into the same graph" | documented |
| OWN-MR-02 | CIO: market intelligence, portfolio-wide insight, risk exposure, scenario analysis, significant events and decision support, from existing features | §2 CIO | documented |
| OWN-MR-03 | RM: customer relationships, assigned portfolios, financial profiles, relevant news, customer needs and follow-up actions, from existing features | §2 RM | documented |
| OWN-MR-04 | Admin: users and roles, configuration, integrations, operational health and auditability, from existing features | §2 Admin | documented |
| OWN-MR-05 | Expert: specialist analysis, financial interpretation, relevant evidence and the expert workflow, from existing features | §2 Expert | documented |
| OWN-MR-06 | Every original feature, rule, workflow and integration stays available to its authorised users; nothing is silently deleted, replaced or stubbed | §3; §5 | documented |
| OWN-MR-07 | Access stays enforced by the existing authorisation model; tests verify role isolation | §3; §5 | documented |
| OWN-MR-08 | Traceability from every original requirement to its redesigned interface; the BRD documents the role-specific UX, navigation, workflows, visuals and feature-to-UI mapping, accumulated, not replaced | §1; §3; §5 | documented |
| OWN-MR-09 | The AI agents beneath each role keep working under the new design | owner's added sentence | documented |
| OWN-MR-10 | Each role has its own assistant | owner's added sentence | documented |
| OWN-MR-11 | The Customer experience keeps working throughout | §4 | documented |
| OWN-MR-12 | Built role by role, CIO first; each role documented, built, tested and compared against the BRD before the next; a report of work, tests, gaps and the next role | §4; §5 | documented |

## GW — Persistent financial graph (2026-10-17, experiment)

Source: [`2026-10-17_persistent_financial_graph.md`](../sources/owner_requests/2026-10-17_persistent_financial_graph.md)
(concept image [GW-01](../assets/proposed_ui/GW-01_concept_persistent-graph_illustrative.png), illustrative); plan
[`docs/GRAPH_WORKSPACE_PLAN.md`](../../GRAPH_WORKSPACE_PLAN.md); feature
[FEAT-40](../features/FEAT-40-persistent-financial-graph.md); screen
[SCR-CL-12](../ux/screens/client.md#scr-cl-12--không-gian-tài-chính-graph-workspace); decision ADR-0035. Built on
branch `exp/graph-workspace` and served on its own public link; the live demo is unchanged (OWN-GW-14). Refinement
(OWN-GW-15…19): [`2026-10-17_graph_dataflow_refinement.md`](../sources/owner_requests/2026-10-17_graph_dataflow_refinement.md). The
centre and the layout (OWN-GW-20…32): [`2026-10-17_central_wealth_core.md`](../sources/owner_requests/2026-10-17_central_wealth_core.md)
(“Core”) and [`2026-10-17_graph_layout_routing.md`](../sources/owner_requests/2026-10-17_graph_layout_routing.md)
(“Layout”); plan [`docs/GRAPH_CORE_LAYOUT_PLAN.md`](../../GRAPH_CORE_LAYOUT_PLAN.md). Unified graph and flows
(OWN-GW-33…50): [`2026-10-17_unified_graph_flows.md`](../sources/owner_requests/2026-10-17_unified_graph_flows.md)
(“Unified”); plan [`docs/UNIFIED_FLOWS_PLAN.md`](../../UNIFIED_FLOWS_PLAN.md).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-GW-01 | The Customer role's primary workspace is a persistent financial graph: “My Wealth” in the centre, connected to assets, income, expenses, liquidity, goals, news, risks and hypothetical scenarios; large, interactive, scrollable | §1 “Center” | documented |
| OWN-GW-02 | A compact vertical icon toolbar with tooltips on the left replaces the horizontal feature navigation (Customer role) | §1 “Left” | documented |
| OWN-GW-03 | On the right, the Assistant and a contextual Information/Inspector panel, in the OperonX Studio interaction pattern (tabs; the inspector follows the selection) | §1 “Right” | documented |
| OWN-GW-04 | At the bottom, a collapsible dashboard strip with the essential metrics and compact charts of the existing overview | §1 “Bottom” | documented |
| OWN-GW-05 | Switching menus changes the graph's focus, filters, visible branches and level of detail — it never replaces the page or resets the graph; a dedicated view opens only where a feature needs a different interaction model (Experts/contact may stay a separate view) | §1 last paragraph; §3 | documented |
| OWN-GW-06 | While the assistant thinks or executes tools, subtle activity shows along the nodes and edges those tools concern | §2 bullet 1 | documented |
| OWN-GW-07 | As the answer streams, the corresponding assets, relationships and financial flows are highlighted progressively | §2 bullet 2 | documented |
| OWN-GW-08 | When the assistant refers to a news event, risk, asset or scenario, the explanation is connected to those graph elements | §2 bullet 3 | documented |
| OWN-GW-09 | When a response completes, the relevant nodes and relationships stay clearly marked; a failure shows truthful failure feedback | §2 bullet 4 | documented |
| OWN-GW-10 | Animations follow real streaming events, tool execution and application state only — no fabricated progress, no unrelated animation; motion is light, non-disruptive, and honours reduced-motion preferences | §2 last paragraph; §4 | documented |
| OWN-GW-11 | No existing requirement is removed, silently simplified or broken: every existing Customer feature is mapped to its new entry point and interaction model, with traceability from requirement to interaction, code and test | §3 | documented |
| OWN-GW-12 | Actual financial data and cash flows are visibly distinct from market estimates, forecasts and unverified items; hypothetical scenarios never change actual portfolio values | §3 last paragraph | documented |
| OWN-GW-13 | Built incrementally on what exists (the overview graph, the assistant, the page modules, OperonX), with no unnecessary dependency or rewrite; tested for navigation persistence, selection and inspection, assistant-to-graph interaction, streaming and animation sync, BRD coverage, performance, responsive layout, accessibility and reduced motion; actual results, gaps and performance reported | §4 | documented |
| OWN-GW-14 | An experiment: its own branch and its own public link; the live demo and `main` are not changed by it | instruction with the request | documented |
| OWN-GW-15 | Graph hierarchy: “My Wealth” the anchor, primary assets (and each lens's own kinds) the second layer, holdings, sources and cross-relationships revealed on demand; fewer edges and crossings, no overlapping labels, no background clutter | refinement §1 | documented |
| OWN-GW-16 | Studio-style dataflow: thin “silk” edges; directional luminous pulses with a subtle trail along curved edges and a reaction where they arrive, reusing the OperonX Studio data-flow patterns | refinement §2; “tiny like a web string, with glowing energy running through it” | documented |
| OWN-GW-17 | Motion is meaningful: the assistant processing, streaming, calling a tool or naming an entity animates the relevant paths and nodes in sync with the real events; relevant relationships highlighted, unrelated branches dimmed | refinement §3 | documented |
| OWN-GW-18 | Distinct flow semantics: actual financial flows, data relationships and hypothetical news/scenario impacts look different; no animation implies a real transaction that did not happen | refinement §4 | documented |
| OWN-GW-19 | Performance: lightweight, on the existing graph; no edge animates continuously; reduced motion respected; tested on a realistic (larger) graph | refinement §5 | documented |
| OWN-GW-20 | “My Wealth” is a premium, dimensional financial core, the most compelling element of the graph: layered translucent surfaces, subtle inner illumination, refined rim lighting, restrained glass-like effects — not a flat filled circle or a generic glowing button | Core, bullet 1 | documented |
| OWN-GW-21 | Slow, elegant ambient motion on the core (breathing light, gently moving concentric rings); no excessive neon, noisy particles, constant spinning or sci-fi game look | Core, bullets 2 and 6 | documented |
| OWN-GW-22 | The core is part of the dataflow: financial flows and assistant activity produce meaningful, synchronized light pulses through the core and the connected edges | Core, bullet 3 | documented |
| OWN-GW-23 | The net worth and its supporting figures stay crisp, stable, readable and accessible; no effect competes with them | Core, bullet 4 | documented |
| OWN-GW-24 | Distinct but subtle core states: idle, selected, assistant thinking/streaming, active financial-flow interaction | Core, bullet 5 | documented |
| OWN-GW-25 | The core runs on the existing renderer and Studio dataflow patterns, GPU-friendly, with reduced-motion support — no separate, expensive animation system | Core, bullet 7 and closing paragraph | documented |
| OWN-GW-26 | Collision-free layout: nodes and labels never overlap; spacing adapts to node and label sizes, graph size and viewport | Layout, bullet 1 | documented |
| OWN-GW-27 | Clear hierarchy: “My Wealth” the anchor, primary assets a well-spaced layer, sources, transactions, risks, goals and scenarios in organized contextual groups; no arbitrary positions, no overcrowded radial layout | Layout, bullet 2 | documented |
| OWN-GW-28 | Edge routing: few crossings and bends, no edge through a node or a label; curved, bundled or orthogonal routing with consistent entry and exit points | Layout, bullet 3 | documented |
| OWN-GW-29 | Readable connections: primary financial flows, supporting relationships and hypothetical impacts look different; inactive edges subtle; only the active paths are highlighted | Layout, bullet 4 | documented |
| OWN-GW-30 | Adaptive exploration: a dense graph reveals secondary nodes progressively, collapses groups and expands a selected branch; fit-to-view, zoom, pan, and focus on the selection without losing context | Layout, bullet 5 | documented |
| OWN-GW-31 | Stable interaction: predictable layout changes; the mental map is kept — nodes do not jump when an asset is selected, a view switched or an assistant answer arrives | Layout, bullet 6 | documented |
| OWN-GW-32 | Tested on realistic and dense graphs for node and label collisions, crossings, readability at zoom levels and performance. Acceptance: organized as complexity grows — no overlapping nodes or labels, no edge through a node, no uncontrolled web; when a layout cannot stay readable, visible complexity is reduced instead of squeezed | Layout, testing paragraph and acceptance criterion | documented |
| OWN-GW-33 | One unified graph for the Customer: assets, liabilities, income, expenses, transactions, news impacts, goals, risks and scenarios in one interactive model; the toolbar, graph, Assistant/Info panel and bottom strip kept; navigation enriches, refocuses or filters the graph instead of replacing it (Experts/contact may keep its own view) | Unified §1 | documented |
| OWN-GW-34 | Actual money flows — verified income, expenses, transfers, debt payments and other real cash movements — drawn as directional animated flows, each traceable to the records it sums | Unified §2 “Actual”; §5 “identity and traceability” | documented |
| OWN-GW-35 | News impacts — estimated consequences of news, policies, infrastructure projects and market changes — drawn as estimated flows to what they affect | Unified §2 “News impacts” | documented |
| OWN-GW-36 | Goal flows — projected savings and contributions toward education, retirement, purchases and other goals — drawn as projected flows | Unified §2 “Goals” | documented |
| OWN-GW-37 | Scenario flows — hypothetical market moves, property prices, interest rates, income changes and user-defined what-ifs — drawn as hypothetical flows | Unified §2 “Scenarios” | documented |
| OWN-GW-38 | Actual data, estimates, assumptions and family-related information distinguished visually and semantically; a hypothetical flow is never shown as a completed transaction or added to current assets | Unified §2 | documented |
| OWN-GW-39 | An impact can be traced from its source through the assets, liabilities, income, expenses and liquidity it affects to projected net worth | Unified §2 | documented |
| OWN-GW-40 | Several scenarios together: their assumptions and dependencies tracked, no double counting, the active scenarios clearly shown | Unified §2 | documented |
| OWN-GW-41 | Every eligible money edge moves continuously and subtly; density, speed, trail and prominence follow the normalized monthly amount within limits; direction follows the money; actual, estimated and hypothetical look different; a non-monetary relation implies no transfer; figures stay crisp | Unified §3 | documented |
| OWN-GW-42 | When the assistant answers, streams, investigates an event or runs a scenario, the graph's movement and pulses follow the entities and paths concerned — nothing decorative or unrelated | Unified §3, §6 | documented |
| OWN-GW-43 | The core stays the visual heart, with a clear hierarchy core → primary assets → secondary entities → context (restates OWN-GW-20…25) | Unified §4 | documented |
| OWN-GW-44 | The layout requirements hold for the enlarged graph (restates OWN-GW-26…31): no collisions, no edge through a node or label, groups around the core, progressive reveal, zoom, pan, fit, focus, graph/list switching, stable under selection, view changes and answers | Unified §5 | documented |
| OWN-GW-45 | The assistant explains graph relationships, investigates news, inspects assets, compares scenarios and helps with supported tasks, in the existing panel | Unified §6 | documented |
| OWN-GW-46 | Selecting a node or an edge shows in Thông tin its details, source, calculation, assumptions, confidence where available and downstream effects | Unified §6 | documented |
| OWN-GW-47 | The assistant knows the current graph selection and the active scenarios | Unified §6 | documented |
| OWN-GW-48 | The existing rendering stack and Studio patterns reused; animation work limited, off-screen activity reduced, reduced motion respected, responsive at realistic volumes | Unified §7 | documented |
| OWN-GW-49 | No transaction amount, projection, news evidence or confidence score is invented; where data or logic is missing the gap is named and only what is supported is built | Unified §7 | documented |
| OWN-GW-50 | BRD discipline: every existing feature and its logic kept; docs/brd updated (decisions, feature mapping, graph semantics, flow rules, UI references, test evidence); a final report of work, tests, gaps and BRD requirements not yet implemented | Unified §8 | documented |

## SS — Assistant sessions, history and compaction (2026-10-17, experiment)

Source: [`2026-10-17_assistant_sessions.md`](../sources/owner_requests/2026-10-17_assistant_sessions.md). Extends AS (FEAT-37); the global memory (OWN-AS-12…16) stays as it is.

| ID | Requirement | Source | Status |
|---|---|---|---|
| OWN-SS-01 | Sessions: create a new one, switch to an earlier one, rename, archive (and bring back) or delete | “Session management” | documented |
| OWN-SS-02 | A concise, meaningful title generated from the first request and refined when more context is available; a title the person set is kept | “Session management” | documented |
| OWN-SS-03 | Each session's messages, timestamps, tool activity and metadata persist; reopening or refreshing restores the right conversation, including a turn that was cut by the refresh; the store chosen after checking the deployment | “Conversation persistence” | documented |
| OWN-SS-04 | Two levels: the person's global memory kept across sessions and retrieved when relevant; each session's history and working context isolated; never another user's data, never an unrelated session mixed in | “Two levels of memory” | documented |
| OWN-SS-05 | Automatic compaction near the context limit into a structured continuation summary (decisions, preferences, unresolved tasks, entities, tool results, references to persistent data), recent messages kept; recoverable, never silent | “Context compaction” | documented |
| OWN-SS-06 | Each session keeps its own goal, context summary and history; a new session resets the active context without erasing global memory or earlier sessions | “Session continuity” | documented |
| OWN-SS-07 | A session switcher and history and a prominent New Chat in the existing assistant panel, compact and consistent with the design, on desktop and phone | “UI integration” | documented |
| OWN-SS-08 | Tests: persistence across refreshes, session isolation, titles, compaction and continuation, tool-call recovery, multi-user access | “Testing” | documented |

## AS — Assistant, memory and agent ecosystem (2026-10-16, backlog B-08)

Source: [`2026-10-16_assistant_memory_agents.md`](../sources/owner_requests/2026-10-16_assistant_memory_agents.md);
plan [`docs/ASSISTANT_PLAN.md`](../../ASSISTANT_PLAN.md); architecture [`assistant.md`](../architecture/assistant.md);
decisions ADR-0026…ADR-0034.

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-AS-01 | The assistant is the main conversational entry point: the Copilot panel becomes its front end, on every page and role | §1 first paragraph | documented |
| OWN-AS-02 | It answers about the application itself (what a page shows, how a number is computed, how to do a task) from the product's own documentation, with the page or document cited | §1 “answer questions about the application” | documented |
| OWN-AS-03 | It answers about the user's **authorized** financial data only: every read goes through the same role, family and separation-of-duty checks as the pages | §1 “the user's authorized financial data” | documented |
| OWN-AS-04 | It discovers and calls application features through one registry of tools, each with roles, read/write, a confirmation rule for writes, a timeout and a cost class; no unrestricted access to internal services | §1 “discover and invoke… controlled, discoverable tools” | documented |
| OWN-AS-05 | It runs multi-step tasks (several tool calls in order), verifies a write by reading the state back, and reports a failure as a failure | §1 “execute supported user tasks, verify outcomes, and report failures honestly” | documented |
| OWN-AS-06 | A write never runs without the user's confirmation in the panel; a refused or expired confirmation runs nothing | §1 “controlled”; Copilot ADR-0012 kept | documented |
| OWN-AS-07 | Questions outside OneWealth are answered with web search and reliable external knowledge, with sources and a stated level of certainty; without a provider, the assistant says web search is unavailable | §1 “outside OneWealth's direct scope” | documented |
| OWN-AS-08 | An unsupported request is declined plainly, saying what it can do instead; it never pretends a capability exists | §1 “gracefully handle unsupported requests” | documented |
| OWN-AS-09 | The client-data barrier holds for the assistant: a model reads client data only where Admin's `client_ai` allows it (demo, on-premise); otherwise the model plans and the answer is assembled from tool results | §2 “privacy-conscious”; BRD-BR-11, NFR-08 | documented |
| OWN-AS-10 | Conversations are kept on the server per user: listed, resumed on another device, searchable; the store chosen by a measurement of the deployment's workload | §2 first paragraph | documented |
| OWN-AS-11 | Short-term memory: the current conversation, its recent messages and the active task's state, compacted when it grows past the context budget, never silently dropped | §2 “short-term memory” | documented |
| OWN-AS-12 | Long-term memory: a few concise items per user (preferences, goals, facts, constraints), each with its source message, time and confidence; not every detail is kept | §2 “long-term memory”; “Do not save every conversation detail” | documented |
| OWN-AS-13 | Archive memory: every message searchable with its conversation, time and author | §2 “archive memory” | documented |
| OWN-AS-14 | Tools to search, retrieve, update, summarise and forget memory, for the assistant and on a page the user sees (“Bộ nhớ”): see, correct, forget one item or all | §2 “Provide tools…”; “inspectable, and correctable” | documented |
| OWN-AS-15 | Retention policies for the archive and the long-term items, set by Compliance; deletion is real | §2 “retention policies, user control, deletion” | documented |
| OWN-AS-16 | Isolation: a user's memories and materials are never read for another user; shared product knowledge, user material and web content are kept apart | §2 “logically isolated”; “safeguards against cross-user data leakage” | documented |
| OWN-AS-17 | A knowledge base for product documentation and the materials a user provides, with answers that cite the passage | §2 “knowledge base / second brain” | documented |
| OWN-AS-18 | A small family of background agents, each with one responsibility and its own tools: memory consolidation and user-requested follow-ups added to the existing CIO agent, challenger, policy agent and newsletter step | §3 | documented |
| OWN-AS-19 | Background work is event-driven where it can be, scheduled only where needed, with token budgets, deduplication, retries, traces and a measured cost per day | §3 “Prefer event-driven execution…” | documented |
| OWN-AS-20 | An Agent Ecosystem Map in the existing UI: the user, the assistant, the agents with their responsibilities and tools, the connections and data flows that exist, overview first with drill-down into runs and traces | §4 | documented |
| OWN-AS-21 | The map shows each agent active, waiting, completed or failed from real execution state, and the states match the traces | §4 “based on real execution state”; §5 last bullet | documented |
| OWN-AS-22 | The map follows the kit's visual language, readable on desktop and phone, with no decorative connections | §4 “aligned with the UI references”; “Avoid a cluttered graph” | documented |
| OWN-AS-23 | A systematic evaluation suite on real models and realistic Vietnamese conversations: answers, grounding, citations, uncertainty, tools, multi-step tasks, failures, out-of-scope, memory, long conversations, security (authorisation, prompt injection, leakage, unsafe tools), concurrency, latency, tokens and cost | §5 | documented |
| OWN-AS-24 | Production readiness is declared only against measured quality, reliability, latency and cost indicators and a gate; missing credentials or services are reported as limitations | §5 “Do not rely on mock responses…” | documented |
| OWN-AS-25 | Built incrementally on what exists (Copilot, CIO agents, OperonX), working features and APIs kept; `docs/brd/` updated with requirements, memory model, agent responsibilities, workflows, UI references and acceptance tests | Execution rules 1–5 | documented |

## MOTION — Living Interface & Smart Animations (2026-10-16, backlog B-01)

Source: [`2026-10-16_living_interface.md`](../sources/owner_requests/2026-10-16_living_interface.md).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-MOTION-01 | **Idle presence**: subtle ambient motion around the assistant, to create a sense of presence | §1 “Idle” | documented |
| OWN-MOTION-02 | **Thinking**: gentle pulses or flowing highlights while the assistant is processing a request or executing tools | §1 “Thinking” | documented |
| OWN-MOTION-03 | **Responding**: briefly highlight the charts, assets, news or graph connections the assistant references, so the page feels connected to the assistant | §1 “Responding”, second paragraph | documented |
| OWN-MOTION-04 | **Completed / error**: clear, elegant visual feedback | §1 “Completed / Error” | documented |
| OWN-MOTION-05 | Premium, minimal, calm; no excessive glow, distracting movement, heavy 3D or whole-page animation; motion communicates a meaningful state change, never decoration | §1 last paragraph | documented |
| OWN-MOTION-06 | Performance: CSS transitions, transforms, opacity and simple SVG; no heavy animation library, no continuous JS loop, no needless re-render or layout; driven by real assistant and app events, never fabricated progress; suspended when the tab is hidden or the interface inactive; `prefers-reduced-motion` respected; usable on low-end devices; measured before and after | §2 | documented |
| OWN-MOTION-07 | Incremental: no redesign, business logic unchanged, every documented feature preserved; feature specs, UX docs, design system, traceability and changelog updated | §3 | documented |

## UI — redesign to the kit (2026-10-16, backlog B-00)

Source: [`2026-10-16_ui_redesign.md`](../sources/owner_requests/2026-10-16_ui_redesign.md); the gaps it names are
G1–G9 of [`docs/UI_REDESIGN_PLAN.md`](../../UI_REDESIGN_PLAN.md).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-UI-01 | Every page wears the kit's concept-board look (R-D1): light first, dark kept | request; plan G1, G2 | documented |
| OWN-UI-02 | The pages that predate the BRD are rebuilt in the new design with every block and action kept | plan G1, G7 | documented |
| OWN-UI-03 | Header search over what the role may open, and a notifications bell, as on the board | plan G2, R-D5 | documented |
| OWN-UI-04 | Graph overview with data sources, risks and goals, expand/collapse, node → page; an event timeline; the CIO's whole-run graph | plan G3, G5 | documented |
| OWN-UI-05 | Copilot answers with as-of time and sources, structured cards, investigate and stress-scenario tools, audited calls | plan G6 | documented |
| OWN-UI-06 | The live demo runs the real models (owner D-03) and shows real runs from fetched news | plan G8 | documented |
| OWN-UI-07 | Browser tests in the suite for every route and the main interactions | plan G9 | documented |
