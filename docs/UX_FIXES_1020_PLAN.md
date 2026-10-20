# UI/UX fixes of 2026-10-20 — plan and result

The owner asked for UI/UX fixes on the live demo (:8030) after a review of every screen. The review signed in as each
demo role and took 67 routes at 1440×900 and 390×844 (134 screenshots); no route had a console error, a failed request,
an error panel or horizontal page scroll, so every finding below is layout or wording. The owner chose all four groups
(H, P, T, S) and asked for a recommendation on the English names (N). Branch `ux/fixes-1020`, off `main` (d5991a3).

| Phase | What | Where |
|---|---|---|
| H | A sheet's header: title squeezed onto three lines at 1440 px; ✕ wrapped to its own line on a phone; tabs cut mid-word with no sign they scroll | `web/core/tokens.css` (`.ws-sheet-h`, `.dk-tabs`), `web/desk/desk.js` |
| P | A phone's header: four rows of chrome before the page | `web/index.html`, `web/shell.js`, `web/header.js`, `web/core/tokens.css` |
| T | Text cut off: graph labels cut mid-word, Toàn cảnh cards, the money-flow chart's labels, phone tables, the heatmap's “−0%” | `web/workspace/graph.js`, `web/charts/charts.js`, `web/pages/exposure.js`, `web/core/tokens.css` |
| S | Small things: the browser's own file picker on Bộ nhớ, raw job ids in Việc nền, “+191.547 đ” beside tỷ, the CIO's bell at “99” | `web/pages/memory.js`, `web/pages/system.js`, `src/wealth/money.py` + `web/core/core.js`, `web/header.js` |
| N | English headings in a Vietnamese product | `web/pages/{plan,policy,advisor,map,perfall,performance,detail}.js` |

## H — a sheet's header keeps one line

**Cause (read in `tokens.css`).** `.ws-sheet-h` is a flex row: back link, title, the group's tabs, ✕. The tabs had
`flex-basis: auto` (their full width, ten tabs for the RM's client pages), so the flex shrink fell on the back link and
the title, which could wrap. On a phone the row wraps (`flex-wrap: wrap`) before it shrinks anything, so ✕ fell to
a line of its own when back + title + ✕ were a few pixels too wide (CIO · Sự kiện & nhận định).

**Fix.** Back link `flex: none; nowrap`; title one line, ellipsis (`min-width: 0`), and on a phone `flex: 1 1 0` so the
line holds back · title · ✕; tabs `flex: 1 1 0` (only the room left), no scrollbar, a fade on the side that has more
(`more-l` / `more-r`, set on scroll and resize), and the current tab scrolled into view.

**Measured** (title box w×h): RM `#/rm/khach-hang/tac-dong` at 1440×900 67×68 px before (three lines) → 103×23 after
(one); 1280×800 the same; on a phone ✕ is on the title's line for CIO, Admin, RM and Compliance sheets.

## P — a phone's header is one row

**Before** (top of `#page`, 390×844): client 256 px, CIO 293 px, RM on a client page 337 px.

**Fix (≤ 760 px).** The search box hides behind a search button (`#q-open`) that opens it full width and focused, and
closes it when it is left empty, on Esc or on navigation. The name row becomes a popover behind the person's
initials (`#me-open`): name, title, Bộ nhớ, Đăng xuất, then the theme switch (the theme button leaves the row on a phone; Đăng xuất stays the name row's first button, which `tests/ui` sign out by).
Order in the row: logo · client picker · Cá nhân/Gia đình · search · bell · initials; for the RM, Cá nhân/Gia đình goes
under the picker. ≤ 380 px and ≤ 370 px tighten the switch and the buttons so 375 and 360 px phones keep one row.
`.shell-top` gets `position: relative; z-index: 25` on a phone: it is `static` with a backdrop filter, so its popover
first rendered under the sheet's header (found by the click test below).

**Measured** (top of `#page`): client 256 → 180 px (360×780: 179); CIO 293 → 215; RM 337 → 258; the header row 52–54 px
at 360, 375, 390 and 412 px. Clicked on 375, 360 and 390 px: the popover opens over the page, the theme switch in it
works, a click outside closes it; search opens focused, finds “vang”, Esc closes it. Desktop is unchanged (both
buttons hidden, the row as before).

## T — text is not cut off

- **Graph labels** (`graph.js` `short`): a long name keeps its first clause when that fits (“Tập trung Đất nền Long
  Thành, Đồng Nai” → “Tập trung Đất nền Long Thành”, “Metro số 1 Bến Thành – Suối Tiên vận hành” → “Metro số 1 Bến
  Thành”), else whole words and “…” — never half a word (“Chính sách quản lý vàng miế…” → “Chính sách quản lý vàng…”).
  The limits (28 / 22 characters) are unchanged, so the layout is the same; the tooltip keeps the full name.
- **Toàn cảnh cards** (`tokens.css`): `.pcard` is a size container; under 300 px the change rows put the name and the
  amount on one line and the bar under them (“Bất động sản” was three lines in a 36 px column); the cash-flow card's
  chart goes under its figures when the text would have less than 140 px; a ratio tile's value wraps instead of
  “Trả nợ vay · 3…”.
- **Money-flow chart labels** (`charts.js` `sankey`): narrow (panel < 560 px, which is 1440 px with the dock open), a
  name takes two lines broken between words at the most even point (“Chi tiêu / sinh hoạt”) instead of 12 characters
  and “…” (“Chi tiêu si…”).
- **Phone tables** (`tokens.css`, ≤ 560 px): headings keep one line and the table scrolls (“Lần lấy được gần nhất”
  was a word a line); `.item` rows put the status under the text, which keeps its width.
- **Heatmap** (`charts.js` `heat`, `exposure.js`): under 1 % two decimals (“−0,18%”), under 0,005 % a dot, never
  “+0%” / “−0%”; column names cut at a word boundary (`words()` in `core.js`) and capitalised.

## S — small things

- **Bộ nhớ's file picker**: a “Chọn tệp…” button with the chosen file's name beside it, as Tài sản's statement upload
  does, instead of the browser's own “Choose File · No file chosen”.
- **Việc nền**: `assistant_retention` and `assistant_consolidate` were shown as their ids; they now have names in the
  page's own table (`system.js` `JOB`), as every other job has.
- **Amounts under a million**: in nghìn, in the server's and the page's formatter alike (`src/wealth/money.py`,
  `web/core/core.js`): “+191.547 đ” → “+192 nghìn”, “+742.980 đ” → “+743 nghìn”; under 1.000 still “850 đ”.
  `tests/test_wealth.py` pins it.
- **The CIO's bell**: it counted the first 200 news of the inbox and showed “99” for a capped count; it now counts the
  high-relevance new news, as the desk does (“100 liên quan cao”), plus the alerts, and shows “99+” over 99.

## N — the English names (recommendation taken)

The owner asked for a recommendation. A feature's English name came with PR #13 and is quoted by the BRD
(`brief_requirements.md`): the page now leads with Vietnamese and keeps that name small in its eyebrow
(`<span lang="en">`). Panel headings and table text are Vietnamese only.

| Before | After |
|---|---|
| h1 Wealth Planning Advisor | eyebrow “Kế hoạch · Wealth Planning Advisor”, h1 “Kế hoạch tài chính” |
| h1 Financial Intelligence Graph | eyebrow “Tổng quan · Financial Intelligence Graph”, h1 “Bản đồ tài chính” |
| h1 Advisory performance (both pages) | eyebrow “… · Advisory performance”, h1 “Hiệu quả tư vấn” |
| Our Wealth at Techcombank / Custody around the world / Self-managed | bold “Tại hệ sinh thái Techcombank” / “Lưu ký bên ngoài” / “Bạn tự quản lý”, the English name small |
| Wealth view · Wealth check · Approval queue · Relationship specialist | Bức tranh tài sản · Kiểm tra tài sản · Hàng chờ duyệt · Chuyên viên của bạn |
| AI pipeline · AI News Reader / Impact Assessor / Planning Advisor / Client Chat | Chuỗi AI · AI đọc tin / đánh giá tác động / tư vấn kế hoạch / trò chuyện với khách |
| Tin quan trọng bị miss · Tin bị miss | Tin quan trọng bị bỏ sót · Tin bị bỏ sót |

The tagline “Financial Intelligence for a Better Tomorrow” is the brand line and stays.

## Verification

- The 134-shot crawl again on the branch (served from the worktree on :8050 with a copy of the live data): 0 errors,
  0 error panels, 0 horizontal page scroll, as before; every off-screen text left is inside a container that scrolls on
  purpose (tab strips, the client's strip, tables on a phone).
- Lint: `ruff check`, `ruff format --check` on the Python changed.
- Suites: recorded in `docs/brd/testing/regression_coverage.md`.
