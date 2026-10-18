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
a family's page opened from the book sets the client picker, the assistant lights the book, phone and dark.

## Limitations

See [Q-24](../requirements/open_questions.md#q-24--which-roles-the-multi-role-request-covers),
[Q-25](../requirements/open_questions.md#q-25--admins-user-and-role-management),
[Q-26](../requirements/open_questions.md#q-26--how-much-of-a-family-a-specialist-sees).
