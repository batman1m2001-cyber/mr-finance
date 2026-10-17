# act-03 — Theo dõi VN-Index, xem, rồi huỷ

Category: actions · persona: trưởng phòng trẻ (C05) · BRD: OWN-AS-18, OWN-AS-06

A follow-up created, listed, cancelled; each checked in the state.

## Turn 1

**Người dùng:** Nhắc mình khi VN-Index xuống dưới 1.200 điểm nhé.

*Công cụ:* — · *chờ xác nhận:* theo_doi · *trạng thái:* pending · *chế độ:* model · 1.7 s · US$0.00068

**Trợ lý:**

Báo cho bạn một lần khi VN-Index dưới 1.200 điểm (theo dõi 30 ngày)?

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Xác nhận

*Công cụ:* theo_doi · *trạng thái:* ok · *chế độ:* model · 1.6 s · US$0.00137

**Trợ lý:**

Đã đặt theo dõi: mình sẽ báo một lần khi VN-Index xuống dưới 1.200 điểm. Khi điều kiện xảy ra, chuông thông báo sẽ hiện lên. Bạn có thể xem hoặc huỷ việc này ở trang Bộ nhớ.

**Kiểm tra:** đạt

## Turn 3

**Người dùng:** Mình đang theo dõi những gì?

*Công cụ:* theo_doi, theo_doi_cua_toi · *trạng thái:* ok · *chế độ:* model · 2.7 s · US$0.00136

**Trợ lý:**

Hiện bạn đang theo dõi một việc:
- VN-Index xuống dưới 1.200 điểm (đang theo dõi, chưa báo).

Bạn có thể xem hoặc huỷ ở trang Bộ nhớ.

**Kiểm tra:** đạt

## Turn 4

**Người dùng:** Huỷ cái đó đi.

*Công cụ:* theo_doi, theo_doi_cua_toi · *chờ xác nhận:* huy_theo_doi · *trạng thái:* pending · *chế độ:* model · 1.3 s · US$0.00070

**Trợ lý:**

Huỷ theo dõi “VN-Index dưới 1.200 điểm”?

**Kiểm tra:** đạt

## Turn 5

**Người dùng:** Xác nhận

*Công cụ:* huy_theo_doi · *trạng thái:* ok · *chế độ:* model · 1.4 s · US$0.00142

**Trợ lý:**

Đã huỷ việc theo dõi VN-Index dưới 1.200 điểm. Bây giờ bạn không còn việc theo dõi nào.

**Kiểm tra:** đạt
