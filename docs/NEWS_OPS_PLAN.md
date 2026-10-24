# News sources and collection figures (2026-10-25) — plan

**Status: done (N1–N3), 2026-10-25.** OWN-NO-01…03 implemented_verified (tests/ui/test_sources_ui.py,
tests/test_news_sources.py, tests/test_agent_eval.py).

The owner asked whether the news sources can be managed (added, removed, configured) and whether the system already
measures what the business asked: how much news is collected each day, in how many minutes, when, from how many
sources, how much on real estate, stocks and policy, how much of it touched a portfolio; and how accurate the impact
agent is, its recall, the money its right and wrong calls made and lost, by asset group.

The check (2026-10-25, on a copy of the live state) found most of it in place: the white list is a versioned
configuration (`news_sources`, Admin's), each run keeps its sources, start and end, the days split by the four groups
(Thử nghiệm hằng ngày, view A), and view B scores the agent: precision, recall, event recall, simulated VND for the
right, wrong and missed calls, overall and by the four groups. Three gaps, closed here. Branch `feat/news-ops`, merged
into `main`, :8030 restarted.

## N1 · Nguồn tin: a page to manage the sources

- Admin's rail gets **Nguồn tin** (`#/admin/nguon-tin`, page `sources`): one row per source — outlet, section,
  domestic or international, on or off, its last 7 days (runs, failures, items read, the last error) — and a form to
  add one (outlet, section, url, kind).
- Each row: **Thử** reads the feed now and says how many items it has and the newest title, or why it failed; **Tắt /
  Bật** flips `approved`; **Xoá** removes it; the url and the names can be edited in place.
- The changes are kept on the page until **Gửi đề xuất**, which proposes the whole list as a new version of
  `news_sources` (the existing `/api/config/propose`, its checks); an Admin approves it there or on Cấu hình
  (`/api/config/decide`), and the next run uses it. The history stays on Cấu hình.
- `GET /api/news/sources` (Admin): the list in force, the proposal waiting, each source's health. `GET
  /api/news/sources/test?url=` (Admin): https only, not to a private or local address, the fetch's own timeout and
  size cap, nothing kept.

## N2 · The day's collection time

- `monitor.days` keeps, per day, the total seconds the runs took (`duration_s_total`, over the runs that recorded it,
  with their count) and the first and last run's time. View A's table shows **Thời gian lấy** (minutes) and **Từ – đến**.

## N3 · News that reached a portfolio

- A news item reached a portfolio when its event has an application run the RMs see (`EFFECTIVE`, `SUPERSEDED`,
  `WITHDRAWN`) with at least one family whose expected 3-month change is not zero. `monitor.days` counts them by the
  day they were collected (`portfolio`), and the families they reached (`portfolio_families`); view A shows **Tác
  động danh mục** beside Liên quan, with its “?” saying how it is counted (it grows after the day, as views are
  approved).

## Gate

- Tests for each: the page's add / off / delete / test / propose / approve in the browser, the test read's refusals
  (http, a private address), the two monitor figures on a seeded day; `test_access` covers the new reads;
  `check_brd_docs` green.
- Screenshots desktop and phone; merged into `main`, :8030 restarted, Nguồn tin and view A checked as Admin.
