# FEAT-33 — Living Interface

| | |
|---|---|
| Type | Extension (owner request, backlog B-01), built 2026-10-16 |
| Requirements | OWN-MOTION-01…07; touches KIT-UX-06; keeps KIT-COPILOT-01…05 and ADR-0012 |
| Users | Every role |
| Entry points | The Copilot button and panel ([SCR-CL-10](../ux/screens/client.md#scr-cl-10--onewealth-copilot-panel-all-roles)) on every page; the pages an answer reads from: SCR-CL-08 Toàn cảnh, SCR-CL-09 graph, Tác động tin, SCR-RM-01 Hôm nay |
| Status | see [traceability](../requirements/requirements_traceability.md) §5 |

## Purpose
The page answers the assistant: it shows that the Copilot is ready, working, done or stopped, and when an answer
uses a number from the page, it points at that number. Nothing moves unless something happened.

## Behaviour
1. **States** (`web/copilot.js`, `data-state` on the button and the panel), each set only by the request itself:

   | State | Set when | What changes |
   |---|---|---|
   | idle | start; 1.6 s after ok; cancel; close after an error | green status dot; while the panel is open, a slow ripple from it every 4.8 s (presence) |
   | busy | the POST is sent | the button's ✦ breathes; three dots and “Đang xử lý…” in the panel; `aria-busy` on the list |
   | ok | the answer's status is ok | ✦ becomes ✓ for 1.6 s; green dot |
   | error | failed, forbidden, or the call failed | red dot on the button and panel; red edge on the answer; kept until the next question or close |
   | pending | a write waits for Xác nhận | amber dot on the button and panel until confirm or cancel |

   The thinking state shows no steps or percentage: the server does not report steps, so none are invented.
2. **Evidence highlight.** A successful answer carries `focus`: keys of the page elements it was read from,
   computed by our code from the tool's own result (never by the model). Pages tag elements with
   `data-focus="key …"`. `web/motion.js::focus(keys)` gives each match a ring that fades in, holds and fades out
   over 2.6 s (`.mf-focus`), and dims the other marks of an SVG chart (`svg.mf-dim`). It scrolls the first mark
   into view only if it is off screen.

   | Tool | Keys | Marked on |
   |---|---|---|
   | tong_quan | `kpi:net_worth`, `kpi:liquidity`, `kpi:risk` | the three KPI tiles of Toàn cảnh |
   | dong_tien | `flow:<month>`, `flow:<month>:out:<category>` | the Dòng tiền panel; the largest spending row and Sankey band of that month only |
   | chu_y | the feed items' `key` (first three) | those items of “Điều đáng chú ý” |
   | tac_dong | `event:<id>` of the largest event | its item on Tác động tin; on the graph, its path lights column by column (as a click would select it), and in the phone list its edges |
   | hom_nay | `family:<id>` | the families' rows on Hôm nay |

   On the current page the marks show at once, and the answer offers **Chỉ trên trang** to show them again. When
   they are on another page, **Mở … →** opens it and the marks show once it has rendered (the shell sends
   `mf:page`). On a phone the panel covers the page, so the marks wait until it closes.
3. **Entrances.** The panel and each new message rise 6 px and fade in over 240 ms; older messages do not move.
4. **Flow dots** (UI redesign R2): picking a Sankey band sends three dots along it three times, then they are
   removed — Web Animations on `transform`, tracked by `motion.js::track` (paused while the tab is hidden), not
   started under reduced motion ([FEAT-29](FEAT-29-financial-pulse-wealth-map-money-flow.md)).
5. **Inactive.** While the tab is hidden, every animation is paused (`html[data-hidden]`) and a highlight that
   arrives then waits until the tab is shown. With the panel closed and nothing happening, nothing runs.
6. **Reduced motion** (`prefers-reduced-motion: reduce`): no animation or transition. States stay as colour and
   text, the highlight is a still outline for the same 2.6 s, and scrolling is instant.

## Rules and validation
- Only `transform` and `opacity` are animated (the older skeleton shimmer animates `background-position`).
  `tests/test_living_interface.py` parses every `@keyframes` and every B-01 `transition` to check this.
- No library and no JS loop: one `setTimeout` clears a highlight, one `requestAnimationFrame` waits for a page's
  layout; there is no `setInterval`.
- A key that is not on the page marks nothing. A failed or forbidden answer has no `focus`.

## API and data
- `POST /api/copilot` → `copilot.focus: [key]` on ok answers ([api_reference](../architecture/api_reference.md)).
- `POST /api/feed` → each item has `key` (`feed:` + its evidence values), stable across calls.
- No change to what the router sees: `focus` is built after the tool ran, from its result, and goes to the
  browser only (ADR-0012 holds; `tests/test_copilot.py` unchanged and green).

## Implementation
`web/motion.js` (new: `focus`, `after`, `present`, `start`); `web/copilot.js` (states, thinking row, entrances,
Chỉ trên trang); `web/shell.js` (starts motion, sends `mf:page`); `data-focus` in `web/pages/pulse.js`,
`impact.js`, `today.js`, `graph.js` (and the path fade) and `web/charts/charts.js` (Sankey bands);
`src/copilot/tools.py` and `ops.py` (`focus`); `src/feed/ops.py` (`key`); motion tokens and rules at the end of
`web/core/tokens.css` ([design system](../ux/design_system.md#motion)).

## Acceptance and tests
`tests/test_living_interface.py`: answers name the elements they were read from (net worth, a month's flow, the
largest event, the feed's first three items); failures mark nothing; every key prefix has a page that renders it;
only transform and opacity animate; hidden tabs pause, reduced motion stops, no JS loop. Browser run on the dev
server (2026-10-16), desktop 1440 px and phone 390 px: busy, answer with marks, phone marks after close, flow row
and band, forbidden answer, graph path and phone list; no page error, no horizontal scroll
([screenshots](../assets/README.md)).

**Performance, measured** (Chromium 125 headless via CDP `Performance.getMetrics`, median of 5 runs, Toàn cảnh,
client C01, keyword router; before = main at 2b8a6c2):

| Window | Before | After |
|---|---|---|
| 5 s at rest, panel closed | 1.5 ms main thread, 0 style recalcs, 0 layouts, 0 animations | the same |
| 5 s at rest, panel open (idle ripple) | 9.2 ms, 0 recalcs | 18.2 ms, 10 recalcs, 0 layouts |
| 2.5 s waiting on a slow answer (busy) | 5.6 ms, 0 recalcs | 20.0 ms, 11 recalcs, 0 layouts |
| One question, answer + 3 s (marks and idle ripple included) | 57 ms, 6 recalcs, 5 layouts | 144 ms, 40 recalcs, 11 layouts (80 ms under reduced motion, which has neither) |
| Long tasks (> 50 ms) during a question | none | none |
| Running animations when the tab is hidden | — | all paused |

The added cost is spread over seconds (at most about 8 ms per second while busy, under 2 ms per second at rest
with the panel open) and nothing runs per frame on the main thread. The header dot's own breathing was dropped after the first measurement, so busy shows two moving
things, not three.

## Limitations
- The goals answer (muc_tieu) and the CIO/Compliance counts mark nothing: the legacy planning page has no stable
  element per goal, and a count has no single element.
- The highlight may sit behind the open panel on desktop (the panel covers the right 400 px); Chỉ trên trang shows
  it again after the panel is moved or closed.
- The thinking state is one state: the server answers in one response, so routing and the tool run are not shown
  separately.
- `web/charts/charts.js` is imported without a version query; a browser that cached the old file shows no band
  mark until it revalidates (pre-existing for all module imports below the entry points).
- Behaviour in the browser is checked by a driven run and screenshots; there is no automated UI test in the suite.
