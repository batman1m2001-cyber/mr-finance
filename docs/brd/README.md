# OneWealth — Living BRD and product knowledge repository

This directory is the long-term source of truth for **what OneWealth must do, what it does, how people use
it, and why it is built the way it is**. It is versioned with the code. Every feature, redesign, refactor and
product decision updates it; nothing here is rewritten wholesale.

Start here, then follow the links. Everything is in English; the product's UI text and the BRD's own wording
are Vietnamese and are quoted as they are.

## 1. The three layers

| Layer | Question it answers | Where | It never contains |
|---|---|---|---|
| **A. Original requirements** | What the business asked for, in its words | [`requirements/`](requirements/) | our design choices or implementation status |
| **B. Product behaviour** | How each capability works: inputs, rules, states, APIs, errors, tests | [`features/`](features/) | screen layout |
| **C. UI/UX** | Where people meet each capability and how they use it | [`ux/`](ux/) | business rules (it links to them) |

Around them: [`architecture/`](architecture/) (how the system is built), [`decisions/`](decisions/) (why),
[`testing/`](testing/) (how we know), [`assets/`](assets/) (screenshots, mockups) and [`sources/`](sources/)
(the documents everything else is derived from).

The chain every requirement must be traceable through:

```text
BRD requirement ─▶ feature (behaviour) ─▶ screen ─▶ code path / API ─▶ test ─▶ evidence
  requirements/      features/            ux/       architecture/        testing/
```

The single place where the chain is assembled, with a status per requirement, is
[`requirements/requirements_traceability.md`](requirements/requirements_traceability.md).

## 2. Which document is authoritative for what

| Kind of information | Authoritative document | Notes |
|---|---|---|
| The original business requirements | The BRD `.docx` (see [`requirements/original_brd_reference.md`](requirements/original_brd_reference.md)) | Immutable. Not in git (public repo); identified by path and SHA-256 |
| Their extracted, numbered form | `requirements/business_requirements.md`, `functional_requirements.md`, `non_functional_requirements.md`, `business_rules.md` | Faithful extraction with the original Vietnamese; never edited to match the code |
| Requirements of the capabilities that predate the BRD | [`requirements/brief_requirements.md`](requirements/brief_requirements.md) (from [`mr_finance_idea_final.md`](../../mr_finance_idea_final.md)) | The original product brief |
| Requirements of the redesign kit (proposed extensions) | [`requirements/kit_requirements.md`](requirements/kit_requirements.md) | Source: [`sources/redesign_kit_2026-10-15/`](sources/redesign_kit_2026-10-15/) |
| Requests of the product owner (approved extensions) | [`requirements/owner_requirements.md`](requirements/owner_requirements.md) | Source: [`sources/owner_requests/`](sources/owner_requests/) |
| Ambiguities, conflicts, BRD-vs-product divergence | [`requirements/open_questions.md`](requirements/open_questions.md) | Each has a proposed interpretation and an owner |
| **Implementation status of each requirement** | [`requirements/requirements_traceability.md`](requirements/requirements_traceability.md) | The only place a status is stated; other files link to it |
| How a capability behaves | the feature file in [`features/`](features/) | One file per feature |
| Where a capability appears in the UI | [`ux/screen_inventory.md`](ux/screen_inventory.md) and [`ux/screens/`](ux/screens/) | |
| Why something is the way it is | [`decisions/`](decisions/) | Append-only ADRs |
| What changed and when | [`CHANGELOG.md`](CHANGELOG.md) | One line per meaningful change |
| How the code is laid out, how to run it | [`AGENTS.md`](../../AGENTS.md), [`README.md`](../../README.md), [`app/main.py`](../../app/main.py) | This repository links to them; it does not copy them |
| Delivery plans and their history | [`docs/PLAN.md`](../PLAN.md), [`docs/NEWS_IMPACT_PLAN.md`](../NEWS_IMPACT_PLAN.md), [`docs/REDESIGN_KIT_PLAN.md`](../REDESIGN_KIT_PLAN.md), [`docs/UI_REDESIGN_PLAN.md`](../UI_REDESIGN_PLAN.md), [`docs/BRD_COMPLETION_PLAN.md`](../BRD_COMPLETION_PLAN.md) | Plans are history; once a plan item is built, its behaviour is documented here |

When two documents disagree, the order above decides, and the disagreement is recorded in
[`requirements/open_questions.md`](requirements/open_questions.md) — it is never silently resolved.

## 3. Identifiers

Identifiers are stable. A retired item keeps its ID and is marked `superseded` or `removed`; an ID is never
reused.

| Prefix | What | Example | Defined in |
|---|---|---|---|
| `BRD-BR-nn` | BRD business requirement (BRD §4) | `BRD-BR-09` | business_requirements.md |
| `BRD-FR-nnn` | BRD functional requirement (BRD §6) | `BRD-FR-401` | functional_requirements.md |
| `BRD-NFR-nn` | BRD non-functional requirement (BRD §15) | `BRD-NFR-04` | non_functional_requirements.md |
| `BRD-KPI-nn` | BRD success metric (BRD §2) | `BRD-KPI-03` | business_requirements.md |
| `BRD-RULE-<area>-nn` | Rule stated in BRD prose or tables without its own code | `BRD-RULE-GOAL-03` | business_rules.md |
| `BRIEF-<area>-nn` | Requirement of the original product brief | `BRIEF-DASH-04` | brief_requirements.md |
| `KIT-<area>-nn` | Requirement of the redesign kit (proposed) | `KIT-COPILOT-01` | kit_requirements.md |
| `OWN-<area>-nn` | Request of the product owner | `OWN-MOTION-03` | owner_requirements.md |
| `FEAT-nn` | Feature (Layer B) | `FEAT-08` | features/README.md |
| `SCR-<role>-nn` | Screen or significant component | `SCR-CIO-03` | ux/screen_inventory.md |
| `ADR-nnnn` | Decision | `ADR-0006` | decisions/README.md |
| `Q-nn` | Open question, ambiguity or conflict | `Q-04` | requirements/open_questions.md |
| `DEF-nn` | Known defect | `DEF-01` | testing/regression_coverage.md |
| `AST-…` | Visual asset | `SCR-CL-05_desktop-light.jpg` | assets/README.md |

The BRD's own codes are kept as they are (`BR-09` → `BRD-BR-09`, `FR-401` → `BRD-FR-401`), so a reader can go
from this repository to the BRD and back without a lookup table.

## 4. Status vocabulary

Two statuses are kept apart. **Documentation status** says whether a requirement is understood;
**implementation status** says whether the product does it. A requirement can be fully documented and not
built.

**Documentation status**

| Value | Meaning |
|---|---|
| `documented` | Extracted, source located, meaning clear |
| `needs_clarification` | Extracted, but the BRD is ambiguous or contradicts itself or another source; see the `Q-nn` it links to |

**Implementation status** (in the traceability matrix only)

| Value | Meaning | Required evidence |
|---|---|---|
| `implemented_verified` | The behaviour exists and an automated test that exercises it passes | ≥ 1 test cited by name, existing in `tests/`, passing in the run recorded in [`testing/regression_coverage.md`](testing/regression_coverage.md) |
| `implemented_unverified` | The behaviour exists in code, but no automated test exercises it (it may have been checked by hand) | a code path; how it was checked, if it was |
| `partially_implemented` | Part of the requirement is built; the gap is stated | the code path, the test for the built part, and the gap |
| `planned` | Not built; scheduled in a named plan phase | the plan and phase |
| `not_implemented` | Not built and not yet scheduled in any plan | why, and what it would take |
| `blocked` | Cannot be built here without something we do not have (data, infrastructure, a decision) | what blocks it, who can unblock it |
| `out_of_scope_demo` | Applies to the bank deployment, not to this public demo | why, and what the demo does instead |
| `not_applicable` | The requirement is descriptive (it states a fact or a target for someone else) | why |

A screen, a component or a passing build is never evidence on its own: the behaviour behind it must be tested
(rule from [the redesign kit](sources/redesign_kit_2026-10-15/BRD_COVERAGE_AND_ACCEPTANCE.md)).

## 5. How to find things

- **"What does requirement X say?"** → search its ID in [`requirements/`](requirements/).
- **"Is X built?"** → its row in [`requirements_traceability.md`](requirements/requirements_traceability.md).
- **"How does feature Y work?"** → [`features/README.md`](features/README.md) → the feature file.
- **"Where is Y in the UI?"** → [`ux/screen_inventory.md`](ux/screen_inventory.md).
- **"Which code implements Y?"** → the feature file's *Implementation* section, then [`architecture/`](architecture/).
- **"Why is it done this way?"** → [`decisions/README.md`](decisions/README.md).
- **"What does it look like?"** → [`assets/README.md`](assets/README.md).
- **"What is still open?"** → [`requirements/open_questions.md`](requirements/open_questions.md) and the
  `planned`/`blocked`/`partially_implemented` rows of the matrix.

## 6. How to keep this repository up to date

The full procedure is [`MAINTAINING.md`](MAINTAINING.md). In short, for any meaningful change:

1. Update the affected feature file(s) and, if a rule changed, the requirement's notes — never the BRD's
   original text.
2. Update the affected screen sections.
3. Add or replace screenshots in `assets/current_ui/` and register them in `assets/README.md`.
4. Update the traceability rows (status, code, tests, evidence).
5. Add a line to [`CHANGELOG.md`](CHANGELOG.md).
6. Record a significant decision as a new ADR.
7. Run `uv run python scripts/check_brd_docs.py` (links, IDs, coverage, cited tests); it also runs in the test
   suite (`tests/test_brd_docs.py`).

## 7. Contents

```text
docs/brd/
├── README.md                    ← you are here
├── PRODUCT_OVERVIEW.md          the whole product on two pages
├── GLOSSARY.md                  terms (BRD §19.1 and ours)
├── CHANGELOG.md                 what changed, newest first
├── MAINTAINING.md               the update rules
├── sources/                     immutable source register and verbatim copies
├── requirements/                Layer A: extracted requirements, open questions, the traceability matrix
├── features/                    Layer B: one file per feature
├── ux/                          Layer C: IA, journeys, screens, design system, interaction patterns
├── architecture/                system, domain model, data flows, agents, integrations, API
├── decisions/                   ADRs
├── testing/                     acceptance criteria, regression coverage, known defects
├── assets/                      screenshots and mockups, registered
└── templates/                   feature, screen, decision, change
```
