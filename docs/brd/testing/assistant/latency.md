# The assistant's latency (2026-10-18)

The owner said the assistant takes too long to answer and asked whether it streams its answer. This page records
the diagnosis, what changed because of it, and the evidence that quality held. Branch `perf/assistant-latency`, from
`exp/graph-workspace`.

**In short:**
- **Streaming.** Yes, the answer streams word by word.
- **The wait.** Our server takes about 0.1 s of a turn. The rest is the model, called twice in a row on a turn that
  uses a tool, with hidden reasoning before each call.
- **The change.** Reasoning is off. On the same 26 conversations, run at the same time against the same data:
  - a turn takes a median of **3.26 s instead of 4.26 s** (p90 5.26 s instead of 7.50 s);
  - the person sees the first step or words after **1.06 s instead of 1.71 s**;
  - it is 0.8 s faster per turn when compared turn by turn, and faster on 44 of 53 turns.

## 1. Where the time went

A timed copy of the server logged each phase of 9 turns. One turn, "Tài sản ròng của tôi bao nhiêu?" (4.8 s in all):

| Phase | Time |
|---|---|
| Our code before the model (session, conversation, context) | 0.09 s |
| First model call, until it asks for a tool | 1.84 s |
| The tools | 0.19 s |
| Second model call, until its first words | 1.50 s |
| The rest of the answer, streamed | 1.10 s |
| Saving and finishing | 0.07 s |

Over the 9 turns:
- **Tool turns** took a median of 4.0 s and at most 5.4 s.
- **Turns without a tool** took 2.0–2.8 s.
- **Our code** took a median of 0.09 s. The model took 90–97% of every turn.

**Reasoning.** The model (`anthropic/claude-haiku-5.5` on OpenRouter) reasons before it answers unless told not to.
Called directly, with the assistant's own tools and instructions, `"reasoning": {"enabled": false}` brought its
first output forward:
- for the call that picks a tool, from 1.35 s to 1.03 s;
- for the call that writes the answer, from 1.41–1.45 s to 0.98–1.00 s.

**Why there were no traces.** The assistant's traces are off on purpose, because its ops hold what people say. So
nothing recorded where a turn's time went, and finding it needed a patched server.

## 2. What changed

1. **No hidden reasoning.** The agent's model settings send `reasoning: {enabled: false}` (`assistant/turn.py`).
2. **A turn's time, without its words.** Each turn's audit row (`assistant.turn`) now keeps its timing in
   milliseconds (`assistant.stream.Clock`):
   - before the first model call;
   - for each model call, its first output and its end;
   - the tools' time;
   - the first words the person saw;
   - the whole turn.

   `scripts/assistant_latency.py` reads these back as medians and p90s, for tool turns and turns without a tool.
3. **Figures said by the tools, not worked out by the model.** Without reasoning, the model compared and divided
   numbers itself and sometimes got it wrong. The tools now state the result themselves:
   - **Combining scenarios** now says whether the fall is over the client's drawdown limit. It uses the single
     stress test's rule (`scenarios/combine.py`; `so_sanh_kich_ban` and `gia_dinh` say it). Before, the model read
     a −8.6% fall as "nearly reaching" an 8% limit.
   - **The overview** says the reserve's months to one decimal ("32,7 tháng (khoảng 3 năm)"). Before, the model
     divided "3 năm" back out itself ("32 tháng").
4. **The scenario tools name the preset levels.** `gia_dinh` lists the preset levels in words (stocks down thirty
   per cent, rates up two points…). Its description also sends a preset added to the scenario just run to
   `so_sanh_kich_ban`. Without reasoning, the model had stopped looking the levels up in `kich_ban`'s description.
5. **The panel drops a lead-in.** Without reasoning, the model usually writes a sentence before its tool call:
   - how often: 38 of 41 tool turns;
   - an example: "Tôi xem dòng tiền của tháng gần nhất…".

   The panel used to run that sentence into the answer as it streamed, then drop it when the kept answer arrived.
   Now it clears the sentence when the step starts, because the step chip says the same thing. The words that stream
   are then the words that stay. This was checked in the browser on desktop and phone.

   An instruction not to write the lead-in had no effect (39 of 43), so it was removed.

## 3. Results

**Speed.** Same 26 conversations (53 turns), two copies of the same data, run in parallel so the provider's speed
was the same for both. The "Finished" column is a later run of the final code on its own (US$ cost not comparable:
33 conversations).

| | Reasoning on | Reasoning off | Finished |
|---|---|---|---|
| Turn, median | 4.26 s | 3.39 s | 3.26 s |
| Turn, p90 | 7.50 s | 5.35 s | 5.26 s |
| Tool turn, median | 5.48 s | 4.25 s | 4.12 s |
| No-tool turn, median | 2.66 s | 2.14 s | 1.99 s |
| First step or words, median | 1.71 s | 1.07 s | 1.06 s |
| Output tokens per turn, median | 489 | 341 | — |
| Cost of the 26 conversations | US$0.123 | US$0.109 | — |

**Where a tool turn's time goes now.** From the audit rows of the last run, 43 tool turns. That run still had the
lead-in instruction, which changed nothing measurable and was then removed.

| Phase | Median | p90 |
|---|---|---|
| Our code before the model | 0.03 s | 0.03 s |
| First call, until its tool call (about 0.3 s of it the lead-in sentence) | 1.37 s | 1.87 s |
| Tools | 0.14 s | 0.78 s |
| Answer call, until its first words | 1.00 s | 1.15 s |
| Writing the answer | 1.39 s | 2.31 s |
| The whole turn | 4.26 s | 5.38 s |

**Quality.**
- **The 26-conversation sample, by machine checks:** 23 pass with reasoning on, 22 with reasoning off.
- **Read by hand, one failure was real.** In `wi-01`, without reasoning, the model reported an 8.6% fall as near the
  8% limit. Fixes 3 and 4 above cover it. With them, `wi-01` was right on 6 of 6 runs.
- **The finished code on 33 conversations** (the sample, plus every what-if and goals conversation): 26 pass by
  machine. Each of the 7 flags was read by hand:
  - **Grader faults.** Figures from an earlier turn's tool, or the person's own arithmetic (40 − 12 = 28). An offer
    to run the "stocks −30%" scenario. In `adv-02`, the pattern 3,53 tỷ matched inside the customer's own 43,53 tỷ.
  - **The guide question (`nav-01`).** The guide does not describe the dotted lines, and the answer says so, as with
    reasoning on.
  - **The memory question (`act-01`).** It answered "what do you remember" from the memory in its prompt, not the
    tool. The answer was correct.

**Residual.** Without reasoning, the model sometimes adds a small figure it worked out itself:
- "nợ chiếm khoảng 5% tổng tài sản" (debt is about 5% of total assets);
- "−0,07 triệu/tháng".

This happened on 2 of 63 turns, and both figures were roughly right. With reasoning on, it did not happen on the same
turns. The instructions already say to use `tinh` for arithmetic. The next step, if it matters, is the same as fix 3:
the tool says the figure.

## 4. How to measure it again

```bash
# where the time goes, from any copy's audit log (turns since a day)
.venv/bin/python scripts/assistant_latency.py --state data/state.db --since 2026-10-18
# the A/B: two served copies (:8041 on the old code, :8042 on the new), the same conversations at once
.venv/bin/python scripts/stress_assistant.py --base http://127.0.0.1:8041 --state <copy-a>/state.db --tag ab-base --only <ids>
.venv/bin/python scripts/stress_assistant.py --base http://127.0.0.1:8042 --state <copy-b>/state.db --tag ab-new --only <ids>
```

Runs kept in `runs/`:
- `ab-base`: reasoning on;
- `ab-noreason`: reasoning off, before fixes 3–5;
- `ab-final`: the finished tools, before the timing gained its per-call ends.

**Spend:** about US$0.68 on the real model in all. That is US$0.04 for the diagnosis and US$0.62 for the A/B and
regression runs, plus about US$0.02 of live browser and stream checks.

## 5. Not done

- **Jev as a tool picker** (TypeSafe's decision model) was measured and not adopted. It adds 0.57 s before every
  model call, and its pick matched the model's on 59% of turns. Pruning the tool list also breaks the prompt cache,
  which costs about three times as much. The owner agreed (2026-10-18). See Operon `docs/JEV_TOOL_SELECTION.md`.
- **Two larger levers remain, both trade-offs, not fixes:**
  - shorter answers, since writing is 1.4 s of a tool turn;
  - a faster model for the call that picks the tool.
