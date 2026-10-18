# The staff assistant stress test — readiness

The owner asked (2026-10-18) for each staff role's assistant to be tested as its users would use it, the way the
customer's was. This page is the assessment for the five staff roles (RM, CIO, Expert, Compliance, Admin) on
`exp/graph-workspace`. The evidence is in [results.md](results.md), [defects.md](defects.md),
[coverage.md](coverage.md), [browser.md](browser.md) and `runs/`.

## Verdict

**Ready for a supervised pilot with staff, on this branch.**

- **No S1 was found.** No family's data reached the wrong person, and no decision was made by the wrong person or
  without its second person. This held in every one of these probes:
  - another RM's family, asked for by name or by a hand-edited request;
  - a family not assigned to the Expert, or an Expert without a certificate;
  - client data asked for by the CIO, Compliance or Admin;
  - an RM deciding as the Expert;
  - the proposer approving their own change;
  - a rejection without a reason;
  - injections in a message, in a fake “[HỆ THỐNG]” line and in held news.

  Every write waited for the person's click, and was read back from the database.
- **Fourteen S2 defects were found and fixed** (defects.md). The most serious kind was the assistant not knowing
  who decides what (D03). It told an RM the CIO approves the Expert's work, and told Admin they could approve the
  CIO's configuration. Each role now has its duties in the prompt and its desk in the guide.
- **Behaviour.** On the final code, all 54 conversations (82 turns) behaved correctly when read by hand. The
  machine checks passed 53; the other one is a grader fault (G7), checked against the copy's database.
  - Three of the 54 were rerun after a wording fix (D23–D25, `final-s3`).
  - Those fixes added three sentences to the staff prompt *after* the full final run. The other 51 conversations
    ran on the prompt without them.
- **Requirements.** 34 BRD and owner requirements were exercised, and all 34 held.
- **Speed.** A turn takes a median of 3.0 s (p90 4.6 s). The first visible event comes after a median of 1.1 s.
- **Cost.** US$0.1548 for the final run (82 turns, 5 of them on a dead provider at no cost): about US$0.002 a
  turn. One web search (the Fed's December meeting) was US$0.048 of it.

## What was tested

- **The catalogue:** 54 multi-turn conversations, written as the staff who would have them, across 11 categories:
  - desk;
  - navigation and procedure;
  - actions;
  - limits;
  - permissions and isolation;
  - separation of duties;
  - memory and sessions;
  - ambiguous and repeated questions;
  - out of scope;
  - adversarial;
  - failure modes.

  [catalogue.md](catalogue.md) lists them. The work each desk shows was seeded through the app's own writes
  (`scripts/stress_staff_seed.py`).
- **Through the real server**, on its own copy (:8041), with the real model. Every claimed write was read back from
  the copy's database.
- **Each role's desk in a browser**, desktop and phone, and the fallback on a dead provider (browser.md).

## What remains

- **D06 (S3, open):** a garbled formula line, seen once in U1. It was not reproduced since.
- **Wording is not fully fixed:**
  - after a cancel, the assistant sometimes asks what to do next (D05);
  - for a family it may not read, the CIO's assistant may say “không tìm thấy” before giving the right reason.

  Neither misleads.
- **The model is not deterministic.** One run of each conversation is evidence, not proof. The Expert's approval
  (D09) failed both runs before its fix and passed all three runs after it.
- **Owner's decisions, not defects:**
  - whether a customer's own proposal, once the RM approves it, should go on to the specialist (the observation in
    defects.md);
  - the confirm-gated agent controls and the jobs view: built after this test (owner, 2026-10-18;
    docs/OWNER_BACKLOG_1018_PLAN.md A). cio-lim-02 now expects the Xác nhận, and adm-act-02 runs a job.

## Spend

US$3 cap. **US$0.4858 spent in all**, from each answer frame's own usage (model and tools):

| Run | US$ |
|---|---|
| U0 smoke | 0.0166 |
| U1 full run | 0.1554 |
| U2 reruns | 0.0924 |
| U3 browser passes and adm-rep-01 | 0.0562 |
| Final run | 0.1548 |
| `final-s3` | 0.0104 |
| All dead-provider runs | 0 |
