# OneWealth — Financial Intelligence Graph & Money Flow

Use this as a focused supplement to `PROMPT_MASTER.md`.

## Product direction

OneWealth should feel like an interactive financial-intelligence system, not a collection of unrelated dashboard widgets. The user should be able to understand the big picture quickly, then explore meaningful relationships.

## Graph model

Inspect the code and BRD first. Determine which of these entities and relationships are actually supported:
- Financial state: net worth, assets, liabilities, income, expenses, liquidity.
- Assets, asset classes, institutions and data sources.
- Cash flows between supported categories.
- Financial goals, plans and hypothetical scenarios.
- News events, companies, industries, market movements and affected assets.
- Risk exposures, stress tests, alerts and possible decisions.
- AI analyses, evidence, source references, timestamps and confidence/uncertainty.

Use a graph where relationships are many-to-many; provide hierarchical navigation as a view, not as the only data structure. Do not add a graph database merely because the UI uses a graph. A frontend graph over existing domain data may be sufficient.

## Visual experiences

Implement a coherent first slice using real data:
1. Financial Pulse overview.
2. Money Flow visualization (Sankey only if the data supports meaningful source/target/value fields).
3. Wealth allocation visualization.
4. Financial Intelligence Graph linking supported entities.
5. Contextual detail panel with source, timestamp, values, evidence and uncertainty where available.

Do not display all views simultaneously by default. Use filters, grouping, progressive disclosure and drill-down. Keep charts readable, keyboard accessible, responsive and useful on smaller screens.

## Motion rules

Animation must communicate direction, magnitude, change or a selected relationship:
- Subtle animated particles or moving dashes along cash-flow edges.
- Highlight a selected node and its directly related path.
- Smooth expand/collapse and view transitions.
- Optionally highlight a supported news-impact path.

Do not use perpetual animation everywhere, glowing neon networks, gratuitous particles, or heavy 3D effects. Respect reduced-motion preferences and provide a static view. Never let animation imply an unverified causal relationship.

## Acceptance

- Graph nodes/edges come from real data or explicit, tested domain logic.
- User can select, filter, expand and inspect entities.
- Relevant cross-feature navigation preserves context.
- Missing/uncertain data is clearly represented.
- Performance remains reasonable for expected data volume.
- Existing features remain available.
- Tests and screenshots/evidence are recorded where tooling permits.
