# One checklist of the agents, one name each (owner, 2026-10-22)

**Asked.** "There are so many agents that they confuse me: give each a name, and a checklist of all of them and what
they do." It came up from the daily agent benchmark, which nobody could point at by one name.

## What is there today (read from the code, 2026-10-22)

Every place the app calls a language model, by the setting (`resources.yaml`) it goes through:

| Part | What it does | Setting | Code |
|---|---|---|---|
| Agent CIO | reads an event's news, drafts the market view and its 2–4 scenarios | `llm:cio` | `src/views/agents.py` |
| Agent Phản biện | critiques the CIO agent's draft before the CIO decides | `llm:challenger` | `src/views/agents.py` |
| Agent Chính sách | summarises one verified policy document, a quote per point | `llm:cio` | `src/policy/agent.py` |
| The daily trial's grouping | one call a morning: the day's news grouped into events | `llm:cio` | `src/trial/daily.py` |
| OneWealth Copilot (the Trợ lý panel) | answers every role with the app's tools; writes wait for the person | `llm:copilot` | `src/assistant/turn.py` |
| its helpers | a conversation's title and goal; memory distilled from a finished conversation; web search; the tool router when there is no tool-calling model | `llm:copilot` | `src/assistant/sessions.py`, `consolidate.py`, `web.py`, `src/copilot/router.py` |
| Declaration chat | records what a client says they own (land, gold, a loan…); rules when no model | `llm:assistant` / `llm:onprem` | `src/declare/` |
| Statement reader | reads an uploaded bank statement into holdings; rules when no model | `llm:assistant` / `llm:onprem` | `src/statements/graph.py` |
| Newsletter writer | the newsletter's opening paragraph only, from approved views | `llm:cio` | `src/newsletter/compose.py` |

And three different things are each called "the benchmark":

| Name | What it checks | When | Today |
|---|---|---|---|
| **Thử nghiệm hằng ngày** (daily trial) | Agent CIO + Phản biện on the day's news, no person; shadow forecasts scored against the market | 08:30 every day to 10-31 (`trial_daily`, `trial_score`) | ran 10-22 on its own: 5 events, 0 errors; first scores due 10-24 |
| **Cổng thay đổi** (change gate, BRD MEAS-07) | a fixed set of sample news with expected answers | only when a new prompt or model is proposed (`agent_eval`) | passes or blocks the proposal |
| **Bộ kiểm tra trợ lý** (assistant test set) | 32 questions to OneWealth Copilot | by hand (`scripts/eval_assistant.py`) | 31/32 last run |

**What is wrong.**

1. **The catalogue lists 5 of these, and one of them wrongly.** The Agent page's catalogue (BRD FR-703,
   `src/views/catalogue.py`) has Agent CIO, Phản biện, Chính sách, "Diễn giải nội bộ" (no model) and "OneWealth
   Copilot (bộ định tuyến)", which describes the old router ("never reads client data"). The real assistant, which
   reads the person's data through its tools, is not in it; nor are the declaration chat, the statement reader, the
   newsletter writer or the trial's grouping.
2. **The same part has two or three names**: "Trợ lý OneWealth" on the map and the memory page, "OneWealth Copilot" on
   the panel and in the owner's requirements, "Copilot (bộ định tuyến)" in the catalogue.
3. **The RM's "Hiệu quả tư vấn" page shows a fourth set** — "AI News Reader, AI Impact Assessor, AI Planning Advisor,
   AI Client Chat" with scores — from generated sample data (`data/advisory.json`, `scripts/make_advisory.py`),
   not marked as sample. Two of the four are not AI at all: the impact is the engine's arithmetic, the plan is the
   RM's.
4. **Nothing stops a new model call from being added without a line in any list.**

## Decisions

- **The names.** Vietnamese on the screens (the app's language), the English beside them in documents:
  Agent CIO (CIO agent), Agent Phản biện (Challenger), Agent Chính sách (Policy agent), **OneWealth Copilot** (the
  assistant: the owner's name for it, OWN requirements), Khai báo qua chat (Declaration chat), Đọc sao kê (Statement
  reader), Viết bản tin (Newsletter writer). The trial's grouping is a step of the daily trial, not an agent of its
  own. "Diễn giải nội bộ" stays, marked "không gọi mô hình".
- **One list, in the code.** The catalogue becomes the checklist: every part above with its name, what it does, its
  owner and risk, its setting and the model it uses now, what data it reads, who checks its output, how it is
  measured (which of the three, or "chưa đo" said plainly) and when it runs. The map, the pages and the document take
  names from it.
- **The setting names (`llm:copilot`, `llm:assistant`) are not renamed in this plan.** Swapping two names is the
  rename most likely to send a client's question to the wrong model; the data barrier's rules, the live `.env`
  (`LLM_MODEL_COPILOT`) and every stored run record are keyed by them. The checklist says, per setting, which parts
  use it, and so does `resources.yaml` — that removes the confusion without the risk.
- **The map keeps its shape.** It draws a question's way and the CIO desk; the parts it does not draw are in the
  checklist right under it, each with a link to its page.

## Steps

- **C1 The checklist.** `src/views/catalogue.py`: eight entries — the parts above, the helpers inside OneWealth Copilot and the
  trial's grouping inside Agent CIO, plus Diễn giải nội bộ — the outdated Copilot entry replaced, the
  three evaluations as a list of their own with their schedule and latest result. `GET /api/agents/catalogue` keeps
  its shape, with the new fields added. `resources.yaml`: a comment per setting naming its users.
- **C2 The guard.** A test: every file in `src/` that calls a model through a setting belongs to a checklist entry,
  every entry's files exist, every entry has a name, an owner and a measure (or "chưa đo"). Adding a model call
  without adding it to the checklist fails the tests.
- **C3 The page.** The Agent page (CIO, Compliance, Admin): the checklist as one table under the map — name, what it
  does, owner, model now, measured by, runs — with "Của tôi" (the agents the person's role owns) for the CIO and
  Compliance; then the three evaluations with their latest result. Screenshots desktop and phone, light and dark.
- **C4 One name everywhere.** The map's labels, the memory page's eyebrow, the trial page and its report take the
  checklist's names. The RM's "Hiệu quả tư vấn" chain: its four steps named for what they are (Agent CIO, Bộ máy tác
  động — không gọi mô hình, Kế hoạch của RM, OneWealth Copilot) and the panel marked **Dữ liệu mẫu**.
- **C5 The one-pager.** `docs/AGENT_CHECKLIST.md`: the checklist and the three evaluations for the business, in
  plain words; a test keeps it listing every entry.

**Gate.** Every model call in `src/` is in the checklist (the C2 test); the Agent page shows all eight with their real
model and measure; no screen uses a name the checklist does not; the tests that touch these pages pass.

**Not in this plan** (raised 2026-10-22, the owner decides separately): the daily trial's empty recall figure, and an
alert when the 08:30 run fails or the model bridge is down.
