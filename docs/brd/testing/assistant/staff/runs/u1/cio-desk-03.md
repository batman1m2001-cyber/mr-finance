# cio-desk-03 — Lần áp dụng và độ chính xác

Category: desk · persona: CIO kiểm tra mô hình · BRD: OWN-MR-01, BRD-FR-503

The apply runs (in force, waiting) and the model's accuracy, each from its tool.

## Turn 1

**Người dùng:** Lần áp dụng nào đang hiệu lực?

*Công cụ:* lan_ap_dung · *trạng thái:* ok · *chế độ:* model · 3.6 s · US$0.00136

**Trợ lý:**

Hiện có 2 lần áp dụng đang hiệu lực (nguồn: trang Áp dụng, số ghi nhận hệ thống):

1. **AR-0001-v1-2**: kỳ vọng 3 tháng **−628,1 triệu**, 5 gia đình, 1 gia đình chạm ngưỡng.
2. **AR-0002-v1-2**: kỳ vọng 3 tháng **+421,9 triệu**, 5 gia đình, 1 gia đình chạm ngưỡng.

Hai lần đã được thay thế là AR-0001-v1-1 và AR-0002-v1-1.

Đây là số ghi nhận từ hệ thống, không phải dự báo chắc chắn. Nếu cần xem phơi nhiễm theo từng gia đình, tôi có thể lấy thêm.

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Mô hình dự báo đúng tới đâu?

*Công cụ:* do_chinh_xac · *trạng thái:* ok · *chế độ:* model · 5.9 s · US$0.00153

**Trợ lý:**

Theo trang Độ chính xác (số ghi nhận đến 17/10/2026), mô hình chạy lại trên lịch sử từ 31/01/2022 đến 17/10/2026:

- **Dải P10–P90** (tỷ lệ biến động thực nằm trong dải):
  - 1 tuần: 72% (đạt)
  - 3 tháng: 77% (đạt)
  - 12 tháng: 75% (đạt)
- **Hướng VN-Index so với mục tiêu 70%**:
  - 1 tuần: 57% trên 245 lần (**chưa đạt**)
  - 3 tháng: 72% trên 54 lần (đạt)
  - 12 tháng: 96% trên 45 lần (đạt)
- **Dự báo đã duyệt**: 90 dự báo, tất cả đang chờ đến hạn chấm. Hạn gần nhất là 22/10/2026.

Độ chính xác dự báo 1 tuần còn thấp. Các số này là kết quả trên lịch sử, không bảo đảm cho tương lai.

**Kiểm tra:** đạt
