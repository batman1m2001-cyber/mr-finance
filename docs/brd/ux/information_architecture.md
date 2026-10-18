# Information architecture

Layer C. How the product is organised for each role, as built on 2026-10-15 (`web/shell.js`). Behaviour lives in
the features; this page says **where** each one is.

## The shell

Every page shares one header ([SCR-CL-01 screenshot](../assets/current_ui/SCR-CL-01_desktop-light.jpg)):

| Element | What it does |
|---|---|
| Brand “OneWealth” | — |
| **Role switcher** — Khách hàng · RM · CIO · Tuân thủ | Changes the route to that role's first page; for staff roles shows “Đang dùng: <name> · <title> `demo`”. Not security ([ADR-0006](../decisions/ADR-0006-the-role-switcher-is-not-security.md)). The `admin` user exists server-side but has no UI role. |
| **Client picker** (client role, and RM's “Khách hàng” section) | Which client the client-scoped pages show (5 sample clients) |
| **Scope** — Cá nhân · Gia đình | Personal or household view (consenting members only) for the pre-BRD pages |
| Theme toggle ◐ | Light / dark; remembered per browser (`mf.theme`) |
| Footer | “Dữ liệu khách hàng và giá là mô phỏng; tin tức lấy từ nguồn công khai; tham số mô hình là giả định. Nội dung không phải khuyến nghị đầu tư. Bộ chuyển vai trò chỉ để demo, không phải cơ chế bảo mật.” + **Làm lại demo** (`POST /api/reset`) |

Address = route: `#/<role>/<section>[/<sub>][/<param>]`, e.g. `#/cio/nhan-dinh/VW-0001-v1`. The last role is
remembered (`mf.role`).

## Navigation per role

```text
Khách hàng (client)                         RM
├── Tổng quan                               ├── Hôm nay ......................... SCR-RM-01
│   ├── Toàn cảnh ....... SCR-CL-08         ├── Khách hàng  (client picker)
│   ├── Bản đồ tài chính  SCR-CL-11         │   ├── Tác động tin ................ SCR-RM-02 (+ SCR-RM-03 drawer)
│   └── Chi tiết ........ SCR-CL-01         │
├── Tài sản ............. SCR-CL-02         │   ├── Đồ thị tác động ............. SCR-CL-09 (staff view)
├── Mục tiêu & kịch bản                     │   ├── Toàn cảnh ................... SCR-CL-08 (staff view)
                                            │   ├── Bản đồ tài chính ............ SCR-CL-11 (staff view)
│   ├── Kế hoạch ........ SCR-CL-03         │   ├── Chi tiết .................... SCR-CL-01 (staff view)
│   └── Khẩu vị rủi ro .. SCR-CL-04         │   ├── Tài sản ..................... SCR-CL-02
├── Tin tác động                            │   ├── Kế hoạch .................... SCR-CL-03
│   ├── Tác động thị trường SCR-CL-05       │   ├── Chi phí chính sách .......... SCR-CL-06
│   ├── Đồ thị tác động . SCR-CL-09         │   ├── Hiệu quả tư vấn ............. SCR-RM-04
│   └── Chi phí chính sách  SCR-CL-06       │   └── Duyệt đề xuất ............... SCR-RM-06
└── Chuyên gia .......... SCR-CL-07         └── Hiệu quả tư vấn (all clients) ... SCR-RM-05

CIO                                         Tuân thủ (Compliance)
├── Hộp tin ............. SCR-CIO-01        ├── Tin bị giữ ...................... SCR-CMP-01
├── Sự kiện & nhận định . SCR-CIO-02        ├── Nghiên cứu ...................... SCR-CMP-02
│   └── /<view id> ...... SCR-CIO-03        ├── Nhật ký ......................... SCR-CMP-03
│                                           ├── Bản tin ......................... SCR-CMP-04
│                                           ├── Chính sách (radar) .............. SCR-CMP-05
│                                           ├── Agent ........................... SCR-CIO-08
│                                           └── Cấu hình ........................ SCR-CIO-09
├── Phơi nhiễm .......... SCR-CIO-04
├── Lần áp dụng ......... SCR-CIO-05
├── Đồ thị lần áp dụng .. SCR-CIO-10
├── Nghiên cứu .......... SCR-CIO-06
├── Bản tin ............. SCR-CIO-14
├── Chính sách .......... SCR-CMP-05 (read only)
├── Mô hình ............. SCR-CIO-07
├── Agent ............... SCR-CIO-08
└── Cấu hình ............ SCR-CIO-09
```

Every page is an ES module in `web/pages/` rendered into `#page` ([ADR-0019](../decisions/ADR-0019-every-page-is-a-module-page.md),
which supersedes ADR-0013's two generations since UI redesign R3, 2026-10-16). The shell owns the client picker,
the personal / family scope and “Làm lại demo”. The same page appears for the client and inside the RM's
“Khách hàng” section (staff view, marked internal).

### Customer, graph workspace (experiment, FEAT-40 — proposed)

```text
Khách hàng — one page: toolbar │ graph │ dock (Trợ lý · Thông tin) │ strip
├── Tổng quan ........... lens   sheets: Toàn cảnh (SCR-CL-08), Chi tiết (SCR-CL-01)
├── Tài sản ............. lens   sheet: Tài sản (SCR-CL-02)
├── Dòng tiền ........... lens   sheet: Dòng tiền chi tiết (Money Flow of SCR-CL-08)
├── Mục tiêu & kịch bản . lens   sheet: Kế hoạch (SCR-CL-03)
├── Tin & sự kiện ....... lens   sheets: Tác động thị trường (SCR-CL-05), Đồ thị tác động (SCR-CL-09), Chi phí chính sách (SCR-CL-06)
├── Rủi ro .............. lens   sheets: Khẩu vị rủi ro (SCR-CL-04), Chi tiết (SCR-CL-01)
├── Chuyên gia .......... sheet  SCR-CL-07 (a separate view, OWN-GW-05)
└── Bộ nhớ .............. sheet  the memory page
```

The tree above (“Navigation per role”) stays the RM's and staff's, and `main`'s Customer navigation until the
experiment is taken (ADR-0035).

### Staff desks (experiment, FEAT-41 — built 2026-10-18)

Each staff role opens on its desk at `#/<role>`: the rail of its groups, its own centre, the dock (Trợ lý · Thông
tin). Every page of the menu above opens as a sheet over the desk at its unchanged address, with its group's tabs.

```text
CIO · Bàn quyết định (SCR-CIO-15)       rail: Bàn quyết định · Tin & sự kiện · Tác động · Nội dung · Mô hình ·
                                              AI & cấu hình · Bộ nhớ
RM · Sổ khách hàng (SCR-RM-07)          rail: Sổ khách hàng · Hôm nay (now #/rm/hom-nay) · Khách hàng · Hiệu quả tư vấn
                                              · Bộ nhớ
Quản trị · Vận hành (SCR-ADM-02)        rail: Vận hành · Hệ thống · Dữ liệu thị trường · Cấu hình · Agent · Nhật ký ·
                                              Bộ nhớ
Chuyên gia · Bàn chuyên gia (SCR-SP-02) rail: Bàn chuyên gia · Duyệt khuyến nghị · Bộ nhớ
Tuân thủ · Bàn kiểm soát (SCR-CMP-06)   rail: Bàn kiểm soát · Tin bị giữ · Nội dung (Nghiên cứu, Bản tin, Chính sách)
                                              · Đo lường · Nhật ký · AI & cấu hình (Agent, Cấu hình) · Bộ nhớ
```

`#/rm` used to open Hôm nay; it now opens the book, and Hôm nay is `#/rm/hom-nay` (its rail group). The page-by-page
map of every role, with each page's requirements, is [role_desks.md](role_desks.md).

## Where each capability lives

| Capability | Feature | Client | RM | CIO | Compliance |
|---|---|---|---|---|---|
| News → goal graph | FEAT-30 | Tin tác động → Đồ thị tác động | Khách hàng → Đồ thị tác động | Đồ thị lần áp dụng (whole run) | — |
| Overview graph (classes, sources, goals, risks, policy, news) | FEAT-30 | Tổng quan → Bản đồ tài chính | Khách hàng → Bản đồ tài chính | — | — |
| Ask / act / navigate (Copilot) | FEAT-32 | ✦ panel on every page | ✦ panel | ✦ panel | ✦ panel |
| What matters now (feed) | FEAT-31 | Tổng quan → Toàn cảnh | Khách hàng → Toàn cảnh | — | — |
| Pulse, Wealth Map, Money Flow | FEAT-29 | Tổng quan → Toàn cảnh | Khách hàng → Toàn cảnh | — | — |
| Net worth, allocation, P&L, risk, liquidity, cash flow | FEAT-21 | Tổng quan → Chi tiết | Khách hàng → Chi tiết | — | — |
| Every holding, statements, chat declarations | FEAT-20, 22, 23 | Tài sản | Khách hàng → Tài sản | — | — |
| Life scenarios, stress tests, goals planning, send to RM | FEAT-26, 27 | Mục tiêu & kịch bản → Kế hoạch | Khách hàng → Kế hoạch | — | — |
| Risk test | FEAT-24 | Mục tiêu & kịch bản → Khẩu vị rủi ro | — | — | — |
| News impact on the family | FEAT-13 | Tin tác động → Tác động thị trường | Khách hàng → Tác động tin | — | — |
| “Cách tính” trace | FEAT-09 | — (Q-14) | from Tác động tin | — | — |
| Goal-branch notes | FEAT-10 | in Tác động thị trường | Hôm nay; Tác động tin | Nghiên cứu | Nghiên cứu |
| Policy costs, house views | FEAT-25 | Tin tác động → Chi phí chính sách; top 3 on Tổng quan | Khách hàng → Chi phí chính sách | — | — |
| Specialist; the approval queue (read-only for the client) | FEAT-27, 28 | Chuyên gia | Khách hàng → Duyệt đề xuất (decides) | — | — |
| Advisory track record (mock) | FEAT-28 | — | Hiệu quả tư vấn (one / all) | — | — |
| Families to call first | FEAT-13 | — | Hôm nay | — | — |
| News inbox, grouping | FEAT-01, 02 | — | — | Hộp tin | — |
| Views, challenger, decisions, preview | FEAT-04…06 | — | — | Sự kiện & nhận định | — |
| Exposure of all clients by factor | FEAT-08 | — | — | Phơi nhiễm | — |
| Runs, post-check, verify, recompute | FEAT-08 | — | — | Lần áp dụng | — |
| Research upload / release | FEAT-03 | — | — | Nghiên cứu (upload) | Nghiên cứu (release) |
| Factor model | FEAT-07, 14 | — | — | Mô hình | — |
| Agent catalogue, AI quality | FEAT-15 | — | — | Agent | Agent |
| Versioned configuration | FEAT-14 | — | — | Cấu hình | Cấu hình |
| Held news | FEAT-02 | — | — | — | Tin bị giữ |
| Audit log | FEAT-11 | — | — | — | Nhật ký |

**Fixed 2026-10-15 (DEF-02):** the RM approval queue had no RM entry after the redesign (the U1 shell mapped the
legacy “RM duyệt” tab only to the client's “Chuyên gia”) and the service checked no role. Now the RM decides under
Khách hàng → **Duyệt đề xuất** (SCR-RM-06), the server requires role `rm`, and the client sees the queue read-only.

Capabilities with **no UI entry**: the scheduled news fetch (FEAT-01, a job), the statement-reading eval (CLI). Not built: FEAT-16…19.
