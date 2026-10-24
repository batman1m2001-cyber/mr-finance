<!-- The CIO's definitions and examples (docs/ASSISTANT_DATA_PLAN.md §3.3). Each "Hỏi:" is followed by its SQL;
tests/test_datacatalog.py runs every one in the CIO's room. -->
## Định nghĩa
- Tin lấy về hôm nay: `ngay_lay = date('now', '+7 hours')`, theo ngày hệ thống lấy về, không theo ngày báo đăng.
- Tin chờ xử lý (trang Hộp tin): `trang_thai = 'new'`. Đã gom vào sự kiện: `'grouped'`. CIO đã bỏ: `'dismissed'`.
- Tin đã lấy về (cả hộp tin): mọi dòng của `tin`, đếm theo `trang_thai`.
- Nhận định bị bác: `nhan_dinh.trang_thai = 'REJECTED'`; đã duyệt `'APPROVED'`; chờ duyệt `'PENDING_APPROVAL'`.
- Lần áp dụng đang dùng: `trang_thai = 'EFFECTIVE'` (ở `tac_dong_gia_dinh` là `trang_thai_lan`).
- Tác động lên một gia đình: `ky_vong_3thang` của lần áp dụng EFFECTIVE; lớn nhất là `abs(ky_vong_3thang)` lớn nhất.

## Ví dụ
Hỏi: Hệ thống đã lấy về bao nhiêu tin?
```sql
select trang_thai, count(*) as so_tin from tin group by trang_thai order by so_tin desc
```
Hỏi: Hôm nay lấy về bao nhiêu tin?
```sql
select count(*) as so_tin from tin where ngay_lay = date('now', '+7 hours')
```
Hỏi: Hôm nay lấy về bao nhiêu tin, theo từng báo?
```sql
select bao, count(*) as so_tin from tin where ngay_lay = date('now', '+7 hours') group by bao order by so_tin desc
```
Hỏi: Hộp tin còn bao nhiêu tin chờ xử lý?
```sql
select count(*) as so_tin from tin where trang_thai = 'new'
```
Hỏi: Mỗi ngày trong 7 ngày qua lấy về bao nhiêu tin?
```sql
select ngay_lay, count(*) as so_tin from tin where ngay_lay >= date('now', '+7 hours', '-6 days') group by ngay_lay order by ngay_lay
```
Hỏi: Tin nào về lãi suất tuần này?
```sql
select ngay_lay, bao, tieu_de from tin where khong_dau(tieu_de) like '%lai suat%' and ngay_lay >= date('now', '+7 hours', '-6 days') order by luc_lay desc limit 20
```
Hỏi: Tin liên quan cao đang chờ xử lý, theo loại sự kiện?
```sql
select coalesce(loai_su_kien, 'chưa xếp loại') as loai, count(*) as so_tin from tin where trang_thai = 'new' and muc_lien_quan = 'high' group by 1 order by so_tin desc
```
Hỏi: Bao nhiêu tin quốc tế và trong nước đang chờ?
```sql
select loai, count(*) as so_tin from tin where trang_thai = 'new' group by loai
```
Hỏi: Bao nhiêu nhận định bị bác trong tháng 10?
```sql
select count(*) as so_nhan_dinh from nhan_dinh where trang_thai = 'REJECTED' and substr(ngay_lap, 1, 7) = strftime('%Y', 'now', '+7 hours') || '-10'
```
Hỏi: Nhận định nào đang chờ duyệt?
```sql
select ma, ma_su_kien, ngay_lap, tom_tat from nhan_dinh where trang_thai = 'PENDING_APPROVAL' order by luc_lap desc
```
Hỏi: Sự kiện nào đang khẩn?
```sql
select ma, tieu_de, ngay_lap, so_tin from su_kien where khan = 1 order by luc_lap desc
```
Hỏi: Sự kiện nào gom nhiều tin nhất?
```sql
select ma, tieu_de, so_tin from su_kien order by so_tin desc limit 5
```
Hỏi: Gia đình nào chịu tác động nhiều nhất từ sự kiện EV-2026-0001?
```sql
select ten_gia_dinh, ky_vong_3thang, ty_le_3thang from tac_dong_gia_dinh where ma_su_kien = 'EV-2026-0001' and trang_thai_lan = 'EFFECTIVE' order by abs(ky_vong_3thang) desc limit 5
```
Hỏi: Gia đình nào chạm ngưỡng cần RM xem trước?
```sql
select ma_su_kien, ten_gia_dinh, p10_3thang from tac_dong_gia_dinh where cham_nguong = 1 and trang_thai_lan = 'EFFECTIVE'
```
Hỏi: Các đề xuất đang hiệu lực và tác động 3 tháng của từng đề xuất?
```sql
select ma, ma_su_kien, so_gia_dinh, ky_vong_3thang, so_cham_nguong from de_xuat where trang_thai = 'EFFECTIVE' order by luc_lap desc
```
Hỏi: Dự báo đã chấm trúng khoảng bao nhiêu phần trăm, theo yếu tố?
```sql
select yeu_to, count(*) as so_du_bao, round(100.0 * avg(trong_khoang), 1) as phan_tram_trung from du_bao where ket_qua = 'scored' group by yeu_to order by so_du_bao desc
```
Hỏi: Hôm nay nguồn số liệu thị trường nào bị lỗi?
```sql
select viec, nguon, chuoi, count(*) as so_lan_loi from nguon_du_lieu where ngay = date('now', '+7 hours') and loi is not null group by viec, nguon, chuoi
```
Hỏi: Việc nền nào lỗi trong 7 ngày qua?
```sql
select viec, ngay, loi from viec_nen where trang_thai = 'failed' and ngay >= date('now', '+7 hours', '-6 days') order by luc_bat_dau desc
```
