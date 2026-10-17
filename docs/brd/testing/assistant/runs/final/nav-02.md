# nav-02 — Tài sản ròng tính thế nào, từ nguồn nào, mới đến đâu

Category: navigation · persona: chuyên gia, hỏi sâu (C01) · BRD: OWN-AS-02, KIT-COPILOT-02, KIT-COPILOT-05

An expert challenges the headline figure: the formula, its sources, its date.

## Turn 1

**Người dùng:** Con số tài sản ròng của tôi được tính như thế nào?

*Công cụ:* tong_quan, huong_dan · *trạng thái:* ok · *chế độ:* model · 4.7 s · US$0.00207

**Trợ lý:**

Tài sản ròng của bạn là **43,53 tỷ đồng**, tính theo công thức:

**Tài sản ròng = tổng tài sản − tổng nợ**
= 45,97 tỷ − 2,44 tỷ = **43,53 tỷ**

- **Tổng tài sản (45,97 tỷ):** gồm 21 khoản, lấy từ ngân hàng, công ty chứng khoán, công ty quản lý quỹ, dịch vụ định giá nhà đất, sao kê bạn tải lên và các khoản bạn tự khai (vàng, bất động sản ngoài hệ thống, cổ phần, bảo hiểm).
- **Nợ (2,44 tỷ):** khoản vay mua nhà Thảo Điền 2,40 tỷ và dư nợ thẻ Visa Signature 45,0 triệu.

Số liệu tính đến ngày 09/10/2026, lấy từ trang Tổng quan. Đây là số ghi nhận trong hệ thống, tính theo giá ngày định giá. So với tháng trước, tài sản ròng tăng 980,5 triệu (2,3%).

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Những nguồn dữ liệu nào tạo nên con số đó?

*Công cụ:* — · *trạng thái:* ok · *chế độ:* model · 3.1 s · US$0.00127

**Trợ lý:**

Con số 43,53 tỷ được tổng hợp từ **21 khoản** lấy từ **7 nguồn**:

- **Techcombank (4 khoản):** tiền gửi, thẻ, khoản vay, giao dịch.
- **TCBS (6 khoản):** cổ phiếu, trái phiếu, lãi lỗ.
- **Techcom Capital (2 khoản):** chứng chỉ quỹ.
- **OneHousing (1 khoản):** định giá bất động sản.
- **Open API (1 khoản):** số dư và danh mục từ ngân hàng hoặc công ty chứng khoán khác.
- **Sao kê tải lên (3 khoản):** đọc từ file PDF hoặc Excel bạn đã tải lên.
- **Bạn tự khai (4 khoản):** vàng, bất động sản ngoài hệ thống, cổ phần, bảo hiểm.

Số liệu tính đến 09/10/2026. Các khoản bạn tự khai không được hệ thống xác minh, nên nếu giá trị đã cũ thì tài sản ròng cũng sẽ lệch theo.

**Kiểm tra:** đạt

## Turn 3

**Người dùng:** Dữ liệu này cập nhật lần cuối khi nào?

*Công cụ:* huong_dan · *trạng thái:* ok · *chế độ:* model · 5.5 s · US$0.00266

**Trợ lý:**

Hệ thống chỉ cho tôi biết **ngày số liệu là 09/10/2026**, theo trang Tổng quan. Tôi chưa có thời điểm đồng bộ cụ thể của từng nguồn (Techcombank, TCBS, Techcom Capital, OneHousing, Open API hay sao kê), nên không xác định được chính xác lần cập nhật cuối.

Mức độ tin cậy của từng khoản được ghi trên trang Tài sản:
- **Đã xác thực (từ ngân hàng):** lấy trực tiếp từ hệ thống kết nối.
- **Từ sao kê:** phụ thuộc vào file bạn đã tải lên, nên sẽ cũ dần nếu bạn không tải file mới.
- **Bạn tự khai:** cần bạn tự cập nhật giá trị.

Để xem ngày cập nhật của từng khoản, bạn mở trang Tài sản.

**Kiểm tra:** đạt
