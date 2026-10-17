# The assistant stress test — the browser pass

What HTTP cannot check, through the real panel on the served copy (:8041) and the real model, by
`scripts/stress_browser.py` (Playwright; customer C01). It was run twice on 2026-10-18: once before D30 and D31 were
known, and once on the final code. The screenshots in `browser/` are from the final pass; the label shots are from
`label_*.jpg` after the D30 fix.

| Check | First pass | Final pass |
|---|---|---|
| A goal picked on *Mục tiêu & kịch bản*, “Nút này nói gì vậy?” | Named the goal, but began “Tôi chưa rõ bạn đang hỏi nút nào” (D31; the panel had reopened a 21-turn conversation) | “Nút đang chọn là mục tiêu Học phí cho con… cần để dành khoảng 79,1 triệu đồng mỗi tháng… ước tính” |
| The graph lights what the assistant reads | Not measured: the probe watched the wrong classes | `GL:tuition` and the core lit (`act`, then `ok` / `lit` / `kept`) |
| A write asks first, and only the click writes | Asked; 0 items before the click, 1 after | The same: “Ghi nhớ (Sở thích): … ?” with Xác nhận / Huỷ; 0 before, 1 after |
| Title and history kept after a reload | Title and 25 messages kept | Title “Quỹ học phí cho con” and 4 messages kept; the history lists it with its goal |
| The panel names the view on screen | “Đang xem: Tổng quan tài chính” on *Mục tiêu & kịch bản* (D30) | “Đang xem: Mục tiêu & kịch bản” on desktop and phone (`label_desktop.jpg`, `label_phone.jpg`) |
| Phone (390 px): the same question, no sideways scroll | Answered; no sideways scroll | Answered from what was already read (no tool, so nothing lit); no sideways scroll |

Screenshots: `pick_desktop.jpg`, `confirm_desktop.jpg`, `history_desktop.jpg`, `pick_phone.jpg`, `label_desktop.jpg`,
`label_phone.jpg`.
