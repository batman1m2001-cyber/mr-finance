# Hướng dẫn cho CIO

Các trang của CIO (`#/cio/…`): từ tin thị trường tới nhận định được duyệt, áp dụng cho mọi gia đình, và chất lượng
của mô hình. Việc hai người (duyệt cấu hình, mô hình) cần một CIO khác.

## Bàn quyết định — #/cio

Trang đầu của CIO: dòng chảy từ tin tới gia đình (tin, sự kiện, nhận định, lần áp dụng, gia đình, RM), những việc
chờ CIO quyết định, phơi nhiễm theo yếu tố, sự kiện gần đây, mô hình và các agent. Duyệt nhận định làm ở trang Sự kiện
& nhận định; cấu hình CIO sở hữu cần một CIO khác duyệt.

## Agent chạy nền — #/cio/agent

Agent CIO chạy khi CIO bấm **Chạy Agent CIO** trên một sự kiện (vào hàng đợi, mỗi lần một việc); Agent Phản biện kiểm
tra nhận định trước khi duyệt; Agent Chính sách tóm tắt văn bản đã xác nhận. Việc nền theo lịch: lấy tin mỗi 10 phút,
dữ liệu thị trường theo lịch từng nguồn, quét chính sách 07:00, tổng hợp trí nhớ mỗi 5 phút, lưu giữ 02:30. Trang
Agent cho thấy từng agent và việc nền: trạng thái, lần chạy gần nhất, số lần chạy và lỗi hôm nay. Trợ lý đọc được
trạng thái này nhưng không chạy agent.

## Hộp tin — #/cio/hop-tin

Trang đầu tiên của CIO: “<n> tin chờ xử lý”. Tin được lấy tự động mỗi 10 phút từ các nguồn đã duyệt; **Lấy tin ngay**
để lấy liền. **Tình trạng nguồn tin (24 giờ)** cho biết lần lấy cuối và số tin mỗi giờ của từng nguồn. Lọc theo nguồn,
trong nước / quốc tế, mức liên quan và từ khóa. Đánh dấu các tin rồi **Bỏ tin**, hoặc **Gom thành sự kiện** để tạo một
sự kiện. Tin nhắc tới tổ chức trong danh sách hạn chế không ở đây mà bị giữ chờ Tuân thủ.

## Sự kiện & nhận định — #/cio/nhan-dinh

Danh sách sự kiện (mới nhất trước) với trạng thái nhận định của chúng. Mở một sự kiện để xem tin nguồn (tin bị giữ được
đánh dấu) và bảng **Agent CIO**: chế độ chạy (trực tiếp với hai mô hình, hoặc mô phỏng) và **Chạy Agent CIO** để soạn
nhận định; bên dưới là các phiên bản.

## Nhận định — #/cio/nhan-dinh/VW-…

Đọc nhận định, xem phản biện, trả lời, xem trước tác động lên thị trường rồi quyết định.

- Tiến trình: Agent soạn → Phản biện → CIO duyệt → Đã duyệt.
- **Điều kiện duyệt** a–g với ✓ / ✕ và lý do; **Duyệt và áp dụng** chỉ bấm được khi mọi điều kiện đạt; **Trả lại**,
  **Bác**; sau khi duyệt có **Thu hồi nhận định**.
- **Kịch bản**: xác suất các nhánh, cú sốc chính theo yếu tố, lan truyền ra thị trường, lập luận.
- **Dòng tác động** và **Phản biện độc lập** (phát hiện theo mức độ, ô trả lời cho từng phát hiện còn mở).
- **Lần áp dụng** do lần duyệt tạo ra; **Vết chạy agent** từng bước (đầu vào, prompt, mô hình, đầu ra).
- Sửa tóm tắt, dòng tác động hay kịch bản thì nhận định quay lại bước phản biện.

## Phơi nhiễm — #/cio/phoi-nhiem

Cho lần áp dụng hiệu lực mới nhất: tổng thay đổi kỳ vọng 3 tháng theo yếu tố trên mọi gia đình, xếp hạng gia đình (xấu
nhất trước, gia đình bị gắn cờ được đánh dấu) và bản đồ nhiệt gia đình × yếu tố (% tài sản ròng).

## Lần áp dụng — #/cio/ap-dung

Một lần áp dụng: trạng thái, nhận định, số gia đình, ngày giá, phiên bản mô hình và bộ tính. **Kiểm tra tính lại**
(khớp tới từng đồng) và **Thẩm định lại với dữ liệu mới**. Tổng kỳ vọng 3 tháng, **Hậu kiểm** (các phát hiện P1–P5),
**Thu hồi lần áp dụng** với lý do, hoặc **Cho hiệu lực** một lần đang bị giữ; lịch sử trạng thái và danh sách mọi lần
áp dụng.

## Đồ thị lần áp dụng — #/cio/do-thi

Một lần áp dụng vẽ thành sáu cột: Tin, Sự kiện, Kịch bản, Yếu tố, Nhóm tài sản, Gia đình — mọi gia đình được tính, cạnh
mang thay đổi 3 tháng của gia đình. Chọn lần áp dụng khác ở ô chọn; chọn một nút để làm sáng đường đi.

## Nghiên cứu — #/cio/nghien-cuu

Báo cáo nghiên cứu và ghi chú quy định chờ Tuân thủ phát hành. **Nạp báo cáo mới**: loại, số, giờ phát hành, xung đột
lợi ích, tiêu đề, tóm tắt; với ghi chú quy định thêm văn bản, tình trạng, ngày hiệu lực, số tuần chuẩn bị, mục đích,
quốc gia, giấy tờ, lời nhắn cho khách và gợi ý cho RM. Danh sách cho biết người nạp, người quyết, số mục tiêu bị ảnh
hưởng và trạng thái. Người nạp không tự phát hành được.

## Bản tin — #/cio/ban-tin

Soạn bản tin từ các nhận định đã duyệt: chọn nhận định, tiêu đề, mở đầu (theo mẫu hoặc Agent CIO), giờ gửi, gửi sớm cho
nhóm Private (số giờ và lý do), xung đột lợi ích. Mở một bản tin để xem trước như khách đọc, **Kiểm tra nội dung**,
**Sửa**, **Gửi Tuân thủ duyệt** (khi kiểm tra đạt), **Rút bản tin** và lịch sử.

## Chính sách — #/cio/chinh-sach

Radar chính sách, chỉ đọc với CIO: các văn bản đang theo dõi, thay đổi từ lần xem trước, tình trạng và bản tóm tắt của
Agent Chính sách. Tuân thủ thêm văn bản và cập nhật tình trạng.

## Mô hình: Tham số — #/cio/mo-hinh/tham-so

Phiên bản mô hình yếu tố, cách tính bốn bước, 15 yếu tố với cỡ cú sốc, mức thể hiện ở 1 tuần / 3 tháng / 12 tháng, độ
biến động bình thường và căng thẳng, mỗi tham số ghi “ước lượng” hay “giả định”. **Ước lượng từ dữ liệu thị trường**:
yếu tố nào đủ dữ liệu, độ phủ ngoài mẫu và kết luận từng yếu tố; **Đề xuất làm phiên bản mới** đưa ước lượng sang Cấu
hình để một CIO khác duyệt.

## Mô hình: Dữ liệu thị trường — #/cio/mo-hinh/du-lieu

Bao nhiêu yếu tố có dữ liệu thật; các nguồn và lịch lấy với lần thành công và lỗi gần nhất; mỗi yếu tố lấy từ đâu (dữ
liệu thị trường, tính ra, hay giả định); các chuỗi đang lưu với giá trị cuối, nguồn đang dùng và đường 120 ngày.

## Mô hình: Độ chính xác — #/cio/mo-hinh/do-chinh-xac

Chọn kỳ (1 tuần / 3 tháng / 12 tháng). Tỷ lệ biến động thực tế nằm trong dải P10–P90 trên lịch sử, hướng VN-Index so
với mục tiêu 70%, các nhận định đã duyệt và ngày tới hạn chấm. Bảng mô hình chạy lại trên lịch sử theo từng yếu tố (vùng
chấp nhận 70–90%) và dự báo của các nhận định đã duyệt khi đã tới hạn.

## Đo lường — #/cio/do-luong

Bốn bảng hằng tháng: **Bỏ sót** (tin quan trọng không thành sự kiện, sự kiện không tới gia đình), **Duyệt cho có** (thời
gian từ sẵn sàng tới duyệt, số lần duyệt dưới 2 phút, tỷ lệ duyệt không sửa), **Từ tin đến RM** (giờ từ tin đầu tiên tới
lần áp dụng hiệu lực, so với 2 giờ), **Tốc độ hộp tin và Agent**.

## Agent — #/cio/agent

Mỗi tác vụ AI một thẻ: chế độ (Trực tiếp, Mô phỏng, Từ khóa, Mẫu tất định, Chưa xây), mục đích, người chịu trách nhiệm,
rủi ro, mô hình, được đọc gì, lần chạy gần nhất; rồi **Chất lượng AI** 7 ngày và từ đầu.

## Cấu hình — #/cio/cau-hinh

CIO duyệt Mô hình yếu tố, Ngưỡng cảnh báo và Giả định lợi suất; các loại khác thuộc Tuân thủ hoặc Quản trị. Mỗi loại
cấu hình một bảng: người sở hữu, có cần hai người không, có bộ đánh giá không; phiên bản đang hiệu lực và nội
dung tóm tắt. **Đề xuất thay đổi** (sửa JSON kèm lý do); đề xuất đang chờ hiện người đề xuất, lý do, các trường đổi và
kết quả bộ đánh giá (với prompt và mô hình). Vai trò sở hữu thấy **Duyệt** (chỉ bấm được khi bộ đánh giá đạt) và **Từ
chối**; người đề xuất không tự duyệt được việc hai người. Bên dưới là lịch sử các phiên bản.
