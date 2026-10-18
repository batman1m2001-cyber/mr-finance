# cio-desk-03 — Lần áp dụng và độ chính xác

Category: desk · persona: CIO kiểm tra mô hình · BRD: OWN-MR-01, BRD-FR-503

The apply runs (in force, waiting) and the model's accuracy, each from its tool.

## Turn 1

**Người dùng:** Lần áp dụng nào đang hiệu lực?

*Công cụ:* lan_ap_dung · *trạng thái:* ok · *chế độ:* model · 3.2 s · US$0.00148

**Trợ lý:**

Hiện có 2 lần áp dụng đang hiệu lực (theo trang Áp dụng):

- **AR-0001-v1-2**: kỳ vọng 3 tháng −628,1 triệu, 5 gia đình, 1 gia đình chạm ngưỡng.
- **AR-0002-v1-2**: kỳ vọng 3 tháng +421,9 triệu, 5 gia đình, 1 gia đình chạm ngưỡng.

Hai lần trước đó (AR-0001-v1-1 và AR-0002-v1-1) đã được thay thế.

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Mô hình dự báo đúng tới đâu?

*Công cụ:* do_chinh_xac · *trạng thái:* ok · *chế độ:* model · 6.0 s · US$0.00166

**Trợ lý:**

Theo trang Độ chính xác (số liệu đến 17/10/2026, lịch sử từ 31/01/2022):

- **Dải dự báo P10–P90** (tỷ lệ biến động thực nằm trong dải): 1 tuần 72%, 3 tháng 77%, 12 tháng 75%. Cả ba đều đạt.
- **Hướng VN-Index so với mục tiêu 70%**:
  - 1 tuần: 57% trên 245 lần, **chưa đạt**.
  - 3 tháng: 72% trên 54 lần, đạt.
  - 12 tháng: 96% trên 45 lần, đạt.
- **Dự báo đã duyệt**: 90 dự báo đang chờ đến hạn chấm, hạn gần nhất 22/10/2026.

Số liệu này là kết quả chạy lại trên lịch sử, không phải bảo đảm cho dự báo sắp tới.

**Kiểm tra:** đạt
