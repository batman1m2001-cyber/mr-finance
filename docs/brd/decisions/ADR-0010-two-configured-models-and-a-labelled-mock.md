# ADR-0010 — Two configured models, refused if equal; a labelled mock

- **Status:** accepted
- **Date:** 2026-10-15
- **Sources:** docs/NEWS_IMPACT_PLAN.md A8, §9

## Context

BRD §8: the challenger must use a different model from the CIO agent; no server-side fallback; three run modes including mock.

## Decision

- `llm:cio` and `llm:challenger` in `resources.yaml`, from `LLM_MODEL_CIO` and `LLM_MODEL_CHALLENGER`. Live mode refuses equal models, a truncated reply (`finish_reason == "length"`) and a reply from a model other than the configured one.
- Without both variables every run is the mock (keyword scenarios, rule challenger), labelled “Mô phỏng” on every view — never a silent fallback.
- Token caps per step (analyst 3000, debate 3000, synthesis 6000, challenger 4000; challenger capped at 8 findings).

## Consequences

- The live demo (oneweath.ngrok.app) runs mock until the owner sets the two variables; each live agent run makes about 8 model calls.
