# FEAT-07 — The scenario engine and the factor model

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-BR-08, BRD-NFR-04, BRD-NFR-05, BRD-NFR-06, BRD-RULE-ENG-01…13, BRD-RULE-AI-08 |
| Users | No direct user: called by previews (FEAT-06) and application runs (FEAT-08); the CIO reads the model on [SCR-CIO-07](../ux/screens/cio.md#scr-cio-07--mô-hình-factor-model) |
| Entry points | `engine.evaluate(holdings, branches, model)`, `engine.propagate(branch, model)`; `GET /api/model` |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
Turn approved scenario branches into VND gains and losses for every holding, deterministically, with no AI
(“máy tính con số”). It is pure: no I/O beyond reading the factor-model file.

## Inputs → outputs
- **In:** holdings (value, class, sector, ticker, duration, currency…), 2–4 branches (probability, regime,
  priced-in, 1–5 core shocks: factor, size S/M/L, direction), the factor model.
- **Out:** for each horizon (`1w` = 0.25 month, `3m`, `12m`): `expected`, `p5`, `p10`, `p50`, `p90`, and the
  expected change `by_holding`, `by_class`, `by_factor`, per `branches`; the variance parts (`sd_parts`); the
  model's version and hash.

## Behaviour (BRD §9.1, four steps)
1. **Core shocks:** size from the factor's S/M/L library × direction × priced-in multiplier (1 / 0.5 / 0).
2. **Other factors:** conditional expectation Δn = Σnc Σcc⁻¹ Δc on the regime's covariance (normal or stressed).
3. **Band:** residual Σn|c × horizon months + core-size uncertainty (σ = 40 % of the shock, propagated) +
   idiosyncratic risk of directly held stocks (from R²).
4. **Positions:** each holding's loadings (§9.3, `src/engine/loadings.py`) × each factor's realisation at the
   horizon; branches mixed as a probability-weighted normal mixture; percentiles by bisection on the mixture CDF.
Results are rounded to the dong once; contributions use largest-remainder rounding so they add up to the
expected change exactly ([ADR-0011](../decisions/ADR-0011-engine-in-floats-rounded-to-the-dong.md)).

## The factor model
`data/factor_model.json`, version **FM-DEMO-2026-10**, from `scripts/make_factor_model.py`: the BRD's 15
factors with their S/M/L sizes and realisation (§9.2) as given; volatilities, correlations (incl. GOLD–USDVND
−0.15, USDVND–VN_GOV 0.25), R² and stress multipliers **assumed** ([ADR-0004](../decisions/ADR-0004-assumed-factor-model-parameters.md)).
Stressed regime: correlations × 1.4, clipped to ±0.85, four overrides, eigenvalue repair with a 0.01 floor
(recorded: smallest eigenvalue before −0.17, largest change 0.10). The model is refused if a correlation is
outside [−1, 1], the matrix is not symmetric or not positive definite, or a realisation is outside [0, 1]. Its
hash changes with any parameter.

## Implementation
`src/engine/linalg.py` (Cholesky, SPD solve, Jacobi eigen, `clip_to_correlation`, normal CDF),
`src/engine/model.py`, `src/engine/loadings.py`, `src/engine/scenario.py`; `ENGINE_VERSION = "engine-1"`.

## Acceptance and tests
`tests/test_engine.py` — 20 test functions (29 cases), among them
`::test_the_core_moves_as_given_and_the_rest_by_conditional_expectation`, `::test_two_core_shocks_follow_the_solved_system`,
`::test_the_band_has_the_three_parts`, `::test_bands_are_ordered_and_widen_with_the_horizon`,
`::test_priced_in_multipliers_scale_the_move_and_its_uncertainty`, `::test_the_expected_change_is_the_probability_weighted_branch_mean`,
`::test_the_contributions_add_up_to_the_expected_change`, `::test_the_same_inputs_give_the_same_numbers_to_the_dong`,
`::test_the_brd_gold_example_has_its_structure`, `::test_the_model_has_the_brds_fifteen_factors_and_both_regimes_are_valid_covariances`,
`::test_a_wrong_factor_model_is_refused`, `::test_wrong_branches_are_refused`.

## Limitations
- Parameters are assumed; the BRD's out-of-sample validation (§16.2) cannot be reproduced without history.
- Tails are normal (thin); P5 is shown as a reference only (BRD F09).
- The pre-BRD stress tests and price-moving policy rules do not use this engine yet (ADR-0007).
