# act-03 — Theo dõi VN-Index, xem, rồi huỷ

Category: actions · persona: trưởng phòng trẻ (C05) · BRD: OWN-AS-18, OWN-AS-06

A follow-up created, listed, cancelled; each checked in the state.

## Turn 1

**Người dùng:** Nhắc mình khi VN-Index xuống dưới 1.200 điểm nhé.

*Công cụ:* — · *chờ xác nhận:* theo_doi · *trạng thái:* pending · *chế độ:* model · 1.5 s · US$0.00062

**Trợ lý:**

Báo cho bạn một lần khi VN-Index dưới 1.200 điểm (theo dõi 30 ngày)?

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Xác nhận

*Công cụ:* theo_doi · *trạng thái:* ok · *chế độ:* model · 1.4 s · US$0.00125

**Trợ lý:**

Đã đặt theo dõi: tôi sẽ báo một lần khi VN-Index xuống dưới 1.200 điểm. Bạn có thể xem hoặc huỷ ở trang Bộ nhớ.

**Kiểm tra:** đạt

## Turn 3

**Người dùng:** Mình đang theo dõi những gì?

*Công cụ:* theo_doi, theo_doi_cua_toi · *trạng thái:* ok · *chế độ:* model · 2.7 s · US$0.00127

**Trợ lý:**

Hiện bạn đang theo dõi một việc:
- VN-Index xuống dưới 1.200 điểm (đang theo dõi, chưa báo).

**Kiểm tra:** đạt

## Turn 4

**Người dùng:** Huỷ cái đó đi.

*Công cụ:* theo_doi, theo_doi_cua_toi · *chờ xác nhận:* huy_theo_doi · *trạng thái:* pending · *chế độ:* model · 1.5 s · US$0.00066

**Trợ lý:**

Huỷ theo dõi “VN-Index dưới 1.200 điểm”?

**Kiểm tra:** đạt

## Turn 5

**Người dùng:** Xác nhận

*Công cụ:* huy_theo_doi · *trạng thái:* ok · *chế độ:* model · 1.4 s · US$0.00134

**Trợ lý:**

Đã huỷ việc theo dõi VN-Index dưới 1.200 điểm. Hiện bạn không còn việc theo dõi nào.

**Kiểm tra:** đạt
