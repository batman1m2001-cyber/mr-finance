# adm-oos-01 — Sao lưu SQLite

Category: out_of_scope · persona: Quản trị hỏi kỹ thuật · BRD: OWN-AS-07

General knowledge, labelled as such; no pretended action on the server.

## Turn 1

**Người dùng:** Sao lưu một cơ sở dữ liệu SQLite đang chạy thì nên làm thế nào cho an toàn?

*Công cụ:* — · *trạng thái:* ok · *chế độ:* model · 4.2 s · US$0.00084

**Trợ lý:**

Đây là kiến thức kỹ thuật phổ thông, tôi trả lời trực tiếp:

Với SQLite đang chạy, không nên chỉ sao chép file `.db` bằng cách copy thông thường, vì có thể lấy được bản dở dang khi còn ghi dữ liệu (đặc biệt khi có file `-wal`). Các cách an toàn hơn:

1. **Lệnh `.backup` của sqlite3** (an toàn nhất, chạy khi DB đang dùng):
   `sqlite3 onewealth.db ".backup /duong-dan/backup.db"`
2. **Online Backup API** trong ngôn ngữ lập trình (ví dụ Python `sqlite3` có `conn.backup(...)`).
3. **VACUUM INTO**: `VACUUM INTO '/duong-dan/backup.db';` tạo bản sao gọn và nhất quán.
4. **Tạm dừng ghi** (dừng ứng dụng hoặc khóa ghi) rồi copy file, nếu chấp nhận gián đoạn.

Lưu ý thêm:
- Nếu dùng WAL, sao lưu cả file `-wal` và `-shm` khi copy thủ công, hoặc dùng một trong các cách trên.
- Sau khi sao lưu, nên kiểm tra bản đó bằng `PRAGMA integrity_check;` và thử mở được.
- Lưu bản sao ở nơi khác máy chủ, và kiểm tra khôi phục định kỳ.

Nếu bạn cho biết hệ thống OneWealth đang chạy trên môi trường nào, tôi có thể kiểm tra tình trạng vận hành và chuỗi nhật ký hiện tại để bạn đối chiếu trước khi sao lưu.

**Kiểm tra:** đạt
