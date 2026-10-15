# Interaction patterns

Layer C. Patterns used across screens, so each screen document only names them.

| Pattern | Behaviour | Used on |
|---|---|---|
| **Role switch** | Changes the route to the role's first page; the server checks the role behind every action anyway | shell |
| **Client and scope pickers** | Changing them re-renders the current client-scoped page | client pages, RM “Khách hàng” |
| **Routes as addresses** | Every page and detail has a URL (`#/cio/nhan-dinh/VW-0001-v1`), so a link or a reload lands in the same place | all |
| **Action with a reason** | Decisions take a reason field; the server enforces its length (5 for view decisions, 10 for finding answers, 20 for research release) and the toast shows the server's refusal in Vietnamese | SCR-CIO-03, 05, SCR-CMP-01, 02 |
| **Checklist before a gate** | The approval conditions are shown as ✓/✕ with the reason of each failure; “Duyệt và áp dụng” is disabled until all pass, and the server checks them again | SCR-CIO-03 |
| **Idempotent action** | The page builds `idem_key = <action>:<view id>:<first 12 of the content hash>`, so a repeated click on the same content is one decision and one run; buttons disable while the request runs | SCR-CIO-03, 05 |
| **Progress line** | Agent soạn → Phản biện → CIO duyệt → Đã duyệt | SCR-CIO-03 |
| **Hero + band + contributions** | One figure, its range over time, where it comes from | SCR-CL-05, SCR-RM-02 |
| **Trace drawer** | “Cách tính” opens a right drawer with the chain to the source; Esc closes | SCR-RM-02 → 03 |
| **Fold the detail** | `details.more` keeps the page short; the summary says what is inside | most new pages |
| **Badge for provenance** | “giả định”, “mô phỏng”, “theo mô hình”, “Độc quyền”, “AI hỗ trợ · CIO duyệt”, “demo” | throughout |
| **Empty state with a promise** | Says what will appear and when (“Khi một lần áp dụng có gia đình chạm ngưỡng −5 %, ca đó hiện ở đây.”) | new pages |
| **Assistant state** | The Copilot button and panel show idle / busy / ok / error / pending, set only by the request (FEAT-33) | every page |
| **Evidence mark** | An answer's `focus` keys ring the matching `data-focus` elements for 2.6 s (a chart dims its other marks; the graph lights the path); on another page after it renders; a still outline under reduced motion | SCR-CL-08, 09, Tác động tin, SCR-RM-01 |
| **Demo reset** | “Làm lại demo” in the footer empties the demo state (including the audit log) | footer |

## States every new page handles

| State | How |
|---|---|
| Loading | skeleton rows (`loading()`), `aria-busy="true"`; a newer navigation cancels an older render |
| Empty | `empty(title, hint)` |
| Error | `failed(e)`: “Không tải được: <message>”, `role="alert"` |
| Permission denied | the server answers with the role needed (“… không được làm việc này; cần vai trò: CIO”); shown as a toast. Pages are not hidden by role beyond the menu (the switcher is a demo) |
| Partial data | “—” for values a source did not provide; held items listed; a run's post-check findings shown with it |
