# To discuss with the owner

Only what needs the owner's decision and could matter if left wrong. Everything else is decided in the plans,
`docs/brd/decisions/` and `docs/brd/requirements/open_questions.md`. In the order raised; an item stays here, marked
**decided**, once answered.

| # | Raised | Question | Why it matters | What I did meanwhile |
|---|---|---|---|---|
| D-01 | 2026-10-15 | The BRD's requirement texts are quoted verbatim in this **public** repository (`docs/brd/requirements/`, ADR-0001). Keep, paraphrase, or make the repo private? | Quoting is itself a disclosure of the document, even though the `.docx` is not committed and it carries no confidentiality mark | Kept the quotes (same practice as `docs/NEWS_IMPACT_PLAN.md`) |
| D-02 | 2026-10-15 | FR-404 goal impact: the BRD gives no thresholds or funding source. Accept our rule (goals draw in date order on financial assets; level = monthly saving needed ÷ surplus, ≤ 0.6 Đạt, ≤ 1 Theo dõi) or give the CIO's? | With our rule every demo goal stays 100 % Đạt, so the feature looks inert in a demo | Built on our rule, labelled “đề xuất, chờ CIO xác nhận” on the page (Q-11) |
| D-03 | 2026-10-16 | The pre-BRD statement reader and declaration chat send client text (statements, chat messages) to the model whenever AI is on (`LLM_API_KEY` set; MF_AI auto). BRD-BR-11 / NFR-08 forbid client data reaching an AI provider. Keep them AI-capable (with an on-premise model only), or force their rule paths? | Turning AI on for the CIO agent would also turn it on for these steps and break the barrier | Nothing changed: no key is set here, so both run their rule paths today; NFR-08 stays `partially_implemented` |
