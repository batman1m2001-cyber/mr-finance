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
| Generation | legacy (`web/app.js`, tab `overview`) |
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
| Generation | legacy (tab `sources`) |
| Features | [FEAT-20](../../features/FEAT-20-consolidation.md), [FEAT-22](../../features/FEAT-22-statement-reading.md), [FEAT-23](../../features/FEAT-23-chat-declaration.md) |
| Requirements | BRIEF-DATA-01…05 |
| Data | `POST /api/dashboard`, `POST /api/statement`, `POST /api/declare` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CL-02_desktop-light.jpg) |

**Layout.** Two input cards — **Tải sao kê** (choose a PDF/Excel/CSV file, or “Dùng sao kê mẫu: vps_C01.csv”) and
**Bổ sung tài sản** (chat, with four example sentences) — then **Tất cả tài sản và khoản nợ**: holdings grouped
by class (collapsible), each with source and trust badge (Đã xác thực / Từ sao kê / Bạn tự khai), purchase date
and price, cost, current value, P&L; totals: assets, debt, net worth.

**Actions.** Upload a statement → its holdings appear labelled “Từ sao kê”; send a chat sentence → the reply says
what was recorded and the table grows; collapse a class.

**States.** Upload/agent errors are shown inline; without a model the rule paths answer (ADR-0015 D2).

---

## SCR-CL-03 — Kế hoạch (Wealth Planning Advisor)

| | |
|---|---|
| Route | `#/client/muc-tieu/ke-hoach`; RM: `#/rm/khach-hang/ke-hoach` |
| Generation | legacy (tab `scenarios`) |
| Features | [FEAT-26](../../features/FEAT-26-life-scenarios-stress-tests-and-goals.md), [FEAT-27](../../features/FEAT-27-rm-approval-queue.md) |
| Requirements | BRIEF-SCEN-01…03 |
| Data | `POST /api/goals`, `POST /api/scenario`, `GET /api/scenarios`, `POST /api/review/propose`, `GET /api/review` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CL-03_desktop-light.jpg) |

**Layout.** “Wealth view” KPI strip (total net worth, portfolio P&L, goals funded, 12-month net cash flow), cash-flow
chart and need-vs-have bars per goal, the monthly saving needed; then **Life goals** list (grouped: family &
children, wealth building, retirement & transfer, risk reserve, decisions & stress tests) beside the selected
item: status, goal status (need / have / gap), performance tracking (this month vs expected, start of year / last
month / now), **Required action** (ranked, each “Gửi chuyên gia duyệt”), **Calculation details** (editable
assumptions + “Chạy lại”, before/after table), and the light / heavy options.

**Actions.** Pick a goal or a stress test; edit assumptions and rerun; send an action or option to the specialist
queue (→ SCR-CL-07).

**Notes.** The regulation note of the goal branch is not shown on these goal cards (Q-20).


**Since 2026-10-16 (FR-603, Q-20).** “Lưu ý quy định cho mục tiêu” sits under the Wealth view: each released
regulation note that applies to a goal, with its level and milestone (the client sees only notes with a client
message).
---

## SCR-CL-04 — Khẩu vị rủi ro (risk test)

| | |
|---|---|
| Route | `#/client/muc-tieu/khau-vi` |
| Generation | legacy (tab `risk`) |
| Feature | [FEAT-24](../../features/FEAT-24-risk-test.md) |
| Requirements | BRIEF-RISK-01…05 |
| Data | `POST /api/risk` |
| Screenshot | [desktop, start state](../../assets/current_ui/SCR-CL-04_desktop-light.jpg) |

**Journey.** “Bắt đầu cho <name>” → 8–12 situational questions, one at a time, each depending on the last → the
result: tolerance, capacity, the mismatch sentence when they differ, the persona, the new drawdown limit (which
the overview then uses).

---

## SCR-CL-05 — Tác động thị trường (family impact, client)

| | |
|---|---|
| Route | `#/client/tin/thi-truong` |
| Generation | new (`web/pages/impact.js`) |
| Features | [FEAT-13](../../features/FEAT-13-impact-delivery-by-role.md), [FEAT-10](../../features/FEAT-10-goal-branch.md) |
| Requirements | BRD-BR-08, BRD-BR-10, BRD-FR-502, BRD-RULE-CONTENT-01 (flow 2), BRD-RULE-CONTENT-02, BRD-NFR-11 |
| Data | `GET /api/families/{id}/impact?role=client`, `GET /api/goals/regulation?family_id=&role=client` |
| Screenshots | [desktop](../../assets/current_ui/SCR-CL-05_desktop-light.jpg) · [desktop dark](../../assets/current_ui/SCR-CL-05_desktop-dark.jpg) · [phone](../../assets/current_ui/SCR-CL-05_phone-light.jpg) |

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
No “Cách tính” drawer for the client (Q-14).

---

## SCR-CL-06 — Chi phí chính sách (policy costs)

| | |
|---|---|
| Route | `#/client/tin/chinh-sach`; RM: `#/rm/khach-hang/chinh-sach` |
| Generation | legacy (tab `alerts`) |
| Feature | [FEAT-25](../../features/FEAT-25-policy-cost-alerts-and-house-views.md) |
| Requirements | BRIEF-IMPACT-01…05, BRIEF-ALERT-01, BRIEF-ALERT-02 |
| Data | `POST /api/alerts`, `GET /api/views`, `POST /api/goals` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CL-06_desktop-light.jpg) |

**Layout.** “Wealth check” (YTD return vs benchmark, goals tracked, required actions, link to the planning
advisor); **Tác động lên tài sản ròng** (diverging bars per policy, filter all / risks / opportunities, the formula);
**House views** (8 mock research-house views matched to holdings, 2 shown + “Xem thêm”); the mock-data and
legal-status notes; **Policy headlines** — one card per policy with level, legal status, the impact (with
probability), holding × sensitivity × probability, the holdings touched, the source line.

**DEF-01 (fixed 2026-10-15).** The “Wealth check” card was squeezed into an 18 px column at 1440 px: the new pages'
`.check` checklist rule (`web/core/tokens.css`) also matched this legacy card. The rule is now scoped to `#page-new`.

---

## SCR-CL-07 — Chuyên gia (specialist team)

| | |
|---|---|
| Route | `#/client/chuyen-gia` |
| Generation | legacy (tab `rm`) |
| Features | [FEAT-28](../../features/FEAT-28-advisory-team-and-track-record.md), [FEAT-27](../../features/FEAT-27-rm-approval-queue.md) |
| Requirements | BRIEF-FLOW-02 |
| Data | `GET /api/advisory?client_id=`, `GET /api/review` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CL-07_desktop-light.jpg) |

**Layout.** The relationship specialist's card (name, title, phone, e-mail, office, hours — all mock, said so);
the **Approval queue** (“Hàng chờ chuyên gia duyệt · n đang chờ”): each proposal with its actions and summary and,
while pending, “Đang chờ chuyên gia duyệt”; decided items with their badge and note. Read-only: the RM decides on
[SCR-RM-06](rm.md#scr-rm-06--duyệt-đề-xuất-approval-queue) (DEF-02 fixed 2026-10-15).

---

## SCR-CL-08 — Toàn cảnh (Pulse, Wealth Map, Money Flow)

| | |
|---|---|
| Route | `#/client/tong-quan/toan-canh` (client's first page); RM: `#/rm/khach-hang/toan-canh` |
| Generation | new (`web/pages/pulse.js`) |
| Feature | [FEAT-29](../../features/FEAT-29-financial-pulse-wealth-map-money-flow.md) |
| Requirements | KIT-UX-01, KIT-UX-02, KIT-UX-03, KIT-UX-05, KIT-UX-06; BRIEF-DASH-01 (net worth), BRIEF-DASH-02 (allocation) |
| Data | `POST /api/dashboard`, `POST /api/flows`, `POST /api/feed` |
| Screenshots | [desktop](../../assets/current_ui/SCR-CL-08_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CL-08_phone-light.jpg) · [dark](../../assets/current_ui/SCR-CL-08_desktop-dark.jpg) |

**Journey.** In one screen: what I am worth and how it moved, what came in and went out last month and what was
left, how long my reserve lasts, how exposed I am — then where the money sits and where it flowed.

**Layout.** KPI strip of six tiles (2 columns on a phone, 3 below 1100 px). **Điều đáng chú ý** (FEAT-31): each
item with a severity badge, title, why, source, and a link to its evidence; the rules beneath. **Bản đồ tài sản** (5/12): a 100 % bar
by class, a legend with value and share, a class opens its holdings. **Dòng tiền** (7/12): month picker, Sankey
(blue in, orange out, green “Còn lại” / red “Thiếu hụt”), the table of bands, a band opens its transactions.
A link to “Chi tiết” (SCR-CL-01).

**States.** A month with no rows: “Không có giao dịch trong tháng này.”; a failed flows call keeps the page and
shows the error under the chart.

**Interaction.** Bands and map segments are focusable buttons (Enter / Space); tooltips on hover and focus; no
animation (reduced motion needs nothing more).

---

## SCR-CL-09 — Đồ thị tác động (Intelligence Graph)

| | |
|---|---|
| Route | `#/client/tin/do-thi`; RM: `#/rm/khach-hang/do-thi` |
| Generation | new (`web/pages/graph.js`) |
| Feature | [FEAT-30](../../features/FEAT-30-financial-intelligence-graph.md) |
| Requirements | KIT-UX-04, KIT-UX-06; BRD-RULE-CONTENT-01 (flow 2) |
| Data | `GET /api/families/{id}/graph?role=client\|rm` |
| Screenshots | [desktop](../../assets/current_ui/SCR-CL-09_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CL-09_phone-light.jpg) · [dark](../../assets/current_ui/SCR-CL-09_desktop-dark.jpg) · [RM, a node selected](../../assets/current_ui/SCR-CL-09_desktop-light-rm.jpg) |

**Journey.** “Which news reaches my money, through what, and down to which goal?” — read left to right.

**Layout.** One panel: “Đồ thị / Danh sách” switch, seven type filters (chips, struck through when hidden), the
graph in seven columns (Tin, Sự kiện, Kịch bản, Yếu tố, Tài sản, Gia đình, Mục tiêu), the detail panel, the
note that edges are potential impacts with stored sources.

**Interaction.** A node is a focusable button: click, Enter or Space selects it, lights its path and dims the
rest; again or “Bỏ chọn” clears. Tooltips on nodes and edges. Phones open on the list.

**States.** No effective run: “Chưa có tin nào được CIO duyệt áp dụng cho gia đình này”.

---

## SCR-CL-10 — OneWealth Copilot (panel, all roles)

| | |
|---|---|
| Route | none: a panel over every page of every role, opened by “✦ Hỏi OneWealth” (bottom right) |
| Generation | new (`web/copilot.js`) |
| Feature | [FEAT-32](../../features/FEAT-32-copilot.md) |
| Requirements | KIT-COPILOT-01…05; BRD-BR-11, BRD-NFR-08 |
| Data | `POST /api/copilot` |
| Screenshots | [client](../../assets/current_ui/SCR-CL-10_desktop-light.jpg) · [RM confirm](../../assets/current_ui/SCR-CL-10_desktop-light-rm.jpg) · [phone](../../assets/current_ui/SCR-CL-10_phone-light.jpg) |

**Layout.** Header with the router label (“bộ định tuyến từ khóa” or the model), the page context (“Đang xem:
Toàn cảnh · Khách hàng · Nguyễn Minh Khoa”), the conversation (answers with a status badge when failed,
forbidden or pending; “Mở … →” evidence link; “Mô hình thấy gì”), suggestion chips, the input, and the note that
the model only picks a tool and that this is not investment advice.

**Interaction.** Enter sends; a pending write shows **Xác nhận** / **Huỷ**; Esc or ✕ closes and returns focus to
the button; a navigate answer changes the page. Phones: the panel fills the width.
