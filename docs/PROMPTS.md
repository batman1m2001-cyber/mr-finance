# Prompts — where what the models are sent lives

Every text a model is given is a file in `prompts/`, asked for by name
(`operonx.prompts`, operonx ≥ 1.44; parts P5 of operonx's `docs/PROMPTS_PLAN.md` and O4 of
`docs/PROMPT_OBJECTS_PLAN.md`). Each is an object with an id: a text (`.md`) or a composite (`.yaml`) that links texts.
`operonx prompt list` shows them; the studio's Prompts page shows each with its versions.

## Before and after

```
before — a constant where it was used            after — prompts/
src/assistant/consolidate.py   SYSTEM            assistant/consolidate.md
src/assistant/web.py           SYSTEM            assistant/web.md
src/assistant/sessions.py      SYSTEM            assistant/session-title.md
src/assistant/attachments.py   PROMPT            assistant/attachment.md
src/assistant/turn.py          RULES + 7 consts  assistant/instructions.yaml (composite, below)
src/research/suggest.py        SYSTEM            research/suggest.md         {{purposes}} {{countries}}
src/trial/daily.py             SYSTEM            trial/daily.md              {{n}}
src/statements/graph.py        READ_PROMPT       statements/read.system.md, statements/read.user.md
src/declare/agent.py           instructions=     declare/agent.md
src/copilot/router.py          system (inline)   copilot/router.md
src/views/prompts.py           DEFAULT           cio/guard.md, analyst.md, debate.md, synthesize.md, challenge.md, policy.md
```

The code keeps its names: `SYSTEM = prompt("assistant/web", root=ROOT).text`. A prompt with data is rendered, never
`str.format`ted: `SYSTEM.render(n=n)`. In a file, data is `{{n}}` and every other brace is plain text, so the JSON a
prompt shows needs no doubling.

Nothing a model receives changed: `tests/test_prompts_golden.py` holds the sha256 of every text, and
`tests/test_instructions_golden.py` that of the assistant's instructions for each role × switch (256 cases).

## The assistant's instructions: one composite

The instructions were `rules.md` with seven Python constants pasted into its holes (`{{facts}}{{data}}`,
`{{duties}}`, `{{recount}}{{voice}}{{english}}`…). Now each rule is a text object and
`prompts/assistant/instructions.yaml` says which go in, by the data `turn.instructions` gives:

```yaml
kind: text
join: "\n"
parts:
  - use: assistant/persona          # who it is, how it speaks
  - pick: reads                     # model mode or template mode
    cases: {true: assistant/facts-model, false: assistant/facts-template}
  - when: data_room                 # cio, rm: count with truy_van
    use: assistant/data-room
  - use: assistant/writes
  - pick: role                      # a staff role's duties; the client has none
    cases: {rm: assistant/duties, cio: assistant/duties, admin: assistant/duties}
    else: none
  - use: assistant/guards
  - use: assistant/now              # {{today}} {{page}}
  - var: graph                      # what the workspace shows, "" when nothing
  - when: remember
    use: assistant/remembered
  - when: recount
    use: assistant/recount
  - when: voice
    use: assistant/voice
  - when: english
    use: assistant/english
```

`assistant/duties.yaml` is `-`, the role's own `assistant/duties/<role>`, then `assistant/duties/common`, joined by a
space. A part that renders nothing is left out with its join, so a client's typed Vietnamese turn is the same text it
always was. The studio's Prompts page draws this as a graph: each object a box, each `pick`/`when` a wire with its case.

## Two kinds of version

```mermaid
flowchart LR
  F[prompts/*.md] -->|"prompt(name)"| C[the assistant, research, trial, statements, declare, copilot prompts]
  F -->|"version 1"| D[views.prompts.DEFAULT]
  D --> K["`prompts` configuration kind<br/>(database: two people + the eval set)"]
  K --> A[CIO agents: analyst, debate, synthesize, challenge, policy]
```

- **The engineering prompts** are versioned by the files: `operonx prompt publish assistant/web --label production`
  freezes a version, `operonx prompt label assistant/web production 1` rolls back. With no label, the working text is
  served. They are read when the process starts.
- **The six CIO prompts** stay governed as they were (BRD-RULE-AI-02): the `prompts` configuration kind in the
  database, changed by two people and only after the eval set passes. `prompts/cio/` is its version 1, the text the
  agents shipped with; an Admin's later versions are not written back to the files. Moving that history into
  `prompts/labels.toml` would have a running server write into its own checkout, so it was left where it is.
  Their data is `{{guard}}`, `{{task}}`, `{{round}}` like every other prompt's (it was `<<guard>>`…; no version
  beyond 1 had been stored, so nothing in the database changed). The guard is still pasted into the other five as
  data: making it a link needs a version of the configuration whose prompts are composites, which two people propose
  and approve after the eval set — the configuration's own flow.
