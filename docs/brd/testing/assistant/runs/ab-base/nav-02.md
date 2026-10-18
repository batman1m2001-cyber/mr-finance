# nav-02 — Tài sản ròng tính thế nào, từ nguồn nào, mới đến đâu

Category: navigation · persona: chuyên gia, hỏi sâu (C01) · BRD: OWN-AS-02, KIT-COPILOT-02, KIT-COPILOT-05

An expert challenges the headline figure: the formula, its sources, its date.

## Turn 1

**Người dùng:** Con số tài sản ròng của tôi được tính như thế nào?

*Công cụ:* tong_quan, huong_dan · *trạng thái:* ok · *chế độ:* model · 5.2 s · US$0.00203

**Trợ lý:**

Tài sản ròng là tổng giá trị tài sản trừ đi tổng nợ, theo giá ngày định giá.

Theo dữ liệu ngày 09/10/2026:
- Tổng tài sản: 45,97 tỷ
- Tổng nợ: 2,44 tỷ (vay mua nhà Thảo Điền 2,40 tỷ; dư nợ thẻ Visa Signature 45,0 triệu)
- **Tài sản ròng = 45,97 − 2,44 = 43,53 tỷ**

Số này tổng hợp 21 khoản từ 7 nguồn, gồm tài khoản ngân hàng, sổ giao dịch chứng khoán, chứng chỉ quỹ, định giá nhà đất, và các khoản bạn tự khai (như vàng, đất ngoài hệ thống, bảo hiểm). Đây là số ghi nhận trong hệ thống, nên các khoản bạn tự khai sẽ không tự cập nhật nếu giá thay đổi.

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Những nguồn dữ liệu nào tạo nên con số đó?

*Công cụ:* — · *trạng thái:* ok · *chế độ:* model · 3.2 s · US$0.00133

**Trợ lý:**

Con số 43,53 tỷ được tổng hợp từ 21 khoản, lấy từ 7 nguồn (số liệu ngày 09/10/2026):

- **Techcombank** (4 khoản): tiền gửi, thẻ, khoản vay, giao dịch
- **TCBS** (6 khoản): cổ phiếu, trái phiếu, lãi lỗ
- **Techcom Capital** (2 khoản): chứng chỉ quỹ
- **OneHousing** (1 khoản): định giá bất động sản
- **Open API** (1 khoản): số dư và danh mục tại ngân hàng hoặc công ty chứng khoán khác
- **Sao kê tải lên** (3 khoản): đọc từ file sao kê PDF hoặc Excel
- **Bạn tự khai** (4 khoản): vàng, bất động sản ngoài hệ thống, cổ phần, bảo hiểm

Các khoản bạn tự khai không được hệ thống tự cập nhật giá, nên nên kiểm tra lại định kỳ.

**Kiểm tra:** đạt

## Turn 3

**Người dùng:** Dữ liệu này cập nhật lần cuối khi nào?

*Công cụ:* — · *trạng thái:* ok · *chế độ:* model · 2.7 s · US$0.00123

**Trợ lý:**

Dữ liệu tổng quan được ghi nhận đến ngày **09/10/2026**. Tuy nhiên, hệ thống chỉ cho tôi biết ngày định giá, không có thời điểm đồng bộ gần nhất của từng nguồn. Vì vậy tôi chưa thể xác nhận các nguồn được cập nhật lúc nào.

Các khoản bạn tự khai (vàng, bất động sản ngoài hệ thống, cổ phần, bảo hiểm) sẽ giữ nguyên giá trị đã nhập cho đến khi bạn sửa.

**Kiểm tra:** đạt
