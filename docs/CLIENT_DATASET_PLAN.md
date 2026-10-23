# A test book of Private clients from a real bank's data, converted to Vietnam (option 2)

**Asked.** Test data with more clients than the five hand-made families (ADR-0005), without drawing every number at
random: take one whole foreign dataset and convert it to Vietnam, so the shape of the book — who holds what, how
holdings change month to month, how income and segment go together — is real, and only the Vietnamese wrapping is
ours. It must be explainable to the jury: one named source, a script, every assumption written down. It is also
what the "Expected effectiveness and impact" criterion is measured on: KPIs computed by running the app over the
book, with a control group, then priced in three scenarios.

**Whose book (revised 2026-10-23).** The book is **Private clients only**. The challenge is set in Private
Banking ("a Wealth Platform … for private clients"); our submission (`nop_bai_cuoc_thi.md` §4, §5.1) sizes the
product on **about 6,500 Private clients**, 88 % coverage ≈ 5,700, and leaves Priority to a later, reduced
version (months 13–24). The first draft of this plan mapped Santander's PARTICULARES to Priority and drew 15 %
Private; that was a sample-size choice with no source, and it is dropped. [ADR-0038](brd/decisions/ADR-0038-a-second-client-set-the-santander-vn-private-book.md),
[Q-27](brd/requirements/open_questions.md).

## The sources

| Source | What it gives | What it does not | Licence |
|---|---|---|---|
| **Santander Product Recommendation** (Kaggle competition, 2016) — the base | ~950k real, anonymised clients of a Spanish bank, 17 monthly snapshots (2015-01…2016-05): age, sex, province, tenure, activity, foreigner and residence flags, household gross income (`renta`), segment (`01 - TOP`, `02 - PARTICULARES`, `03 - UNIVERSITARIO`), and 24 product flags (current/payroll accounts, short/medium/long deposits, funds, securities, pensions, mortgage, loans, credit card, direct debits, taxes…) | **No amounts**: a flag says the client holds a product, not how much. No transactions, no real estate, no gold | Competition rules — **check before use** (step D0) |
| **Survey of Consumer Finances 2022** (US Federal Reserve) — the shape of amounts | Household balance sheets of the top income bands: what each asset class is worth relative to income, and how often it is held | It is the US: too few deposits, gold and property for Vietnam | Public, US government |
| **Our submission's assumptions** — the level of amounts | ≈ 60 tỷ total wealth per Private client, ≈ 35 % of it at TCB (≈ 21 tỷ AUM), 0.8 %/yr revenue on assets, 6 %/yr attrition, 2–3 people per household (`nop_bai_cuoc_thi.md` §4, §5.8) | Marked there as "ước tính sơ bộ, cần thay bằng số thực của Private Banking" | Ours; cited as assumptions |
| **Vietnamese calibration** (our table, cited) | How Vietnamese wealthy households differ: more property, gold and deposits, fewer funds and pensions; the city mix; the occupation mix | — | Each figure carries its source, or is marked "giả định" |

Only Santander is "taken whole". SCF, the submission's figures and the Vietnamese table are aggregates (ratios,
shares, means), committed as small JSON files; no SCF row enters the data. The book's amounts are scaled so its
mean total wealth and TCB share match the submission's — so the KPIs measured on the book and the Cost & Benefit
table speak of the same clients.

## How each Santander field becomes a mr-finance client

The target is the schema of `data/clients/*.json` (scripts/make_fixtures.py) — nothing in the app changes shape.

| Santander | mr-finance | Rule |
|---|---|---|
| `ncodpers` | `id` `S0001…` | stable order (by the source id), so a rerun gives the same ids |
| `age`, `sexo` | `age`, `name` | the age as is; a Vietnamese name drawn from a name table by sex, seeded by the id |
| `nomprov` | `city` | rank-preserving: the most frequent provinces map to the most frequent Vietnamese cities of wealthy clients (TP.HCM, Hà Nội, Đà Nẵng, Hải Phòng, Bình Dương, Đồng Nai, Cần Thơ, Khánh Hòa) |
| `renta` | `income_monthly` | by **percentile**, not by exchange rate: the client's income rank in the sample is placed on the Vietnamese Private income curve (calibration table) |
| `segmento` | `segment` = Private, and a **tier** | `01 - TOP` is the Private book. Within it, the tier by income rank (giả định, D2): bottom 30 % "Mới lên Private", next 55 % HNW, top 15 % UHNW. `02 - PARTICULARES` enters only as its top income decile: to fill TOP if it runs short (`book` = `private_from_particulares`, treated as Private) or, when asked, as "Priority đủ ngưỡng lên Private" (`book` = `priority_upgrade`, labelled apart). `03 - UNIVERSITARIO` dropped |
| `indext`, `pais_residencia`, `indresi` | `nationality`, `residence` | foreign or non-resident → foreigner / Việt kiều; **7 % by default** (5–10 %), set by the sampling (D1) |
| `antiguedad`, `fecha_alta` | `client_since` | the tenure as is, the date shifted by +10 years |
| — (not in Santander) | `occupation` | drawn from the Vietnamese occupation table conditioned on age, income and tier (business owner, executive, professional, retired ≥ 60…) — the submission's Private client is a business owner or senior executive |
| product flags | which `sources` exist | see below |
| the 12 last snapshots | `MONTHS` 2025-10…2026-09 | shifted by +10 years 4 months; a product that appears or disappears between two months becomes an event (a deposit opened, a fund bought, a loan repaid) |

| Santander product | mr-finance holding |
|---|---|
| current, *particular*, *más particular*, e-account, payroll account | `techcombank.accounts` CASA; payroll → salary rows in `transactions` |
| short / medium / long-term deposit | `techcombank.accounts` TD, 3–6 / 6–12 / 12–36 months |
| funds | `techcom_capital.funds` (TCBF/TCEF/TCMF, by risk) |
| securities | `tcbs.stocks` (+ `tcbs.bonds` for the cautious) from `market.json`'s tickers |
| derivatives | `tcbs.margin` |
| pension plan, pensions | `declared` insurance; pension income for ≥ 60 |
| mortgage | `techcombank.loans` home loan **and** its `onehousing.properties` collateral |
| loans | `techcombank.loans` personal |
| credit card | `techcombank.cards` |
| direct debits, taxes | `transactions` categories (bills, tax) |
| junior account | a `dependents` entry |
| guarantees | `declared` business stake |

**The amounts.** For each holding the client has, its value = income × the SCF ratio for that asset class in the
client's income band × the Vietnamese multiplier for that class; then the whole book is scaled once so the mean
total wealth is ≈ 60 tỷ and the share held at TCB ≈ 35 % (the submission's assumptions; both are arguments of the
script, so the real figures replace them in one place); then quantised into real units (shares at the
`market.json` price, fund units at NAV, sqm at the area's price). Property, gold and business stakes — which
Santander cannot show — are given by the Vietnamese ownership rates for the tier. Spending, behaviour in the
April 2026 dip, `benchmark`, `drawdown_limit` and `persona_hint` follow the same rules the hand-made clients obey
(age, holdings, tier), written once in the script.

## Sizes

| Set | Clients | What it is for |
|---|---|---|
| `demo` (ADR-0005) | 5 families, 7 people | the five-minute demo on screen; the test suite |
| `santander_vn` (default) | **1,000** Private | the KPIs: ±3 % at 95 % on a share, every rare case present (concentration, a shortfall before a large outflow, idle CASA, a rate or policy hit), room for a control group of 500 |
| `santander_vn --n 6500` | **6,500** Private | the whole Private book of the submission: NFR-01's scale on real-shaped clients (time, AI cost per client), and the book-wide totals |

The 1,000 are the same mix as the 6,500 (no oversampling), so a KPI measured on them scales to the book without
weights. A bigger sample does not raise the score by itself, nor fix a wrong assumption.

## Decisions

- **The five hand-made families stay the demo.** `tests/` assume them (`== 5` families in test_app.py,
  test_control_group.py; 26 test files name C01–C05). The new book is a second client set,
  `data/datasets/santander_vn/`, chosen with `MF_CLIENTS=santander_vn` (default `demo`). The people store reads the
  set's folder; nothing else changes.
- **Private only.** Every client is Private (above); Priority enters only on request, labelled, for the "Priority
  over the line" use case.
- **One source taken whole, the rest aggregates.** Every client file's `note` says: "Dữ liệu mô phỏng: hồ sơ và sản
  phẩm từ dữ liệu ẩn danh Santander (Kaggle 2016), quy đổi sang Việt Nam; số tiền theo tỷ lệ SCF 2022, giả định của
  bài nộp và bảng hiệu chỉnh Việt Nam." The footer's mock-data line is kept.
- **Deterministic.** One seed; run it again and nothing changes. The raw Santander file (~2.3 GB; the 214 MB zip is
  read as is) is never committed — the script reads it from a path given on the command line, and the row-level
  sample stays under `out/` (git-ignored) until D0 says otherwise.
- **Speed.** Two passes over the raw file (chunked, only the needed columns): a minute or two each, once. The
  conversion of the sample: seconds.

## Steps

- **D0 Licence.** Read the Santander competition rules. If they allow only competition use, keep the plan but commit
  nothing row-level from Santander: commit the converted clients only (no source ids, no original values), or, if
  even that is not allowed, fall back to Santander's aggregate co-ownership rates. Owner decides (TO_DISCUSS).
- **D1 Sample — written.** `scripts/santander_sample.py <train_ver2.csv[.zip]>`: the clients active in 2016-05,
  aged 25–80, income known; drawn from TOP, 7 % foreign, seeded; `--n 1000` by default, `--n 6500` for the book,
  `--priority-upgrade 0.1` to add the labelled Priority group; TOP short → the top decile of PARTICULARES, flagged.
  Writes the 12 last snapshots to `out/santander/sample_<n>.csv.gz` and the mix reached to `sample_<n>.json`.
  Checked on a synthetic file of the same shape (exact counts, 7 % foreign, byte-identical rerun); **not yet run on
  the real file** (needs the Kaggle download, after the rules are accepted).
- **D2 Calibration.** `data/calibration/scf_ratios.json` (from the SCF 2022 summary extract, top income bands, by
  asset class), `data/calibration/submission.json` (the 60 tỷ / 35 % / 0.8 % / 6 % / 2–3 people, cited to the
  submission) and `data/calibration/vn.json` (income curve, tier cut-offs, city mix, occupation mix,
  property/gold/deposit multipliers, names), each figure with its source or "giả định".
- **D3 Convert.** `scripts/make_santander_vn.py`: sample + calibration → `data/datasets/santander_vn/clients/*.json`,
  in the fixtures' schema, using the helpers of make_fixtures.py (salary, loan, card, living rows).
- **D4 History and RMs.** make_history.py and make_people.py take the client set; the book is spread over the RMs at
  ≈ 150 clients per RM (the submission's figure): 7 RMs for 1,000, 44 for 6,500.
- **D5 Switch.** `MF_CLIENTS` in the people store's seed; `.env.example`; reset reseeds the chosen set.
- **D6 Tests.** Every converted client passes the same checks as the hand-made ones (valuation, consolidate, risk,
  dashboard); the book's distributions are within the calibration (all Private, tiers, foreign share, mean wealth,
  TCB share, allocation by tier); a rerun gives byte-identical files. The existing suite is unchanged under
  `MF_CLIENTS=demo`.
- **D7 KPIs.** One script runs the app over the book and writes the table the submission cites: concentration risk,
  shortfall before a large outflow, idle CASA, rate and policy alerts reached, RM preparation time, assistant
  accuracy (`assistant_eval`, `agent_eval`) — with and without the app (`g9-control-group`), and in money in three
  scenarios (low / base / high), each figure marked measured or assumed.
- **D8 Documents.** ADR-0038 accepted, `docs/brd/` per MAINTAINING.md, and a one-page data card
  `data/datasets/santander_vn/README.md`: the source, every transformation, every assumption, the limits — what the
  jury reads.

## Limits (say them)

- The book's structure is a Spanish bank's of 2015–16; Santander's TOP segment is its own definition of a top
  client, not Techcombank Private's threshold. The amounts are a model, not observed.
- It tests the features and the scale, not how accurate a model is on real Vietnamese clients.
- Households: Santander has none; spouses are not created (or a few, marked as derived).

## For the owner

1. The licence (D0).
2. ~~N for the demo book and the scale run~~ — 1,000 and 6,500 (above).
3. ~~The mix~~ — Private only, 7 % foreign / Việt kiều; Priority only as the optional labelled group. Still open:
   the tier cut-offs (30 / 55 / 15 % is giả định), and whether to add the Priority group.
4. The Vietnamese calibration figures: which published sources we cite; and the real figures to replace the
   submission's 60 tỷ / 35 % when Private Banking gives them.
