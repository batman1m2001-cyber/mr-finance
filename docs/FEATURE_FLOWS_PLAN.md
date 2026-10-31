---
title: One flow per feature (93 → about 15)
status: parked
phases:
  - {id: FF0, title: Pin every route's contract and the startup time, status: open}
  - {id: FF1, title: "operonx: a route's body contract of its own (upstream)", status: open}
  - {id: FF2, title: Jobs and thin handlers — market data, admin, housekeeping, evaluation, zone, status: open}
  - {id: FF3, title: Domain features — allocation, evidence, policy, research + newsletter, status: open}
  - {id: FF4, title: Events and client features — news + events + impact, agent review, client data in, goals + scenarios, status: open}
  - {id: FF5, title: Pages and the assistant (AgentOp with memory), status: open}
  - {id: FF6, title: Count, docs, full suite, status: open}
rows: []
updated: 2026-10-31
---

# One flow per feature — plan

**Status: parked 2026-10-31** at the owner's request ("save them in a plan to come back later"). Nothing is built yet.

Owner request (2026-10-31): "87 is still very high, see the other, they're big also but have only < 20 flow".
This plan replaces the flow-merge milestone m33 (docs/FLOW_MERGE_PLAN.md on the scratch clone). That one merged only
flows that were copies of each other and stopped at 88, because it never questioned one flow per endpoint.

## 1. Why there are 93

Counted on main 369a72d: `grep -rn "@graph" --include=*.py src app` gives 93.

- `app/main.py` gives each of its 68 HTTP Services and 23 Jobs a graph of its own, plus a couple of shared sub-flows.
- **58 of the 93 are a single op** (`START >> op >> END`): request handlers wrapped in a graph. Of the rest, 9 have
  2 ops, 8 have 3 and 18 have 4 or more.
- The callbot, which is about as big, has 14 flows, and each is a real pipeline.

So the number comes from one flow per endpoint, not from how complex the app is.

## 2. The target: about 15 feature flows

Each feature flow takes an `action` input and branches on it. Each route binds its own action with `variants`, so
every URL, job name and schedule stays the same.

| # | Flow | Holds | Today |
|---|---|---|---|
| 1 | pages | dashboard, overview, timeline, money flows, feed, search, risk, contacts | ~10 |
| 2 | assistant | assistant, copilot and voice, on the agent-with-memory node (AgentOp + sessions, as src/declare/graph.py) | 9 |
| 3 | allocation | | 9 |
| 4 | evidence | | 5 |
| 5 | policy | | 4 |
| 6 | research + newsletter | | 6 |
| 7 | news + events + impact | | 7 |
| 8 | agent review / decide | | 5 |
| 9 | client data in | statements, declare | 5 |
| 10 | goals + scenarios | | 5 |
| 11 | admin | accounts, config, control | 8 |
| 12 | market data | one job flow; each of the 11 scheduled jobs passes its source | 11 |
| 13 | evaluation | trial, accuracy, agent eval | 4 |
| 14 | zone | | 2 |
| 15 | housekeeping | heartbeat, audit, ingest, reference | 4 |

```python
@graph
def allocation_flow(action, client_id=None, by=None, tilt=None, ...):
    # "view" | "send" | "override" share check → consolidate → case; "tilt" … ; one branch per action
    ...

Service("allocation_tilt", http("POST", "/api/allocation/tilt"), graph=allocation_flow,
        variants={"tilt": {"action": "tilt"}}, body=tilt_body)   # body=: FF1
```

## 3. Decisions

**D1. Every route keeps its exact request contract. This needs FF1 upstream first.** Checked in the installed
operonx 1.30.1 (`operonx/app/serve/runner.py` 440–462): an HTTP door refuses an unknown body field by checking it
against the union of every variant's graph parameters. A missing required parameter is refused by the same rule.
In one graph per feature, every parameter becomes optional and shared across routes. So without FF1, `/api/allocation/tilt`
would accept `send`'s fields and run without its required `client_id`. Those requests get a 400 today. This is what
stopped m33, and it is still true.

FF1 fixes it in operonx, which is upstream: `Service(..., body=fn)`. A plain function's signature (names, which are
required, defaults) is that route's body contract. The door checks it before any run, then fills the graph's
parameters from it. Without `body=`, the graph's parameters are the contract, as they are today. It also lets a
one-op handler keep its own signature after it joins a feature flow.

**D2. No logic change.** Each `action` branch runs the same ops in the same order with the same inputs as the flow
it replaces. Existing tests are not edited. New tests only pin things down.

**D3. The assistant reuses the agent node with memory.** Assistant, copilot and voice turns run on AgentOp with
sessions, the way src/declare/graph.py does, instead of `Runner` called by hand in `turn.py`. The event sequence
stays the same, pinned by FF0.

**D4. Startup is measured, not assumed.** 68 routes each compile their variant of a bigger graph. FF0 records the
time to build `APP` and compile every service. If FF2 makes it more than 20% slower, FF1 also caches compiles by
(graph, binding) before FF3 goes on.

**D5. The tracing config follows the routes.** `operonx.toml` `[tracing.services.<name>] sinks = []` is keyed by
service name, and service names don't change.

## 4. Phases

- **FF0: pin the contract.** One test generated from the current code covers every Service: method, path, required
  fields, accepted fields, and the response to a canned request. It also covers every Job (name, schedule) and the
  assistant's stream event sequence. The m33 F1 card wrote a similar test, on branch `milestone/m33/card/F1` of the
  scratch clone; reuse it if that clone still exists. Record the startup baseline.
- **FF1: operonx `Service(body=)`, upstream (Operon repo).** Include its tests and a guide entry. Release it, then
  bump `pyproject.toml`.
- **FF2–FF5: the feature groups** from the table, one commit per feature. Each has the FF0 test and the tests near
  the change.
- **FF6: final pass.** Flow count (the grep above, target < 20), AGENTS.md and the docs that name flows, startup
  after vs before, and the full suite once (~30 min).

## 5. When it resumes: through the studio assistant, measured

The owner also wants to know whether the studio assistant performs close to plain Claude Code. Run it as an A/B:
the same brief, the same model (Sonnet) and the same claude binary go to the studio assistant (a scratch studio on a
clone) and to `claude -p` with the studio's full reach (`--permission-mode acceptEdits --allowedTools Bash WebFetch
WebSearch`) on a second clone. Compare time, cost, tool calls, interventions and the result (flow count, FF0 test,
full suite).

A first try on 2026-10-31 ran 2.5 min before it was stopped to park this plan, so it's too short to judge. Both
arms read the same files at about the same pace. In 87 s the studio arm found D1's approach ("one @graph per
feature, compiled once per build-time route"). One prompt difference to watch: the studio's system prompt says
"plan doc first, stop at the end of a phase". On a request to work end to end, that can cost an owner reply per
phase that plain Claude Code doesn't need.
