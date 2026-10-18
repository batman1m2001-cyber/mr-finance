# Expert screens (`#/specialist/…`)

The Expert is the `specialist` role (“Chuyên gia”, BRD-RULE-ROLE-05): a certified specialist assigned to a family
approves the action recommendations an RM approved for it before they reach the client (BRD-RULE-WF-08, G8). The demo
specialists are `sp_global`, `sp_real_estate`, `sp_insurance`, `sp_banking`, `sp_private`; whose certificate is in
force is Compliance's configuration “Chứng nhận chuyên gia”.

## SCR-SP-01 — Duyệt khuyến nghị (specialist queue)

| | |
|---|---|
| Route | `#/specialist/duyet` (a sheet over the desk since FEAT-41) |
| Generation | new (G8, `web/pages/specialist.js`) |
| Feature | [FEAT-27](../../features/FEAT-27-rm-approval-queue.md) |
| Requirements | BRD-RULE-ROLE-05, BRD-RULE-WF-08 |
| Data | `GET /api/review` (the queue, the approvers per family, the certificate); `POST /api/review/specialist` |

The certificate (or “Chưa có chứng chỉ còn hiệu lực”), then **Chờ bạn duyệt** — one card per recommendation waiting
for this specialist: the family, kind, time, title, actions and the RM's note, a note field, Duyệt and Từ chối (a
rejection needs a reason of 10 characters or more) — and **Bạn đã xử lý**. Documented 2026-10-18; unchanged by FEAT-41.

## SCR-SP-02 — Bàn chuyên gia (Expert desk)

| | |
|---|---|
| Route | `#/specialist`, `#/specialist/ban`; every other Expert address opens its page as a sheet over the desk |
| Feature | [FEAT-41](../../features/FEAT-41-role-desks.md) (and the page it gathers: FEAT-27) |
| Requirements | OWN-MR-01, OWN-MR-05, OWN-MR-06, OWN-MR-07, OWN-MR-10; BRD-RULE-ROLE-05, BRD-RULE-WF-08; Q-26 |
| Data | `GET /api/desk` (Duyệt khuyến nghị's filter over the queue, the certificate, the families); the picture: `POST /api/dashboard`, `POST /api/goals` (family scope); the decision: `POST /api/review/specialist` |
| Screenshots | [desktop](../../assets/current_ui/SCR-SP-02_desktop-light.jpg) · [a family picked, dark](../../assets/current_ui/SCR-SP-02-family_desktop-dark.jpg) · [phone, dark](../../assets/current_ui/SCR-SP-02_phone-dark.jpg) |

**Centre.** Header “Chuyên gia · Bàn chuyên gia” with “<n> khuyến nghị chờ bạn · <f> gia đình được giao · <d> đã xử
lý gần đây” and the certificate as a pill (green with its name and end date, red without one). The bench: on the left
**Chờ bạn duyệt** (oldest first: title, client, RM, how long it has waited) over **Gia đình được giao** (each with how
many wait); on the right the evidence — the picked recommendation (the oldest on arrival) with its actions and the
RM's note, then **Bức tranh của gia đình** (net worth, risk profile, risk against the limit, liquidity in months and
years, allocation bars, goals with their status), then the decision bar (note, Duyệt, Từ chối), which stays in view.
Below: **Bạn đã xử lý**. A phone stacks the queue, the families and the evidence.

**Thông tin (a pick).** The recommendation's id, client, RM and time with the rule (“Từ chối cần lý do từ 10 ký tự;
máy chủ kiểm tra lại chứng chỉ và việc phân công”), or the family and whether this specialist may decide for it.
