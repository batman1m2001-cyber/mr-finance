# FEAT-04 — The CIO agent (views and scenarios)

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-BR-05, BRD-BR-11, BRD-FR-301, BRD-FR-302, BRD-FR-307, BRD-FR-704, BRD-RULE-AI-01…14, BRD-RULE-WF-03, BRD-RULE-LC-01, BRD-NFR-10 |
| Users | CIO runs it; the result is reviewed by the challenger (FEAT-05) and decided by the CIO (FEAT-06) |
| Entry points | [SCR-CIO-02/03](../ux/screens/cio.md#scr-cio-03--nhận-định-view-detail) “Chạy Agent CIO”; `POST /api/events/run-agent {event_id, by, mode?}` |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
Turn one event into a **view**: a Vietnamese summary, impact rows (−3…+3) and 2–4 scenario branches with
probabilities and core shocks chosen from the shock library. The agent writes scenarios; it never writes a
money figure and never sees client data.

## Preconditions and permissions
Role `cio`. The event exists and is not held for the agent run itself (approval is what holds are checked
against). Mode: `live` only when `LLM_MODEL_CIO` and `LLM_MODEL_CHALLENGER` are both set and differ; else
`mock` ([ADR-0010](../decisions/ADR-0010-two-configured-models-and-a-labelled-mock.md)).

## Behaviour (graph `cio_agent_flow`, BRD §8.1)
1. `gather` — deterministic packet: the event's news (wrapped “DỮ_LIỆU … HẾT_DỮ_LIỆU”), released research, the
   asset-class/sector/ticker/FX catalogue, the 15 factors and their S/M/L library. Opens an agent run and a
   view `VW-nnnn-vN` in `DRAFTING`.
2. Four `analyse` nodes **in parallel**: macro & rates, equities & funds, credit & real estate, commodities &
   other.
3. `discuss` — bull/bear debate **only** when a row is ±2 or more or the groups disagree; at most two rounds;
   otherwise recorded as skipped.
4. `compose` — synthesis, then the schema check (`src/views/schema.py`); on failure back to synthesis, **at most
   two retries**; still failing → the view goes to `AGENT_ERROR` and the CIO sees the errors.
5. `save_view` — the valid view is stored with its content hash → `PENDING_CHALLENGE`.
6. `review` — the challenger (FEAT-05).
Every node is recorded with input, prompt, prompt version (`v1`), model, output and time (FR-704).

## Rules (schema, BRD §8.2)
summary in Vietnamese, ≥ 20 characters, no buy/sell wording; ≥ 1 impact row with a target in the catalogue,
level −3…+3, direction, horizon, confidence, rationale and sources; `priced_in` ∈ {chưa, một phần, đã hết};
2–4 branches, probability 5–95 %, sum 100 % ± 1.1; regime normal/stressed; 1–5 core shocks per branch from the
15 factors, size S/M/L, up/down; rationale ≥ 20 characters; every source id belongs to the event.
The live synthesis prompt requires a stressed branch to include VN-Index and real-estate credit among its core
shocks (BRD-RULE-AI-05), and the format check enforces it on every agent answer (a draft without them goes back to
synthesis). A CIO edit that drops one is not refused: the challenger raises it as a critical finding (R2).

## Live-mode safeguards
Two different models (refused if equal); a reply with `finish_reason == "length"` is refused; a reply from a
model other than the configured one is refused; token caps: analyst 3,000, debate 3,000, synthesis 6,000,
challenger 4,000.

## Implementation
`src/views/graph.py`, `src/views/ops.py` (`gather`, `analyse`, `discuss`, `compose`, `save_view`, `review`),
`src/views/agents.py` (prompts, `call_model`, `resolve_mode`), `src/views/mock.py` (keyword scenarios),
`src/views/schema.py`, `src/views/store.py`; models `llm:cio`, `llm:challenger` in `resources.yaml`.

## Acceptance and tests
`tests/test_views.py::test_the_mock_agent_writes_a_valid_view_and_records_every_node`,
`::test_a_bad_draft_is_sent_back_twice_then_the_run_fails`, `::test_the_schema_refuses`,
`::test_an_injection_in_the_news_stays_data`, `::test_live_mode_uses_two_models_and_no_client_data_reaches_them`,
`::test_live_mode_refuses_same_models_a_cut_reply_and_another_model`, `::test_only_the_cio_runs_the_agent_and_decides`.
Live run recorded 2026-10-15 (OpenRouter): CIO agent 26 s over 7 nodes (news plan §9).

## Live demo (UI redesign R6, 2026-10-16)
The public demo runs live: CIO agent `anthropic/claude-sonnet-5.5`, challenger `google/gemini-3.8-flash` (two
vendors, ADR-0010), through the configured OpenAI-compatible endpoint. `scripts/demo_walkthrough.py` filled it over
HTTP from news the server fetched: three events (stock market, property, monetary); agent + challenger took 71 s,
37 s and 86 s and 54 k, 35 k and 64 k tokens (154 k of the 300 k daily budget); the first had one critical finding,
which the script answered (“chấp nhận”, its reason naming the script); two views approved and applied to every
family (AR-0001-v1-1, AR-0002-v1-1), the third left pending for the CIO screen. Every decision the script took
says so in its reason and is in the audit chain.

## Limitations
- The mock agent writes its summary from the headlines: a headline with an action word (“bắt đáy”) fails the
  content rule and the view ends AGENT_ERROR — the guard holds, the mock cannot recover (seen on the dev server).
- The inbox (“hộp chờ”) run mode of FR-307 is not built (FEAT-19).
- NFR-10 since 2026-10-16: a daily token budget (`AGENT_DAILY_TOKENS`, default 300 000) refuses calls past it;
  tokens per event in `GET /api/agents` (`budget.by_event`). No money cost (no price per token configured).
- The stressed-branch rule is not enforced after the model answers.
