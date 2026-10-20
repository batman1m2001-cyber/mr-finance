# Client screens (`#/client/…`)

Layer C. As built on 2026-10-15. Screenshots are **current state** (dev server, seeded demo data, client C01
“Nguyễn Minh Khoa”) — illustrations of behaviour, not evidence of it; the evidence is the tests cited in the
features. Template: [`../../templates/screen_template.md`](../../templates/screen_template.md).

Shared by every client screen: the shell (role switcher, client picker, Cá nhân / Gia đình, theme) and the
footer disclaimer ([information architecture](../information_architecture.md#the-shell)). The RM sees SCR-CL-01,
02, 03 and 06 inside “Khách hàng” in staff mode.

---

## SCR-CL-01 — Tổng quan (overview)

| | |
|---|---|
| Route | `#/client/tong-quan/chi-tiet` (“Chi tiết”); RM: `#/rm/khach-hang/tong-quan` (“Chi tiết”) |
| Generation | rebuilt in R3 (`web/pages/detail.js`; was tab `overview`, ADR-0019) |
| Features | [FEAT-21](../../features/FEAT-21-dashboard.md), [FEAT-20](../../features/FEAT-20-consolidation.md), [FEAT-25](../../features/FEAT-25-policy-cost-alerts-and-house-views.md) (Headline News card) |
| Requirements | BRIEF-DASH-01…07, BRIEF-DATA-04, BRIEF-DATA-05 |
| Data | `POST /api/dashboard`, `POST /api/alerts` |
| Screenshots | [desktop](../../assets/current_ui/SCR-CL-01_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CL-01_phone-light.jpg) |

**Journey.** The client opens the app and sees, in seconds, what they are worth, how it moved this month, and
whether anything needs attention.

**Layout, top to bottom.**
1. Net worth hero (“TÀI SẢN RÒNG · CÁ NHÂN”, e.g. 24,5 tỷ, ▲ +1,8 % vs last month, assets/debt/date, owner chip)
   beside “Tài sản theo nguồn dữ liệu” — three source groups with share and value, each clickable to the holdings.
2. Three cards: **Phân bổ tài sản** (class, value, share, P&L %), **Lãi / lỗ danh mục** (realised, unrealised,
   YTD return vs VN-Index, per class), **Rủi ro** (accepted drawdown vs stress estimate, bar, “Gần ngưỡng”,
   concentration warning).
3. **Thanh khoản dự phòng** — liquid assets as months of spending, safe mark 6 months.
4. **Dòng tiền** — past 6 months and a 12/24/36-month forecast (lighter bars), large payments flagged (e.g.
   T3/27 study fees 1,8 tỷ), recurring items found in transactions.
5. **Headline News** — the top policy-cost alerts (risk/opportunity, VND) and “Xem tất cả 13 tin →”.

**Actions.** Switch scope; open a source group; change the forecast horizon; open all alerts (→ SCR-CL-06).

**States.** Loading (dimmed); a client without a risk test shows “Chưa làm bài test rủi ro: ngưỡng lấy theo hồ
sơ”; values not provided by a source show “—”.

**Responsive / a11y.** Single column on phone (3,308 px tall); no horizontal scroll at 390 px; chart has a legend.

**Notes.** The Headline News card's numbers come from the point rules, not from the engine shown on SCR-CL-05
(Q-03). Since 2026-10-16 the summary lives on [SCR-CL-08](#scr-cl-08--toàn-cảnh-pulse-wealth-map-money-flow) (Toàn
cảnh, opened first); this page is unchanged under “Chi tiết”, so every block above stays. The card is still to be
replaced by the Intelligence Feed (FEAT-31).

---

## SCR-CL-02 — Tài sản (holdings)

| | |
|---|---|
| Route | `#/client/tai-san`; RM: `#/rm/khach-hang/tai-san` |
| Generation | rebuilt in R3 (`web/pages/holdings.js`; was tab `sources`) |
| Features | [FEAT-20](../../features/FEAT-20-consolidation.md), [FEAT-22](../../features/FEAT-22-statement-reading.md), [FEAT-23](../../features/FEAT-23-chat-declaration.md) |
| Requirements | BRIEF-DATA-01…05 |
| Data | `POST /api/dashboard`, `POST /api/statement`, `POST /api/declare` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CL-02_desktop-light.jpg), [phone](../../assets/current_ui/SCR-CL-02_phone-light.jpg) |

**Layout.** Two input cards — **Tải sao kê** (choose a PDF/Excel/CSV file, or “Dùng sao kê mẫu: vps_C01.csv”) and
**Bổ sung tài sản** (chat, with four example sentences) — then **Tất cả tài sản và khoản nợ**: holdings grouped
by class (collapsible), each with source and trust badge (Đã xác thực / Từ sao kê / Bạn tự khai), purchase date
and price, cost, current value, P&L; totals: assets, debt, net worth.

**Actions.** Upload a statement → its holdings appear labelled “Từ sao kê”; send a chat sentence → the reply says
what was recorded and the table grows; collapse a class.

**States.** Upload/agent errors are shown inline; without a model the rule paths answer (ADR-0015 D2).

**Tests.** `tests/ui/test_pages.py::test_a_statement_and_a_declaration_reach_the_book`.

---

## SCR-CL-03 — Kế hoạch (Wealth Planning Advisor)

| | |
|---|---|
| Route | `#/client/muc-tieu/ke-hoach`; RM: `#/rm/khach-hang/ke-hoach` |
| Generation | rebuilt in R3 (`web/pages/plan.js`; was tab `scenarios`) |
| Features | [FEAT-26](../../features/FEAT-26-life-scenarios-stress-tests-and-goals.md), [FEAT-27](../../features/FEAT-27-rm-approval-queue.md) |
| Requirements | BRIEF-SCEN-01…03 |
| Data | `POST /api/goals`, `POST /api/scenario`, `GET /api/scenarios`, `POST /api/review/propose`, `GET /api/review` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CL-03_desktop-light.jpg), [phone](../../assets/current_ui/SCR-CL-03_phone-light.jpg) |

**Layout.** “Bức tranh tài sản” (Wealth view until 2026-10-20) KPI strip (total net worth, portfolio P&L, goals funded, 12-month net cash flow), cash-flow
chart and need-vs-have bars per goal, the monthly saving needed; then **Life goals** list (grouped: family &
children, wealth building, retirement & transfer, risk reserve, decisions & stress tests) beside the selected
item: status, goal status (need / have / gap), performance tracking (this month vs expected, start of year / last
month / now), **Required action** (ranked, each “Gửi chuyên gia duyệt”), **Calculation details** (editable
assumptions + “Chạy lại”, before/after table), and the light / heavy options.

**Actions.** Pick a goal or a stress test; edit assumptions and rerun; send an action or option to the specialist
queue (→ SCR-CL-07).

**Notes.** The regulation note of the goal branch is not shown on these goal cards (Q-20).


**Since 2026-10-16 (FR-603, Q-20).** “Lưu ý quy định cho mục tiêu” sits under Bức tranh tài sản: each released
regulation note that applies to a goal, with its level and milestone (the client sees only notes with a client
message).

**Tests.** `tests/ui/test_pages.py::test_a_proposal_is_approved_by_the_rm_and_the_client_sees_it`.

---

## SCR-CL-04 — Khẩu vị rủi ro (risk test)

| | |
|---|---|
| Route | `#/client/muc-tieu/khau-vi` |
| Generation | rebuilt in R3 (`web/pages/risktest.js`; was tab `risk`) |
| Feature | [FEAT-24](../../features/FEAT-24-risk-test.md) |
| Requirements | BRIEF-RISK-01…05 |
| Data | `POST /api/risk` |
| Screenshot | [desktop, start](../../assets/current_ui/SCR-CL-04_desktop-light.jpg), [phone, a question](../../assets/current_ui/SCR-CL-04_phone-light-question.jpg), [desktop dark, result](../../assets/current_ui/SCR-CL-04_desktop-dark-result.jpg) |

**Journey.** “Bắt đầu cho <name>” → 8–12 situational questions, one at a time, each depending on the last → the
result: tolerance, capacity, the mismatch sentence when they differ, the persona, the new drawdown limit (which
the overview then uses).

**Since R3.** A progress bar over the questions, answers as lettered cards, “← Câu trước”; the result shows
tolerance and capacity on the five named levels with the level each falls in. **Tests.**
`tests/ui/test_pages.py::test_the_risk_test_goes_back_and_sets_the_limit`.

---

## SCR-CL-05 — Tác động thị trường (family impact, client)

| | |
|---|---|
| Route | `#/client/tin/thi-truong` |
| Generation | new (`web/pages/impact.js`) |
| Features | [FEAT-13](../../features/FEAT-13-impact-delivery-by-role.md), [FEAT-10](../../features/FEAT-10-goal-branch.md) |
| Requirements | BRD-BR-08, BRD-BR-10, BRD-FR-502, BRD-RULE-CONTENT-01 (flow 2), BRD-RULE-CONTENT-02, BRD-NFR-11 |
| Data | `GET /api/families/{id}/impact?role=client`, `GET /api/goals/regulation?family_id=&role=client`, `GET /api/families/{id}/how?run=` |
| Screenshots | [desktop, with the timeline](../../assets/current_ui/SCR-CL-05_desktop-light.jpg) · [desktop dark](../../assets/current_ui/SCR-CL-05_desktop-dark.jpg) · [phone](../../assets/current_ui/SCR-CL-05_phone-light.jpg) · [Cách tính, desktop](../../assets/current_ui/SCR-CL-05-how_desktop-light.jpg) · [Cách tính, phone](../../assets/current_ui/SCR-CL-05-how_phone-light.jpg) · [goals in VND, desktop](../../assets/current_ui/SCR-CL-05-goals_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CL-05-goals_phone-light.jpg) |

**Journey.** After the CIO approves news and the post-check passes, the client sees what it may do to their
wealth over the next 3 months, how wide the range is, and where it comes from — without tickers or advice.

**Layout.**
1. **Hero:** “TIN TÁC ĐỘNG · 3 THÁNG TỚI”, one figure (e.g. −726 triệu), the sentence (“3 sự kiện đang có hiệu lực;
   chủ yếu qua Cổ phiếu (−559 triệu)”), % of net worth, badge “AI hỗ trợ · CIO duyệt”, the formula in words,
   price date, “tham số mô hình là giả định”, the approver's name and title.
2. **Dải kết quả có thể** — fan chart of the selected event: expected line, P10–P90 band, P5 dashed, at today /
   1 week / 3 months / 12 months, labelled ends.
3. **Đến từ đâu** — contribution by asset class (diverging bars, values).
4. **Sự kiện** — each effective event by **type** (“Chính sách tiền tệ”, “Vàng”…), status, approval time, its
   3-month change and %, “Xem dải” to switch the chart.
5. **Lưu ý cho mục tiêu của bạn** — goal-branch messages for declared goals (level badge, message, “Nên chuẩn
   bị trước <date>”, documents).
6. The client note (AI-assisted, assumed parameters, not a recommendation, contact your RM).

**States.** Empty: “Khi có tin đáng chú ý đã được kiểm duyệt, tác động lên tài sản của bạn sẽ hiện ở đây.”; no goal
panel when nothing matches.

**Responsive / a11y.** Phone 2,150 px tall; fan chart uses short labels on narrow screens; colours from the
validated palette; hover tooltips on marks.

**Rationale.** One hero number instead of tables (the U1 target “news page ≤ 736 words”: 257 achieved). Event type
instead of headline because a headline can name a company ([ADR-0008](../../decisions/ADR-0008-the-client-sees-asset-classes-only.md)).
No trace drawer for the client (Q-14): it names holdings and headlines; the client's own “Cách tính” came in F10.

**Since R4.** A “Dòng thời gian” panel: one row per event, its steps in order — first news, event, AI draft, AI
challenge, CIO approval, applied, effective — each with the time stored on its record; the selected event's row is
outlined. Tests: `tests/ui/test_pages.py::test_the_timeline_the_news_impact_card_and_the_cio_run_graph`.

**Since F10.** Each effective event has a **“Cách tính”** button: a drawer with the number and its band, the formula
in words, each scenario (probability, the factor moves with their units, the family's change in it), the asset
classes (value, contribution) and the outlets — no holding, ticker or headline (F-D9, FEAT-09). The goals panel
adds **“Tác động 3 tháng (VND)”**: each goal's expected change with P10 and P90, its share of the goals' pool, and
a footnote with what stays unallocated (BR-08); runs stored before F10 show the levels only. Tests:
`tests/test_apply.py::test_fd9_the_client_reads_how_its_number_is_made_by_asset_class_with_no_holding_named`,
`tests/test_apply.py::test_br08_each_goal_gets_its_vnd_share_of_the_pools_impact_at_every_horizon`.

---

## SCR-CL-06 — Chi phí chính sách (policy costs)

| | |
|---|---|
| Route | `#/client/tin/chinh-sach`; RM: `#/rm/khach-hang/chinh-sach` |
| Generation | rebuilt in R3 (`web/pages/policy.js`; was tab `alerts`) |
| Feature | [FEAT-25](../../features/FEAT-25-policy-cost-alerts-and-house-views.md) |
| Requirements | BRIEF-IMPACT-01…05, BRIEF-ALERT-01, BRIEF-ALERT-02 |
| Data | `POST /api/alerts`, `GET /api/views`, `POST /api/goals` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CL-06_desktop-light.jpg), [phone](../../assets/current_ui/SCR-CL-06_phone-light.jpg) |

**Layout.** “Kiểm tra tài sản” (Wealth check until 2026-10-20; YTD return vs benchmark, goals tracked, required actions, link to the planning
advisor); **Tác động lên tài sản ròng** (diverging bars per policy, filter all / risks / opportunities, the formula);
**House views** (8 mock research-house views matched to holdings, 2 shown + “Xem thêm”); the mock-data and
legal-status notes; **Policy headlines** — one card per policy with level, legal status, the impact (with
probability), holding × sensitivity × probability, the holdings touched, the source line.

**DEF-01 (fixed 2026-10-15).** The “Wealth check” card was squeezed into an 18 px column at 1440 px: the new pages'
`.check` checklist rule (`web/core/tokens.css`) also matched this legacy card. The rule is now scoped to `#page-new`.

**Since R3.** The risks / opportunities filter applies to the bars and to the cards below. **Tests.**
`tests/ui/test_pages.py::test_the_policy_filter_keeps_one_side`.

---

## SCR-CL-07 — Chuyên gia (specialist team)

| | |
|---|---|
| Route | `#/client/chuyen-gia` |
| Generation | rebuilt in R3 (`web/pages/advisor.js`; was tab `rm`) |
| Features | [FEAT-28](../../features/FEAT-28-advisory-team-and-track-record.md), [FEAT-27](../../features/FEAT-27-rm-approval-queue.md) |
| Requirements | BRIEF-FLOW-02 |
| Data | `GET /api/advisory?client_id=`, `GET /api/review` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CL-07_desktop-light.jpg) |

**Layout.** The relationship specialist's card (name, title, phone, e-mail, office, hours — all mock, said so);
the **Hàng chờ duyệt** (Approval queue until 2026-10-20; “Hàng chờ chuyên gia duyệt · n đang chờ”): each proposal with its actions and summary and,
while pending, “Đang chờ chuyên gia duyệt”; decided items with their badge and note. Read-only: the RM decides on
[SCR-RM-06](rm.md#scr-rm-06--duyệt-đề-xuất-approval-queue) (DEF-02 fixed 2026-10-15).

**Tests.** `tests/ui/test_pages.py::test_a_proposal_is_approved_by_the_rm_and_the_client_sees_it`.

---

## SCR-CL-08 — Toàn cảnh (Pulse, Wealth Map, Money Flow)

| | |
|---|---|
| Route | `#/client/tong-quan/toan-canh` (client's first page); RM: `#/rm/khach-hang/toan-canh` |
| Generation | new (`web/pages/pulse.js`) |
| Feature | [FEAT-29](../../features/FEAT-29-financial-pulse-wealth-map-money-flow.md) |
| Requirements | KIT-UX-01, KIT-UX-02, KIT-UX-03, KIT-UX-05, KIT-UX-06, OWN-UI-01; BRIEF-DASH-01 (net worth), BRIEF-DASH-02 (allocation) |
| Data | `POST /api/dashboard`, `POST /api/flows`, `POST /api/feed`, `POST /api/goals` |
| Screenshots | [desktop](../../assets/current_ui/SCR-CL-08_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CL-08_phone-light.jpg) · [dark](../../assets/current_ui/SCR-CL-08_desktop-dark.jpg) · [band picked](../../assets/current_ui/SCR-CL-08_flow-picked.jpg) |

**Journey.** In one screen: what I am worth and how it moved, what came in and went out last month and what was
left, how long my reserve lasts, how exposed I am — then where the money sits and where it flowed.

**Layout** (the concept board, R2). Four Pulse cards (two per row below 1100 px, one on a phone), each with one
small chart: net worth with the classes that moved it, the month's cash flow with six months of in/out bars,
the reserve with a ring, the stress loss on a gauge. **Dòng tiền của bạn** (7/12): month picker, Sankey with a
colour and icon per category, three ratios, the table of bands. **Phân bổ tài sản** (5/12): donut with the total
inside and a legend; a class opens its holdings. **Điều đáng chú ý** (7/12, FEAT-31): impact cards — icon by type,
severity, type and (for news) the 3-month impact as pills, why, source, evidence link. **Mục tiêu tài chính**
(5/12): followed goals with status, need, deadline, progress bar and gap. A link to “Chi tiết” (SCR-CL-01).

**States.** A month with no rows: “Không có giao dịch trong tháng này.”; a failed flows call keeps the page and
shows the error under the chart.

**Interaction.** Bands, donut segments and legend rows are focusable buttons (Enter / Space); tooltips on hover
and focus. A picked band dims the others and sends three dots along itself three times (none under reduced motion;
paused while the tab is hidden).

---

## SCR-CL-09 — Đồ thị tác động (Intelligence Graph)

| | |
|---|---|
| Route | `#/client/tin/do-thi`; RM: `#/rm/khach-hang/do-thi` |
| Generation | new (`web/pages/graph.js`) |
| Feature | [FEAT-30](../../features/FEAT-30-financial-intelligence-graph.md) |
| Requirements | KIT-UX-04, KIT-UX-06; BRD-RULE-CONTENT-01 (flow 2) |
| Data | `GET /api/families/{id}/graph?role=client\|rm` |
| Screenshots | [desktop](../../assets/current_ui/SCR-CL-09_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CL-09_phone-light.jpg) · [dark](../../assets/current_ui/SCR-CL-09_desktop-dark.jpg) · [RM, a node selected](../../assets/current_ui/SCR-CL-09_desktop-light-rm.jpg) · [News Impact panel](../../assets/current_ui/SCR-CL-09_desktop-light-impact.jpg) |

**Journey.** “Which news reaches my money, through what, and down to which goal?” — read left to right.

**Layout.** One panel: “Đồ thị / Danh sách” switch, seven type filters (chips, struck through when hidden), the
graph in seven columns (Tin, Sự kiện, Kịch bản, Yếu tố, Tài sản, Gia đình, Mục tiêu), the detail panel, the
note that edges are potential impacts with stored sources.

**Interaction.** A node is a focusable button: click, Enter or Space selects it, lights its path and dims the
rest; again or “Bỏ chọn” clears. Tooltips on nodes and edges. Phones open on the list.

**States.** No effective run: “Chưa có tin nào được CIO duyệt áp dụng cho gia đình này”.

**Since R4.** Selecting an event opens the News Impact panel: direction, main scenario, the chain with a count per
column, the classes (client) or holdings (RM) it may move with this event's own share and share of net worth, the
goals before → after, the outlets. The CIO opens the same page on a whole run (SCR-CIO-10).

---

## SCR-CL-10 — OneWealth Copilot (panel, all roles)

| | |
|---|---|
| Route | none: a panel over every page of every role, opened by “✦ Hỏi OneWealth” (bottom right) |
| Generation | new (`web/copilot.js`) |
| Feature | [FEAT-32](../../features/FEAT-32-copilot.md) |
| Requirements | KIT-COPILOT-01…05, OWN-UI-05; BRD-BR-11, BRD-NFR-08 |
| Data | `POST /api/copilot` |
| Screenshots | [client](../../assets/current_ui/SCR-CL-10_desktop-light.jpg) · [RM confirm](../../assets/current_ui/SCR-CL-10_desktop-light-rm.jpg) · [phone](../../assets/current_ui/SCR-CL-10_phone-light.jpg) · states (FEAT-33): [marks](../../assets/current_ui/SCR-CL-10_desktop-light-marks.jpg) · [flow marks](../../assets/current_ui/SCR-CL-10_desktop-light-flow.jpg) · [refusal](../../assets/current_ui/SCR-CL-10_desktop-light-error.jpg) · [phone busy](../../assets/current_ui/SCR-CL-10_phone-light-busy.jpg) · [phone marks after close](../../assets/current_ui/SCR-CL-10_phone-light-marks.jpg) · [graph path](../../assets/current_ui/SCR-CL-09_desktop-light-path.jpg) · R5: [investigate (chain)](../../assets/current_ui/SCR-CL-10_desktop-light-chain.jpg) · [stress scenario](../../assets/current_ui/SCR-CL-10_desktop-light-scenario.jpg) · [phone, goals card](../../assets/current_ui/SCR-CL-10_phone-light-card.jpg) |

**Layout.** Header with the router label (“bộ định tuyến từ khóa” or the model), the page context (“Đang xem:
Toàn cảnh · Khách hàng · Nguyễn Minh Khoa”), the conversation (answers with a status badge when failed,
forbidden or pending; “Mở … →” evidence link; “Mô hình thấy gì”), suggestion chips, the input, and the note that
the model only picks a tool and that this is not investment advice.

**Interaction.** Enter sends; a pending write shows **Xác nhận** / **Huỷ**; Esc or ✕ closes and returns focus to
the button; a navigate answer changes the page. Phones: the panel fills the width.

**States and marks** ([FEAT-33](../../features/FEAT-33-living-interface.md)). A status dot left of the title: green
(ready; a slow ripple while the panel is open), accent while the request runs (three dots in the list, the
button's ✦ breathes), ✓ on the button after an answer, red after a refusal or failure (also a dot on the button
and a red edge on the answer), amber while a write waits for Xác nhận. An answer that read numbers on this page
marks them and offers **Chỉ trên trang**; otherwise **Mở … →** opens the page and marks them there. Phones: the
marks wait until the panel is closed.

**Since R5.** Under an ok answer: its card (figures; a list with chips and progress, a row marks its element on
the page; bars; the chain of an event's path), then “Số liệu <date> · trả lời lúc <time>” and “Nguồn: …”. The
chips sit under “Bạn có thể muốn:”; the first offer “Vì sao tin này ảnh hưởng tới tôi?” and “Tạo kịch bản VN-Index
giảm mạnh”.

---

## SCR-CL-11 — Bản đồ tài chính (overview graph)

| | |
|---|---|
| Route | `#/client/tong-quan/ban-do`; RM: `#/rm/khach-hang/ban-do` |
| Generation | new in R4 (`web/pages/map.js`) |
| Feature | [FEAT-30](../../features/FEAT-30-financial-intelligence-graph.md) |
| Requirements | KIT-UX-04, OWN-UI-04; BRD-RULE-CONTENT-01 (flow 2), ADR-0008 |
| Data | `POST /api/overview` |
| Screenshots | [desktop](../../assets/current_ui/SCR-CL-11_desktop-light.jpg) · [dark](../../assets/current_ui/SCR-CL-11_desktop-dark.jpg) · [phone (list)](../../assets/current_ui/SCR-CL-11_phone-light.jpg) · [a class opened](../../assets/current_ui/SCR-CL-11_desktop-light-expanded.jpg) · [RM, every kind on](../../assets/current_ui/SCR-CL-11_desktop-light-all-rm.jpg) |

**Journey.** “What is my whole picture and what touches it?” — the client in the centre, then into a class, a
risk, a goal or a news event, and on to the page that shows it.

**Layout.** Left (c8): kind chips (Tài sản, Nguồn dữ liệu, Mục tiêu, Rủi ro, Chính sách, Tin tức — sources and
policy start off), “Đồ thị / Danh sách”, the radial graph, the note on sources and wording. Right (c4): the news
events and policy items by impact, or the selected node — figures, “Mở rộng n khoản” for a class, “Mở trang” /
“Xem đường đi của tin”, and its links with their records.

**Interaction.** Nodes are buttons (click, Enter, Space); a class also opens with double-click or `+`/`−`. The
selection lights its links and hides the other labels. News edges are dashed (“có thể ảnh hưởng”). Phones open on
the list.

**Tests.** `tests/test_overview.py`; `tests/ui/test_pages.py::test_the_overview_graph_selects_expands_and_opens_pages`,
`tests/ui/test_pages.py::test_the_overview_graph_is_a_list_on_a_phone`.

---

## SCR-CL-12 — Không gian tài chính (graph workspace)

| | |
|---|---|
| Route | `#/client/xem/<lens>` — lenses `tong-quan`, `tai-san`, `dong-tien`, `muc-tieu`, `tin`, `rui-ro`; a sheet keeps its page's old address (`#/client/tai-san`, `#/client/tin/do-thi/<event>`, `#/client/chuyen-gia`, `#/client/bo-nho`, …) and opens over its lens, so the server's links need no change; `#/client` and `#/client/tong-quan/ban-do` are the Tổng quan lens (FEAT-40) |
| Generation | proposed (experiment, branch `exp/graph-workspace`) |
| Feature | [FEAT-40](../../features/FEAT-40-persistent-financial-graph.md); reuses FEAT-30 (graph), FEAT-32 (assistant), FEAT-33 (marks) and every Customer page as a sheet |
| Requirements | OWN-GW-01…14; every requirement of SCR-CL-01…11 through the capability map in FEAT-40 |
| Data | `POST /api/overview` (+ `flow`, `liquidity`, `scenario`, `certainty`), `POST /api/dashboard` + `POST /api/flows` (strip), `GET /api/scenarios` + `POST /api/scenario` (scenarios, on request), `POST /api/assistant/stream` |
| Concept | [GW-01](../../assets/proposed_ui/GW-01_concept_persistent-graph_illustrative.png) (illustrative) |

**Journey.** The client signs in to their whole financial world: “My Wealth” in the centre with what feeds, drains,
funds, threatens and may move it. They switch lenses to explore one part, open a sheet when a task needs a form or a
table, and ask the assistant, watching the graph follow what it reads.

**Layout.** Top bar (brand, search, scope, bell, theme, account). Left: the toolbar of lenses (icons, tooltips, the
current one marked). Centre: the graph (pan, zoom, “Vừa khung”, the certainty legend, “Đồ thị / Danh sách”). Right:
the dock, tabs **Trợ lý** and **Thông tin**, collapsible to a rail. Bottom: the strip of overview cards, “Thu gọn”.
A sheet slides over the centre with its title, “Đóng”, and the page module inside.

**Interaction.** Lens → view state (no reload); node → inspector; class → holdings; sheet → over the graph, closed
back to the same state; asking → the graph follows the stream (FEAT-40). Keyboard: the toolbar is a list of buttons
(arrows, Enter), nodes are buttons, `Escape` closes a sheet, `/` focuses the search.

**Responsive / a11y.** Phone (as built, G6–G7): the toolbar is a row under the header, with a Trợ lý button that
goes to the dock. The graph comes first; the list view is one tap away. The strip is a swipeable row, and the dock
sits below the graph. A sheet takes the graph's place in the page, with a close button: the graph stays mounted
and the dock stays reachable. (A full-screen sheet covered the dock, so the assistant could not be used while a
sheet was open.) Every animation has a still equivalent under reduced motion. Colour is never the only carrier of certainty (line style and a word).

**Tests.** Planned in FEAT-40 “Acceptance”.
