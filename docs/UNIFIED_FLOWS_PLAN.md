# The unified graph and its money flows — plan

Owner request (2026-10-17):
[`2026-10-17_unified_graph_flows.md`](brd/sources/owner_requests/2026-10-17_unified_graph_flows.md) (“Unified”).
It becomes OWN-GW-33…50 ([owner_requirements.md](brd/requirements/owner_requirements.md)) and the FEAT-40 section
“Money flows, scenarios and the assistant”. Work happens on branch `exp/graph-workspace`, served on :8040. There is
no PR to main.

## 1. Audit — what exists (read and measured 2026-10-17)

| Request | Already built | Missing |
|---|---|---|
| §1 One graph | The workspace (OWN-GW-01…14): toolbar, graph, Trợ lý/Thông tin dock, strip, lenses that refocus, sheets for the old pages, Chuyên gia as its own view | The month's transactions show only as two totals (`FL:in`, `FL:out`); their categories are listed in Thông tin, not on the graph |
| §2 Actual | Income into “My Wealth”, spending out, this month's loan and card repayments, as moving sparks | Categories as their own flows; no transfer rows exist in the data (below) |
| §2 News | Event → class edges with the 3-month expected change per class (`by_class`), certainty `estimate`; policy items with one total impact | Not drawn as flows; no direction; no monthly basis |
| §2 Goals | Goal nodes with need, have, gap, status | The monthly saving each goal needs (`goal.monthly`, already computed) is not on the graph. The followed goals share one funding pool (below) |
| §2 Scenarios | Five stress tests as nodes; one can be run, and its total change sits on its node, never in net worth | No per-class effect, no flows, no way to run several together, no user-defined what-if |
| §2 Trace | The news path sheet (Đồ thị tác động: event → scenario → factor → asset → goal) | Nothing traces a scenario, and nothing reaches liquidity and projected net worth on the graph |
| §3 Animation | Sparks on money edges, 1–3 per 0.9 s beat from the edge's share of the largest flow | Speed, trail and prominence fixed; only actual money moves; no off-screen pause |
| §4 Core | OWN-GW-20…25, built and verified | — |
| §5 Layout | OWN-GW-26…31, built and verified (audit at 0 on real and 3× graphs) | The new edges (goal, category, scenario) must keep the audit at 0 |
| §6 Assistant | Its tool steps light the nodes they read, text events ripple the core, `kich_ban` runs one stress test | It knows the page, not the selection or the active scenarios. It cannot compare or combine scenarios, or list a node's links. Edges cannot be selected |
| §7 | Transform and opacity only, reduced motion, Web Animations tracked | Animations keep running when the graph is hidden (a sheet, another tab, scrolled off on a phone) |

**Facts the decisions rest on (client C01, demo data):**
- The month's transactions have the categories salary, pension, rent, living, card, loan, school, health and
  rent_out. There are **no transfer rows**. Transfers would show like any other category, but none can be tested.
- Three followed goals (tuition, emigration, medical) each count **the same 4.03 tỷ** liquid pool as `have`. Their
  monthly needs (79.1 tr, 122.4 tr, 1.25 tr) together exceed the 5 tr monthly surplus many times over.
- A policy item's `impact` is exposure × sensitivity × probability. It is a one-off expected change with no horizon,
  and it is not split by class (only by the names it `affected`).
- A news run carries, per class, the 3-month expected change. It also has its P5/P10/P50/P90 bands, the
  `modelled_share` and the `goal_impact` (FR-404). That is its confidence, as recorded.
- A stress test computes each holding's shock (`_stress`), but it returns only the top three rows and the totals.
  A rate rise adds a yearly interest cost on floating loans. A dollar rise adds a cost on foreign-currency spending.

## 2. Decisions

**F1. Certainty stays three-valued, family is a separate mark.**
- `actual`: a record (a transaction, a holding).
- `estimate`: computed under the CIO's assumptions. This covers news and policy impacts, and a goal's monthly need,
  which comes from the return assumptions.
- `hypothetical`: a scenario.
- **Family** is orthogonal: in family scope, a holding or a transaction category owned by another member carries
  `owner`. It shows as a small person mark on the node and “của <tên>” in Thông tin. Lines keep their certainty style.

**F2. The flow model: which edges carry money, and how much per month.** Each money edge carries an `amount` (the
figure shown), a `monthly` (its rate per month, used for the animation only) and a `dir` (which way the money goes).

| Edge | amount | monthly | Direction |
|---|---|---|---|
| Income → “My Wealth” (actual) | the month's income | same | into the core |
| “My Wealth” → spending (actual) | the month's spending | same | out |
| Category → income / spending → category (actual, on demand) | the category's sum of rows | same | with its side |
| Debt repaid (actual) | this month's repayment | same | out to the debt |
| “My Wealth” → goal (estimate) | `goal.monthly`, what closes the gap by the date | same | toward the goal |
| News event → class (estimate) | the class's 3-month expected change | amount ÷ 3 (its own horizon) | into the class if positive, out of it if negative |
| Policy item ↔ class (estimate) | the item's impact, **only when it touches one class**; otherwise no amount (a relation) | none: no horizon, so prominence is relative (below) | by sign |
| Scenario → class (hypothetical, while active) | the class's shocked change | none: a one-off, so prominence is relative | by sign |
| Scenario → spending (hypothetical, while active) | the extra yearly cost (floating interest, foreign spending) | amount ÷ 12 | out |

Every other edge is a relation, with no sparks: holdings, sources, risks, liquidity, an inactive scenario, and a
goal that needs nothing (`monthly` 0 or none, “chưa có nguồn bù”).

**F3. Goals share their pool, and it is said once.**
- When two or more followed goals name the same funding pool (`have_label` and `have`), each goal edge is marked
  `shared`.
- Thông tin says “nguồn 4,03 tỷ dùng chung cho 3 mục tiêu”. The strip and the goal list total the monthly needs
  against the surplus (“cần 202,8 tr/tháng · dư 5 tr/tháng”).
- No goal is shown as funded by money another goal already counts.

**F4. Combining scenarios (`POST /api/scenario/combine`), one engine, no double counting.**
- **Assets are compounded per holding:** `after = value × Π(1 + shockᵢ)`. Shocks are never summed on the same base.
- **Attribution by Shapley value:** each scenario is credited with its average marginal change over the orders in
  which the scenarios could be applied. The parts add up to the total exactly, whatever the signs. A split in
  proportion to the standalone changes was rejected: with opposite signs on one holding (gold up with the dollar,
  down in the person's what-if) it divides by almost zero.
- **Costs are keyed** (`floating_interest`, `fx_spending`). The same key from two scenarios counts once, the larger.
  That covers a rate rise in the stress test and the same rise in the person's own what-if.
- **Net worth after** = assets after − debt − one year of the extra costs. This is the standalone stress rule
  (`_stress`), kept so that combining one scenario gives exactly its standalone result. A test holds that.
- **Liquidity after:** the liquid holdings after their shocks; months = liquid ÷ (spending + costs ÷ 12).
- **Income and expenses:** the what-if's income change and the costs ÷ 12 change the monthly surplus.
- **Goals:** recomputed on the shocked picture (the same `_sim` runs), so a goal's status under the scenarios
  depends on them. A goal changes status only through the shocks and the surplus.
- **Output:**
  - the active list and each one's assumptions in words;
  - per class and per scenario;
  - before and after net worth, liquidity, surplus and goals;
  - the costs, with the shared ones named;
  - the note “giả định — không cộng vào tài sản ròng”.
- The actual overview never changes.

**F5. The person's own what-if (`custom`).** A stress scenario whose shocks are the person's inputs:
- real estate %, stocks and equity funds %, gold %, each from −50 % to +50 %;
- floating loan rate +0 to +5 points;
- monthly income from −50 % to +50 %.

It runs through the same `_stress` and combine. Its assumptions are exactly the inputs. Nothing else is shocked.

**F6. Active scenarios.**
- Running a scenario makes it active. A bar above the graph shows the active ones as chips, the combined net worth
  “nếu xảy ra” and “Bỏ tất cả”.
- An active scenario's node has a solid accent ring, and its class edges run hollow, dotted sparks.
- Turning one off recombines the rest.
- The set is kept per viewer and client in the browser (a convenience, like the followed goals), and the server
  computes from it every time.

**F7. The animation follows the money.** For an edge with a `monthly` rate `m`, against `R` = the larger of this
month's income and spending:
- intensity `i = clamp(√(m ÷ R), 0.12, 1)`;
- sparks per beat: 1 + round(2i), which is 1 to 3;
- trail length 6 + 14i px;
- speed 140 + 140i px/s, rounded to keep the 0.9 s beat;
- opacity 0.4 + 0.55i.

Edges with no rate (a policy item, a scenario) take `i` relative to the largest of their own family, capped at 0.5:
a one-off never looks like a monthly stream.

Treatments by certainty:
- **actual:** a bright head with a trail;
- **estimate:** a dashed head, no glow, opacity × 0.75;
- **hypothetical:** hollow dotted heads, only while active.

There are at most 48 spark paths: low-intensity edges drop to one spark first. Nothing moves under reduced motion.

**F8. Off screen, nothing runs.** An IntersectionObserver on the graph, the page's visibility and an open sheet
mark the SVG `asleep`. CSS animations pause (`animation-play-state`), and tracked Web Animations pause and resume
with it.

**F9. Edges can be selected.**
- Each edge gets a wide, invisible hit path. A click or Enter selects the edge, and the graph lights both its ends.
- Thông tin shows:
  - **from → to**, and its words;
  - **amount and monthly rate**;
  - **certainty** in words;
  - **sources:** the records, each linked;
  - **Cách tính:** the formula it came from (the `how` registry);
  - **assumptions:** for a scenario, its shocks; for news, the CIO's view and horizon; for a goal, the return
    assumptions and the date;
  - **confidence, only where recorded:** news P10–P90 and the modelled share, policy probability, “ghi nhận” for a
    record;
  - **downstream:** for news and scenarios, the classes they reach, then net worth and the goals; for a goal, the
    shared pool.
- Node selection keeps its present behaviour.

**F10. The assistant sees the graph.**
- The panel's request adds `graph`: the lens, the selection (id and kind, plus the label only in model mode) and
  the active scenarios.
- The instructions add “Đang chọn …” and “Kịch bản đang bật …”.
- Two read tools:
  - `lien_ket`: a node's links, with amounts, certainty and sources, from the overview. It explains relationships.
  - `so_sanh_kich_ban`: standalone and combined results for the given scenarios, or the active ones.
- The stream lights what each tool read:
  - `so_sanh_kich_ban`: the scenarios and the classes they hit, whose hypothetical edges pulse;
  - `dieu_tra`: the event and its classes;
  - `lien_ket`: the node and its neighbours.

**F11. Categories on demand.** Picking money in or out in Dòng tiền (or Tổng quan) fans out its categories behind
it, like a class's holdings. Each category is its own actual flow with its rows (`flow:<m>:<side>:<category>`) and
an owner mark in family scope.

**F12. What is not built, and why.**
- **Transfer flows:** the data has no transfer rows.
- **A monthly basis for policy items and scenarios:** they are one-offs.
- **Confidence scores for actual records or scenarios:** none is recorded, and none is invented.

## 3. Phases

| Phase | What | Gate |
|---|---|---|
| U0 ✅ | BRD: the source, OWN-GW-33…50, FEAT-40 section, this plan | `scripts/check_brd_docs.py` 0 errors |
| U1 ✅ | Data: the flow fields (F2) on overview edges, goal edges with the shared pool (F3), stress rows by class, `POST /api/scenario/combine` (F4) and the custom what-if (F5) | pytest: one scenario combined = its standalone result; compounding (two −50 % → −75 %, not −100 %); attributions add up; a cost key counted once; the what-if's income moves the surplus and goal status; the overview's net worth never changes; directions and monthly rates as F2; no amount on a policy edge that touches several classes |
| U2 | Animation: F7 intensity, certainty treatments, directions, the cap, F8 sleep | UI test: each money edge's sparks run its `dir`; more money → more sparks, longer trail, higher opacity; relations have no sparks; estimate and hypothetical look different from actual; asleep → no running animation; reduced motion → none; idle frame time within 1 ms of before |
| U3 | Scenarios on the graph: run, activate, the bar, hypothetical class edges, the what-if form, the trace in Thông tin | UI test: two active scenarios → the bar shows the combined figure from the server; net worth on the core unchanged; turning one off recombines; the trace lists classes → liabilities/expenses → liquidity → projected net worth → goals |
| U4 | Edge selection (F9) and categories (F11); the shared goal pool in Thông tin and the strip | UI test: clicking a news, goal, flow and scenario edge shows its source, calculation, assumptions, confidence where recorded, and downstream; categories fan out and are clear (audit) |
| U5 | The assistant (F10): context, `lien_ket`, `so_sanh_kich_ban`, stream mapping | pytest: the context reaches the instructions (label only in model mode); both tools return the server's numbers; stream nodes per tool. UI test: a scripted comparison lights the scenarios' edges. One real-model turn, cost reported |
| V | The layout audit (real and 3×, with scenarios active and categories open); frame times; full suites; FEAT-40 feature map (every BRD feature → its graph form); report; matrix; screenshots | OWN-GW-33…50 implemented_verified or named gaps |

## 4. Out of scope

- A new rendering or animation engine (the owner: “reuse the current stack”). Everything stays in `graph.js`'s SVG
  and CSS.
- Probabilities across scenarios. Combining them is a what-if, not a forecast, and it is never added to net worth.
- Life events as combinable scenarios. They are the goals (FEAT-26). Their what-if lives in Kế hoạch, as before.
