# rm-act-01 — Duyệt đề xuất của khách, xác nhận, đọc lại

Category: actions · persona: RM của C01 (rm01) · BRD: BRD-FR-603, OWN-AS-06

The RM approves the client's proposal: it waits for Xác nhận, then the queue says approved.

## Turn 1

**Người dùng:** Khách C01 có đề xuất nào đang chờ tôi không?

*Công cụ:* de_xuat · *trạng thái:* ok · *chế độ:* model · 3.5 s · US$0.00188

**Trợ lý:**

Có. Hàng chờ của khách C01 hiện có 2 đề xuất đang chờ:

1. **Học phí cho con (trong nước / du học) – Tích lũy đều**: đang chờ RM (bạn) duyệt.
2. **Giảm tỷ trọng cổ phiếu ngân hàng**: đang chờ chuyên gia duyệt, bạn chưa thể duyệt ở bước này.

Ngoài ra có 2 đề xuất học phí đã được duyệt trước đó. Bạn muốn tôi duyệt hoặc từ chối đề xuất học phí đang chờ không?

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Được, duyệt đề xuất đó.

*Công cụ:* — · *chờ xác nhận:* duyet_de_xuat · *trạng thái:* pending · *chế độ:* model · 1.5 s · US$0.00095

**Trợ lý:**

Duyệt đề xuất “Học phí cho con (trong nước / du học) — Tích lũy đều”?

**Kiểm tra:** đạt

## Turn 3

**Người dùng:** Xác nhận

*Công cụ:* duyet_de_xuat · *trạng thái:* ok · *chế độ:* model · 1.8 s · US$0.00193

**Trợ lý:**

Đã duyệt đề xuất **Học phí cho con (trong nước / du học) – Tích lũy đều** của khách C01. Đề xuất này giờ chuyển sang chuyên gia có chứng chỉ để duyệt tiếp.

**Kiểm tra:** đạt
