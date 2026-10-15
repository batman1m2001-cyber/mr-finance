# FEAT-34 — Header search and notifications

| | |
|---|---|
| Type | Extension (owner request, UI redesign R1), built 2026-10-16 |
| Requirements | OWN-UI-03; keeps BRD flow 2 (the client sees no headline), ADR-0008 |
| Users | Every role |
| Entry points | The header of every page: the search box (“/” focuses it) and the bell; `POST /api/search {q, role, client_id?, scope?}` |
| Status | see [traceability](../requirements/requirements_traceability.md) §5 |

## Purpose
Find anything the role can already open — a page, a holding, a goal, a client, an event, a news item, a research
note — from one box, and see what needs attention without opening a page.

## Behaviour
1. **Pages** are matched in the browser from the shell's menu of the current role (label and section).
2. **Records** come from `search_flow`: consolidate the picked client → goals → `find` (`src/search/ops.py`).
   Matching folds accents (“vang” finds “Vàng”); every query word must start a word of the record; records where
   a query word is a whole word rank first (an RM typing “khoa” gets the client Nguyễn Minh Khoa before
   “Tài khoản”). At most six hits per kind.

   | Role | Kinds | Opens |
   |---|---|---|
   | Khách hàng | holdings, goals, events **by type label only** | Tài sản, Kế hoạch, Tác động thị trường |
   | RM | holdings, goals, clients, events | the client's pages; a client hit switches the picked client |
   | CIO | events, news (every status), research | the event, Hộp tin, Nghiên cứu |
   | Tuân thủ | held news, research | Tin bị giữ, Nghiên cứu |

3. **Keyboard**: “/” focuses the box; ↑/↓ move; Enter opens the selected (or first) hit; Esc closes.
4. **Bell**: the client's or RM's “Điều đáng chú ý” (`POST /api/feed`, the same items as on Toàn cảnh), the CIO's
   new news (`GET /api/news/inbox`), Compliance's held news. The count is on the bell; a click lists them; an item
   opens its evidence page and marks the item there ([FEAT-33](FEAT-33-living-interface.md)). It reloads when the
   role, client or scope changes.

## Rules
- Only records another page of the same role already shows; the client is never matched on a headline (an event
  is found by its type label, and shows only that).
- A query longer than 80 characters or an unknown role is refused; one character returns nothing.

## Implementation
`src/search/{ops,graph}.py`, service `search` in `app/main.py`; `web/header.js` (mounted by `web/shell.js`,
which gives it the role, client, scope, menu and `go`); markup in `web/index.html`; styles at the top of
`web/core/tokens.css`.

## Acceptance and tests
`tests/test_search.py` (5): holdings and goals with their pages, accent-insensitive; whole words first and the RM
finds clients; the client never matches a headline while staff do; news and research stay with staff; refusals
and the endpoint. `tests/ui/test_header.py` (2): “/” → type → Enter opens a holding, a page hit, an RM's client
hit switches the client; the bell's count equals the feed's items and an item opens.

## Limitations
- Search runs a consolidation per query (debounced 180 ms); fine for the demo's seven people, not measured at scale.
- The CIO's bell lists new news only, not events waiting for a decision.
