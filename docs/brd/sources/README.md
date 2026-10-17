# Sources

Every document the requirements are derived from. Sources are **immutable**: they are never edited to match
the product. A new version of a source is registered as a new row; the old row stays.

| ID | Source | Kind | Where it lives | Identity | Role |
|---|---|---|---|---|---|
| SRC-01 | *Đặc tả bộ agent tác động tin tức – Yêu cầu kinh doanh và nền tảng công nghệ* (dated Oct 15, 2026, author “@Bob”) | BRD, `.docx`, 806,263 bytes, 5 embedded figures | **Not in git.** Local path: `/home/thanglq/mr-finance/Đặc tả bộ agent tác động tin tức - Yêu cầu kinh doanh và nền tảng công nghệ.docx` (excluded by `.git/info/exclude`) | SHA-256 `5ea9d8da3e84bd196f8649a87a3b041ca9a1e01db109dca7f1570dd5a4cde1e3` | **Authoritative** for the news-impact capabilities. Details: [`../requirements/original_brd_reference.md`](../requirements/original_brd_reference.md); why it is not committed: [ADR-0001](../decisions/ADR-0001-keep-the-brd-file-out-of-the-public-repository.md) |
| SRC-02 | *Plan v2: Tập trung vào selling point Consolidate + Dashboard tổng thể* | Original product brief, Markdown | [`/mr_finance_idea_final.md`](../../../mr_finance_idea_final.md) (in git since the first commit, 2026-10-09) | git history of that file | Authoritative for the capabilities that predate the BRD (consolidation, dashboard, risk test, scenarios, policy alerts, RM queue). Extracted in [`../requirements/brief_requirements.md`](../requirements/brief_requirements.md) |
| SRC-03 | OneWealth Redesign & Product Evolution Kit | Proposal (prompts, change proposal, acceptance rules) + 2 images | Verbatim copies of its 6 Markdown files: [`redesign_kit_2026-10-15/`](redesign_kit_2026-10-15/); images: [`../assets/proposed_ui/`](../assets/proposed_ui/). The zip itself (`OneWealth_Redesign_Kit.zip`) is not committed | zip SHA-256 `8d91ce944e33eadf7fe18572eb60f555388f63ad89eedeeaa38181485cfc6672` | **Proposed** extensions (Pulse, Money Flow, graph, feed, Copilot) and the documentation/acceptance rules this repository follows. Extracted in [`../requirements/kit_requirements.md`](../requirements/kit_requirements.md). Its concept board is illustrative, not data |
| SRC-04 | Delivery plans: `docs/PLAN.md` (P0–P7), `docs/NEWS_IMPACT_PLAN.md` (N0–N5, U1–U2), `docs/REDESIGN_KIT_PLAN.md` (K1–K6) | Plans | [`../../PLAN.md`](../../PLAN.md), [`../../NEWS_IMPACT_PLAN.md`](../../NEWS_IMPACT_PLAN.md), [`../../REDESIGN_KIT_PLAN.md`](../../REDESIGN_KIT_PLAN.md) | git | Not requirements. They record what was decided and built, and when. Their decisions are summarised as ADRs in [`../decisions/`](../decisions/) |
| SRC-05 | Requests of the product owner, given in the working session | Markdown, verbatim | [`owner_requests/`](owner_requests/): [`2026-10-16_living_interface.md`](owner_requests/2026-10-16_living_interface.md), [`2026-10-16_ui_redesign.md`](owner_requests/2026-10-16_ui_redesign.md), [`2026-10-16_assistant_memory_agents.md`](owner_requests/2026-10-16_assistant_memory_agents.md), [`2026-10-17_persistent_financial_graph.md`](owner_requests/2026-10-17_persistent_financial_graph.md) (+ concept image `GW-01`), [`2026-10-17_graph_dataflow_refinement.md`](owner_requests/2026-10-17_graph_dataflow_refinement.md), [`2026-10-17_assistant_sessions.md`](owner_requests/2026-10-17_assistant_sessions.md), [`2026-10-17_central_wealth_core.md`](owner_requests/2026-10-17_central_wealth_core.md), [`2026-10-17_graph_layout_routing.md`](owner_requests/2026-10-17_graph_layout_routing.md), [`2026-10-17_unified_graph_flows.md`](owner_requests/2026-10-17_unified_graph_flows.md) | SHA-256 `a585fa4b95e2786f062193e430660c94356ff26ff433c22b9d86499cac6bb766`, `b0868dcdc6dce0ddef309185b93adbd2e62c7de4ee2d8f848c545ed491af91e2`, `d4d7aa3d56c1a9a14e261d952d395c53cfcdaf36b5358d2f52f0f0185fadcb29`, `fcd4ca0bd5ba092a00797d0ba103d1155d438620be1b868b909d5385f683ab9c`, `7074a7e2b4f1c51a81d8a252f7d5b5d7d25d1f7c738781969edce5dd16e803a2`, `09b32a68d8f34f2880f564f89141a61881cccf390fa0288c9233c1f9f80e2e66`, `f667ace77621f28549d54200c770dfc2ea6ebdbf4090a5cd9ea533c589546300`, `9f21115571fbc2e28f10adb897b91b0085500ecbd0b045cd2703438fcbaf3165`, `6dead00b8ea40d18171cb0e69f4a4f57417b436ba8e832d01fb4220f8b6049f7` | **Approved** extensions (the owner asked for them). Extracted in [`../requirements/owner_requirements.md`](../requirements/owner_requirements.md) |

## Hashes of the kit files kept here

| File | SHA-256 |
|---|---|
| `README.md` | `5852cd48bf98ddf03c2a0a968f795912795eea09bb037a3b875cb9416b2ae9b6` |
| `PROMPT_MASTER.md` | `2048f37c88041d39deeccd236fd9012a487fa13f0992e9fa584fcae03e0d9440` |
| `CHANGE_PROPOSAL.md` | `6789e498e628867a5abdfc03ba761ba984a58d8c1d34d60fa714c76431348b15` |
| `BRD_COVERAGE_AND_ACCEPTANCE.md` | `89654529fa9e92a49edb283742fcc4a26e1ce746ff711fbe0d067ab68eb525d1` |
| `PROMPT_FINANCIAL_INTELLIGENCE_GRAPH.md` | `6aabac67d031811f6a42aa72247cbfbfe588b85c651e4d28b845b49cb1d332c3` |
| `PROMPT_ONEWEALTH_COPILOT.md` | `1ea19e1d7dc36cdd8717fedf8c01099489ec1c8964171f462a094477338ef60e` |
| `assets/current_dashboard_reference.png` | `f8a907df83002225fba40a7e73c7c35716453f9179ac48a2c1480cbdda654029` |
| `assets/onewealth_redesign_concept_board.png` | `e2aff7efd4ae77eea2252d89778a7b5c79df4c1bffa6f5cbee3d8838c2053a72` |

`scripts/check_brd_docs.py` re-hashes the kit copies here and fails if one was edited.

## Checking the BRD file

```bash
sha256sum "/home/thanglq/mr-finance/Đặc tả bộ agent tác động tin tức - Yêu cầu kinh doanh và nền tảng công nghệ.docx"
# 5ea9d8da3e84bd196f8649a87a3b041ca9a1e01db109dca7f1570dd5a4cde1e3
```

`scripts/check_brd_docs.py --brd <path>` checks the hash and that every BRD code (`BR-nn`, `FR-nnn`,
`NFR-nn`) in the file has an entry here. Without the file, that part is skipped and the check says so.

A different hash means a new BRD version: register it as a new row (SRC-05…), extract what changed, and record
the differences in [`../CHANGELOG.md`](../CHANGELOG.md). Never overwrite the extraction of the earlier version.
