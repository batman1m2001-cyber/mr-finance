# Admin screens

Admin's own pages. Admin also has Dữ liệu thị trường ([SCR-CIO-11](cio.md#scr-cio-11--dữ-liệu-thị-trường-market-data)),
Cấu hình ([SCR-CIO-09](cio.md#scr-cio-09--cấu-hình-versioned-configuration)), Agent and Nhật ký.

## SCR-ADM-01 — Hệ thống (system)

| | |
|---|---|
| Route | `#/admin/he-thong` (Admin's first page) |
| Generation | new (F5, `web/pages/system.js`) |
| Feature | [FEAT-12](../../features/FEAT-12-roles-and-separation-of-duties.md), [FEAT-19](../../features/FEAT-19-external-ai-inbox.md) (the zone and the inbox), [FEAT-36](../../features/FEAT-36-alerts-and-central-log.md) (alerts, the log) |
| Requirements | BRD-RULE-ROLE-04, BRD-NFR-12, BRD-RULE-ROLE-02 (the RM assignment), BRD-FR-307 (the mode shown) |
| Data | `GET /api/system` (Admin only), `POST /api/market/load` (Admin only) |
| Screenshots | [desktop, after a load of the history since 2026-10-01](../../assets/current_ui/SCR-ADM-01_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-ADM-01_phone-light.jpg) · [alerts, desktop](../../assets/current_ui/SCR-ADM-01-alerts_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-ADM-01-alerts_phone-light.jpg) · [the AI zone section, desktop](../../assets/current_ui/SCR-ADM-01-zone_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-ADM-01-zone_phone-light.jpg) |

- **Four tiles:** the audit chain's check (intact or where it breaks), the agents' mode and models, the last news fetch, and the configuration waiting for approval.
- **Cảnh báo:** the last 30 alerts of every kind (title, kind, id, how many times and when last, the error, status
  Đang mở / Đã xem / Đã hết, who acknowledged with their note), and “Đã xem” on an open one (asks for an optional
  note; audited). The lede counts the open alerts.
- **Background jobs:** every job declared in `app/main.py`, with what it does, when it runs, and how it last went. The news and market jobs report ok or error with the error text. A job that keeps no record here says so.
- **News sources:** the last fetch from each source: items fetched, accepted, refused, and any error.
- **Agents:** the last 7 days, per agent: runs, failures, and the last run. Eval-set runs still waiting are listed.
- **Vùng AI và hộp chờ:** the AI mode in force (a link to “Chế độ chạy AI” in Cấu hình), the zone's last ten
  packages (when received, signature valid or not, Chờ nhập / Đang nhập / Đã nhập / Từ chối, and the view it became
  or the error), and the last sync to the zone with the catalogue versions it put in force. The Agent tile counts
  the runs queued.
- **Load the market history again:**
  - Admin picks a start date (2015-01-01 to today) and sends the request.
  - The `market_load` job runs it within a minute, one load at a time.
  - Every load is listed with its status (Đang chờ, Đang nạp, Xong, Lỗi) and the points kept.
  - Each request is an audit row (`market.load_asked`).
- **Nhật ký hệ thống:** the central log's last 30 warnings and errors (when, level, process, event, what).
- **People:**
  - Every staff account: name, title, role, login, whether a password is set, and an RM's families.
  - The number of customer accounts.
  - A link to "Phân công RM" in Cấu hình, where Admin changes the assignment.

Not here, on purpose: setting or resetting a password. On the public demo anyone can sign in as Admin, so a password form would let a visitor lock others out. Passwords are set with `scripts/set_password.py`.

## SCR-ADM-02 — Vận hành (Admin desk)

| | |
|---|---|
| Route | `#/admin`, `#/admin/ban`; every other Admin address opens its page as a sheet over the desk |
| Feature | [FEAT-41](../../features/FEAT-41-role-desks.md) (and the pages it gathers: FEAT-11, 12, 14, 15, 19, 35, 36) |
| Requirements | OWN-MR-01, OWN-MR-04 (partly, Q-25), OWN-MR-06, OWN-MR-07, OWN-MR-10; BRD-RULE-ROLE-04, BRD-NFR-12 |
| Data | `GET /api/desk` — Hệ thống's read (`GET /api/system`) and the bell's alerts for Admin |
| Screenshots | [desktop](../../assets/current_ui/SCR-ADM-02_desktop-light.jpg) · [a node picked, dark](../../assets/current_ui/SCR-ADM-02-pick_desktop-dark.jpg) · [phone, dark](../../assets/current_ui/SCR-ADM-02_phone-dark.jpg) |

**Centre.** Header “Quản trị · Vận hành” with “<n> nút lỗi · <a> cảnh báo đang mở · <j> việc lỗi · <c> cấu hình chờ
duyệt” and a pill for the chain. The map: four lanes (Nguồn → Lưu trữ → AI → Con người) of node buttons, each with a
coloured dot, its label, its value (“11/11 nguồn”, “613 dòng”, “Mô hình thật”) and a note (“lấy gần nhất 1 ngày
trước”); a phone shows two lanes per row. Below: **Cảnh báo**, **Việc đang lỗi**, **Cấu hình chờ duyệt**, **Người dùng
và vai trò**, **Chuỗi nhật ký**.

**Thông tin (a node picked).** Its state and value, the note and the error, its parts with their own states, and
“Mở <page>”.

