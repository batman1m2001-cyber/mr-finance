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
| `SCR-CIO-07_desktop-light.jpg` | SCR-CIO-07 Mô hình | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CL-01_desktop-light.jpg` | SCR-CL-01 Tổng quan | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CL-01_phone-light.jpg` | SCR-CL-01 Tổng quan | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CL-02_desktop-light.jpg` | SCR-CL-02 Tài sản | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CL-03_desktop-light.jpg` | SCR-CL-03 Kế hoạch | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CL-04_desktop-light.jpg` | SCR-CL-04 Khẩu vị rủi ro | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CL-05_desktop-dark.jpg` | SCR-CL-05 Tác động thị trường | current | desktop 1440×900, dark, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CL-05_desktop-light.jpg` | SCR-CL-05 Tác động thị trường | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CL-05_phone-light.jpg` | SCR-CL-05 Tác động thị trường | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CL-06_desktop-light.jpg` | SCR-CL-06 Chi phí chính sách | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CL-07_desktop-light.jpg` | SCR-CL-07 Chuyên gia | current | desktop 1440×900, light, viewport | 2026-10-15, dev server, seeded demo data (client C01), after DEF-02: queue read-only with one pending item |
| `SCR-CL-08_desktop-light.jpg` | SCR-CL-08 Toàn cảnh | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, dev server, client C01, personal, T9/26 |
| `SCR-CL-08_phone-light.jpg` | SCR-CL-08 Toàn cảnh | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-16, dev server, client C01, personal, T9/26 |
| `SCR-CL-08_desktop-dark.jpg` | SCR-CL-08 Toàn cảnh | current | desktop 1440×900, dark, full page (≤ 2,600 px) | 2026-10-16, dev server, client C01, personal, T9/26 |
| `SCR-CL-09_desktop-light.jpg` | SCR-CL-09 Đồ thị tác động | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, dev server, three effective runs, client C01 |
| `SCR-CL-09_phone-light.jpg` | SCR-CL-09 Đồ thị tác động | current | phone 390×844, light (list view), full page (≤ 2,600 px) | 2026-10-16, dev server, three effective runs, client C01 |
| `SCR-CL-09_desktop-dark.jpg` | SCR-CL-09 Đồ thị tác động | current | desktop 1440×900, dark, full page (≤ 2,600 px) | 2026-10-16, dev server, three effective runs, client C01 |
| `SCR-CL-09_desktop-light-rm.jpg` | SCR-CL-09 Đồ thị tác động | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-16, dev server, three effective runs, RM, C01, a scenario node selected |
| `SCR-CMP-01_desktop-light.jpg` | SCR-CMP-01 Tin bị giữ | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CMP-02_desktop-light.jpg` | SCR-CMP-02 Nghiên cứu (release) | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CMP-02_phone-light.jpg` | SCR-CMP-02 Nghiên cứu (release) | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-CMP-03_desktop-light.jpg` | SCR-CMP-03 Nhật ký | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-RM-01_desktop-light.jpg` | SCR-RM-01 Hôm nay | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-RM-01_phone-light.jpg` | SCR-RM-01 Hôm nay | current | phone 390×844, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-RM-02_desktop-light.jpg` | SCR-RM-02 Tác động tin (with the Mục tiêu panel, FR-404) | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, runs recomputed with goal impact (client C01) |
| `SCR-RM-03_desktop-light.jpg` | SCR-RM-03 Cách tính (drawer) | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-RM-04_desktop-light.jpg` | SCR-RM-04 Hiệu quả tư vấn (one client) | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-RM-05_desktop-light.jpg` | SCR-RM-05 Hiệu quả tư vấn (all) | current | desktop 1440×900, light, full page (≤ 2,600 px) | 2026-10-15, dev server, seeded demo data (client C01) |
| `SCR-RM-02_phone-light.jpg` | SCR-RM-02 Tác động tin (staff), Mục tiêu panel (FR-404) | current | phone 390×844, light, viewport | 2026-10-15, dev server, runs recomputed with goal impact (client C01) |
| `SCR-RM-06_desktop-light.jpg` | SCR-RM-06 Duyệt đề xuất | current | desktop 1440×900, light, viewport | 2026-10-15, dev server, one pending proposal (client C01) |

## proposed_ui/ — the redesign kit (SRC-03)

| File | What | State | Notes |
|---|---|---|---|
| `KIT-01_concept-board_illustrative.png` | The kit's concept board: Pulse, Money Flow, graph, news impact, Copilot, coverage and plan panels | proposed — **illustrative only** | Its figures are invented (e.g. “90 yêu cầu / 84 đã triển khai”, “Thu nhập 180,2 tr”); not a specification. SHA-256 `e2aff7ef…2a77` |
| `KIT-02_current-overview_reference.png` | The kit's screenshot of the overview before the redesign kit | original (of the kit) | Shows the same page as SCR-CL-01. SHA-256 `f8a907df…4029` |

## approved_ui/

Empty: no design has been approved yet. Add images here only with the decision (ADR) that approved them.
