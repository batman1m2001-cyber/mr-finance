# Prompts — where what the models are sent lives

Every text a model is given is a file in `prompts/`, asked for by name
(`operonx.prompts`, operonx ≥ 1.40; part P5 of operonx's `docs/PROMPTS_PLAN.md`).
`operonx prompt list` shows them; the studio's Prompts page shows each with its versions.

## Before and after

```
before — a constant where it was used            after — prompts/
src/assistant/consolidate.py   SYSTEM            assistant/consolidate.md
src/assistant/web.py           SYSTEM            assistant/web.md
src/assistant/sessions.py      SYSTEM            assistant/session-title.md
src/assistant/attachments.py   PROMPT            assistant/attachment.md
src/assistant/turn.py          RULES             assistant/rules.md          {{who}} {{language}} … filled per person
src/research/suggest.py        SYSTEM            research/suggest.md         {{purposes}} {{countries}}
src/trial/daily.py             SYSTEM            trial/daily.md              {{n}}
src/statements/graph.py        READ_PROMPT       statements/read.system.md, statements/read.user.md
src/declare/agent.py           instructions=     declare/agent.md
src/views/prompts.py           DEFAULT           cio/guard.md, analyst.md, debate.md, synthesize.md, challenge.md, policy.md
```

The code keeps its names: `SYSTEM = prompt("assistant/web", root=ROOT).text`. A template the code fills with
`str.format` is the prompt itself (`RULES.format(who=…)` is unchanged); in the file a variable is `{{who}}` and
every other brace is plain text, so the JSON a prompt shows needs no doubling.

Nothing a model receives changed: `tests/test_prompts_golden.py` holds the sha256 of all 16 texts as the constants
had them.

## Two kinds of version

```mermaid
flowchart LR
  F[prompts/*.md] -->|"prompt(name)"| C[the 10 prompts of assistant, research, trial, statements, declare]
  F -->|"version 1"| D[views.prompts.DEFAULT]
  D --> K["`prompts` configuration kind<br/>(database: two people + the eval set)"]
  K --> A[CIO agents: analyst, debate, synthesize, challenge, policy]
```

- **The ten engineering prompts** are versioned by the files: `operonx prompt publish assistant/web --label production`
  freezes a version, `operonx prompt label assistant/web production 1` rolls back. With no label, the working text is
  served. They are read when the process starts.
- **The six CIO prompts** stay governed as they were (BRD-RULE-AI-02): the `prompts` configuration kind in the
  database, changed by two people and only after the eval set passes. `prompts/cio/` is its version 1, the text the
  agents shipped with; an Admin's later versions are not written back to the files. Moving that history into
  `prompts/labels.toml` would have a running server write into its own checkout, so it was left where it is.
