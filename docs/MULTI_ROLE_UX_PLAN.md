# Multi-role UX plan — a desk for every staff role

Owner request, 2026-10-18 (verbatim in [docs/brd/sources/owner_requests/2026-10-18_multi_role_ux.md](brd/sources/owner_requests/2026-10-18_multi_role_ux.md)):
extend the Customer's graph-centric redesign to CIO, RM, Admin and Expert, each with a purpose-built experience,
without removing or weakening any capability; each role's own AI agents keep working, and each role gets its own
assistant. Branch `ux/multi-role` off `exp/graph-workspace` (the branch that ships, 2026-10-18).

This plan is the audit, the design decisions and the build order. Behaviour, once built, is documented in
`docs/brd/` (MAINTAINING.md); this file is history after that.

## 1. Audit (2026-10-18, commit 6e735dd)

### 1.1 Roles that exist

| Role (code) | UI label | Demo user | BRD rule | Pages today (`web/shell.js`) | Home today |
|---|---|---|---|---|---|
| `client` | Khách hàng | C01… | ROLE-06 | the graph workspace (FEAT-40, ADR-0035): 6 lenses, 10 sheets | `#/client/xem/tong-quan` |
| `cio` | CIO | `cio`, `cio2` | ROLE-01 | 13 menu items, 15 pages (SCR-CIO-01…14, SCR-CMP-05) | Hộp tin (the raw inbox) |
| `rm` | RM | `rm01`… | ROLE-02 | Hôm nay; Khách hàng (10 client pages, picker); Hiệu quả tư vấn | Hôm nay |
| `admin` | Quản trị | `admin` | ROLE-04 | Hệ thống, Dữ liệu thị trường, Cấu hình, Agent, Nhật ký | Hệ thống |
| `specialist` | Chuyên gia ("Expert") | `sp_global`… | ROLE-05 | Duyệt khuyến nghị (no screen document) | Duyệt khuyến nghị |
| `compliance` | Tuân thủ | `compliance`, `compliance2` | ROLE-03 | 8 menu items | Tin bị giữ |

The request names four roles; **Compliance** also exists and the completion criterion is "every role has a coherent,
role-appropriate UX", so it is the fifth phase. "Expert" is the `specialist` role ("Chuyên gia", BRD-RULE-ROLE-05).

### 1.2 What breaks or is weak today (evidence: screenshots in `$SP/mr/shots/before`, 1440 × 900)

- **CIO:** thirteen top-level tabs overflow the header at 1440 px ("Cấu hì…" cut). The home is the inbox — 300 raw
  items — not what waits for the CIO's decision. Nothing on one screen says where the news-to-family pipeline stands.
- **RM:** Hôm nay is three lists; the RM's book (who are my families, who needs a call, what waits for me) is spread
  over Hôm nay, the client picker and Duyệt đề xuất.
- **Admin:** a long page of tables; integrations, jobs, the AI zone and the chain are not seen as one system.
- **Expert:** one list of cards with no evidence beside a recommendation: the specialist decides without the family's
  picture, although `people.auth.may_see` already lets them read their assigned families.
- **Compliance:** eight tabs, each its own queue; no single "what must I control now".
- **Assistants:** every role has one (`registry.agent_tools(role)`), but outside client and RM the tool sets are thin:
  CIO 20 tools of which 5 are its own (inbox, fetch, events, urgent mark, alerts) — none for views awaiting a
  decision, runs, exposure or accuracy; Admin only alerts; Compliance only held news; Expert only the queue. Staff
  get the floating panel (one JSON reply), not the docked, streaming panel with the progress list.

### 1.3 The AI agents beneath each role (must not break)

| Agent | Role that drives it | Where it is triggered in the UI today | Backend |
|---|---|---|---|
| Agent CIO (FEAT-04) + challenger (FEAT-05) | CIO | Sự kiện & nhận định → "Chạy Agent CIO"; view edits | `views/` (agent_worker, queue, eval) |
| Policy agent (FEAT-16) | Compliance | Chính sách → a document → "Chạy Agent Chính sách" | `policy/` |
| Newsletter opening (FEAT-17) | CIO | Bản tin → "Soạn bản tin mới" (template or agent) | `newsletter/` |
| AI zone agent, inbox mode (FEAT-19) | Admin watches | Hệ thống → Vùng AI và hộp chờ | `zone/` |
| Assistant + background agents (FEAT-37…39) | every role | the Copilot panel | `assistant/` |

Rule for this plan: **no change to any agent's backend**; every trigger stays where it is (its page becomes a
sheet, unchanged); each desk shows its role's agents' state, read from `GET /api/agents`.

### 1.4 Permissions (unchanged)

Every read is gated by `app/web.py::ROUTE_ROLES` and `people.auth.may_see`; every write by `control.roles.require`.
The UI never grants anything. The desks read only through a new composed read, `GET /api/desk`, which takes the
role **from the session** (sign-in on) and returns only that role's desk, built from the same stores the existing
reads use, with the same family filter.

## 2. Decisions

- **D1 — One frame, five purpose-built centres.** Every staff role gets the Customer's frame — the rail on the
  left, a centre, the dock (Trợ lý · Thông tin) on the right, existing pages as sheets over the centre — but its own
  centre, built for its job, not the Customer's radial wealth graph (ADR-0036, superseding ADR-0035 §1 for staff).
- **D2 — Every page stays, at its address.** The menu ids of `web/shell.js` do not change; every old route opens
  its page module unchanged, as a sheet. The rail groups the pages (presentation only); the sheet header shows the
  group's pages as tabs. A new first menu entry, `ban` ("Bàn làm việc"), is the desk: `#/<role>` and
  `#/<role>/ban` show it. `#nav` is still drawn (hidden) so the route crawler covers every page.
- **D3 — One composed read per desk.** `GET /api/desk` (`src/desk/reads.py`): counts and short lists the desk and
  the assistant both use, so what the screen says and what the assistant says are the same numbers. Read-only.
- **D4 — Each role's own assistant, docked.** The Copilot docks in every desk (streaming, the progress list, the
  live highlight on the centre), with the role's starters and new read tools over the desk's data (§4). Writes keep
  the confirm step. Tool descriptions keep the catalogue rules (no digits); every tool has its progress sentences.
- **D5 — No new permission, no new write.** The Expert desk decides through the existing `POST /api/review/specialist`,
  the RM desk records contacts through the existing contact write; nothing else writes.
- **D6 — Shared code where it is the same thing.** The dock's divider and fold move from `workspace.js` into
  `web/workspace/dock.js`, used by both; the rest of the Customer workspace is not touched.

## 3. The desks

### CIO — "Bàn quyết định" (SCR-CIO-15)

- **Centre:** the pipeline as a flow graph, left to right: Tin → Sự kiện → Nhận định → Lần áp dụng → Gia đình → RM.
  Each stage a node with its count and what waits for the CIO (badge), edges with the flow between them. A stage
  picked → Thông tin lists its items, each linking to its page (a sheet).
- **Panels:** *Cần bạn quyết định* (views waiting for the CIO, held runs, configuration needing a (second) CIO, draft
  or returned letters); *Phơi nhiễm* (the latest effective run, top factors); *Sự kiện nổi bật*; *Mô hình và dữ liệu*
  (accuracy verdict, factors on real data, failing jobs); *Agent* (CIO agent and challenger mode, last runs).
- **Rail groups:** Bàn quyết định · Tin & sự kiện (Hộp tin, Sự kiện & nhận định) · Tác động (Lần áp dụng, Phơi
  nhiễm, Đồ thị lần áp dụng) · Nội dung (Nghiên cứu, Bản tin, Chính sách) · Mô hình (Tham số, Dữ liệu thị trường,
  Độ chính xác, Đo lường) · AI & cấu hình (Agent, Cấu hình) · Bộ nhớ.
- **Assistant tools:** `ban_quyet_dinh`, `phoi_nhiem`, `lan_ap_dung`, `do_chinh_xac` (read).

### RM — "Sổ khách hàng" (SCR-RM-07)

- **Centre:** the book as a relationship map: the RM in the middle, their families around, nearer when they need the
  RM sooner (a 3-month bad case past −5 %, a goal task "liên hệ ngay", a proposal waiting), sized by net worth. A
  family picked → Thông tin: its card and actions (open its impact, its overview, approve its proposals, record a
  contact) — each sets the client picker and opens the existing page.
- **Panels:** *Cần gọi trước* (Hôm nay's list), *Việc theo mục tiêu*, *Đề xuất chờ duyệt*, *Liên hệ gần đây*.
- **Rail groups:** Sổ khách hàng · Hôm nay · Khách hàng (the ten client pages) · Hiệu quả tư vấn · Bộ nhớ.
- **Assistant tools:** `so_khach_hang` (read) beside its 32.

### Admin — "Vận hành" (SCR-ADM-02)

- **Centre:** the system as a map: news sources and market jobs → the store and the audit chain → the agents and the
  AI zone → the people; each node green / amber / red from its last run, with the error on hover.
- **Panels:** open alerts, failing jobs, configuration waiting (two-person), people and roles, the chain.
- **Rail groups:** Vận hành · Hệ thống · Dữ liệu thị trường · Cấu hình · Agent · Nhật ký · Bộ nhớ.
- **Assistant tools:** `van_hanh`, `chuoi_nhat_ky`, `cau_hinh_cho_duyet` (read).

### Expert — "Bàn chuyên gia" (SCR-SP-02; the existing page documented as SCR-SP-01)

- **Centre:** the queue beside the evidence: the picked recommendation's actions, numbers and the RM's note, and the
  family's picture (net worth, allocation, risk profile, goals) read through the reads the specialist may already
  open; the certificate; approve / reject with the note rule, through the existing write.
- **Rail groups:** Bàn chuyên gia · Duyệt khuyến nghị · Bộ nhớ.
- **Assistant tools:** `ban_chuyen_gia`, `ho_so_khach` (read; an assigned family only).

### Compliance — "Bàn kiểm soát" (SCR-CMP-06)

- **Centre:** the controls as a flow: news → held → released; research → release; letters → approval; policy
  documents → verified → summarised; the chain. Each with its count waiting.
- **Rail groups:** Bàn kiểm soát · Tin bị giữ · Nội dung (Nghiên cứu, Bản tin, Chính sách) · Đo lường · Nhật ký ·
  AI & cấu hình (Agent, Cấu hình) · Bộ nhớ.
- **Assistant tools:** `ban_kiem_soat`, `chuoi_nhat_ky`, `cau_hinh_cho_duyet` (read).

## 4. Build order

| Phase | What | Gate |
|---|---|---|
| M0 | Foundation: `src/desk/reads.py` + `GET /api/desk`; `web/desk/` frame; `dock.js` extraction; shell routing; docked Copilot for staff; plan + ADR-0036 + owner request | full suite; Customer UI tests unchanged — **done 2026-10-18** |
| M1 | CIO desk + tools | preservation, isolation, desk UI tests; screenshots desktop/phone, light/dark — **done 2026-10-18** |
| M2 | RM desk + tool | same — **done 2026-10-18** |
| M3 | Admin desk + tools | same — **done 2026-10-18** |
| M4 | Expert desk + tools | same — **done 2026-10-18** |
| M5 | Compliance desk + tools | same |
| M6 | BRD close-out: IA, inventory, journeys, matrix rows, regression record; a few real-model turns per role (cost counted) | full suite + every UI test; `check_brd_docs.py` |

**Tests every phase adds:** (1) *preservation* — every old route of the role opens its page as a sheet, with no
error; (2) *isolation* — `/api/desk` gives each role only its own desk, a client gets none, another role's desk
address opens the person's own; the new tools exist only for their roles and refuse others on the server; (3) the
desk's figures equal the existing reads' (no second arithmetic); (4) UI — the desk renders, a pick fills Thông tin,
a stage opens its sheet, the assistant's step lights its node, phone and dark without errors or horizontal scroll.

## 5. What this plan does not do

- No agent backend change, no new write, no permission change.
- The Customer workspace is untouched apart from `dock.js`.
- `main` gets nothing (the experiment branch ships, 2026-10-18).
