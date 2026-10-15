# Requirements of the original product brief — `BRIEF-<area>-nn`

Layer A, second source. The product began from the brief [`mr_finance_idea_final.md`](../../../mr_finance_idea_final.md)
(“Plan v2: Tập trung vào selling point Consolidate + Dashboard tổng thể”), before the BRD existed. Its
capabilities are built (docs/PLAN.md P1–P7) and are **kept** alongside the BRD's
([ADR-0003](../decisions/ADR-0003-keep-the-capabilities-that-predate-the-brd.md)). The brief is written as a
pitch, not as a specification; requirements below are its explicit statements, and its examples (amounts,
names) stay examples.

Its message: *“KH có tài sản ở nhiều sản phẩm, nhiều kênh, nhiều nền tảng nhưng không ai cho họ thấy bức tranh
toàn cảnh. Chúng tôi làm việc đó và cho biết điều gì đang tác động tới bức tranh ấy.”*

Status: [`requirements_traceability.md`](requirements_traceability.md) §3.

## DATA — three tiers of sources (brief §1)

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| BRIEF-DATA-01 | Tier 1, automatic: Techcombank (deposits, cards, loans, salary, recurring spending), TCBS (stocks, bonds, cost, P&L), Techcom Capital (fund certificates), OneHousing (home valuation, area prices, liquidity) | §1 table | documented |
| BRIEF-DATA-02 | Tier 2, with the client's consent: other banks and brokers by Open API (NHNN framework) or by uploading a PDF/Excel statement that AI reads and splits into items | §1 table | documented |
| BRIEF-DATA-03 | Tier 3, self-declared: income, children and their ages, dependents, property outside the system, gold, insurance, personal debt, company shares — by smart form or by chatting with AI (“Tôi có 1 căn ở Thảo Điền mua 2019 giá 8 tỷ”) | §1 table | documented |
| BRIEF-DATA-04 | Each asset is labelled verified (API/ecosystem), from a statement, or self-declared; the certainty of later analyses follows the label | §1 “Độ tin cậy” | documented |
| BRIEF-DATA-05 | Family: link spouse/children accounts (each person's consent) to view wealth per person or per household | §1 “Gia đình” | documented |

## RISK — the AI risk-appetite test (brief §2)

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| BRIEF-RISK-01 | Adaptive questions: each depends on the previous answer, about 8–12 instead of 20 fixed | §2.1 | documented |
| BRIEF-RISK-02 | Situational questions, not 1–5 scores (e.g. the client's own portfolio falling 10 → 8 tỷ; certain 6 % vs 50/50 +15 %/−3 %) | §2.2 | documented |
| BRIEF-RISK-03 | Separate risk tolerance (what the client wants, from the test) from risk capacity (what they can bear, computed from cash flow, debt and dependents); warn when they diverge | §2.3 | documented |
| BRIEF-RISK-04 | Re-ask on big life changes, strong market moves or every 6 months; compare what the client says with what they did (e.g. sold in a 5 % dip) | §2.4 | needs_clarification (Q-16: re-ask triggers are not built; “what they did” is) |
| BRIEF-RISK-05 | Result: one of 5 personas with a concrete risk profile | §2.5 | documented |

## DASH — the overall dashboard (brief §3)

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| BRIEF-DASH-01 | Net worth with its month change; personal / family switch | §3 wireframe | documented |
| BRIEF-DASH-02 | Allocation by asset class | §3 | documented |
| BRIEF-DASH-03 | Portfolio P&L, realised and unrealised, against a benchmark the client sets | §3 “Các chỉ số chính” | documented |
| BRIEF-DASH-04 | Risk threshold: maximum drawdown the client accepts against the current risk; warn on concentration in a sector, area or issuer | §3 | documented |
| BRIEF-DASH-05 | Liquidity reserve: highly liquid assets as months of spending covered | §3 | documented |
| BRIEF-DASH-06 | Future cash flow as a 12–36-month calendar of payables, inflows and outflows; AI detects recurring items from statements (salary, rent, school fees); flag large upcoming payments | §3 | documented |
| BRIEF-DASH-07 | A count of impact alerts linking to the alerts | §3 wireframe | documented |

## SCEN — simulations (brief §4)

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| BRIEF-SCEN-01 | Life-event scenarios the client tries: children's education (domestic/abroad, FX +5 %), early retirement at 55, selling a second home, buying property with a loan (rates +2 %, rent short), passing wealth to children, a business needing cash, large medical costs, emigrating / study abroad, weddings / helping children buy a home | §4 A table | documented |
| BRIEF-SCEN-02 | Market stress tests run by the system: the 2022 corporate-bond crisis replayed, a 2022–2023-style property freeze (18 months illiquid), VN-Index −30 %, rates +2 %, USD/VND +5 % | §4 B | documented |
| BRIEF-SCEN-03 | Each scenario gives a heavy and a light option; it is only a simulation; a concrete recommendation must be approved by the RM | §4 | documented |

## IMPACT — measuring impact on the client's assets (brief §5)

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| BRIEF-IMPACT-01 | Impact (VND) = holding × sensitivity × probability; transparent and explainable | §5 formula | documented |
| BRIEF-IMPACT-02 | Sensitivity by class: bonds by duration, stocks by sector beta, property by OneHousing area prices, loans by floating rate | §5 | documented |
| BRIEF-IMPACT-03 | Probability by legal status: draft (low), consultation (medium), passed (high) | §5 | documented |
| BRIEF-IMPACT-04 | Show VND, % of net worth and a high/medium/low level, with the cited source | §5 | documented |
| BRIEF-IMPACT-05 | Macro channels (policy rate, USD/VND, gold and its domestic spread, credit room for property) and micro ones (local infrastructure — opportunities, not only bad news; province mergers, zoning, land price tables) | §5 table | documented |

## ALERT — early policy warnings (brief §6)

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| BRIEF-ALERT-01 | Warn on the 14 listed policies and drafts (second-property tax, transfer-tax change, annual land price tables, state-bank draft, bank-ownership limits, professional-investor bond rules, securities transfer tax, market upgrade, gold-bar management, digital-asset pilot, FX/study-abroad transfers, PIT reform, unit-linked insurance, global minimum tax), each targeted at the clients it concerns | §6 table | documented |
| BRIEF-ALERT-02 | Check each policy's latest legal status before any demo | §6 “Lưu ý” | documented |

## FLOW — the demo flow and compliance (brief §7)

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| BRIEF-FLOW-01 | The five-minute demo: connect data → AI test → dashboard (personal/family, the large school payment) → an alert (second-property tax, metro) → a scenario (sell a home, see cash flow) → RM approval | §7 | documented |
| BRIEF-FLOW-02 | Compliance: the RM approves before anything is recommended (“RM duyệt … đáp ứng compliance theo đề bài”) | §7.6 | documented |

## Capabilities in the product that no source document asks for

Recorded so they are not lost and not mistaken for requirements. Each is an **existing capability** (feature
file linked); its origin is the merge noted.

| Capability | Origin | Feature |
|---|---|---|
| Specialist team per client and an “Advisory performance” track record (recommendations, accuracy, missed news, AI pipeline scores), all from mock `data/advisory.json` | PR #13 “sync/onewealth” (2026-10-15) | [FEAT-28](../features/FEAT-28-advisory-team-and-track-record.md) |
| House views (research houses' forecasts, mock `data/views.json`) matched to holdings | PR #13 | [FEAT-25](../features/FEAT-25-policy-cost-alerts-and-house-views.md) |
| Goals planning (“Wealth Planning Advisor”: need, have, gap, status, ranked actions, month-by-month tracking) | PR #13 (`goals_flow`) | [FEAT-26](../features/FEAT-26-life-scenarios-stress-tests-and-goals.md) |
| Three source groups on the overview (“Our Wealth at Techcombank”, “Custody around the world”, “Self-managed”) | PR #13 | [FEAT-21](../features/FEAT-21-dashboard.md) |
