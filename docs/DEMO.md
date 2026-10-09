# The five-minute demo

The brief's demo (section 7 of `mr_finance_idea_final.md`), on one client: **Nguyễn Minh Khoa**
(C01, "Chuyên gia"), 42, with his wife Trần Thu Hà, who consented to share her accounts. Every
number below is what the product shows on the demo data. `tests/test_demo.py` walks the same steps
through the same calls, so if the tests pass, the demo runs.

## Before you start

```bash
uv run operonx serve          # or, with pip: operonx serve (in the activated .venv)
```

Open <http://127.0.0.1:8030>, pick **Nguyễn Minh Khoa · Chuyên gia**, and press **Làm lại demo** in the
footer, so nothing from a previous run is left. The AI steps use their rule path unless a model is
configured (`.env.example`); the demo looks the same either way.

## 1. Connect the data (30 s) — Kết nối dữ liệu

- **Tier 1** is already connected: Techcombank, TCBS, Techcom Capital, OneHousing. The client did
  nothing. Say: *this is what only Techcombank has.*
- **Tier 2**: press **Dùng sao kê mẫu: vps_C01.csv**. It reads 3 holdings from VPS (MWG, SSI, cash:
  1,02 tỷ), each labelled *Từ sao kê*.
- **Tier 3**: in the chat, press the two example lines:
  *"Tôi có 1 mảnh đất 500m2 ở Long Thành mua 2019 giá 3 tỷ"* → valued at **9 tỷ** by its area's price;
  *"Tôi có 2 con, 14 tuổi và 10 tuổi"* → two dependents.
- Point at the trust mix on Tổng quan: verified, from a statement, declared. The confidence of the
  analysis follows these labels.

## 2. The risk test (30 s) — Bài test rủi ro

Answer boldly (the last option each time; for *Thu nhập* pick **Biến động theo kinh doanh**, for the
big expense **Không thể lùi**). In 9–10 questions it says: **wants Mạo hiểm, can bear Thận trọng**,
profile **Thận trọng**, drawdown limit **8%**, with the reasons (dependents, an expense that cannot
wait, income). Point at the two scores on one scale.

## 3. The overall dashboard (1 min) — Tổng quan

- **Cá nhân → Gia đình**: net worth **34,5 tỷ → 45,1 tỷ** (the brief's example dashboard shows 45,2).
- Allocation, P&L against VN-Index, the risk card now measured against the test's 8%.
- The **cash-flow calendar**: the ⚠ in March 2027 is the 1,8 tỷ tuition in Australia, found from the
  family's dated events; the recurring items were found in the transactions.

## 4. An alert lands (1 min) — Cảnh báo (in the family view)

- **Metro số 1** near the Thảo Điền flat: an opportunity, about **+778 triệu** after probability.
- **Thuế với người sở hữu từ 2 BĐS**: a draft, so a low probability; its line says how much more
  tax per year the second and third properties would pay. Filter **Rủi ro** to find it.
- Every alert shows exposure × sensitivity × probability and its source. The note above the list is
  the brief's: check each item's legal status before showing it.

## 5. A scenario (1 min) — Kịch bản (family view)

Press **Bán căn nhà thứ hai**. It picks the largest property that is not lived in (the Long Thành plot
just declared): tax and fees, cash that comes back, liquidity **6,57 tỷ → 15,3 tỷ**, and a light and a
heavy option. Press **Gửi RM duyệt** on one.

## 6. The RM approves (30 s) — RM duyệt

The proposal waits in the queue with its numbers. Add a note, press **Duyệt**. Back on Kịch bản, the
option says **RM đã duyệt**. Say: *everything the client sees is a simulation until an RM approves it.*
