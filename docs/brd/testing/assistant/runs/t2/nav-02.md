# nav-02 — Tài sản ròng tính thế nào, từ nguồn nào, mới đến đâu

Category: navigation · persona: chuyên gia, hỏi sâu (C01) · BRD: OWN-AS-02, KIT-COPILOT-02, KIT-COPILOT-05

An expert challenges the headline figure: the formula, its sources, its date.

## Turn 1

**Người dùng:** Con số tài sản ròng của tôi được tính như thế nào?

*Công cụ:* tong_quan, huong_dan · *trạng thái:* ok · *chế độ:* model · 4.9 s · US$0.00198

**Trợ lý:**

Tài sản ròng = tổng tài sản − tổng nợ, tính theo giá ngày định giá.

Theo số ghi nhận ngày 09/10/2026 trên trang Tổng quan:
- **Tổng tài sản:** 45,97 tỷ đồng
- **Tổng nợ:** 2,44 tỷ đồng (vay mua nhà Thảo Điền 2,40 tỷ và dư nợ thẻ Visa Signature 45,0 triệu)
- **Tài sản ròng:** 43,53 tỷ đồng (45,97 − 2,44), tăng 980,5 triệu so với tháng trước

Số này tổng hợp 21 khoản từ 7 nguồn: Techcombank, TCBS, Techcom Capital, OneHousing, tài khoản ngân hàng/CTCK khác qua Open API, sao kê bạn tải lên, và 4 khoản bạn tự khai (vàng, bất động sản ngoài hệ thống, cổ phần, bảo hiểm). Nếu một khoản thiếu hoặc sai giá trị, bạn có thể cập nhật lại để con số chính xác hơn.

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Những nguồn dữ liệu nào tạo nên con số đó?

*Công cụ:* — · *trạng thái:* ok · *chế độ:* model · 2.8 s · US$0.00122

**Trợ lý:**

Con số 43,53 tỷ đồng được tổng hợp từ 21 khoản, lấy từ 7 nguồn:

- **Techcombank** (4 khoản): tiền gửi, thẻ, khoản vay, giao dịch
- **TCBS** (6 khoản): cổ phiếu, trái phiếu, lãi lỗ
- **Techcom Capital** (2 khoản): chứng chỉ quỹ
- **OneHousing** (1 khoản): định giá bất động sản
- **Open API** (1 khoản): số dư và danh mục từ ngân hàng hoặc công ty chứng khoán khác
- **Sao kê tải lên** (3 khoản): đọc từ file PDF hoặc Excel bạn đã tải lên
- **Bạn tự khai** (4 khoản): vàng, bất động sản ngoài hệ thống, cổ phần, bảo hiểm

Đây là số ghi nhận tính đến ngày 09/10/2026. Nếu khoản tự khai chưa đúng giá trị hiện tại, con số tài sản ròng sẽ lệch theo.

**Kiểm tra:** called none of ['tong_quan', 'huong_dan', 'tim_kiem']

## Turn 3

**Người dùng:** Dữ liệu này cập nhật lần cuối khi nào?

*Công cụ:* — · *trạng thái:* ok · *chế độ:* model · 2.4 s · US$0.00117

**Trợ lý:**

Số liệu tổng quan có ngày ghi nhận là **09/10/2026**. Hệ thống không trả về giờ cập nhật cụ thể hay thời điểm đồng bộ của từng nguồn (Techcombank, TCBS, OneHousing…), nên tôi chưa thể xác nhận chính xác từng khoản được cập nhật khi nào.

Nếu cần kiểm tra độ mới của từng nguồn, bạn có thể mở trang Hệ thống để xem trạng thái kết nối. Tôi có thể mở trang đó cho bạn.

**Kiểm tra:** đạt
