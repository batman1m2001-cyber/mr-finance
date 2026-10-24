# Measuring the news agents (2026-10-24)

Given in the working session as a written task, "Refactor and Implement News & Portfolio Impact Agent Evaluation",
after the owner asked which of the many agents matter ("focus only on very critical one like: agent get news, agent
generate scenario in CIO... because now I need to evaluate the efficient of thoses agents"). Quoted as written.

| Their words | What it asks |
|---|---|
| "News collection monitoring ... fetched, processed and retained ... start, end, duration and status ... real estate, stocks and policy/macro ... portfolio-relevant" | a funnel and health per ingest run, the four groups, the relevant share, daily and historical trends; collection time kept apart from publication time |
| "Accuracy ... precision ... recall against independent material events ... missed events ... direction and impact estimation error at 3d and 1w ... a configurable materiality threshold" | the scenario agents scored against what the market did, with coverage (due, scored, pending, failed, excluded) and a defensible ground truth |
| "Financial (VND) ... correct calls, incorrect calls, missed opportunities, correct negative warnings, and the net ... by asset family ... labelled simulated" | the scored moves valued on the existing simulated book through the existing engine, with n on every figure; unavailable shown as unavailable |
| "preserve the original prediction ... no future leakage ... dedupe overlapping news ... incorrect kept distinct from pending" | auditable records with failure reasons |
| "View A ... View B ... a drill-down per prediction ... no percentage without its denominator" | the trial page in two views |
| "per model call ... tokens ... cost, latency, retries, status and error ... missing must never show as 0" | the root cause of the 0 cost fixed |
| "Do not: Add new AI agents. Rebuild the impact engine or portfolio simulation. Introduce a separate backtesting platform ... fabricate ground truth, financial outcomes, or evaluation results. mark pending or unscored predictions as incorrect. treat market movements as proof that the agent caused a financial gain or loss." | the limits of the work |

Plan: [`docs/AGENT_EVALUATION_PLAN.md`](../../../AGENT_EVALUATION_PLAN.md) (E0–E5).
