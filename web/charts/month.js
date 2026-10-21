/* One month's money in and out (UX_TOOLBAR_PLAN T4): the sankey of the month's transactions by category, its ratios,
   the table under it and a band's transactions — Toàn cảnh's Money Flow, moved so the client's dashboard has it
   (Toàn cảnh stays the staff's page and keeps its own copy). Numbers from POST /api/flows only. */
import {n, $, esc, pct, post, vnd} from "../core/core.js";
import {sankey} from "./charts.js";

const MONTH = (m) => `T${Number(m.slice(5))}/${m.slice(2, 4)}`;

/* the panel's inside, into ``el``; ``first`` is POST /api/flows's ``flows``; returns {pick(month)} */
export function monthFlows(el, {client, scope, first}) {
  let f = first;
  el.innerHTML = `<h3>Tiền vào và ra trong tháng <span class="hint" id="mf-of"></span>
      <select id="mf-month" aria-label="Tháng" style="margin-left:auto"></select></h3>
    <div id="mf-sankey"></div>
    <div class="ratios" id="mf-ratios"></div>
    <div id="mf-rows" class="mt"></div>
    <div class="footnote">Chỉ từ giao dịch tài khoản; không suy diễn dòng tiền đầu tư. Bấm một dải để xem các giao dịch tạo nên nó.</div>`;

  const rowsOf = (b, side) => {
    const box = $("#mf-rows", el);
    if (!b) {  // the table view of the chart: every band and its total
      const line = (x, sign) => `<tr class="click" data-cat="${esc(x.category)}" data-side="${sign}" data-focus="flow:${f.month}:${sign}:${esc(x.category)}"><td>${esc(x.label)}</td><td class="r num">${n(`${sign === "in" ? "+" : "−"}${vnd(x.amount)}`, "flow.band", {rows: String(x.rows.length)})}</td><td class="r small muted">${x.rows.length} giao dịch</td></tr>`;
      box.innerHTML = `<table class="table"><tbody>${f.inflow.map(x => line(x, "in")).join("")}${f.outflow.map(x => line(x, "out")).join("")}
        <tr><td><b>${f.left >= 0 ? "Còn lại" : "Thiếu hụt"}</b></td><td class="r num"><b class="${f.left >= 0 ? "up" : "down"}">${n(vnd(f.left, true), "flow.left", {total_in: vnd(f.total_in), total_out: vnd(f.total_out)})}</b></td><td></td></tr></tbody></table>`;
      for (const r of box.querySelectorAll("[data-cat]")) r.onclick = () => rowsOf((r.dataset.side === "in" ? f.inflow : f.outflow).find(x => x.category === r.dataset.cat), r.dataset.side);
      return;
    }
    if (!b.rows) {  // Còn lại / Thiếu hụt: a difference, not rows
      box.innerHTML = `<p class="small">${esc(b.label)} = tiền vào ${n(vnd(f.total_in), "flow.in")} − tiền ra ${n(vnd(f.total_out), "flow.out")} = <b>${n(vnd(f.left, true), "flow.left", {total_in: vnd(f.total_in), total_out: vnd(f.total_out)})}</b>. <button type="button" class="linkbtn small" id="mf-all">Xem bảng tổng</button></p>`;
    } else {
      box.innerHTML = `<div class="row"><b>${esc(b.label)}</b><span class="muted small">${side === "in" ? "tiền vào" : "tiền ra"} · ${b.rows.length} giao dịch · ${n(vnd(b.amount), "flow.band", {rows: String(b.rows.length)})}</span><button type="button" class="linkbtn small" id="mf-all" style="margin-left:auto">← Bảng tổng</button></div>
        <table class="table"><tbody>${b.rows.map(r => `<tr><td class="num">${esc(r.date)}</td><td>${esc(r.desc)}${scope === "family" ? `<div class="small muted">${esc(r.owner_name)}</div>` : ""}</td><td class="r num">${n(vnd(r.amount), "transaction.amount", {date: r.date})}</td></tr>`).join("")}</tbody></table>`;
    }
    $("#mf-all", el).onclick = () => rowsOf(null);
  };
  const ratios = () => {
    const rate = f.total_in ? f.left / f.total_in : null;
    const big = f.outflow[0];
    $("#mf-ratios", el).innerHTML = [
      [f.left >= 0 ? "Tỷ lệ để dành" : "Chi vượt thu", rate == null ? "—" : n(pct(Math.abs(rate), false, 0), "flow.saving_rate", {left: vnd(f.left, true), total_in: vnd(f.total_in)}), f.left >= 0 ? "up" : "down"],
      ["Tiền ra / tiền vào", f.total_in ? n(pct(f.total_out / f.total_in, false, 0), "flow.out_in", {total_out: vnd(f.total_out), total_in: vnd(f.total_in)}) : "—", ""],
      ["Nhóm chi lớn nhất", big ? `${esc(big.label)} · ${n(vnd(big.amount), "flow.band", {rows: String(big.rows.length)})}` : "—", ""],
    ].map(([k, v, c]) => `<div class="ratio"><span class="k">${k}</span><b class="${c}">${v}</b></div>`).join("");
  };
  const draw = () => {
    el.dataset.focus = `flow:${f.month}`;
    $("#mf-of", el).textContent = `${MONTH(f.month)} · ${scope === "family" ? "gia đình" : "cá nhân"} · ${f.rows} giao dịch`;
    const sel = $("#mf-month", el);
    sel.innerHTML = [...f.months].reverse().map(m => `<option value="${m}" ${m === f.month ? "selected" : ""}>${MONTH(m)}</option>`).join("");
    sel.onchange = () => pick(sel.value);
    sankey($("#mf-sankey", el), f, {label: `Dòng tiền ${MONTH(f.month)}`, onPick: rowsOf});
    ratios();
    rowsOf(null);
  };
  async function pick(month) {
    if (month && month !== f.month) {
      try { f = (await post("/api/flows", {client_id: client, scope, month})).flows; } catch (e) { $("#mf-rows", el).textContent = e.message; return; }
    }
    draw();
  }
  draw();
  return {pick};
}
