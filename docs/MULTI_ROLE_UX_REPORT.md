# OneWealth — Multi-role UX: final report (M6)

2026-10-18. The owner's request is
[2026-10-18_multi_role_ux.md](brd/sources/owner_requests/2026-10-18_multi_role_ux.md) (OWN-MR-01…12); the plan is
[MULTI_ROLE_UX_PLAN.md](MULTI_ROLE_UX_PLAN.md). The request: give every staff role a purpose-built workspace in the
Customer workspace's frame, without losing any function, and give each role its own assistant. Built on branch
`ux/multi-role` (commits 544d894 → M6) and merged into the experiment `exp/graph-workspace`, which serves the demo
on :8040.

Status words follow the traceability matrix: **verified** (a test in the suite checks it), **unverified** (built,
checked by hand or screenshot, no suite test), **partial** (some of it is built).

## 1. What was built

Each staff role now opens on its desk. The desk has the same frame as the Customer workspace: the rail of the role's
page groups on the left, the role's own centre, and the dock (Trợ lý · Thông tin) on the right. Every page the role
had before opens as a sheet over the desk, at its old address, with its group's tabs.

| Role | Desk (address) | Centre | Its assistant's new tools | Screen |
|---|---|---|---|---|
| CIO | Bàn quyết định (`#/cio`) | The flow from news to families (six stages with counts), what waits for the CIO, exposure by factor, events, the model, the agents | `ban_quyet_dinh`, `phoi_nhiem`, `lan_ap_dung`, `do_chinh_xac` | SCR-CIO-15 |
| RM | Sổ khách hàng (`#/rm`) | The RM's families as a relationship map, nearer when they need the RM sooner, sized by net worth; calls, goal tasks, proposals, contacts | `so_khach_hang` | SCR-RM-07 |
| Admin | Vận hành (`#/admin`) | The system as a map — sources → storage → AI → people — each node green, amber or red from its last record; alerts, failing jobs, configuration waiting, people and roles, the chain | `van_hanh`, `chuoi_nhat_ky`, `cau_hinh_cho_duyet` | SCR-ADM-02 |
| Expert (`specialist`) | Bàn chuyên gia (`#/specialist`) | The queue beside the evidence: the recommendation's actions and the RM's note next to the family's net worth, risk, liquidity, allocation and goals; the certificate; approve or reject | `ban_chuyen_gia`, `ho_so_khach` | SCR-SP-02 |
| Compliance | Bàn kiểm soát (`#/compliance`) | Every control as a lane with what waits at each step — held news, research, letters, policy documents, configuration, the audit chain — and one queue, oldest first | `ban_kiem_soat` (and `chuoi_nhat_ky`, `cau_hinh_cho_duyet`) | SCR-CMP-06 |

Every desk reads one server read, `GET /api/desk`, built from the same stores and compositions the role's pages use.
The desk never computes a figure of its own. The assistant's desk tools call the same read, so the assistant says the
numbers the screen shows; while it works, each step lights the part of the desk it is reading.

## 2. What was kept

- **Every page, at its address.** CIO 13, RM 13, Admin 6, Expert 2, Compliance 9. Each opens as a sheet with no
  error, in the browser tests, and each menu is checked page for page against the menu before the desks.
- **Every write, unchanged.** Decisions stay on their pages, with their rules: approvals, releases with a reason, the
  second person, the release time. The Expert's desk decides through the existing `POST /api/review/specialist`; no
  new write and no new permission were added.
- **Access.** The desk is the session's role's alone: a client gets 403, and the query cannot change the role. An RM
  sees only their own families, and a specialist only the families assigned to them. Every new tool is offered to its
  roles only. The access matrix test (`tests/test_access.py`) runs every read as every person.
- **The agents beneath.** Agent CIO and its challenger, the policy agent and the letter agent are untouched; the
  agent map counts the new tools.
- **The Customer.** The Customer's workspace browser tests passed in every phase.

## 3. Tests

| Run | Non-UI | Browser (UI) |
|---|---|---|
| M3 (3277f33) | 835 passed, 1 skipped | 104 passed |
| M4 (2bfb7ac) | 855 passed, 1 skipped | 107 passed, 1 failed → fixed, rerun green (see §5) |
| M5 (9dbcdc5) | 867 passed, 1 skipped | 111 passed |
| M6 (close-out) | 878 passed, 1 skipped | 111 passed |

The multi-role tests themselves are `tests/test_role_desks.py` (51 cases) and `tests/ui/test_role_desks_ui.py` (18).
For each role they cover four things:

1. **Preservation.** The menu is kept page for page; every page sits in exactly one rail group; every old address
   opens as a sheet.
2. **Isolation.** The desk is the role's alone; another role's desk address never shows it; an RM's book and a
   specialist's desk hold their families only.
3. **Figure equality.** The desk's numbers equal the existing pages' reads.
4. **The assistant.** The tools say the desk's numbers, they run signed in inside a served turn, and each step
   lights the desk.

Screenshots of every desk, desktop and phone, light and dark, are in `docs/brd/assets/current_ui/` and the screen
documents.

## 4. Each role's assistant on a real model

Seven turns on the copy server, with the live router (`anthropic/claude-haiku-5.5`), one or two per role:

| Role | Question | Tools it called (desk parts lit) | Answer | Cost |
|---|---|---|---|---|
| CIO | Có gì chờ tôi duyệt? | `ban_quyet_dinh` (decide, stages) | One view waiting (VW-0003-v1), the flow's counts | US$0.00142 |
| RM | Sổ khách hàng có gì cần làm? | `so_khach_hang` (book, calls, proposals) | **First run refused** (§5); after the fix: 3 families, nothing urgent | US$0.00183 + US$0.00184 |
| Admin | Hệ thống có gì bất thường? | `van_hanh`, `canh_bao_he_thong` (map, alerts) | Nothing failing; zone and availability not yet run | US$0.00123 |
| Expert | Khuyến nghị nào đang chờ tôi duyệt? | `ban_chuyen_gia`, `de_xuat` (queue) | Two recommendations, with ids, families and RM | US$0.00127 |
| Expert | Hồ sơ của gia đình C04 thế nào? | `ho_so_khach` (evidence) | Net worth 48,38 tỷ, allocation, real estate 60,4 % over the 35 % limit, risk | US$0.00142 |
| Compliance | Có gì chờ Tuân thủ? | `ban_kiem_soat` (controls, queue) | Three items, oldest first, by control; nothing held; chain intact | US$0.00129 |

Total **US$0.0103** for 14 model requests. These live turns are not part of the suite; the suite runs the same tools
with fake models.

## 5. Defects found and fixed on the way

| Found by | Defect | Fix |
|---|---|---|
| The real-model RM turn | `so_khach_hang` was refused inside a signed-in turn. The book read mapped every client's family through the checked read, which refuses a family the RM may not see. Tests without sign-in did not catch it. | The map now comes from the people table (it is never shown). Every desk tool is now tested signed in inside a served turn (`test_a_desk_tool_works_signed_in_inside_a_served_turn`, 11 cases); before the fix, exactly this one failed |
| The M4 browser run | Under `#/specialist/duyet`, a click could land on the desk's own decision bar behind the sheet | The desk's centre is now inert (no focus, no click) while a sheet is open, on every desk |
| M1–M3 runs | Badges unstyled on desks; a phone sheet widened by a row of tabs; motion-rule violations on the lit ring | Scoped styles; a one-column grid; an opacity-only ring (rule B-01) |

## 6. Gaps and open questions

| # | What | Status | Who decides |
|---|---|---|---|
| Q-24 | The request names CIO, RM, Admin and Expert. We read Expert as `specialist` and gave Compliance a desk too. | Answered by the owner (2026-10-18): as read | — |
| Q-25 | Admin's "users and roles": the product has no account or password form, on purpose. The desk shows people by role and accounts without a password, and links the RM assignment (a two-person configuration). OWN-MR-04 stays **partial**. | Open | Owner |
| Q-26 | What a specialist sees of a family. Only what they could already read for an assigned family (overview, goals), through the existing reads. | Applied, our reading | Compliance |
| — | The floating assistant panel was shown on no role's home: every role's assistant is docked. | Removed on the owner's word (2026-10-18): the button, its open/close and its styles | — |
| — | `#/rm` used to open Hôm nay; it now opens the book, and Hôm nay is `#/rm/hom-nay`. Old bookmarks to `#/rm` land on the book. | By design | — |
| — | With sign-in off (a developer's machine), the Expert desk reads as the role's demo user (`?user=`), as Duyệt khuyến nghị does. With sign-in on, the session decides. | By design | — |

## 7. Next steps

1. The owner answers Q-25 (an account form, or "shown, not edited" stands) and confirms Q-24 and Q-26.
2. Decide the floating panel's fate.
3. Optionally, a small real-model eval of the desk tools in `scripts/eval_assistant.py`, so the live turns in §4 can
   be rerun on demand.
4. Taking the experiment to `main` stays the owner's call (ADR-0035).
