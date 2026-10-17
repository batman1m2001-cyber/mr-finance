# nav-01 — Người mới hỏi đồ thị nghĩa là gì

Category: navigation · persona: người mới, nói chuyện thân mật (C05) · BRD: OWN-AS-02, KIT-COPILOT-02, OWN-GW-38

A first-time user reads the graph: the core, the dotted lines, then asks to open a page.

## Turn 1

**Người dùng:** Mình mới dùng app này, cái vòng tròn to ở giữa màn hình là gì vậy?

*Công cụ:* huong_dan · *trạng thái:* ok · *chế độ:* model · 5.6 s · US$0.00188

**Trợ lý:**

Vòng tròn lớn ở giữa là bạn. Con số trong vòng là **tài sản ròng** (tổng tài sản trừ đi các khoản nợ).

Quanh vòng là các nhóm thông tin: lớp tài sản, tiền vào và tiền ra, thanh khoản dự phòng, mục tiêu, rủi ro, kịch bản, tin tức và chính sách. Bạn bấm vào mục nào thì trợ lý sẽ giải thích mục đó.

Thanh công cụ phía trên giúp bạn chuyển góc nhìn: Tổng quan, Tài sản, Dòng tiền, Mục tiêu và kịch bản, Tin và sự kiện, Rủi ro. Nếu muốn xem tổng hợp nhanh, bạn mở "Toàn cảnh" từ góc nhìn Tổng quan.

**Kiểm tra:** đạt

## Turn 2

**Người dùng:** Còn mấy đường chấm chấm nối vào nó nghĩa là gì?

*Công cụ:* huong_dan · *trạng thái:* ok · *chế độ:* model · 5.2 s · US$0.00231

**Trợ lý:**

Hướng dẫn sử dụng không mô tả cụ thể đường chấm chấm, nên tôi chưa chắc nghĩa của chúng. Điều tôi biết chắc là:

- Các đường nối trên đồ thị thể hiện mối liên hệ giữa các mục, ví dụ một tin hay một yếu tố ảnh hưởng tới tài sản nào.
- Với đường dòng của một tin, độ dày và tốc độ thể hiện tác động kỳ vọng mỗi tháng. Đây chỉ là hình vẽ, không phải dòng tiền thật và không cộng vào tài sản ròng.
- Khi bạn chọn một mục, trợ lý sẽ sáng các mục liên quan để bạn thấy nó nối với đâu.

Nếu bạn chọn một mục rồi hỏi "mục này nối với gì?", tôi sẽ xem các liên kết của mục đó và nói rõ từng liên kết.

**Kiểm tra:** does not say /giả định|ước tính/

## Turn 3

**Người dùng:** Ok, mở giúp mình chỗ xem dòng tiền đi

*Công cụ:* mo_trang · *trạng thái:* ok · *chế độ:* model · 2.8 s · US$0.00225

**Trợ lý:**

Tôi đã mở trang Dòng tiền. Ở đó bạn chọn tháng để xem tiền vào, tiền ra, phần còn lại và khoản chi lớn nhất trong tháng.

**Kiểm tra:** đạt
