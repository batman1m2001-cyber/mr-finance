# Assets

Screenshots, mockups and reference images. **State** says what an image shows:
`original` (from a source document), `current` (the running product), `proposed` (a design not built),
`approved` (a design accepted for building). An image is never evidence that a behaviour works — tests are.
Images of mock data show invented clients and prices.

Naming: `<screen id>_<device>-<theme>.jpg` for screenshots; `KIT-nn_<what>.png` for kit images. Replace a
screenshot when its screen changes (same name), and say so in the changelog.

The BRD's own five figures are **not** stored here (ADR-0001); they are identified by hash in
[`../requirements/original_brd_reference.md`](../requirements/original_brd_reference.md#figures) and redrawn as
diagrams in [`../architecture/`](../architecture/).

## current_ui/ — the product on 2026-10-15

Captured with Playwright (`deviceScaleFactor` 1, JPEG q78) from the dev server on the code of commit b5e1cb1; no
page error, console error or horizontal scroll in any capture.

| File | Screen | State | Device, theme | Source, date |
|---|---|---|---|---|
| `SCR-CIO-01_desktop-light.jpg` | SCR-CIO-01 Hộp tin | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CIO-01_phone-light.jpg` | SCR-CIO-01 Hộp tin | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CIO-02_desktop-light.jpg` | SCR-CIO-02 Sự kiện & nhận định | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CIO-03_desktop-dark.jpg` | SCR-CIO-03 Nhận định | current | desktop 1440×900, dark, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CIO-03_desktop-light.jpg` | SCR-CIO-03 Nhận định | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CIO-03_phone-light.jpg` | SCR-CIO-03 Nhận định | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CIO-04_desktop-light.jpg` | SCR-CIO-04 Phơi nhiễm | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CIO-05_desktop-light.jpg` | SCR-CIO-05 Lần áp dụng | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CIO-06_desktop-light.jpg` | SCR-CIO-06 Nghiên cứu (upload) | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CIO-07_desktop-light.jpg` | SCR-CIO-07 Mô hình | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, dev server, market history backfilled from 2020 |
| `SCR-CIO-07_phone-light.jpg` | SCR-CIO-07 Mô hình | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-16, dev server, market history backfilled from 2020 |
| `SCR-CIO-11_desktop-light.jpg` | SCR-CIO-11 Dữ liệu thị trường | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, dev server, market history backfilled from 2020 |
| `SCR-CIO-11_phone-light.jpg` | SCR-CIO-11 Dữ liệu thị trường | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-16, dev server, market history backfilled from 2020 |
| `SCR-CIO-12_desktop-light.jpg` | SCR-CIO-12 Độ chính xác | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, dev server on a copy of the live state (market history from 2020, two approved views) |
| `SCR-CIO-12_phone-light.jpg` | SCR-CIO-12 Độ chính xác | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-16, dev server on a copy of the live state (market history from 2020, two approved views) |
| `SCR-CIO-13_desktop-light.jpg` | SCR-CIO-13 Đo lường | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, dev server on a copy of the live state (market history from 2020, two approved views) |
| `SCR-CIO-13_phone-light.jpg` | SCR-CIO-13 Đo lường | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-16, dev server on a copy of the live state (market history from 2020, two approved views) |
| `SCR-ADM-01_desktop-light.jpg` | SCR-ADM-01 Hệ thống | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, dev server on a copy of the live state, after a load of the history since 2026-10-01 |
| `SCR-ADM-01_phone-light.jpg` | SCR-ADM-01 Hệ thống | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-16, dev server on a copy of the live state, after a load of the history since 2026-10-01 |
| `SCR-CIO-14_desktop-light.jpg` | SCR-CIO-14 Bản tin (CIO), the form open | current | desktop 1440×900, light, full page | 2026-10-16, BRD completion F8, dev server in inbox mode (two approved views) |
| `SCR-CIO-14_phone-light.jpg` | SCR-CIO-14 Bản tin (CIO) | current | phone 390×844, light, viewport | 2026-10-16, BRD completion F8, dev server in inbox mode (two approved views) |
| `FEAT-17-draft_desktop-light.jpg` | FEAT-17 a draft letter (CIO): the agent's fallback reason, the edit panel | current | desktop 1440×900, light, full page | 2026-10-16, BRD completion F8, dev server in inbox mode (two approved views) |
| `SCR-CMP-04_desktop-light.jpg` | SCR-CMP-04 an approved letter (Compliance), Private 2 hours early with its reason | current | desktop 1440×900, light, full page | 2026-10-16, BRD completion F8, dev server in inbox mode (two approved views) |
| `SCR-CMP-04_phone-light.jpg` | SCR-CMP-04 an approved letter (Compliance) | current | phone 390×844, light, viewport | 2026-10-16, BRD completion F8, dev server in inbox mode (two approved views) |
| `SCR-CMP-05_desktop-light.jpg` | SCR-CMP-05 the policy radar (Compliance) | current | desktop 1440×900, light, full page | 2026-10-16, BRD completion F9, dev server; two real documents from the Official Gazette (113/2026 and 112/2026/VBHN-TT-NHNN), the first verified and summarised in mock mode |
| `SCR-CMP-05_phone-light.jpg` | SCR-CMP-05 the policy radar (Compliance) | current | phone 390×844, light, viewport | 2026-10-16, BRD completion F9, dev server; two real documents from the Official Gazette (113/2026 and 112/2026/VBHN-TT-NHNN), the first verified and summarised in mock mode |
| `SCR-CMP-05-document_desktop-light.jpg` | SCR-CMP-05 one document (CIO): summary, quotes, text | current | desktop 1440×900, light, full page | 2026-10-16, BRD completion F9, dev server; two real documents from the Official Gazette (113/2026 and 112/2026/VBHN-TT-NHNN), the first verified and summarised in mock mode |
| `SCR-CMP-05-document_phone-light.jpg` | SCR-CMP-05 one document (CIO) | current | phone 390×844, light, viewport | 2026-10-16, BRD completion F9, dev server; two real documents from the Official Gazette (113/2026 and 112/2026/VBHN-TT-NHNN), the first verified and summarised in mock mode |
| `FEAT-16-quote_desktop-light.jpg` | FEAT-16 a quote clicked: scrolled to and outlined in the document's text | current | desktop 1440×900, light, viewport | 2026-10-16, BRD completion F9, dev server; two real documents from the Official Gazette (113/2026 and 112/2026/VBHN-TT-NHNN), the first verified and summarised in mock mode |
| `SCR-ADM-01-alerts_desktop-light.jpg` | SCR-ADM-01 Hệ thống, “Cảnh báo” | current | desktop 1440×900, light, viewport at the section | 2026-10-16, dev server, after an unsigned package to the inbox was rejected (AL-000001) |
| `SCR-ADM-01-alerts_phone-light.jpg` | SCR-ADM-01 Hệ thống, “Cảnh báo” | current | phone 390×844, light, viewport at the section | as above |
| `FEAT-36-bell-cio_desktop-light.jpg` | the bell, CIO: the open alert first, then new news | current | desktop 1440×900, light, bell open | as above |
| `FEAT-36-bell-admin_phone-light.jpg` | the bell, Admin: system alerts | current | phone 390×844, light, bell open | as above |
| `SCR-ADM-01-zone_desktop-light.jpg` | SCR-ADM-01 Hệ thống, “Vùng AI và hộp chờ” | current | desktop 1440×900, light, viewport at the section | 2026-10-16, dev server :8031 in inbox mode beside the AI zone :8041, after the zone's package IN-000001 was imported |
| `SCR-ADM-01-zone_phone-light.jpg` | SCR-ADM-01 Hệ thống, “Vùng AI và hộp chờ” | current | phone 390×844, light, viewport at the section | as above |
| `SCR-CIO-03-inbox_desktop-light.jpg` | SCR-CIO-03 Nhận định, a view from the AI zone | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, VW-0004-v1 imported from the zone (zone in mock), waiting for the CIO |
| `SCR-CIO-03-inbox_phone-light.jpg` | SCR-CIO-03 Nhận định, a view from the AI zone | current | phone 390×844, light, full page (≤ 2,600 px) | as above |
| `SCR-CIO-08_desktop-light.jpg` | SCR-CIO-08 Agent | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, dev server, mock agents, three approved views |
| `SCR-CIO-08_phone-light.jpg` | SCR-CIO-08 Agent | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-16, dev server, mock agents, three approved views |
| `SCR-CIO-09_desktop-light.jpg` | SCR-CIO-09 Cấu hình | current | desktop 1440×900, light, viewport at the prompts panel | 2026-10-16 (F4), dev server on a copy of the live state, the second Admin on a prompts proposal whose eval set could not run (AI off) |
| `SCR-CIO-09_phone-light.jpg` | SCR-CIO-09 Cấu hình | current | phone 390×844, light, from the prompts panel down | 2026-10-16 (F4), dev server, the second Admin |
| `SCR-CIO-10_desktop-light.jpg` | SCR-CIO-10 Đồ thị lần áp dụng | current | desktop 1440×900, light, full page | 2026-10-16, UI redesign R4, dev server, one approved event (client C01) |
| `SCR-CIO-10_phone-light.jpg` | SCR-CIO-10 Đồ thị lần áp dụng | current | phone 390×844, light, the list view | 2026-10-16, UI redesign R4, dev server, one approved event (client C01) |
| `SCR-CL-01_desktop-light.jpg` | SCR-CL-01 Tổng quan | current | desktop 1440×900, light, full page | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-01_phone-light.jpg` | SCR-CL-01 Tổng quan | current | phone 390×844, light, full page | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-02_desktop-light.jpg` | SCR-CL-02 Tài sản | current | desktop 1440×900, light, full page | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-02_phone-light.jpg` | SCR-CL-02 Tài sản | current | phone 390×844, light, full page | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-03_desktop-light.jpg` | SCR-CL-03 Kế hoạch | current | desktop 1440×900, light, full page | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-03_phone-light.jpg` | SCR-CL-03 Kế hoạch | current | phone 390×844, light, full page | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-04_desktop-light.jpg` | SCR-CL-04 Khẩu vị rủi ro | current | desktop 1440×900, light, full page | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-04_phone-light-question.jpg` | SCR-CL-04 Khẩu vị rủi ro | current | phone 390×844, light, the second question | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-04_desktop-dark-result.jpg` | SCR-CL-04 Khẩu vị rủi ro | current | desktop 1440×900, dark, the result | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-05_desktop-dark.jpg` | SCR-CL-05 Tác động thị trường | current | desktop 1440×900, dark, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CL-05-how_desktop-light.jpg` | SCR-CL-05 the client's “Cách tính” drawer | current | desktop 1440×900, light, viewport | 2026-10-16, BRD completion F10, dev server; run recomputed by the CIO so it carries the per-goal VND (client C01) |
| `SCR-CL-05-how_phone-light.jpg` | SCR-CL-05 the client's “Cách tính” drawer | current | phone 390×844, light, viewport | 2026-10-16, BRD completion F10, dev server; run recomputed by the CIO so it carries the per-goal VND (client C01) |
| `SCR-CIO-09-client-ai_desktop-light.jpg` | SCR-CIO-09 Cấu hình (Admin): “AI với dữ liệu khách hàng” (client_ai), its proposal box open | current | desktop 1440×900, light, viewport | 2026-10-16, BRD remaining plan G2, dev server |
| `SCR-CIO-09-client-ai_phone-light.jpg` | SCR-CIO-09 Cấu hình (Admin): “AI với dữ liệu khách hàng” (client_ai), its proposal box open | current | phone 390×844, light, viewport | 2026-10-16, BRD remaining plan G2, dev server |
| `FEAT-09-how-holdings_desktop-light.jpg` | FEAT-09 “Cách tính” on every figure — Tài sản (client): a group's share | current | desktop 1440×900, light, viewport | 2026-10-16, BRD remaining plan G1, dev server |
| `FEAT-09-how-holdings_phone-light.jpg` | FEAT-09 “Cách tính” on every figure — Tài sản (client): a group's share | current | phone 390×844, light, viewport | 2026-10-16, BRD remaining plan G1, dev server |
| `FEAT-09-how-plan_desktop-light.jpg` | FEAT-09 “Cách tính” on every figure — Kế hoạch (client): a goal's need | current | desktop 1440×900, light, viewport | 2026-10-16, BRD remaining plan G1, dev server |
| `FEAT-09-how-plan_phone-light.jpg` | FEAT-09 “Cách tính” on every figure — Kế hoạch (client): a goal's need | current | phone 390×844, light, viewport | 2026-10-16, BRD remaining plan G1, dev server |
| `FEAT-09-how-exposure_desktop-light.jpg` | FEAT-09 “Cách tính” on every figure — Phơi nhiễm (CIO): a heat-map cell, with the code | current | desktop 1440×900, light, viewport | 2026-10-16, BRD remaining plan G1, dev server |
| `FEAT-09-how-exposure_phone-light.jpg` | FEAT-09 “Cách tính” on every figure — Phơi nhiễm (CIO): a heat-map cell, with the code | current | phone 390×844, light, viewport | 2026-10-16, BRD remaining plan G1, dev server |
| `SCR-CL-05-goals_desktop-light.jpg` | SCR-CL-05 the goals panel with the VND column | current | desktop 1440×900, light, element | 2026-10-16, BRD completion F10, dev server; run recomputed by the CIO so it carries the per-goal VND (client C01) |
| `SCR-CL-05-goals_phone-light.jpg` | SCR-CL-05 the goals panel with the VND column | current | phone 390×844, light, element | 2026-10-16, BRD completion F10, dev server; run recomputed by the CIO so it carries the per-goal VND (client C01) |
| `SCR-CL-05_desktop-light.jpg` | SCR-CL-05 Tác động thị trường | current | desktop 1440×900, light, full page, with the timeline | 2026-10-16, UI redesign R4, dev server, one approved event (client C01) |
| `SCR-CL-05_phone-light.jpg` | SCR-CL-05 Tác động thị trường | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CL-06_desktop-light.jpg` | SCR-CL-06 Chi phí chính sách | current | desktop 1440×900, light, full page | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-06_phone-light.jpg` | SCR-CL-06 Chi phí chính sách | current | phone 390×844, light, full page | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-07_desktop-light.jpg` | SCR-CL-07 Chuyên gia | current | desktop 1440×900, light, viewport | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-08_desktop-light.jpg` | SCR-CL-08 Toàn cảnh (with the feed) | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, dev server, client C01, personal, T9/26, three effective runs |
| `SCR-CL-08_phone-light.jpg` | SCR-CL-08 Toàn cảnh (with the feed) | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-16, dev server, client C01, personal, T9/26, three effective runs |
| `SCR-CL-08_flow-picked.jpg` | SCR-CL-08 Toàn cảnh | current | desktop 1440×900, light, the Dòng tiền panel | 2026-10-16, dev server, client C01: “Trả nợ vay” picked, others dimmed, flow dots on their way, its transaction below |
| `SCR-CL-08_desktop-dark.jpg` | SCR-CL-08 Toàn cảnh (with the feed) | current | desktop 1440×900, dark, full page (≤ 2,600 px) | 2026-10-16, dev server, client C01, personal, T9/26, three effective runs |
| `SCR-CL-09_desktop-light.jpg` | SCR-CL-09 Đồ thị tác động | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, dev server, three effective runs, client C01 |
| `SCR-CL-09_phone-light.jpg` | SCR-CL-09 Đồ thị tác động | current | phone 390×844, light (list view), full page (≤ 2,600 px) | 2026-10-16, dev server, three effective runs, client C01 |
| `SCR-CL-09_desktop-dark.jpg` | SCR-CL-09 Đồ thị tác động | current | desktop 1440×900, dark, full page (≤ 2,600 px) | 2026-10-16, dev server, three effective runs, client C01 |
| `SCR-CL-09_desktop-light-rm.jpg` | SCR-CL-09 Đồ thị tác động | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, dev server, three effective runs, RM, C01, a scenario node selected |
| `SCR-CL-09_desktop-light-impact.jpg` | SCR-CL-09 Đồ thị tác động | current | desktop 1440×900, light, an event selected: the News Impact panel | 2026-10-16, UI redesign R4, dev server, one approved event (client C01) |
| `SCR-CL-10_desktop-light.jpg` | SCR-CL-10 Copilot panel | current | desktop 1440×900, light, viewport | 2026-10-16, dev server, keyword router, client C01: a month's flow (name and number scrubbed, “Mô hình thấy gì” open) and the feed |
| `SCR-CL-10_desktop-light-rm.jpg` | SCR-CL-10 Copilot panel | current | desktop 1440×900, light, viewport | 2026-10-16, dev server, keyword router, RM: a write waiting for Xác nhận |
| `SCR-CL-10_phone-light.jpg` | SCR-CL-10 Copilot panel | current | phone 390×844, light, viewport | 2026-10-16, dev server, keyword router, client: net worth answer |
| `HEADER_desktop-light-search.jpg` | Header (every page) | current | desktop 1440×900, light, viewport | 2026-10-16, dev server, client C01: “vàng” → a holding and an event type (FEAT-34) |
| `HEADER_desktop-light-bell.jpg` | Header (every page) | current | desktop 1440×900, light, viewport | 2026-10-16, dev server, client C01: the bell's four feed items |
| `HEADER_phone-light-search.jpg` | Header (every page) | current | phone 390×844, light, viewport | 2026-10-16, dev server: search on its own row |
| `HEADER_desktop-dark.jpg` | Header (every page) | current | desktop 1440×900, dark, viewport | 2026-10-16, dev server: Toàn cảnh under the R1 tokens |
| `SCR-CL-10_desktop-light-marks.jpg` | SCR-CL-10 Copilot panel | current | desktop 1440×900, light, viewport | 2026-10-16, dev server, client C01: net-worth answer, three KPI tiles marked, ✓ on the button (FEAT-33) |
| `SCR-CL-10_desktop-light-flow.jpg` | SCR-CL-10 Copilot panel | current | desktop 1440×900, light, full page | 2026-10-16, dev server, client C01: month's flow answer, Dòng tiền panel and the largest spending row marked |
| `SCR-CL-10_desktop-light-error.jpg` | SCR-CL-10 Copilot panel | current | desktop 1440×900, light, viewport | 2026-10-16, dev server, client asks an RM task: refusal, red dot and edge |
| `SCR-CL-10_phone-light-busy.jpg` | SCR-CL-10 Copilot panel | current | phone 390×844, light, viewport | 2026-10-16, dev server, answer delayed 4 s in the page: thinking dots |
| `SCR-CL-10_phone-light-marks.jpg` | SCR-CL-10 Copilot panel | current | phone 390×844, light, viewport | 2026-10-16, dev server: the KPI marks shown after the panel closed |
| `SCR-CL-10_desktop-light-chain.jpg` | SCR-CL-10 Copilot | current | desktop 1440×900, light, “Vì sao…”: the chain card | 2026-10-16, UI redesign R5, dev server, one approved event (client C01) |
| `SCR-CL-10_desktop-light-scenario.jpg` | SCR-CL-10 Copilot | current | desktop 1440×900, light, a stress scenario: figures card | 2026-10-16, UI redesign R5, dev server, one approved event (client C01) |
| `SCR-CL-10-session_desktop-dark.jpg` | SCR-CL-10 Copilot, sessions | current | desktop 1440×900, dark, viewport | 2026-10-17, experiment server :8040, client C01: the session bar (title and goal written by the model, rename pencil) and “Trò chuyện mới” (OWN-SS-07) |
| `SCR-CL-10-history_desktop-dark.jpg` | SCR-CL-10 Copilot, sessions | current | desktop 1440×900, dark, viewport | 2026-10-17, same: the history — search, Gần đây / Lưu trữ, grouped by day, rename / archive / delete on each row |
| `SCR-CL-10-history_phone-dark.jpg` | SCR-CL-10 Copilot, sessions | current | phone 390×844, dark, viewport | 2026-10-17, same, on a phone: the docked panel's history |
| `SCR-CL-10_phone-light-card.jpg` | SCR-CL-10 Copilot | current | phone 390×844, light, the goals card | 2026-10-16, UI redesign R5, dev server, one approved event (client C01) |
| `SCR-CL-11_desktop-light.jpg` | SCR-CL-11 Bản đồ tài chính | current | desktop 1440×900, light, full page | 2026-10-16, UI redesign R4, dev server, one approved event (client C01) |
| `SCR-CL-11_desktop-dark.jpg` | SCR-CL-11 Bản đồ tài chính | current | desktop 1440×900, dark, full page | 2026-10-16, UI redesign R4, dev server, one approved event (client C01) |
| `SCR-CL-11_phone-light.jpg` | SCR-CL-11 Bản đồ tài chính | current | phone 390×844, light, the list view | 2026-10-16, UI redesign R4, dev server, one approved event (client C01) |
| `SCR-CL-11_desktop-light-expanded.jpg` | SCR-CL-11 Bản đồ tài chính | current | desktop 1440×900, light, Cổ phiếu opened onto its holdings | 2026-10-16, UI redesign R4, dev server, one approved event (client C01) |
| `SCR-CL-11_desktop-light-all-rm.jpg` | SCR-CL-11 Bản đồ tài chính (RM) | current | desktop 1440×900, light, every kind on | 2026-10-16, UI redesign R4, dev server, one approved event (client C01) |
| `SCR-CL-09_desktop-light-path.jpg` | SCR-CL-09 Đồ thị tác động | current | desktop 1440×900, light, full page | 2026-10-16, dev server, client C01: “Tin nào ảnh hưởng tới tôi?” lights the largest event's path |
| `SCR-CMP-01_desktop-light.jpg` | SCR-CMP-01 Tin bị giữ | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CMP-02_desktop-light.jpg` | SCR-CMP-02 Nghiên cứu (release) | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CMP-02_phone-light.jpg` | SCR-CMP-02 Nghiên cứu (release) | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CMP-03_desktop-light.jpg` | SCR-CMP-03 Nhật ký | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-SH-01_desktop-light.jpg` | SCR-SH-01 Đăng nhập | current | desktop 1440×900, light, viewport | 2026-10-16, dev server, demo accounts on |
| `SCR-SH-01_phone-light.jpg` | SCR-SH-01 Đăng nhập | current | phone 390×844, light, viewport | 2026-10-16, dev server, demo accounts on |
| `SCR-RM-01_desktop-light.jpg` | SCR-RM-01 Hôm nay | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-RM-01_phone-light.jpg` | SCR-RM-01 Hôm nay | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-RM-02_desktop-light.jpg` | SCR-RM-02 Tác động tin (with the Mục tiêu panel, FR-404) | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, runs recomputed with goal impact (client C01) |
| `SCR-RM-03_desktop-light.jpg` | SCR-RM-03 Cách tính (drawer) | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-RM-04_desktop-light.jpg` | SCR-RM-04 Hiệu quả tư vấn (one client) | current | desktop 1440×900, light, full page | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-RM-04_phone-light.jpg` | SCR-RM-04 Hiệu quả tư vấn (one client) | current | phone 390×844, light, full page | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-RM-05_desktop-light.jpg` | SCR-RM-05 Hiệu quả tư vấn (all) | current | desktop 1440×900, light, full page | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-RM-02_phone-light.jpg` | SCR-RM-02 Tác động tin (staff), Mục tiêu panel (FR-404) | current | phone 390×844, light, viewport | 2026-10-15, dev server, runs recomputed with goal impact (client C01) |
| `SCR-RM-06_desktop-light.jpg` | SCR-RM-06 Duyệt đề xuất | current | desktop 1440×900, light, viewport | 2026-10-16, UI redesign R3, dev server after “Làm lại demo” (client C01) |
| `SCR-CL-12_desktop-dark.jpg` | SCR-CL-12 Không gian làm việc, Tổng quan lens | current (experiment `exp/graph-workspace`) | desktop 1440×900, dark, viewport | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-sheet_desktop-dark.jpg` | SCR-CL-12, an old address opened as a sheet over the graph | current (experiment `exp/graph-workspace`) | desktop 1440×900, dark, viewport | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12_phone-dark.jpg` | SCR-CL-12 Không gian làm việc, Tổng quan lens | current (experiment `exp/graph-workspace`) | phone 390×844, dark, viewport | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-dock_phone-dark.jpg` | SCR-CL-12, the dock (Trợ lý) below the graph | current (experiment `exp/graph-workspace`) | phone 390×844, dark, viewport | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-sheet_phone-dark.jpg` | SCR-CL-12, an old address as a sheet in the graph's place | current (experiment `exp/graph-workspace`) | phone 390×844, dark, viewport | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-dataflow_desktop-dark.jpg` | SCR-CL-12, a stream in flight: lit paths, pulses home, news through its classes (OWN-GW-16…18) | current (experiment `exp/graph-workspace`) | desktop graph area 992×580, dark | 2026-10-17, experiment server :8040, scripted stream, seeded demo data (client C01) |
| `SCR-CL-12-failed_desktop-dark.jpg` | SCR-CL-12, Mục tiêu lens: a failed read in red, a scenario's hollow pulse | current (experiment `exp/graph-workspace`) | desktop graph area 992×580, dark | 2026-10-17, experiment server :8040, scripted stream, seeded demo data (client C01) |
| `SCR-CL-12-core_desktop-dark.jpg` | SCR-CL-12, the central wealth core: aura, rings, bezel, glass body, the figures on their face, ports where money meets the rim (OWN-GW-20…25) | current (experiment `exp/graph-workspace`) | desktop, crop around the core at 2×, dark | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-core_desktop-light.jpg` | SCR-CL-12, the central wealth core in the light theme | current (experiment `exp/graph-workspace`) | desktop, crop around the core at 2×, light | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-dense_desktop-dark.jpg` | SCR-CL-12, a graph three times the demo client's: the smallest items folded into “+n” group nodes, nothing squeezed (OWN-GW-30, 32) | current (experiment `exp/graph-workspace`) | desktop 1440×900, dark, viewport | 2026-10-17, experiment server :8040, demo data with every item copied 3× in the browser (client C01) |
| `SCR-CL-12-group_desktop-dark.jpg` | SCR-CL-12, a group opened by hand (the goals on Tổng quan) with its “Thu gọn” node; money in and out leave their sides because the lower half cannot hold it | current (experiment `exp/graph-workspace`) | desktop 1440×900, dark, viewport | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-flows_desktop-dark.jpg` | SCR-CL-12, Dòng tiền: spending picked, its three categories of the month open (UNIFIED_FLOWS F11, OWN-GW-34) | current (experiment `exp/graph-workspace`) | desktop 1440×900, dark, viewport | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-flows_phone-dark.jpg` | SCR-CL-12, Dòng tiền on a phone, spending's categories open | current (experiment `exp/graph-workspace`) | phone 390×844, dark, full page | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-scenarios_desktop-dark.jpg` | SCR-CL-12, Mục tiêu & kịch bản with two stress tests active: the bar's combined figure, each scenario on its own spoke (OWN-GW-37…40) | current (experiment `exp/graph-workspace`) | desktop 1440×900, dark, viewport | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-scenarios_phone-dark.jpg` | SCR-CL-12, two stress tests active on a phone | current (experiment `exp/graph-workspace`) | phone 390×844, dark, full page | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-edge_desktop-dark.jpg` | SCR-CL-12, Tin & sự kiện: a news edge picked; Thông tin shows Nguồn, Cách tính, Giả định, Độ tin cậy, Ảnh hưởng tiếp theo (OWN-GW-46) | current (experiment `exp/graph-workspace`) | desktop 1440×900, dark, viewport | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-edge_phone-dark.jpg` | SCR-CL-12, a picked news edge on a phone | current (experiment `exp/graph-workspace`) | phone 390×844, dark, full page | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-compare_desktop-dark.jpg` | SCR-CL-12, the assistant comparing the active scenarios: their hypothetical edges lit, hollow pulses home (scripted stream; OWN-GW-42, 47) | current (experiment `exp/graph-workspace`) | desktop 1440×900, dark, viewport | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CL-12-compare_phone-dark.jpg` | SCR-CL-12, the comparison on a phone | current (experiment `exp/graph-workspace`) | phone 390×844, dark, full page | 2026-10-17, experiment server :8040, seeded demo data (client C01) |
| `SCR-CIO-15_desktop-light.jpg` | SCR-CIO-15 Bàn quyết định: the flow, the decision queue, exposure, events | current (experiment `exp/graph-workspace`) | desktop 1440×900, light, viewport | 2026-10-18, multi-role M1, copy server :8042 on a copy of the experiment's state (`ux/multi-role`) |
| `SCR-CIO-15_desktop-dark.jpg` | SCR-CIO-15 Bàn quyết định, dark | current (experiment `exp/graph-workspace`) | desktop 1440×900, dark, viewport | 2026-10-18, multi-role M1, copy server :8042 on a copy of the experiment's state (`ux/multi-role`) |
| `SCR-CIO-15_phone-light.jpg` | SCR-CIO-15 Bàn quyết định on a phone: the rail on top, the stages two by two | current (experiment `exp/graph-workspace`) | phone 390×844, light, viewport | 2026-10-18, multi-role M1, copy server :8042 on a copy of the experiment's state (`ux/multi-role`) |
| `SCR-CIO-15-sheet_desktop-light.jpg` | SCR-CIO-15, a page as a sheet (Dữ liệu thị trường) with its group's tabs | current (experiment `exp/graph-workspace`) | desktop 1440×900, light, viewport | 2026-10-18, multi-role M1, copy server :8042 on a copy of the experiment's state (`ux/multi-role`) |
| `SCR-RM-07_desktop-light.jpg` | SCR-RM-07 Sổ khách hàng (rm03): a family at the threshold picked, its card in Thông tin | current (experiment `exp/graph-workspace`) | desktop 1440×900, light, viewport | 2026-10-18, multi-role M2, copy server :8042 on a copy of the experiment's state (`ux/multi-role`) |
| `SCR-RM-07-calm_desktop-dark.jpg` | SCR-RM-07 Sổ khách hàng (rm01): three families, nothing waiting | current (experiment `exp/graph-workspace`) | desktop 1440×900, dark, viewport | 2026-10-18, multi-role M2, copy server :8042 on a copy of the experiment's state (`ux/multi-role`) |
| `SCR-RM-07_phone-dark.jpg` | SCR-RM-07 Sổ khách hàng on a phone (rm01) | current (experiment `exp/graph-workspace`) | phone 390×844, dark, viewport | 2026-10-18, multi-role M2, copy server :8042 on a copy of the experiment's state (`ux/multi-role`) |
| `SCR-ADM-02_desktop-light.jpg` | SCR-ADM-02 Vận hành: the operations map, alerts, failing jobs, configuration, people | current (experiment `exp/graph-workspace`) | desktop 1440×900, light, viewport | 2026-10-18, multi-role M3, copy server :8042 on a copy of the experiment's state (`ux/multi-role`) |
| `SCR-ADM-02-pick_desktop-dark.jpg` | SCR-ADM-02, the Agent node picked: each agent's runs in Thông tin | current (experiment `exp/graph-workspace`) | desktop 1440×900, dark, viewport | 2026-10-18, multi-role M3, copy server :8042 on a copy of the experiment's state (`ux/multi-role`) |
| `SCR-SP-02_desktop-light.jpg` | SCR-SP-02 Bàn chuyên gia: the queue beside the evidence, the decision bar | current (experiment `exp/graph-workspace`) | desktop 1440×900, light, viewport | 2026-10-18, multi-role M4, copy server :8042 on a copy of the experiment's state with two RM recommendations seeded (`ux/multi-role`) |
| `SCR-SP-02-family_desktop-dark.jpg` | SCR-SP-02, a family picked: its picture without a decision | current (experiment `exp/graph-workspace`) | desktop 1440×900, dark, viewport | 2026-10-18, multi-role M4, copy server :8042 on a copy of the experiment's state with two RM recommendations seeded (`ux/multi-role`) |
| `SCR-SP-02_phone-dark.jpg` | SCR-SP-02 on a phone: queue, families and evidence stacked | current (experiment `exp/graph-workspace`) | phone 390×844, dark, viewport | 2026-10-18, multi-role M4, copy server :8042 on a copy of the experiment's state with two RM recommendations seeded (`ux/multi-role`) |
| `SCR-ADM-02_phone-dark.jpg` | SCR-ADM-02 on a phone: two lanes per row | current (experiment `exp/graph-workspace`) | phone 390×844, dark, viewport | 2026-10-18, multi-role M3, copy server :8042 on a copy of the experiment's state (`ux/multi-role`) |

## proposed_ui/ — the redesign kit (SRC-03)

| File | What | State | Notes |
|---|---|---|---|
| `KIT-01_concept-board_illustrative.png` | The kit's concept board: Pulse, Money Flow, graph, news impact, Copilot, coverage and plan panels | proposed — **illustrative only** | Its figures are invented (e.g. “90 yêu cầu / 84 đã triển khai”, “Thu nhập 180,2 tr”); not a specification. SHA-256 `e2aff7ef…2a77` |
| `GW-01_concept_persistent-graph_illustrative.png` | The owner's concept for the persistent financial graph (2026-10-17): left toolbar, radial graph around “Tổng tài sản”, Assistant + Thông tin dock, bottom strip, the assistant interaction flow | proposed — **illustrative only** | Its figures are invented (e.g. “43,5 tỷ”, “Cổ phiếu 9,4 tỷ”); layout and interaction inspiration, not a specification (OWN-GW, FEAT-40). SHA-256 `1f206ade…a4a8` |
| `KIT-02_current-overview_reference.png` | The kit's screenshot of the overview before the redesign kit | original (of the kit) | Shows the same page as SCR-CL-01. SHA-256 `f8a907df…4029` |

## approved_ui/

Empty: no design has been approved yet. Add images here only with the decision (ADR) that approved them.
