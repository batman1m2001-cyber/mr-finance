# The assistant stress test

The owner's request of 2026-10-17 (`docs/brd/sources/owner_requests/2026-10-17_assistant_stress_test.md`): act as
real customers and test the assistant end to end, through its real interface and backend; fix what fails; report
honestly. Plan and decisions: `docs/ASSISTANT_STRESS_PLAN.md`.

| File | What it is |
|---|---|
| [catalogue.md](catalogue.md) | The conversations, by category, with their checks (source: `scripts/stress_catalogue.py`; data: `catalogue.json`) |
| [results.md](results.md) | Each conversation's verdict, cost and latency in the final runs, linked to its transcript |
| [defects.md](defects.md) | Every defect found, ranked by severity, with its cause, fix, regression test and status |
| [coverage.md](coverage.md) | The BRD requirements the conversations test, and whether they held |
| [readiness.md](readiness.md) | The assessment: what is ready, what blocks, what remains |
| `runs/<tag>/` | Every run: a JSON record (the answer, its events, the state read back) and a Markdown transcript per conversation |
| [browser.md](browser.md), `browser/` | The browser pass (the real panel, desktop and phone): its record and screenshots |

How to run it again (a served copy on its own state; never the live demo):

```bash
# a copy of the state, served on :8041 (MF_JOBS=off), then:
.venv/bin/python scripts/stress_assistant.py --base http://127.0.0.1:8041 --state <copy>/state.db --tag <tag>
# the failure modes on a copy whose model provider URL is dead (:8042):
.venv/bin/python scripts/stress_assistant.py --server fail --base http://127.0.0.1:8042 --state <copy2>/state.db --tag <tag>-fail
.venv/bin/python scripts/stress_report.py --run <tag> --run <tag>-fail
# the browser pass (Playwright, the real model; a few cents):
.venv/bin/python -P scripts/stress_browser.py <out-dir>
```

The regression tests for the defects fixed: `tests/test_assistant_stress.py` (offline, scripted model; no credit).
