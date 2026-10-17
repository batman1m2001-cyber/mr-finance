# nav-03 — “Nút này nghĩa là gì?” với một mục tiêu đang chọn

Category: navigation · persona: đang xem đồ thị, chọn một mục tiêu (C01) · BRD: OWN-GW-47, OWN-GW-45, KIT-COPILOT-01

The person picks a goal node and asks about “this”: the selection must reach the answer.

## Turn 1

**Người dùng:** Nút này nói gì vậy?

*Đồ thị:* `{"lens": "muc-tieu", "selected": {"id": "GL:tuition", "kind": "goal", "label": "Học phí cho con (trong nước / du học)"}}`

*Công cụ:* lien_ket · *trạng thái:* ok · *chế độ:* model · 4.2 s · US$0.00168

**Trợ lý:**

Mục đang chọn là mục tiêu **“Học phí cho con (trong nước / du học)”**. Nó nối với bạn và cho biết bạn **cần để dành khoảng 79,1 triệu đồng mỗi tháng** cho mục tiêu này.

Đây là **số ước tính**, không phải số thực tế đã ghi nhận, nên không cộng vào tài sản ròng. Số liệu tính theo ngày 09/10/2026, lấy từ đồ thị tài chính.

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Sao nó lại ghi là chậm tiến độ?

*Đồ thị:* `{"lens": "muc-tieu", "selected": {"id": "GL:tuition", "kind": "goal", "label": "Học phí cho con (trong nước / du học)"}}`

*Công cụ:* muc_tieu · *trạng thái:* ok · *chế độ:* model · 5.4 s · US$0.00201

**Trợ lý:**

Mục này ghi **chậm tiến độ** vì khoản tiền hiện có chưa đủ cho mục tiêu, và dòng tiền hằng tháng không đủ để bù phần thiếu:

- **Cần:** 7,56 tỷ đồng vào năm 2030.
- **Có:** 4,03 tỷ đồng, là thanh khoản ngoài quỹ dự phòng 6 tháng chi tiêu.
- **Thiếu:** 3,53 tỷ đồng.
- **Cần để dành:** khoảng 79,1 triệu đồng mỗi tháng.
- **Dòng tiền dư thực tế:** khoảng 5,0 triệu đồng mỗi tháng.

Vì dòng tiền dư chỉ 5,0 triệu, thấp hơn nhiều so với 79,1 triệu cần để dành, hệ thống đánh dấu mục này chậm tiến độ. Số 79,1 triệu là ước tính. Số liệu lấy từ trang Mục tiêu theo hồ sơ hiện tại, ngày 09/10/2026.

**Kiểm tra:** đạt
