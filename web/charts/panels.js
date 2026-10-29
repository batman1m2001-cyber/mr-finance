/* The two money panels the business reads first (owner, 2026-10-21): allocation with profit against cost, and cash
   flow — six months past and 12/24/36 ahead, with the large payments and the recurring items. One drawing for both
   places they show: Chi tiết (pages/detail.js) and the workspace's “Dòng tiền & phân bổ” view (workspace/money.js).
   Both take the dashboard (POST /api/dashboard, with ``months`` for the cash-flow horizon). */
import {n, $, esc, pct, vnd} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {hover} from "./charts.js";
import {cashSeries, cashflow, monthName} from "./money.js?v=20261016r4";

// each class's colour on the allocation's bar, legend and icons (the muted --ac-* palette, business feedback 2026-10-29)
export const GROUP_COLOR = {
  "Bất động sản": "var(--ac-property)", "Cổ phiếu": "var(--ac-stock)", "Tiền & tiền gửi": "var(--ac-cash)", "Vàng": "var(--ac-gold)",
  "Chứng chỉ quỹ": "var(--ac-fund)", "Cổ phần DN": "var(--s6)", "Trái phiếu": "var(--ac-bond)", "Tài sản số": "var(--s8)",
  "Bảo hiểm": "var(--ac-insurance)",
};
const GROUP_ICON = {"Bất động sản": "home", "Cổ phiếu": "stock", "Tiền & tiền gửi": "bank", "Vàng": "gold", "Chứng chỉ quỹ": "fund",
  "Cổ phần DN": "business", "Trái phiếu": "bond", "Tài sản số": "crypto", "Bảo hiểm": "shield"};
export const PAST = 6;

// how soon each group turns into cash, the quickest first (business feedback 2026-10-29: cash and deposits lead)
const LIQUIDITY = ["Tiền & tiền gửi", "Cổ phiếu", "Chứng chỉ quỹ", "Vàng", "Trái phiếu", "Tài sản số", "Bảo hiểm", "Cổ phần DN", "Bất động sản"];
const liquidity = (g) => (LIQUIDITY.includes(g) ? LIQUIDITY.indexOf(g) : LIQUIDITY.length);

/* allocation: a 100% stacked bar and the table with profit against cost, the groups by liquidity under Tài sản, each
   debt under Khoản nợ, and the totals, into ``el`` (business feedback 2026-10-29: the bar reads easier than a donut) */
export function drawAlloc(el, d) {
  const rows = [...d.allocation].sort((a, b) => liquidity(a.group) - liquidity(b.group)), assets = d.net_worth.assets;
  const debts = (d.holdings || []).filter(h => h.kind === "liability").sort((a, b) => b.value - a.value);
  const nw = d.net_worth;
  const debtRow = (h) => {
    const pay = (h.detail || {}).monthly_payment;
    return `<tr><td><span class="ic-chip sm" style="--tone:var(--critical)">${icon(h.class === "card" ? "card" : "loan", {size: 12})}</span> ${esc(h.name)}${pay ? `<div class="small muted"><span>Trả nợ / tháng</span>: ${n(vnd(pay), "holding.terms")}</div>` : ""}</td>
      <td class="r down">−${n(vnd(h.value), "holding.value")}</td><td class="r">${n(pct(h.value / (assets || 1), false, 1), "class.share", {value: vnd(h.value), assets: vnd(assets)})}</td><td class="r"><span class="muted">—</span></td></tr>`;
  };
  const total = rows.reduce((x, a) => x + a.value, 0) || 1;
  const head = (cls, label) => `<tr class="secrow ${cls}"><th colspan="4">${label} <span class="small">tỷ trọng: % tổng tài sản</span></th></tr>`;
  el.innerHTML = `<div class="allocbox">
    <div class="stack100" role="img" aria-label="Phân bổ tài sản">${rows.map(a => `<span class="sb" data-key="${esc(a.group)}" style="flex:${a.value / total} 1 0;background:${GROUP_COLOR[a.group] || "var(--other)"}">${a.value / total >= 0.08 ? `<span>${esc(a.group)}</span> <b>${pct(a.share, false, 0)}</b>` : ""}</span>`).join("")}</div>
    <div class="legend mt-xs">${rows.map(a => `<span><i style="background:${GROUP_COLOR[a.group] || "var(--other)"}"></i>${esc(a.group)}</span>`).join("")}</div>
    <div class="scrollx mt"><table class="table alloctable"><thead><tr><th>Loại tài sản</th><th class="r">Giá trị hiện tại</th><th class="r">Tỷ trọng</th><th class="r">Lãi/lỗ</th></tr></thead>
    <tbody>${head("asset", "Tài sản")}
    ${rows.map(a => `<tr><td><span class="ic-chip sm" style="--tone:${GROUP_COLOR[a.group] || "var(--other)"}">${icon(GROUP_ICON[a.group] || "wallet", {size: 12})}</span> ${esc(a.group)}</td>
      <td class="r">${n(vnd(a.value), "class.value")}</td><td class="r"><b>${n(pct(a.share, false, a.share < 0.1 ? 1 : 0), "class.share", {value: vnd(a.value), assets: vnd(assets)})}</b></td>
      <td class="r">${a.return == null ? `<span class="muted" title="Chưa có giá vốn">—</span>` : `<span class="${a.return >= 0 ? "up" : "down"}" title="${vnd(a.pnl, true)} so với giá vốn">${n(pct(a.return, true), "class.return", {pnl: vnd(a.pnl, true)})}</span>`}</td></tr>`).join("")}</tbody>
    ${debts.length ? `<tbody>${head("debt", "Khoản nợ")}${debts.map(debtRow).join("")}</tbody>` : ""}
    <tfoot><tr><td>Tổng tài sản</td><td class="r">${n(vnd(nw.assets), "assets.total")}</td><td></td><td></td></tr>
      <tr><td>Tổng nợ</td><td class="r">${nw.liabilities ? "−" : ""}${n(vnd(nw.liabilities), "liabilities.total")}</td><td></td><td></td></tr>
      <tr class="total"><td><b>Tài sản ròng</b></td><td class="r"><b>${n(vnd(nw.value), "net_worth", {assets: vnd(nw.assets), liabilities: vnd(nw.liabilities)})}</b></td><td></td><td></td></tr></tfoot></table></div></div>`;
  // a label that does not fit its segment is hidden, not clipped (after the English is in: next frame); the legend
  // still names it
  requestAnimationFrame(() => { for (const s of el.querySelectorAll(".sb")) if (s.scrollWidth > s.clientWidth + 1) s.replaceChildren(); });
  for (const s of el.querySelectorAll(".sb")) {
    const a = rows.find(x => x.group === s.dataset.key);
    if (a) hover(s, `<b>${esc(a.group)}</b><br>${vnd(a.value)} · ${pct(a.share)}`);
  }
}

/* the cash-flow panel's inside: heading with the 12/24/36 switch, legend, the chart's host (#cash), large payments
   and recurring items; the chart itself is drawn by drawCash once the host has its width */
export function cashBody(cf, months) {
  return `<h3>Dòng tiền · ${PAST} tháng qua và ${cf.months.length} tháng tới <span class="hint">dự báo ${cf.months.length} tháng tới: vào ${n(vnd(cf.total_in), "cashflow.forecast", {months: String(cf.months.length)})} · ra ${n(vnd(cf.total_out), "cashflow.forecast", {months: String(cf.months.length)})}</span>
      <span class="seg" role="group" aria-label="Số tháng" style="margin-left:auto">${[12, 24, 36].map(m => `<button type="button" data-months="${m}" aria-pressed="${months === m}">${m} tháng</button>`).join("")}</span></h3>
    <div class="legend"><span><i style="background:var(--in)"></i>Tiền vào</span><span><i style="background:var(--out)"></i>Tiền ra</span>
      <span><i style="background:var(--in);opacity:.42"></i><i style="background:var(--out);opacity:.42"></i>Dự báo (màu nhạt)</span><span><b class="down">⚠</b> Khoản phải trả lớn</span></div>
    <div id="cash" class="mt"></div>
    <div class="cols mt">
      <div class="c6"><div class="subhead">Khoản phải trả lớn</div>${cf.large.length ? `<ul class="warns">${cf.large.map(l => `<li>${icon("alert", {size: 14})}<span><b>${monthName(l.month)}</b> · ${esc(l.label)} · ${n(vnd(l.amount), "cashflow.large", {month: monthName(l.month)})}</span></li>`).join("")}</ul>` : `<p class="small muted">Không có khoản lớn nào trong ${cf.months.length} tháng tới.</p>`}</div>
      <div class="c6"><div class="subhead">Khoản định kỳ tìm thấy trong giao dịch</div>
        <div class="list">${cf.recurring.map(r => `<div class="kv"><span><span class="legend-dot" style="background:${r.direction === "in" ? "var(--in)" : "var(--out)"}"></span> ${esc(r.label)} <span class="muted small">· ${r.cadence === "monthly" ? "hằng tháng" : "theo kỳ"}</span></span><b>${n(`${r.direction === "in" ? "+" : "−"}${vnd(r.amount)}`, "cashflow.recurring")}</b></div>`).join("")}</div></div>
    </div>`;
}

/* the chart, at the width its host is shown at (nothing while the host is hidden) */
export function drawCash(box, cf) {
  const host = $("#cash", box);
  if (host && host.clientWidth) host.replaceChildren(cashflow(cashSeries(cf, PAST, cf.months.length), cf.large, host.clientWidth));
}
