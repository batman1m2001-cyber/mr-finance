# FEAT-14 — Versioned configuration with owners and approval

| | |
|---|---|
| Type | BRD capability — every item of the BRD's §13.1 table (11 kinds; F1, F4) |
| Requirements | BRD-FR-701, BRD-BR-07 (model parameters), BRD-RULE-SEC-04, BRD-RULE-SEC-05, BRD-RULE-AI-02, BRD-RULE-MEAS-07, BRD-NFR-06 |
| Users | CIO (factor model, thresholds, return assumptions), Compliance (restricted list, forbidden phrases, consent), Admin (news and price sources, ticker map, RM assignment, prompts, models) |
| Entry points | [SCR-CIO-09 Cấu hình](../ux/screens/cio.md#scr-cio-09--cấu-hình-versioned-configuration) (CIO, Compliance, Admin); `GET /api/config`, `GET /api/config/{id}`, `POST /api/config/propose`, `POST /api/config/decide` |
| Decision | [ADR-0016](../decisions/ADR-0016-configuration-two-person-rule.md) |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Behaviour
`src/control/config.py`. Kinds, owners, two-person rule:

| Kind | Version 1 | Owner | Two people |
|---|---|---|---|
| factor_model | `data/factor_model.json` | CIO | yes |
| thresholds | `pre_review_pct` −0.05, `concentration_share` 0.4, `modelled_share` 0.5, `implausible_share` 0.25 | CIO | yes |
| restricted | `news_config.json` → `restricted` | Compliance | yes |
| news_sources | `news_config.json` → `sources` | Admin | no |
| price_sources | `market_sources.json` (jobs, series and their sources in order; FEAT-35) | Admin | no |
| ticker_map | `market_sources.json` → `ticker_map` (demo ticker → exchange symbol) | Admin | no |
| rm_assignment | `data/people/staff.json` → `teams` (family → RM) | Admin | no |
| return_assumptions | `config.RETURNS`: deposit 5 %, balanced portfolio 7 %, inflation 4 %, withdrawal 4 %, rental yield 3.5 %, best deposit 6.5 % | CIO | no |
| forbidden_phrases | `recommendation` (buy/sell wording a view must not use, §8.2) and `compliance` (wording a client-facing regulation note must not use, FR-604) | Compliance | no |
| consent | the consent text and version, and whether Open API reads and the family view need each person's consent | Compliance | no |
| prompts | `views/prompts.py::DEFAULT` (guard, the analyst groups, the four step prompts) | Admin | yes + eval set |
| models | the two agent models; version 1 is `LLM_MODEL_CIO` / `LLM_MODEL_CHALLENGER` from .env | Admin | yes + eval set |

A user of the owner's role proposes (content checked; refused if identical or if another proposal waits);
a user of that role approves — not the proposer where two people are required — or rejects. Approval makes the
version ACTIVE and the previous one SUPERSEDED. Every step goes in the audit chain with the content hash. What
uses it: the engine's default model and every new run's snapshot (factor model and thresholds frozen with the
run: an old run still recomputes to the dong), the post-check limits, the RM pre-review flag, the news gates
(sources, restricted list); the life-scenario simulator (return assumptions); the format check of every view and
the regulation-note check (forbidden phrases); the family view and Open API reads (consent); every agent step
(prompts: each node records the prompts version id; models: the client is built for the configured model on the
same provider). The demo reset returns to version 1. Everyone acts as themselves (signed in); the page shows the
proposer that a second person must approve (the server refuses it as well).

**Prompts and models: the eval set (MEAS-07).** A proposal of either is approved only after the fixed eval set
(`data/agent_eval.json`, `src/views/evalset.py`) passed on it: the `agent_eval` job (every minute) runs the six
sample events through every agent step with the proposal in force for that run only, as agent runs `eval` on the
proposal's id, and keeps the result on the proposal. It passes when all six give a valid view the challenger
answered and at least 5 of 6 shock the expected factor the expected way (one sample carries a prompt injection).
Without the AI switch and two different models it cannot run, so the proposal cannot be approved.

**NFR-06.** A new asset class: `loadings.classes` in the factor model (label and loads per factor unit) — the
engine values it, the agents' catalogue names it. A new analyst group: a lens in `prompts.lenses` (label, task,
factors) runs beside the BRD's four. A new model: `models`. Stays code: the four BRD groups' graph, the debate,
synthesis and challenger steps, and the built-in classes' valuation rules.

## Implementation
`src/control/config.py` (`config_versions` table in `src/control/db.py`), `src/control/{ops,graph}.py` (served
writes), reads in `app/web.py`; consumers `src/engine/model.py::default_model`, `src/apply/run.py`,
`src/apply/reads.py::rm_today`, `src/news/ops.py::config`; `web/pages/config.js`.

## Acceptance and tests
`tests/test_config.py`: nothing changes until a second owner approves; the proposer and other roles are refused;
wrong content, identical content and a second pending proposal refused; one-person kind; rejection; a new
restricted name holds news; a run freezes thresholds and model, an old run still verifies, a model change gives a
new model; demo reset; endpoints. Browser: CIO threshold change approved by `cio2`; Compliance restricted-list
change approved by `compliance2`.

`tests/test_config_f4.py`: owners and two people for the new kinds; refused content (keys, equal models, a
prompt without AI-05 or without one of the BRD's four groups); return assumptions drive the simulator; forbidden
phrases change what the guard refuses; consent decides the family view; a prompt change runs the eval set on the
proposal's prompts, needs a second Admin, and then the agents use it and record its version; a failed eval or the
AI off blocks approval; a declared analyst group runs; a declared asset class is valued and catalogued.

## Limitations
- The page edits every kind as JSON except the factor model (proposed from Mô hình or by the API).
- The eval set is small (six samples) and scores the main branch's direction, not the impact rows.
- Measured: the suite took 70 s before and 73 s after (the first version lookup in a test without a state file
  no longer creates the database).
