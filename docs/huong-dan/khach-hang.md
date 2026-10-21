# Hướng dẫn cho khách hàng

Các trang của khách hàng (`#/client/…`). RM cũng thấy phần lớn các trang này trong mục “Khách hàng”, cho gia đình
đang chọn.

## Đồ thị tài chính (màn hình chính) — #/client/xem/tong-quan

Màn hình chính của khách hàng là một đồ thị luôn hiện. **Vòng tròn lớn ở giữa là bạn**: con số trong vòng là tài sản
ròng (tổng tài sản trừ nợ). Ở chế độ **Gia đình** vẫn chỉ có một vòng, là tổng của cả nhà; chữ cái đầu trên viền một
khoản cho biết khoản đó của thành viên nào (một số nếu nhiều người cùng có). Quanh vòng là các nhóm: lớp tài sản, tiền
vào và tiền ra, thanh khoản dự phòng, mục tiêu, rủi ro, kịch bản, tin và chính sách.

- **Góc nhìn** (thanh công cụ): Tổng quan, Tài sản (`#/client/xem/tai-san`), Dòng tiền (`…/dong-tien`), Mục tiêu &
  kịch bản (`…/muc-tieu`), Tin & sự kiện (`…/tin`), Rủi ro (`…/rui-ro`). Mỗi góc nhìn làm nổi các loại liên quan; đồ
  thị không đổi chỗ.
- **Đường nối**: nét liền là tiền và các khoản thực tế đã ghi nhận (càng dày càng nhiều tiền); **nét đứt là ước
  tính** (tin, chính sách, rủi ro: “có thể ảnh hưởng”); **chấm chấm là giả định** (kịch bản, nhãn “giả định”, “nếu
  xảy ra”). Ước tính và giả định không bao giờ được cộng vào tài sản ròng. Chú thích ở góc đồ thị nhắc lại ba loại.
- **Bấm một nút hoặc một đường** để xem ở ô Thông tin: số tiền, mỗi tháng, mức chắc chắn, từ bản ghi nào. Trong góc
  nhìn Tài sản, chọn một lớp tài sản để mở các khoản của nó.
- **Kịch bản**: bật ở góc nhìn Mục tiêu & kịch bản. Kịch bản đang bật có một đường giả định về phía bạn; chọn nó để
  thấy nó chạm tới lớp tài sản và mục tiêu nào. Bật kịch bản không đổi số liệu đã lưu.
- **Trợ lý** (thẻ Trợ lý cạnh ô Thông tin) biết bạn đang ở góc nhìn nào và đang chọn gì: hỏi “mục này là gì?” là hỏi
  về mục đang chọn. Các mục trợ lý đang đọc sáng lên trên đồ thị.
- **Ô Thông tin khi chưa chọn gì**: ở Tổng quan là **Điều đáng chú ý** (tin, mục tiêu, ngưỡng và thay đổi có thể ảnh
  hưởng tới bạn, quan trọng trước, kèm lý do và nguồn); ở các góc nhìn khác là danh sách các mục của góc nhìn đó.
- **Trang của góc nhìn**: dưới tiêu đề là nút mở các trang riêng (Tài sản, Kế hoạch, Khẩu vị rủi ro, Tác động thị
  trường, Đồ thị tác động, Chi phí chính sách) và nút mở phần số liệu của góc nhìn trong Bảng số liệu. Trang riêng mở
  thành một tấm phủ trên đồ thị; đóng lại thì đồ thị vẫn như cũ.
- **Cách xem**: Đồ thị, Danh sách, hoặc **Bảng số liệu** (xem dưới).
- **Tổng quan nhanh** (dải thẻ dưới đồ thị): tài sản ròng, dòng tiền tháng, phân bổ, rủi ro, thanh khoản dự phòng. Bấm
  một thẻ để mở góc nhìn của nó, ngay tại phần số liệu đó trong Bảng số liệu.

## Bảng số liệu — #/client/tong-quan/chi-tiet

Nút **Bảng số liệu** ở Cách xem. Mọi con số ở một chỗ, thay cho hai trang Toàn cảnh và Chi tiết trước đây (địa
chỉ cũ `#/client/tong-quan/toan-canh` và `#/client/tong-quan/chi-tiet` mở bảng này). Theo thứ tự:

- **Dòng tiền**: 6 tháng qua và dự báo 12/24/36 tháng, các khoản phải trả lớn và các khoản định kỳ tìm thấy trong giao
  dịch.
- **Phân bổ tài sản** với lãi / lỗ từng nhóm so với giá vốn, và **lãi / lỗ danh mục** (đã chốt, chưa chốt, lợi nhuận
  từ đầu năm so với VN-Index).
- **Tiền vào và ra trong tháng**: chọn tháng; biểu đồ dòng chảy từ nguồn tiền vào (lương, cổ tức…) sang các nhóm chi và
  phần còn lại; ba tỷ lệ (tỷ lệ để dành, tiền ra trên tiền vào, nhóm chi lớn nhất) và bảng chi tiết. Bấm một dải để
  xem các giao dịch tạo nên nó. Tháng không có giao dịch hiện “Không có giao dịch trong tháng này.”
- **Tài sản ròng** (tài sản, nợ, ngày số liệu, các thành viên được tính) và tài sản theo nguồn dữ liệu.
- **Rủi ro**: mức sụt giảm chấp nhận so với ước tính khi căng thẳng, cảnh báo tập trung.
- **Thanh khoản dự phòng** (quỹ khẩn cấp): tiền và tài sản rút được ngay, đủ chi bao nhiêu tháng so với mốc an toàn 6
  tháng.
- **Chính sách và dự án** nổi bật. Chưa làm bài kiểm tra rủi ro thì ngưỡng lấy theo hồ sơ.

Mục tiêu đang theo dõi ở góc nhìn Mục tiêu & kịch bản và trang Kế hoạch.

## Bản đồ tài chính — #/client/tong-quan/ban-do

Bức tranh toàn bộ dưới dạng đồ thị: bạn ở giữa, xung quanh là tài sản, nguồn dữ liệu, mục tiêu, rủi ro, chính sách và
tin tức. Bật tắt từng loại bằng các nút phía trên (nguồn dữ liệu và chính sách tắt sẵn). Bấm một nút để xem số liệu và
các liên kết của nó; nhóm tài sản mở ra các khoản bằng nhấp đúp hoặc “Mở rộng”. Đường nét đứt là tin “có thể ảnh
hưởng”. **Mở trang** đưa tới trang chi tiết. Trên điện thoại trang mở ở dạng danh sách.

## Tài sản — #/client/tai-san

Mọi tài sản và khoản nợ, nhóm theo loại, mỗi khoản có nguồn và mức tin cậy: **Đã xác thực** (từ ngân hàng), **Từ sao
kê**, **Bạn tự khai**; ngày và giá mua, giá vốn, giá trị hiện tại, lãi / lỗ; cuối bảng là tổng tài sản, nợ và tài sản
ròng.

- **Tải sao kê**: chọn tệp PDF, Excel hoặc CSV của công ty chứng khoán hay ngân hàng khác (hoặc dùng sao kê mẫu); các
  khoản đọc được hiện với nhãn “Từ sao kê”.
- **Bổ sung tài sản**: gõ một câu như “Tôi có căn hộ ở Thủ Đức khoảng 5 tỷ”; ứng dụng trả lời đã ghi gì và bảng có thêm
  dòng.

## Kế hoạch — #/client/muc-tieu/ke-hoach

Cố vấn kế hoạch tài sản: các chỉ số tổng (tài sản ròng, lãi / lỗ danh mục, mục tiêu đã đủ tiền, dòng tiền ròng 12
tháng), số cần so với số có cho từng mục tiêu và số tiền cần để dành mỗi tháng.

- **Mục tiêu cuộc sống**: nhóm theo gia đình và con cái, tích lũy, hưu trí và chuyển giao, quỹ dự phòng, quyết định và
  kịch bản căng thẳng. Chọn một mục để xem trạng thái (cần / có / thiếu), theo dõi so với dự kiến, **Việc cần làm** xếp
  theo thứ tự, **Chi tiết tính toán** (sửa giả định rồi **Chạy lại**, bảng trước / sau) và phương án nhẹ / mạnh.
- **Gửi chuyên gia duyệt**: gửi một việc hay phương án tới RM; theo dõi ở trang Chuyên gia.
- **Lưu ý quy định cho mục tiêu**: quy định mới có liên quan tới mục tiêu của bạn, mức độ và mốc cần chuẩn bị.

## Khẩu vị rủi ro — #/client/muc-tieu/khau-vi

Bài kiểm tra khẩu vị rủi ro: bấm “Bắt đầu”, trả lời 8–12 câu tình huống (câu sau tùy câu trước, có thanh tiến độ và
nút “← Câu trước”). Kết quả: mức chịu đựng rủi ro và khả năng chịu rủi ro trên năm mức, câu giải thích khi hai mức
khác nhau, hình mẫu nhà đầu tư và ngưỡng sụt giảm mới — ngưỡng này được dùng ở phần Rủi ro của Bảng số liệu.

## Tác động thị trường — #/client/tin/thi-truong

Sau khi CIO duyệt một nhận định về tin thị trường và hậu kiểm đạt, trang này cho biết tài sản của bạn có thể thay đổi
bao nhiêu trong 3 tháng tới, dải dao động rộng hay hẹp và đến từ đâu — theo nhóm tài sản, không nêu mã cổ phiếu, không
phải khuyến nghị.

- **Con số chính**: mức thay đổi kỳ vọng 3 tháng, phần trăm tài sản ròng, công thức bằng lời, ngày giá, người duyệt.
- **Dải kết quả có thể**: đường kỳ vọng và dải P10–P90 ở 1 tuần, 3 tháng, 12 tháng.
- **Đến từ đâu**: đóng góp theo nhóm tài sản.
- **Sự kiện**: từng sự kiện đang hiệu lực theo loại, thay đổi 3 tháng; **Xem dải** để vẽ dải của sự kiện đó; **Cách
  tính** mở cách ra con số; **Dòng thời gian**: từ tin đầu tiên tới lúc có hiệu lực.
- **Lưu ý cho mục tiêu của bạn**: tác động 3 tháng lên từng mục tiêu (VND, P10, P90) và việc nên chuẩn bị trước hạn.

Chưa có tin nào được duyệt thì trang báo tác động sẽ hiện khi có.

## Đồ thị tác động — #/client/tin/do-thi

Tin nào chạm tới tiền của bạn, qua đường nào, tới mục tiêu nào — đọc từ trái sang phải qua bảy cột: Tin, Sự kiện,
Kịch bản, Yếu tố, Tài sản, Gia đình, Mục tiêu. Bấm một nút để làm sáng đường đi của nó; bấm lần nữa hoặc “Bỏ chọn” để
bỏ. Chọn một sự kiện mở bảng tác động: hướng, kịch bản chính, các nhóm tài sản và mục tiêu trước → sau. Có nút chuyển
“Đồ thị / Danh sách” và bộ lọc theo loại.

## Chi phí chính sách — #/client/tin/chinh-sach

Chính sách (lãi suất, thuế, quy định…) có thể làm bạn mất hay được bao nhiêu: **Tác động lên tài sản ròng** theo từng
chính sách (lọc tất cả / rủi ro / cơ hội), nhận định của các nhà nghiên cứu khớp với tài sản của bạn (dữ liệu giả
định), và từng thẻ chính sách: mức độ, tình trạng pháp lý, tác động có xác suất, cách tính (giá trị × độ nhạy × xác
suất) và nguồn.

## Chuyên gia — #/client/chuyen-gia

Chuyên viên quan hệ khách hàng của bạn (tên, liên hệ — dữ liệu demo) và **Hàng chờ chuyên gia duyệt**: các phương án
bạn đã gửi từ Kế hoạch, đang chờ hay đã được duyệt / từ chối kèm ghi chú. Trang này chỉ để xem; RM và chuyên gia quyết
định ở trang của họ.
