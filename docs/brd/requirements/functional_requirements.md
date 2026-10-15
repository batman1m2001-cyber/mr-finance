# Functional requirements (BRD §6) — `BRD-FR-nnn`

Layer A. The BRD groups its functional requirements in eight modules (§6.1–§6.8), one table each. The
Vietnamese is the BRD's text; the English is our faithful reading. Status: see
[`requirements_traceability.md`](requirements_traceability.md).

## 6.1 News collection and events — “Thu thập tin và sự kiện”

### BRD-FR-101 — RSS every 10 minutes
- **Source:** §6.1, row FR-101
- **Original:** “Lấy tin RSS từ danh sách nguồn (hiện 10 nguồn: VnExpress, VnEconomy, Báo Đầu tư, Vietstock, Nhân Dân, VTV, Fed…) mỗi 10 phút”
- **Meaning:** Fetch RSS from the source list every 10 minutes.
- **Acceptance:** a scheduled fetch every 10 minutes; each configured source is read; a broken feed does not stop the others.
- **Doc status:** needs_clarification (Q-08: “10 nguồn” is not a fixed list; §11.1 names 6 domestic + 2 international)

### BRD-FR-102 — Classify, score relevance, suggest an event type
- **Source:** §6.1, FR-102
- **Original:** “Phân loại tin quốc tế hoặc trong nước theo nguồn và từ khóa; chấm mức liên quan; gợi ý loại sự kiện”
- **Meaning:** Classify each item as international or domestic by source and keywords; score its relevance; suggest an event type.
- **Acceptance:** every kept item has kind, relevance and a suggested type.
- **Doc status:** documented

### BRD-FR-103 — The CIO's inbox
- **Source:** §6.1, FR-103
- **Original:** “Hộp tin mới cho CIO: lọc theo nguồn, bỏ tin, gom nhiều tin thành một sự kiện”
- **Meaning:** A new-news inbox for the CIO: filter by source, dismiss items, group several items into one event.
- **Acceptance:** filter by source; dismiss with a record; select ≥ 1 items → one event.
- **Doc status:** documented

### BRD-FR-104 — Public source and timestamps checked before an event
- **Source:** §6.1, FR-104
- **Original:** “Kiểm tra nguồn công khai và dấu thời gian (công bố, nạp, lập sự kiện) trước khi lập sự kiện”
- **Meaning:** Before an event is created, check that sources are public and that the timestamps (published, ingested, event created) are in order.
- **Acceptance:** an event refuses items that failed the gates; timestamps are stored for each item.
- **Doc status:** documented

### BRD-FR-105 — Hold events naming the restricted list
- **Source:** §6.1, FR-105
- **Original:** “Chặn sự kiện nhắc tổ chức trong danh sách hạn chế cho tới khi Tuân thủ cho phép”
- **Meaning:** Block an event that names a restricted organisation until Compliance allows it.
- **Acceptance:** the event is held; approval condition “no held news” fails until release.
- **Doc status:** documented

## 6.2 Exclusive research and regulation notes — “Nghiên cứu độc quyền và ghi chú quy định”

### BRD-FR-201 — Upload a report
- **Source:** §6.2, FR-201
- **Original:** “Nạp báo cáo: số báo cáo, loại (nghiên cứu, house view, ghi chú quy định), giờ phát hành, tóm tắt luận điểm, công bố xung đột lợi ích”
- **Meaning:** Upload a report with: number, kind (research, house view, regulation note), release time, thesis summary, conflict-of-interest disclosure.
- **Acceptance:** the five fields are captured; the kind is one of three.
- **Doc status:** documented

### BRD-FR-202 — Compliance releases or rejects
- **Source:** §6.2, FR-202
- **Original:** “Tuân thủ cho phát hành hoặc từ chối, ghi chú từ 20 ký tự; kiểm tra danh sách hạn chế; người phát hành khác người nạp”
- **Meaning:** Compliance releases or rejects with a note of at least 20 characters; the restricted list is checked; the releaser differs from the uploader.
- **Acceptance:** a shorter note is refused; a restricted mention cannot be released; the uploader cannot release.
- **Doc status:** documented

### BRD-FR-203 — Nothing unreleased or early reaches the inbox
- **Source:** §6.2, FR-203
- **Original:** “Báo cáo chưa phát hành hoặc chưa tới giờ không hiện trong hộp tin và không gắn được vào sự kiện”
- **Meaning:** A report not released, or before its time, neither appears in the inbox nor can be attached to an event.
- **Acceptance:** absent from the inbox and refused by event creation until released.
- **Doc status:** documented

### BRD-FR-204 — Regulation-note fields; goal branch, not price events
- **Source:** §6.2, FR-204
- **Original:** “Ghi chú quy định có thêm: tên văn bản, trạng thái, ngày hiệu lực, loại mục tiêu bị ảnh hưởng, số tuần chuẩn bị thêm, hồ sơ, thông điệp cho khách, gợi ý cho RM; đi nhánh mục tiêu, không vào sự kiện giá”
- **Meaning:** A regulation note also has: document name, status, effective date, affected goal types, extra preparation weeks, documents, client message, RM hint; it goes to the goal branch, never into a price event.
- **Acceptance:** the eight fields are captured; a released note never enters the news inbox.
- **Doc status:** documented

## 6.3 Agents and views — “Agent và nhận định”

### BRD-FR-301 — Run the CIO agent
- **Source:** §6.3, FR-301
- **Original:** “Chạy Agent CIO cho một sự kiện: 4 nhóm phân tích, tranh luận tăng/giảm tối đa 2 vòng, tổng hợp, kiểm tra định dạng (thử lại tối đa 2 lần)”
- **Meaning:** Run the CIO agent on one event: four analyst groups, a bull/bear debate of at most 2 rounds, synthesis, format check (at most 2 retries).
- **Acceptance:** the run records each step; a third format failure ends the run in AGENT_ERROR. Details: BRD-RULE-AI-03.
- **Doc status:** documented

### BRD-FR-302 — Content of a view
- **Source:** §6.3, FR-302
- **Original:** “Nhận định gồm dòng tác động theo loại tài sản, ngành, mã, tỷ giá (mức −3 đến +3) và bộ kịch bản 2–4 nhánh”
- **Meaning:** A view holds impact rows by asset class, sector, ticker and exchange rate (levels −3 to +3) and a set of 2–4 scenario branches.
- **Acceptance:** schema of §8.2 (BRD-RULE-AI-04).
- **Doc status:** documented

### BRD-FR-303 — The challenger
- **Source:** §6.3, FR-303
- **Original:** “Agent Phản biện chạy trước khi duyệt, chạy lại trên dòng CIO sửa; phát hiện theo mức Nghiêm trọng, Trung bình, Thấp”
- **Meaning:** The challenger agent runs before approval and again on what the CIO edits; findings are Critical, Medium or Low.
- **Acceptance:** an edit sends the view back to challenge; findings carry one of three severities.
- **Doc status:** documented

### BRD-FR-304 — CIO edits and decides
- **Source:** §6.3, FR-304
- **Original:** “CIO sửa dòng tác động và kịch bản (xác suất, chế độ, cỡ cú sốc), trả lời phát hiện, rồi Duyệt, Trả lại, Bác hoặc Thu hồi, kèm lý do”
- **Meaning:** The CIO edits impact rows and scenarios (probability, regime, shock size), answers findings, then Approves, Returns, Rejects or Withdraws, with a reason.
- **Acceptance:** each action requires a reason and is recorded; edits are schema-checked.
- **Doc status:** documented

### BRD-FR-305 — Market-level preview before approval
- **Source:** §6.3, FR-305
- **Original:** “Xem trước kết quả lan truyền ở tầm thị trường cho từng nhánh trước khi duyệt”
- **Meaning:** Before approving, preview each branch's propagation at market level.
- **Acceptance:** every factor's propagated move per branch and horizon, with no client data.
- **Doc status:** documented

### BRD-FR-306 — The policy agent
- **Source:** §6.3, FR-306
- **Original:** “Agent Chính sách tóm tắt văn bản đã xác nhận nguồn, trích điều khoản; radar chính sách”
- **Meaning:** A policy agent summarises source-verified documents and quotes their articles; a policy radar.
- **Acceptance:** summary with exact article quotes, only for verified documents; does not read portfolios (§8 table).
- **Doc status:** needs_clarification (Q-09: “radar chính sách” is not described further)

### BRD-FR-307 — Three AI run modes
- **Source:** §6.3, FR-307
- **Original:** “Chế độ chạy AI: trực tiếp qua API, qua hộp chờ (kết quả đẩy lên rồi đi qua cùng chốt kiểm tra), hoặc mô phỏng”
- **Meaning:** AI runs live through an API, through the inbox (results pushed, then through the same checks), or mocked.
- **Acceptance:** three modes; inbox results pass the same validation as live ones (§8.4).
- **Doc status:** documented

## 6.4 Impact computation and application runs — “Tính tác động và lần áp dụng”

### BRD-FR-401 — Snapshot, compute every family, hash
- **Source:** §6.4, FR-401
- **Original:** “Khi CIO duyệt, chụp ảnh cấu hình và giá, tính cho mọi gia đình, lưu lần áp dụng có mã băm”
- **Meaning:** On approval, snapshot configuration and prices, compute every family, store the application run with a hash.
- **Acceptance:** one run per approval; its snapshot hash covers holdings, prices, model and branches.
- **Doc status:** documented

### BRD-FR-402 — The family result
- **Source:** §6.4, FR-402
- **Original:** “Kết quả gia đình: dải 3 kỳ hạn, đóng góp theo yếu tố và loại tài sản, tới từng vị thế; chi phí lãi vay; tỷ lệ tài sản tính theo mô hình”
- **Meaning:** A family result: the band at three horizons, contributions by factor and asset class down to each position; loan interest cost; the share of assets valued by a model.
- **Acceptance:** all listed parts present for each family.
- **Doc status:** needs_clarification (Q-10: “chi phí lãi vay” — extra interest cost per year (§9.3) or the loan's 3-month contribution)

### BRD-FR-403 — Ranking and all-client summary
- **Source:** §6.4, FR-403
- **Original:** “Xếp hạng 20 (sau này toàn bộ) gia đình theo tác động; tóm tắt toàn bộ khách theo yếu tố”
- **Meaning:** Rank the 20 (later all) families by impact; summarise all clients by factor.
- **Acceptance:** families ordered by impact; a per-factor summary.
- **Doc status:** documented (20 is the author's demo size; here: all families of the demo, [ADR-0005](../decisions/ADR-0005-mock-clients-and-prices-public-news.md))

### BRD-FR-404 — Impact on goals
- **Source:** §6.4, FR-404
- **Original:** “Tác động lên mục tiêu: tỷ lệ đáp ứng trước, sau, mức Đạt, Theo dõi, Thiếu”
- **Meaning:** Impact on goals: funding ratio before and after, with a level On track (Đạt), Watch (Theo dõi), Short (Thiếu).
- **Acceptance:** for each goal of each family in a run, the ratio before/after and the level.
- **Doc status:** documented (the BRD gives no thresholds; our rule decided in ADR-0017, Q-11 resolved)

### BRD-FR-405 — Recompute and compare; withdraw a run
- **Source:** §6.4, FR-405
- **Original:** “Thẩm định lại (tính lại) và so sánh; thu hồi lần áp dụng”
- **Meaning:** Re-assess (recompute) and compare; withdraw an application run.
- **Acceptance:** a recompute makes a new run and supersedes the previous; a run can be withdrawn.
- **Doc status:** documented

### BRD-FR-406 — “Cách tính” and the trace
- **Source:** §6.4, FR-406
- **Original:** “Giải thích “cách tính” và truy vết từ một con số của gia đình về tin nguồn”
- **Meaning:** Explain “how it was computed” and trace a family's number back to the source news.
- **Acceptance:** from a number: formula, positions, scenarios, approval, news.
- **Doc status:** documented

## 6.5 Post-check and hand-over to the RM — “Hậu kiểm và chuyển RM”

### BRD-FR-501 — Post-check rules
- **Source:** §6.5, FR-501
- **Original:** “Quy tắc hậu kiểm: tài sản chiếm quá nhiều tài sản ròng, giá định giá đã cũ; Agent Phản biện viết tóm tắt”
- **Meaning:** Post-check rules: an asset too large a share of net worth; stale valuation prices; the challenger writes a summary.
- **Acceptance:** both rules produce findings with severities; a summary exists.
- **Doc status:** needs_clarification (Q-12: “Agent Phản biện viết tóm tắt” conflicts with F02 / §7.1 — a summary of family results may not go to an external AI)

### BRD-FR-502 — RMs see only post-checked runs
- **Source:** §6.5, FR-502
- **Original:** “RM chỉ thấy lần áp dụng đã qua hậu kiểm (hiệu lực, thay thế hoặc thu hồi kèm nhãn)”
- **Meaning:** RMs see only runs that passed post-check (effective, superseded or withdrawn, labelled).
- **Acceptance:** an RM read never returns COMPUTING, POST_CHECKING, NEEDS_CIO_REVIEW or FAILED runs.
- **Doc status:** documented

### BRD-FR-503 — The “RM xem trước” flag
- **Source:** §6.5, FR-503
- **Original:** “Đánh dấu “RM xem trước” khi kịch bản xấu 3 tháng ≤ −5% tài sản ròng”
- **Meaning:** Flag “RM pre-review” when the 3-month bad case is at or below −5 % of net worth.
- **Acceptance:** flag iff 3-month P10 / net worth ≤ −0.05.
- **Doc status:** documented

## 6.6 Goal branch — “Nhánh tác động lên mục tiêu”

### BRD-FR-601 — Declared or inferred outflow purpose
- **Source:** §6.6, FR-601
- **Original:** “RM khai mục đích dòng tiền ra nước ngoài và nước đến cho mục tiêu; máy suy từ tên khi chưa khai”
- **Meaning:** The RM declares a goal's outflow purpose and destination country; the machine infers them from the goal's name when not declared.
- **Acceptance:** declare endpoint; inference with the name traps of §10 (BRD-RULE-GOAL-02).
- **Doc status:** documented

### BRD-FR-602 — Match notes to goals; milestone and level
- **Source:** §6.6, FR-602
- **Original:** “Khớp ghi chú quy định đã phát hành với mục tiêu; tính mốc chuẩn bị và mức: liên hệ ngay, nhắc, ghi chú”
- **Meaning:** Match released regulation notes to goals; compute the preparation milestone and the level: contact now, remind, note.
- **Acceptance:** BRD §10 example reproduced (milestone 2026-12-07, “Nhắc trên thẻ mục tiêu”).
- **Doc status:** documented

### BRD-FR-603 — Where the goal branch is shown
- **Source:** §6.6, FR-603
- **Original:** “Hiển thị trên trang chủ RM, tab Mục tiêu, trang Nghiên cứu (CIO, Tuân thủ)”
- **Meaning:** Shown on the RM's home page, the Goals tab, and the Research page (CIO, Compliance).
- **Acceptance:** visible in those three places.
- **Doc status:** documented

### BRD-FR-604 — Refuse AML wording
- **Source:** §6.6, FR-604
- **Original:** “Từ chối ghi chú có thông điệp nhắc PEP, xếp hạng rủi ro, giao dịch đáng ngờ, giám sát”
- **Meaning:** Refuse a note whose message mentions PEP, risk rating, suspicious transactions or monitoring.
- **Acceptance:** upload refused; the check covers the client message and the RM hint (BRD §20 F18).
- **Doc status:** documented

## 6.7 Configuration, log, agent catalogue — “Cấu hình, nhật ký, danh mục agent”

### BRD-FR-701 — Versioned, owned configuration; propose then approve
- **Source:** §6.7, FR-701
- **Original:** “Cấu hình có phiên bản và chủ sở hữu: nguồn tin, danh sách trắng, danh sách hạn chế, ngưỡng, giả định lợi suất, mô hình yếu tố; đề xuất rồi duyệt”
- **Meaning:** Versioned configuration with owners — news sources, white list, restricted list, thresholds, return assumptions, factor model — changed by proposal then approval.
- **Acceptance:** each kind has versions and an owner; a change is proposed then confirmed (two people where §13.1 says so).
- **Doc status:** documented

### BRD-FR-702 — Hash-chained log; integrity check; export
- **Source:** §6.7, FR-702
- **Original:** “Nhật ký nối chuỗi băm (mỗi dòng chứa mã băm dòng trước); kiểm tra toàn vẹn; xuất”
- **Meaning:** A hash-chained log (each row holds the previous row's hash); an integrity check; export.
- **Acceptance:** verify finds any edit; the log can be exported.
- **Doc status:** documented

### BRD-FR-703 — The agent catalogue
- **Source:** §6.7, FR-703
- **Original:** “Danh mục agent: mục đích, chủ sở hữu, mức rủi ro, mô hình AI, lần chạy gần nhất, tham khảo mã nguồn mở”
- **Meaning:** An agent catalogue: purpose, owner, risk level, AI model, latest run, open-source references.
- **Acceptance:** one entry per agent (§8 table) with the six fields.
- **Doc status:** documented

### BRD-FR-704 — Step-by-step trace of the CIO agent
- **Source:** §6.7, FR-704
- **Original:** “Vết chạy từng bước của Agent CIO: đầu vào, đầu ra, phiên bản prompt, mô hình”
- **Meaning:** A per-step run trace of the CIO agent: input, output, prompt version, model.
- **Acceptance:** each node of each run stored with these fields.
- **Doc status:** documented

## 6.8 CIO newsletter — “Bản tin CIO”

### BRD-FR-801 — The CIO newsletter
- **Source:** §6.8, FR-801
- **Original:** “Soạn bản tin chung từ nhận định đã duyệt; mặc định khách Private và đại chúng nhận cùng lúc (phân phối công bằng); cho Private sớm hơn phải ghi căn cứ để Tuân thủ xem; Tuân thủ duyệt; xem trước, không gửi thật trong demo”
- **Meaning:** Compose a general newsletter from approved views; by default Private and retail clients receive it at the same time (fair distribution); giving Private earlier access needs a recorded justification for Compliance; Compliance approves; preview only, nothing sent in the demo.
- **Acceptance:** draft from approved views; same-time default; justification for early access; Compliance approval; no real sending.
- **Doc status:** documented
