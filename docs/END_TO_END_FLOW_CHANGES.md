# Changes to "Luồng end-to-end mới" (NEWS_EVIDENCE_BRD §11)

The owner's document *Luồng end-to-end mới* is not in this repository. This page lists, for each section the BRD's
§11 names, what the document says, what the app does now, and where to see it. Edit the document from this table.

| Section | The document says | The app does now (2026-10-28) | Where |
|---|---|---|---|
| §5 Tactical tilt | Black–Litterman (P1); the CIO types tilts by hand as a fallback | The CIO picks **Tăng tỷ trọng / Trung lập / Giảm tỷ trọng** for each class; each step is ±2 points. Black–Litterman runs beside it on the same tilts, and the CIO picks which one every client uses. Both stay within ±5 points of the base and inside each class's range. | CIO › Phân bổ (`#/cio/phan-bo`), `POST /api/allocation/method` |
| §5 Goal list | "Chance of reaching the goal before and after rebalancing" | **Required return per year** to reach the retirement goal, next to the return the Growth model expects; the goal is short when the first is higher, with the gap and its year. | Client › Phân bổ tài sản (`#/client/muc-tieu/phan-bo`) |
| §6 Effect of a view | P5–P90 scenarios; Red/Yellow from the 3-month P10 | Each line shows **direction · time · evidence**: "7/12 lần" (statistics), "2 tiền lệ" or "qua pháp lý" (qualitative), or an amount from a contract or rule (certain, N1). The level is the estimated effect as a share of net worth: High from 1 %, Medium from 0.3 %. | Client and RM news lines; CIO › Bằng chứng tin (`#/cio/bang-chung`) |
| §6 Real estate | Certain part split from the historical band | Unchanged; the historical band follows the precedent rule of §6. | — |
| §4 Agents | 4 analyst groups, a challenger | Added: the **event-type catalogue** (the CIO adds types and precedent dates; statistics on VN-Index, SJC gold, USD/VND and the 10-year yield), **client labels** (§7), the **qualitative frame** and the **§9 checks** (Agent Bằng chứng tin), and **Gợi ý nhãn mục tiêu** (AI suggests a goal's purpose and country; the RM saves it). | CIO › Bằng chứng tin; RM › Tác động tin; [AGENT_CHECKLIST.md](AGENT_CHECKLIST.md) |
| §7 Who approves an allocation action | The CIO | The CIO approves or rejects **each action** of an allocation the RM sends; the client sees only the approved ones. An RM may move a holding to another bucket with a reason; the CIO sees every move. | CIO › Phân bổ; RM › Phân bổ tài sản |
