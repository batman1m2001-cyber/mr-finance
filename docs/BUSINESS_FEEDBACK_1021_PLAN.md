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

**What the backtest already says (2026-10-21, `measure/backtest.py`, walk-forward 2022-01 → 2026-10).** The
engine's 3-month direction is right 72 % of the time (54 month-ends; target 70 %): VN-Index 72 %, VN rates 92 %, VN
government bonds 85 %, gold 68 %; Brent 46 % and foreign flows 39 % are worse than chance. At 1 week it is 57 %. It
assumes the agent read the news right: it scores the engine, not the agent. Short horizons are mostly noise, so the
daily right / wrong is an early signal, not the accuracy.

**No person in the loop for the check.** The CIO's approval guards what reaches a client; measuring the agent needs
the agent alone (an edit by the CIO would mix the two). Every forecast of the trial is a *shadow* forecast: recorded
and scored, never applied, never on a client's screen (BRD KPI-05 untouched). The daily run approves nothing.

**Work** (in this order).

- **B1.0 The models through Claude Code.** `scripts/claude_bridge.py`: a local OpenAI-compatible endpoint
  (`/v1/chat/completions`) that answers each call with headless `claude -p` on the owner's subscription: no tools,
  an empty working directory, a scrubbed environment, the model asked for (Haiku 5.5, Sonnet 5.5, Opus 5.5), the
  reply's model and token counts as the app expects. Only `llm:cio` and `llm:challenger` point at it
  (`LLM_AGENT_BASE_URL` in `resources.yaml`); the assistant keeps its own. The agent's code does not change.
  CIO agent on Sonnet 5.5, challenger on Opus 5.5. The bridge runs on 127.0.0.1, which the barrier counts as inside
  the bank: harmless for the news agents (they never see client data) and said in the bridge so nobody points a client
  step at it. Gate: one event's agent + challenger run through it, time and tokens recorded.
- **B1.1 Agent-only daily run, 08:30 every day to 10-31** (a `Job` in `app/main.py`, the `demo_walkthrough.py` flow
  without the approval): ingest, the day's news grouped into events by type (the newest four per type, as the script
  does), the CIO agent and the challenger on each, and each draft's forecasts recorded as shadow forecasts.
- **B1.2 Horizons for the trial:** shadow forecasts at 3 days, 1 week and 3 months (1 day is dropped: noise). The
  scoring job already scores what is due against the market series the jobs load each afternoon.
- **B1.3 Buy / sell, for the report only:** the direction on an asset class read as *tăng → mua / nắm giữ, giảm →
  bán / giảm tỷ trọng*; right when the realised move has the same sign. The client still sees impact, not advice.
- **B1.4 Segments:** macro (monetary, fx, credit, commodity, geopolitics), policy (regulation), sector (equity, real
  estate, gold, crypto); untyped news gets a type from its words and its source's section (Vietstock "Vĩ mô" →
  macro). Broker views wait for the owner's answer on sources.
- **B1.5 The 3-month replay:** news from 2026-07-01 to 07-21 (after the models' knowledge cutoff, so they cannot
  remember the outcome), taken from the outlets' archives, 20–30 events; the agent run with the market as it was that
  day; each 3-month forecast scored against what happened by 10-21. A first read, not proof (said on the page).
- **B1.6 The report:** one page for the business (and a JSON per day): collected by segment and source, recall
  against the reference, events and forecasts made, scored right / wrong by segment and horizon, buy / sell hit
  rate, speed (news → inbox, agent run, news → forecast), the backtest and the replay, subscription use per day.

**Gate.** 10-22 08:30 runs on its own and its report is readable that morning; every number links to its records.

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

## Decided by the owner (2026-10-21)

- **B1 is the priority.** Models through the owner's Claude Code subscription (headless `claude -p`, checked on this
  server: Max plan, OAuth, no API key), not a paid API: no US$ budget, the plan's usage limits instead. A local
  OpenAI-compatible bridge turns the app's model calls into `claude -p` calls (no tools, an empty working directory,
  structured output), so the app's configuration changes and its code does not. Haiku 5.5 for grouping and
  classifying, Sonnet 5.5 for the CIO agent, Opus 5.5 for the challenger (two different models, BRD §8).
  Demo and trial only: production needs the bank's own models (`client_ai = onprem`).
- **B2: iPhone only, a demo.** An installable web app, and a "Tải ứng dụng" button on the site that shows how
  (iPhone cannot be prompted by a page: Share → Thêm vào màn hình chính).
- **B3: the look and the layout only.** The routes, the data, the pages' logic and the assistant's flow stay as they
  are; the UI suite and `test_how` must pass unchanged in what they check.
- **B4: backlog.** The owner takes it later.

- **No person in the loop for the trial;** the daily run approves nothing (shadow forecasts only).

## Still open

1. Broker views: may we collect the domestic brokers' public commentary pages (terms of use differ per broker)?
