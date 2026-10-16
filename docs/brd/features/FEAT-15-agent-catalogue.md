# FEAT-15 — Agent catalogue and the Agent Ecosystem Map

| | |
|---|---|
| Type | BRD capability — built 2026-10-16 |
| Requirements | BRD-FR-703, BRD-RULE-MEAS-04, BRD-RULE-AI-01, OWN-AS-20, OWN-AS-21, OWN-AS-22 |
| Users | CIO, Compliance, Admin |
| Entry points | [SCR-CIO-08](../ux/screens/cio.md#scr-cio-08--agent-the-ecosystem-map-catalogue-and-ai-quality) (CIO and Compliance → Agent); `GET /api/agents/catalogue?days=7`; `GET /api/agents` (mode, models, budget); `GET /api/agents/map`, `GET /api/agents/map/<part>[?run=<id>]` (A7); the panel's “Bản đồ agent →” |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Behaviour
`src/views/catalogue.py::catalogue` lists five language-model tasks — Agent CIO, Agent Phản biện, Agent Chính
sách (not built), Diễn giải nội bộ (templates), the Copilot router — each with purpose, owner, risk and why, the
BRD §8 default model, the model or mode configured now, what it may read, the latest stored run, and the
open-source references the BRD names (TradingAgents, FinRobot; operonx in place of LangGraph, ADR-0002).
`quality(days)` counts, from stored views, challenges and agent runs, for the period and all time: views decided,
the share the CIO edited, challenger findings and critical ones, agent runs and errors, format retries (§16.3).

## The Agent Ecosystem Map (built in ASSISTANT_PLAN A7, 2026-10-17; ADR-0033)

The page opens on the map; the catalogue stays below it.

1. **Overview**: the person; the front door (the assistant, the keyword fallback, its tools in four families); the
   data; the CIO desk; the rules; the background agents — each part with its state (Đang chạy, Đang chờ, Hoàn tất,
   Lỗi, Chưa chạy) and the last day's runs; a count of parts per state; a strip of the five steps of a question
   (Hỏi → Chọn công cụ → Đọc dữ liệu được phép → Ghi: chờ xác nhận → Trả lời có nguồn) that lights their parts.
2. **Lines**: only what the code does; hovering a part lights its lines and fades the rest.
3. **A part** opens a drawer: what it does, what it may read, its model, its jobs, each line with its label and the
   code that makes it, its tools (for a tool family) and its last 20 runs.
4. **A run** opens its steps: a job's items and their ops from the trace, an agent run's nodes, a turn's tools — with
   status and time; never a prompt, a question or an answer.
5. **Phone**: a list per group; the lines are in each part's drawer.

States are read from records (assistant.md §7, “As built (A7)”).

## Implementation
`src/views/catalogue.py`, `src/views/ecosystem.py`; routes in `app/web.py`; `web/pages/agents.js`; styles “A7” in
`web/core/tokens.css`; the panel's link in `web/copilot.js`; nav “Agent” for CIO, Compliance and Admin.

## Acceptance and tests
`tests/test_catalogue.py` (six fields per entry, BRD order, policy agent marked not built; latest run and quality
from the store after a mock run and an approval; endpoint and bad `days`). The map: `tests/test_agent_map.py` (every
line's code exists, every tool on the map once, icons from the kit; the assistant's services keep no trace; the policy
sweep, consolidator and CIO desk states match the traces of the same runs; the assistant's from its audited turns;
served to the desk), `tests/test_access.py` (CIO, Compliance and Admin only), `tests/ui/test_agent_map_ui.py`
(every part and line drawn, lit, a run opened; a list on a phone; the panel's link).

## Limitations
Owners and risk levels are the BRD's, held in code (not versioned configuration, FR-701). No weekly e-mail: the
report is on the page. The map's parts and lines are held in code (a test keeps them true to it); the states are
read when the page opens (“Làm mới” reads them again), not pushed.
