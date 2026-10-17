# OneWealth — Redesign the Central Wealth Node (owner, 2026-10-17)

Verbatim, as given in the working session after the money-flow sparks
([`2026-10-17_graph_dataflow_refinement.md`](2026-10-17_graph_dataflow_refinement.md)).

---

### Redesign the Central Wealth Node

The central "My Wealth" node is currently too flat and visually weak. It represents the heart of OneWealth and must become the most visually compelling element in the financial graph.

Redesign it as a premium, dimensional financial core—not a simple filled circle or a generic glowing button.

- Create depth using layered translucent surfaces, subtle inner illumination, refined rim lighting, and restrained volumetric/glass-like effects.
- Add slow, elegant ambient motion, such as subtle breathing light and gently moving concentric rings.
- Integrate the core with the graph's directional dataflows. Financial flows and assistant activity should produce meaningful, synchronized light pulses through the core and relevant connected edges.
- Keep the net-worth value and supporting figures crisp, stable, readable, and accessible. Effects must never compete with the financial information.
- Give the core distinct but subtle states: idle, selected, assistant thinking/streaming, and active financial-flow interaction.
- Maintain a sophisticated visual hierarchy. Avoid excessive neon, noisy particles, constant spinning, or a generic sci-fi game aesthetic.
- Prioritize smooth performance using the existing rendering stack, GPU-friendly effects where appropriate, and reduced-motion support.

Inspect the current graph renderer and existing OperonX Studio dataflow effects before implementation. Integrate with the existing architecture rather than layering an expensive independent animation system on top.

The result should feel like the living heart of a financial intelligence system: visually magnetic, calm, intelligent, and seamlessly connected to the graph around it.
