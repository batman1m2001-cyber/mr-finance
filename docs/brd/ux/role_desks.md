# Role desks — where every staff capability lives (FEAT-41)

Layer C. The checklist MAINTAINING.md asks of a redesign: every page of every staff role before the desks, the
features and requirements it carries, and where it is after. Nothing is removed: every address below still opens
its page module, unchanged, as a sheet over the role's desk (ADR-0036 §2). **State:** `planned` until the role's
phase is built, then `built` with its test.

The desks themselves (the new centres) are screens SCR-CIO-15, SCR-RM-07, SCR-ADM-02, SCR-SP-02 and SCR-CMP-06 in
[screen_inventory.md](screen_inventory.md).

## CIO (`#/cio/…`) — desk "Bàn quyết định" (SCR-CIO-15)

| Page (address) | Screen | Features | Key requirements | Rail group | State |
|---|---|---|---|---|---|
| Hộp tin `hop-tin` | SCR-CIO-01 | FEAT-01, 02 | BRD-FR-101…103 | Tin & sự kiện | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Sự kiện & nhận định `nhan-dinh[/EV-…]` | SCR-CIO-02 | FEAT-02, 04 | BRD-FR-103, 301, 307 | Tin & sự kiện | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Nhận định `nhan-dinh/VW-…` | SCR-CIO-03 | FEAT-04, 05, 06 | BRD-BR-05…07, BR-14, FR-302…305 | Tin & sự kiện | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Phơi nhiễm `phoi-nhiem` | SCR-CIO-04 | FEAT-08 | BRD-BR-13, FR-403 | Tác động | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Lần áp dụng `ap-dung[/AR-…]` | SCR-CIO-05 | FEAT-08 | BRD-FR-401, 405, 501 | Tác động | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Đồ thị lần áp dụng `do-thi[/AR-…]` | SCR-CIO-10 | FEAT-30 | KIT-UX-04 | Tác động | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Nghiên cứu `nghien-cuu` | SCR-CIO-06 | FEAT-03, 10 | BRD-FR-201, 204, 603 | Nội dung | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Bản tin `ban-tin[/NL-…]` | SCR-CIO-14 | FEAT-17 | BRD-FR-801 | Nội dung | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Chính sách `chinh-sach[/PD-…]` (read only) | SCR-CMP-05 | FEAT-16 | BRD-FR-306 | Nội dung | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Mô hình → Tham số `mo-hinh/tham-so` | SCR-CIO-07 | FEAT-07, 14 | BRD-RULE-ENG-08…11 | Mô hình | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Mô hình → Dữ liệu thị trường `mo-hinh/du-lieu` | SCR-CIO-11 | FEAT-35 | BRD-RULE-ENG-11 | Mô hình | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Mô hình → Độ chính xác `mo-hinh/do-chinh-xac` | SCR-CIO-12 | FEAT-18 | BRD-BR-15, KPI-03/04 | Mô hình | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Đo lường `do-luong` | SCR-CIO-13 | FEAT-18 | BRD-RULE-MEAS-03, 05 | Mô hình | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Agent `agent` | SCR-CIO-08 | FEAT-15 | BRD-FR-703 | AI & cấu hình | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Cấu hình `cau-hinh` | SCR-CIO-09 | FEAT-14 | BRD-FR-701 | AI & cấu hình | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |
| Bộ nhớ `bo-nho` | — | FEAT-37 | OWN-AS-* | rail foot | built — `tests/ui/test_role_desks_ui.py::test_the_cio_works_at_its_desk_and_every_page_is_a_sheet` |

## RM (`#/rm/…`) — desk "Sổ khách hàng" (SCR-RM-07)

| Page (address) | Screen | Features | Key requirements | Rail group | State |
|---|---|---|---|---|---|
| Hôm nay `hom-nay` | SCR-RM-01 | FEAT-13, 10 | BRD-BR-09, FR-503, FR-603 | Hôm nay | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |
| Khách hàng → Tác động tin `khach-hang/tac-dong` | SCR-RM-02 (+ SCR-RM-03) | FEAT-13, 09, 10 | BRD-BR-12, FR-404, 406, 601 | Khách hàng | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |
| Khách hàng → Đồ thị tác động `khach-hang/do-thi` | SCR-CL-09 | FEAT-30 | KIT-UX-04 | Khách hàng | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |
| Khách hàng → Toàn cảnh `khach-hang/toan-canh` | SCR-CL-08 | FEAT-29, 31 | KIT-UX-01…05 | Khách hàng | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |
| Khách hàng → Bản đồ tài chính `khach-hang/ban-do` | SCR-CL-11 | FEAT-30 | OWN-UI-04 | Khách hàng | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |
| Khách hàng → Chi tiết `khach-hang/tong-quan` | SCR-CL-01 | FEAT-21 | BRIEF-DASH-* | Khách hàng | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |
| Khách hàng → Tài sản `khach-hang/tai-san` | SCR-CL-02 | FEAT-20, 22, 23 | BRIEF-DATA-* | Khách hàng | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |
| Khách hàng → Kế hoạch `khach-hang/ke-hoach` | SCR-CL-03 | FEAT-26, 27 | BRIEF-SCEN-* | Khách hàng | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |
| Khách hàng → Chi phí chính sách `khach-hang/chinh-sach` | SCR-CL-06 | FEAT-25 | BRIEF-IMPACT-* | Khách hàng | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |
| Khách hàng → Hiệu quả tư vấn `khach-hang/hieu-qua` | SCR-RM-04 | FEAT-28 | Q-19 | Khách hàng | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |
| Khách hàng → Duyệt đề xuất `khach-hang/duyet` | SCR-RM-06 | FEAT-27 | BRIEF-FLOW-02 | Khách hàng | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |
| Hiệu quả tư vấn (all) `hieu-qua` | SCR-RM-05 | FEAT-28 | Q-19 | Hiệu quả tư vấn | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |
| Bộ nhớ `bo-nho` | — | FEAT-37 | OWN-AS-* | rail foot | built — `tests/ui/test_role_desks_ui.py::test_the_rm_works_at_its_book_and_every_page_is_a_sheet` |

## Admin (`#/admin/…`) — desk "Vận hành" (SCR-ADM-02)

| Page (address) | Screen | Features | Key requirements | Rail group | State |
|---|---|---|---|---|---|
| Hệ thống `he-thong` | SCR-ADM-01 | FEAT-12, 19, 36 | BRD-RULE-ROLE-04, NFR-12 | Hệ thống | built — `tests/ui/test_role_desks_ui.py::test_admin_works_at_the_operations_map_and_every_page_is_a_sheet` |
| Dữ liệu thị trường `du-lieu` | SCR-CIO-11 | FEAT-35 | BRD-RULE-ENG-11 | Dữ liệu thị trường | built — `tests/ui/test_role_desks_ui.py::test_admin_works_at_the_operations_map_and_every_page_is_a_sheet` |
| Cấu hình `cau-hinh` | SCR-CIO-09 | FEAT-14 | BRD-FR-701, RULE-SEC-05 | Cấu hình | built — `tests/ui/test_role_desks_ui.py::test_admin_works_at_the_operations_map_and_every_page_is_a_sheet` |
| Agent `agent` | SCR-CIO-08 | FEAT-15 | BRD-FR-703 | Agent | built — `tests/ui/test_role_desks_ui.py::test_admin_works_at_the_operations_map_and_every_page_is_a_sheet` |
| Nhật ký `nhat-ky` | SCR-CMP-03 | FEAT-11 | BRD-BR-12, FR-702 | Nhật ký | built — `tests/ui/test_role_desks_ui.py::test_admin_works_at_the_operations_map_and_every_page_is_a_sheet` |
| Bộ nhớ `bo-nho` | — | FEAT-37 | OWN-AS-* | rail foot | built — `tests/ui/test_role_desks_ui.py::test_admin_works_at_the_operations_map_and_every_page_is_a_sheet` |

## Expert (`#/specialist/…`) — desk "Bàn chuyên gia" (SCR-SP-02)

| Page (address) | Screen | Features | Key requirements | Rail group | State |
|---|---|---|---|---|---|
| Duyệt khuyến nghị `duyet` | SCR-SP-01 | FEAT-27 | BRD-RULE-ROLE-05, WF-08 | Duyệt khuyến nghị | planned |
| Bộ nhớ `bo-nho` | — | FEAT-37 | OWN-AS-* | rail foot | planned |

## Compliance (`#/compliance/…`) — desk "Bàn kiểm soát" (SCR-CMP-06)

| Page (address) | Screen | Features | Key requirements | Rail group | State |
|---|---|---|---|---|---|
| Tin bị giữ `giu` | SCR-CMP-01 | FEAT-02 | BRD-BR-04, FR-105 | Tin bị giữ | planned |
| Nghiên cứu `nghien-cuu` | SCR-CMP-02 | FEAT-03 | BRD-BR-03, FR-202, 203 | Nội dung | planned |
| Bản tin `ban-tin[/NL-…]` | SCR-CMP-04 | FEAT-17 | BRD-FR-801 | Nội dung | planned |
| Chính sách `chinh-sach[/PD-…]` | SCR-CMP-05 | FEAT-16 | BRD-FR-306 | Nội dung | planned |
| Đo lường `do-luong` | SCR-CIO-13 | FEAT-18 | BRD-RULE-MEAS-03, 05 | Đo lường | planned |
| Nhật ký `nhat-ky` | SCR-CMP-03 | FEAT-11 | BRD-BR-12, FR-702 | Nhật ký | planned |
| Agent `agent` | SCR-CIO-08 | FEAT-15 | BRD-FR-703 | AI & cấu hình | planned |
| Cấu hình `cau-hinh` | SCR-CIO-09 | FEAT-14 | BRD-FR-701 | AI & cấu hình | planned |
| Bộ nhớ `bo-nho` | — | FEAT-37 | OWN-AS-* | rail foot | planned |

## Every role: shared pieces

| Piece | Feature | Before | After |
|---|---|---|---|
| Header search, bell, theme, sign-out | FEAT-34, 36 | header | header (unchanged) |
| The assistant | FEAT-32, 37…39 | floating panel, one reply | docked in Trợ lý, streaming, progress list, the role's new read tools |
| “Cách tính” on any figure | FEAT-09, BRD-NFR-11 | every page | every page and every desk figure |
| The client picker and scope (RM) | — | header, inside Khách hàng | header, inside Khách hàng; a family picked on the RM desk sets it |
