# Integrations

| External system | Used for | How | Configuration | State |
|---|---|---|---|---|
| Public RSS/Atom feeds (VnExpress, VnEconomy, CafeF, Vietstock, Fed…; 11 configured) | news (FEAT-01) | HTTPS GET every 10 min, 15 s timeout | `data/news_config.json` (from `scripts/make_news_config.py`) | live |
| VNDirect chart API → Vietcap OHLC chart | VN-Index and the 10 demo stocks, daily (FEAT-35) | HTTPS, `market_equity` 15:45 | `data/market_sources.json` (`price_sources`, `ticker_map` config) | live, unofficial |
| cafef foreign trading history | foreign net buying on HOSE (FEAT-35) | HTTPS, `market_flows` 16:00, 30 days a page | same | live, unofficial |
| HNX government yield curve → worldgovernmentbonds.com | VN yields 3M/1Y/5Y/10Y (FEAT-35) | HTTPS POST per day (HNX: incomplete TLS chain, unverified context; WGB: needs an Origin header), `market_yields` 17:30 | same | live, unofficial |
| Vietcombank rate table → MSN | USD/VND (FEAT-35) | HTTPS per day, `market_fx` hourly | same | live, unofficial |
| MSN Finance chart API | gold, Brent, ACWI, S&P 500, US 10-year, six currencies (FEAT-35) | HTTPS, one request per run; the anonymous key from MSN's public page configuration, kept a day | same | live, unofficial |
| Binance klines | BTC, ETH in USDT (FEAT-35) | HTTPS, `market_crypto` hourly | same | live |
| PNJ gold price history | SJC bars, VND per lượng (FEAT-35) | HTTPS per day (422 until the day ends), `market_gold` hourly | same | live, unofficial; giavang.org no longer answers (2026-10-16) |
| Blocked from this server (2026-10-16) | — | SJC and TCBS (Cloudflare), Yahoo (429), Stooq (captcha), FRED without a key (times out), SBV rate portal (port closed) | — | not used |
| LLM provider (OpenAI-compatible; OpenRouter used) | CIO agent, challenger, statements, declarations | operonx `resolve_hub().get("llm:<key>")`; `resources.yaml` | `.env`: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_MODEL_CIO`, `LLM_MODEL_CHALLENGER`, `LLM_MODEL_COPILOT`, `MF_AI` | optional; mock/rules without it. Live demo since 2026-10-16: CIO `anthropic/claude-sonnet-5.5`, challenger `google/gemini-3.8-flash`, Copilot router `anthropic/claude-haiku-5.5` |
| Audit key | HMAC chain | env | `AUDIT_HMAC_KEY` — read by `src/control/audit.py` but **not listed in `.env.example`** (AGENTS.md asks for every name there) | optional |
| ngrok | public demo URL https://oneweath.ngrok.app → port 8030 | tunnel | outside the repo | live demo |
| operonx-studio | drawing and tracing the graphs | `uv run operonx studio` | `operonx.toml` `[tracing]` | developer tool |

**Not integrated (mock data instead, [ADR-0005](../decisions/ADR-0005-mock-clients-and-prices-public-news.md)):**
core banking, TCBS, Techcom Capital, OneHousing, Open API banks, price feeds, research repository, NHNN/UBCKNN/MoF
document portals, RM Workbench, CRM, SSO — every one is a pilot-phase item in BRD §11.1 and §12.2.

Secrets live only in `.env` (gitignored). `.env.example` lists `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`,
`LLM_MODEL_CIO`, `LLM_MODEL_CHALLENGER`, `MF_AI`, `MF_STATE`, `PORT`; `AUDIT_HMAC_KEY` is missing from it.
