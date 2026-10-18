# Hướng dẫn cho Tuân thủ

Các trang của Tuân thủ (`#/compliance/…`). Nhiều việc cần hai người Tuân thủ khác nhau.

## Bàn kiểm soát — #/compliance

Trang đầu của Tuân thủ: mỗi chốt kiểm soát một dòng (tin bị giữ, nghiên cứu, bản tin, chính sách, cấu hình) với số
việc chờ ở từng bước, chuỗi nhật ký, một hàng chờ chung cũ nhất trước và các cảnh báo. Mỗi quyết định làm ở trang của
nó với quy tắc của nó: cho tin đi tiếp cần lý do; nghiên cứu do người khác người nạp phát hành, khi đã tới giờ; văn bản
chính sách do người thứ hai xác nhận. Tuân thủ không xem bảng tài sản của khách.

## Tin bị giữ — #/compliance/giu

Trang đầu tiên của Tuân thủ: tin nhắc tới tổ chức trong danh sách hạn chế, với nguồn, thời gian và các tên được nhắc.
Nhập **Lý do cho phép** (bắt buộc) rồi **Cho phép**; việc này được ghi nhật ký và gỡ điều kiện duyệt *g* của các sự
kiện đang bị giữ vì tin đó. Bên cạnh là **Danh sách hạn chế** (dữ liệu giả lập: tên, mã, tên khác). Chỉ Tuân thủ được
cho phép.

## Nghiên cứu — #/compliance/nghien-cuu

Danh sách báo cáo và ghi chú quy định chờ phát hành. Mỗi mục chờ có ô **Ghi chú của Tuân thủ** (từ 20 ký tự) và nút
**Phát hành** / **Từ chối**. Bị từ chối khi: ghi chú quá ngắn, người nạp tự phát hành, chưa tới giờ phát hành, hoặc báo
cáo nhắc tên trong danh sách hạn chế.

## Bản tin — #/compliance/ban-tin

Các bản tin CIO gửi duyệt. Mở một bản tin để đọc như khách sẽ đọc; khi đang chờ, **Duyệt** hoặc **Trả lại** (ghi chú từ
10 ký tự). Người soạn không tự duyệt được; bản tin chưa qua kiểm tra nội dung không duyệt được. Gửi sớm cho nhóm
Private hiện cảnh báo với cả hai giờ gửi và lý do của CIO.

## Chính sách — #/compliance/chinh-sach

Radar chính sách: các văn bản đang theo dõi, **Mới** / **Thay đổi** từ lần xem trước, tình trạng. Tuân thủ **Thêm văn
bản** (địa chỉ công báo, hoặc địa chỉ chính thức kèm số, cơ quan ban hành, ngày, tình trạng và nội dung). Mở một văn
bản: bản tóm tắt của Agent Chính sách với trích dẫn từng điều (chỉ dùng nội bộ, không gửi khách), **Chạy Agent Chính
sách** sau khi nguồn đã được xác minh, phần xác minh nguồn (do một người Tuân thủ thứ hai), **Cập nhật trạng thái** và
lịch sử.

## Đo lường — #/compliance/do-luong

Như trang Đo lường của CIO: bỏ sót, duyệt cho có, thời gian từ tin tới RM, tốc độ hộp tin và Agent.

## Nhật ký — #/compliance/nhat-ky

Kết quả kiểm tra chuỗi nhật ký (nguyên vẹn, thuật toán đang dùng; hoặc “Gãy ở dòng n” và lý do), rồi 200 dòng mới nhất:
lúc, ai, việc, đối tượng, mã băm. **Tải JSON (kèm kiểm tra chuỗi)** và **Tải CSV** để tải toàn bộ. Cơ sở dữ liệu chặn
sửa và xoá nhật ký.

## Agent — #/compliance/agent

Như trang Agent của CIO: các tác vụ AI, chế độ, rủi ro, mô hình, lần chạy và chất lượng.

## Cấu hình — #/compliance/cau-hinh

Như trang Cấu hình của CIO. Tuân thủ duyệt các loại của mình: Danh sách hạn chế, Cụm từ cấm, Đồng ý chia sẻ dữ liệu,
Bên liên quan (xung đột lợi ích), Chứng nhận chuyên gia, Nhóm đối chứng và **Lưu giữ hội thoại với trợ lý** (số ngày
giữ cuộc trò chuyện với trợ lý sau lượt cuối, từ 30 tới 3650, mặc định 365; hai người duyệt).
