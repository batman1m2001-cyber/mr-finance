# nav-03 — “Nút này nghĩa là gì?” với một mục tiêu đang chọn

Category: navigation · persona: đang xem đồ thị, chọn một mục tiêu (C01) · BRD: OWN-GW-47, OWN-GW-45, KIT-COPILOT-01

The person picks a goal node and asks about “this”: the selection must reach the answer.

## Turn 1

**Người dùng:** Nút này nói gì vậy?

*Đồ thị:* `{"lens": "muc-tieu", "selected": {"id": "GL:tuition", "kind": "goal", "label": "Học phí cho con (trong nước / du học)"}}`

*Công cụ:* lien_ket · *trạng thái:* ok · *chế độ:* model · 4.7 s · US$0.00145

**Trợ lý:**

Mục đang chọn là **Học phí cho con (trong nước / du học)**. Nút này cho biết mục tiêu này cần để dành khoảng **79,1 triệu đồng mỗi tháng**.

- **Mức chắc chắn:** đây là **ước tính**, không phải số thực tế. Ước tính và giả định không được cộng vào tài sản ròng.
- **Liên kết:** mục tiêu nối với "Bạn" ở chiều cần để dành mỗi tháng, dựa trên 1 bản ghi.
- **Ngày dữ liệu:** 09/10/2026, lấy từ đồ thị tài chính.

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Sao nó lại ghi là chậm tiến độ?

*Đồ thị:* `{"lens": "muc-tieu", "selected": {"id": "GL:tuition", "kind": "goal", "label": "Học phí cho con (trong nước / du học)"}}`

*Công cụ:* lien_ket, muc_tieu, chu_y · *trạng thái:* ok · *chế độ:* model · 9.3 s · US$0.00254

**Trợ lý:**

Công cụ không nêu rõ lý do mục này bị ghi "chậm tiến độ". Tôi chỉ biết trạng thái này được tính trên tài sản hiện có, không phải trên dòng tiền dự kiến.

Những gì tôi xác nhận được:
- **Mục tiêu:** Học phí cho con (trong nước / du học) đang ở trạng thái "chậm tiến độ". Trong 4 mục tiêu đang theo dõi, mục này và "Định cư / con đi du học" là hai mục chậm tiến độ. Hai mục còn lại đúng tiến độ.
- **Con số cần để dành:** khoảng 79,1 triệu đồng/tháng, là ước tính, không phải số thực tế.
- **Một điều đáng chú ý trên bảng tin:** mức sụt giảm ước tính khi thị trường xấu là 11,8%, vượt ngưỡng chấp nhận 8%. Tôi chưa có dữ liệu xác nhận đây là nguyên nhân khiến mục học phí chậm tiến độ.

Để xem chi tiết so sánh tài sản hiện có với mục tiêu, bạn có thể mở trang **Kế hoạch** (mục tiêu và tiến độ). Tôi cũng có thể mở trang đó cho bạn.

**Kiểm tra:** đạt
