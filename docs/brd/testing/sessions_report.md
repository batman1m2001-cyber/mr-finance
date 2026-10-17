# Assistant sessions — verification (2026-10-17)

Owner request [`2026-10-17_assistant_sessions.md`](../sources/owner_requests/2026-10-17_assistant_sessions.md),
OWN-SS-01…08, plan [`SESSIONS_PLAN.md`](../../SESSIONS_PLAN.md), FEAT-37. Experiment branch `exp/graph-workspace`.

## What was there, what was built

| | Before | Now |
|---|---|---|
| Sessions | list, open, delete | + rename, archive, restore; search and day groups in the panel |
| Title | first 80 characters of the question | ≤ 7 words by the model after turns 1 and 4 and after a compaction; the person's name kept |
| Goal, summary | — | per session, shown in the session bar (“Mục tiêu”, “Tóm tắt phiên”) |
| A turn | written at its end | written at its start, steps as they end; followed after a reload |
| Compaction | upstream notes | seven fixed sections, kept on the session, read-back tool `doc_lai_phien` |
| New Chat | “+ Mới” link | “Trò chuyện mới” button beside the session's name |

## Measured

- **A reload mid-answer** (experiment server, real model, two tools; the stream was closed after the first tool
  ended): the server finished the turn. Both tools ran, and the answer and its cost (US$0.0013) were kept. The
  turn read `running` 3 s after the cut and `ok` afterwards. So decision 2 follows the turn after a reload rather
  than marking it cut.
- **Titles on the real model** (three sessions): “Tài sản và dòng tiền tháng 9”, “Tài sản và chi tiêu tháng 10”; each
  with a one-sentence goal. US$0.0001 a title, 1.3–2.4 s, after the answer.
- **Paid calls in this phase**: 2 probe turns (US$0.0027) and 3 titles (US$0.0003). Total US$0.003.

## Tests

- `tests/test_assistant_sessions.py`, 12 tests:
  - owner-only rename, archive and restore;
  - cut, stale and finished turns;
  - two signed-in customers over HTTP;
  - titles: once, refined, the person's name kept, nothing sent in template mode, a broken answer ignored;
  - compaction in seven sections, continued from;
  - read-back limited to the session;
  - upstream's prompt shape guarded.
- `tests/ui/test_sessions_ui.py`, 2 browser tests:
  - named, reloaded, renamed, New Chat, search, archive and restore;
  - a running turn followed to its answer on a phone, and a dead one marked “Bị ngắt”.
- Existing tests adapted: `tests/ui/test_agent_map_ui.py` (the history's new markup).
- Full suite: 730 passed, 1 skipped (15 min 48 s).

## Screens

- [Session bar](../assets/current_ui/SCR-CL-10-session_desktop-dark.jpg)
- [History, desktop](../assets/current_ui/SCR-CL-10-history_desktop-dark.jpg)
- [History, phone](../assets/current_ui/SCR-CL-10-history_phone-dark.jpg)

## Gaps

- A turn cut by a server stop is not resumed; the person asks again (the panel shows what ran).
- Search in the panel matches titles and goals; the words said are searched on Bộ nhớ (the text is sealed, FEAT-37
  Limitations).
- Flaky, existing: `tests/test_agent_map.py::test_the_consolidator_state_matches_what_its_traces_report` failed once
  when run after the assistant tests (a schema `KeyError` in the consolidator's job). It passed alone, in the same
  order again, and in the full suite. It is not from this change.
