# ADR-0032 — One tool registry: roles, writes confirmed and verified, timeouts, costs

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** OWN-AS-04…06; brief §1 (“controlled, discoverable tools—not unrestricted access”); ADR-0012;
  docs/ASSISTANT_PLAN.md A-D7

## Context

The Copilot has 13 tools in `copilot/tools.py`, each wrapping a served graph or a role-filtered read, writes
confirmed first. The assistant needs many more, chosen by a model.

## Decision

- `src/assistant/registry.py` holds every tool: name, Vietnamese description, roles, kind (read / write / external /
  memory), typed arguments (enumerations and server-resolved ids — never a path, query or URL), the run (the page's own
  graph or read), for writes a confirmation summary and a verifier, a timeout and a cost class.
- A turn gets only its role's tools. Writes have `approval="always"`: the run parks; the person confirms in the panel;
  the run resumes. After the write, the verifier reads the state back; a failed check is reported.
- The Copilot's tools move in unchanged; `copilot_flow` reads them from the registry.

## Consequences

Adding a capability to the assistant is adding a registry entry with its tests (role refusal, confirmation,
verification). The model can only do what a page can do for that person.
