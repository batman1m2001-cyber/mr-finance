# Business feedback, 2026-10-21 — plan

The meeting's four notes, what the product already has for each (read from the code and the live data on 2026-10-21),
and the work. Nothing done so far is thrown away: the old pages are all still in `web/pages/` and the RM uses them
today; the client's graph workspace becomes one page of the classic app instead of the whole app.

Order: **B1 first** (the trial runs until 2026-10-31, so it must start 2026-10-22), then B3, B4, B2.

## B1 · The daily news-agent trial, until 2026-10-31

**Asked.** Run the news AI agent every day on new information and measure: accuracy and recall of the news and of the
forecasts (buy / sell), how many right and wrong, how much was collected, whether the scenarios came true, and how fast
the agent collects and answers — overall and per segment (macro, policy, a sector, domestic and international broker
views).

**What exists.**

| Measure | Where | State on 2026-10-21 |
|---|---|---|
| News collected | `news_ingest` job every 10 min, 11 whitelisted feeds (`data/news_config.json`) | 1,045 items since 10-12, ~100 a day |
| Collection recall | `news/reference.py`, KPI-02: share of stories an independent reference carries that we collected | runs every 2 h |
| Forecast right / wrong | `measure/forecasts.py`: each approved view's forecast per factor and horizon, scored when due: direction and P10–P90 | 90 forecasts, 0 scored; horizons 1w / 3m / 12m; first due 10-22 |
| Speed | `measure/reports.py`: news → inbox (≤ 10 min), agent run time (≤ 15 min), news → effective (≤ 2 h) | monthly report |
| Segment | `event_type` on each news item (10 types) | 52% of items have none |
| Pages | CIO's Mô hình: Độ chính xác (`pages/accuracy.js`), Đo lường (`pages/measure.js`) | monthly, not daily |

**The gaps that matter.**

1. **No forecast is made without the CIO.** News becomes an event only when the CIO groups it, and the agent's view
   counts only once approved: 3 events in 10 days. A daily trial needs the agent to run on its own every day.
2. **The horizons are too long for the trial.** 1 week is the shortest: by 10-31 only the views approved by 10-24 can
   be scored, and 3m / 12m never.
3. **No "buy / sell".** The product forecasts factors (VN-Index, rates, gold…) and the impact on each portfolio; it
   never says buy or sell (it is not advice to the client).
4. **Segments do not match the business's.** No broker views are collected at all; half the news has no type.

**Work.**

- **B1.1 Agent-only daily run** (the `demo_walkthrough.py` flow as a daily job, 08:30): ingest, group the day's news
  into events by type automatically, run the CIO agent and the challenger on each, and **record every draft's
  forecasts as the agent's own** ("shadow", before any human edit), whether or not a person approves it. Shadow
  forecasts never reach a client screen. Approved views keep being scored as today, so "the agent alone" and "the
  agent plus the CIO" are measured side by side.
- **B1.2 Short horizons for the trial:** 1 day and 3 days beside 1 week (`HORIZON_DAYS`), the same bands scaled from
  the factor model. Scored daily against the market series the jobs already load at 15:45 / 16:00 / 17:30.
- **B1.3 Buy / sell, defined for the report only:** a forecast's direction on an asset class read as *tăng → mua /
  nắm giữ, giảm → bán / giảm tỷ trọng*; right when the realised move has the same sign over the horizon. Internal; the
  client still sees impact, not advice.
- **B1.4 Segments:** macro (monetary, fx, credit, commodity, geopolitics), policy (regulation), sector (equity,
  real estate, gold, crypto), broker views (new). Unclassified news gets a type from the same words plus the source's
  section (Vietstock "Vĩ mô" → macro). Broker views: add the domestic brokers' public daily-commentary feeds where one
  exists (checked per broker, licence noted); international broker research is behind paywalls: only public summaries.
- **B1.5 The daily report:** one page and one JSON per day, from 10-22 to 10-31: collected (by segment, source),
  recall against the reference, events, forecasts made, scored right / wrong (direction and band) by segment and
  horizon, buy / sell hit rate, speed (news → inbox, agent run, news → forecast), and the model cost.

**Gate.** The 10-22 run completes on its own at 08:30 and its report is readable that morning; every number links to
its records; cost per day stays under the cap.

**Cost.** One live event run took ~154k tokens (R6). At 5–8 events a day that is ~1M tokens a day; the cap is
yours to set (see the decisions below).

## B2 · A phone app

**Asked.** Should there be an app, downloaded as a file and unzipped rather than through Google Play (review takes
time)? Risk: the phone gets a virus?

**Recommendation: no store and no file. Make the web app installable (a PWA).** The site already works on a phone;
it needs a manifest, icons and a small service worker (none exist today). On Android, Chrome offers "Cài đặt ứng
dụng"; on iPhone, Safari's "Thêm vào màn hình chính". It opens full screen with its own icon, updates without
reinstalling, and needs no review.

**Why not an APK file to download:**

- **iPhone cannot install it at all** outside the App Store or TestFlight (most private-banking clients carry an
  iPhone).
- **On Android, the client must allow "install unknown apps"** and get past Play Protect's warning. It trains them to
  do exactly what the bank tells them never to do. A file passed around can also be swapped for a fake: this is the
  real virus risk, to the client, not to us.
- **Google is closing the door:** since 2026-09-30, apps installed outside the stores in Brazil, Indonesia, Singapore
  and Thailand must come from a verified developer, and Google plans to extend this to every certified Android device
  in 2027 ([Android Authority](https://androidauthority.com/android-sideloading-developer-verification-first-wave-rollout-3717921),
  [Android developers](https://developer.android.com/developer-verification/guides)).
- **A PWA carries no installer:** the phone runs it in the browser's sandbox, like the website.

**Limits of a PWA:** on iPhone, notifications only work once it is added to the home screen, and are less reliable
than Android's ([MagicBell](https://www.magicbell.com/blog/pwa-ios-limitations-safari-support-complete-guide)). A
store app (a wrapper around the same web app) stays possible later, for production, through the bank's own
developer account.

**Work (small):** `web/manifest.webmanifest`, icons, a service worker that caches the static files (never data),
the install prompt in the header menu, phone screenshots on Android and iPhone sizes.

## B3 · The interface: the old look, the new bar, the assistant optional

**Asked.** "The old interface, plus the bar like the new one, plus the chatbot, but optional." Private clients are
middle-aged: the new look reads too young.

**What "old" is.** The app the day before the graph workspace (`2241f62`, 2026-10-17): a top menu with tabs (Tổng
quan → Toàn cảnh, Bản đồ tài chính, Chi tiết; Tài sản; Mục tiêu; Tin; Chuyên gia), the page modules, and the
assistant as **a floating button that opens a side panel** (removed 2026-10-18 at the owner's request). The theme
followed the phone's or computer's setting.

**What stays from the new work.** The left bar with labels (T2), Bảng số liệu order (cash flow first, T3), one name
per thing (T5), the graph as a page with its groups (T6), the feed, the sources in the inspector.

**Work.**

- **B3.1 The classic client app.** The client routes to its pages again, the way the RM's pages render today, with
  Toàn cảnh as the home page. The left bar lists the pages (Tổng quan, Tài sản, Dòng tiền, Mục tiêu, Tin tức, Rủi ro,
  Chuyên gia), each opening its tabs. The graph is one page under Tổng quan ("Đồ thị tài chính"), not the whole
  screen. The old addresses keep working.
- **B3.2 The assistant, optional.** Back to a button at the bottom right ("Hỏi trợ lý"); the panel opens beside the
  page and closes; closed by default, remembered per person. Everything it does today (steps, confirmations,
  conversations, marks on the page) is unchanged.
- **B3.3 A calmer, more readable look** for the client (staff desks unchanged): light theme by default; 16 px body
  and 15 px tables (13 today); 44 px touch targets; higher contrast; no glow and no moving sparks; the brand colour for
  actions only; figures large and plain; fewer chips and pills.
- **B3.4 Checks:** every client page on desktop and phone, light and dark; the UI suite; `test_how`; a side-by-side
  of before and after for the business to approve before it goes to the public link.

**Effort.** Medium: routing and the bar (shell), the button (copilot.js), the look (tokens). No page is rewritten.

## B4 · The technical document

**Asked.** Highlight OperonX's strengths; add a data-governance disclaimer: the AI only pulls news onto the machine and
predicts the impact on portfolios inside TCB's environment, no data leaks out.

**What is true today (checked in the code):**

- **The news agents never see client data:** "No client data reaches this module" (`views/agents.py`, BR-11), and
  `tests/test_views.py` checks the prompts. They read public news and the factor model.
- **The impact on each portfolio is computed by our engine on our own server,** not by an AI model.
- **The client-data barrier** (`control/barrier.py`, BRD-NFR-08) has three modes. In `onprem` and `off`, every model
  call is checked before it is sent: one bound outside the bank and carrying a client's name, id, or account / card /
  loan / property number is refused, logged and audited. The assistant's model then sees only the scrubbed question
  and each tool's status; the answer is the tools' own text.
- **The public demo runs in `demo` mode,** where the assistant's external model does read the tools' results (the
  client's figures, without names).

So the disclaimer can be written **for the production setting** (`client_ai = onprem`, models inside TCB), and must
say that the demo differs.

**Work.**

- **B4.1 OperonX's strengths,** each with its evidence: one engine for the agents, the jobs and the web; every run
  traced step by step; durable runs and retries; jobs on a schedule; human approval built in; measured numbers (100
  concurrent calls on 4 workers in the callbot; US$0.002 per assistant turn).
- **B4.2 Data governance section:** what leaves the machine (RSS fetches, model calls with public news), what never
  does (client data in `onprem` and `off` modes), the barrier, the audit chain, retention, and the demo's exception.
- **B4.3 Verify before writing:** a test that lists every model call path (`statements`, `declare`, `views`,
  `newsletter`, `policy`, `assistant` turn / consolidate / web, `copilot` router) and asserts each passes the barrier.
  The doc only claims what that test proves.
- Published as the next version of the architecture artifact (Vietnamese, English terms in diagrams).

## Decisions for you

1. **The trial's daily model budget.** Suggested: US$5 a day, stop for the day when reached.
2. **May the daily run approve its own views** (like the demo script: new events appear on the demo clients' screens
   each day), or only record the shadow forecasts and leave approval to a person?
3. **Broker views:** may we collect the domestic brokers' public commentary pages (terms of use differ per broker)?

Everything else above is decided in this plan.
