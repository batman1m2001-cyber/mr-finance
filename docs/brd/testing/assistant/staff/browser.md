# The staff assistant stress test — browser pass (U3)

This pass covers what HTTP cannot check, in the real panel docked on each staff desk:
- the assistant answering;
- the desk lighting what each step reads (`web/desk/desk.js`: a step's nodes take `act`, the answer keeps `lit`);
- the panel's state;
- a write's Xác nhận button;
- phone width;
- the fallback on a dead provider.

The script is `scripts/stress_staff_browser.py` (Playwright, the real model, on :8041; with `--fail`, on :8042). The
records are [record.json](browser/record.json) and [record_fail.json](browser/record_fail.json), and the screenshots
are in `browser/`.

| Desk | Desktop: lit while it read | Phone (390 px, its own conversation): lit | Sideways scroll | Page errors | Provider down (:8042): lit, answer |
|---|---|---|---|---|---|
| RM, Sổ khách hàng | book, calls, proposals, tasks | book, calls, proposals | none | none | book, calls, proposals; the book's own text |
| CIO, Bàn quyết định | decide, stage:views, stage:runs | the same | none | none | the same; the two decisions waiting |
| Expert, Bàn chuyên gia | queue | queue | none | none | queue; the queue, oldest first |
| Compliance, Bàn kiểm soát | controls, queue | controls, queue | none | none | controls, queue; six items with dates |
| Admin, Vận hành | ops, alerts, jobs | ops, alerts, jobs | none | none | ops, alerts, jobs; the two alerts |

**The RM's write (desktop).** “Nhớ giúp tôi: tôi chỉ gọi khách vào buổi sáng, trước 11 giờ”:
- the Xác nhận button appeared;
- the memory held **0** new items before the click and **1** after it;
- the answer said where to see or change it.

Screenshot: `browser/rm_confirm_desktop.jpg`.

**Provider down.** Each role's question was answered from its own desk read (D12, D13), not from another role's
tool. The panel shows the “dự phòng: từ khóa” badge and the fallback line under the input
(`browser/cio_fail.jpg`).

**What the pass found:**
- D18 (S2): asked again on the phone, Admin's assistant said it had “just checked again” with no tool called.
- D21 (S4): Compliance's desk lit nothing for held news or configuration.
- D22 (S4): an empty box under the RM's answer.
- A fault in the test itself: the first two runs recorded the panel's `mf:focus` marks, which desks do not use, so
  they showed “nothing lit”. The record above is the third run, with the desk's own `data-node` marks.
- The phone pass first reused the person's restored conversation, so a repeat was answered from memory. It now
  starts its own conversation, and the repeat became its own catalogue case (adm-rep-01).

Cost of the three passes: US$0.0175, US$0.0164 and US$0.0193 (12 turns each, read from each answer frame's usage).
The dead-provider pass cost US$0.
