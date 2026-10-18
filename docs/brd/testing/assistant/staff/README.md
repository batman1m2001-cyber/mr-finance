# The staff assistant stress test

This folder answers the owner's request of 2026-10-18
(`docs/brd/sources/owner_requests/2026-10-18_staff_assistant_stress.md`). The request: test each staff role's
assistant the way the customer's was tested, as its users would use it, end to end; fix what fails; report
honestly. The plan and its decisions are in `docs/STAFF_STRESS_PLAN.md`. The customer's test is in the folder above.

| File | What it is |
|---|---|
| [catalogue.md](catalogue.md) | The conversations, by role and category, with their checks. Source: `scripts/stress_staff_catalogue.py`; data: `catalogue.json` |
| [results.md](results.md) | Each conversation's verdict, cost and latency in the final runs, linked to its transcript |
| [defects.md](defects.md) | Every defect found, ranked by severity, with its cause, fix, regression test and status; the grader faults |
| [coverage.md](coverage.md) | The BRD and owner requirements the conversations test, and whether they held |
| [readiness.md](readiness.md) | The assessment: what is ready, what remains, the spend |
| [browser.md](browser.md), `browser/` | The browser pass on each desk (desktop, phone, provider down): its records and screenshots |
| `review.json` | My verdicts by hand where they differ from the machine checks |
| `runs/<tag>/` | Every run: per conversation, a JSON record (the answer, its events, the state read back) and a Markdown transcript. `final`, `final-fail` and `final-s3` are the reported ones |

To run it again, on a served copy of the state (never the live demo):

```bash
# 1. a copy: MF_STATE on a copy of state.db and assistant.db, served on :8041 with MF_JOBS=off; then the working day
MF_STATE=<copy>/state.db .venv/bin/python -P scripts/stress_staff_seed.py --base http://127.0.0.1:8041
# 2. the catalogue (the real model; about US$0.16)
.venv/bin/python -P scripts/stress_assistant.py --catalogue docs/brd/testing/assistant/staff/catalogue.json \
    --out docs/brd/testing/assistant/staff/runs --state <copy>/state.db --tag <tag>
# 3. the failure modes, on a second copy served with LLM_BASE_URL on a dead port (:8042)
.venv/bin/python -P scripts/stress_assistant.py --catalogue docs/brd/testing/assistant/staff/catalogue.json \
    --out docs/brd/testing/assistant/staff/runs --server fail --base http://127.0.0.1:8042 --state <copy2>/state.db --tag <tag>-fail
# 4. the reports
.venv/bin/python -P scripts/stress_report.py --dir docs/brd/testing/assistant/staff \
    --name "The staff assistant stress test" --run <tag> --run <tag>-fail
# 5. the browser pass (Playwright; a few cents), and the same on the dead provider
.venv/bin/python -P scripts/stress_staff_browser.py <out-dir>
.venv/bin/python -P scripts/stress_staff_browser.py <out-dir> --fail --base http://127.0.0.1:8042
```

Each step needs the copy reset to its seeded state, because the conversations write.

The regression tests for the defects fixed are in `tests/test_staff_stress.py`. They run offline, with no model,
and cost no credit.
