# Requests of the product owner — `OWN-<area>-nn` (approved extensions)

Layer A, fourth source: requests the product owner gives directly, kept verbatim in
[`../sources/owner_requests/`](../sources/owner_requests/) (SRC-05). They are **not in the BRD**; the owner asked for
them, so they are approved for building. Each request is split into testable requirements below, in the owner's
words where possible.

Status: [`requirements_traceability.md`](requirements_traceability.md) §5.

## MOTION — Living Interface & Smart Animations (2026-10-16, backlog B-01)

Source: [`2026-10-16_living_interface.md`](../sources/owner_requests/2026-10-16_living_interface.md).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-MOTION-01 | **Idle presence**: subtle ambient motion around the assistant, to create a sense of presence | §1 “Idle” | documented |
| OWN-MOTION-02 | **Thinking**: gentle pulses or flowing highlights while the assistant is processing a request or executing tools | §1 “Thinking” | documented |
| OWN-MOTION-03 | **Responding**: briefly highlight the charts, assets, news or graph connections the assistant references, so the page feels connected to the assistant | §1 “Responding”, second paragraph | documented |
| OWN-MOTION-04 | **Completed / error**: clear, elegant visual feedback | §1 “Completed / Error” | documented |
| OWN-MOTION-05 | Premium, minimal, calm; no excessive glow, distracting movement, heavy 3D or whole-page animation; motion communicates a meaningful state change, never decoration | §1 last paragraph | documented |
| OWN-MOTION-06 | Performance: CSS transitions, transforms, opacity and simple SVG; no heavy animation library, no continuous JS loop, no needless re-render or layout; driven by real assistant and app events, never fabricated progress; suspended when the tab is hidden or the interface inactive; `prefers-reduced-motion` respected; usable on low-end devices; measured before and after | §2 | documented |
| OWN-MOTION-07 | Incremental: no redesign, business logic unchanged, every documented feature preserved; feature specs, UX docs, design system, traceability and changelog updated | §3 | documented |

## UI — redesign to the kit (2026-10-16, backlog B-00)

Source: [`2026-10-16_ui_redesign.md`](../sources/owner_requests/2026-10-16_ui_redesign.md); the gaps it names are
G1–G9 of [`docs/UI_REDESIGN_PLAN.md`](../../UI_REDESIGN_PLAN.md).

| ID | Requirement | Source | Doc status |
|---|---|---|---|
| OWN-UI-01 | Every page wears the kit's concept-board look (R-D1): light first, dark kept | request; plan G1, G2 | documented |
| OWN-UI-02 | The pages that predate the BRD are rebuilt in the new design with every block and action kept | plan G1, G7 | documented |
| OWN-UI-03 | Header search over what the role may open, and a notifications bell, as on the board | plan G2, R-D5 | documented |
| OWN-UI-04 | Graph overview with data sources, risks and goals, expand/collapse, node → page; an event timeline; the CIO's whole-run graph | plan G3, G5 | documented |
| OWN-UI-05 | Copilot answers with as-of time and sources, structured cards, investigate and stress-scenario tools, audited calls | plan G6 | documented |
| OWN-UI-06 | The live demo runs the real models (owner D-03) and shows real runs from fetched news | plan G8 | documented |
| OWN-UI-07 | Browser tests in the suite for every route and the main interactions | plan G9 | documented |
