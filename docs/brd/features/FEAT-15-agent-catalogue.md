# FEAT-15 — Agent catalogue

| | |
|---|---|
| Type | BRD capability — built 2026-10-16 |
| Requirements | BRD-FR-703, BRD-RULE-MEAS-04, BRD-RULE-AI-01 |
| Users | CIO, Compliance |
| Entry points | [SCR-CIO-08](../ux/screens/cio.md#scr-cio-08--agent-catalogue-and-ai-quality) (CIO and Compliance → Agent); `GET /api/agents/catalogue?days=7`; `GET /api/agents` (mode, models, budget) |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Behaviour
`src/views/catalogue.py::catalogue` lists five language-model tasks — Agent CIO, Agent Phản biện, Agent Chính
sách (not built), Diễn giải nội bộ (templates), the Copilot router — each with purpose, owner, risk and why, the
BRD §8 default model, the model or mode configured now, what it may read, the latest stored run, and the
open-source references the BRD names (TradingAgents, FinRobot; operonx in place of LangGraph, ADR-0002).
`quality(days)` counts, from stored views, challenges and agent runs, for the period and all time: views decided,
the share the CIO edited, challenger findings and critical ones, agent runs and errors, format retries (§16.3).

## Implementation
`src/views/catalogue.py`; route in `app/web.py`; `web/pages/agents.js`; nav “Agent” for CIO and Compliance.

## Acceptance and tests
`tests/test_catalogue.py` (six fields per entry, BRD order, policy agent marked not built; latest run and quality
from the store after a mock run and an approval; endpoint and bad `days`).

## Limitations
Owners and risk levels are the BRD's, held in code (not versioned configuration, FR-701). No weekly e-mail: the
report is on the page.
