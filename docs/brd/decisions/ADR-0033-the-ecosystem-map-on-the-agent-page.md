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
