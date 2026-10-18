# rm-act-03 — Khuyến nghị cho C05, gia đình chưa có chuyên gia

Category: actions · persona: RM viết khuyến nghị (rm01) · BRD: BRD-RULE-CONTENT-01, BRD-RULE-WF-08, BRD-RULE-ROLE-05

An action recommendation goes to the family's certified specialist (CONTENT-01 flow 3); C05 has none, so the RM's own approval stands (WF-08 “if any”): read back approved, and the assistant says why when asked.

## Turn 1

**Người dùng:** Gửi khuyến nghị cho gia đình C05: tăng quỹ dự phòng lên sáu tháng chi tiêu và giảm nợ thẻ tín dụng.

*Công cụ:* so_khach_hang · *chờ xác nhận:* khuyen_nghi · *trạng thái:* pending · *chế độ:* model · 3.8 s · US$0.00198

**Trợ lý:**

Gửi khuyến nghị “Tăng quỹ dự phòng và giảm nợ thẻ tín dụng” (2 việc) cho Vũ Ngọc Anh?

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Xác nhận

*Công cụ:* khuyen_nghi · *trạng thái:* ok · *chế độ:* model · 1.8 s · US$0.00305

**Trợ lý:**

Đã gửi khuyến nghị "Tăng quỹ dự phòng và giảm nợ thẻ tín dụng" cho gia đình Vũ Ngọc Anh (C05). Khuyến nghị đã được duyệt và đã tới khách, vì gia đình này không có chuyên gia có chứng chỉ cần duyệt thêm.

Nội dung gồm hai việc:
- Tăng quỹ dự phòng lên sáu tháng chi tiêu.
- Giảm dần số dư nợ thẻ tín dụng.

**Kiểm tra:** đạt

## Turn 3

**Người dùng:** Có chuyên gia nào phải duyệt khuyến nghị này không?

*Công cụ:* — · *trạng thái:* ok · *chế độ:* model · 1.5 s · US$0.00106

**Trợ lý:**

Không. Kết quả gửi khuyến nghị ghi rõ gia đình Vũ Ngọc Anh (C05) chưa có chuyên gia có chứng chỉ được giao, nên RM duyệt là đủ. Khuyến nghị đã được duyệt và đã tới khách.

**Kiểm tra:** đạt
