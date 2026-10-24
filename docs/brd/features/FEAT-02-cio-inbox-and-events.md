# FEAT-02 — CIO inbox and events

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-FR-103, BRD-FR-104, BRD-FR-105, BRD-BR-04, BRD-RULE-WF-02, BRD-RULE-DATA-08 |
| Users | CIO (inbox, grouping); Compliance (release of held items) |
| Entry points | [SCR-CIO-01 Hộp tin](../ux/screens/cio.md#scr-cio-01--hộp-tin-inbox), [SCR-CIO-02](../ux/screens/cio.md#scr-cio-02--sự-kiện--nhận-định-events), [SCR-CMP-01](../ux/screens/compliance.md#scr-cmp-01--tin-bị-giữ-held-news) |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
Let the CIO turn many news items about the same happening into one **event**, the unit the CIO agent analyses,
and keep anything naming a restricted organisation out of the process until Compliance releases it.

## Preconditions and permissions
- Grouping: role `cio`, checked on the server (`src/events/ops.py`).
- Dismissing: role `cio`; releasing a held item: role `compliance`, both checked on the server
  (`src/news/ops.py`; DEF-03 fixed 2026-10-15).

## Behaviour
1. **Inbox** (`GET /api/news/inbox`): newest first; filters by source, kind, status, relevance, time window and
   words; a feed-health strip (last run per source).
2. **Dismiss** (`POST /api/news/dismiss {ids, by, note?}`): items leave the inbox, recorded with who and why.
3. **Group** (`POST /api/events {news_ids, title?, by}`): one or more kept items → event `EV-2026-nnnn`. Items
   that did not pass the gates, unreleased research, or unknown ids are refused (FR-104, FR-203). The event
   records its news, who grouped it, timestamps, and the list of **held** items it contains.
4. **Hold and release** (`POST /api/news/release {item_id, by, note}`): Compliance clears a held item with a
   note; the event's `held` list shrinks. While an event holds anything, its views cannot be approved
   (approval condition *g*, FEAT-06).

## States
News item status: `new` → `grouped` | `dismissed` (`refused` items never enter); the `held` flag is cleared by
Compliance's release. Event: `status` and `held[]`.

## Implementation
`src/news/ops.py` (`dismiss`, `release`), `src/news/graph.py` (`dismiss_flow`, `release_flow`),
`src/events/{ops,graph,store}.py` (`event_flow`), reads in `app/web.py` (`news_inbox`, `events_list`, `event_one`).

## Acceptance and tests
`tests/test_news.py::test_the_inbox_filters_and_dismiss`, `::test_the_inbox_endpoint_returns_items_and_feed_health`,
`::test_an_item_naming_the_restricted_list_is_held_until_the_cio_releases_it`;
`tests/test_views.py::test_an_event_groups_news_and_a_restricted_mention_holds_it`.

## Limitations
- Event types are a hint from keywords, chosen again by the CIO agent; there is no manual event-type field.
- The UI measurement of U1: the inbox page went from 1,841 to 257 words above the list (news plan §9).
