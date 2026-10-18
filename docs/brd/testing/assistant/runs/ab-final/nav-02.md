# nav-02 — Tài sản ròng tính thế nào, từ nguồn nào, mới đến đâu

Category: navigation · persona: chuyên gia, hỏi sâu (C01) · BRD: OWN-AS-02, KIT-COPILOT-02, KIT-COPILOT-05

An expert challenges the headline figure: the formula, its sources, its date.

## Turn 1

**Người dùng:** Con số tài sản ròng của tôi được tính như thế nào?

*Công cụ:* tong_quan, huong_dan · *trạng thái:* ok · *chế độ:* model · 4.2 s · US$0.00203

**Trợ lý:**

Tài sản ròng của bạn là **43,53 tỷ đồng**, tính đến 09/10/2026.

**Công thức:** Tài sản ròng = tổng tài sản − tổng nợ
- Tổng tài sản: 45,97 tỷ
- Tổng nợ: 2,44 tỷ (vay mua nhà Thảo Điền 2,40 tỷ; dư nợ thẻ Visa 45,0 triệu)
- 45,97 − 2,44 = 43,53 tỷ

Con số này lấy từ 21 khoản tài sản trong 7 nguồn (Techcombank, TCBS, Techcom Capital, OneHousing, tài khoản ngân hàng khác, sao kê bạn tải lên, và các khoản bạn tự khai như vàng, bất động sản ngoài hệ thống, cổ phần, bảo hiểm). Các khoản tự khai chưa được hệ thống xác minh, nên có thể lệch so với thực tế.

Tháng này tài sản ròng tăng 980,5 triệu (2,3%).

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Những nguồn dữ liệu nào tạo nên con số đó?

*Công cụ:* — · *trạng thái:* ok · *chế độ:* model · 2.5 s · US$0.00127

**Trợ lý:**

Con số 43,53 tỷ đồng được tổng hợp từ 21 khoản tài sản thuộc 7 nguồn:

1. **Techcombank** (4 khoản): tiền gửi, thẻ, khoản vay, giao dịch.
2. **TCBS** (6 khoản): cổ phiếu, trái phiếu, lãi lỗ.
3. **Techcom Capital** (2 khoản): chứng chỉ quỹ.
4. **OneHousing** (1 khoản): định giá bất động sản.
5. **Open API** (1 khoản): số dư và danh mục tại ngân hàng hoặc công ty chứng khoán khác.
6. **Sao kê tải lên** (3 khoản): dữ liệu đọc từ file sao kê PDF và Excel bạn đã tải lên.
7. **Bạn tự khai** (4 khoản): vàng, bất động sản ngoài hệ thống, cổ phần, bảo hiểm.

Dữ liệu từ 6 nguồn đầu được hệ thống ghi nhận. Các khoản tự khai là do bạn nhập, nên chưa được đối chiếu với nguồn bên ngoài. Số liệu có hiệu lực đến ngày 09/10/2026.

**Kiểm tra:** đạt

## Turn 3

**Người dùng:** Dữ liệu này cập nhật lần cuối khi nào?

*Công cụ:* — · *trạng thái:* ok · *chế độ:* model · 1.9 s · US$0.00117

**Trợ lý:**

Dữ liệu tổng quan có hiệu lực đến ngày **09/10/2026**. Tôi chỉ có ngày định giá này, chưa có thời điểm đồng bộ cụ thể của từng nguồn. Nếu bạn cần biết nguồn nào đồng bộ gần nhất, hãy kiểm tra ở trang Tài sản, hoặc tôi có thể mở trang đó cho bạn.

**Kiểm tra:** đạt
