# The client's four sections, by the bank's names (business feedback 2, 2026-10-22)

**Asked.** The business's second feedback file ("Các lỗi -2.docx", nine items, screenshots of the new app next to the
old one). They like the new vertical layout, but the menu must use the old version's names — "các keyword để đi thi
đúng đề bài bọn Wealth" — and drop what is said twice. "Chỉ là tên, còn sắp xếp layout dọc theo bản mới": the
names, not the old look. Sign-in is not touched.

## What they asked, item by item

| # | Ask | Today |
|---|---|---|
| 1, 7 | Remove the **Đồ thị tài chính** tab: "không cần, nhìn Toàn cảnh là được rồi" | Tổng quan has Toàn cảnh and Đồ thị tài chính |
| 2 | The menu named **Wealth View · Wealth Planning Advisor · Headline News · Relationship specialist**; Wealth View's tabs **Wealth view · Dữ liệu chi tiết tài sản** | 7 items: Tổng quan, Tài sản, Dòng tiền, Mục tiêu, Tin tức, Rủi ro, Chuyên gia |
| 3 | Tài sản (its page is already "Dữ liệu chi tiết tài sản") moves, unchanged, under Wealth View | its own menu item |
| 4 | Remove **Dòng tiền**: it is in Wealth View already | its own menu item, the dashboard's cash part |
| 5 | Kế hoạch tài chính unchanged, named **Wealth Planning Advisor** | Mục tiêu › Kế hoạch |
| 6 | Tin tức named **Headline News**; the Wealth Check coloured as the old one | grey "kém VN-Index" line |
| 8 | The risk test under Wealth Planning Advisor, tab **Risk profile test**; WPA's tabs **Wealth planning advisor · Risk profile test** | Rủi ro › Khẩu vị rủi ro |
| 9 | Chuyên gia named **Relationship specialist** | "Chuyên gia của bạn" |

(Item 0, the overview before cash flow on Toàn cảnh, shipped already: be5525d.)

## Decisions

- **Four menu items, the bank's names in English** as written (their capitals: "Wealth View", "Relationship
  specialist"); the tabs as written ("Wealth view", "Dữ liệu chi tiết tài sản", "Wealth planning advisor", "Risk
  profile test"). Headline News keeps its three tabs (Tác động tin, Đồ thị tác động, Chi phí chính sách): only the
  name was asked.
- **The graph is hidden from the client, not deleted.** No tab, no header-search hit, no page the assistant can open;
  its former tab's address (`#/client/tong-quan/ban-do`) and any unknown address open Wealth View. Only its own
  address `#/client/xem/<lens>` still opens it, linked from nowhere, so the kept code keeps its tests (seven UI test
  files drive it there) and can come back with one tab. (First written as "no address opens it"; narrowed while
  building W1 when those tests showed the code would otherwise be unreachable and untested.) The RM's Bản đồ tài
  chính and the iPhone app are unchanged. On that address the graph shows one row of tabs (its section's first page, "Trên đồ thị") and keeps the 72 px rail
  (the client's pages have a 104 px one for the bank's names): built with the wider rail, its 952 px canvas let the
  layout re-place nodes outside the visible area, which main shows too at a 1408 px window. **Open finding**: the
  graph's layout at that width; fix it before the graph comes back as a client tab.
- **Every old address keeps working** (citations, search, the bell, bookmarks): `#/client/tai-san`,
  `#/client/dong-tien` (→ Wealth View at Dòng tiền), `#/client/muc-tieu/ke-hoach`, `#/client/rui-ro/khau-vi`,
  `#/client/tin/...`, `#/client/chuyen-gia`. No address is renamed.
- **The page headings follow the menu**: eyebrow = the section, title = the tab (Relationship specialist, Risk profile
  test); the Vietnamese sub-line stays.
- **Item 6's colour**: the old Wealth Check shows "▲ hơn VN-Index 0,7%" in green; the new one prints the same line in
  grey. Ahead is green, behind red, with its arrow; the button says "Mở Wealth Planning Advisor".
- **The assistant and the guide use the new names**: its page list, the keyword router, its lens names, the user
  guide (docs/huong-dan/khach-hang.md), the guide test's questions; the client's graph pages leave its list.

## Steps

- **W1 The menu.** `web/workspace/lenses.js`: the toolbar is the four sections; Wealth View's tabs; Wealth Planning
  Advisor's tabs; the sheets' sections (Tài sản → Wealth View, Khẩu vị rủi ro → Wealth Planning Advisor); the old
  addresses resolved as above. `workspace.js`: the title "Wealth View". The header search lists the four sections
  and their tabs.
- **W2 The pages.** Headings of holdings, plan, risktest, advisor, the Tin tức pages; the Wealth Check colour (policy.js).
- **W3 The assistant and the guide.** `src/assistant/tools.py` PAGES, `src/copilot/router.py`, `src/assistant/turn.py`,
  `docs/huong-dan/khach-hang.md`, `data/assistant_guide_questions.json`.
- **W4 The BRD.** `docs/brd/ux/screens/client.md`, `ux/information_architecture.md`, `ux/screen_inventory.md`,
  `ux/user_journeys.md`; FEAT-40 (the graph is not a client tab), FEAT-29, FEAT-24 (the risk test's place), FEAT-21,
  FEAT-25, FEAT-28; ADR-0037 for the decision; `requirements_traceability.md` and `CHANGELOG.md`.
- **W5 Tests and the gate.** The UI tests that name the old menu, a new one for the four sections and every old
  address; screenshots desktop and phone, light and dark; merge, restart :8030.

**Gate.** The client's menu is the four sections with the tabs above, in both themes and on a phone; nothing a client
can click, search or ask leads to the graph; every old address opens its page; no client screen, assistant answer
or guide page uses a removed name; the UI and assistant tests pass (apart from the four failing on main before this).
