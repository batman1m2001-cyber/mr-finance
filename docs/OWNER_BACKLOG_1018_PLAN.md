# Owner backlog of 2026-10-18 — plan

The owner's go (2026-10-18): "just go, don't let anything remain". Three items were held for the owner after the
multi-role desks (FEAT-41) and the staff assistant stress test. This plan does all three, in order, on
`feat/owner-backlog-1018` (off `exp/graph-workspace`), then merges to `exp/graph-workspace`.

| Phase | What | Owner's words |
|---|---|---|
| F | The workspace fold: “4 mục tiêu khác” shows flat on a large screen | "I don't see the collapse +4 … I still see them as flat expand" |
| A | The CIO's background agents: the assistant runs them on a confirm; a jobs view | "do you have UI/UX for them, and can our assistant control them?" |
| U | Admin's users and roles (Q-25) | "do it, add the feature you think it's best for it" |

Every phase: tests first where they can be, lint (`ruff check`, `ruff format --check`), the non-UI suite and the UI
subset it touches, a CHANGELOG line, `scripts/check_brd_docs.py` at 0 errors, desktop and phone screenshots for UI.

## F — the fold is a rule, not a fit

**Cause (read in `web/workspace/graph.js` `layout()`).** A group folds only when the ring is too short for its
slots (OWN-GW-27). At 1440×900 the goals do not fit and fold behind “+4”; on a larger screen they fit, so nothing
folds and the same family shows a flat ring. The fold depends on the screen, so the person sees two products.

**First idea, dropped on measurement.** A fixed top N per group (3 goals, …) leaves this family's four goals flat
everywhere (a group of four shows whole: “+1” gains nothing), so the owner's complaint would stand.

**Fix.** The fold is decided on a canvas no larger than the one a 1440×900 window gives (992×563): on a larger
canvas the layout first runs at that area (same aspect), keeps its fold, then places the ring at the real size. A
smaller canvas folds more, as before; a phone is unchanged.

- Measured (C01, Tổng quan; `+n` groups shown): before, 1440×900 had 4 (goals among them), 1680×1050 had 1, 1920×1080
  and 2560×1440 had none. After, 1440, 1680, 1920 and 2560 all have the same four: tin tức, mục tiêu, khoản nợ, lớp tài
  sản. 1280×720 and the phone fold five, as before.
- Opening “+4 mục tiêu khác” on 2560×1440 shows the four goals and “Thu gọn”; to make room, other groups fold, as at
  1440.
- Test: `tests/ui/test_graph_layout_ui.py::test_a_large_screen_folds_as_the_reference_does` (1440×900 and 2560×1440:
  the same groups, goals among them, and the layout audit clear).

## A — the CIO's agents and the jobs, run from the assistant and from one page

**What exists.** `POST /api/events/run-agent` queues Agent CIO (`agent_jobs`, run by `agent_worker`); the challenger
re-runs through `POST /api/views/decide` action `challenge`; jobs run on their schedules or `operonx run <job>`; the
Agent page draws the map; Hệ thống lists the jobs read-only. The assistant reads all of it (`agent_nen`) and says it
does not run them.

**Decisions.**
- Running an agent or a job is not a decision: it starts a draft or fetches data, and every decision it leads to
  stays on its page with its second person. So the assistant may start one, on the person's Xác nhận, like its other
  writes (planned, confirmed, read back).
- Who runs what, as the BRD's roles say: the CIO runs Agent CIO and the challenger (BRD §5 WF-03/04, FR-301…303);
  Admin runs the background jobs (BRD-RULE-ROLE-04: operations). Compliance reads.
- Which jobs may run now: the fetches and checks a person would want again at once — news, market, policy sweep,
  audit check, AI-zone sync and import, accuracy score. Not the clockwork (heartbeat, agent worker, memory
  consolidation, retention, the market-history load, which has its own request).

**Built.**
1. `src/control/jobs.py`: the jobs app/main.py declares, registered at start; `run_now(job, by)` refuses a job not
   on the list or already running (one at a time per job; a run left running 30 minutes is failed), records a row in
   `job_runs` (who, when, how it went, the record's summary), audits `job.run_now` and `job.run_done`, and runs the
   job in the server's loop. A failed run raises the job alert as a scheduled run does.
2. Services: `POST /api/jobs/run {job, by}` (Admin). Reads: `GET /api/jobs` (CIO, Admin, Compliance): the agent
   queue (last 20 requests), each agent's runs in 7 days, today's token budget, each job with its schedule, last run
   and whether it may run now, and the last manual runs.
3. The page **Việc nền** (`web/pages/jobs.js`, menu of CIO, Admin and Compliance): three sections —
   *Agent* (the queue with each request's state and its view; the CIO's “Chạy Agent CIO” on an event that has no
   view yet, and “Phản biện lại” on a view waiting for it); *Lịch chạy* (each job: when it runs, the last run, its
   state; Admin's “Chạy ngay” button); *Lần chạy tay* (who ran what, when, how it went). Compliance sees it without
   buttons. Phone: one column, the tables become lists.
4. Assistant writes (`src/assistant/actions.py`), each with plan, confirm and verify:
   - `chay_agent_cio` (CIO): an event, optional mode; verify reads the `agent_jobs` row back.
   - `phan_bien_lai` (CIO): a view in a state the challenger runs from; verify reads a new challenge or the error the
     view kept.
   - `chay_viec_nen` (Admin): a job from the list; verify reads the `job_runs` row back.
   `agent_nen` says what can be run and by whom instead of “không chạy agent”; the DUTIES of CIO and Admin, the
   staff suffix (“chạy agent” leaves the page-only list), the guide's desk sections and the router keywords follow.
5. Tests: the services and their refusals (wrong role, unknown job, one at a time), the three tools through their
   plans and verifiers (offline, no model), the page (UI subset), the router.
6. Stress-test catalogue: the CIO's and Admin's cases that expected a refusal now expect the Xác nhận; one new case
   per tool. Rerun only those cases on the copy (a few cents; cost reported).

## U — Admin's users and roles (Q-25)

**Decision (owner: "add the feature you think it's best").** Admin manages staff accounts on a page of its own,
**Tài khoản và vai trò**, with every change approved by a second Admin, as the configuration is. Customers' accounts
are not managed here (they come with the family's onboarding).

- **What Admin can ask for:** add a staff account (name, email as login, role, title); change a role; disable or
  enable an account; reset a password.
- **Two people.** Each is a request (`account_requests`): proposed by one Admin, approved or rejected by another; the
  proposer cannot approve; a rejection needs a reason; the proposer may withdraw it while it waits. Every step is
  audited (`account.requested`, `account.approved`, `account.rejected`, `account.withdrawn`).
- **Takes effect at once.** A disabled account fails sign-in and its open sessions fail `verify` on the next request;
  a role change is read at each request (the viewer is built from the people table every time).
- **No password travels.** An approved add or reset makes a one-time code (10 characters, 24 hours, kept hashed),
  shown once to the approving Admin to hand to the person. The sign-in page takes the login, the code and a new
  password (“Có mã một lần?”). A used or expired code fails; a new reset replaces an old code.
- **Guards.** No request on one's own account. The last enabled Admin cannot be disabled or moved. An RM who still
  has families in the RM assignment cannot be disabled or moved off RM: the request says to move them first, with a
  link to Cấu hình › Phân công RM. A new RM gets families through that same assignment (two people), linked from
  the request's result.
- **Demo.** While `MF_DEMO_ACCOUNTS` is on, the seeded accounts (the demo personas) cannot be disabled, moved or
  reset, so a visitor cannot lock the next one out; accounts added on the page can. The page says so.
- **The assistant.** Admin's assistant reads the accounts and the waiting requests (`tai_khoan`), and can file a
  request on a Xác nhận (`yeu_cau_tai_khoan`): it never approves one (the second person decides on the page) and
  never shows a code.

**Built.** `src/people/accounts.py` (requests, guards, codes), the flag table `account_flags` (disabled, the code's
hash and expiry), `verify`/`login` checks, the services `POST /api/accounts/request`, `/api/accounts/decide`,
`/api/accounts/redeem` and `GET /api/accounts`, the page `web/pages/accounts.js` in Admin's menu, the sign-in
page's code form, the two assistant tools, Admin's desk linking the page. Tests: each guard, the two-person rule,
disable taking effect on a live session, the code's single use and expiry, the demo guard, the audit lines. Docs:
Q-25 answered, OWN-MR-04 implemented, SCR-ADM-03, the matrix, FEAT-41, the API reference, the stress catalogue's
adm-lim-01 and Admin's DUTIES line.

## Order and release

F, then A, then U, each a commit on the branch; merged to `exp/graph-workspace`; the owner pushes main
(`cd /home/thanglq/mr-finance-graph && git push origin exp/graph-workspace:main`); then :8030 pulls, its data is
backed up, it restarts, and a live smoke check runs on every persona.
