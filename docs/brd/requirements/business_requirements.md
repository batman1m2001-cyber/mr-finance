# Business requirements (BRD §2, §4)

Layer A. Extracted from the BRD ([reference](original_brd_reference.md)); the Vietnamese is the BRD's text,
the English is our faithful reading. Implementation status is **not** here: see
[`requirements_traceability.md`](requirements_traceability.md).

“BRD demo column” is what the BRD reports about its author's demo (§4, column “Demo”), not about this product
(see [original_brd_reference.md](original_brd_reference.md#what-the-brd-describes--and-what-it-does-not)).

## The problem and the goals (BRD §2)

> Khách Private nhận hàng nghìn tin mỗi ngày nhưng không ai nói cho họ biết tin đó làm tài sản và kế hoạch của
> mình thay đổi bao nhiêu tiền.

| Party | Today's problem (BRD §2 table) |
|---|---|
| Private client | Assets scattered (bank, broker, property, gold, shares); noisy news nobody turns into a money impact; brokers' and funds' views are not set beside their portfolio and goals |
| RM | Not enough data to analyse each portfolio, so contacts follow a calendar or targets, not the moment |
| CIO, Research | The investment view stops at a generic bulletin; nobody measures which portfolios it touches or whether it was right |
| Compliance | AI might give unreviewed advice; numbers are hard to trace to a source; risk of client data leaking |

Business goals (BRD §2, “Mục tiêu kinh doanh”):

1. The client receives, quickly and under control, the money impact of important news on their portfolio and goals.
2. The RM contacts the right client at the right time, with content prepared.
3. The CIO's view and TCB's exclusive research reach each portfolio, and their accuracy is measured.
4. Every number and every piece of content that reaches a client has a reviewer and is traceable.

Design principle (BRD §1): **“AI soạn kịch bản, máy tính con số, con người duyệt”** — AI writes scenarios, the
machine computes the numbers, people approve.

## Success metrics (BRD §2) — `BRD-KPI-nn`

The BRD calls these “proposed; targets to be confirmed by the Private Banking division”. They measure the
tool, not the client's P&L; the rate at which clients act on recommendations is tracked but never targeted
(to avoid sales pressure).

| ID | Group | Metric (BRD) | Target (BRD) | Doc status |
|---|---|---|---|---|
| BRD-KPI-01 | Tốc độ | From news out to result ready for the RM | ≤ 2 h; urgent news ≤ 30 min | documented |
| BRD-KPI-02 | Độ phủ tin | Important news collected | ≥ 95 % | documented; “important” is our reading until the bank defines it (Q-07, G-D6) |
| BRD-KPI-03 | Độ chính xác | Right direction (VN-Index, out-of-sample) | ≥ 70 % (author's demo: 77 %) | documented |
| BRD-KPI-04 | Độ chính xác | Coverage of the P10–P90 band (out-of-sample, per factor and horizon) | 70–90 % (author's demo: 68–87 %) | documented |
| BRD-KPI-05 | Kiểm soát | Recommendations with a reviewer and a log | 100 % | documented |
| BRD-KPI-06 | RM | Contacts that start from a system signal | ≥ 50 % | documented |
| BRD-KPI-07 | Khách | High-level alerts opened | ≥ 70 % | documented |

## Business requirements (BRD §4) — `BRD-BR-nn`

> “Mười lăm yêu cầu dưới đây là điều kiện để nghiệp vụ chấp nhận hệ thống.” — these fifteen are the business's
> acceptance conditions.

### BRD-BR-01 — Three news sources, each item labelled
- **Source:** §4, row BR-01 · Priority: Bắt buộc (mandatory) · BRD demo column: Đã có
- **Original:** “Hệ thống nhận tin từ ba nguồn: quốc tế, trong nước, nghiên cứu độc quyền của TCB, và gắn nhãn nguồn cho từng tin”
- **Meaning:** The system takes news from three sources — international, domestic, and TCB's exclusive research — and labels each item with its source.
- **Acceptance:** every inbox item shows one of the three labels; a released research report enters labelled as exclusive.
- **Doc status:** documented

### BRD-BR-02 — White-listed public sources; publication not after ingestion
- **Source:** §4, BR-02 · Bắt buộc · Đã có
- **Original:** “Chỉ dùng tin từ nguồn công khai trong danh sách trắng do Tuân thủ duyệt; thời điểm công bố không muộn hơn lúc nạp”
- **Meaning:** Only items from public sources on a Compliance-approved white list; an item's publication time may not be later than its ingestion time.
- **Acceptance:** an item from a source off the list is refused; an item published in the future is refused (the BRD's F20 tolerance: more than 10 minutes ahead).
- **Doc status:** documented

### BRD-BR-03 — Exclusive research enters only when released
- **Source:** §4, BR-03 · Bắt buộc · Đã có
- **Original:** “Nghiên cứu độc quyền chỉ vào hệ thống khi Tuân thủ cho phát hành, người phát hành khác người nạp, và đã qua giờ công bố”
- **Meaning:** Exclusive research enters only when Compliance releases it, the releaser is not the uploader, and its publication time has passed.
- **Acceptance:** an unreleased report is invisible in the inbox; the uploader cannot release; release before the publication time is refused.
- **Doc status:** documented

### BRD-BR-04 — Restricted-list mentions held for Compliance
- **Source:** §4, BR-04 · Bắt buộc · Đã có
- **Original:** “Tin nhắc tới tổ chức trong danh sách hạn chế bị chặn chờ Tuân thủ”
- **Meaning:** News naming an organisation on the restricted list is held until Compliance acts.
- **Acceptance:** such an item is held; an event containing it cannot be approved until Compliance releases it.
- **Doc status:** documented

### BRD-BR-05 — 2–4 scenarios per event; AI gives no impact numbers
- **Source:** §4, BR-05 · Bắt buộc · Đã có
- **Original:** “Mỗi sự kiện có 2–4 kịch bản với xác suất, cú sốc lõi và tin nguồn; AI không tự đưa con số tác động”
- **Meaning:** Each event has 2–4 scenarios, each with a probability, core shocks and source news; AI never produces impact figures itself.
- **Acceptance:** a view with fewer than 2 or more than 4 branches is refused; AI chooses shock sizes from the library only; all money figures come from the engine.
- **Doc status:** documented

### BRD-BR-06 — Independent challenge before approval
- **Source:** §4, BR-06 · Bắt buộc · Đã có
- **Original:** “Nhận định được phản biện độc lập bởi tuyến 2 trước khi CIO duyệt; phát hiện nghiêm trọng phải được trả lời”
- **Meaning:** A second-line, independent challenge runs before the CIO approves; every critical finding must be answered.
- **Acceptance:** approval is blocked without a challenge on the current content, or with an unanswered critical finding.
- **Doc status:** needs_clarification (Q-05: “tuyến 2” is an organisational line; the BRD implements it as a different AI model owned by Compliance)

### BRD-BR-07 — The CIO approves; nothing is computed before
- **Source:** §4, BR-07 · Bắt buộc · Đã có
- **Original:** “CIO duyệt kịch bản thị trường và tham số mô hình; không tính cho gia đình nào khi chưa duyệt”
- **Meaning:** The CIO approves market scenarios and model parameters; no family is computed before approval.
- **Acceptance:** no application run exists for a view that is not APPROVED.
- **Doc status:** documented

### BRD-BR-08 — VND impact per position, three horizons, one engine
- **Source:** §4, BR-08 · Bắt buộc · Đã có
- **Original:** “Tác động tính bằng VND cho từng vị thế và khoản vay, 3 kỳ hạn (1 tuần, 3 tháng, 12 tháng) × mức kỳ vọng và các mốc P5, P10, P50, P90; cộng lên theo loại tài sản, yếu tố, gia đình, mục tiêu. Đây là bộ máy duy nhất cho xếp hạng, cảnh báo, mục tiêu và diễn giải.”
- **Meaning:** Impact in VND for every position and loan, for 1 week, 3 months and 12 months, as an expected value and P5/P10/P50/P90; summed by asset class, factor, family and goal. This one engine feeds ranking, alerts, goals and explanations.
- **Acceptance:** per-position results at three horizons with five statistics; contributions add up to the totals; ranking and RM flags come from the same results.
- **Doc status:** needs_clarification (Q-03: “the only engine … for alerts” versus the product's separate policy-cost alerts)

### BRD-BR-09 — RM pre-review at a 5 % bad case
- **Source:** §4, BR-09 · Bắt buộc · Đã có
- **Original:** “Gia đình có kịch bản xấu mất từ 5% tài sản ròng trong 3 tháng phải được RM xem trước”
- **Meaning:** A family whose bad case loses 5 % or more of net worth over 3 months must be pre-reviewed by its RM.
- **Acceptance:** flag when the 3-month P10 ≤ −5 % of net worth (FR-503 makes “bad case” = P10).
- **Doc status:** documented

### BRD-BR-10 — Regulation that delays goals abroad reaches the right families
- **Source:** §4, BR-10 · Bắt buộc · Đã có
- **Original:** “Quy định không đổi giá nhưng ảnh hưởng mục tiêu có dòng tiền ra nước ngoài được báo tới đúng gia đình, không dùng dữ liệu chống rửa tiền”
- **Meaning:** A regulation that moves no price but affects goals sending money abroad is reported to the right families, without using anti-money-laundering data.
- **Acceptance:** matching uses goals only; AML wording is refused (§10).
- **Doc status:** documented

### BRD-BR-11 — AI never reads client data
- **Source:** §4, BR-11 · Bắt buộc · Đã có
- **Original:** “AI soạn nhận định không đọc dữ liệu khách, mục tiêu, ghi chú RM”
- **Meaning:** The AI that drafts views does not read client data, goals or RM notes.
- **Acceptance:** no client name, account, balance or goal appears in any prompt (tested on every prompt).
- **Doc status:** documented. Scope note: the BRD extends this to every LLM task (§8 “tất cả chỉ đọc tin, văn bản và mô hình yếu tố, không đọc dữ liệu gia đình”) and to any data sent to an AI provider (§14, NFR-08) — see BRD-RULE-ZONE-01, BRD-RULE-AI-11.

### BRD-BR-12 — Every number traceable; the log cannot be edited
- **Source:** §4, BR-12 · Bắt buộc · Đã có
- **Original:** “Mọi con số truy ngược được tới kịch bản, lời duyệt, tin nguồn; nhật ký không sửa được”
- **Meaning:** Every number traces back to its scenario, the approval and the source news; the log is immutable.
- **Acceptance:** from a family number, the trace shows scenarios, approver and reason, formula and news; editing the log is refused and detected.
- **Doc status:** documented

### BRD-BR-13 — CIO sees exposure of all clients by factor
- **Source:** §4, BR-13 · Priority: Nên có (should) · Đã có
- **Original:** “CIO thấy mức phơi nhiễm toàn bộ khách theo yếu tố để tránh khuyên mọi khách cùng một hướng”
- **Meaning:** The CIO sees all clients' exposure by factor, so as not to push every client the same way (herding).
- **Acceptance:** an aggregate of exposure per factor over all families of a run.
- **Doc status:** documented

### BRD-BR-14 — The CIO can withdraw a view; RMs see “Đã thu hồi”
- **Source:** §4, BR-14 · Bắt buộc · Đã có
- **Original:** “CIO thu hồi được nhận định; RM thấy nhãn “Đã thu hồi””
- **Meaning:** The CIO can withdraw an approved view; RMs see it labelled withdrawn.
- **Acceptance:** withdrawing a view withdraws its runs; the RM's reads carry the label.
- **Doc status:** documented

### BRD-BR-15 — Accuracy measured over time
- **Source:** §4, BR-15 · Nên có · BRD demo column: **Chưa có** (not in the author's demo either)
- **Original:** “Đo độ chính xác của kịch bản theo thời gian (biến động thực tế so với dải đã dự báo)”
- **Meaning:** Measure scenario accuracy over time: actual moves against the forecast band.
- **Acceptance:** per factor and horizon, the share of realised moves inside P10–P90 (target 70–90 %, ≥ 24 observations, §16.3).
- **Doc status:** documented
