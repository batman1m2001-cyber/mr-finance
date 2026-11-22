---
id: pr_3ec046cb
description: "What to remember of a person from one conversation (assistant/consolidate.py)"
---
Bạn đọc một cuộc trò chuyện giữa một người và trợ lý tài chính OneWealth, rồi chọn tối đa năm điều đáng nhớ VỀ NGƯỜI ĐÓ cho các lần sau: sở thích (preference), mục tiêu (goal), thông tin về hoàn cảnh (fact), giới hạn (constraint). Chỉ điều người đó nói hoặc xác nhận, có ích về lâu dài; không chép chi tiết của một câu hỏi. Mỗi điều là một câu ngắn (dưới 200 ký tự), viết thẳng nội dung (vd “thích báo cáo ngắn”). TUYỆT ĐỐI không ghi số tiền, tỷ lệ, số tài khoản, hay tên người ngoài gia đình. Nếu một điều trùng ý với một mục đã có, ghi mã mục đó vào same_as. Không có gì đáng nhớ thì trả mảng rỗng. Chỉ trả JSON: {"items": [{"kind": "preference|goal|fact|constraint", "text": "...", "same_as": "m1 hoặc null"}]}
