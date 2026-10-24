<!-- Compliance's (and Admin's) definitions and examples (docs/ASSISTANT_DATA_PLAN.md §3.3); every SQL runs in the
compliance room in tests/test_datacatalog.py. -->
## Định nghĩa
- Tin đang bị giữ: mọi dòng của `tin_bi_giu`.
- Cảnh báo chưa xử lý: `canh_bao.trang_thai != 'resolved'`; chưa ai xem: `trang_thai = 'open'`.
- Đăng nhập: `nhat_ky.hanh_dong = 'auth.sign_in'`; CIO duyệt: `'decision.approve'`; trợ lý trả lời: `'assistant.turn'`.

## Ví dụ
Hỏi: Có bao nhiêu tin đang bị giữ?
```sql
select count(*) as so_tin from tin_bi_giu
```
Hỏi: Tin bị giữ vì nhắc đến VCB?
```sql
select ngay_lay, bao, tieu_de from tin_bi_giu where cong_ty_han_che like '%VCB%' order by luc_lay desc
```
Hỏi: Tin bị giữ theo công ty hạn chế?
```sql
select cong_ty_han_che, count(*) as so_tin from tin_bi_giu group by cong_ty_han_che order by so_tin desc
```
Hỏi: Hôm nay ai đã đăng nhập?
```sql
select nguoi, count(*) as so_lan, min(gio) as lan_dau from nhat_ky where hanh_dong = 'auth.sign_in' and ngay = date('now', '+7 hours') group by nguoi
```
Hỏi: Tháng này CIO duyệt bao nhiêu quyết định?
```sql
select count(*) as so_quyet_dinh from nhat_ky where hanh_dong = 'decision.approve' and substr(ngay, 1, 7) = strftime('%Y-%m', 'now', '+7 hours')
```
Hỏi: Ai làm nhiều việc nhất trong 7 ngày qua?
```sql
select nguoi, count(*) as so_viec from nhat_ky where ngay >= date('now', '+7 hours', '-6 days') group by nguoi order by so_viec desc limit 10
```
Hỏi: Nhật ký của sự kiện EV-2026-0001?
```sql
select ngay, gio, nguoi, hanh_dong from nhat_ky where doi_tuong = 'EV-2026-0001' order by so_thu_tu
```
Hỏi: Hôm nay trợ lý trả lời bao nhiêu lượt?
```sql
select count(*) as so_luot from nhat_ky where hanh_dong = 'assistant.turn' and ngay = date('now', '+7 hours')
```
Hỏi: Cảnh báo nào chưa xử lý?
```sql
select loai, tieu_de, trang_thai, muc_do, so_lan, ngay_tao from canh_bao where trang_thai != 'resolved' order by luc_gan_nhat desc
```
Hỏi: Có bao nhiêu cảnh báo chưa ai xem?
```sql
select count(*) as so_canh_bao from canh_bao where trang_thai = 'open'
```
Hỏi: Việc nền nào lỗi trong 7 ngày qua?
```sql
select viec, ngay, loi from viec_nen where trang_thai = 'failed' and ngay >= date('now', '+7 hours', '-6 days') order by luc_bat_dau desc
```
Hỏi: Mỗi ngày có bao nhiêu việc trong nhật ký, 7 ngày qua?
```sql
select ngay, count(*) as so_viec from nhat_ky where ngay >= date('now', '+7 hours', '-6 days') group by ngay order by ngay
```
