# RM screens (`#/rm/…`)

Layer C. As built on 2026-10-15; screenshots are current state with seeded demo data (three effective runs,
EV-2026-0001…0003). The RM is the demo user `rm01` (Phạm Gia Bảo); every RM screen shows “Đang dùng … demo”.
Inside **Khách hàng**, the client picker chooses the family, and the client pages SCR-CL-08/01/02/03/06 appear in
staff mode ([client.md](client.md)).

---

## SCR-RM-01 — Hôm nay (today)

| | |
|---|---|
| Route | `#/rm/hom-nay` (the RM's first page) |
| Generation | new (`web/pages/today.js`) |
| Features | [FEAT-13](../../features/FEAT-13-impact-delivery-by-role.md), [FEAT-10](../../features/FEAT-10-goal-branch.md) |
| Requirements | BRD-BR-09, BRD-FR-503, BRD-FR-603, BRD-RULE-WF-07 |
| Data | `GET /api/rm/today` |
| Screenshots | [desktop](../../assets/current_ui/SCR-RM-01_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-RM-01_phone-light.jpg) |

**Journey.** Morning: which families must I look at before anything reaches them, and in what order? Then which
goals need a call because of a new regulation?

**Layout.** Hero “HÔM NAY · CẦN XEM TRƯỚC” with the number of families whose 3-month bad case (P10) reaches −5 %
of net worth; the rule in one line (“Chỉ tính các lần áp dụng đã qua hậu kiểm và đang hiệu lực”). **Danh sách** —
one row per family, worst first: name and net worth, the events that crossed the threshold, the 3-month expected
change (VND and %), the worst P10 % and its event, “Mở”. **Việc theo mục tiêu** — level badge (RM liên hệ ngay /
RM xác nhận mục tiêu / Nhắc trên thẻ mục tiêu), family · goal · purpose · country, the regulation (draft/issued),
the preparation milestone, the RM's task.

**Actions.** A row opens that family's impact (→ SCR-RM-02).

**States.** Empty list: “Không có ca nào cần xem trước — Khi một lần áp dụng có gia đình chạm ngưỡng −5%, ca đó
hiện ở đây.”; empty goal tasks: “Không có việc nào theo mục tiêu …”.

**Notes.** The browser groups the server's per-run cases by family and sums their expected changes (a
presentation-side sum; [architecture](../../architecture/system_overview.md#4-logic-in-the-presentation-layer)).
The RM sees every family: no assignment (Q-17).

---

## SCR-RM-02 — Tác động tin (family impact, staff)

| | |
|---|---|
| Route | `#/rm/khach-hang/tac-dong` |
| Generation | new (`web/pages/impact.js`, staff mode) |
| Features | [FEAT-13](../../features/FEAT-13-impact-delivery-by-role.md), [FEAT-09](../../features/FEAT-09-number-trace.md), [FEAT-10](../../features/FEAT-10-goal-branch.md) |
| Requirements | BRD-BR-08, BRD-BR-12, BRD-BR-14, BRD-FR-402, BRD-FR-404, BRD-FR-406, BRD-FR-502, BRD-FR-601, BRD-NFR-11 |
| Data | `GET /api/families/{id}/impact?role=rm`, `GET /api/goals/regulation?family_id=`, `POST /api/goals/outflow` |
| Screenshots | [desktop](../../assets/current_ui/SCR-RM-02_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-RM-02_phone-light.jpg) |

Same structure as [SCR-CL-05](client.md#scr-cl-05--tác-động-thị-trường-family-impact-client), plus: event
**headlines** instead of types; superseded and withdrawn runs with their labels (“Đã thu hồi”); a **“Cách tính”**
link per event (→ SCR-RM-03); “Chi tiết cho RM: theo yếu tố và theo vị thế” (contributions by factor and by
holding); **Mục tiêu** — the selected event's effect on each dated goal (funding before → after
with Đạt / Theo dõi / Thiếu, FR-404; also on SCR-CL-05); the goal panel with inferred goals (“RM xác nhận mục tiêu”) and a form “Khai dòng tiền ra nước ngoài cho
mục tiêu (RM)” to declare purpose and country (FR-601).

---

## SCR-RM-03 — Cách tính (trace drawer)

| | |
|---|---|
| Opened from | “Cách tính” on SCR-RM-02 |
| Generation | new (`web/pages/trace.js`, `drawer()` in `web/core/core.js`) |
| Feature | [FEAT-09](../../features/FEAT-09-number-trace.md) |
| Requirements | BRD-BR-12, BRD-FR-406, BRD-NFR-11 |
| Data | `GET /api/trace/{run_id}/{family_id}` |
| Screenshot | [desktop](../../assets/current_ui/SCR-RM-03_desktop-light.jpg) |

**Layout.** A right-hand drawer, a vertical timeline: **Con số** (the number, its band, the formula sentence) →
**Vị thế góp phần nhiều nhất** (holding, method: beta, USD revenue share, R², “theo mô hình” proxies, contribution)
→ **Kịch bản (Agent CIO soạn, CIO duyệt)** (each branch: probability, regime, core shocks, the family's change in
that branch) → the approval, the event, the news (outlet, link, time) → the snapshot (hash, price date, model,
engine).

**Interaction.** `role="dialog"`, `aria-modal`, focus on the close button, Esc or the backdrop closes it.

---

## SCR-RM-04 — Hiệu quả tư vấn (of one client)

| | |
|---|---|
| Route | `#/rm/khach-hang/hieu-qua` |
| Generation | legacy (tab `performance`) |
| Feature | [FEAT-28](../../features/FEAT-28-advisory-team-and-track-record.md) |
| Requirements | none (Q-19) |
| Data | `GET /api/advisory?client_id=` |
| Screenshot | [desktop](../../assets/current_ui/SCR-RM-04_desktop-light.jpg) |

**Layout.** “NỘI BỘ” banner (staff only). KPI tiles (recommendations, hit rate, money gained, losses, missed
actions, missed news); **AI pipeline** (four AI stages with a 0–100 score, a 12-month sparkline and stage counts);
**Nhật ký khuyến nghị**; **Tin quan trọng bị bỏ lỡ**; news-reading engagement; risk appetite over time. All mock,
said at the bottom (“Dữ liệu giả định cho demo …”).

**Caution.** Not accuracy tracking (BR-15 is not built); the page note says it is illustrative and not accuracy
tracking (Q-19).

---

## SCR-RM-05 — Hiệu quả tư vấn (all clients)

| | |
|---|---|
| Route | `#/rm/hieu-qua` |
| Generation | legacy (tab `perfall`) |
| Feature | [FEAT-28](../../features/FEAT-28-advisory-team-and-track-record.md) |
| Data | `GET /api/advisory/all` |
| Screenshot | [desktop](../../assets/current_ui/SCR-RM-05_desktop-light.jpg) |

The same record summed over the five clients: KPI tiles, AI pipeline scores per client, a per-client table (a row
opens that client's SCR-RM-04), the recommendation log, missed news, engagement. Same caution as SCR-RM-04.

---

## SCR-RM-06 — Duyệt đề xuất (approval queue)

| | |
|---|---|
| Route | `#/rm/khach-hang/duyet` |
| Generation | legacy (tab `rm`, staff mode) |
| Feature | [FEAT-27](../../features/FEAT-27-rm-approval-queue.md) |
| Requirements | BRIEF-FLOW-02, BRIEF-SCEN-03 |
| Data | `GET /api/review`, `POST /api/review/decide` (`by` = the RM) |
| Screenshot | [desktop](../../assets/current_ui/SCR-RM-06_desktop-light.jpg) |

The options the picked client sent from Kế hoạch: actions, summary numbers, a note field, **Duyệt** / **Từ chối**;
decided items below with their badge and note. Only an RM may decide (server check). Added 2026-10-15 (DEF-02).
