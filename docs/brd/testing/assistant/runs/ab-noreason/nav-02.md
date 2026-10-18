# nav-02 — Tài sản ròng tính thế nào, từ nguồn nào, mới đến đâu

Category: navigation · persona: chuyên gia, hỏi sâu (C01) · BRD: OWN-AS-02, KIT-COPILOT-02, KIT-COPILOT-05

An expert challenges the headline figure: the formula, its sources, its date.

## Turn 1

**Người dùng:** Con số tài sản ròng của tôi được tính như thế nào?

*Công cụ:* tong_quan, huong_dan · *trạng thái:* ok · *chế độ:* model · 4.8 s · US$0.00200

**Trợ lý:**

Tài sản ròng được tính theo công thức: **tổng giá trị tài sản − tổng nợ**, theo giá ngày định giá.

Với số liệu ngày 09/10/2026 (lấy từ trang Tổng quan):
- Tổng tài sản: 45,97 tỷ
- Tổng nợ: 2,44 tỷ (vay mua nhà Thảo Điền 2,40 tỷ; dư nợ thẻ Visa 45,0 triệu)
- **Tài sản ròng: 43,53 tỷ** (45,97 − 2,44)

Số này được tổng hợp từ 21 khoản thuộc 7 nguồn: Techcombank, TCBS, Techcom Capital, OneHousing, tài khoản ngân hàng/CTCK khác qua Open API, sao kê bạn tải lên, và các khoản bạn tự khai (vàng, bất động sản ngoài hệ thống, cổ phần, bảo hiểm). Các khoản tự khai chưa được đối chiếu với nguồn bên ngoài, nên giá trị của chúng là do bạn nhập.

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Những nguồn dữ liệu nào tạo nên con số đó?

*Công cụ:* — · *trạng thái:* ok · *chế độ:* model · 2.5 s · US$0.00124

**Trợ lý:**

Con số 43,53 tỷ được tổng hợp từ 21 khoản thuộc 7 nguồn:

- **Techcombank** (4 khoản): tiền gửi, thẻ, khoản vay, giao dịch
- **TCBS** (6 khoản): cổ phiếu, trái phiếu, lãi lỗ
- **Techcom Capital** (2 khoản): chứng chỉ quỹ
- **OneHousing** (1 khoản): định giá bất động sản
- **Open API** (1 khoản): số dư và danh mục từ ngân hàng/công ty chứng khoán khác
- **Sao kê tải lên** (3 khoản): đọc từ file sao kê PDF/Excel bạn đã tải lên
- **Bạn tự khai** (4 khoản): vàng, bất động sản ngoài hệ thống, cổ phần, bảo hiểm

Số liệu này có ngày định giá 09/10/2026. Các khoản tự khai do bạn nhập nên chưa được đối chiếu với nguồn bên ngoài. Nếu muốn xem chi tiết từng khoản, bạn có thể mở trang Tài sản.

**Kiểm tra:** đạt

## Turn 3

**Người dùng:** Dữ liệu này cập nhật lần cuối khi nào?

*Công cụ:* — · *trạng thái:* ok · *chế độ:* model · 2.0 s · US$0.00118

**Trợ lý:**

Dữ liệu tổng quan có ngày định giá (as_of) là **09/10/2026**. Tuy nhiên, công cụ tổng quan không cung cấp thông tin về thời điểm đồng bộ lần cuối của từng nguồn (Techcombank, TCBS, OneHousing, v.v.), nên tôi không xác định được chính xác lúc nào mỗi nguồn được cập nhật. Nếu cần, bạn có thể kiểm tra trong phần thiết lập kết nối của từng nguồn hoặc nhờ đội hỗ trợ kiểm tra thêm.

**Kiểm tra:** đạt
