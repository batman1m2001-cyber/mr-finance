# nav-03 — “Nút này nghĩa là gì?” với một mục tiêu đang chọn

Category: navigation · persona: đang xem đồ thị, chọn một mục tiêu (C01) · BRD: OWN-GW-47, OWN-GW-45, KIT-COPILOT-01

The person picks a goal node and asks about “this”: the selection must reach the answer.

## Turn 1

**Người dùng:** Nút này nói gì vậy?

*Đồ thị:* `{"lens": "muc-tieu", "selected": {"id": "GL:tuition", "kind": "goal", "label": "Học phí cho con (trong nước / du học)"}}`

*Công cụ:* lien_ket · *trạng thái:* ok · *chế độ:* model · 3.7 s · US$0.00174

**Trợ lý:**

Nút "Học phí cho con (trong nước / du học)" đang nối với một mục là **Bạn**, với nội dung: **cần để dành khoảng 79,1 triệu đồng mỗi tháng**.

Đây là **ước tính**, không phải số thực tế, nên không được cộng vào tài sản ròng. Số liệu lấy từ đồ thị tài chính, ngày 09/10/2026.

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Sao nó lại ghi là chậm tiến độ?

*Đồ thị:* `{"lens": "muc-tieu", "selected": {"id": "GL:tuition", "kind": "goal", "label": "Học phí cho con (trong nước / du học)"}}`

*Công cụ:* muc_tieu · *trạng thái:* ok · *chế độ:* model · 4.3 s · US$0.00200

**Trợ lý:**

Mục này được ghi "chậm tiến độ" vì số tiền hiện có chưa đủ so với mục tiêu:

- **Cần:** 7,56 tỷ đồng vào năm 2030
- **Có:** 4,03 tỷ đồng (phần thanh khoản ngoài 6 tháng chi tiêu)
- **Thiếu:** 3,53 tỷ đồng
- **Cần để dành:** khoảng 79,1 triệu đồng/tháng, trong khi dòng tiền dư hiện chỉ khoảng 5,0 triệu đồng/tháng

Số liệu đọc từ hệ thống là số ghi nhận, lấy từ trang Mục tiêu, ngày 09/10/2026. Mức cần để dành/tháng là ước tính.

**Kiểm tra:** đạt
