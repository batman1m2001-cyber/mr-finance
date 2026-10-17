# The assistant, tested as its customers use it — plan

Owner request, 2026-10-17: “OneWealth — Real-World AI Assistant Stress Test”. The verbatim copy is in
`docs/brd/sources/owner_requests/2026-10-17_assistant_stress_test.md`. Act as real customers and test the assistant
end to end, through its real interface and backend. Fix what fails, add regression tests, and report honestly.

Decided with the owner (2026-10-17):
- **Target:** the graph experiment, branch `exp/graph-workspace` (:8040). It has the newest assistant: the graph
  context, `lien_ket` and `so_sanh_kich_ban`. Fixes stay on this branch.
- **Budget:** at most US$3 of paid model calls for the whole test. The spend is counted per turn and reported.

Deliverables, in `docs/brd/testing/assistant/`:
- the catalogue;
- the transcripts;
- the results;
- the defects;
- the coverage matrix;
- the readiness report.

## 1. What exists (read 2026-10-17)

- **The A8 eval.** `scripts/eval_assistant.py` and `data/assistant_eval.json` hold 32 cases (42 turns). They run
  `assistant_flow` in-process, not through the server. Its checks are reused here: grounding (every figure comes
  from a tool or the question), refusals, other clients' figures, the role's writes. The gate passed at 31/32
  (assistant_readiness.md).
- **The client's 22 tools.**

  | Kind | Tools |
  |---|---|
  | Read | `tong_quan`, `dong_tien`, `dong_luc`, `tac_dong`, `dieu_tra`, `chu_y`, `muc_tieu`, `kich_ban`, `lien_ket`, `so_sanh_kich_ban`, `de_xuat`, `tai_lieu`, `tim_kiem`, `huong_dan`, `mo_trang`, `tim_lich_su`, `doc_lai_phien`, `theo_doi_cua_toi`, `nho_lai` |
  | Write (the person confirms) | `gui_de_xuat`, `ghi_nho`, `quen`, `theo_doi`, `huy_theo_doi` |
  | Paid | `tim_tren_web` |

- **What no tool does.** No tool creates or changes a goal, and none turns a scenario on in the graph: the person
  does those on the page. Requests for them are tested for an honest answer that points to where it is done (§4,
  “actions”).
- **The real path.** The panel posts to `POST /api/assistant/stream` (SSE). The body carries the role, client,
  scope, route, followed goals, the graph context and a `conversation_id`. A write comes back as `waits`, and the
  panel answers with `{turn_id, approvals}`. Conversations live on the server (`/api/assistant/conversations`).

## 2. Decisions

**S1. Through the server, on its own copy.** A second server runs the same code on its own state:
- `PORT=8041`, `MF_STATE` on a copy of `state.db` and `assistant.db`, `OPERONX_RUNS_DIR` apart, `MF_JOBS=off`;
- its writes (memory, follow-ups, proposals) never touch :8040's data.

Every conversation signs in through `/api/auth/demo` and speaks over the same SSE stream the panel uses. A write
is confirmed or refused the way the panel does it. The state is then read back through the app's own endpoints, so
a claimed success is checked, not believed.

**S2. Personas.** Three demo customers with different pictures:
- C01, wealthy, with a family scope;
- C02 and C03, smaller.

Each is spoken to in its own voice: a novice, an expert, anxious, terse, or a typo-heavy mobile writer. An RM
session is used only where the brief asks for a request on another user's data.

**S3. The catalogue is data.** `docs/brd/testing/assistant/catalogue.json` holds the conversations. Each has a
category, a persona, the BRD rows it covers, and its turns. Each turn has its message and its checks:
- the tools expected and forbidden;
- the status (answer, write waiting);
- what it must and must not say;
- a confirm or deny for a write, and the state to read back;
- the graph context sent.

`catalogue.md` is generated from it for reading.

**S4. Two judges, neither a model.**
- **Machine checks per turn:** the S3 checks, plus the eval's grounding and leak checks across the conversation;
  the mode (model, template); the cost and the latency.
- **My review of every transcript:** accuracy against the data, calculations, tone, clarification, honesty about
  limits, and wasted tokens.

A failure is recorded only after reading the transcript. A grader fault is fixed in the grader and named as one.
No model judges another model: that would cost credit and add a second source of error.

**S5. Severity.**

| Severity | Meaning |
|---|---|
| S1 critical | A privacy leak, a write without confirmation, a claimed action that did not happen, or invented personal data or a source |
| S2 major | A wrong figure or calculation, the wrong tool, a broken workflow, a missed refusal, false reassurance |
| S3 minor | Unclear or poorly adapted wording, a missing clarifying question, a needless tool call or token waste |
| S4 cosmetic | Formatting |

Fixes go in severity order. Each confirmed defect gets a regression test, offline where the cause is code or a
rule, with a scripted model. The conversation that showed it is then rerun on the real model.

**S6. Failure modes on purpose.**
- A third server (:8042) whose provider URL is dead: the fallback path and its honesty.
- Web search without a provider.
- A tool that fails: a client whose data is missing.
- A conversation long enough to compact.

None of these is mocked inside the model's path: each is a real server whose dependency is really absent.

**S7. In the browser too.** A Playwright pass on :8041 checks what HTTP cannot:
- the graph selection reaching the answer;
- the nodes lighting;
- the confirm button and the state after it;
- the session title and history after a reload;
- phone width.

**S8. Cost control.**
- The harness stops at US$2.70 spent.
- Every turn's `usage` (model and tool cost) is summed per conversation.
- A rerun covers only the conversations affected by a fix, plus one full final run.
- Web search is paid, so it runs in few, deliberate turns.

## 3. Phases

| Phase | What | Gate |
|---|---|---|
| T0 | This plan; the owner's request saved; the :8041 copy; `scripts/stress_assistant.py`; the catalogue | One conversation per category runs end to end on the real model, writes confirmed and read back, cost counted |
| T1 | The full catalogue on the real model; transcripts; machine checks; my review of every one | Every failure classified: real (with severity) or grader fault |
| T2 | Fix the confirmed defects in severity order; regression tests; rerun the conversations that showed them | Every S1 and S2 fixed or named as an external blocker; the suites stay green |
| T3 | The browser pass (S7) and the failure modes (S6) | Each scenario run and recorded |
| T4 | A final full run; results; defects; coverage matrix; readiness report; the BRD rows touched | The reports state the actual coverage and the spend; `check_brd_docs.py` reports 0 errors |

### Progress (2026-10-18)

| Phase | Status |
|---|---|
| T0 | Done (99c8443): the plan, the request, the harness, the catalogue, the :8041 copy |
| T1 | Done: 74 conversations; every failure classified (D01–D21 real, G1–G3 grader) |
| T2 | Done: every S1 and S2 fixed (D13 is the S1; it is also on `main`, the owner's decision); T2's rerun found D22–D27 and D19 again, all fixed |
| T3 | Done: the browser pass twice (D30, D31; browser.md) and the failure modes on :8042 (fm-01…07, 7 of 7 by hand) |
| T4 | Done: the final run (76 of 81 by the machine checks, 80 of 81 by hand), results, defects (32: 28 fixed, 4 open), coverage (49 requirements, 46 held), readiness. US$1.97 of the US$3 cap |

## 4. The catalogue, by category

Each category has several multi-turn conversations. Each one starts from a real concern, then follows up,
challenges the answer, adds a constraint or corrects itself.

| Category | What is checked |
|---|---|
| Navigation | How to use a feature, where a figure lives, what a graph node means, how a number is computed (guide citations, `mo_trang` links) |
| Personal finances | Net worth, cash flow, spending, debt, liquidity, allocation, financial health: figures equal to the pages' |
| Financial knowledge | Basic and advanced (savings, stocks, bonds, funds, gold, rates, inflation, tax, risk): general knowledge labelled as such, no personal figures invented |
| News and impacts | Which news touches me and how much; sources; estimate against fact |
| Goals and planning | Home, education, retirement, emergency fund, independence: the goals tool's figures and its assumptions |
| What-if | Crash, property, income loss, rates, competing goals; `kich_ban`, `so_sanh_kich_ban`; nothing added to net worth |
| Personal concerns | Anxiety, family, job insecurity, debt: empathy without false reassurance; a practical next step |
| Actions | Remember, forget, follow, unfollow, send a proposal: confirm, refuse, read back; goal and scenario changes asked for, which no tool does |
| Memory and sessions | Multi-turn context, a remembered fact used in a new session, titles, history search, separation between sessions and users |
| Ambiguous and difficult | Missing information, contradictions, corrections, broad questions, multi-step tasks |
| Out of scope | General questions: web search with sources, or an honest “cannot”; no pretended capability |
| Adversarial | Prompt injection in the message and in retrieved content; another client's data; a claimed role; conflicting instructions; secrets |
