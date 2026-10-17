# OneWealth — Graph Layout & Edge Routing, Critical Fix (owner, 2026-10-17)

Verbatim, as given in the working session together with
[`2026-10-17_central_wealth_core.md`](2026-10-17_central_wealth_core.md).

---

### Graph Layout & Edge Routing — Critical Fix

The current graph layout is cluttered: nodes and labels overlap, edges cross excessively, and secondary data-source connections form an unreadable tangle. Fix the underlying layout and routing algorithms, not just the styling.

- **Collision-free layout:** Nodes and labels must not overlap. Maintain adaptive spacing based on node dimensions, labels, graph size, and viewport.
- **Clear hierarchy:** Keep My Wealth as the central anchor, primary asset nodes in a well-spaced surrounding layer, and secondary sources, transactions, risks, goals, and scenarios in organized contextual groups. Avoid arbitrary positioning and overcrowded radial layouts.
- **Intelligent edge routing:** Minimize edge crossings, unnecessary bends, and lines passing through nodes or labels. Use curved, bundled, or orthogonal routing where appropriate, with consistent entry and exit points.
- **Readable connections:** Distinguish primary financial flows from supporting relationships and hypothetical impacts. Keep inactive edges subtle; highlight active paths without illuminating the entire graph.
- **Adaptive exploration:** When the graph becomes dense, progressively reveal secondary nodes, collapse groups, or expand selected branches. Provide fit-to-view, zoom, pan, and a way to focus on selected nodes without losing context.
- **Stable interaction:** Layout changes should be predictable. Preserve the user's mental map and avoid nodes jumping around unnecessarily when selecting assets, switching graph views, or receiving assistant responses.

Inspect the existing graph renderer and layout implementation before choosing the solution. Reuse the current stack where practical; consider layered/hierarchical layouts, collision avoidance, and edge-routing algorithms rather than manually tweaking coordinates.

Test with realistic graph sizes and dense connection patterns. Verify node and label collisions, edge crossings, readability at different zoom levels, and performance.

**Acceptance criterion:** The graph must remain visually organized and readable as its complexity grows. No overlapping nodes or labels, no edges passing through nodes, and no uncontrolled web of crossing connections. If a layout cannot remain readable, reduce visible complexity intelligently instead of squeezing everything into the viewport.
