/* The workspace's “Dòng tiền & phân bổ” view (owner, 2026-10-21): the cash flow over time and the allocation with
   profit against cost, where the graph is — the two blocks the business reads first, one click from the overview
   (the view switch, or the strip's cash-flow and allocation cards). The drawing is Chi tiết's (charts/panels.js); the
   horizon (12/24/36 months) is Chi tiết's too, remembered for the session. */
import {$, esc, post} from "../core/core.js";
import {cashBody, drawAlloc, drawCash} from "../charts/panels.js?v=20261021m1";

const store = (k, v) => { try { if (v === undefined) return sessionStorage.getItem(k); sessionStorage.setItem(k, v); } catch (_) { /* private mode */ } return null; };

export function mount(el, {client, scope}) {
  let key = null, d = null;

  function draw() {
    const months = Number(store("mf.detail.months")) || 12;
    el.innerHTML = `<div class="cols">
      <div class="panel c12" id="ws-cash">${cashBody(d.cashflow, months)}</div>
      <div class="panel c12"><h3>Phân bổ tài sản <span class="hint">lãi/lỗ: % so với giá vốn · giá ngày ${esc(d.as_of)}</span></h3><div id="ws-alloc"></div></div>
    </div>`;
    drawAlloc($("#ws-alloc", el), d);
    drawCash(el, d.cashflow);
    for (const b of el.querySelectorAll("[data-months]")) b.onclick = () => { store("mf.detail.months", b.dataset.months); key = null; load(); };
  }

  async function load() {
    const months = Number(store("mf.detail.months")) || 12;
    const k = `${client()}|${scope()}|${months}`;
    if (k === key && d) { draw(); return; }
    key = k;
    el.innerHTML = `<div class="small muted">Đang tải…</div>`;
    try {
      const {dashboard} = await post("/api/dashboard", {client_id: client(), scope: scope(), months});
      if (k !== key) return;
      d = dashboard;
      draw();
    } catch (e) { key = null; el.innerHTML = `<div class="small muted">Không tải được số liệu: ${esc(e.message)}</div>`; }
  }

  return {
    load,
    /* the chart again at the width it is shown at */
    resize() { if (d && !el.hidden) drawCash(el, d.cashflow); },
    reset() { key = null; },
  };
}
