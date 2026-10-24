# OneWealth — The assistant reads the data itself: plan

**Status: done** (D0–D5, 2026-10-24; owner, 2026-10-24: “can you think a way to give assistant access to our db, and knowledge to
flexibly, dynamically answer user” → “go”).
- **D0 done:** [ADR-0040](brd/decisions/ADR-0040-the-assistant-queries-role-scoped-read-only-views.md); OWN-DA-01…08
  in docs/brd (planned); BRD checker 0 errors.
- **D1 done:** `news.store.count` (one where-clause with `inbox`), `control.alerts.counts`, search's `total`; the
  inbox page, the bell, Hệ thống, the CIO desk, the alerts, search and held-news tools all say counted totals. On a
  copy of the live data the inbox page reads “1.417 tin chờ xử lý” and “40 / 1.417” (desktop and phone). Gate:
  `tests/test_totals.py`, 6 tests, each seeding past the old cap (310 > 300, 5,003 > 5,000, 53 > 50, 260 > 200).
  Found beyond §2: the held-news tool read `inbox()`'s first 200; Hệ thống counted open alerts among the last 30;
  the bell asked for 1,000 news to count them. `wealth_store.reviews` has no cap, so the queue tool's total is its
  length (now in its data); no separate count function was needed there.
- **D2 done:** `src/assistant/dataroom.py` (`query`, `truy_van`, not yet in the registry: D4). Gate:
  `tests/test_dataroom.py`, 54 tests. Every adversarial case of §4 is refused, and a refusal names nothing outside
  the room: a real table reads like a missing one. Changed from §3.1–3.2, with evidence:
  - **TEMP tables, not TEMP views.** SQLite tells the authorizer which view a read comes from by name, and a CTE
    named like a view gets that name. A probe on a copy of the live data showed `with tin as (select email from
    main.people) select * from tin` reaching the authorizer as a read of `people.email` from source `tin`, so a
    rule based on the view would leak. Instead, each query copies the room tables its SQL names (and the role
    holds) into TEMP before the authorizer is set. The authorizer then allows reads of those tables and of nothing
    in `main`. Building `tin` (1,481 rows) took 30 ms; a family table about 2 ms plus the served read (about
    50–250 ms for an RM's three households).
  - **Family data comes from the served reads**, not `json_extract` on the real tables. Those columns can be sealed
    (`control.crypto`), and the served reads already apply `people.auth` (`desk.reads.book_of`, `auth.client_for`,
    `auth.visible`). `tac_dong_gia_dinh` carries a family's totals per run, never its holdings.
  - **Functions:** §3.2's list plus `upper`, `length`, `substr`, `instr`, `trim`, `replace`, `ifnull`, `iif`,
    `nullif`, `abs`, `total`, `group_concat`, `datetime`, `julianday`, `json_array_length` and the window
    functions. Also added is `khong_dau(text)`, which strips Vietnamese diacritics, because SQLite's `lower` only
    folds ASCII. Excluded: `printf`/`format`, `randomblob`, `zeroblob`, `load_extension`, `sqlite_*` and
    `json_each` (it reads as a table).
  - **Two SQLite facts handled:**
    - A read of no column, such as `count(*)` over a join, reaches the authorizer without a database name. It is
      allowed for a room table's name only. That is safe because TEMP shadows unqualified names and no real table
      shares a room name (tested).
    - A recursive CTE is denied whether or not the query says `recursive`.
- **D3 done:** `src/assistant/datacatalog.py::catalog(role)`, built from `dataroom.TABLES` (tables, column names and
  types) and `src/assistant/catalog/`: `tables.md` (all 17 tables, 194 columns: meaning, unit, allowed values as the
  stores write them), `rules.md` (Vietnam time, `khong_dau` search, count with `count(*)`), and `cio.md`, `rm.md`,
  `client.md`, `compliance.md` (Admin reads Compliance's) with definitions and 18 / 14 / 13 / 12 examples. Gate:
  `tests/test_datacatalog.py`, 10 tests: a column missing from the docs (or documented and not in the room) fails;
  the codes in `news.STATUSES`, `views.LIFECYCLE`, `apply.run.STATUS_LABEL`, `alerts.KINDS`, `flows.LABELS` and
  `contacts.CHANNELS` are each documented; every example runs in its role's room. On a copy of the live data every
  example runs; the CIO's question of 2026-10-24 reads new 1,419 and grouped 64, and 57 fetched today. Changed from
  §3.3: “bị bác” is `trang_thai = 'REJECTED'` (the code is upper case). The CIO's catalog is about 11,000
  characters; D5 measures what it costs per turn.
- **D4 done:** `truy_van` in `assistant.registry` for the five roles with a room (label “Truy vấn dữ liệu”), its
  description followed by the role's catalog (`Tool.reference`; the docstring path drops line breaks). Three calls a
  turn (`Ctx.queries`). One `assistant.query` audit row per query, refusals included (actor, role, SQL, rows, ms or
  the reason). Each step carries `query` (SQL, total, shown, tables, `as_of`, ms), and the panel shows it under
  “Cách tính”, a closed `<details>` (desktop and phone). With `client_ai` off, `dataroom.template` writes the
  step's text (“Có 1.415 tin.”, one value, or the first 10 rows) and the model sees only its status. Gate:
  `tests/test_assistant_data.py` (8 tests, the 2026-10-24 conversation replayed on a scripted model) and
  `tests/ui/test_copilot_ui.py::test_an_answer_from_the_data_room_shows_how_it_counted_collapsed`. Changed from
  §3.5, with evidence: the rule in the prompt did not make Haiku 5.5 count again. Replaying the CIO's conversation
  on the real model with a copy of the live data, “Sao lại 200? Tôi thấy 1.415 tin chờ xử lý mà.” got “Tôi đã đếm
  lại ngay… 1.420” with **no tool called**, three runs of three (the rule, a stronger rule, and a line at the
  prompt's end). So `turn.disputes` marks a turn whose question names a number the last answer did not say; its
  prompt says so and its first model request carries `tool_choice="required"` (`turn.Copilot`). With it the replay
  counted again (`select count(*) … where trang_thai = 'new'`, 1.420, SQL shown). Its answer still offered a guess
  why a page could differ; D5 grades that. Cost of the replays: 8 turns, 13 requests, US$0.0209. A request with
  the CIO's catalog is about 15,000 input tokens, so a turn of four requests would pass `LIMITS.total_tokens`
  (60,000); D5 measures it.
- **D5 done:** `data/assistant_data_eval.json` (87 conversations, 90 turns: 30 per role, the CIO's chat of
  2026-10-24 first, one dispute per role; gold answers are SQL run in the role's room on the data at run time) and
  `scripts/eval_assistant_data.py` (a copy of the state, the real flow, `usage.cost`; results in
  `evals/assistant_data/results/`, not committed). Grader: `tests/test_eval_data_checker.py`, 14 tests, every
  gold SQL run. Haiku 5.5 on a copy of the live data, all 90 turns:

  | Role | Correct | p50 | p95 | US$ / turn | Input tokens / request |
  |---|---|---|---|---|---|
  | CIO | 29/30 → 30/30 | 3.50 s | 5.55 s | 0.00309 | 14,823 |
  | RM | 30/30 | 3.71 s | 6.12 s | 0.00316 | 14,734 |
  | Client | 30/30 | 4.00 s | 5.23 s | 0.00281 | 12,922 |
  | All | 89/90 (98.9 %) → 90/90 | 3.58 s | 5.30 s | 0.00302 | 14,156 |

  Gate: accuracy ≥ 90 % (each role too), p95 ≤ 6 s overall, ≤ US$0.01 a turn: passed. The 3 disputes were each
  counted again with SQL and none guessed why. The CIO's one miss (cio-20, “Đã chấm điểm bao nhiêu dự báo?”: 20,
  gold 26) was the catalog's: `ket_qua = 'scored'` was also documented as “đã chấm”. The catalog now says `da_cham`
  includes `no_data`; cio-20 re-run passes (20 + 6 = 26). An RM p95 of 6.12 s is over 6 s for that role alone (one
  8.1 s turn, rm-20); the gate is on all turns. A turn is 2.0 requests; the largest took 44,237 input tokens, so
  `LIMITS.total_tokens` (60,000) holds. Changed, with evidence:
  - **Totals in SQL** (`rules.md`): the pilot's client-27 summed 12 rows itself, 1,336,781,000 for the true
    1,385,965,000, and said 111.4 M a month (gold 115.5 M). With the rule it used `avg` and was right.
  - **No guessing why, said in the recount's tool result** (`dataroom.RECOUNTED`, appended when `ctx.recount`).
    With the rule in the system prompt alone, even a stronger one, Haiku counted again and then guessed in 3 of 3
    disputes (“có thể bạn đang nhớ số khác”, “có thể hai gia đình còn lại chưa nằm trong bảng”). With the line
    next to the count: 0 of 3, twice. Pointing the person to where a missing item is added (“bạn có thể bổ sung
    trên trang Tài sản”) is not graded a guess.
  - **Two gold answers were wrong in the pilot** and were fixed (cio-09 asked about titles, cio-20 counts
    `da_cham`); six questions with a tie or two readings were rewritten.

  **Model (§3.6): Haiku 5.5 stays.** It passes the gate, so Sonnet is not needed for the SQL step, and Sonnet
  cannot take it: on OpenRouter Sonnet 5.5 refuses `reasoning: {enabled: false}` (400, “Reasoning is mandatory”),
  and with reasoning on it refuses a forced `tool_choice`, which the recount needs (D4). Measured with reasoning
  `low` on 15 turns (5 per role, no disputes): 15/15, p95 4.93 s, US$0.0593 a turn, 6 × the gate; Haiku on the
  same 15: 15/15, p95 5.02 s, US$0.0031. Sonnet was run on 15 turns, not 90: at US$0.06 a turn, 90 would have
  cost about US$5.3 against the phase's US$1–2. D5's model calls: 216 turns, 433 requests, US$1.60.
  Suite with D5: 1,252 passed, 5 failed; the 5 fail the same way on D4's merge (772556d), so none is this
  plan's: `test_assistant_tools[yeu_cau_tai_khoan]` ×2 (a demo account), `test_security::test_sql_in_the_inputs_is_data`
  (no table `people`), `test_zone::test_the_zones_door_takes_only_a_signed_bundle_of_the_catalogues` and
  `test_agent_map_ui::test_the_map_draws_what_the_endpoint_says_and_opens_a_run`.

## 1. Why: the CIO chat of 2026-10-24

CIO Trần Quang Huy asked how many news items had been fetched. The assistant said **200**; the inbox held
**1,415** new items, with 64 grouped. When he pushed back, it argued with him.

Root cause: the `hop_tin` tool returned `len(news_store.inbox())`, and `inbox()` stops at `limit=200`. The model
had a capped list and nothing else, so it could only repeat the cap.

**Hotfix (shipped, main a956bab, live on :8030):** `news_store.counts()` counts in the database: by status, and
what was fetched since a given time, by source. `hop_tin` answers from it and says what came in today (Vietnam
time). The keyword router sends count questions to it, never to `lay_tin`. Re-run on the real model with a copy
of the live data: “53 tin hôm nay” by source, 1,415 new and 64 grouped (US$0.0017); the follow-up confirmed
1,415 without arguing (US$0.0009). Test: `tests/test_news.py::test_the_assistant_counts_the_inbox_in_the_database_not_a_capped_list`.

The hotfix covers one question. The owner's point is that people will ask many questions no fixed tool foresees
(“tin nào về lãi suất tuần này”, “bao nhiêu nhận định bị bác tháng 10”, “gia đình nào chịu tác động nhiều nhất từ
sự kiện X”). Each one we miss today ends as a wrong number or as “không có công cụ”.

## 2. The same bug elsewhere (audit, 2026-10-24)

Every place where a capped list is shown or said as a total:

| Where | Cap | What a person sees |
|---|---|---|
| `src/desk/reads.py:55`: the CIO desk's “Tin” stage, `news.inbox(status="new", limit=5000)` | 5,000 | Right today (1,415); wrong past 5,000 |
| `web/pages/inbox.js:11`: the inbox page, `limit: "300"`, header “N tin chờ xử lý” from `items.length` | 300 | **Wrong today: says 300 for 1,415** |
| `src/control/alerts.py::for_role(limit=50)`, used by the alerts tool (`actions.py` ~195) | 50 | Wrong past 50 open alerts |
| `src/search/ops.py`: `LIMIT = 6` per kind; `actions.py:100` says “N kết quả” | 6 | “6 kết quả” when there are more |
| search ops call `news.inbox(limit=5000)` | 5,000 | Silent beyond 5,000 |
| `contacts.recent(limit=10)` | 10 | Fine: worded “gần nhất” |
| `events.listing`, `wealth_store.reviews`, `apply_run.runs` | none | Fine |

**Rule from here on:** a number shown or said as a total comes from a count in the database (one shared function
for the page and the assistant), never from the length of a page of rows. A page of rows says “50 / 1.415”.

## 3. Design: a governed, read-only data room

The model gets one new tool, `truy_van`. It writes a SQL `select` against a **catalog** of views made for its
role and person. The tool runs the query on a connection that cannot write and cannot see anything else. The
fixed tools stay: they are faster, cheaper and already checked for the common questions. `truy_van` is for
everything else.

### 3.1 What the model can see: views, not tables

- **One connection per request** to `state.db`, opened `mode=ro` with `PRAGMA query_only = ON`.
- **TEMP views built for the person signed in**, from the same access rules the pages use (`people.auth.visible`,
  `desk.reads.book_of`). The model never sees a real table name.

| Role | Views (Vietnamese names, Vietnamese column names where it helps the model) |
|---|---|
| CIO | `tin` (news_items, minus refused, minus held), `su_kien` (events), `nhan_dinh` (views), `de_xuat` (application_runs), `tac_dong_gia_dinh` (family_impacts: aggregates only), `du_bao` (forecasts), `viec_nen` (job_runs), `nguon_du_lieu` (source_runs) |
| RM | the CIO's news and event views, plus `gia_dinh`, `tai_san`, `lien_he` and `duyet` restricted to their book |
| Client | `tai_san`, `dong_tien`, `muc_tieu` for their own family only, plus `tin` and `su_kien` |
| Compliance / admin | `nhat_ky` (audit_log, no `data` payloads), `tin_bi_giu`, `viec_nen`, `canh_bao` |

- JSON `data` columns are flattened into typed columns inside the view (`json_extract`), so the model never parses
  JSON. Times are given in Vietnam time (`ngay_lay`, `gio_lay`) next to the epoch values.
- Never exposed: `accounts`, `people.email`, passwords, the audit chain's hashes, other families' rows, held news.

### 3.2 What the query can do: SQLite's authorizer

`con.set_authorizer` allows only `SELECT`, `READ` on the temp views, and a short list of functions (`count`,
`sum`, `avg`, `min`, `max`, `date`, `strftime`, `json_extract`, `lower`, `like`, `coalesce`, `round`). Everything
else is denied: any real table, `ATTACH`, `PRAGMA`, writes, `load_extension`, recursive CTEs.

Limits:
- a progress handler stops a query after 2 s;
- results are capped at 200 rows, and **the total is always returned**, so the answer says “50 / 1.415”;
- one statement per call, and at most 3 `truy_van` calls per turn.

### 3.3 What the model knows: a data catalog

The catalog is generated from the view definitions plus a hand-written file `src/assistant/catalog/<role>.md`.
- **Every view and column:** its meaning, unit (VND, %, Vietnam time) and allowed values (`trang_thai`: mới, đã
  gom, …).
- **Definitions the business uses:** “tin lấy về hôm nay” is `ngay_lay = date('now', '+7 hours')` and not by
  `published`. “Nhận định bị bác” is `trang_thai = 'rejected'`. Each one is the same definition the page uses.
- **10–20 example question → SQL pairs per role,** including today's CIO question.

The catalog joins the existing knowledge (`huong_dan`, “Cách tính”). The model reads it through the same tool
descriptions it already uses; nothing about data values is in the prompt, so ADR-0012 holds.

### 3.4 What the person sees

- The answer, with the query shown under **“Cách tính”** (collapsed): the SQL, the row count, and `as_of`.
- An audit entry per query: who, role, SQL, row count, time taken.
- The client-data barrier stays the same: with `client_ai` off, the model writes the SQL from the catalog but
  never reads the rows. The answer is assembled from the result by a template (“Có 1.415 tin.”).

### 3.5 One behaviour rule

When the person contradicts a number, the assistant **counts again** and shows how it counted. It does not argue
and it does not guess why. This goes in the assistant's system prompt and in the eval.

### 3.6 Which model

Today every assistant step runs on `llm:copilot`, which is **Haiku 5.5** (`LLM_MODEL_COPILOT`). The CIO agent's
`llm:cio` is Sonnet 5.5. Writing SQL against a catalog is harder than picking a tool, so `truy_van` may need
Sonnet. The eval decides: Haiku first, and Sonnet only for the SQL step if Haiku's accuracy is below the gate.

## 4. Phases

Each phase is its own branch and PR, merged when its gate passes.

| # | What | Gate |
|---|---|---|
| D0 | The ADR for the design change. Today `Param` is never “a path, a query language or a URL”, and `truy_van` is that exception, bounded by §3.1–3.2. Requirements are added to docs/brd | ADR merged; BRD checker green |
| D1 | **Shared counts.** One count function per list (news, alerts, search, reviews). Every page and tool showing a total uses it. Fixes the inbox page's “300” and alerts' 50 | A test per row of §2 seeds more rows than the cap and asserts the total |
| D2 | **The data room:** the views per role (§3.1), the authorizer and limits (§3.2), and `truy_van` returning rows + total + SQL + `as_of` | Adversarial tests: a real table, `ATTACH`, a write, another family's row, held news, a 10 s query. Each one refused, none of them leaks |
| D3 | **The catalog** (§3.3): generated column docs plus hand-written definitions and examples per role | Every view and column documented (a test fails on an undocumented column) |
| D4 | **Wire-up:** the tool in the registry, “Cách tính” showing the SQL, the audit entry, the re-count rule (§3.5), and the template path for `client_ai` off | Tests for each, plus the 2026-10-24 conversation replayed |
| D5 | **Eval on real models:** ~30 questions per role (CIO, RM, client), gold answers computed from the DB, today's chat included | Accuracy ≥ 90%, p95 ≤ 6 s, ≤ US$0.01 per turn; Haiku vs Sonnet for the SQL step measured and the model chosen |

Cost: D5 is the only phase with model calls. About 90 questions × 2 models, roughly US$1–2, reported with
`usage.cost`.

## 5. Settled here (not open)

- **No raw SQL on real tables.** The model sees role-scoped views or nothing.
- **No new database or service:** SQLite's own read-only mode and authorizer. On PostgreSQL (DATA-10), the same
  views become a read-only role with row-level security.
- **The fixed tools stay.** `truy_van` is the fallback for questions they don't cover, never a replacement.
- **Not this Claude Code session as the assistant's model.** It is one interactive session with shell access to
  this box, with no role isolation and no capacity for many users. The assistant stays on API models behind the
  barrier.
