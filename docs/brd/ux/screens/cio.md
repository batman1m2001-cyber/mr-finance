# CIO screens (`#/cio/…`)

Layer C. As built on 2026-10-15 (all new pages, `web/pages/`). The CIO is the demo user `cio` (Trần Quang Huy);
`cio2` exists for two-person checks. Screenshots: current state, seeded demo data.

---

## SCR-CIO-01 — Hộp tin (inbox)

| | |
|---|---|
| Route | `#/cio/hop-tin` (the CIO's first page) |
| Features | [FEAT-01](../../features/FEAT-01-news-ingestion.md), [FEAT-02](../../features/FEAT-02-cio-inbox-and-events.md) |
| Requirements | BRD-BR-01, BRD-FR-101, BRD-FR-102, BRD-FR-103, BRD-NFR-02, BRD-NFR-12 |
| Data | `GET /api/news/inbox`, `POST /api/news/ingest`, `POST /api/news/dismiss`, `POST /api/events` |
| Screenshots | [desktop](../../assets/current_ui/SCR-CIO-01_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CIO-01_phone-light.jpg) |

**Layout.** Title “<n> tin chờ xử lý”, the fetch rule (“Lấy tin tự động mỗi 10 phút từ 11 nguồn …”, last fetch),
**Lấy tin ngay**; a folded **Tình trạng nguồn tin (24 giờ)** (per source: last fetch, items per hour); filters
(source, international/domestic, relevance, words); the list — checkbox, headline, outlet · kind · time · type
hint, relevance badge (Thấp / Vừa / Liên quan cao, “Độc quyền” for released research) — 40 at a time with “more”;
**Bỏ tin** and **Gom thành sự kiện** act on the checked items.

**States.** Empty filter: “Không có tin nào khớp bộ lọc”. Held items are not here (→ SCR-CMP-01).

---

## SCR-CIO-02 — Sự kiện & nhận định (events)

| | |
|---|---|
| Route | `#/cio/nhan-dinh`; an event: `#/cio/nhan-dinh/EV-2026-nnnn` |
| Features | [FEAT-02](../../features/FEAT-02-cio-inbox-and-events.md), [FEAT-04](../../features/FEAT-04-cio-agent.md) |
| Requirements | BRD-FR-103, BRD-FR-105, BRD-FR-301, BRD-FR-307 |
| Data | `GET /api/events`, `GET /api/events/{id}`, `POST /api/events/run-agent`, `GET /api/agents` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CIO-02_desktop-light.jpg) |

**Layout.** The list of events (newest first) with their views' status badges; an event shows its **Tin nguồn**
(with held items marked) and the **Agent CIO** panel — the mode a run would use (live with the two models, or
“Mô phỏng”) and **Chạy Agent CIO**; then its versions.

**States.** “Chưa có sự kiện”; a held event says what is held and by whom it can be released.

---

## SCR-CIO-03 — Nhận định (view detail)

| | |
|---|---|
| Route | `#/cio/nhan-dinh/VW-nnnn-vN` |
| Features | [FEAT-04](../../features/FEAT-04-cio-agent.md), [FEAT-05](../../features/FEAT-05-challenger.md), [FEAT-06](../../features/FEAT-06-view-decisions.md) |
| Requirements | BRD-BR-05, BRD-BR-06, BRD-BR-07, BRD-BR-14, BRD-FR-302…305, BRD-FR-704, BRD-RULE-LC-01 |
| Data | `GET /api/views/{id}`, `POST /api/views/decide` |
| Screenshots | [desktop](../../assets/current_ui/SCR-CIO-03_desktop-light.jpg) · [desktop dark](../../assets/current_ui/SCR-CIO-03_desktop-dark.jpg) · [phone](../../assets/current_ui/SCR-CIO-03_phone-light.jpg) |

**Journey.** Read the view, see what the challenger found, answer it, check the market preview, decide.

**Layout.**
1. Header: back to the event, “NHẬN ĐỊNH VW-0001-V1 · MÔ PHỎNG, KHÔNG GỌI AI” (or the models), a progress line
   *Agent soạn → Phản biện → CIO duyệt → Đã duyệt*, the status badge.
2. **Nhận định** (summary, mode badge, priced-in, content hash) beside **Điều kiện duyệt** — the a–g checklist
   with ✓/✕ and the reason of each failure — and the action area: reason field and the buttons the status allows
   (**Duyệt và áp dụng**, disabled until every check passes; Trả lại; Bác; **Thu hồi nhận định** once approved).
3. **Kịch bản** — a probability bar of the branches, then one card per branch: name, probability, regime, core
   shocks as chips (factor ▲/▼ size), “Lan truyền ra thị trường” (FR-305 preview: every factor's move, bars scaled to
   a usual 1-month move), “Lập luận”.
4. **Dòng tác động** (−3…+3 per target, horizon, confidence) beside **Phản biện độc lập** (findings by severity, each
   with its answer field while open).
5. **Lần áp dụng** — the run(s) this approval made, with status, total and flagged families.
6. **Vết chạy agent (từng bước)** — folded: each node's input, prompt, prompt version, model, output, time.

**Edits.** Editing summary, impact rows or branches is schema-checked and sends the view back to the challenger.

---

## SCR-CIO-04 — Phơi nhiễm (exposure)

| | |
|---|---|
| Route | `#/cio/phoi-nhiem` |
| Feature | [FEAT-08](../../features/FEAT-08-application-runs.md) |
| Requirements | BRD-BR-13, BRD-FR-403 |
| Data | `GET /api/runs`, `GET /api/runs/{id}` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CIO-04_desktop-light.jpg) |

For the latest effective run: **Theo yếu tố** (the total 3-month expected change by factor across all families),
**Xếp hạng gia đình** (worst first, flagged families marked), **Bản đồ nhiệt** (families × factors, % of net worth).
Empty: “Chưa có lần áp dụng nào đang hiệu lực”.

---

## SCR-CIO-05 — Lần áp dụng (application runs)

| | |
|---|---|
| Route | `#/cio/ap-dung[/AR-…]` |
| Feature | [FEAT-08](../../features/FEAT-08-application-runs.md) |
| Requirements | BRD-FR-401, BRD-FR-405, BRD-FR-501, BRD-FR-502, BRD-RULE-LC-02, BRD-NFR-04 |
| Data | `GET /api/runs[/{id}]`, `GET /api/runs/{id}/verify`, `POST /api/runs/recompute`, `POST /api/runs/decide` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CIO-05_desktop-light.jpg) |

**Layout.** Header: run id and status badge, its view, families, price date, model version, engine version;
**Kiểm tra tính lại** (verify to the dong) and **Thẩm định lại với dữ liệu mới** (recompute). **Tổng kỳ vọng 3
tháng** (total, flagged families, snapshot id and SHA-256) beside **Hậu kiểm** (summary + findings P1–P5 by severity
and family) and the reason field with **Thu hồi lần áp dụng** (or “Cho hiệu lực” for a held run). **Lịch sử trạng
thái** (COMPUTING → POST_CHECKING → EFFECTIVE, who, note). **Mọi lần áp dụng** (all runs, status, total, flagged,
time).

---

## SCR-CIO-06 — Nghiên cứu (research, CIO)

| | |
|---|---|
| Route | `#/cio/nghien-cuu` |
| Features | [FEAT-03](../../features/FEAT-03-research-and-regulation-notes.md), [FEAT-10](../../features/FEAT-10-goal-branch.md) |
| Requirements | BRD-FR-201, BRD-FR-204, BRD-FR-603, BRD-FR-604 |
| Data | `GET /api/research`, `GET /api/goals/regulation`, `POST /api/research` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CIO-06_desktop-light.jpg) |

**Layout.** “<n> chờ phát hành · <m> đã xử lý” and the rules in one paragraph; a folded **Nạp báo cáo mới** form
(kind, number, release time, conflicts, title, summary; for a regulation note: document, status, effective date,
prep weeks, purposes, countries, documents, client message, RM hint); the list — kind, title, number, release time,
uploader, decider, summary, the regulation's details, “<n> mục tiêu bị ảnh hưởng” (matches with level badges), the
status badge.

---

## SCR-CIO-07 — Mô hình (factor model)

| | |
|---|---|
| Route | `#/cio/mo-hinh` |
| Features | [FEAT-07](../../features/FEAT-07-scenario-engine.md), [FEAT-14](../../features/FEAT-14-versioned-configuration.md) |
| Requirements | BRD-RULE-ENG-08…11, BRD-FR-701 (read-only) |
| Data | `GET /api/model` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CIO-07_desktop-light.jpg) |

Version (FM-DEMO-2026-10) with “tham số giả định”; **Cách tính** (the four steps in words, the stressed-matrix
repair figures); **15 yếu tố** — group, S/M/L sizes, realisation at 1 week / 3 months / 12 months (the BRD's), monthly
volatility normal / stressed, each assumed value badged “giả định”. Read-only: no edit or approval (FR-701 gap).

---

## SCR-CIO-08 — Agent (catalogue and AI quality)

| | |
|---|---|
| Route | `#/cio/agent`; Compliance: `#/compliance/agent` |
| Generation | new (`web/pages/agents.js`) |
| Feature | [FEAT-15](../../features/FEAT-15-agent-catalogue.md) |
| Requirements | BRD-FR-703, BRD-RULE-MEAS-04 |
| Data | `GET /api/agents/catalogue?days=7` |
| Screenshots | [desktop](../../assets/current_ui/SCR-CIO-08_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CIO-08_phone-light.jpg) |

One card per task: name and mode badge (Trực tiếp / Mô phỏng / Từ khóa / Mẫu tất định / Chưa xây), purpose, owner,
risk (badge and why), model (configured and the BRD default, with the resource), what it may read, latest run (id,
subject, time, mode, status). Then **Chất lượng AI** (7 days and all time) and **Tham khảo mã nguồn mở**.

---

## SCR-CIO-09 — Cấu hình (versioned configuration)

| | |
|---|---|
| Route | `#/cio/cau-hinh`; Compliance: `#/compliance/cau-hinh` |
| Generation | new (`web/pages/config.js`) |
| Feature | [FEAT-14](../../features/FEAT-14-versioned-configuration.md) |
| Requirements | BRD-FR-701, BRD-RULE-SEC-04, BRD-RULE-SEC-05 |
| Data | `GET /api/config`, `POST /api/config/propose`, `POST /api/config/decide` |
| Screenshots | [desktop, a pending proposal](../../assets/current_ui/SCR-CIO-09_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CIO-09_phone-light.jpg) |

One panel per kind: owner and “hai người”, the version in force (number, id, hash, who approved), its content in
short; a pending proposal with who proposed, when, why, its content, and — for the owner's role — an approver
picker (the proposer left out where two people are required), **Duyệt** and **Từ chối**; for thresholds and the
restricted list an “Đề xuất thay đổi” JSON editor with a reason; the history.

