/* The workspace's “Bảng số liệu” (UX_TOOLBAR_PLAN T3+T4): the client's dashboard where the graph is — Chi tiết's
   blocks led by the overview (net worth with its tiers, allocation with profit against cost, the portfolio's profit
   and loss), then cash flow over time and the month's money in and out (Toàn cảnh's), risk, the reserve and the
   policy items (business feedback 2026-10-22: the overview first, cash flow second). It replaces the client's Toàn
   cảnh and Chi tiết sheets; the drawing is pages/detail.js (ctx.board), which the staff's pages keep using as they are. */
import {esc} from "../core/core.js";
import {render} from "../pages/detail.js?v=20261024d2";
import {href} from "./lenses.js?v=20261024d2";

export function mount(el, {client, scope}) {
  let key = null, board = {}, loading = null;

  function load() {
    const k = `${client()}|${scope()}`;
    if (k === key && loading) return loading;
    key = k;
    board = {};
    el.innerHTML = `<div class="small muted">Đang tải…</div>`;
    const ctx = {client, scope, role: "client", href, board, go: () => { key = null; return load(); }};  // a horizon button: drawn again
    loading = render(el, ctx).catch((e) => { key = null; loading = null; el.innerHTML = `<div class="small muted">Không tải được số liệu: ${esc(e.message)}</div>`; });
    return loading;
  }

  return {
    load,
    /* a section (cash, alloc, pnl, month, nw, risk, liq) at the top of the view (the view scrolls; on a phone, the page) */
    at(part, smooth) {
      const s = part && el.querySelector(`#d-${part}`);
      if (!s) return;
      const behavior = smooth ? "smooth" : "auto";
      if (el.scrollHeight > el.clientHeight + 1) el.scrollTo({top: el.scrollTop + s.getBoundingClientRect().top - el.getBoundingClientRect().top - 8, behavior});
      else {  // a phone: the page scrolls, under the header
        const top = document.querySelector(".shell-top");
        scrollTo({top: scrollY + s.getBoundingClientRect().top - Math.max(0, top ? top.getBoundingClientRect().bottom : 0) - 8, behavior});
      }
    },
    /* the month's flows at a month (a feed item's “Xem dòng tiền”) */
    month(m) { return board.month ? board.month.pick(m) : null; },
    /* the chart again at the width it is shown at */
    resize() { if (board.redraw && !el.hidden) board.redraw(); },
    reset() { key = null; loading = null; },
  };
}
