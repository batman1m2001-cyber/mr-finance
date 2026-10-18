# Screens every person sees

Layer C. As built on 2026-10-16.

---

## SCR-SH-01 — Đăng nhập (sign in)

| | |
|---|---|
| Route | any address, without a session |
| Feature | [FEAT-12](../../features/FEAT-12-roles-and-separation-of-duties.md) |
| Requirements | BRD-RULE-SEC-01, BRD-RULE-ROLE-02 |
| Data | `GET /api/auth/me`, `POST /api/auth/login`, `GET /api/auth/accounts`, `POST /api/auth/demo` |
| Screenshot | [desktop](../../assets/current_ui/SCR-SH-01_desktop-light.jpg), [phone](../../assets/current_ui/SCR-SH-01_phone-light.jpg) |

A card “Đăng nhập” with the e-mail or customer code and the password; a wrong one is answered in words under the
button (“Sai tên đăng nhập hoặc mật khẩu”, the same for any failure). Nothing of the app shows before signing in:
no navigation, no family picker, no Copilot.

With `MF_DEMO_ACCOUNTS=on` (the public demo), **Tài khoản demo** lists the accounts by role — customers (a household
member says whose family), RMs, CIOs, Compliance, Admin — each with its name, title and login; one click signs in.

After signing in the header shows the person's name and title and **Đăng xuất**; the navigation is their role's
only, and an address of another role's page opens their own. A customer has no family picker; an RM's lists the
families assigned to them.

---

## SCR-SH-02 — Việc nền (the agents and the background jobs)

| | |
|---|---|
| Route | CIO `#/cio/viec-nen`, Admin `#/admin/viec-nen`, Compliance `#/compliance/viec-nen` (a sheet over the desk) |
| Feature | [FEAT-41](../../features/FEAT-41-role-desks.md), [FEAT-15](../../features/FEAT-15-agent-catalogue.md) |
| Requirements | OWN-MR-02, OWN-MR-04, OWN-AS-06; BRD-RULE-AI-13, BRD-RULE-ROLE-04, BRD-NFR-10, BRD-NFR-12 |
| Data | `GET /api/jobs`; `POST /api/events/run-agent`, `POST /api/views/decide` (`challenge`), `POST /api/jobs/run` |
| Screenshots | [CIO, desktop](../../assets/current_ui/SCR-SH-02_desktop-dark.jpg) · [Admin, phone](../../assets/current_ui/SCR-SH-02-admin_phone-dark.jpg) |

The owner asked (2026-10-18) whether the CIO's background agents had a UI, and whether the assistant could control
them. Header “Việc nền” with the agents' mode, the runs waiting and the jobs failing, and who runs what.

- **Agent.** The mode and the two models, today's tokens against the budget, each agent's runs in 7 days with its
  last error. The CIO gets **Chạy Agent CIO** on each event with no view and no open request, and **Phản biện lại**
  on a view whose challenger failed. Then **Các lần “Chạy Agent CIO”**: each request's state, who asked, the mode, its
  view or its error.
- **Lịch chạy.** Each job: its clock, the last run (scheduled or by hand) and its error. Admin gets **Chạy ngay** on
  the jobs that may run by hand (control/jobs.py `RUNNABLE`: news, the price jobs, the policy sweep, the chain check,
  the AI zone's import and sync, the accuracy score); one run at a time per job.
- **Lần chạy tay.** Who ran what, when, how long, how many items, the error.

Compliance reads the page without buttons. The assistant does the same writes on a Xác nhận (`chay_agent_cio`,
`phan_bien_lai` for the CIO; `chay_viec_nen` for Admin); what they lead to (a view's approval) stays on its page. A
phone reads the rows as lists, no sideways scroll.
