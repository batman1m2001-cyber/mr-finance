# A test book of Private clients from a real bank's data, converted to Vietnam (option 2)

**Asked.** Test data with more clients than the five hand-made families (ADR-0005), without drawing every number at
random: take one whole foreign dataset and convert it to Vietnam, so the shape of the book — who holds what, how
holdings change month to month, how wealth is spread — is real, and only the Vietnamese wrapping is ours. It must be
explainable to the jury: named sources, a script, every assumption written down. It is also what the "Expected
effectiveness and impact" criterion is measured on: KPIs computed by running the app over the book, with and without
the app, then priced in three scenarios.

**Whose book.** **Private clients only, all of them Techcombank clients.** The challenge is set in Private Banking
("a Wealth Platform … for private clients"); our submission sizes the product on about 6,500 Private clients and
leaves Priority to a later phase. Techcombank Private requires AUM ≥ 23 tỷ or a total relationship value ≥ 25 tỷ
(three-month average; techcombank.com, "may change by period"). The owner gives the book's size: **6,500 Private
clients, AUM 428,000 tỷ** (≈ 65.8 tỷ each; scope and source to be confirmed, Q-27).
[ADR-0038](brd/decisions/ADR-0038-a-second-client-set-the-santander-vn-private-book.md).

## Four layers, one source each

| Layer | Source | What is real |
|---|---|---|
| **1. Clients and behaviour** | **Santander Product Recommendation** (Kaggle, 2016): anonymised clients of a Spanish bank, 17 monthly snapshots, 24 product flags | who holds which products, how that changes month to month, age, sex, tenure, the income rank |
| **2. The make-up of each client's wealth** | **Survey of Consumer Finances 2022** (US Federal Reserve), public household-level extract `SCFP2022.csv`: 4,595 households × 5 implicates; it oversamples the rich — **1,694 households ≥ US$1M net worth, 682 ≥ $10M, 408 ≥ $30M** | the balance sheet of a real wealthy household: deposits, bonds, funds, stocks, retirement and insurance, home, other property, business, debts |
| **3. The size** | **Techcombank's own figures**: ≥ 25 tỷ per client, 6,500 clients, 428,000 tỷ AUM | the floor, the count, the total |
| **4. Vietnam** | a few cited multipliers (gold, property share, no US retirement accounts) | nothing: these are the only assumptions on the amounts, each marked "giả định" or cited |

No synthetic dataset from Hugging Face or Kaggle is used: none holds real client-level wealth, and a synthetic one
is no more explainable than ours. Spain's EFF (Banco de España; same country as Santander, rich oversample from the
wealth tax) would fit layer 2 better; access needs an application, so SCF now, EFF if access comes in time — the
pipeline does not change.

What the SCF's rich households look like (weighted, net worth ≥ $1M): home 31 %, retirement and insurance 24 %,
business 10 %, funds 10 %, other property 9 %, deposits 7 %, stocks 6 %, bonds 1 %. **51 % of them have more than half
their wealth in one class** (19 % in a business, 22 % in property): the concentrated cases the KPIs look for, which
an average allocation with noise never produces.

## How each Santander field becomes a mr-finance client

The target is the schema of `data/clients/*.json` (scripts/make_fixtures.py) — nothing in the app changes shape.

| Santander | mr-finance | Rule |
|---|---|---|
| unused columns (`ind_empleado`, `conyuemp`, `canal_entrada`, `indfall`, `tipodom`, `cod_prov`, `indrel*`, `tiprel_1mes`, `ult_fec_cli_1t`, `ind_nuevo`) | — | dropped |
| `ncodpers` | `id` `S0001…` | renumbered by the source id; **the source id is not kept** |
| `age`, `sexo` | `age`, `name` | the age as is; a Vietnamese name drawn by sex, seeded by the id |
| `nomprov` | `city` | **rank kept, shares rebalanced**: provinces ordered by frequency are cut to the Vietnamese city shares of wealthy clients (TP.HCM, Hà Nội, then Đà Nẵng, Hải Phòng, Bình Dương, Đồng Nai, Cần Thơ, Khánh Hòa). One-to-one would put 66 % in TP.HCM, because 66 % of the sample is in Madrid |
| `renta` | the rank of AUM | **never converted by exchange rate**: only its rank is used (layer 3, below) |
| `segmento` | `segment` = Private, and a tier | `01 - TOP` only. Tier by AUM at TCB: 25–50 tỷ "Mới lên Private", 50–100 HNW, 100–250 HNW cao, 250–750 VHNW, ≥ 750 UHNW |
| `indext`, `indresi`, `pais_residencia` | `nationality`, `residence` | foreign or non-resident → foreigner / Việt kiều, 7 % (set by the sampling) |
| `antiguedad`, `fecha_alta` | `client_since` | the tenure as is, the date +10 years |
| — | `occupation` | by age, tier and the matched household's business share (business owner, executive, professional, retired ≥ 60) |
| product flags | which TCB `sources` exist | table below |
| the 12 last snapshots | `MONTHS` 2025-10…2026-09 | +10 years 4 months; a flag that changes between two months becomes an event with an amount |

| Santander product (share of the 6,500 holding it, May 2016) | mr-finance holding at TCB |
|---|---|
| current account (61 %) | `techcombank.accounts` CASA |
| *particular*, *más particular*, e-account, savings (25 %, 16 %, 53 %, ≈ 0 %): interest-paying accounts | read as term deposits (with CASA keeping 5–25 % of the deposits). Read as CASA in the first run, they left 4,894 clients with over 5 tỷ idle; read as deposits, 535 clients hold no term deposit and 427 keep over half their AUM in CASA — the idle-cash cases, from the data |
| payroll / pension payroll (26 % / 30 %) | salary or pension rows |
| long-term deposit (48 %); short and medium (≈ 1 % each) | `techcombank.accounts` TD. Santander barely shows short terms, so **the tenor is drawn again** across 1–36 months (giả định), else every client would hold 12–36 months |
| funds (19 %) | `techcom_capital.funds` |
| securities (20 %) | `tcbs.stocks`, `tcbs.bonds` |
| derivatives (0.2 %) | `tcbs.margin` |
| pension plan (8 %) | insurance |
| mortgage (2.3 %), loans (0.2 %) | `techcombank.loans`. **Few loans in Santander**: debts and property come mostly from the matched SCF household (47 % of SCF's rich have a mortgage); a TCB loan only where Santander shows one |
| credit card (23 %) | `techcombank.cards` |
| direct debits, taxes | `transactions` categories |

## The amounts: how a client is matched to an SCF household

1. **AUM at TCB.** The 6,500 are ranked by `renta`, with a little noise (income does not decide wealth; rank
   correlation ≈ 0.7, giả định). The rank is placed on a Pareto curve with floor 25 tỷ and α ≈ 1.61 — the α that
   gives a mean of 65.8 tỷ. Then the part above the floor is scaled so the book sums to **exactly 428,000 tỷ** and no
   client is under 25 tỷ. Result: ≈ 67 % at 25–50 tỷ, 22 % at 50–100, 8 % at 100–250, 2 % at 250–750, 0.4 % ≥ 750;
   median ≈ 38 tỷ; the ≈ 700 clients over 100 tỷ hold ≈ 40 % of AUM.
2. **The share at TCB (s)** falls with wealth — the richer keep a smaller part at one bank: ≈ 45 % at 25 tỷ to ≈ 20 %
   at ≥ 750 tỷ, book mean ≈ 35 % (giả định; the curve is a script argument). **Total wealth W = AUM ÷ s.** The KPIs
   priced in money are rerun with s = 25 %, 35 %, 50 % to show which conclusions hold.
3. **The match.** Each client is paired with one SCF household with net worth ≥ US$1M, nearest on:
   - wealth rank: the client's rank of W in the book against the household's weighted rank of net worth (rank, not
     exchange rate);
   - age, within ±7 years;
   - the same yes/no on what Santander shows: securities ↔ stocks, funds ↔ funds, mortgage ↔ mortgage, pension plan
     ↔ retirement account.

   One implicate of the household, chosen by the seed. A household may serve several clients (6,500 clients, 1,694
   households); each reuse is jittered (±10 % per class) so no two clients are identical.
4. **Vietnam.** The household's shares, with US retirement accounts (no Vietnamese equivalent) moved to deposits and
   insurance, a gold share added, property raised — cited multipliers or "giả định" — then renormalised.
5. **TCB and the rest.** The client's AUM is spread over the TCB products the client holds (Santander's flags), in
   the proportions of the matched household's classes; W × each class − the TCB part is held elsewhere: other banks,
   other brokers, property, business, gold, vehicles (if a household's financial assets are too small to hold the
   AUM, W is raised). TCB loans where Santander shows them, other debts from the household.
6. **Units.** Shares at `market.json` prices, fund units at NAV, m² at the area's price.

Spending, the April 2026 dip, `benchmark`, `drawdown_limit` and `persona_hint` follow the hand-made clients' rules
(age, holdings, tier), written once in the script. The households' members: Santander has none; a spouse or children
for part of the book, marked "suy ra".

## Sizes

| Set | Clients | What it is for |
|---|---|---|
| `demo` (ADR-0005) | 5 families, 7 people | the five-minute demo on screen; the test suite |
| `santander_vn` | **6,500** Private | **the book**: every KPI is computed on all of it (rules are cheap: NFR-01 applied a view to 6,500 families in 167 s); with and without the app on the same clients; the book-wide totals |
| `santander_vn`, first 1,000 | **1,000**, a subset of the 6,500 | only what calls a real model (assistant accuracy, the quality of a written insight), and quick iterations. Not a second sample: the 1,000 are the first 1,000 of the 6,500's draw order |

## Decisions

- **The five hand-made families stay the demo.** `tests/` assume them. The new book is a second client set,
  `data/datasets/santander_vn/`, chosen with `MF_CLIENTS=santander_vn` (default `demo`).
- **Private only, all TCB clients.** Priority enters only on request (`--priority-upgrade`), labelled.
- **Each layer one source.** Every client file's `note`: "Dữ liệu mô phỏng: hành vi từ dữ liệu ẩn danh Santander
  (Kaggle 2016); cơ cấu tài sản từ hộ thật trong SCF 2022 (Fed); quy mô theo AUM Private 428.000 tỷ / 6.500 khách;
  hiệu chỉnh Việt Nam là giả định." The footer's mock-data line is kept.
- **Deterministic.** One seed; run it again and nothing changes. The raw Santander file and the SCF file are never
  committed; the row-level sample stays under `out/` (git-ignored) until D0 says otherwise.
- **With and without the app** on the same 6,500: without, an RM reviews 40 of 150 clients a quarter, chosen by the
  product to sell (the submission's figures); with, all 150 get the app's picture and alerts. Both run on every
  client — stronger than splitting the book in two.

## Steps

- **D0 Licence.** The Santander competition rules (owner). SCF: public US-government data, cited.
- **D1 Sample — done.** `scripts/santander_sample.py <train_ver2.csv.zip>` (the zip read as is). Real run, 2026-10-23:
  45,948 clients eligible (active, 25–80, income known; TOP and the top income decile of PARTICULARES); **6,500 drawn,
  all from TOP, none filled**, 7.0 % foreign, 48 provinces, median age 52, 96 % with all 12 months, 64.5 % with at
  least one product change (16,807 events); 2 min 49 s. Nested: the 1,000 are inside the 6,500.
- **D2 Calibration — done.** `data/calibration/tcb.json` (25 tỷ floor, 6,500, 428,000 tỷ, the tier cut-offs, the
  share-at-TCB curve), `data/calibration/vn.json` (city shares, gold, property, retirement mapping, names,
  occupations, TD tenors, events), each figure with its source or "giả định".
- **D3 Match and convert — done.** `scripts/make_santander_vn.py <sample> <SCFP2022.csv>`: the six steps above →
  `data/datasets/santander_vn/clients/S0001…S6500.json` in the fixtures' schema (make_fixtures.py's helpers), plus
  `book.json` (the book as it came out) and `subset_1000.json`; extra fields `tier`, `nationality`, `client_since`,
  `timeline` (Santander's month-by-month changes, for D4), `provenance` (the SCF household, AUM, total wealth). Real
  run, 2026-10-23, 12.6 s:
  - every client valued by the app's own `wealth.valuation` without an error; AUM at TCB re-valued = **428,000 tỷ**,
    0 đồng off per client (CASA takes the rounding); min 25 tỷ, median 38.8 tỷ, max 9,134 tỷ;
  - share at TCB 35.0 % for the book (51.6 % at the floor, 20 % at ≥ 750 tỷ); total wealth 1.22 million tỷ;
  - tiers 4,331 / 1,452 / 552 / 137 / 28; cities as `vn.json`; 7 % foreign;
  - 601 SCF households used (each ≈ 11 times, jittered); **58.7 % of clients hold more than half their wealth in one
    class** (top class: home 1,973, business 1,871, other property 1,358, deposits 1,009);
  - book allocation by value: business 28.6 %, property 23.3 %, deposits 21.5 %, CASA 7.0 %, funds 6.5 %, stocks
    5.4 %, gold 4.5 %, insurance 2.0 %, bonds 1.2 % — business is the SCF's richest households' (an American trait;
    the Vietnamese property multiplier may need raising: owner);
  - a rerun is byte-identical; the files (76 MB) are git-ignored until D0.
  Simplifications: properties outside TP.HCM and Đồng Nai are declared at a value (market.json has no area there);
  bonds and funds held elsewhere are declared (Open API reads only cash and stocks); no spouses yet.
- **D4 History and RMs.** make_history.py and make_people.py take the client set; ≈ 150 clients per RM → 44 RMs.
- **D5 Switch.** `MF_CLIENTS` in the people store's seed; `.env.example`; reset reseeds the chosen set.
- **D6 Tests.** Every converted client passes the hand-made clients' checks (valuation, consolidate, risk,
  dashboard); the book: all Private, ≥ 25 tỷ each, Σ AUM = 428,000 tỷ, mean share at TCB ≈ 35 %, 7 % foreign, tiers
  as above; a rerun is byte-identical; the suite unchanged under `MF_CLIENTS=demo`.
- **D7 KPIs.** One script runs the app over the 6,500 (model-calling KPIs on the 1,000) and writes the table the
  submission cites, each figure marked measured or assumed:
  - scale: share of affected portfolios assessed per event (100 %), time for the whole book;
  - personalisation: the spread of impact among clients with the same equity weight; precision and recall of who
    is alerted;
  - accuracy: direction and size of the impact against the move, on the April 2026 dip; `assistant_eval`,
    `agent_eval`;
  - risk found: concentration over the threshold, a shortfall before a large outflow, idle CASA, a drawdown over
    the limit, a rate or draft-policy hit;
  - explainability and control: share of insights with source and calculation (100 %), share of recommendations
    reviewed by an RM (100 %), seeded bad recommendations caught by the challenger, audit trail complete (100 %);
  - RM: clients reviewed per quarter per RM (40 → 150), preparation time;
  - money: share of wealth at TCB, attrition, timely cross-sell — low / base / high, with s = 25 / 35 / 50 %.
- **D8 Documents.** ADR-0038 accepted, `docs/brd/` per MAINTAINING.md, and a one-page data card
  `data/datasets/santander_vn/README.md`: the sources, every transformation, every assumption, the limits.

## Limits (say them)

- The behaviour is a Spanish bank's of 2015–16; the make-up of wealth is US households' of 2022; Santander's TOP is
  not Techcombank's threshold. Only the size is Techcombank's.
- It tests the features and the scale, not how accurate a model is on real Vietnamese clients.
- Households: Santander has none; members are derived and marked.

## For the owner

1. The Santander licence (D0).
2. 428,000 tỷ: Private only, or Private and Priority? Its source and date, for the data card.
3. If Private Banking can give **the Private AUM by product** (CASA, TD, bonds, funds, stocks, insurance — six
   percentages), it replaces step 5's split at TCB.
4. The share-at-TCB curve (≈ 35 % mean, falling with wealth) and the tier cut-offs are giả định.
5. Our submission's §5.8 assumes 60 tỷ per client, 35 % at TCB, i.e. 21 tỷ at TCB — under the 25 tỷ floor and a third
   of 65.8 tỷ. It needs correcting whatever happens to this plan (TO_DISCUSS).
