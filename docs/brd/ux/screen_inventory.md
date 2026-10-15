# Screen inventory

Layer C index. One row per screen or significant component; details in [`screens/`](screens/). States:
**current** = built and screenshotted 2026-10-15; **proposed** = in a plan, not built. A redesign never deletes a
row: a replaced screen is marked `replaced by SCR-…` and keeps its capabilities' new location.

| ID | Screen | Role · route | Gen. | Features | Key requirements | State | Screenshots |
|---|---|---|---|---|---|---|---|
| [SCR-CL-01](screens/client.md#scr-cl-01--tổng-quan-overview) | Tổng quan → Chi tiết | client `#/client/tong-quan/chi-tiet`; RM `…/khach-hang/tong-quan` | legacy | FEAT-21, 20, 25 | BRIEF-DASH-* | current | [d](../assets/current_ui/SCR-CL-01_desktop-light.jpg) [p](../assets/current_ui/SCR-CL-01_phone-light.jpg) |
| [SCR-CL-02](screens/client.md#scr-cl-02--tài-sản-holdings) | Tài sản | client `#/client/tai-san`; RM `…/khach-hang/tai-san` | legacy | FEAT-20, 22, 23 | BRIEF-DATA-* | current | [d](../assets/current_ui/SCR-CL-02_desktop-light.jpg) |
| [SCR-CL-03](screens/client.md#scr-cl-03--kế-hoạch-wealth-planning-advisor) | Kế hoạch | client `#/client/muc-tieu/ke-hoach`; RM `…/khach-hang/ke-hoach` | legacy | FEAT-26, 27 | BRIEF-SCEN-* | current | [d](../assets/current_ui/SCR-CL-03_desktop-light.jpg) |
| [SCR-CL-04](screens/client.md#scr-cl-04--khẩu-vị-rủi-ro-risk-test) | Khẩu vị rủi ro | client `#/client/muc-tieu/khau-vi` | legacy | FEAT-24 | BRIEF-RISK-* | current | [d](../assets/current_ui/SCR-CL-04_desktop-light.jpg) |
| [SCR-CL-05](screens/client.md#scr-cl-05--tác-động-thị-trường-family-impact-client) | Tác động thị trường | client `#/client/tin/thi-truong` | new | FEAT-13, 10 | BR-08, BR-10, FR-502, §14 flow 2 | current | [d](../assets/current_ui/SCR-CL-05_desktop-light.jpg) [dark](../assets/current_ui/SCR-CL-05_desktop-dark.jpg) [p](../assets/current_ui/SCR-CL-05_phone-light.jpg) |
| [SCR-CL-06](screens/client.md#scr-cl-06--chi-phí-chính-sách-policy-costs) | Chi phí chính sách | client `#/client/tin/chinh-sach`; RM `…/khach-hang/chinh-sach` | legacy | FEAT-25 | BRIEF-IMPACT-*, BRIEF-ALERT-* | current | [d](../assets/current_ui/SCR-CL-06_desktop-light.jpg) |
| [SCR-CL-07](screens/client.md#scr-cl-07--chuyên-gia-specialist-team) | Chuyên gia | client `#/client/chuyen-gia` | legacy | FEAT-28, 27 | BRIEF-FLOW-02 | current (queue read-only) | [d](../assets/current_ui/SCR-CL-07_desktop-light.jpg) |
| [SCR-CL-08](screens/client.md#scr-cl-08--toàn-cảnh-pulse-wealth-map-money-flow) | Tổng quan → Toàn cảnh | client `#/client/tong-quan/toan-canh`; RM `…/khach-hang/toan-canh` | new | FEAT-29, 31 | KIT-UX-01…03, 05 | current | [d](../assets/current_ui/SCR-CL-08_desktop-light.jpg) [p](../assets/current_ui/SCR-CL-08_phone-light.jpg) [dark](../assets/current_ui/SCR-CL-08_desktop-dark.jpg) |
| [SCR-CL-09](screens/client.md#scr-cl-09--đồ-thị-tác-động-intelligence-graph) | Đồ thị tác động | client `#/client/tin/do-thi`; RM `…/khach-hang/do-thi` | new | FEAT-30 | KIT-UX-04 | current | [d](../assets/current_ui/SCR-CL-09_desktop-light.jpg) [p](../assets/current_ui/SCR-CL-09_phone-light.jpg) [dark](../assets/current_ui/SCR-CL-09_desktop-dark.jpg) |
| [SCR-CL-10](screens/client.md#scr-cl-10--onewealth-copilot-panel-all-roles) | Copilot panel | every role, every page | new | FEAT-32 | KIT-COPILOT-01…05 | current | [d](../assets/current_ui/SCR-CL-10_desktop-light.jpg) [rm](../assets/current_ui/SCR-CL-10_desktop-light-rm.jpg) [p](../assets/current_ui/SCR-CL-10_phone-light.jpg) |
| [SCR-RM-01](screens/rm.md#scr-rm-01--hôm-nay-today) | Hôm nay | RM `#/rm/hom-nay` | new | FEAT-13, 10 | BR-09, FR-503, FR-603 | current | [d](../assets/current_ui/SCR-RM-01_desktop-light.jpg) [p](../assets/current_ui/SCR-RM-01_phone-light.jpg) |
| [SCR-RM-02](screens/rm.md#scr-rm-02--tác-động-tin-family-impact-staff) | Tác động tin | RM `#/rm/khach-hang/tac-dong` | new | FEAT-13, 09, 10 | BR-12, FR-404, FR-406, FR-601 | current | [d](../assets/current_ui/SCR-RM-02_desktop-light.jpg) [p](../assets/current_ui/SCR-RM-02_phone-light.jpg) |
| [SCR-RM-03](screens/rm.md#scr-rm-03--cách-tính-trace-drawer) | Cách tính (drawer) | from SCR-RM-02 | new | FEAT-09 | BR-12, FR-406 | current | [d](../assets/current_ui/SCR-RM-03_desktop-light.jpg) |
| [SCR-RM-04](screens/rm.md#scr-rm-04--hiệu-quả-tư-vấn-of-one-client) | Hiệu quả tư vấn (one client) | RM `#/rm/khach-hang/hieu-qua` | legacy | FEAT-28 | — (Q-19) | current | [d](../assets/current_ui/SCR-RM-04_desktop-light.jpg) |
| [SCR-RM-05](screens/rm.md#scr-rm-05--hiệu-quả-tư-vấn-all-clients) | Hiệu quả tư vấn (all) | RM `#/rm/hieu-qua` | legacy | FEAT-28 | — (Q-19) | current | [d](../assets/current_ui/SCR-RM-05_desktop-light.jpg) |
| [SCR-RM-06](screens/rm.md#scr-rm-06--duyệt-đề-xuất-approval-queue) | Duyệt đề xuất | RM `#/rm/khach-hang/duyet` | legacy | FEAT-27 | BRIEF-FLOW-02 | current | [d](../assets/current_ui/SCR-RM-06_desktop-light.jpg) |
| [SCR-CIO-01](screens/cio.md#scr-cio-01--hộp-tin-inbox) | Hộp tin | CIO `#/cio/hop-tin` | new | FEAT-01, 02 | FR-101…103 | current | [d](../assets/current_ui/SCR-CIO-01_desktop-light.jpg) [p](../assets/current_ui/SCR-CIO-01_phone-light.jpg) |
| [SCR-CIO-02](screens/cio.md#scr-cio-02--sự-kiện--nhận-định-events) | Sự kiện & nhận định | CIO `#/cio/nhan-dinh[/EV-…]` | new | FEAT-02, 04 | FR-103, FR-301, FR-307 | current | [d](../assets/current_ui/SCR-CIO-02_desktop-light.jpg) |
| [SCR-CIO-03](screens/cio.md#scr-cio-03--nhận-định-view-detail) | Nhận định | CIO `#/cio/nhan-dinh/VW-…` | new | FEAT-04, 05, 06 | BR-05…07, BR-14, FR-302…305 | current | [d](../assets/current_ui/SCR-CIO-03_desktop-light.jpg) [dark](../assets/current_ui/SCR-CIO-03_desktop-dark.jpg) [p](../assets/current_ui/SCR-CIO-03_phone-light.jpg) |
| [SCR-CIO-04](screens/cio.md#scr-cio-04--phơi-nhiễm-exposure) | Phơi nhiễm | CIO `#/cio/phoi-nhiem` | new | FEAT-08 | BR-13, FR-403 | current | [d](../assets/current_ui/SCR-CIO-04_desktop-light.jpg) |
| [SCR-CIO-05](screens/cio.md#scr-cio-05--lần-áp-dụng-application-runs) | Lần áp dụng | CIO `#/cio/ap-dung[/AR-…]` | new | FEAT-08 | FR-401, FR-405, FR-501 | current | [d](../assets/current_ui/SCR-CIO-05_desktop-light.jpg) |
| [SCR-CIO-06](screens/cio.md#scr-cio-06--nghiên-cứu-research-cio) | Nghiên cứu (upload) | CIO `#/cio/nghien-cuu` | new | FEAT-03, 10 | FR-201, FR-204, FR-603 | current | [d](../assets/current_ui/SCR-CIO-06_desktop-light.jpg) |
| [SCR-CIO-07](screens/cio.md#scr-cio-07--mô-hình-factor-model) | Mô hình | CIO `#/cio/mo-hinh` | new | FEAT-07, 14 | §9, FR-701 (read) | current | [d](../assets/current_ui/SCR-CIO-07_desktop-light.jpg) |
| [SCR-CIO-08](screens/cio.md#scr-cio-08--agent-catalogue-and-ai-quality) | Agent | CIO `#/cio/agent`; Compliance `#/compliance/agent` | new | FEAT-15 | FR-703, RULE-MEAS-04 | current | [d](../assets/current_ui/SCR-CIO-08_desktop-light.jpg) [p](../assets/current_ui/SCR-CIO-08_phone-light.jpg) |
| [SCR-CIO-09](screens/cio.md#scr-cio-09--cấu-hình-versioned-configuration) | Cấu hình | CIO `#/cio/cau-hinh`; Compliance `#/compliance/cau-hinh` | new | FEAT-14 | FR-701, RULE-SEC-04/05 | current | [d](../assets/current_ui/SCR-CIO-09_desktop-light.jpg) [p](../assets/current_ui/SCR-CIO-09_phone-light.jpg) |
| [SCR-CMP-01](screens/compliance.md#scr-cmp-01--tin-bị-giữ-held-news) | Tin bị giữ | Compliance `#/compliance/giu` | new | FEAT-02 | BR-04, FR-105 | current | [d](../assets/current_ui/SCR-CMP-01_desktop-light.jpg) |
| [SCR-CMP-02](screens/compliance.md#scr-cmp-02--nghiên-cứu-research-release) | Nghiên cứu (release) | Compliance `#/compliance/nghien-cuu` | new | FEAT-03 | BR-03, FR-202, FR-203 | current | [d](../assets/current_ui/SCR-CMP-02_desktop-light.jpg) [p](../assets/current_ui/SCR-CMP-02_phone-light.jpg) |
| [SCR-CMP-03](screens/compliance.md#scr-cmp-03--nhật-ký-audit-log) | Nhật ký | Compliance `#/compliance/nhat-ky` | new | FEAT-11 | BR-12, FR-702 | current | [d](../assets/current_ui/SCR-CMP-03_desktop-light.jpg) |
| SCR-PRO-01 | Financial Pulse / Wealth Map / Money Flow | client, RM | — | FEAT-29 | KIT-UX-01…03 | replaced by SCR-CL-08 (built 2026-10-16) | concept [KIT-01](../assets/proposed_ui/KIT-01_concept-board_illustrative.png) |
| SCR-PRO-02 | Financial Intelligence Graph | client, RM, CIO | — | FEAT-30 | KIT-UX-04 | replaced by SCR-CL-09 (built 2026-10-16; CIO run view not built) | concept KIT-01 |
| SCR-PRO-03 | Intelligence Feed | client, RM | — | FEAT-31 | KIT-UX-05 | replaced by a panel of SCR-CL-08 (built 2026-10-16) | concept KIT-01 |
| SCR-PRO-04 | Copilot panel | all | — | FEAT-32 | KIT-COPILOT-* | replaced by SCR-CL-10 (built 2026-10-16) | concept KIT-01 |

Screens of **BRD capabilities not built** (no row yet): policy agent (FEAT-16), CIO
newsletter (FEAT-17), accuracy (FEAT-18).

**Verification of the current screens (2026-10-15):** 21 routes captured at 1440 × 900 and 390 × 844; no page
error or console error, no horizontal scroll at either width (capture log in
[`../testing/regression_coverage.md`](../testing/regression_coverage.md#ui-checks)).
