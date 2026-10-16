# ADR-0033 — The Agent Ecosystem Map lives on the Agent page, drawn from real records

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** OWN-AS-20…22; brief §4; FEAT-15; docs/ASSISTANT_PLAN.md A-D8

## Context

The brief asks for a clear map of the assistant and the agents, their tools, connections and live states, with
drill-down, integrated in the existing UI and in the kit's visual language.

## Decision

- The Agent page (FEAT-15) opens on the map: overview first (person → assistant → tools and agents → data), grouped
  into front door, background, CIO desk and rules; each node's state (active, waiting, done, failed) from its records
  (`agent_runs`, `agent_jobs`, assistant runs, consolidator and follow-up rows); a node opens its runs, a run opens the
  existing trace drawer.
- Edges are only those that exist in code (a tool the agent owns, a store it reads or writes, an event that triggers
  it); the map's data comes from one endpoint built from the registry and the stores, and a test compares it with
  the traces.
- The panel links to the map; no separate monitoring page. Desktop and phone (a list per group on a phone).

## Consequences

The catalogue table stays below the map. A wrong edge or state is a failing test, not a drawing mistake.

## Notes (as built, A7, 2026-10-17)

- Built as decided: `src/views/ecosystem.py` (21 parts, 27 lines, each line's `file::symbol` checked by a test),
  `GET /api/agents/map` and `/api/agents/map/<part>` (CIO, Compliance, Admin), `web/pages/agents.js`.
- The groups are six, not four: the person and the data are drawn as their own lanes so each line crosses one gap.
- *Assistant runs* are its audited turns, not traces: tracing the assistant's services copied the person's question
  into `.operonx/runs`, so A7 turned those traces off. Jobs keep their traces (they hold counts) and the map's
  drill-down reads their ops from them.
- *A run opens the existing trace drawer*: the existing drawer (`trace.js`) explains an application run's numbers;
  the map's run drawer is its own (steps, status, time) in the same `core.drawer`.
- Desktop: lanes in three columns with plain lines (one colour, lit with the selected part); the main path of a
  question is a numbered strip above that lights its parts. Phone: a list per group, the lines in each part's drawer.
