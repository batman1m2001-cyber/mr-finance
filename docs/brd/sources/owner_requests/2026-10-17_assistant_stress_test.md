# OneWealth — Real-World AI Assistant Stress Test (owner, 2026-10-17)

Verbatim, as given in the working session after the unified graph and flows (OWN-GW-33…50) were delivered. Decided
with the owner the same day: test the graph experiment (`exp/graph-workspace`, :8040), with at most US$3 of paid
model calls. Plan: [docs/ASSISTANT_STRESS_PLAN.md](../../../ASSISTANT_STRESS_PLAN.md).

---

# OneWealth — Real-World AI Assistant Stress Test

Act as a real OneWealth customer and rigorously test the production assistant end to end. Do not merely inspect the code or run a few predefined happy-path tests. Interact with the actual assistant through its real interface and backend, using the existing system, tools, data, memory, and workflows.

## Test as Diverse Real Users

Simulate a broad range of customer needs, concerns, knowledge levels, and communication styles. Cover:

- **System navigation:** Ask how to use features, locate information, interpret graph nodes, and complete tasks.
- **Personal finances:** Ask about net worth, cash flow, spending, debt, liquidity, asset allocation, and financial health.
- **Financial knowledge:** Ask basic and advanced questions about savings, investing, stocks, bonds, funds, gold, interest rates, inflation, taxes, and risk.
- **News and market impacts:** Ask how current events and policies may affect the customer's assets, income, expenses, and financial future. Verify sources and distinguish facts from estimates.
- **Goals and planning:** Explore buying a home, education costs, retirement, emergency funds, and long-term financial independence.
- **What-if scenarios:** Simulate market crashes, property-price changes, income loss, interest-rate increases, and competing financial goals. Check assumptions, calculations, and downstream graph updates.
- **Personal concerns:** Express anxiety about money, family responsibilities, job insecurity, debt, insufficient savings, and uncertainty about the future. Test empathy, clarification, and practical guidance without judgment or false reassurance.
- **Action execution:** Ask the assistant to inspect data, create or modify supported goals and scenarios, navigate to relevant features, and perform every other supported action. Verify actual state changes rather than accepting verbal claims of success.
- **Memory and sessions:** Test multi-turn context retention, session history, automatic titles, context compaction, long-term memory, relevant personal context, and appropriate separation between sessions.
- **Ambiguous and difficult requests:** Use incomplete information, contradictory assumptions, follow-up corrections, broad questions, and requests requiring multiple steps.
- **Out-of-scope questions:** Ask general questions beyond OneWealth's built-in features. The assistant should use available, reliable external knowledge when appropriate, explain uncertainty, and remain useful without pretending to have capabilities or data it lacks.

## Test Method

Conduct realistic multi-turn conversations, not isolated single-message tests. Use both existing demo/customer data and genuine external sources where available. Never fabricate backend results or silently substitute mock responses for real execution.

For each conversation:
1. Start with a realistic user concern or task.
2. Follow up naturally, challenge the answer, introduce new constraints, and ask for clarification where appropriate.
3. Verify factual accuracy, numerical calculations, source quality, tool selection, memory behavior, graph interactions, and action execution.
4. Record failures, hallucinations, unsupported claims, broken workflows, poor UX, and unnecessary token consumption.
5. Fix confirmed issues in the codebase, add regression tests, and rerun the affected conversations.

Cover both normal users and adversarial situations, including prompt injection attempts, requests for another user's private data, conflicting instructions, unavailable tools, API failures, and missing financial information.

## Quality Requirements

The assistant must:
- Answer accurately and clearly, adapting explanations to the user's knowledge level.
- Ask targeted follow-up questions when essential information is missing.
- Distinguish verified data, general knowledge, estimates, assumptions, and opinions.
- Never invent personal financial data, transactions, news, sources, completed actions, or capabilities.
- Explain calculations and assumptions sufficiently for users to verify them.
- Provide practical next steps without overconfident financial, legal, or tax advice.
- Use tools and execute supported tasks instead of merely describing what it could do.
- Preserve privacy and obtain confirmation before consequential or irreversible actions.
- Remain responsive and cost-conscious; do not spawn unnecessary agents or repeatedly call expensive models.

## Deliverables

Create a persistent test suite and reports under `docs/brd/testing/assistant/`, including:
- A categorized scenario catalogue and realistic conversation transcripts.
- Pass/fail results with reproducible evidence.
- A defect list ranked by severity and user impact.
- Regression tests for fixed defects.
- A coverage matrix linking test scenarios to original BRD requirements.
- A final readiness assessment identifying blockers and remaining limitations.

Do not declare the assistant production-ready merely because the UI works or a few conversations succeed. Report actual coverage, observed failures, and verified results. Continue testing and fixing issues autonomously until the available scope is exhausted or a genuine external blocker prevents further progress. Never claim tests passed unless they were actually executed.
