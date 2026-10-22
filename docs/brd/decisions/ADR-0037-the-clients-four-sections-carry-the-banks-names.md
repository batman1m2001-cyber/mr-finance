# ADR-0037 — The client's four sections carry the bank's names; the graph is hidden from the client

- **Status:** accepted, built 2026-10-22
- **Context source:** [business feedback 2](../sources/owner_requests/2026-10-22_business_feedback_2.md);
  plan [`docs/WEALTH_NAMES_PLAN.md`](../../WEALTH_NAMES_PLAN.md)
- **Amends:** [ADR-0035](ADR-0035-the-customer-workspace-is-one-persistent-graph.md) (the graph is no longer the
  client's main screen, nor one of its tabs)

## Context

The client's vertical menu had seven items (Tổng quan, Tài sản, Dòng tiền, Mục tiêu, Tin tức, Rủi ro, Chuyên gia),
and Tổng quan had two tabs (Toàn cảnh, Đồ thị tài chính). The business likes the vertical layout but needs the
bank's own section names, the ones the Wealth exam is set in, and finds two items said twice: Dòng tiền is on
Toàn cảnh, and the graph adds nothing Toàn cảnh does not show.

## Decision

1. **Four sections**, in English as the bank writes them:

   | Section | Its tabs | Was |
   |---|---|---|
   | Wealth View | Wealth view · Dữ liệu chi tiết tài sản | Tổng quan › Toàn cảnh; Tài sản |
   | Wealth Planning Advisor | Wealth planning advisor · Risk profile test | Mục tiêu › Kế hoạch; Rủi ro › Khẩu vị rủi ro |
   | Headline News | Tác động tin · Đồ thị tác động · Chi phí chính sách | Tin tức |
   | Relationship specialist | — | Chuyên gia |

   Only the names and the grouping change: every page is the same page, and the layout stays the new one.
2. **No address is renamed.** `#/client/tai-san`, `#/client/muc-tieu/ke-hoach`, `#/client/rui-ro/khau-vi`,
   `#/client/tin/…`, `#/client/chuyen-gia` open their pages under their new section; `#/client/dong-tien` opens
   Wealth View at its cash flow; `#/client/tong-quan/ban-do` (the former Đồ thị tài chính tab) and any unknown
   address open Wealth View.
3. **The graph is hidden from the client, not deleted.** No tab, no header-search hit, no page the assistant can open
   (its six graph pages left the assistant's list). Its own address `#/client/xem/<lens>` still opens it, linked from
   nowhere, so the code keeps its tests and can come back with one tab. The RM's Bản đồ tài chính is unchanged.
4. **Headings follow the menu**: a client page's eyebrow is its section, its title the tab where the bank names it
   (Risk profile test, Relationship specialist); staff see the same pages with their own headings.
5. **The assistant and the user guide use the same names** (its page list, keyword router, lens names;
   `docs/huong-dan/khach-hang.md`).

## Consequences

- The rail is wider on the client's pages (104 px) so the names break between words, never inside one. The graph's
  unlinked address keeps the 72 px rail and one row of tabs (the way back, "Trên đồ thị"), so the graph keeps the geometry its tests were written
  for: at a 32 px narrower canvas (952 px; also a 1408 px window on main) its layout re-places some nodes outside the
  visible area — a latent layout defect, recorded in the plan, not fixed here since no client sees the graph.
- Business item 6 ("đổ màu như này") showed a real defect: `.kpi .s` outranked `.up`/`.down`, so every KPI line
  meant to read green (ahead) or red (behind) was grey; it is fixed for every page.
- FEAT-40's graph workspace remains built and tested, but it is no longer what a client sees.
