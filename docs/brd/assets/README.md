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

## proposed_ui/ — the redesign kit (SRC-03)

| File | What | State | Notes |
|---|---|---|---|
| `KIT-01_concept-board_illustrative.png` | The kit's concept board: Pulse, Money Flow, graph, news impact, Copilot, coverage and plan panels | proposed — **illustrative only** | Its figures are invented (e.g. “90 yêu cầu / 84 đã triển khai”, “Thu nhập 180,2 tr”); not a specification. SHA-256 `e2aff7ef…2a77` |
| `KIT-02_current-overview_reference.png` | The kit's screenshot of the overview before the redesign kit | original (of the kit) | Shows the same page as SCR-CL-01. SHA-256 `f8a907df…4029` |

## approved_ui/

Empty: no design has been approved yet. Add images here only with the decision (ADR) that approved them.
