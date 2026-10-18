# adm-oos-01 — Sao lưu SQLite

Category: out_of_scope · persona: Quản trị hỏi kỹ thuật · BRD: OWN-AS-07

General knowledge, labelled as such; no pretended action on the server.

## Turn 1

**Người dùng:** Sao lưu một cơ sở dữ liệu SQLite đang chạy thì nên làm thế nào cho an toàn?

*Công cụ:* — · *trạng thái:* ok · *chế độ:* model · 3.7 s · US$0.00086

**Trợ lý:**

Đây là câu hỏi kiến thức phổ thông, không cần tra cứu hệ thống. Tôi trả lời trực tiếp.

Với SQLite đang chạy, bạn không nên chỉ copy file .db thô, vì có thể gặp ghi dở và file bị hỏng. Cách an toàn:

1. **Dùng lệnh backup có sẵn của SQLite**: `sqlite3 nguon.db ".backup dich.db"`. Lệnh này tự xử lý khóa và đảm bảo bản sao nhất quán.
2. **Hoặc dùng `VACUUM INTO`**: `VACUUM INTO 'dich.db';` chạy trong kết nối đang mở, cho ra một bản sao gọn và nhất quán.
3. **Bật WAL và sao lưu cả file phụ**: nếu dùng chế độ WAL, phải sao lưu cả `-wal` và `-shm`, hoặc tốt hơn là dùng một trong hai cách trên.
4. **Kiểm tra bản sao**: chạy `PRAGMA integrity_check;` trên bản sao và thử khôi phục thử định kỳ.
5. **Lưu nhiều bản, ở nơi khác máy chủ**: giữ bản theo ngày và chuyển ra ổ hoặc nơi lưu trữ riêng.

Nếu bạn cho biết hệ thống đang chạy trên môi trường nào (Linux, Docker, hay Windows), tôi có thể gợi ý lịch sao lưu cụ thể hơn.

**Kiểm tra:** đạt
