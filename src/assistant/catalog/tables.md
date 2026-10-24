<!-- The data room's tables, as the assistant reads them (docs/ASSISTANT_DATA_PLAN.md §3.3). One "## name" per table of
src/assistant/dataroom.py TABLES, one "- `column`: …" line per column; tests/test_datacatalog.py fails on a column
missing here or named here and not in the room. Times: "luc_*" are epoch seconds, "ngay*" are YYYY-MM-DD and "gio*"
HH:MM, both in Vietnam time (UTC+7). Money is VND. -->

## tin
Tin đã qua bộ lọc, chưa bị Tuân thủ giữ (tin bị từ chối và tin bị giữ không có ở đây). Một dòng là một tin.
- `ma`: mã tin
- `tieu_de`: tiêu đề
- `tom_tat`: tóm tắt (có thể rỗng)
- `nguon`: mã nguồn: vnexpress_kd, vnexpress_tg, cafef_ck, vneconomy_tg, vneconomy_tc, vneconomy_ck, vneconomy_do, vietstock_cp, vietstock_vm, ecb, fed
- `bao`: tên báo: VnExpress, VnEconomy, CafeF, Vietstock, European Central Bank, Federal Reserve
- `chuyen_muc`: chuyên mục của báo
- `loai`: domestic (trong nước) hoặc intl (quốc tế)
- `trang_thai`: new (chờ xử lý, chưa gom), grouped (đã gom vào sự kiện), dismissed (CIO đã bỏ)
- `muc_lien_quan`: high (cao), medium (vừa), low (thấp)
- `loai_su_kien`: monetary (chính sách tiền tệ), fx (tỷ giá), gold (vàng), credit (tín dụng, trái phiếu), real_estate (bất động sản), regulation (chính sách, quy định), commodity (hàng hóa), crypto (tiền số), equity (thị trường cổ phiếu), geopolitics (địa chính trị, thương mại); NULL khi chưa xếp loại
- `diem`: điểm liên quan từ 0 đến 1 (high ≥ 0,75; medium 0,25–0,5; low 0)
- `luc_dang`: lúc báo đăng (epoch giây)
- `ngay_dang`: ngày báo đăng (giờ Việt Nam)
- `luc_lay`: lúc hệ thống lấy tin về (epoch giây)
- `ngay_lay`: ngày hệ thống lấy tin về (giờ Việt Nam)
- `gio_lay`: giờ lấy tin về, HH:MM (giờ Việt Nam)
- `url`: đường dẫn bài báo

## tin_bi_giu
Tin đang bị Tuân thủ giữ vì nhắc đến công ty trong danh sách hạn chế. Cùng cột như tin thường, thêm `cong_ty_han_che`.
- `ma`: mã tin
- `tieu_de`: tiêu đề
- `tom_tat`: tóm tắt (có thể rỗng)
- `nguon`: mã nguồn: vnexpress_kd, vnexpress_tg, cafef_ck, vneconomy_tg, vneconomy_tc, vneconomy_ck, vneconomy_do, vietstock_cp, vietstock_vm, ecb, fed
- `bao`: tên báo
- `chuyen_muc`: chuyên mục của báo
- `loai`: domestic (trong nước) hoặc intl (quốc tế)
- `trang_thai`: new (chờ xử lý), grouped (đã gom vào sự kiện), dismissed (CIO đã bỏ)
- `muc_lien_quan`: high (cao), medium (vừa), low (thấp)
- `loai_su_kien`: monetary (chính sách tiền tệ), fx (tỷ giá), gold (vàng), credit (tín dụng, trái phiếu), real_estate (bất động sản), regulation (chính sách, quy định), commodity (hàng hóa), crypto (tiền số), equity (thị trường cổ phiếu), geopolitics (địa chính trị, thương mại); NULL khi chưa xếp loại
- `diem`: điểm liên quan từ 0 đến 1 (high ≥ 0,75; medium 0,25–0,5; low 0)
- `luc_dang`: lúc báo đăng (epoch giây)
- `ngay_dang`: ngày báo đăng (giờ Việt Nam)
- `luc_lay`: lúc lấy tin về (epoch giây)
- `ngay_lay`: ngày lấy tin về (giờ Việt Nam)
- `gio_lay`: giờ lấy tin về, HH:MM (giờ Việt Nam)
- `url`: đường dẫn bài báo
- `cong_ty_han_che`: mã các công ty hạn chế mà tin nhắc đến, cách nhau bằng dấu phẩy

## su_kien
Sự kiện: CIO hoặc tác tử gom một nhóm tin thành một sự kiện để nhận định.
- `ma`: mã sự kiện, dạng EV-2026-0001
- `tieu_de`: tiêu đề sự kiện
- `loai`: loại sự kiện (cùng mã với `tin.loai_su_kien`)
- `trang_thai`: open (đang mở)
- `khan`: 1 khi CIO đánh dấu khẩn, 0 khi không
- `nguoi_lap`: ai lập: cio, hoặc agent:… (tác tử)
- `luc_lap`: lúc lập (epoch giây)
- `ngay_lap`: ngày lập (giờ Việt Nam)
- `so_tin`: số tin trong sự kiện
- `bi_giu`: 1 khi sự kiện có tin đang bị Tuân thủ giữ

## nhan_dinh
Nhận định của CIO về một sự kiện; mỗi lần sửa là một phiên bản mới.
- `ma`: mã nhận định, dạng VW-0001-v1
- `ma_su_kien`: mã sự kiện (`su_kien.ma`)
- `phien_ban`: số phiên bản
- `trang_thai`: DRAFTING (đang soạn), PENDING_CHALLENGE (chờ phản biện), PENDING_APPROVAL (chờ duyệt), APPROVED (đã duyệt), REJECTED (bị bác), REWORK_REQUESTED (yêu cầu làm lại), AGENT_ERROR (tác tử lỗi), WITHDRAWN (đã rút), SUPERSEDED (đã thay bằng phiên bản sau)
- `nguoi_lap`: ai lập: cio hoặc agent:…
- `che_do`: live (chạy thật)
- `luc_lap`: lúc lập (epoch giây)
- `ngay_lap`: ngày lập (giờ Việt Nam)
- `tom_tat`: tóm tắt nhận định
- `so_tac_dong`: số tác động (yếu tố thị trường) trong nhận định

## de_xuat
Một lần áp dụng một nhận định đã duyệt lên các gia đình (đề xuất cho RM).
- `ma`: mã lần áp dụng, dạng AR-0001-v1-1
- `ma_nhan_dinh`: mã nhận định (`nhan_dinh.ma`)
- `ma_su_kien`: mã sự kiện
- `trang_thai`: COMPUTING (đang tính), POST_CHECKING (đang hậu kiểm), EFFECTIVE (hiệu lực), NEEDS_CIO_REVIEW (chờ CIO xem lại), FAILED (lỗi tính), SUPERSEDED (đã thay thế), WITHDRAWN (đã thu hồi)
- `nguoi_lap`: ai chạy
- `ma_quyet_dinh`: mã quyết định duyệt, dạng DC-000001
- `ngay_gia`: ngày giá thị trường dùng để tính
- `so_gia_dinh`: số gia đình được tính
- `ky_vong_3thang`: tổng thay đổi giá trị kỳ vọng sau 3 tháng của mọi gia đình, VND (âm là giảm)
- `so_cham_nguong`: số gia đình chạm ngưỡng cần RM xem trước
- `so_muc_tieu_doi`: số mục tiêu đổi trạng thái
- `luc_lap`: lúc chạy (epoch giây)
- `ngay_lap`: ngày chạy (giờ Việt Nam)

## tac_dong_gia_dinh
Tác động của một lần áp dụng lên từng gia đình: chỉ số tổng, không có từng khoản.
- `ma_lan_ap_dung`: mã lần áp dụng (`de_xuat.ma`)
- `ma_su_kien`: mã sự kiện
- `trang_thai_lan`: trạng thái của lần áp dụng (COMPUTING, POST_CHECKING, EFFECTIVE, NEEDS_CIO_REVIEW, FAILED, SUPERSEDED, WITHDRAWN); lần đang dùng là EFFECTIVE
- `ma_gia_dinh`: mã gia đình, dạng C01
- `ten_gia_dinh`: tên chủ hộ
- `tong_tai_san`: tổng tài sản, VND
- `tai_san_rong`: tài sản ròng (tài sản trừ nợ), VND
- `ky_vong_1tuan`: thay đổi giá trị kỳ vọng sau 1 tuần, VND
- `ky_vong_3thang`: thay đổi giá trị kỳ vọng sau 3 tháng, VND
- `ky_vong_12thang`: thay đổi giá trị kỳ vọng sau 12 tháng, VND
- `ty_le_3thang`: thay đổi kỳ vọng 3 tháng so với tài sản ròng, dạng tỷ lệ (-0,0045 là -0,45%)
- `p10_3thang`: kịch bản xấu (phân vị 10) sau 3 tháng, VND
- `cham_nguong`: 1 khi gia đình chạm ngưỡng cần RM xem trước

## du_bao
Dự báo từng yếu tố thị trường của một nhận định, và kết quả khi đến hạn.
- `ma`: mã dự báo
- `ma_nhan_dinh`: mã nhận định
- `ma_su_kien`: mã sự kiện
- `yeu_to`: yếu tố: VN_RATE (lãi suất VN), VN_HOUSE (giá nhà VN), VN_GOV (lợi suất trái phiếu chính phủ VN), VNINDEX, USDVND, US10Y (lợi suất Mỹ 10 năm), SJC_GAP (chênh vàng SJC), RE_SPREAD, GOLD, GLOBAL_EQ (cổ phiếu toàn cầu), FOREIGN_FLOW (khối ngoại), FIN_SPREAD, DXY, BTC, BRENT
- `ky_han`: 1w (1 tuần), 3m (3 tháng), 12m (12 tháng)
- `ngay_goc`: ngày bắt đầu dự báo
- `ngay_den_han`: ngày đến hạn
- `ky_vong`: thay đổi kỳ vọng, theo `don_vi`
- `p10`: phân vị 10 (kịch bản xấu), theo `don_vi`
- `p50`: trung vị, theo `don_vi`
- `p90`: phân vị 90, theo `don_vi`
- `don_vi`: pct (%), bp (điểm cơ bản), pp (điểm phần trăm), sd (độ lệch chuẩn)
- `mo_hinh`: mã mô hình, như FM-EST-2026-09
- `da_cham`: 1 khi đã chấm điểm
- `ket_qua`: scored (đã chấm), no_data (không có số liệu thực tế); NULL khi chưa đến hạn
- `thuc_te`: thay đổi thực tế, theo `don_vi`
- `trong_khoang`: 1 khi thực tế nằm trong khoảng p10–p90
- `dung_huong`: 1 khi đoán đúng hướng

## viec_nen
Các lần chạy việc nền (việc định kỳ hoặc do người bấm).
- `ma`: mã lần chạy, dạng JR-000001
- `viec`: tên việc, như trial_score
- `trang_thai`: running (đang chạy), done (xong), failed (lỗi)
- `nguoi_chay`: ai chạy
- `luc_bat_dau`: lúc bắt đầu (epoch giây)
- `ngay`: ngày bắt đầu (giờ Việt Nam)
- `so_giay`: thời gian chạy, giây
- `loi`: thông báo lỗi, NULL khi không lỗi

## nguon_du_lieu
Các lần lấy số liệu thị trường, một dòng cho một chuỗi số liệu.
- `ma`: số thứ tự lần lấy
- `viec`: market_world, market_crypto, market_gold, market_fx, market_equity, market_yields, market_flows
- `chuoi`: mã chuỗi số liệu, như XAUUSD, USDVND, SPX, SJC, BTCUSD, VN_GOV_5Y
- `nguon`: msn, binance, vcb, pnj, vndirect, hnx, cafef
- `luc_bat_dau`: lúc lấy (epoch giây)
- `ngay`: ngày lấy (giờ Việt Nam)
- `so_diem`: số điểm số liệu lấy được
- `loi`: thông báo lỗi, NULL khi không lỗi

## gia_dinh
Các gia đình trong sổ khách hàng của RM; một dòng là một hộ (chủ hộ).
- `ma_gia_dinh`: mã gia đình, dạng C01
- `ten`: tên chủ hộ
- `tuoi`: tuổi chủ hộ
- `nghe_nghiep`: nghề nghiệp chủ hộ
- `phan_khuc`: phân khúc, như Priority
- `thanh_pho`: thành phố, như TP.HCM
- `so_thanh_vien`: số thành viên trong hộ
- `thu_nhap_thang`: thu nhập mỗi tháng, VND
- `chi_tieu_thang`: chi tiêu mỗi tháng, VND
- `nguong_sut_giam`: mức sụt giảm tài sản tối đa chấp nhận được, dạng tỷ lệ (0,15 là 15%)

## tai_san
Từng khoản tài sản và khoản nợ của gia đình, theo giá trị hiện tại.
- `ma_gia_dinh`: mã gia đình
- `ma_khoan`: mã khoản
- `chu_so_huu`: tên thành viên đứng tên
- `nguon`: techcombank, tcbs, techcom_capital, onehousing, open_api (ngân hàng khác), statement (sao kê), declared (khách tự khai)
- `loai`: asset (tài sản) hoặc liability (khoản nợ)
- `lop`: deposit (tiền gửi), cash (tiền mặt, tài khoản), stock (cổ phiếu), bond (trái phiếu), fund (chứng chỉ quỹ), gold (vàng), real_estate (bất động sản), insurance (bảo hiểm), loan (khoản vay), card (thẻ tín dụng)
- `ten`: tên khoản
- `gia_tri`: giá trị hiện tại, VND (khoản nợ: số còn nợ, số dương)
- `gia_tri_thang_truoc`: giá trị tháng trước, VND
- `gia_von`: giá vốn đã bỏ ra, VND; NULL khi không biết
- `thanh_khoan`: 1 khi rút hoặc bán được nhanh
- `muc_soc`: tỷ lệ giá trị mất đi khi thị trường sốc (0,1 là 10%)
- `do_tin_cay`: verified (đã xác minh), statement (theo sao kê), declared (khách tự khai)

## lien_he
Các lần RM liên hệ gia đình.
- `ma`: mã lần liên hệ
- `ma_gia_dinh`: mã gia đình
- `luc`: lúc liên hệ (epoch giây)
- `ngay`: ngày liên hệ (giờ Việt Nam)
- `nguoi`: ai liên hệ
- `kenh`: Gọi điện, Gặp mặt hoặc Tin nhắn
- `tu_tin_hieu`: 1 khi liên hệ từ một tín hiệu hệ thống gợi ý
- `ghi_chu`: ghi chú

## duyet
Yêu cầu duyệt của khách hàng (như tài khoản cho mục tiêu), chờ hoặc đã có quyết định.
- `ma`: mã yêu cầu
- `ma_khach_hang`: mã khách hàng gửi yêu cầu (có thể là thành viên, như C01S)
- `ma_gia_dinh`: mã gia đình
- `loai`: loại yêu cầu, theo mục tiêu, như tuition (học phí)
- `tieu_de`: tiêu đề yêu cầu
- `trang_thai`: pending_specialist (chờ chuyên gia), approved (đã duyệt), rejected (từ chối)
- `ghi_chu`: ghi chú
- `luc_lap`: lúc gửi (epoch giây)
- `ngay_lap`: ngày gửi (giờ Việt Nam)
- `luc_quyet_dinh`: lúc có quyết định (epoch giây), NULL khi còn chờ

## dong_tien
Giao dịch vào ra trên tài khoản của gia đình bạn.
- `ngay`: ngày giao dịch, YYYY-MM-DD
- `thang`: tháng giao dịch, YYYY-MM
- `so_tien`: số tiền, VND, luôn dương (xem `chieu`)
- `chieu`: in (tiền vào) hoặc out (tiền ra)
- `mo_ta`: nội dung giao dịch
- `nhom`: salary, pension, rent, rent_out, living, card, loan, school, health, other
- `ten_nhom`: tên nhóm: Lương, Lương hưu, Tiền cho thuê, Tiền thuê nhà, Chi tiêu sinh hoạt, Thanh toán thẻ, Trả nợ vay, Học phí, Y tế, other
- `chu_tai_khoan`: tên thành viên có tài khoản

## muc_tieu
Các mục tiêu tài chính của gia đình bạn và tiến độ.
- `ma`: mã mục tiêu, như tuition, retire_early, medical
- `ten`: tên mục tiêu
- `giai_doan`: Gia đình & con cái, Tích lũy tài sản, Nghỉ hưu & chuyển giao, Dự phòng rủi ro
- `dang_theo_doi`: 1 khi bạn đang theo dõi mục tiêu này
- `can`: số tiền cần, VND
- `co`: nguồn đang có cho mục tiêu, VND
- `thieu`: còn thiếu, VND (âm là đã dư)
- `can_de_danh_thang`: cần để dành mỗi tháng, VND
- `du_thang`: số dư mỗi tháng của gia đình, VND
- `han`: hạn, chữ tự do (như 2030, 55 tuổi, trong 12 tháng)
- `trang_thai`: on_track (đúng hướng), at_risk (có rủi ro), off_track (lệch hướng)
- `tien_do`: tiến độ từ 0 đến 1 (`co` / `can`)

## nhat_ky
Nhật ký kiểm toán: ai làm gì, lúc nào (không có nội dung chi tiết).
- `so_thu_tu`: số thứ tự trong nhật ký
- `luc`: lúc ghi (epoch giây)
- `ngay`: ngày ghi (giờ Việt Nam)
- `gio`: giờ ghi, HH:MM (giờ Việt Nam)
- `nguoi`: ai làm: cio, rm01, C01, client:C01, admin, system:ingest, agent:…
- `hanh_dong`: việc làm, như auth.sign_in, news.add, event.create, view.create, challenge.add, decision.approve, run.status, alert.raise, alert.resolve, agent.start, agent.finish, assistant.turn
- `doi_tuong`: đối tượng của việc (mã sự kiện, mã nhận định, người…)

## canh_bao
Cảnh báo hệ thống thuộc vai trò của bạn.
- `ma`: mã cảnh báo
- `loai`: news_feed (nguồn tin không lấy được), market_job (chuỗi thị trường không lấy được), agent (tác tử lỗi), inbox (gói từ vùng AI bị từ chối), audit_chain (chuỗi nhật ký kiểm toán gãy), zone_sync (không gửi được vùng AI), job (việc nền chạy tay lỗi), availability (sẵn sàng dưới 99,5 %)
- `khoa`: khóa gộp: cùng loại và khóa là một cảnh báo
- `trang_thai`: open (đang mở), acked (đã xem), resolved (đã xử lý)
- `muc_do`: medium hoặc high
- `tieu_de`: tiêu đề
- `chi_tiet`: chi tiết
- `so_lan`: số lần cảnh báo lặp lại
- `luc_tao`: lúc tạo (epoch giây)
- `ngay_tao`: ngày tạo (giờ Việt Nam)
- `luc_gan_nhat`: lần gần nhất (epoch giây)
