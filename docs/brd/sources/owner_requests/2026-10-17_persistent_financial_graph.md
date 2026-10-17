# OneWealth — Persistent Financial Graph Redesign (owner, 2026-10-17)

Verbatim, as given in the working session, with the concept image
[`GW-01_concept_persistent-graph_illustrative.png`](../../assets/proposed_ui/GW-01_concept_persistent-graph_illustrative.png)
(“inspiration for layout and interaction, not a rigid visual specification”).

Instructions given with it:

> you should break it to another branch, and serve in another publink, this is just experiment

> update the brd first, extract the change to a refactor md plan (refer to brd) , then go

---

# OneWealth — Persistent Financial Graph Redesign

The existing OneWealth application is already well developed. This is an architectural UI/UX refactor, not a
greenfield rewrite.

Inspect the entire codebase and `docs/brd/` before implementation. Use the attached concept image as inspiration
for layout and interaction, not as a rigid visual specification. You have existing OperonX Studio context—reuse its
graph dataflow animation patterns and right-side panel interaction model where appropriate.

## 1. Replace the Dashboard-Centric Experience

Create a **Persistent Financial Graph** as the primary workspace for the Customer role.

- **Left:** Replace the current horizontal feature navigation with a compact vertical icon toolbar with tooltips.
- **Center:** A large, interactive, scrollable financial graph. My Wealth is the central node, connected to assets,
  income, expenses, liquidity, goals, news, risks, and hypothetical scenarios.
- **Right:** Reuse the OperonX Studio-style interaction pattern for the Assistant and contextual
  Information/Inspector panel.
- **Bottom:** Provide a collapsible dashboard strip for essential metrics and compact charts from the existing
  overview.

Keep the graph as the persistent central workspace. Switching menus should change the graph's focus, filters,
visible branches, and level of detail—not replace the entire page or reset the graph. Open dedicated views only
when a feature genuinely requires a different interaction model.

## 2. Make the Graph Feel Alive

Refactor the assistant interaction lifecycle so the graph feels like an active participant in the conversation.

- While the assistant is thinking or executing tools, show subtle, meaningful activity along relevant nodes and
  edges.
- As the answer streams, progressively highlight the corresponding assets, relationships, and financial flows.
- When the assistant references a news event, risk, asset, or scenario, connect the explanation to the relevant
  graph elements.
- When a response completes, leave a clear visual indication of the relevant nodes and relationships. On failure,
  show truthful failure feedback.

Coordinate animations with real streaming events, tool execution, and application state. Do not fabricate progress
or trigger unrelated animations. Keep motion elegant, lightweight, and non-disruptive.

## 3. Preserve All Existing Capabilities

**The original BRD is the functional source of truth. This redesign must not remove, silently simplify, or break
any existing requirement.**

Before implementation, map every existing feature to its new entry point and interaction model. Reuse the graph as
a unified visualization and navigation layer, while retaining dedicated interfaces for workflows that cannot
reasonably be represented within it. The Experts/contact functionality may remain a separate view.

Update `docs/brd/` and maintain traceability between original requirements, redesigned interactions,
implementation, and tests. Preserve existing business logic, data integrity, permissions, and integrations.

Distinguish actual financial data and cash flows from market estimates, forecasts, and unverified rumors.
Hypothetical scenarios must never silently modify actual portfolio values.

## 4. Implementation and Verification

Audit the current graph implementation, assistant streaming architecture, existing UI components, and OperonX
integration before selecting an approach. Reuse existing capabilities and avoid unnecessary dependencies or a
complete rewrite.

Implement the redesign incrementally, then test:

- Navigation and graph-state persistence across menu changes.
- Node selection, contextual inspection, and assistant-to-graph interaction.
- Streaming responses and synchronized animations.
- Existing feature coverage against the original BRD.
- Performance, responsive layouts, accessibility, and reduced-motion preferences.

Do not stop at mockups or recommendations. Implement the changes, run available checks, and report actual results,
remaining gaps, and performance observations.

**Design principle:** OneWealth is one interconnected financial world, not a collection of dashboards. The graph
remains the user's workspace; navigation changes what they explore, and the assistant brings that world to life
through meaningful, real-time interaction.
