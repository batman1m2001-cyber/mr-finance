# nav-03 — “Nút này nghĩa là gì?” với một mục tiêu đang chọn

Category: navigation · persona: đang xem đồ thị, chọn một mục tiêu (C01) · BRD: OWN-GW-47, OWN-GW-45, KIT-COPILOT-01

The person picks a goal node and asks about “this”: the selection must reach the answer.

## Turn 1

**Người dùng:** Nút này nói gì vậy?

*Đồ thị:* `{"lens": "muc-tieu", "selected": {"id": "GL:tuition", "kind": "goal", "label": "Học phí cho con (trong nước / du học)"}}`

*Công cụ:* huong_dan · *trạng thái:* ok · *chế độ:* model · 8.7 s · US$0.00164

**Trợ lý:**

Bạn đang ở trang Tổng quan, nhưng tôi chưa biết bạn đang nhắc đến nút nào. Hướng dẫn sử dụng nói chung như sau:

- **Nút "Cách tính"** hoặc **con số có gạch chân**: mở ngăn bên phải, giải thích con số là gì, công thức, các đầu vào và giá trị của chúng. Phần nào là giả định thì được ghi rõ.
- **Nút ✦**: mở khung trợ lý để hỏi bằng tiếng Việt về số liệu của bạn hoặc cách dùng ứng dụng.
- **Nút Xác nhận / Huỷ**: xuất hiện trước khi có thao tác ghi dữ liệu, như lưu mục tiêu hay gửi đề xuất. Nếu không xác nhận thì không có gì được ghi.

Bạn có thể cho tôi biết chữ trên nút hoặc vị trí của nó trên màn hình không? Tôi sẽ giải thích cụ thể hơn.

**Kiểm tra:** called none of ['lien_ket', 'muc_tieu']; does not say /học phí/

## Turn 2

**Người dùng:** Sao nó lại ghi là chậm tiến độ?

*Đồ thị:* `{"lens": "muc-tieu", "selected": {"id": "GL:tuition", "kind": "goal", "label": "Học phí cho con (trong nước / du học)"}}`

*Công cụ:* huong_dan, muc_tieu, lien_ket · *trạng thái:* ok · *chế độ:* model · 8.6 s · US$0.00268

**Trợ lý:**

Mục "Học phí cho con (trong nước / du học)" được ghi là **chậm tiến độ** vì hệ thống tính mục này dựa trên tài sản hiện có của bạn, và hiện tài sản chưa đủ theo kế hoạch.

Theo đồ thị, mục này cần để dành khoảng **79,1 triệu đồng mỗi tháng**. Đây là con số ước tính, tính đến ngày 2026-10-09, từ mục tiêu trên đồ thị tài chính. Hệ thống không cho tôi thấy số tiền bạn đang để dành hằng tháng, nên tôi chưa thể nói chính xác khoảng cách là bao nhiêu.

Nếu muốn, tôi có thể xem trang Dòng tiền để biết số tiền còn lại mỗi tháng, hoặc trang Mục tiêu để xem chi tiết tiến độ.

**Kiểm tra:** đạt
