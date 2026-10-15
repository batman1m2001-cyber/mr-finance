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

Light (white surfaces, ink text) and dark (deep indigo, lavender accent, large hero figure — the look the team
chose on 2026-10-15). The theme follows the OS until the user toggles it (◐, stored as `mf.theme`); dark tokens are
defined for `prefers-color-scheme: dark` unless `data-theme="light"`, and for `data-theme="dark"`.

## Tokens (light → dark)

| Group | Tokens | Use |
|---|---|---|
| Surfaces | `--plane` `--surface` `--surface-2` `--surface-3` | page, cards, nested blocks |
| Ink | `--ink` `--ink-2` `--muted` | text levels; every text colour ≥ 4.5:1 on its surface in both themes |
| Lines | `--hair` `--axis` `--ring` | borders, chart axes, focus ring |
| Accent | `--accent` `--accent-soft` `--brand` `--hero` | actions, current nav, hero figure |
| Series | `--s1`…`--s8`, `--other` | categorical series in fixed order (validated palette; asset classes have fixed colours in `CLASS_COLOR`) |
| Status | `--good` `--warning` `--serious` `--critical` (+ `-soft`) | statuses with a label, never colour alone |
| Money | `--up` `--down` `--flat`; `--in` `--out` | gain/loss; cash in/out |
| Semantics from the BRD figures | `--ai` (blue), `--human` (orange), `--data` (grey) | AI step, human checkpoint, client data |
| Band | `--band` `--band-2` | P10–P90 band of the fan chart |
| Space, shape | `--s-1`…`--s-7` (4–48 px), `--radius` 14 px, `--radius-s` 9 px, `--shadow` | |
| Type | `--font` system UI stack | |

## Components (new pages; classes scoped to `:is(#page-new, .drawer)`)

| Component | Where defined | Notes |
|---|---|---|
| Panel, grid `cols` / `c4` `c8` `c12` | tokens.css | 12-column grid, one column below 900 px |
| Hero (`hero-panel`, `.hero`, `.eyebrow`, `.takeaway`, `.footnote`) | tokens.css | the one figure of a page |
| Badges: `good` `warn` `bad` `human` `assumed`; `severity()`, `runBadge()`, `viewBadge()` | core.js | statuses always with text |
| Table `.table`, `.scrollx` | tokens.css | horizontal scroll inside the table on phones, never the page |
| States `loading()`, `empty(title, hint)`, `failed(e)` | core.js | skeleton with `aria-busy`; empty with a hint of what will appear; error with `role="alert"` |
| Drawer `drawer(title, html)` | core.js | dialog, Esc/backdrop close, focus on close |
| Toast `toast(msg)` | core.js | the result of an action, including server refusals |
| Charts: `fan` (band over horizons), `diverging` (contributions), `probBar` (branch probabilities), `heat` (families × factors), `spark`, `moves` (factor moves), `hover` tooltips | charts.js | SVG, no library |

The legacy pages (`web/app.css`, `web/app.js`) use their own classes but read the same tokens, so both generations
share colours and themes ([ADR-0013](../decisions/ADR-0013-wrap-the-legacy-pages-in-the-new-shell.md)).

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
- **Reduced motion**: no animation or transition; states stay as colour and text; a mark is a still outline.

## Responsive

Breakpoints at 900 px (grid to one column) and 640 px (tighter header, short chart labels). Every current route
was captured at 390 px with no horizontal page scroll (2026-10-15).

## Accessibility — what is in place, what is not

In place: `aria-pressed` on the role and scope toggles, `aria-current` on nav, `role="dialog"` + `aria-modal` on the
drawer with Esc, `aria-busy` on loading and on the Copilot while it works, `role="alert"` on errors, reduced-motion stops the skeleton shimmer and all motion (FEAT-33), text
contrast ≥ 4.5:1. Not verified: full keyboard paths through charts (tooltips are hover-only), screen-reader
reading of the SVG charts (no table alternative on SCR-CL-05's fan chart), focus return after the drawer closes.
