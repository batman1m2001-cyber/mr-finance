<!-- What every role's catalog says before its tables (docs/ASSISTANT_DATA_PLAN.md §3.3). -->
Một câu SELECT (SQLite) trên các bảng dưới đây, và chỉ các bảng đó. Trả về tối đa 200 dòng, luôn kèm tổng số dòng.
- Giờ Việt Nam: hôm nay là `date('now', '+7 hours')`; 7 ngày gần nhất là `>= date('now', '+7 hours', '-6 days')`;
  tháng này là `substr(ngay, 1, 7) = strftime('%Y-%m', 'now', '+7 hours')`. So ngày bằng cột `ngay*` (YYYY-MM-DD),
  không bằng `luc*` (epoch giây).
- Tìm theo chữ: `khong_dau(tieu_de) like '%lai suat%'` (bỏ dấu và chữ hoa ở cả hai phía).
- Hỏi "bao nhiêu" thì đếm bằng `count(*)`, không liệt kê dòng rồi đếm. Liệt kê thì kèm `order by` và `limit`.
- Tiền là VND; tỷ lệ là số thập phân (0,15 là 15%).
