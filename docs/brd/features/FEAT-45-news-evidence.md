# FEAT-45 — News as evidence, not forecast

| | |
|---|---|
| Type | Extension (owner BRD, 2026-10-28) |
| Requirements | OWN-NE-01…12 ([owner_requirements](../requirements/owner_requirements.md#ne--news-as-evidence-not-forecast-2026-10-28)); the BRD verbatim: [`docs/NEWS_EVIDENCE_BRD.md`](../../NEWS_EVIDENCE_BRD.md) |
| Users | the client and the RM (read approved frames), the CIO (reviews every frame and the agent's drafts) |
| Entry points | the frame panel from the impact chart, the cards and the feed (FEAT-25); [SCR-CIO-16](../ux/screens/cio.md#scr-cio-16--bằng-chứng-tin-news-evidence) `#/cio/bang-chung`; `POST /api/evidence` (+ `/decide`, `/draft`, `/draft/decide`) |
| Plan | the BRD's §15: P0 and P1 built; P2 not built |
| Status | built (2026-10-28) |

## Purpose

Say what a news item may do to a client's assets as **direction · time · evidence**, never as a forecast figure:
statistics when history gives enough cases, otherwise a qualitative frame a CIO has approved.

## Behaviour

1. **Frame.** Each news item has a frame (`data/evidence.json`): its event type from a fixed catalogue, channels,
   mechanism, targets (asset, loan, plan labels), direction, what changes, timeframe, what to watch, precedents
   (event, outcome, difference, source).
2. **Statistics.** With at least 8 dated events of its type and the market's history, the share of moves in the same
   direction against the base rate (`evidence/_stats.py`); 10 points over it calls a direction. The sentence says n
   and the base rate. Fewer cases: qualitative. With statistics the computed direction wins over the agent's.
3. **Checks.** A frame is checked (§9): catalogue values, required fields, no forecast figure, no FR-604 words; it
   goes back to the agent with the reasons, at most twice.
4. **Matching.** Rules match a frame's targets to the labels a client has; a plan label read from a goal's name is
   *inferred* and reaches the client only after the RM confirms the goal (Example 4).
5. **Who sees what.** The client and the RM read approved frames; the CIO also sees the review, the unsourced
   precedents (never shown as “Nguồn”) and the thresholds.
6. **Review.** The CIO approves, returns or rejects; a returned frame leaves the chart until approved; each decision
   is in the audit log.
7. **The agent (P1).** On Bằng chứng tin the CIO hands a high-relevance news item to the agent. It reads only the
   item (title, summary, outlet, date), picks the event type and drafts the frame — mock by keywords from the seed
   frame of that type, or live on the CIO's model; a new type goes qualitative with direction Chưa rõ. The draft
   waits for the CIO; a draft that failed the checks cannot be approved.

## Not built (P2)

The full catalogue of event types; the agent suggesting plan labels; the *Luồng end-to-end mới* document updated per
the BRD's §11. Open: [Q-30](../requirements/open_questions.md#q-30--the-news-evidence-thresholds-and-who-sees-what).

## Tests

`tests/test_evidence.py` (every OWN-NE row cites its test in the traceability matrix).
