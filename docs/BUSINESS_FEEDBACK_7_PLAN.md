# Business feedback 7 — the RM's screens (2026-10-25) — plan

**Status: done 2026-10-25** — G1–G4 merged into `main`, live on :8030; gate `tests/ui/test_feedback7_ui.py` (4) and the related desk, assistant and BRD-page files pass.

The owner's seven notes on the RM's desk, Khách hàng sheet and Advisory performance
([source](brd/sources/owner_requests/2026-10-25_business_feedback_7.md), BRD `OWN-FB-19…25`). Branch
`ux/feedback-7`, merged into `main` when the gate passes, then live on :8030.

## G1 · The desk is Tổng quan (notes 1, 2, 7)

- Rail, desk title, heading, hint, back link: **Tổng quan** (was Sổ khách hàng / Sổ khách). The assistant's first
  suggestion: "Tổng quan có gì cần làm?".
- The list: **Khách hàng đang quản lý** (was Gia đình của bạn); the subtitle counts khách hàng; the empty states say
  khách hàng.
- The net-worth column in the accent colour, bold. It is a net worth, not a change: no "+".

## G2 · No Hôm nay (note 3)

- The rail item and the page go (`web/pages/today.js`); `#/rm/hom-nay` → `#/rm`.
- The contact log moves to the desk's Thông tin pane: a client's card and Liên hệ gần đây's "Ghi liên hệ →" open the
  form (client, channel, the signal it answers, note), posting `/api/rm/contacts` as before; the desk reloads.
  "Cần gọi trước" and "Việc theo mục tiêu" lose their "Hôm nay →" links. `/api/rm/today` stays (the form's channels
  and signals, the assistant's `hom_nay` tool), its answer opens the desk.

## G3 · The client picker in the sheet (notes 4, 6)

- On the RM's Khách hàng and Advisory performance sheets the client picker (and Cá nhân / Gia đình) sits in the sheet,
  on the line of the inner tabs, labelled "Khách hàng"; the top bar no longer has it on those sheets. It goes back to
  the top bar when the desk closes (the Customer and other pages).
- "Tất cả khách hàng" is every client: no picker there (`noPick` on the menu entry).
- On a phone the picker takes its own line.

## G4 · No Nội bộ line on the RM's sheets (note 5)

- `internal()` leaves detail, holdings, plan, policy, graph (the RM's), impact, advisor, performance and perfall.
  The CIO's graph and the Cách tính drawer keep it. BRD-RULE-SEC-03 amended: the stamp stays on the trace drawer and
  the CIO's pages; the RM's sheets are staff-only by role (BRD-RULE-SEC-02), the line was noise there.

## Gate

The related tests (role desks, BRD pages, header, feedback 6 UI, assistant, staff stress), screenshots of the RM's
desk, Khách hàng and Advisory performance on a desktop and a phone, live on :8030.
