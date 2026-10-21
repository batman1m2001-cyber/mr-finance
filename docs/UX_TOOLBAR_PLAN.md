# The client's side toolbar: findings and plan (2026-10-21)

Owner request: look at each item of the client's side toolbar and make the interface more efficient — redesign the
visual, remove duplication. Business feedback the same day: cash flow over time and allocation with profit/loss
were easy to find in the old overview and are hard to find now.

Audit: the live demo, client C01 (Nguyễn Minh Khoa), desktop 1440×900 and phone 390, every toolbar item clicked and
its Thông tin tab read; code in `web/workspace/lenses.js`, `workspace.js`, `inspector.js`, `strip.js`, `web/shell.js`.

## What the toolbar is today

Eight icons, no labels (the name shows only on hover):

| Icon | Opens | What the user gets |
|---|---|---|
| Tổng quan | lens | the whole graph; Thông tin lists news and policy by impact |
| Tài sản | lens | holdings and sources on the graph; Thông tin lists them; "Xem đầy đủ → Tài sản" |
| Dòng tiền | lens | **this month only**: 3 nodes (income, spending, reserve); "Xem đầy đủ → Toàn cảnh" |
| Mục tiêu & kịch bản | lens | goals and scenarios; "Xem đầy đủ → Kế hoạch" |
| Tin & sự kiện | lens | news and policy nodes; Thông tin: the same list as Tổng quan |
| Rủi ro | lens | stress loss, concentration, reserve; "Xem đầy đủ → Khẩu vị rủi ro, Chi tiết tài sản" |
| Chuyên gia | page (sheet) | the advisor team |
| Bộ nhớ | page (sheet) | what the assistant remembers |

A lens only filters the graph. The charts and tables sit behind a "Xem đầy đủ" button at the bottom of the
Thông tin tab: three clicks, and easy to miss.

## Findings

1. **The content is hidden behind the lenses.** The cash-flow chart over time exists (Chi tiết) but the Dòng tiền
   lens shows one month and links to Toàn cảnh, not to the chart. This is the business's complaint.
2. **The same numbers in five places.** Net worth, cash flow and allocation appear in the strip, Toàn cảnh,
   Chi tiết, the new "Dòng tiền & phân bổ" view and (allocation) the Tài sản page, each drawn differently.
3. **Tổng quan and Tin & sự kiện show the same Thông tin list** (news and policy by impact).
4. **Bộ nhớ is reachable three ways** (header link, toolbar, assistant panel), and its toolbar icon is the same
   clock-arrow as the assistant's conversation history.
5. **One thing, several names:** "Tin & sự kiện" (toolbar) vs "Tin tác động" (menu); "Chi tiết" vs "Chi tiết tài
   sản"; Khẩu vị rủi ro sits under Mục tiêu & kịch bản in the menu but under Rủi ro in the toolbar.
6. **Wrong label:** in the Tài sản lens, Khoản vay and Dư nợ thẻ are labelled "Tài sản".
7. **Controls cover the graph:** legend, Ngày/Tháng/Năm, the view switch and four icon buttons float over the top
   of the graph and hide node labels (Dòng tiền and Tin lenses: "3 lớp tài sản khác", "2 khoản nợ khác" cut off).
8. **The subtitle never changes** with the lens ("Tài sản, dòng tiền, mục tiêu, rủi ro và tin tức quanh bạn").
9. **A page open, Thông tin stale:** with Bộ nhớ or Chuyên gia open, Thông tin still shows the previous lens.
10. **Strip, Rủi ro hiện tại:** a stray vertical line beside "Vượt ngưỡng" (to check: the gauge drawn without its bar).

## Plan

Done on `ux/money-view` (2026-10-21): the "Dòng tiền & phân bổ" view (cash flow 12/24/36 months, large payments,
recurring items, allocation with profit/loss), one click from the overview and from the strip's two cards; Chi tiết
draws the same panels (`web/charts/panels.js`).

**T1 · Quick fixes (S).** Findings 6, 7, 8, 9, 10: liabilities labelled "Nợ"; the controls in their own row above the
graph (as the new view already does); a subtitle per lens; Thông tin follows the open page; the strip's gauge.

**T2 · Toolbar with names (S).** A short label under each icon, always visible (the rail grows ~16 px). Lenses on
top, then a divider, then Chuyên gia. Bộ nhớ leaves the toolbar (header and assistant panel keep it).

**T3 · Each lens opens its content (M).** The view switch becomes per lens: **Đồ thị | Bảng**. The Bảng of each lens is
its page, in the centre, no sheet: Tổng quan → net worth and the strip's KPIs in full; Tài sản → the holdings
table; Dòng tiền → the cash-flow view; Mục tiêu → Kế hoạch; Tin → Tác động thị trường; Rủi ro → risk and reserve.
"Xem đầy đủ" goes away.

**T4 · One place per number (M).** With T3, Toàn cảnh and Chi tiết have no job of their own: their blocks move into
the lenses' Bảng, and their addresses open the matching lens (search, citations and the bell keep working). Toàn
cảnh's month sankey goes to Dòng tiền → Bảng. The strip stays the one summary.

**T5 · One name per thing (S).** Toolbar, menu, sheet title and the assistant's page names use the same words; Khẩu
vị rủi ro under Rủi ro everywhere.

Gate for every step: desktop and phone screenshots, the UI suite (`tests/ui`), `test_how` (every figure keeps its
"Cách tính"), no console errors.

## Open for the owner

- T4 retires two pages (Toàn cảnh, Chi tiết) as separate screens. Their content is kept, not deleted.
- Bộ nhớ out of the toolbar (T2).
