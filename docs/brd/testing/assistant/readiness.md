# The assistant stress test — readiness

The owner asked (2026-10-17) for the assistant to be tested as real customers would use it, end to end, and for an
honest assessment, not a declaration that it is ready because the interface works. This page is that assessment for
the assistant on `exp/graph-workspace` (2026-10-18). The evidence is in [results.md](results.md),
[defects.md](defects.md), [coverage.md](coverage.md), [browser.md](browser.md) and `runs/`.

## Verdict

**Not production-ready yet. It is ready for a supervised pilot on this branch once the privacy fix (D13) is on the
branch that serves customers.**

- **One S1 defect was found and fixed here, but the live demo still has it.** A signed-in customer who named
  another family's id got that family's net worth, debts and holdings (D13). It is fixed on `exp/graph-workspace`.
  `main`, which serves the public demo, has the same code (a read-only check of `origin/main`). Until the fix is
  ported, the live assistant can show one family's data to another. Porting it is the owner's decision.
- **Behaviour.** On the final code, 80 of the 81 conversations (166 turns) behaved correctly when read by hand. The
  machine checks passed 76; the other four are grader faults, each recomputed (review.json). The one real failure is
  an open S3 (D29).
- **Requirements.** 49 BRD requirements were exercised. 46 held, and the 3 that did not all fail on that same
  conversation.
- **Speed.** A turn takes a median of 4.0 s (p90 8.8 s); the first visible event comes after a median of 1.6 s.
- **Cost.** About US$0.003 a turn: US$0.50 over the 161 counted turns of the final run.

## What was tested

- **The catalogue.** 81 multi-turn conversations, written as real customers and their concerns, across 13
  categories:
  - navigation, personal finances, financial knowledge, news, goals, what-if and personal concerns;
  - actions (each write confirmed or declined, then read back from the app);
  - memory and sessions, including a 21-turn conversation that compacts;
  - ambiguous requests, out-of-scope requests, adversarial requests (prompt injection, another family's data, a
    claimed role, secrets);
  - failure modes: a dead model provider, web search used up, a month with no data.
- **How it ran.**
  - Every turn went through the real stream endpoint, signed in as the person.
  - The conversations ran on a served copy of the experiment's state (:8041). The failure modes ran on a second copy
    whose model provider is unreachable (:8042).
  - The real model was used: `anthropic/claude-haiku-5.5` via OpenRouter.
  - The real panel was driven in a browser on desktop and phone (browser.md).
- **Review.** Every failed turn was read by hand, and every figure in question was recomputed.

## Runs

| Run | What it was | Conversations passing the machine checks |
|---|---|---|
| T1 | The first full run | 64 of 74 (found D01–D21) |
| T2 | After fixing D01–D21 | 62 of 77, and 2 of 3 failure modes (found D22–D27, and D19 again) |
| final | After fixing D22–D28 (the final code, plus D30 and D32 checked by targeted reruns) | 76 of 81 by the machine checks; 80 of 81 by hand |

## Defects

32 defects were found (defects.md):

| Severity | Fixed | Open |
|---|---|---|
| S1 | 1 | 0 |
| S2 | 10 | 0 |
| S3 | 13 | 2 |
| S4 | 4 | 2 |

The defects found most often share one cause. The tool told the model only a headline, while the page and its card
held the rest:
- only the largest spending group (D25);
- only the largest of 18 policy factors (D27);
- only goal statuses (D10);
- only a combined class split (D32);
- whole-percent shares (D08).

The model then improvised: it refused, multiplied shares back into amounts, or told a customer that no real-estate
policy applied when three did. Each case is fixed, and each has a test that fails without its fix.

## What still blocks or limits

1. **D13 on `main`.** This is the only blocker, and it is the owner's decision.
2. **D29, open S3.** The guide search is lexical and returns the top three passages. For some wordings it misses the
   passage that answers, and the assistant then says the guide does not cover it. It is intermittent: one run in
   three. The remedy is hybrid search (embeddings: a cost decision) or a larger result set, measured first.
3. **D31, open S4.** In a long conversation, “Nút này nói gì vậy?” once began with “which button?”, although the
   same answer named the picked item. It happened once in two browser passes.
4. **D18 (data) and D05 (rounding).** C04's demo data contradicts itself. Amounts round half down, the same as the
   pages, so they are left unchanged to stay consistent.
5. **Web answers without sources (D23).** The provider sometimes returns no citations. Such answers are now
   labelled unverified, but they still carry no sources.

## What this test did not cover

- **Load and concurrency.** Conversations ran one after another, with one person at a time.
- **Other models.** Only the configured model was tested; template mode (no model reading client data) was not run
  live.
- **Roles.** Staff roles appear only in the adversarial and failure-mode conversations (rm01 and rm02). There was no
  full RM, CIO or compliance journey.
- **Data.** Only the demo personas (C01–C05) were used: no real bank data, and Vietnamese only.
- **Accessibility.** No audit of the panel beyond the existing UI tests.
- **The graders.** The machine checks cannot see a tool's `data`, so figures read from it were checked by hand (G2).

## Spend

The paid model calls of this test cost **US$1.97**, as counted by the harness, against the owner's cap of US$3:

| Item | Cost (US$) |
|---|---|
| Smoke run and T1 | 0.507 |
| T2 | 0.432 |
| The first final run (before D28–D32) | 0.463 |
| Targeted reruns: nav-01, fm-06, wi-02 and fm-05 | 0.063 |
| The final run | 0.504 |
| Probes | 0.001 |

The two browser passes are not in that count. They used a handful of short turns, estimated at under US$0.02.
