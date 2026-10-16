# FEAT-17 — CIO newsletter

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-FR-801, BRD-RULE-CONTENT-01 (flow 1), BRD-RULE-CONTENT-02 (labels), BRD-RULE-CONTENT-03 (conflict of interest), BRD-RULE-SEC-04 (approver ≠ author) |
| Users | CIO (author), Compliance (approver) |
| Entry points | [SCR-CIO-14](../ux/screens/cio.md) and [SCR-CMP-04](../ux/screens/compliance.md) “Bản tin”; `GET /api/newsletters[/{id}]`, `POST /api/newsletters`, `POST /api/newsletters/act` |
| Screenshots | [a draft, CIO](../assets/current_ui/FEAT-17-draft_desktop-light.jpg) · [approved, Compliance](../assets/current_ui/SCR-CMP-04_desktop-light.jpg) |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
A general market letter to every client, made only from views the CIO has approved, read by Compliance before it
could go, and labelled the way client content must be. The demo shows the preview; nothing is sent.

## Drafting (`src/newsletter/compose.py`, `store.draft`)
- The CIO picks 1–6 **approved** views (a view in any other state is refused, 409).
- Each view becomes a section: the event's headline as the heading, the date the CIO approved it, its impacts by
  asset class, sector and FX in words (“Bất động sản: tăng nhẹ trong 3 tháng”), its scenarios with probabilities and
  their main factor moves, the outlets behind it. **Ticker rows are counted, not named** (“và 1 tác động tới cổ
  phiếu cụ thể”): a letter to every client names no stock.
- The opening paragraph: **template** (lists the sections), or **agent** — the CIO agent's model (`llm:cio`) writes
  2–3 sentences from the sections only. In mock mode the template is used and says so; in inbox mode (no model at the
  bank) or on a model error, the template is used with the reason kept (`agent_findings`); if what the model wrote
  fails the guard, the template is used and the finding kept.
- Distribution: `send_at` (default tomorrow 08:00). Private and retail at the same time by default; Private earlier
  by 0–72 hours only with a reason of at least 20 characters, shown highlighted to Compliance (FR-801).
- Conflict of interest: `{related, parties, statement}` like research ([FEAT-03](FEAT-03-research-and-regulation-notes.md)).
  A party on Compliance's `related_parties` list named in the letter must be declared, unless research the letter
  quotes already discloses it.

## The guard (`compose.guard`, every version)
No recommendation wording (Compliance's `forbidden_phrases`), no ticker of the catalogue, no name on the restricted
list, and the labels CONTENT-02 requires: AI involvement, the responsible person, the time, “không phải khuyến nghị
đầu tư”, the RM and complaints path, the conflict-of-interest disclosure (“Không có xung đột lợi ích cần công bố.”
when none). A letter that fails cannot be submitted or approved; the CIO fixes it by editing the title, the opening
or a section's heading (a headline can carry banned words, e.g. “bắt đáy”).

## Workflow (`store.act`)
DRAFT → (edit) → submit → PENDING_COMPLIANCE → approve → APPROVED, or return (a note of at least 10 characters) →
RETURNED → edit → submit …; the CIO may withdraw at any point. Only a CIO edits, submits and withdraws; only
Compliance approves or returns, and **never the letter's author** (SEC-04, refused even for someone holding both
roles). Approval records `preview_only`; `sent` stays false. Every step is an audit row (`newsletter.draft`,
`.edit`, `.submit`, `.approve`, `.return`, `.withdraw`).

## Tests
`tests/test_newsletter.py`.
