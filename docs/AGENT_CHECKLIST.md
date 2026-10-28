# Danh sách agent của OneWealth — The agent checklist

One page for the business: every part of the app that uses a language model, one name each, and the three ways
they are measured. The same list is on the **Agent** page (CIO, Tuân thủ, Quản trị), read from the code
(`src/views/catalogue.py`), with each part's model *right now*. A test fails if the app gets a new model call that
is not on this list, and another fails if this page misses one of its names.

## The parts that use a model

| Tên (on the screens) | English | What it does | Owner | Risk | Measured by |
|---|---|---|---|---|---|
| **Agent CIO** | CIO agent | Reads an event's news and drafts the market view with 2–4 scenarios. In the daily trial it also groups the morning's news into events. Never sees client data. | CIO | high | Thử nghiệm hằng ngày, Cổng thay đổi |
| **Agent Phản biện** | Challenger | Checks Agent CIO's draft before the CIO decides, and challenges the CIO's own edits. A different model from Agent CIO. | Tuân thủ | medium | Thử nghiệm hằng ngày, Cổng thay đổi |
| **Agent Chính sách** | Policy agent | Summarises one verified public policy document; every point carries a quote from it. | Tuân thủ | medium | not measured yet |
| **Diễn giải nội bộ** | Internal explanation | The explanation of a computed figure for the RM, stamped internal. **Calls no model** today: a fixed template. | CIO | low | not measured yet |
| **Agent Bằng chứng tin** | News evidence agent | Reads one news item (title, summary, outlet, date) and drafts its event type and a qualitative frame. A frame that fails the checks goes back with the reasons, at most twice; the CIO approves it on the Bằng chứng tin page. Never sees client data. | CIO | medium | not measured yet |
| **Gợi ý nhãn mục tiêu** | Goal label suggester | Reads the name, date and category of each goal the RM has not declared and the rule cannot read, and suggests a purpose and destination country for money sent abroad. Nothing is kept until the RM saves it. Never sees amounts or client names. | RM | low | not measured yet |
| **OneWealth Copilot** | the assistant | The Trợ lý panel, for every role: answers with the app's own tools; anything it would write waits for the person to confirm. Includes its helpers: naming a conversation, distilling memory from a finished one, web search with the question masked, and the keyword router when no model is set. | Quản trị | medium | Bộ kiểm tra trợ lý |
| **Khai báo qua chat** | Declaration chat | Records what a client says they own or owe (land, gold, a loan, dependants, income). Rules when no model is set. | Quản trị | medium | not measured yet |
| **Đọc sao kê** | Statement reader | Reads an uploaded bank statement into holdings; the client checks them before saving. Rules when no model is set. | Quản trị | medium | not measured yet |
| **Viết bản tin** | Newsletter writer | Writes only the newsletter's opening paragraph, from approved views; a content filter and Tuân thủ check it. | CIO | low | not measured yet |

**Not a model, though older screens called them "AI":** the impact on a portfolio is the engine's arithmetic
(**Bộ máy tác động**), and the plan is the RM's (**Kế hoạch của RM**). The RM's "Hiệu quả tư vấn" page shows them in
its chain under these names, marked **Dữ liệu mẫu** — its scores are generated sample data.

**Which setting each part uses** (`resources.yaml`; the names are historical, so read them here):
`llm:cio` — Agent CIO, Agent Chính sách, Agent Bằng chứng tin, Gợi ý nhãn mục tiêu, Viết bản tin · `llm:challenger` — Agent Phản biện · `llm:copilot` —
OneWealth Copilot · `llm:assistant` — Khai báo qua chat and Đọc sao kê (demo) · `llm:onprem` — the same two, on the
bank's own model.

## The three ways they are measured

None of them is "the benchmark"; each has its own name.

| Tên | English | What it checks | When |
|---|---|---|---|
| **Thử nghiệm hằng ngày** | Daily trial | Agent CIO and Agent Phản biện on the day's real news, with no person in the loop; their forecasts are scored against the market afterwards. | 08:30 every morning until 31/10/2026; scoring every 15 minutes |
| **Cổng thay đổi** | Change gate | A fixed set of sample news with expected answers. A new prompt or model is approved only if it passes. | When a prompt or model change is proposed |
| **Bộ kiểm tra trợ lý** | Assistant test set | 32 questions to OneWealth Copilot: right tool, refusals, no other client's figures, every figure sourced. | By hand, whenever its model or instructions change (last: 31/32, 17/10/2026) |

The Agent page shows each one's latest result.
