# ADR-0038 — A second client set: a Private book converted from Santander's public data

- **Status:** proposed (D1 written; D0 licence open; D2–D8 not built)
- **Date:** 2026-10-23
- **Sources:** plan [`docs/CLIENT_DATASET_PLAN.md`](../../CLIENT_DATASET_PLAN.md); [Q-18](../requirements/open_questions.md),
  [Q-27](../requirements/open_questions.md); BRD-NFR-01; the challenge brief ("a Wealth Platform … for private
  clients"); our submission, `nop_bai_cuoc_thi.md` §4 (about 6,500 Private clients, Priority a later phase) and §5.8
  (the cost-and-benefit assumptions)
- **Keeps:** [ADR-0005](ADR-0005-mock-clients-and-prices-public-news.md) for the demo

## Context

The demo has five hand-made families (ADR-0005). That is enough to show every screen, not to measure the
"expected effectiveness and impact" of the product: no KPI over a book, no control group, no book-wide figure, and
NFR-01's 6,500 is measured only on clones of the five (`scripts/scale_test.py`). Random clients would make any KPI
an artefact of how they were drawn. The submission and the brief both place the product in Private Banking, sized on
about 6,500 Private clients.

## Decision

1. **A second client set,** `santander_vn`, chosen with `MF_CLIENTS=santander_vn`; `demo` stays the default and the
   test suite's. The app's schema does not change.
2. **One public source taken whole:** the anonymised clients of Santander Product Recommendation (Kaggle, 2016) —
   who holds which of 24 products, month by month — converted to Vietnam by rank (income, province), products mapped
   onto the app's sources. Amounts come from aggregate ratios only: SCF 2022 for their shape, the submission's
   assumptions (≈ 60 tỷ per client, ≈ 35 % at TCB) for their level, a Vietnamese table for property, gold and
   deposits. Every figure carries its source or "giả định".
3. **Private only.** Clients are drawn from Santander's `01 - TOP`, tiered by income (Mới lên Private, HNW, UHNW;
   cut-offs giả định). `02 - PARTICULARES` enters only as its top income decile — to fill TOP if short, flagged —
   or, on request, as a labelled "Priority đủ ngưỡng lên Private" group. 7 % foreign / Việt kiều by default.
4. **Sizes:** 1,000 clients to measure the KPIs (one mix with the book, so no weights), 6,500 for the book and
   NFR-01.
5. **Deterministic and uncommitted at the source:** one seed, byte-identical reruns; the raw file and the row-level
   sample are never committed (`out/` is git-ignored) until the competition rules are read (D0).

## Consequences

- KPIs, the control group's difference and the three money scenarios can be computed by running the app over a book
  shaped like a real bank's, and rerun by anyone with the source file.
- The book is labelled "Dữ liệu mẫu" everywhere: it tests the features and the scale, not accuracy on Techcombank's
  clients. Santander's TOP is not Techcombank Private's threshold.
- If the licence forbids reuse beyond the competition, only converted clients (no source ids or values) are
  committed, or the plan falls back to Santander's aggregate co-ownership rates.
- The submission's 60 tỷ / 35 % are assumptions; when Private Banking gives real figures, they replace them as
  script arguments and the book is regenerated.
