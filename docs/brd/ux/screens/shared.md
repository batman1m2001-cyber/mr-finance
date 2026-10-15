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
