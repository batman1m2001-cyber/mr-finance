# Change Proposal — OneWealth

## Why change

The current dashboard has a cleaner baseline, but it still feels static and card-oriented. Information is spread across panels, and users must mentally connect portfolio composition, cash flow, news, risk and goals. The redesign should make meaningful relationships visible while keeping the interface calm and readable.

## Proposed experience changes

### 1. Financial Pulse
A compact summary of net worth, meaningful changes, liquidity and key signals. Avoid large empty panels and repeated labels. Keep detailed data available.

### 2. Money Flow
A Sankey-style view for real aggregated cash-flow data when source, destination, period and amount are available. Flow width encodes value. Selecting a path opens the underlying figures and source. Do not infer cash flows from static asset allocations.

### 3. Wealth Map
Use an appropriate allocation chart/treemap to explain portfolio composition. Provide values, percentages, timestamps and drill-down.

### 4. Financial Intelligence Graph
Connect supported news events, entities, assets, exposures, risks and goals. Use graph relationships only when grounded in data/business logic. Provide filters, grouping, progressive disclosure and detail panels.

### 5. Intelligence Feed
Prioritize the changes that matter: verified risk threshold breaches, notable portfolio changes, supported news impacts and goals requiring attention. Explain why each item is shown and link to evidence.

### 6. OneWealth Copilot
A persistent, contextual side panel for asking questions, investigating relationships, opening relevant views and executing supported tasks through real APIs/tools with permissions and confirmations.

## Proposed engineering changes

- Audit the BRD and current code before selecting architecture.
- Create a stable requirement-to-code/test matrix.
- Separate UI presentation from business calculations and agent orchestration.
- Reuse current APIs/services where suitable.
- Add only the domain relationships, visualization dependencies and tool interfaces justified by requirements.
- Add regression tests and verify behavior end to end.
- Document blockers rather than simulate unsupported features.

## Implementation sequence

1. Repository and BRD audit; baseline checks.
2. Requirement inventory and current-state architecture report.
3. Design system and information hierarchy.
4. First real-data visualization (choose Sankey, allocation, or graph based on data readiness).
5. Cross-feature navigation using shared context.
6. Copilot MVP for contextual read-only questions and navigation.
7. Add task execution only for supported tools with authorization/confirmation.
8. Regression testing, coverage report and documentation.

## Definition of done

- All BRD requirements inventoried and traceable.
- No in-scope requirement silently omitted.
- Existing functionality regression-tested.
- No fabricated data or mock functionality presented as production-ready.
- Visualizations use real supported data and are inspectable.
- Motion is purposeful and respects reduced-motion preferences.
- Copilot reports actual tool execution status honestly.
- Tests/checks and blockers are explicitly reported.
