# ADR-0038 — A second client set: a Private book from Santander's clients, SCF households and Techcombank's totals

- **Status:** proposed (D1–D3 done on the real files: 6,500 clients, Σ AUM 428,000 tỷ re-valued by the app; D0 licence open; D4–D8 not built)
- **Date:** 2026-10-23
- **Sources:** plan [`docs/CLIENT_DATASET_PLAN.md`](../../CLIENT_DATASET_PLAN.md); [Q-18](../requirements/open_questions.md),
  [Q-27](../requirements/open_questions.md); BRD-NFR-01; the challenge brief ("a Wealth Platform … for private
  clients"); our submission, `nop_bai_cuoc_thi.md` §4 (about 6,500 Private clients, Priority a later phase);
  techcombank.com (Private: AUM ≥ 23 tỷ or relationship value ≥ 25 tỷ); the owner (6,500 Private clients, AUM
  428,000 tỷ)
- **Keeps:** [ADR-0005](ADR-0005-mock-clients-and-prices-public-news.md) for the demo

## Context

The demo has five hand-made families (ADR-0005). That is enough to show every screen, not to measure the
"expected effectiveness and impact" of the product: no KPI over a book, no comparison with and without the app, no
book-wide figure, and NFR-01's 6,500 is measured only on clones of the five (`scripts/scale_test.py`). Random clients
would make any KPI an artefact of how they were drawn, and no public dataset holds real client-level wealth (none on
Hugging Face or Kaggle; the synthetic ones are no more explainable than ours).

## Decision

1. **A second client set,** `santander_vn`, chosen with `MF_CLIENTS=santander_vn`; `demo` stays the default and the
   test suite's. The app's schema does not change.
2. **Four layers, one source each:**
   - **clients and behaviour** — Santander Product Recommendation (Kaggle, 2016): anonymised clients of a Spanish
     bank, who holds which of 24 products month by month; segment `01 - TOP` only;
   - **the make-up of each client's wealth** — each client matched to one real wealthy household of the Survey of
     Consumer Finances 2022 (public extract; 1,694 households ≥ US$1M net worth), on wealth rank, age and the
     products both show;
   - **the size** — Techcombank's figures: ≥ 25 tỷ per client, 6,500 clients, AUM summing to exactly 428,000 tỷ
     (Pareto, α ≈ 1.61, by Santander's income rank);
   - **Vietnam** — a few multipliers (gold, property, no US retirement accounts), cited or marked "giả định".
3. **Private only, all Techcombank clients.** Total wealth = AUM ÷ the share held at TCB, a curve falling with
   wealth (≈ 35 % mean, giả định), rerun at 25 / 35 / 50 % wherever a KPI is priced in money.
4. **The book is the 6,500**; every KPI runs on all of it, with and without the app on the same clients. The first
   1,000 of the same draw are a subset for what calls a real model.
5. **Deterministic and uncommitted at the source:** one seed, byte-identical reruns; the raw files and the row-level
   sample are never committed (`out/` is git-ignored) until the competition rules are read (D0).

## Consequences

- KPIs, the with/without difference and the three money scenarios can be computed on a book whose behaviour, wealth
  make-up and size each come from a named source, and rerun by anyone with the two public files.
- The concentrated cases are real: 51 % of SCF's rich households hold more than half their wealth in one class.
- The book is labelled "Dữ liệu mẫu" everywhere: it tests the features and the scale, not accuracy on Techcombank's
  clients. Santander's TOP is not Techcombank's threshold; SCF's households are American.
- If the licence forbids reuse beyond the competition, only converted clients (no source ids or values) are
  committed, or the plan falls back to Santander's aggregate co-ownership rates.
- When Private Banking gives the AUM by product or the share held at TCB, they replace the assumptions as script
  arguments and the book is regenerated.
