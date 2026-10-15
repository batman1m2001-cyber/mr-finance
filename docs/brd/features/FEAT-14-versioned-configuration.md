# FEAT-14 — Versioned configuration with owners and approval

| | |
|---|---|
| Type | BRD capability — built 2026-10-16 for four kinds |
| Requirements | BRD-FR-701, BRD-BR-07 (model parameters), BRD-RULE-SEC-04, BRD-RULE-SEC-05, BRD-NFR-06; not yet BRD-RULE-AI-02 |
| Users | CIO (factor model, thresholds), Compliance (restricted list), Admin (news sources) |
| Entry points | [SCR-CIO-09 Cấu hình](../ux/screens/cio.md#scr-cio-09--cấu-hình-versioned-configuration) (CIO and Compliance); `GET /api/config`, `GET /api/config/{id}`, `POST /api/config/propose`, `POST /api/config/decide` |
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

A user of the owner's role proposes (content checked; refused if identical or if another proposal waits);
a user of that role approves — not the proposer where two people are required — or rejects. Approval makes the
version ACTIVE and the previous one SUPERSEDED. Every step goes in the audit chain with the content hash. What
uses it: the engine's default model and every new run's snapshot (factor model and thresholds frozen with the
run: an old run still recomputes to the dong), the post-check limits, the RM pre-review flag, the news gates
(sources, restricted list). The demo reset returns to version 1. The page leaves the proposer out of the
approver list for two-person kinds (the server refuses it as well: op errors do not reach clients).

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

## Limitations
- Return assumptions, forbidden phrases, data-sharing consent, price sources and ticker mapping are not yet
  configuration; prompts and AI models stay code and environment (RULE-AI-02).
- The page edits thresholds and the restricted list as JSON; the factor model and sources are proposed through
  the API (large files). Admin has no screen (no Admin role in the switcher).
- Measured: the suite took 70 s before and 73 s after (the first version lookup in a test without a state file
  no longer creates the database).
