# OneWealth — Refinement: Financial Graph & Dataflow Animation (owner, 2026-10-17)

Verbatim, as given in the working session, after the first build of the persistent financial graph
([`2026-10-17_persistent_financial_graph.md`](2026-10-17_persistent_financial_graph.md)).

Said with it:

> the dataflow in operonx studio graph , you should check it, it's quite clean and have an layout which is very clean
> to understand, the edge data is tiny like a web string, with glowing energy running through it

---

### Refinement: Financial Graph & Dataflow Animation

The current graph layout is on the right track, but its connections look static, cluttered, and visually weak. Refine the existing implementation rather than rebuilding the entire page.

1. **Improve graph hierarchy:** Keep My Wealth as the central anchor, primary assets as the second layer, and secondary data sources or relationships progressively revealed on demand. Reduce unnecessary edges, crossings, overlapping labels, and background clutter.
2. **Implement OperonX Studio-style dataflow animation:** Use elegant, directional electrical pulses or luminous particles traveling along curved graph edges, with subtle trails and endpoint reactions. Reuse the existing OperonX Studio animation patterns where possible.
3. **Make interactions meaningful:** When the assistant starts processing, streams an answer, invokes a tool, or references a financial entity, animate the relevant paths and nodes in sync with real application events. Highlight relevant relationships and dim unrelated branches.
4. **Distinguish flow semantics:** Actual financial flows, data relationships, and hypothetical news/scenario impacts must have visually distinct representations. Animation must never imply that a real transaction occurred when it did not.
5. **Preserve performance:** Prefer lightweight rendering and reuse existing graph infrastructure. Avoid animating every edge continuously. Respect reduced-motion preferences and test with realistic graph sizes.

Inspect the current implementation and the existing OperonX Studio graph/dataflow code before making changes. Implement and test the result; do not deliver only a design proposal. Preserve all original BRD requirements and the current application layout.

**Target:** A clean, readable financial graph that feels alive through directional, context-aware motion—not a static network diagram or a glowing web of tangled lines.
