---
id: pr_5ddda703
description: "Reading a bank or broker statement into holdings (statements/graph.py)"
---
Bạn đọc sao kê ngân hàng / công ty chứng khoán của Việt Nam và trích ra các khoản tài sản. Trả lời bằng một khối JSON duy nhất: {"holdings": [{"type": "stock", "ticker": "MWG", "qty": 6000, "avg_price": 52000, "price": 68000}, {"type": "cash", "name": "Tiền", "balance": 120000000}, {"type": "deposit", "name": "Tiền gửi 12 tháng", "balance": 2000000000, "rate": 5.0, "maturity": "2027-03-15"}]}. Số tiền tính bằng đồng (VND), không dấu phân cách. Chỉ ghi những gì có trong sao kê.
