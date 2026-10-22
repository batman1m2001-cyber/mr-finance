# Design system

Layer C. The canonical source is the code: [`web/core/tokens.css`](../../../web/core/tokens.css) (tokens, both
themes, base components), [`web/core/core.js`](../../../web/core/core.js) (formatters, states, badges, drawer, toast)
and [`web/charts/charts.js`](../../../web/charts/charts.js) (charts). This page explains them; when they disagree,
the code wins and this page is corrected.

## Principles

- **One figure first.** A page leads with the number that matters (net worth, the 3-month impact, the families to
  call) and its one-sentence reading; details are folded below (`<details class="more">`).
- **Say what is assumed.** Mock data, assumed parameters and AI involvement are labelled where the number is
  (`badge assumed` “giả định”, “mô phỏng”, “AI hỗ trợ · CIO duyệt”), and in the footer.
- **Colour has a job.** Gain/loss, status, identity of a series, AI vs human — never decoration.
- **Vietnamese UI, VND as people say it** (“24,5 tỷ”, “−726 triệu”, `vnd()`), percentages with a sign when they are
  changes (`pct(x, true)`), “—” for unavailable.

## Themes

The Techcombank-ecosystem look (2026-10-21): black, white and greys, light for everyone unless the person picks dark
(◐, stored as `mf.theme`). Red is Techcombank's and is used sparingly, because it reads as an error:
- `--brand-red`: the logo and the thin mark of where you are;
- `--cta` (business feedback 4, after Techcombank Private's pages, whose one red element is Đăng nhập; OWN-WN-11):
  the main action only — a primary button, Hỏi trợ lý, the bell's count. White words on it clear 4.5:1 (#d71920
  light, #e31b23 dark). Tabs, links, selections and focus stay black (`--accent`); nothing larger is red.

## Tokens (light → dark)

| Group | Tokens | Use |
|---|---|---|
| Surfaces | `--plane` #f4f4f5, `--surface` white, `--surface-2`, `--surface-3` | page, cards, nested blocks and tracks |
| Ink | `--ink` `--ink-2` `--muted` | text levels; every text colour ≥ 4.5:1 on its surface in both themes |
| Lines | `--hair` (card borders), `--axis` (inputs, chart axes), `--ring` | |
| Accent | `--accent` #141414 `--accent-soft` `--brand` `--hero` | links, current tab, selections, focus, hero figure |
| Red | `--brand-red` #e31b23; `--cta` #d71920 `--cta-ink` `--cta-hover` | the logo and where you are; the main action (see Themes) |
| Series | `--s1`…`--s8`, `--other` | categorical series in fixed order; asset classes have fixed colours (`CLASS_COLOR`) |
| Status | `--good` `--warning` `--serious` `--critical` (+ `-soft`) | statuses with a label, never colour alone |
| Money | `--up` `--down` `--flat`; `--in` `--out` | gain/loss; cash in/out |
| Semantics from the BRD figures | `--ai` (blue), `--human` (orange), `--data` (grey) | AI step, human checkpoint, client data |
| Band | `--band` `--band-2` | fan-chart band, focus halo |
| Elevation | `--shadow` (cards), `--shadow-pop` (menus, popovers) | |
| Shape, space | `--radius` 16 px, `--radius-s` 10 px; `--s-1`…`--s-7` (4–48 px) | |
| Motion | `--dur-1` `--dur-2` `--hold` `--ease-out` | see Motion below |

## Shell

Row 1: logo and “OneWealth / Financial Intelligence for a Better Tomorrow”, the search box (“/”), the client picker,
the Cá nhân / Gia đình switch, the bell with its count, the theme toggle. Row 2: the role's tabs, and on the right
“Xem với vai trò” with the demo role switcher. Below 760 px the header scrolls away instead of staying pinned and the
tagline hides ([FEAT-34](../features/FEAT-34-header-search-and-notifications.md)). Since 2026-10-20 a phone's header
is one row from 360 px (two for the RM, whose Cá nhân / Gia đình goes under the client picker): search sits behind a
search button and opens full width, focused; the name row (name, title, Bộ nhớ, Đăng xuất, the theme switch) is a
popover behind the person's initials. The page starts about 76 px higher than before ([UX_FIXES_1020_PLAN.md](../../UX_FIXES_1020_PLAN.md)).

A sheet's header (a desk's page over the desk) keeps the back link, the title and ✕ on one line: the title takes an
ellipsis before anything wraps, and the group's tabs take only the room left, scrolling with a fade on the side that
has more, the current tab scrolled into view.

## Components

| Component | Where defined | Notes |
|---|---|---|
| Panel, grid `cols` / `c4` `c8` `c12` | tokens.css | 12-column grid, one column below 900 px; panel title 14.5 px, ink, sentence case |
| Hero (`hero-panel`, `.hero`, `.eyebrow`, `.takeaway`, `.footnote`) | tokens.css | the one figure of a page; the eyebrow is sentence case |
| Icons `icon(name, {size, label})`, `CLASS_ICON`, `FLOW_ICON` | core/icons.js | 59 Lucide icons inlined (ISC), decorative unless labelled |
| Icon chip `.ic-chip` (`sm`, `lg`; `--tone`) | tokens.css | a tinted square behind an icon (asset class, category, kind) |
| Pill `.pill` (`good` `warn` `bad` `ai`; `--tone`) | tokens.css | short status or impact label |
| Small charts `sparkBars`, `ring`, `donut`, `gauge`, `progress` | charts/mini.js | from given numbers only, each with an aria-label |
| Badges: `good` `warn` `bad` `human` `assumed`; `severity()`, `runBadge()`, `viewBadge()` | core.js | statuses always with text |
| Controls: selects, inputs, checkboxes on new pages | tokens.css | one look; focus halo in `--band` |
| Popover `.pop`, `.pop-item`, `.pop-head` | tokens.css | search results, bell |
| Table `.table`, `.scrollx` | tokens.css | horizontal scroll inside the table on phones, never the page |
| States `loading()`, `empty(title, hint)`, `failed(e)` | core.js | skeleton with `aria-busy`; empty with a hint of what will appear; error with `role="alert"` |
| Drawer `drawer(title, html)`, toast `toast(msg)` | core.js | dialog with Esc; the result of an action, including refusals |
| A figure with its formula `n(text, metric, inputs)`, `nAttrs` (SVG), `howOn` and `opts.metric` (charts); `data-quote`, `data-axis`, `data-explains` | core.js, tokens.css `.how-n`, `.num-svg`, `.how` | every money or percent figure (NFR-11, G1): a dotted underline on hover, focusable, Enter or a click opens “Cách tính” — what it is, the formula, the inputs, the code for staff. It is a `span role=button`, never a nested button; a row that opens something else still does, from anywhere but the figure |
| Charts: `fan`, `diverging`, `probBar`, `heat`, `spark`, `moves`, `sankey`, `hover` | charts/charts.js | SVG, no library |
| Copilot button | tokens.css, copilot.js | a 56 px round mark with the sparkles icon; its states are in Motion |

Since UI redesign R3 every page uses these tokens and components; the old `web/app.css` and `web/app.js` are gone
(ADR-0019).

## Data visualisation rules (applied)

The categorical palette was validated with the dataviz `validate_palette.js` (light: passes with direct labels or
a table; dark: passes on the indigo surface). Rules followed: one axis; colour follows the entity, not its rank;
diverging bars around zero for contributions; a legend for ≥ 2 series; tooltips on marks; text in ink tokens, not
series colours; P5 dashed as “reference only”.

## Motion

Owner request B-01 ([FEAT-33](../features/FEAT-33-living-interface.md)); rules in the last block of `tokens.css`,
driven by [`web/motion.js`](../../../web/motion.js) and `web/copilot.js`.

- **Only for a change of state**: a request sent, its outcome, something entering, the evidence an answer read, a
  chosen graph path. Nothing moves at rest with the Copilot closed (measured: 0 animations, 0 style or layout work).
- **Only `transform` and `opacity`** (checked by `tests/test_living_interface.py`); no library, no JS loop.
- **Tokens**: `--dur-1` 160 ms (a control answers), `--dur-2` 240 ms (something enters), `--hold` 2.6 s (a mark
  stays), `--ease-out` `cubic-bezier(.2, .8, .2, 1)`.
- **Classes**: `data-state` on `.cp-panel` (idle, busy, ok, error, pending); `.cp-in` (enter);
  `.cp-dots` (thinking); `.mf-focus` (ring) and `svg.mf-dim` (dim the other marks); `.mf-lit` with `--i` (graph
  path, one column per 70 ms); `html[data-hidden]` pauses all animation.
- **Colours** reuse the status tokens: `--good` ready/ok, `--accent` working, `--critical` error, `--warning`
  pending; the ring is `--accent` with a `--band` halo.
- **Flow dots** (Sankey, R2): a picked band sends three dots along itself three times, then stops — Web Animations
  on `transform`, registered with `motion.js::track` so a hidden tab pauses them.
- **Reduced motion**: no animation or transition; states stay as colour and text; a mark is a still outline.

## Responsive

Breakpoints at 900 px (grid to one column) and 640 px (tighter header, short chart labels). Every current route
was captured at 390 px with no horizontal page scroll (2026-10-15).

## Accessibility — what is in place, what is not

In place: `aria-pressed` on the role and scope toggles, `aria-current` on nav, `role="dialog"` + `aria-modal` on the
drawer with Esc, `aria-busy` on loading and on the Copilot while it works, `role="alert"` on errors, reduced-motion stops the skeleton shimmer and all motion (FEAT-33), text
contrast ≥ 4.5:1. Not verified: full keyboard paths through charts (tooltips are hover-only), screen-reader
reading of the SVG charts (no table alternative on SCR-CL-05's fan chart), focus return after the drawer closes.
