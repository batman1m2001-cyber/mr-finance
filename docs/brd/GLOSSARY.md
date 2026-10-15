# Glossary

BRD terms (§19.1) with the product's names.

| Term | Meaning | In the product |
|---|---|---|
| Agent | A program that uses an AI model for one task, with an owner and limited rights | CIO agent, challenger |
| Sự kiện (event) | News items about one happening; the unit the agent analyses | `EV-2026-nnnn` |
| Nhận định (view) | The CIO agent's output for an event: impact rows and scenarios | `VW-nnnn-vN` |
| Kịch bản / nhánh (scenario branch) | A possible course with a probability and core shocks | 2–4 per view |
| Cú sốc lõi (core shock) | A risk factor moving up/down by size S/M/L | 1–5 per branch |
| Yếu tố rủi ro (risk factor) | A market variable driving many assets | 15, `data/factor_model.json` |
| Độ nhạy (beta, duration) | How much an asset moves per unit of a factor | `src/engine/loadings.py` |
| Dải xấu / cơ sở / tốt | P10 / P50 / P90 of the mixed outcome (P5 = very bad, reference) | fan chart |
| Chế độ căng thẳng (stressed regime) | Parameters for turbulent markets, higher correlations | `regime: stressed` |
| Lần áp dụng (application run) | One computation of an approved view for every family, with a snapshot | `AR-…` |
| Hậu kiểm (post-check) | Rule checks on results before RMs see them | P1–P5 |
| Ghi chú quy định (regulation note) | A note on a rule that moves no price but affects goals | goal branch |
| Tipping-off | Revealing to a client that they are monitored for AML | forbidden wording |
| Gia đình (family) | A client and the household members who consented | `C01` + `C01S` |
| Cách tính | “How it was computed”: the trace of a number | SCR-RM-03 |
| Mô phỏng (mock) | A run without AI (keyword scenarios, rule challenger) | labelled on every view |
