# Hướng dẫn cho CIO

Các trang của CIO (`#/cio/…`): từ tin thị trường tới nhận định được duyệt, áp dụng cho mọi gia đình, và chất lượng
của mô hình, và các chốt kiểm soát: tin bị giữ, nghiên cứu, bài viết, chính sách, nhật ký. Việc hai người (duyệt cấu
hình, phát hành nghiên cứu, duyệt bài viết, xác nhận nguồn văn bản) cần một CIO khác: người làm không tự duyệt.

## Bàn quyết định — #/cio

Trang đầu của CIO: dòng chảy từ tin tới gia đình (tin, sự kiện, nhận định, lần áp dụng, gia đình, RM), những việc
chờ CIO quyết định (cả tin bị giữ, nghiên cứu chờ phát hành, văn bản chờ xác nhận nguồn, bài viết chờ duyệt),
phơi nhiễm theo yếu tố, sự kiện gần đây, mô hình và các agent. Duyệt nhận định làm ở trang Sự kiện
& nhận định; cấu hình CIO sở hữu cần một CIO khác duyệt.

## Agent chạy nền — #/cio/agent

Agent CIO chạy khi CIO bấm **Chạy Agent CIO** trên một sự kiện (vào hàng đợi, mỗi lần một việc); Agent Phản biện kiểm
tra nhận định trước khi duyệt; Agent Chính sách tóm tắt văn bản đã xác nhận. Việc nền theo lịch: lấy tin mỗi 10 phút,
dữ liệu thị trường theo lịch từng nguồn, quét chính sách 07:00, tổng hợp trí nhớ mỗi 5 phút, lưu giữ 02:30. Trang
Agent cho thấy từng agent và việc nền: trạng thái, lần chạy gần nhất, số lần chạy và lỗi hôm nay.

## Việc nền — #/cio/viec-nen

Các agent và việc nền trên một trang. **Agent**: chế độ (mô hình thật hay mô phỏng), token đã dùng hôm nay, từng agent
trong 7 ngày, các lần “Chạy Agent CIO”. CIO bấm **Chạy Agent CIO** trên một sự kiện chưa có nhận định, và **Phản biện
lại** khi Agent Phản biện lần trước lỗi. Nhận định ra là bản nháp: qua Agent Phản biện, rồi CIO duyệt ở trang Sự kiện
& nhận định. **Lịch chạy**: từng việc nền, lịch và lần gần nhất (Quản trị chạy ngay được). Trợ lý chạy Agent CIO hay
chạy lại Agent Phản biện khi CIO bấm Xác nhận; nó không duyệt nhận định.

## Hộp tin — #/cio/hop-tin

Nằm ngay trên Bàn quyết định: “<n> tin chờ xử lý”. Tin được lấy tự động mỗi 10 phút từ các nguồn đã duyệt; **Lấy tin ngay**
để lấy liền. **Tình trạng nguồn tin (24 giờ)** cho biết lần lấy cuối và số tin mỗi giờ của từng nguồn. Lọc theo nguồn,
trong nước / quốc tế, mức liên quan và từ khóa. Đánh dấu các tin rồi **Bỏ tin**, hoặc **Gom thành sự kiện** để tạo một
sự kiện. Tin nhắc tới tổ chức trong danh sách hạn chế không ở đây mà bị giữ ở Tin bị giữ.

## Tin bị giữ — #/cio/giu

Tin nhắc tới tổ chức trong danh sách hạn chế, với nguồn, thời gian và các tên được nhắc. Nhập **Lý do cho phép** (bắt
buộc) rồi **Cho phép**; việc này được ghi nhật ký và gỡ điều kiện duyệt *g* của các sự kiện đang bị giữ vì tin đó. Bên
cạnh là **Danh sách hạn chế** (dữ liệu giả lập: tên, mã, tên khác).

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

Báo cáo nghiên cứu và ghi chú quy định; một CIO nạp, một CIO khác phát hành. **Nạp báo cáo mới**: loại, số, giờ phát hành, xung đột
lợi ích, tiêu đề, tóm tắt; với ghi chú quy định thêm văn bản, tình trạng, ngày hiệu lực, số tuần chuẩn bị, mục đích,
quốc gia, giấy tờ, lời nhắn cho khách và gợi ý cho RM. Danh sách cho biết người nạp, người quyết, số mục tiêu bị ảnh
hưởng và trạng thái. Mục người khác nạp có ô ghi chú (từ 20 ký tự) và **Phát hành** / **Từ chối**; bị từ chối khi
ghi chú quá ngắn, người nạp tự phát hành, chưa tới giờ phát hành, hoặc báo cáo nhắc tên trong danh sách hạn chế.

## Bản tin — #/cio/ban-tin

Soạn bản tin từ các nhận định đã duyệt: chọn nhận định, tiêu đề, mở đầu (theo mẫu hoặc Agent CIO), giờ gửi, gửi sớm cho
nhóm Private (số giờ và lý do), xung đột lợi ích. Mở một bản tin để xem trước như khách đọc, **Kiểm tra nội dung**,
**Sửa**, **Gửi CIO khác duyệt** (khi kiểm tra đạt), **Rút bản tin** và lịch sử. Chỉ người soạn sửa, gửi hay rút
bài. Bài của CIO khác đang chờ thì bạn **Duyệt** hoặc **Trả lại** (ghi chú từ 10 ký tự); bài chưa qua kiểm tra nội
dung không duyệt được.

## Chính sách — #/cio/chinh-sach

Radar chính sách: các văn bản đang theo dõi, **Mới** / **Thay đổi** từ lần xem trước, tình trạng. **Thêm văn bản**
(địa chỉ công báo, hoặc địa chỉ chính thức kèm số, cơ quan ban hành, ngày, tình trạng và nội dung). Mở một văn bản:
bản tóm tắt của Agent Chính sách với trích dẫn từng điều (chỉ dùng nội bộ), **Chạy Agent Chính sách** sau khi nguồn đã
xác nhận, **Xác nhận nguồn** (một CIO khác người thêm), **Cập nhật trạng thái** và lịch sử.

## Nhật ký — #/cio/nhat-ky

Kết quả kiểm tra chuỗi nhật ký (nguyên vẹn, hoặc “Gãy ở dòng n” và lý do), rồi 200 dòng mới nhất: lúc, ai, việc, đối
tượng, mã băm. **Tải JSON (kèm kiểm tra chuỗi)** và **Tải CSV**. Dòng cũ vẫn ghi vai trò lúc đó (Tuân thủ, Chuyên gia).

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

CIO duyệt Mô hình yếu tố, Ngưỡng cảnh báo, Giả định lợi suất, Danh sách hạn chế, Cụm từ cấm, Đồng ý chia sẻ dữ liệu,
Bên liên quan (xung đột lợi ích), Nhóm đối chứng và Lưu giữ hội thoại với trợ lý; các loại khác thuộc Quản trị. Mỗi loại
cấu hình một bảng: người sở hữu, có cần hai người không, có bộ đánh giá không; phiên bản đang hiệu lực và nội
dung tóm tắt. **Đề xuất thay đổi** (sửa JSON kèm lý do); đề xuất đang chờ hiện người đề xuất, lý do, các trường đổi và
kết quả bộ đánh giá (với prompt và mô hình). Vai trò sở hữu thấy **Duyệt** (chỉ bấm được khi bộ đánh giá đạt) và **Từ
chối**; người đề xuất không tự duyệt được việc hai người. Bên dưới là lịch sử các phiên bản.

## Cấu hình: Lưu giữ hội thoại với trợ lý — #/cio/cau-hinh

Đổi số ngày giữ cuộc trò chuyện với trợ lý sau lượt cuối (từ 30 tới 3650, mặc định 365): ở Cấu hình, bảng **Lưu giữ
hội thoại với trợ lý**, **Đề xuất thay đổi**; một CIO khác duyệt. Việc nền lưu giữ chạy 02:30 xoá cuộc trò chuyện quá hạn.
