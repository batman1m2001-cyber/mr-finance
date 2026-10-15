# Integrations

| External system | Used for | How | Configuration | State |
|---|---|---|---|---|
| Public RSS/Atom feeds (VnExpress, VnEconomy, CafeF, Vietstock, Fed…; 11 configured) | news (FEAT-01) | HTTPS GET every 10 min, 15 s timeout | `data/news_config.json` (from `scripts/make_news_config.py`) | live |
| LLM provider (OpenAI-compatible; OpenRouter used) | CIO agent, challenger, statements, declarations | operonx `resolve_hub().get("llm:<key>")`; `resources.yaml` | `.env`: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_MODEL_CIO`, `LLM_MODEL_CHALLENGER`, `LLM_MODEL_COPILOT`, `MF_AI` | optional; mock/rules without it. Live demo since 2026-10-16: CIO `anthropic/claude-sonnet-5.5`, challenger `google/gemini-3.8-flash`, Copilot router `anthropic/claude-haiku-5.5` |
| Audit key | HMAC chain | env | `AUDIT_HMAC_KEY` — read by `src/control/audit.py` but **not listed in `.env.example`** (AGENTS.md asks for every name there) | optional |
| ngrok | public demo URL https://oneweath.ngrok.app → port 8030 | tunnel | outside the repo | live demo |
| operonx-studio | drawing and tracing the graphs | `uv run operonx studio` | `operonx.toml` `[tracing]` | developer tool |

**Not integrated (mock data instead, [ADR-0005](../decisions/ADR-0005-mock-clients-and-prices-public-news.md)):**
core banking, TCBS, Techcom Capital, OneHousing, Open API banks, price feeds, research repository, NHNN/UBCKNN/MoF
document portals, RM Workbench, CRM, SSO — every one is a pilot-phase item in BRD §11.1 and §12.2.

Secrets live only in `.env` (gitignored). `.env.example` lists `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`,
`LLM_MODEL_CIO`, `LLM_MODEL_CHALLENGER`, `MF_AI`, `MF_STATE`, `PORT`; `AUDIT_HMAC_KEY` is missing from it.
