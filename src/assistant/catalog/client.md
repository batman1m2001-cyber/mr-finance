<!-- The client's definitions and examples (docs/ASSISTANT_DATA_PLAN.md §3.3); every SQL runs in the client's room in
tests/test_datacatalog.py. The family tables hold the client's own family only. -->
## Định nghĩa
- Tổng tài sản: `sum(gia_tri)` với `loai = 'asset'`. Nợ: `loai = 'liability'`. Tài sản ròng: tài sản trừ nợ.
- Chi tiêu: `dong_tien` với `chieu = 'out'`; thu nhập: `chieu = 'in'`. Tháng trước:
  `thang = strftime('%Y-%m', 'now', '+7 hours', 'start of month', '-1 month')`.
- Mục tiêu có rủi ro: `muc_tieu.trang_thai in ('at_risk', 'off_track')`.

## Ví dụ
Hỏi: Tổng tài sản của gia đình tôi là bao nhiêu?
```sql
select sum(gia_tri) as tong_tai_san from tai_san where loai = 'asset'
```
Hỏi: Tài sản ròng của tôi?
```sql
select sum(case when loai = 'asset' then gia_tri else -gia_tri end) as tai_san_rong from tai_san
```
Hỏi: Tài sản của tôi chia theo loại thế nào?
```sql
select lop, sum(gia_tri) as gia_tri, round(100.0 * sum(gia_tri) / (select sum(gia_tri) from tai_san where loai = 'asset'), 1) as phan_tram from tai_san where loai = 'asset' group by lop order by gia_tri desc
```
Hỏi: Tôi có bao nhiêu tiền gửi?
```sql
select sum(gia_tri) as tien_gui from tai_san where lop = 'deposit'
```
Hỏi: Tháng trước tôi chi bao nhiêu, theo nhóm?
```sql
select ten_nhom, sum(so_tien) as da_chi from dong_tien where chieu = 'out' and thang = strftime('%Y-%m', 'now', '+7 hours', 'start of month', '-1 month') group by ten_nhom order by da_chi desc
```
Hỏi: Mỗi tháng tôi thu và chi bao nhiêu?
```sql
select thang, sum(case when chieu = 'in' then so_tien else 0 end) as thu, sum(case when chieu = 'out' then so_tien else 0 end) as chi from dong_tien group by thang order by thang
```
Hỏi: Tháng nào tôi chi nhiều nhất?
```sql
select thang, sum(so_tien) as da_chi from dong_tien where chieu = 'out' group by thang order by da_chi desc limit 1
```
Hỏi: Những khoản chi lớn nhất của tôi?
```sql
select ngay, mo_ta, so_tien from dong_tien where chieu = 'out' order by so_tien desc limit 5
```
Hỏi: Mỗi tháng tôi trả học phí bao nhiêu?
```sql
select thang, sum(so_tien) as hoc_phi from dong_tien where nhom = 'school' group by thang order by thang
```
Hỏi: Mục tiêu nào của tôi đang có rủi ro?
```sql
select ten, trang_thai, thieu, han from muc_tieu where trang_thai in ('at_risk', 'off_track')
```
Hỏi: Học phí cho con còn thiếu bao nhiêu?
```sql
select ten, can, co, thieu, can_de_danh_thang, han from muc_tieu where ma = 'tuition'
```
Hỏi: Tiến độ các mục tiêu tôi đang theo dõi?
```sql
select ten, round(100 * tien_do) as phan_tram, trang_thai from muc_tieu where dang_theo_doi = 1 order by tien_do
```
Hỏi: Hôm nay có tin gì về vàng?
```sql
select bao, tieu_de, gio_lay from tin where ngay_lay = date('now', '+7 hours') and (loai_su_kien = 'gold' or khong_dau(tieu_de) like '%vang%') order by luc_lay desc limit 10
```
