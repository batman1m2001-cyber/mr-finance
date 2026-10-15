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
| Route | `#/client/tong-quan`; RM: `#/rm/khach-hang/tong-quan` |
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
(Q-03). The redesign plan replaces this page with Financial Pulse / Wealth Map / Money Flow (FEAT-29) and the
card with the Intelligence Feed (FEAT-31), keeping every block (checklist above).

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

**Known defect DEF-01.** At 1440 px the “Wealth check” card's first column is squeezed: the label wraps one word
per line and the “Mở Wealth Planning Advisor” button is a narrow column (visible in the screenshot).

---

## SCR-CL-07 — Chuyên gia (specialist team)

| | |
|---|---|
| Route | `#/client/chuyen-gia` |
| Generation | legacy (tab `rm`) |
| Features | [FEAT-28](../../features/FEAT-28-advisory-team-and-track-record.md), [FEAT-27](../../features/FEAT-27-rm-approval-queue.md) |
| Requirements | BRIEF-FLOW-02 |
| Data | `GET /api/advisory?client_id=`, `GET /api/review`, `POST /api/review/decide` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CL-07_desktop-light.jpg) |

**Layout.** The relationship specialist's card (name, title, phone, e-mail, office, hours — all mock, said so);
the **Approval queue** (“Hàng chờ chuyên gia duyệt · n đang chờ”): each proposal with its actions and summary and,
while pending, a note field with **Duyệt** / **Từ chối**; decided items with their badge and note.

**Known defect DEF-02.** The approve/reject buttons are on the client's page and the RM menu has no entry to the
queue ([information architecture](../information_architecture.md)); `review_flow` checks no role.
