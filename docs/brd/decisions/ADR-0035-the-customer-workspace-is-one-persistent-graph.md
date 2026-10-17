# ADR-0035 — The Customer's workspace is one persistent graph; pages become lenses and sheets

- **Status:** accepted for the experiment (branch `exp/graph-workspace`); `main` keeps ADR-0013/ADR-0019's page shell
  until the owner decides
- **Date:** 2026-10-17
- **Sources:** OWN-GW-01…14; FEAT-40; docs/GRAPH_WORKSPACE_PLAN.md

## Context

The owner asks for the Customer role to work in one financial graph that never goes away: navigation changes what
the graph shows, the assistant animates it from real events, and no existing requirement is lost. Today every
menu item replaces `#page` with a page module (ADR-0019); the overview graph (FEAT-30, `map.js`) is one of those
pages; the assistant answers in one JSON reply (`POST /api/assistant`), so nothing can move while it works.

## Decision

1. **Scope:** the Customer role only. RM and the staff roles keep the page shell; the RM's client pages are the same
   modules and keep working.
2. **The workspace is a long-lived component**, not a page: the shell mounts it once for the client and hands it the
   route. A route is a lens (and optionally a sheet); a lens is view state, never a re-render of the graph.
3. **Dedicated views are sheets:** the existing page modules render unchanged into a panel over the graph, which
   stays mounted. A capability that does not fit the graph keeps its whole page this way, so nothing is simplified.
   Every old Customer address resolves to a lens and sheet.
4. **The graph's data stays one endpoint** (`POST /api/overview`, FEAT-30), extended with `flow`, `liquidity` and
   `scenario` kinds and a `certainty` on every node and edge (`actual`, `estimate`, `hypothetical`). Scenario
   values are never summed into totals.
5. **Streaming through operonx itself:** a second door on the assistant, `POST /api/assistant/stream`, a served
   graph with doors (`ingress` → the turn as a generator op over `Runner.stream` → `egress` per event), read as
   server-sent events. The JSON door stays for every other role and for the tests. The new service writes no
   traces (its items hold the person's words, as ADR-0033's privacy fix).
6. **Motion follows FEAT-33's rule:** transform and opacity only, particles as Web Animations tracked by
   `motion.js`, nothing on a timer, paused when hidden, still under reduced motion. Every animation starts from a
   stream event or a person's action.
7. **No new dependency:** SVG and the existing chart helpers; Studio's patterns (live-run node states, particles
   along wires, a tabbed right dock) are reimplemented in the kit's tokens, not imported.

## Consequences

The Customer shell changes shape (toolbar, dock, strip) while every page module is reused as a sheet; the RM shell
does not move. Tests that drive Customer routes now find their content inside a sheet. If the experiment is not
taken, the branch is dropped and nothing on `main` changed.
