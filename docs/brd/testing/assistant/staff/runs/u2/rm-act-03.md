# rm-act-03 — Khuyến nghị cho C05, gia đình chưa có chuyên gia

Category: actions · persona: RM viết khuyến nghị (rm01) · BRD: BRD-RULE-CONTENT-01, BRD-RULE-WF-08, BRD-RULE-ROLE-05

An action recommendation goes to the family's certified specialist (CONTENT-01 flow 3); C05 has none, so the RM's own approval stands (WF-08 “if any”): read back approved, and the assistant says why when asked.

## Turn 1

**Người dùng:** Gửi khuyến nghị cho gia đình C05: tăng quỹ dự phòng lên sáu tháng chi tiêu và giảm nợ thẻ tín dụng.

*Công cụ:* — · *chờ xác nhận:* khuyen_nghi · *trạng thái:* pending · *chế độ:* model · 1.8 s · US$0.00098

**Trợ lý:**

Gửi khuyến nghị “Củng cố tài chính: quỹ dự phòng và nợ thẻ tín dụng” (2 việc) cho Vũ Ngọc Anh?

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Xác nhận

*Công cụ:* khuyen_nghi · *trạng thái:* ok · *chế độ:* model · 1.8 s · US$0.00198

**Trợ lý:**

Đã gửi khuyến nghị "Củng cố tài chính: quỹ dự phòng và nợ thẻ tín dụng" cho gia đình C05, gồm hai việc: tăng quỹ dự phòng lên sáu tháng chi tiêu và giảm nợ thẻ tín dụng. Khuyến nghị đã được duyệt (mã R-ca4853ab).

**Kiểm tra:** đạt

## Turn 3

**Người dùng:** Có chuyên gia nào phải duyệt khuyến nghị này không?

*Công cụ:* de_xuat, huong_dan · *trạng thái:* ok · *chế độ:* model · 7.4 s · US$0.00227

**Trợ lý:**

Tôi chưa xác định được gia đình C05 có chuyên gia có chứng chỉ được giao hay không, nên chưa thể khẳng định. Hướng dẫn cho biết: nếu có chuyên gia, việc RM đã duyệt còn phải chờ chuyên gia đó duyệt trước khi tới khách; nếu không có, RM duyệt là đủ.

Tuy nhiên, danh sách đề xuất ghi khuyến nghị này đã ở trạng thái "đã duyệt" và đã gửi cho khách. Nếu C05 có chuyên gia được giao, bạn nên kiểm tra lại với bộ phận quản lý vì khuyến nghị có thể đã đi qua mà chưa có bước duyệt của chuyên gia.

**Kiểm tra:** đạt
