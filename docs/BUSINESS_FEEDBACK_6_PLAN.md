# Business feedback 6 — the staff desks (2026-10-24) — plan

The owner's 18 notes on the RM's and the CIO's desks, one on the Customer's Headline News and one on the sign-in page
([source](brd/sources/owner_requests/2026-10-24_business_feedback_6.md), BRD `OWN-FB-01…18`). Branch
`ux/feedback-6`, merged into `main` when every phase passes its gate, then live on :8030.

Nothing is thrown away that something else still opens: a page that loses its tab keeps its address (the bell, the
feed, the assistant and old links open it), unless the note asks for it to go.

## F1 · Sheets: nested tabs, no repeated header

- A sub-menu entry may carry `tab` (the top tab it belongs to) and the menu item `tabs` (their labels). The desk shows
  the top tabs, and under them the inner tabs of the current one when it has more than one page. An entry with
  `hidden: true` routes but has no tab.
- A sheet with tabs shows no title of its own and the back link is the chevron alone (labelled for a screen reader):
  the note on Tác động ("bỏ phần này") is about every sheet, the title repeated the current tab.
- Old addresses that lose their page (`MOVED` in `web/shell.js`) are replaced in the address bar by the page that
  took their place.

## F2 · RM (notes 1–6)

| Tab | Inner tabs (page) | Address |
|---|---|---|
| Wealth view | Tổng quan (detail) · Dữ liệu chi tiết tài sản (holdings) | `khach-hang/tong-quan`, `khach-hang/tai-san` |
| Wealth planning advisor | — (plan) | `khach-hang/ke-hoach` |
| Headline news | News and prediction (policy) · Đồ thị tác động (graph) | `khach-hang/chinh-sach`, `khach-hang/do-thi` |
| Advisory performance | Khách hàng này (performance) · Tất cả khách hàng (perfall) | `khach-hang/hieu-qua`, `khach-hang/tat-ca` |

- Tác động tin, Toàn cảnh, Bản đồ tài chính: no tab. `toan-canh` and `ban-do` → `tong-quan`; `tac-dong` keeps its
  address with no tab (the desk's "Tin tác động" rows, the bell's evidence).
- Duyệt đề xuất: no tab ("Bỏ tab Duyệt đề xuất"); the address stays, opened from the desk's "Đề xuất chờ duyệt" and
  the family's card, because the RM still decides there.
- The rail's Hiệu quả is "Advisory performance", the same two inner tabs (`hieu-qua/khach-hang`, `hieu-qua/tat-ca`).
- Sổ khách hàng: the drawing of the families goes; the cards stay, with a card of the families (each a row: name,
  why, net worth, its pages) in its place so a family can still be picked.
- Advisory performance laid out as the owner's mock: the Nội bộ banner, "Advisory performance" with "Hiệu quả tư vấn
  và AI cho khách hàng X · 12 tháng", the six figures, the AI pipeline (four numbered cards with arrows: AI News
  Reader, AI Impact Assessor, AI Planning Advisor, AI Client Chat, each with its Vietnamese line, score 0–100 and
  12-month trend), the log of recommendations, the important news missed. The figures stay the sample of
  `scripts/make_advisory.py`, marked "Dữ liệu mẫu".

## F3 · CIO · Decision board (notes 7–13)

- "Bàn quyết định" / "Bàn" → **Decision board** everywhere (desk title, rail, menu, heading, hint, assistant guide).
- The flow: Tin → Nhận định → Lần áp dụng, then Gia đình → RM inside their own tinted frame ("đến khách hàng").
  The Sự kiện stage goes (its count is in Tin's note).
- "Cần bạn quyết định": every row says its impact level (the highest relevance of its news: cao, vừa, thấp) and its
  news group (`EVENT_TYPE`), from `GET /api/desk` (`level`, `group`, `sources`, `scope` domestic / international).
  Filters above them as the inbox's: nguồn, trong nước / quốc tế, mức liên quan, tìm. 20 rows, then Xem thêm.
- The inbox in the board: its section "Tin mới" under the decisions, the inbox page itself (`pages/inbox.js` drawn
  into the desk): source health, filters, Lấy tin ngay, Bỏ tin, Gom thành sự kiện. The Tin tức group leaves the rail;
  `#/cio/hop-tin` → `#/cio`; `#/cio/nhan-dinh/<id>` stays (every decision row opens it), with no tab.
- The exposure card: **Tổng quan tác động tới tài sản**, full width; "Sự kiện gần đây", "Mô hình và dữ liệu",
  "Agent dưới bàn" go. Plain words: "Nếu kịch bản <tin> xảy ra, 5 gia đình dự kiến −1,2 tỷ trong 3 tháng; 1 gia đình
  cần RM xem trước." A picker of the effective scenarios (named by their news, never `AR-0001-v1-3`), the factor
  bars, and the families ranked: Gia đình, Kỳ vọng, % tài sản ròng, P10 (with its plain meaning in the "?").

## F4 · CIO · Tác động, Nội dung, Hiệu quả; Admin (notes 14–16)

- Tác động: one tab group **Tác động danh mục** (the old Phơi nhiễm page) and Đồ thị lần áp dụng. Lần áp dụng is no
  tab; its address stays (a run waiting for review opens there). The page's words: "Nếu kịch bản … xảy ra", "Kịch bản"
  for the picker, each named by its news and date; P10 said once: "P10: 1 trong 10 khả năng kết quả xấu hơn mức này".
- Nội dung: one tab **Bài viết** (`ban-tin`): the CIO writes an article — title and body, their own news or policy
  note — or a letter from approved views as today; audience Private clients only. Nghiên cứu and Chính sách are no
  tab; their addresses stay (search results, the RM's research). The server: a draft needs 1–6 views **or** a body.
- Mô hình (Tham số, Dữ liệu thị trường, Độ chính xác, Thử nghiệm hằng ngày), Đo lường, Agent, Việc nền, Cấu hình
  leave the CIO's rail; Admin gets a group Mô hình with those pages (it has Agent, Việc nền, Cấu hình already). The
  CIO's old addresses stay routable for links already sent (a configuration waiting opens `#/cio/cau-hinh`).
- A CIO group **Hiệu quả**: one plain page — news collected (today, 7 days), relevant, grouped into events, views
  approved; the forecasts scored right / wrong with their counts and what is still waiting; nothing technical (no
  model ids, tokens, prompts). Every figure from the existing reads (news monitor, forecasts, eval rates).

## F5 · Customer · Headline News (note 17)

- `score()` keeps each alert's impact by asset class (`by_class`: the rule's hits split over the holdings they
  touch, by value, or by the holding's own sensitivity for the sector rule; outflows and income their own class) and
  the bar is a stack of those parts, each named with its amount on hover; the parts add to the row's figure.

## F6 · Accounts (note 18)

- Remove the Compliance accounts (compliance, compliance2) and the Expert accounts (sp_*) from the seed, the live
  database and the sign-in page; the roles leave the sign-in, the menus, the desks and the roles an Admin can give.
- Their duties go to the CIO, the four-eyes rule kept (never the author): newsletters and articles, research,
  the policy register, held news, the configuration they owned; a second CIO (cio2) does the second pair of eyes.
  With no expert a recommendation is the RM's alone (as it already was for a family with none). The audit chain keeps
  the old roles' names on what they did.
- The live database: the accounts deleted, a recommendation waiting for an expert goes to the RM, a letter waiting
  for Compliance waits for the second CIO.

## F7 · Gate

- Tests updated for the new menus and duties; `test_how`, `test_access`, `check_brd_docs` green; the full suite in
  the background, failures compared with main's known five.
- Screenshots of every changed page, desktop and phone; merged into `main`, :8030 restarted and checked by signing in
  as the CIO, an RM, Admin and a client.
