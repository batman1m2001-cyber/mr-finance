# Maintaining this repository

Update the documents a change affects — not every document. Keep IDs stable and history visible.

| When | Update |
|---|---|
| A feature is proposed | `requirements/` if a new requirement source; a new `features/FEAT-nn-….md` (Type: proposed); matrix rows `planned` |
| A feature is built or changes behaviour | its feature file; the matrix rows (status, code, tests, evidence); screen sections; screenshots; changelog |
| The UI is redesigned | screen sections and inventory; new screenshots (same names); a checklist of where every capability went; never delete a capability silently |
| A business rule changes | never edit the BRD's extracted text; add the change to the feature file and an entry in `open_questions.md` or an ADR; matrix notes |
| An API or data model changes | `architecture/api_reference.md`, `domain_model.md`, the feature file |
| A new agent or workflow | `architecture/agent_workflows.md`, a feature file, matrix |
| A requirement is removed or superseded | keep its row; status and note say so; an ADR says why |
| A defect reveals an undocumented rule | add the rule to the feature file; a `DEF-nn` in `testing/regression_coverage.md` if open |
| A decision changes the architecture | a new ADR; the old one marked superseded |
| A new BRD version arrives | register it in `sources/README.md` (new row), extract the differences, keep the old extraction, update the checker's hash |
| The suite is run for a change | a row in `testing/regression_coverage.md` with the real result |

Always: one line in [`CHANGELOG.md`](CHANGELOG.md), then `uv run python scripts/check_brd_docs.py` (also run by
`tests/test_brd_docs.py`). Templates: [`templates/`](templates/).

Rules: state facts only with a source (BRD section, code path, test, measurement); mark assumptions and
proposals as such; never cite an illustrative image or mock figure as evidence.
