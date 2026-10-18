# Hướng dẫn cho Quản trị

Các trang của Quản trị (`#/admin/…`).

## Vận hành — #/admin

Trang đầu của Quản trị: hệ thống như một bản đồ (nguồn → lưu trữ → AI → người dùng), mỗi phần xanh, vàng hay đỏ theo
lần ghi nhận gần nhất; cảnh báo, việc lỗi, cấu hình chờ duyệt, người dùng theo vai trò, chuỗi nhật ký. Cấu hình do
vai trò khác sở hữu (ngưỡng của CIO, chứng nhận chuyên gia của Tuân thủ) thì vai trò đó duyệt. Quản trị không xem tài
sản hay danh mục của khách.

## Hệ thống — #/admin/he-thong

Trang đầu tiên của Quản trị.

- **Bốn ô**: kiểm tra chuỗi nhật ký, chế độ và mô hình của các agent, lần lấy tin cuối, cấu hình đang chờ duyệt.
- **Cảnh báo**: 30 cảnh báo gần nhất (loại, số lần, lần cuối, lỗi, trạng thái Đang mở / Đã xem / Đã hết, ai đã xem kèm
  ghi chú); **Đã xem** trên một cảnh báo đang mở (ghi chú tùy chọn, được ghi nhật ký).
- **Tác vụ nền**: mọi tác vụ định kỳ, làm gì, khi nào chạy, lần chạy cuối ra sao.
- **Nguồn tin**: lần lấy cuối của từng nguồn: số tin lấy, nhận, loại và lỗi.
- **Agent**: 7 ngày qua theo từng agent: số lần chạy, lỗi, lần cuối.
- **Vùng AI và hộp chờ**: chế độ chạy AI đang hiệu lực, 10 gói gần nhất từ vùng AI và lần đồng bộ cuối.
- **Nạp lại lịch sử thị trường**: chọn ngày bắt đầu (từ 2015-01-01) rồi gửi; tác vụ chạy trong vòng một phút, từng lần
  một, với trạng thái Đang chờ / Đang nạp / Xong / Lỗi.
- **Nhật ký hệ thống**: 30 cảnh báo và lỗi gần nhất.
- **Người dùng**: mọi tài khoản nhân viên (tên, chức danh, vai trò, đăng nhập, đã có mật khẩu chưa, các gia đình của
  RM) và số tài khoản khách; liên kết tới “Phân công RM” trong Cấu hình. Đặt mật khẩu không làm ở đây.

## Dữ liệu thị trường — #/admin/du-lieu

Như trang Dữ liệu thị trường của CIO: nguồn và lịch lấy, yếu tố lấy từ đâu, các chuỗi đang lưu.

## Cấu hình — #/admin/cau-hinh

Như trang Cấu hình của CIO. Quản trị duyệt các loại của mình: Nguồn tin (danh sách trắng), Nguồn dữ liệu thị trường,
Bảng mã chứng khoán, Phân công RM, Chế độ chạy AI, AI với dữ liệu khách hàng (mô hình có được đọc dữ liệu khách hay
không), Lời nhắc của agent và Mô hình AI của agent.

## Agent — #/admin/agent

Các tác vụ AI và chất lượng của chúng.

## Việc nền — #/admin/viec-nen

Các việc nền theo lịch và các agent trên một trang. **Lịch chạy**: từng việc, lịch, lần gần nhất và lỗi; Quản trị bấm
**Chạy ngay** cho lấy tin, tin tham chiếu, các việc giá (cổ phiếu, tỷ giá, vàng…), quét chính sách, kiểm tra chuỗi
nhật ký, nhập và gửi vùng AI, chấm độ chính xác. Mỗi việc chạy một lần một lúc; lần chạy được ghi nhật ký, lỗi thì có
cảnh báo. Nhịp máy chủ, hàng đợi agent, tổng hợp trí nhớ và lưu giữ không chạy tay.
**Lần chạy tay**: ai chạy việc gì, lúc nào, kết quả. Trợ lý chạy ngay một việc khi Quản trị bấm Xác nhận. Các agent
(Agent CIO, Agent Phản biện) do CIO chạy.

## Nhật ký — #/admin/nhat-ky

Như trang Nhật ký của Tuân thủ: kiểm tra chuỗi và các dòng mới nhất, tải JSON hoặc CSV.
