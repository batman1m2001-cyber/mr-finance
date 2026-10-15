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

Light first, as on the kit's concept board (owner, 2026-10-16; [UI redesign plan](../../UI_REDESIGN_PLAN.md) R-D1):
a pale lavender-grey plane, white cards with a soft shadow, 16 px corners, sentence-case card titles, small tinted
icon chips, one indigo accent. Dark (deep indigo, lavender accent) is kept from 2026-10-15. The theme follows the OS
until the user toggles it (◐, stored as `mf.theme`).

## Tokens (light → dark)

| Group | Tokens | Use |
|---|---|---|
| Surfaces | `--plane` #f6f6fb, `--surface` white, `--surface-2`, `--surface-3` | page, cards, nested blocks and tracks |
| Ink | `--ink` `--ink-2` `--muted` | text levels; every text colour ≥ 4.5:1 on its surface in both themes |
| Lines | `--hair` (card borders), `--axis` (inputs, chart axes), `--ring` | |
| Accent | `--accent` #5b47d6 `--accent-soft` `--brand` `--hero` | actions, current tab, hero figure; the logo and Copilot button use #7a63f0 → #4a36c4 |
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
“Xem với vai trò” with the demo role switcher. Below 760 px the header scrolls away instead of staying pinned, the
tagline hides, search takes its own row ([FEAT-34](../features/FEAT-34-header-search-and-notifications.md)).

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
- **Classes**: `data-state` on `.cp-fab` / `.cp-panel` (idle, busy, ok, error, pending); `.cp-in` (enter);
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
