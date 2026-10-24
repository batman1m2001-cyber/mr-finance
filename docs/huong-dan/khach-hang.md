# Hướng dẫn cho khách hàng

Các trang của khách hàng (`#/client/…`). RM cũng thấy phần lớn các trang này trong mục “Khách hàng”, cho gia đình
đang chọn.

## Wealth View — #/client/tong-quan

Màn hình chính của khách hàng.

Thanh bên trái có bốn mục, đúng tên của ngân hàng: **Wealth View**, **Wealth Planning Advisor**, **Headline News** và
**Relationship specialist**. Wealth View có hai thẻ: **Wealth view** (trang này) và **Dữ liệu chi tiết tài sản**.
Wealth Planning Advisor có hai thẻ: **Wealth planning advisor** (kế hoạch) và **Risk profile test** (bài test khẩu vị
rủi ro). Headline News có hai thẻ: **News and Prediction** (chi phí chính sách) và **Đồ thị tác động**.

Wealth view là toàn bộ bức tranh tài chính của bạn ở một trang, mọi con số ở một chỗ (các địa chỉ cũ — Toàn cảnh
`#/client/tong-quan/toan-canh`, Chi tiết `#/client/tong-quan/chi-tiet`, Dòng tiền `#/client/dong-tien`, đồ thị tài
chính trước đây `#/client/xem/…` và `#/client/tong-quan/ban-do` — đều mở trang này hoặc trang của mục đó). Khách hàng
không còn trang đồ thị: nhìn Wealth view là đủ. Theo thứ tự:

- **Tài sản ròng** (tổng tài sản trừ nợ, so với tháng trước, ngày số liệu, các thành viên được tính) và **tài sản theo
  nguồn dữ liệu**: tại hệ sinh thái Techcombank, lưu ký bên ngoài, bạn tự quản lý; bấm một nhóm để xem từng nguồn.
- **Phân bổ tài sản** với lãi / lỗ từng nhóm so với giá vốn, và **lãi / lỗ danh mục** (đã chốt, chưa chốt, lợi nhuận
  từ đầu năm so với VN-Index).
- **Dòng tiền**: 6 tháng qua và dự báo 12/24/36 tháng, các khoản phải trả lớn và các khoản định kỳ tìm thấy trong giao
  dịch.
- **Tiền vào và ra trong tháng**: chọn tháng; biểu đồ dòng chảy từ nguồn tiền vào (lương, cổ tức…) sang các nhóm chi và
  phần còn lại; ba tỷ lệ (tỷ lệ để dành, tiền ra trên tiền vào, nhóm chi lớn nhất) và bảng chi tiết. Bấm một dải để
  xem các giao dịch tạo nên nó. Tháng không có giao dịch hiện “Không có giao dịch trong tháng này.”
- **Rủi ro**: mức sụt giảm chấp nhận so với ước tính khi căng thẳng, cảnh báo tập trung.
- **Thanh khoản dự phòng** (quỹ khẩn cấp): tiền và tài sản rút được ngay, đủ chi bao nhiêu tháng so với mốc an toàn 6
  tháng.
- **Chính sách và dự án** nổi bật. Chưa làm bài kiểm tra rủi ro thì ngưỡng lấy theo hồ sơ.

Mục tiêu đang theo dõi ở Wealth Planning Advisor.

## Dữ liệu chi tiết tài sản — #/client/tai-san

Thẻ thứ hai của Wealth View. Mọi tài sản và khoản nợ, nhóm theo loại, mỗi khoản có nguồn và mức tin cậy: **Đã xác thực** (từ ngân hàng), **Từ sao
kê**, **Bạn tự khai**; ngày và giá mua, giá vốn, giá trị hiện tại, lãi / lỗ; cuối bảng là tổng tài sản, nợ và tài sản
ròng.

- **Tải sao kê**: chọn tệp PDF, Excel hoặc CSV của công ty chứng khoán hay ngân hàng khác (hoặc dùng sao kê mẫu); các
  khoản đọc được hiện với nhãn “Từ sao kê”.
- **Bổ sung tài sản**: gõ một câu như “Tôi có căn hộ ở Thủ Đức khoảng 5 tỷ”; ứng dụng trả lời đã ghi gì và bảng có thêm
  dòng.

## Wealth Planning Advisor — #/client/muc-tieu/ke-hoach

Kế hoạch tài chính, cố vấn kế hoạch tài sản: các chỉ số tổng (tài sản ròng, lãi / lỗ danh mục, mục tiêu đã đủ tiền, dòng tiền ròng 12
tháng), số cần so với số có cho từng mục tiêu và số tiền cần để dành mỗi tháng.

- **Mục tiêu cuộc sống**: nhóm theo gia đình và con cái, tích lũy, hưu trí và chuyển giao, quỹ dự phòng, quyết định và
  kịch bản căng thẳng. Chọn một mục để xem trạng thái (cần / có / thiếu), theo dõi so với dự kiến, **Việc cần làm** xếp
  theo thứ tự, **Chi tiết tính toán** (sửa giả định rồi **Chạy lại**, bảng trước / sau) và phương án nhẹ / mạnh.
- **Gửi chuyên gia duyệt**: gửi một việc hay phương án tới RM; theo dõi ở Relationship specialist.
- **Lưu ý quy định cho mục tiêu**: quy định mới có liên quan tới mục tiêu của bạn, mức độ và mốc cần chuẩn bị.

## Risk profile test — #/client/rui-ro/khau-vi

Thẻ thứ hai của Wealth Planning Advisor: bài kiểm tra khẩu vị rủi ro: bấm “Bắt đầu”, trả lời 8–12 câu tình huống (câu sau tùy câu trước, có thanh tiến độ và
nút “← Câu trước”). Kết quả: mức chịu đựng rủi ro và khả năng chịu rủi ro trên năm mức, câu giải thích khi hai mức
khác nhau, hình mẫu nhà đầu tư và ngưỡng sụt giảm mới — ngưỡng này được dùng ở phần Rủi ro của Wealth View.

## News and Prediction — #/client/tin/chinh-sach

Thẻ đầu của Headline News (trước đây là Chi phí chính sách). Chính sách (lãi suất, thuế, quy định…) có thể làm bạn mất hay được bao nhiêu: **Tác động lên tài sản ròng** theo từng
chính sách (lọc tất cả / rủi ro / cơ hội), nhận định của các nhà nghiên cứu khớp với tài sản của bạn (dữ liệu giả
định), và từng thẻ chính sách: mức độ, tình trạng pháp lý, tác động có xác suất, cách tính (giá trị × độ nhạy × xác
suất) và nguồn.

## Đồ thị tác động — #/client/tin/do-thi

Thẻ thứ hai của Headline News. Tin nào chạm tới tiền của bạn, qua đường nào, tới mục tiêu nào — đọc từ trái sang phải qua bảy cột: Tin, Sự kiện,
Kịch bản, Yếu tố, Tài sản, Gia đình, Mục tiêu. Bấm một nút để làm sáng đường đi của nó; bấm lần nữa hoặc “Bỏ chọn” để
bỏ. Chọn một sự kiện mở bảng tác động: hướng, kịch bản chính, các nhóm tài sản và mục tiêu trước → sau. Có nút chuyển
“Đồ thị / Danh sách” và bộ lọc theo loại.

## Tác động tin — #/client/tin/thi-truong

Không còn là một thẻ: trang mở từ chuông, từ “Điều đáng chú ý” và từ liên kết “Tác động của tin” trên Wealth View. Sau khi CIO duyệt một nhận định về tin thị trường và hậu kiểm đạt, trang này cho biết tài sản của bạn có thể thay đổi
bao nhiêu trong 3 tháng tới, dải dao động rộng hay hẹp và đến từ đâu — theo nhóm tài sản, không nêu mã cổ phiếu, không
phải khuyến nghị.

- **Con số chính**: mức thay đổi kỳ vọng 3 tháng, phần trăm tài sản ròng, công thức bằng lời, ngày giá, người duyệt.
- **Dải kết quả có thể**: đường kỳ vọng và dải P10–P90 ở 1 tuần, 3 tháng, 12 tháng.
- **Đến từ đâu**: đóng góp theo nhóm tài sản.
- **Sự kiện**: từng sự kiện đang hiệu lực theo loại, thay đổi 3 tháng; **Xem dải** để vẽ dải của sự kiện đó; **Cách
  tính** mở cách ra con số; **Dòng thời gian**: từ tin đầu tiên tới lúc có hiệu lực.
- **Lưu ý cho mục tiêu của bạn**: tác động 3 tháng lên từng mục tiêu (VND, P10, P90) và việc nên chuẩn bị trước hạn.

Chưa có tin nào được duyệt thì trang báo tác động sẽ hiện khi có.

## Relationship specialist — #/client/chuyen-gia

Chuyên gia của bạn: chuyên viên quan hệ khách hàng (tên, liên hệ — dữ liệu demo) và **Hàng chờ chuyên gia duyệt**: các phương án
bạn đã gửi từ Wealth Planning Advisor, đang chờ hay đã được duyệt / từ chối kèm ghi chú. Trang này chỉ để xem; RM quyết
định ở trang của họ.
