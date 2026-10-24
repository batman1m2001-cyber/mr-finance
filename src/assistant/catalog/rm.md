<!-- The RM's definitions and examples (docs/ASSISTANT_DATA_PLAN.md §3.3); every SQL runs in the RM's room in
tests/test_datacatalog.py. The family tables hold the RM's own book only. -->
## Định nghĩa
- Gia đình của tôi: các dòng của `gia_dinh` (chỉ sổ khách hàng của bạn).
- Tổng tài sản: `sum(gia_tri)` với `loai = 'asset'`. Nợ: `loai = 'liability'`. Tài sản ròng: tài sản trừ nợ,
  `sum(case when loai = 'asset' then gia_tri else -gia_tri end)`.
- Thiệt hại khi thị trường sốc: `sum(gia_tri * muc_soc)` trên tài sản.
- Yêu cầu chờ duyệt: `duyet.trang_thai = 'pending_specialist'`.
- Chi vượt thu: `chi_tieu_thang > thu_nhap_thang`.

## Ví dụ
Hỏi: Sổ của tôi có bao nhiêu gia đình?
```sql
select count(*) as so_gia_dinh from gia_dinh
```
Hỏi: Tài sản ròng của từng gia đình?
```sql
select ma_gia_dinh, sum(case when loai = 'asset' then gia_tri else -gia_tri end) as tai_san_rong from tai_san group by ma_gia_dinh order by tai_san_rong desc
```
Hỏi: Gia đình nào có tổng tài sản lớn nhất?
```sql
select g.ten, sum(t.gia_tri) as tong_tai_san from tai_san t join gia_dinh g on g.ma_gia_dinh = t.ma_gia_dinh where t.loai = 'asset' group by g.ma_gia_dinh order by tong_tai_san desc limit 1
```
Hỏi: Tỷ trọng bất động sản của từng gia đình?
```sql
select ma_gia_dinh, round(100.0 * sum(case when lop = 'real_estate' then gia_tri else 0 end) / sum(gia_tri), 1) as phan_tram_bds from tai_san where loai = 'asset' group by ma_gia_dinh
```
Hỏi: Gia đình C01 đang nợ những khoản nào?
```sql
select ten, lop, gia_tri from tai_san where ma_gia_dinh = 'C01' and loai = 'liability' order by gia_tri desc
```
Hỏi: Khoản nào khách tự khai, chưa xác minh?
```sql
select ma_gia_dinh, ten, gia_tri from tai_san where do_tin_cay = 'declared' order by gia_tri desc
```
Hỏi: Mỗi gia đình rút nhanh được bao nhiêu tiền?
```sql
select ma_gia_dinh, sum(gia_tri) as thanh_khoan from tai_san where loai = 'asset' and thanh_khoan = 1 group by ma_gia_dinh
```
Hỏi: Nếu thị trường sốc, mỗi gia đình mất khoảng bao nhiêu?
```sql
select ma_gia_dinh, round(sum(gia_tri * muc_soc)) as thiet_hai from tai_san where loai = 'asset' group by ma_gia_dinh order by thiet_hai desc
```
Hỏi: Gia đình nào chi tiêu vượt thu nhập?
```sql
select ten, thu_nhap_thang, chi_tieu_thang from gia_dinh where chi_tieu_thang > thu_nhap_thang
```
Hỏi: Gia đình nào lâu nhất tôi chưa liên hệ?
```sql
select g.ten, max(l.ngay) as lan_cuoi from gia_dinh g left join lien_he l on l.ma_gia_dinh = g.ma_gia_dinh group by g.ma_gia_dinh order by lan_cuoi is not null, lan_cuoi limit 3
```
Hỏi: Tháng này tôi liên hệ bao nhiêu lần, theo kênh?
```sql
select kenh, count(*) as so_lan from lien_he where substr(ngay, 1, 7) = strftime('%Y-%m', 'now', '+7 hours') group by kenh
```
Hỏi: Yêu cầu nào của khách đang chờ duyệt?
```sql
select ma_gia_dinh, tieu_de, ngay_lap from duyet where trang_thai = 'pending_specialist' order by luc_lap
```
Hỏi: Hôm nay có tin liên quan cao nào?
```sql
select bao, tieu_de, gio_lay from tin where ngay_lay = date('now', '+7 hours') and muc_lien_quan = 'high' order by luc_lay desc limit 20
```
Hỏi: Tuần này có sự kiện nào mới?
```sql
select ma, tieu_de, loai, ngay_lap from su_kien where ngay_lap >= date('now', '+7 hours', '-6 days') order by luc_lap desc
```
