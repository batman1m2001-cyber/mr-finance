# The original BRD — reference record

| | |
|---|---|
| Title | *Đặc tả bộ agent tác động tin tức – Yêu cầu kinh doanh và nền tảng công nghệ* |
| Date and author (as written) | “Oct 15, 2026 · @Bob” |
| Status (as written, §1) | “Tài liệu này là nghiên cứu cá nhân, không phải quan điểm chính thức của Techcombank.” — personal research, not Techcombank's official view |
| File | `.docx`, 806,263 bytes, SHA-256 `5ea9d8da3e84bd196f8649a87a3b041ca9a1e01db109dca7f1570dd5a4cde1e3` |
| Location | `/home/thanglq/mr-finance/` (not committed; [ADR-0001](../decisions/ADR-0001-keep-the-brd-file-out-of-the-public-repository.md)) |
| Read | In full on 2026-10-15: all 20 sections, 38 tables, 5 figures, the one equation |
| Language | Vietnamese |

## What the BRD describes — and what it does not

The BRD specifies a **news-impact agent system** (“bộ agent tác động tin tức”) for Private clients: news →
CIO view with 2–4 scenarios → independent challenge → CIO approval → a deterministic engine computes VND impact
for every family → post-check → RM. It is step 4 of a five-step “Trợ lý Wealth AI” journey (§1).

It also describes **its own author's demo**, built on TypeScript, Hono, Cloudflare Workers/D1, React and
LangGraph, with 20 mock families and 143–160 tests (§1, §12.1, §16.1, §20). **That demo is not this
repository.** OneWealth here is a Python/operonx implementation of the same requirements
([ADR-0002](../decisions/ADR-0002-implement-the-brd-on-operonx-not-the-brd-stack.md)). Consequences:

- The BRD's “Demo: Đã có / Chưa có” column (§4) reports the author's demo. It is recorded as a fact about that
  demo, never as our status. Our status is in [`requirements_traceability.md`](requirements_traceability.md).
- Stack-specific statements (Cloudflare D1, 28 tables, ~80 endpoints, Zod, decimal.js, LangGraph, Workers
  Builds, Cloudflare Access) describe the author's demo. They are extracted as **architecture notes**, not as
  requirements, unless the BRD makes them a rule (e.g. “schema validation before saving” is a rule; “Zod” is a
  tool). See [`open_questions.md`](open_questions.md) Q-01.

The BRD does **not** cover the capabilities of the original brief (consolidation, dashboard, risk test, life
scenarios, policy-cost alerts, the RM approval queue); §3 even puts “connecting outside data (Open API,
statements)” out of scope for its phase. Those capabilities predate the BRD and are kept
([`brief_requirements.md`](brief_requirements.md), [ADR-0003](../decisions/ADR-0003-keep-the-capabilities-that-predate-the-brd.md)).

## Section map

The BRD has no page numbers in its source; locations are given as **§section** and, inside a table, the
**row code** or first cell. Section 20 is placed before section 19 in the document (recorded as-is).

| § | Title (Vietnamese) | Content | Extracted to |
|---|---|---|---|
| 1 | Tóm tắt điều hành | Purpose, principle “AI soạn kịch bản, máy tính con số, con người duyệt”, demo status, decisions needed | [PRODUCT_OVERVIEW](../PRODUCT_OVERVIEW.md), Q-01, Q-02 |
| 2 | Bối cảnh và vấn đề kinh doanh | Pains per party (table), business goals, success metrics (table) | [business_requirements.md](business_requirements.md) §Goals, BRD-KPI-01…07 |
| 3 | Phạm vi và người dùng | In/out of scope, 6 roles (table) | BRD-RULE-SCOPE-*, BRD-RULE-ROLE-* |
| 4 | Yêu cầu kinh doanh | BR-01…BR-15 (table) | BRD-BR-01…15 |
| 5 | Luồng nghiệp vụ | Figure 1, 8 steps with time targets (table) | BRD-RULE-WF-*; Figure 1 redrawn in [data_flows.md](../architecture/data_flows.md) |
| 6 | Yêu cầu chức năng | 8 modules, FR-101…FR-801 (8 tables) | BRD-FR-* |
| 7 | Kiến trúc tổng thể | Figure 2, three layers; §7.1 external AI zone (Figure 3, data-flow table) | BRD-RULE-ZONE-*; [system_overview.md](../architecture/system_overview.md) |
| 8 | Bộ agent AI | 4 LLM tasks (table); §8.1 CIO agent graph; §8.2 output schema (table); §8.3 AI controls; §8.4 three run modes (table) | BRD-RULE-AI-*; [agent_workflows.md](../architecture/agent_workflows.md) |
| 9 | Động cơ định lượng và mô hình yếu tố | §9.1 four steps + equation; §9.2 15 factors (table); §9.3 sensitivities (table); §9.4 gold example | BRD-RULE-ENG-* |
| 10 | Nhánh tác động lên mục tiêu | Purposes, matching rules, 3 levels (table), compliance rule, example | BRD-RULE-GOAL-* |
| 11 | Dữ liệu | §11.1 sources (table); §11.2 model (table); §11.3 quality; §11.4 DB design (Figure 4, 25-row table, lifecycles, AI-zone tables) | BRD-RULE-DATA-*, BRD-RULE-LC-*; [domain_model.md](../architecture/domain_model.md) |
| 12 | Nền tảng công nghệ | §12.1 demo stack; §12.2 target bank state; §12.3 main endpoints | Architecture notes; [integrations.md](../architecture/integrations.md), [api_reference.md](../architecture/api_reference.md) |
| 13 | Bảo mật, phân quyền và nhật ký | §13.1 auth, roles, SoD, config ownership; §13.2 barrier; §13.3 audit chain | BRD-RULE-SEC-* |
| 14 | Tuân thủ và pháp lý | Legal table (7 rows), 3 content flows, content labelling, “exclusive” research | BRD-RULE-CONTENT-*; legal rows kept as context |
| 15 | Yêu cầu phi chức năng | NFR-01…NFR-12 (table) | BRD-NFR-* |
| 16 | Kiểm thử, kiểm chứng mô hình và đo lường | §16.1 test groups; §16.2 back-tests; §16.3 operating metrics | BRD-RULE-MEAS-*; [acceptance_criteria.md](../testing/acceptance_criteria.md) |
| 17 | Rủi ro và biện pháp | 12 risks with mitigations (table) | Context; each mitigation maps to a rule already extracted |
| 18 | Lộ trình triển khai | Figure 5, 4 stages (table), staffing | Context ([PRODUCT_OVERVIEW](../PRODUCT_OVERVIEW.md) §Roadmap) |
| 20 | Phản biện độc lập | 27 findings F01–F27 on the author's demo, with what was done and what remains | Context; findings that state a rule are cited by the rule (e.g. F04 → approval condition e) |
| 19 | Thuật ngữ và tham khảo | Glossary (table), references | [GLOSSARY.md](../GLOSSARY.md) |

## Figures

The figures are part of the BRD and stay with it (not committed). Each is identified by its hash and redrawn
by us as a Mermaid diagram where it carries requirements; the redrawing is ours and says so.

| ID | BRD § | Caption (as written) | What it shows | SHA-256 (embedded PNG) | Redrawn in |
|---|---|---|---|---|---|
| BRD-FIG-1 | 5 | “luồng nghiệp vụ một sự kiện · 3 nguồn tin, 3 agent AI, 3 chốt người” | International, domestic news and TCB research (only when Compliance releases) → collection every 10 min (white list, restricted list, grouping) → AI zone (CIO agent with 4 groups, challenger) → CIO approval (return to edit) → engine with family data → post-check → RM pre-review if bad case ≥ 5 % / 3 months, else update to family | `89a119a2…0f76` | [data_flows.md §1](../architecture/data_flows.md#1-one-event-from-news-to-the-family-brd-figure-1) |
| BRD-FIG-2 | 7 | “kiến trúc bản demo · 5 tầng, 3 lớp xử lý” | User channels (CIO, RM, Compliance, Admin, client app later) → API → AI layer / compute layer / control layer → shared DB → external sources and cron | `8ef39860…77a2` | [system_overview.md §2](../architecture/system_overview.md#2-the-brds-three-layers-brd-figure-2) |
| BRD-FIG-3 | 7.1 | “hai vùng tách biệt · luồng dữ liệu một chiều” | External AI zone (public news, released research copies, agents, own DB, outbox) → signed results only → TCB inbox → format check → CIO approval → engine + family data → RM, client | `2ff68e6b…224b` | [data_flows.md §3](../architecture/data_flows.md#3-the-two-zones-brd-figure-3) |
| BRD-FIG-4 | 11.4 | “quan hệ giữa các bảng chính · Cloudflare D1, 28 bảng” | news_items → events → views → decisions → application_runs → family_impacts / goal_impacts; agent_runs, challenges, finding_responses, config_versions, price_snapshots, run_snapshots, policy_documents, external_outputs; audit_log under all | `a30e1e4c…109d` | [domain_model.md §2](../architecture/domain_model.md#2-the-brds-entity-chain-brd-figure-4) |
| BRD-FIG-5 | 18 | “lộ trình 5 giai đoạn, không theo tỷ lệ thời gian · 3 cổng” | Core demo (10/2026, done) → preparation (11–12/2026) → pilot (4 months, 300 clients, 20 RMs) → expansion (to month 12, 70 %) → full (months 18–24, 88 %), with three control gates | `1ca090c1…774c` | [PRODUCT_OVERVIEW §Roadmap](../PRODUCT_OVERVIEW.md#roadmap-from-the-brd-18) |

Full hashes: FIG-1 `89a119a2561e844acc1b8bab482148f68c369eeba5c5c4d4a18c83b9095f0f76`,
FIG-2 `8ef3986024df22aaac91996a911b8e411dafcac613dd610effd876009ca277a2`,
FIG-3 `2ff68e6b074e963faa10cd2cd01d4bf732eac63cc47855c4f233fbb81b30224b`,
FIG-4 `a30e1e4cc194780695fed21ea25d55abc1790cdbc527c15910eb6e721a42109d`,
FIG-5 `1ca090c1703934704b08fa65540b39b8cfc6b035901d0073810d6e7d5328774c`.

## Limits of the extraction

- The equation in §9.1 is stored as LaTeX text in the document and was read as text:
  `Δn = Σnc Σcc⁻¹ Δc`, `Σn|c = Σnn − Σnc Σcc⁻¹ Σcn`.
- The figures were read as images; their text was transcribed by reading, not by OCR software.
- Nothing in the document was inaccessible.
