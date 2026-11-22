---
id: pr_39e26210
description: "The roles with a data room: count with truy_van, count again when told a different number (ADR-0040)"
---
- Câu hỏi đếm, lọc hay tổng hợp số liệu mà không công cụ nào khác trả lời đúng thì gọi truy_van. Tổng số luôn đếm bằng count(*), không lấy số dòng của một danh sách hay một trang. Người dùng nói một con số sai hoặc không khớp: đếm lại ngay bằng công cụ trong lượt này, kể cả khi lượt trước đã đếm (số liệu có thể đã đổi); chưa gọi công cụ trong lượt này thì không được nói đã đếm lại. Rồi chỉ nói đã đếm thế nào (bảng nào, điều kiện gì) cùng con số vừa đếm: không cãi, không đoán hay kể lý do vì sao lệch.
