# FEAT-41 — Role desks (every staff role's own workspace)

| | |
|---|---|
| Type | Extension (owner request, 2026-10-18), **experiment**: branch `exp/graph-workspace` |
| Requirements | OWN-MR-01…12; keeps every requirement the staff screens carry today (the map in [ux/role_desks.md](../ux/role_desks.md)) |
| Users | CIO, RM, Admin, Expert (`specialist`), Compliance. The Customer keeps FEAT-40 |
| Entry points | `#/<role>` and `#/<role>/ban` (the desk); every older staff address opens its page as a sheet over the desk; `GET /api/desk` |
| Plan | [docs/MULTI_ROLE_UX_PLAN.md](../../MULTI_ROLE_UX_PLAN.md) M0–M6; decision [ADR-0036](../decisions/ADR-0036-every-staff-role-works-at-its-own-desk.md) |
| Status | see [traceability](../requirements/requirements_traceability.md) §5 |

## Purpose

Each staff role starts its day on one screen built for its job — what waits for it, where the work stands, what to
do next — instead of a row of tabs; every page it had stays, one click away, unchanged; and its own assistant sits
beside it, reading the same numbers the screen shows.

## Preconditions and permissions

Signed in as a staff role. The desk reads only `GET /api/desk`, which takes the role from the session (sign-in on;
`?role=` only when sign-in is off) and returns that role's desk alone; a client gets 403. The desk is built from the
stores the existing reads use, with their filters (`people.auth.may_see` for families). Nothing on a desk writes
except through an existing, already-checked write.

## Behaviour

1. **The frame** (shared with the Customer's workspace, FEAT-40): the rail on the left (the role's groups of pages,
   with tooltips), the centre, the dock on the right (Trợ lý · Thông tin, divider and fold as FEAT-40), sheets over
   the centre. A phone stacks them: rail on top, centre, dock.
2. **Addresses:** `#/<role>` and `#/<role>/ban` show the desk; every menu address of `web/shell.js` is unchanged and
   opens its page module, unchanged, as a sheet; the sheet's header shows the group's pages as tabs and closes back
   to the desk (✕, ← or Escape).
3. **The centre** is the role's own (§ Desks below). A pick fills Thông tin with the item and its links.
4. **The assistant** docks in Trợ lý, streams, shows the progress list, and lights on the centre what each step reads.

## Desks

Filled in as each phase is built (plan §3): CIO (M1), RM (M2), Admin (M3), Expert (M4), Compliance (M5).

### CIO — Bàn quyết định (SCR-CIO-15, built in M1, 2026-10-18)

- **Rail:** Bàn quyết định · Tin & sự kiện (Hộp tin, Sự kiện & nhận định) · Tác động (Lần áp dụng, Phơi nhiễm, Đồ
  thị) · Nội dung (Nghiên cứu, Bản tin, Chính sách) · Mô hình (Tham số, Dữ liệu thị trường, Độ chính xác, Đo lường) ·
  AI & cấu hình (Agent, Cấu hình) · Bộ nhớ at the foot. All 13 pages of the old menu, at their old addresses.
- **The flow** from news to families, six stages, each with its count, what waits (a badge) and a note: Tin (new
  inbox items; high relevance waits) → Sự kiện (events; those with no view or held wait) → Nhận định (view versions;
  `PENDING_APPROVAL` waits) → Lần áp dụng (effective runs; `NEEDS_CIO_REVIEW` and computing wait) → Gia đình
  (families in effective runs; those at the RM pre-review threshold flagged) → RM (families on the RM's Hôm nay).
  A stage picked lists its items in Thông tin, each opening its page, and a button opens the stage's page.
- **Cần bạn quyết định:** views awaiting approval, runs held for review, CIO-owned configuration pending (“Chờ một
  CIO khác duyệt” when this CIO proposed a two-person kind), newsletters Compliance returned, events with no view —
  newest first, each opening its page as a sheet (the approval controls are the page's, unchanged).
- **Phơi nhiễm:** the newest effective run's expected 3-month change over every family (with “Cách tính”), the six
  largest factor totals as bars, the three worst families with the pre-review badge.
- **Sự kiện gần đây**, **Mô hình và dữ liệu** (factors with real data, failing data jobs, approved views' forecasts
  waiting to be scored and the next due date), **Agent dưới bàn** (Agent CIO's mode, models, prompt version, today's
  tokens — FEAT-04, 05 run from their pages as before).
- **Assistant:** the CIO's own (intro and suggestions for the CIO); four read tools over the same composition —
  `ban_quyet_dinh`, `phoi_nhiem`, `lan_ap_dung`, `do_chinh_xac` — plus the CIO tools it had (`hop_tin`, `lay_tin`,
  `su_kien`, `danh_dau_khan`, …). A step lights the stage or panel it reads (`data-node`).
- **Unchanged:** every page, write and permission; the Customer's workspace (FEAT-40).

### RM — Sổ khách hàng (SCR-RM-07, built in M2, 2026-10-18)

- **Rail:** Sổ khách hàng · Hôm nay · Khách hàng (the ten pages of the picked client as tabs: Tác động tin, Đồ thị tác
  động, Toàn cảnh, Bản đồ tài chính, Chi tiết, Tài sản, Kế hoạch, Chi phí chính sách, Hiệu quả tư vấn, Duyệt đề xuất) ·
  Hiệu quả tư vấn · Bộ nhớ at the foot. `#/rm` is now the book; Hôm nay is one click away at its address.
- **The book** (a relationship map): the RM in the middle, each assigned family a dot — on the inner ring when it needs
  the RM now (at the pre-review threshold of an effective run, or a goal task “liên hệ ngay”), the middle ring for a
  proposal waiting for the RM or a goal to confirm, the outer ring for a reminder, the edge when nothing waits; sized
  by net worth at the newest effective run (equal when none); a count of reasons on the dot. Only the families the
  RM may see (BRD-RULE-ROLE-02); control-group families carry no signal (BRD-RULE-MEAS-06), as on Hôm nay.
- **A family picked** → Thông tin: segment, age, occupation, city; its level and each reason; net worth (with the run
  it is from), proposals waiting, last contact; the news that moved it (each effective run's event with its expected
  3-month change); its pages as buttons — Tác động tin, Toàn cảnh, Chi tiết, Tài sản, Kế hoạch, Duyệt đề xuất, Ghi
  liên hệ — each setting the client picker first, then opening the page as a sheet.
- **Panels:** Cần gọi trước (Hôm nay's list, one row per family, worst P10 first), Đề xuất chờ duyệt (pending, not the
  RM's own notes; opens Duyệt đề xuất for that family), Việc theo mục tiêu, Liên hệ gần đây (“từ tín hiệu” when the
  contact cites a signal, KPI-06). Recording a contact stays on Hôm nay.
- **Assistant:** the RM's own intro, suggestions and box hint; `so_khach_hang` reads the book (who needs the RM soon and
  why, proposals, goal tasks, the last contact); its 32 tools unchanged. Steps light the map (`book`), the call list
  (`hom_nay`), proposals (`de_xuat`) and contacts (`lien_he`, `ghi_lien_he`).
- **Unchanged:** every RM page and write (decide a proposal, record a contact, recommend to a specialist).

### Admin — Vận hành (SCR-ADM-02, built in M3, 2026-10-18)

- **Rail:** Vận hành · Hệ thống · Dữ liệu thị trường · Cấu hình · Agent · Nhật ký · Bộ nhớ at the foot. All six pages
  at their addresses.
- **The map:** four lanes left to right — Nguồn (news feeds, market jobs, the AI zone), Lưu trữ (the schedule, the
  audit chain with its write-once copy, availability), AI (the agents with runs and failures, the queue and the
  evaluations waiting), Con người (accounts, configuration waiting). Each node green / amber / red / grey from its
  last record (grey: never run), its error as a tooltip; a node picked lists its parts in Thông tin (each feed, each
  market job by Hệ thống's name, each agent) and opens its page.
- **One read:** the desk draws Hệ thống's own composition (`app.web.system_read`, factored out of `GET /api/system`
  unchanged), so the two never disagree; the alerts are the bell's for Admin.
- **Panels:** Cảnh báo (open and acknowledged; acknowledging stays in the bell), Việc đang lỗi, Cấu hình chờ duyệt (who
  proposed, two-person), Người dùng và vai trò (counts by role, accounts without a password; the RM assignment opens on
  Cấu hình), Chuỗi nhật ký (check, rows, write-once segments, head).
- **Users and roles (Q-25):** shown, not edited — the product has no account or password form on purpose; OWN-MR-04
  stays partly met until the owner answers.
- **Assistant:** Admin's own suggestions; `van_hanh` (what is not green, alerts, failing jobs, configuration),
  `chuoi_nhat_ky` and `cau_hinh_cho_duyet` (also Compliance's) beside `canh_bao_he_thong` and `da_xem_canh_bao`.
  Steps light the map's nodes and panels.

### Expert — Bàn chuyên gia (SCR-SP-02, built in M4, 2026-10-18)

- **Rail:** Bàn chuyên gia · Duyệt khuyến nghị · Bộ nhớ at the foot. Both pages at their addresses.
- **The bench:** the queue beside the evidence. Left, the recommendations an RM approved for the families assigned to
  this specialist, oldest first (what Duyệt khuyến nghị lists: the same filter over the same queue), and the families
  assigned with how many wait for each; right, the picked recommendation — its actions, who wrote it, the RM's note —
  and its family's picture: net worth, risk profile, risk against the limit, liquidity, allocation, goals, read
  through `POST /api/dashboard` and `/api/goals`, the reads a specialist already makes for an assigned family (Q-26).
  A family picked shows its picture without a decision.
- **The decision:** approve, or reject with a reason of 10 characters or more, through the existing
  `POST /api/review/specialist`; the server checks the certificate and the assignment again (BRD-RULE-ROLE-05,
  WF-08). The bar stays in view under a long picture. Without a certificate in force the bench says so and offers
  no decision. Below: what the specialist decided.
- **Sign-in off** (a developer's machine): the desk reads as the specialist the page decides as (`?user=`, the role's
  demo user), as Duyệt khuyến nghị does.
- **Assistant:** the Expert's own suggestions; `ban_chuyen_gia` (the queue, oldest first, and the certificate) and
  `ho_so_khach` (an assigned family's picture through the overview and goal reads; refused for any other family)
  beside the existing `de_xuat` and `chuyen_gia_duyet`. Steps light the queue and the evidence.
- **Unchanged:** Duyệt khuyến nghị and its write; the RM's recommendation and decision writes.
- **Every desk (from M4):** while a page is open as a sheet, the centre under it is inert — no focus, no click — so
  the Expert's decision bar cannot be reached behind Duyệt khuyến nghị.

### Compliance — Bàn kiểm soát (SCR-CMP-06, built in M5, 2026-10-18)

- **Rail:** Bàn kiểm soát · Tin bị giữ · Nội dung (Nghiên cứu, Bản tin, Chính sách) · Đo lường · Nhật ký · AI và cấu
  hình (Agent, Cấu hình) · Bộ nhớ at the foot. All nine pages at their addresses.
- **The controls:** one lane per control, its steps left to right, the first what waits — Tin bị giữ (held →
  let through, BRD-BR-04), Nghiên cứu (waiting → released / rejected, BR-03), Bản tin (waiting → approved / returned,
  FR-801), Chính sách (waiting for a second person's verification → verified → summarised by the policy agent,
  FR-306), Cấu hình (waiting, FR-701), Chuỗi nhật ký (rows, the hash check, the write-once segments, FR-702). A lane
  picked lists what waits in Thông tin, each opening its item, and “Mở <page>”.
- **One queue:** everything waiting for Compliance, oldest first, each row its page; research not yet at its release
  time says “Chưa tới giờ”. The alerts the bell holds for Compliance beside it.
- **Read-only:** every figure from the stores the pages read; each decision stays on its page with its rule (a reason,
  a second person, the release time).
- **Assistant:** Compliance's own suggestions; `ban_kiem_soat` (what waits, oldest first, each control, the chain)
  beside `tin_bi_giu`, `chuoi_nhat_ky`, `cau_hinh_cho_duyet`, which now light their lanes.

## API and data

`GET /api/desk` → `{role, as_of, …the role's sections}`; see [api_reference.md](../architecture/api_reference.md).

## Implementation

`src/desk/reads.py` (the composed reads), `app/web.py` (`/api/desk`), `web/desk/` (the frame and one module per
role), `web/workspace/dock.js` (divider and fold, shared with FEAT-40).

## Acceptance and tests

Listed per phase in the plan §4 and in the traceability rows OWN-MR-01…12. CIO (M1): `tests/test_role_desks.py`
(menu kept page for page, every page in one rail group, the desk the session's role's alone, figures equal to the
runs, inbox and RM reads, the assistant's numbers equal to the desk's, the agent map counts the new tools) and
`tests/ui/test_role_desks_ui.py` (every old CIO address opens as a sheet with no error, group tabs, a stage pick, the
queue opens a view with its approval, the docked assistant lights the desk, no other role reaches it, phone and
dark, the Customer's workspace after it). RM (M2): the same files — the menu and the ten client pages kept, each
RM's book is their families alone (rm01 C01/C04/C05, rm03 C03), the call list is Hôm nay's, proposals the queue's
(not the RM's own notes), net worth the run's, the assistant's numbers the book's; every old RM address as a sheet,
a family's page opened from the book sets the client picker, the assistant lights the book, phone and dark. Admin
(M3): the desk is Hệ thống's read (chain, configuration, people), a failing feed and a broken chain turn their nodes
red and the assistant names them, the chain and configuration tools read what their pages read; every Admin address
as a sheet, a node opens its page, the assistant lights the chain, no other role reaches the map, phone. Expert
(M4): each of the five specialists' desks is their families alone and lists what Duyệt khuyến nghị lists for them
(none without a certificate), oldest first; sign-in off reads as the page's user; a decision through the existing
write moves the item to “decided” and the note rule holds; the assistant's queue is the desk's and a family not
assigned is refused; in the browser both Expert addresses as sheets, the picture beside the oldest, a family picked,
a short rejection refused and an approval made on the bench, the assistant lights queue and evidence, no other role
reaches the bench, phone light and dark. Compliance (M5): the menu kept page for page; each control's waiting
count equals its page's (held news, research, letters, policy documents, configuration), the queue holds them all
oldest first and the chain is the check's; no other role gets the desk; the assistant's counts are the desk's; in the
browser five lanes waiting, a lane picked opens its page, all nine addresses as sheets with the Nội dung tabs, the
assistant lights the controls, no other role reaches it, phone light and dark. Every desk tool also runs signed in
inside a served turn (`test_a_desk_tool_works_signed_in_inside_a_served_turn`), where each read is checked against the
person: a desk read that touches a family the person may not see fails there (the RM's book did, until fixed).

## Limitations

See [Q-24](../requirements/open_questions.md#q-24--which-roles-the-multi-role-request-covers),
[Q-25](../requirements/open_questions.md#q-25--admins-user-and-role-management),
[Q-26](../requirements/open_questions.md#q-26--how-much-of-a-family-a-specialist-sees).
