# OneWealth — Unified Financial Graph & Flow Intelligence (owner, 2026-10-17)

Verbatim, as given in the working session after the core and layout work (OWN-GW-20…32) was delivered.

---

# OneWealth — Unified Financial Graph & Flow Intelligence

Continue from the current implementation. Do not rebuild the application from scratch.

First, inspect the existing codebase, the original BRD and its accumulated materials under `docs/brd/`, including feature specifications, architecture, UI references, business logic, and decisions. Understand the current graph renderer, financial data model, news-impact engine, goals, scenarios, and assistant before making changes.

## 1. One Unified Financial Graph

Make the central financial graph the primary interface for the Customer role. Integrate assets, liabilities, income, expenses, transactions, news impacts, financial goals, risks, and scenarios into one coherent, interactive financial model.

Preserve the existing layout: compact left icon toolbar, large central graph, right-side Assistant/Info panel inspired by OperonX Studio, and collapsible bottom dashboard.

Switching navigation items should enrich or refocus the graph, filter its nodes and flows, or reveal relevant details—not unnecessarily replace the entire central experience. The Expert/contact section may retain its own dedicated interface where appropriate.

## 2. Real & Hypothetical Money Flows

Every relevant relationship should be represented consistently, with directional animated flows wherever meaningful.

- **Actual:** Verified income, expenses, transfers, debt payments, and other real cash movements.
- **News impacts:** Estimated financial consequences of news, policies, infrastructure projects, market changes, and other external events.
- **Goals:** Projected savings, contributions, purchases, education expenses, retirement funding, and other goal-related cash flows.
- **Scenarios:** Hypothetical market movements, property-price changes, interest-rate changes, income changes, and user-defined what-if simulations.

Distinguish actual data, estimates, assumptions, and family-related information visually and semantically. Hypothetical flows must never be presented as completed transactions or silently added to current assets.

Support tracing an impact from its source through affected assets, liabilities, income, expenses, liquidity, and projected net worth. When multiple scenarios interact, track their assumptions and dependencies, prevent double-counting, and clearly indicate which scenarios are active.

## 3. Data-Driven Flow Animation

Refactor the existing animation system so all eligible financial-flow edges have continuous, subtle directional motion, inspired by the dataflow effects in OperonX Studio.

Drive particle density, speed, trail length, and prominence by normalized monthly monetary flow, with sensible limits. Higher-volume flows should feel stronger; smaller flows should remain visible but restrained.

- Animate direction correctly for inflows and outflows.
- Use distinct visual treatments for actual, estimated, and hypothetical flows.
- Non-monetary relationships must not imply fabricated financial transfers.
- When the assistant answers, streams text, investigates an event, or runs a scenario, synchronize graph movement and light pulses with the relevant nodes and paths.
- Keep labels and financial figures crisp and readable.

## 4. Central Wealth Core

Redesign the central net-worth node as the visual heart of OneWealth. It should feel dimensional, luminous, and alive—not like a flat circle or generic button.

Use restrained layered depth, inner illumination, refined rim lighting, subtle breathing motion, and concentric effects. Let real financial flows and assistant activity produce meaningful responses through the core and connected edges.

Maintain a clear hierarchy between the core, primary assets, secondary entities, and contextual information. Avoid excessive neon, distracting particles, or a generic sci-fi game aesthetic.

## 5. Graph Layout & Interaction

Fix the underlying layout and edge-routing algorithms. Do not merely adjust individual node coordinates or hide visual defects with styling.

- Prevent node and label collisions.
- Minimize edge crossings and unnecessary bends.
- Never route edges through nodes or labels.
- Organize assets, transactions, news, goals, risks, and scenarios into clear visual groups around the central wealth core.
- Preserve the identity and traceability of individual financial flows.
- Progressively reveal secondary nodes or collapse groups when the graph becomes dense.
- Provide reliable zoom, pan, fit-to-view, selection, focus, and graph/list switching.
- Keep layouts stable when selecting nodes, changing views, or receiving assistant responses.

Prioritize readability over displaying every node simultaneously. The graph should remain understandable as the number of relationships grows.

## 6. Assistant Integration

Keep the existing Assistant/Info panel architecture inspired by OperonX Studio.

The assistant must be able to explain graph relationships, investigate news, inspect assets, compare scenarios, and help users perform supported tasks. When it responds, the graph should react contextually to the relevant entities and flows rather than running unrelated decorative animations.

Selecting a node or edge should expose its details, source, calculation, assumptions, confidence where available, and downstream effects in the Info panel. Keep the assistant aware of the current graph selection and active scenario.

## 7. Performance & Correctness

Reuse the current rendering stack and existing OperonX Studio patterns where practical. Avoid introducing an expensive parallel animation or calculation system without a clear need.

Use efficient rendering, limit unnecessary animation work, reduce off-screen activity, and respect reduced-motion preferences. Ensure the graph remains responsive with realistic data volumes.

Never invent transaction amounts, financial projections, news evidence, or confidence scores. If required data or logic is missing, identify the gap and implement only what can be supported correctly.

## 8. BRD & Implementation Discipline

The original BRD is the source of truth for business requirements. Preserve every existing feature and its business logic; this is a redesign of how capabilities are presented and connected, not permission to remove or simplify required functionality.

Update `docs/brd/` incrementally with architecture decisions, feature mappings, graph semantics, flow-calculation rules, UI references, and testing evidence. Keep the documentation consistent with the actual implementation.

Before finishing:
- Map existing BRD features to their new graph representations and interactions.
- Test actual and hypothetical flows, directionality, scenario combinations, and double-counting safeguards.
- Test dense graph layouts, node selection, assistant streaming, and animation performance.
- Run the relevant tests and fix regressions.
- Report completed work, test results, remaining gaps, and any BRD requirements that are not yet implemented.

Proceed autonomously through implementation and verification. Do not stop at a proposal or mockup. Make sensible engineering decisions unless a genuinely critical ambiguity blocks safe implementation.
