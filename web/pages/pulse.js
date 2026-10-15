/* Toàn cảnh (redesign kit K2): Financial Pulse, Wealth Map and Money Flow on one page. The numbers are the
   dashboard's (POST /api/dashboard) and the month's transactions (POST /api/flows); nothing here is
   computed that the server did not return, except sums of what it returned. The full former overview
   stays one click away (“Chi tiết”). */
import {ASSET_CLASS, CLASS_COLOR, $, esc, pct, post, signClass, vnd} from "../core/core.js";
import {hover, sankey} from "../charts/charts.js";

const STATUS = {
  ok: ["good", "An toàn"], near: ["warn", "Gần ngưỡng"], over: ["bad", "Vượt ngưỡng"],
  low: ["warn", "Thấp"], critical: ["bad", "Rất thấp"],
};
const GROUP = {cash: "deposit"};  // cash and deposits are one group, as on the allocation table
const MONTH = (m) => `T${Number(m.slice(5))}/${m.slice(2, 4)}`;

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope();
  const state = {month: null};
  const [{dashboard: d}, first] = await Promise.all([
    post("/api/dashboard", {client_id: client, scope}),
    post("/api/flows", {client_id: client, scope}),
  ]);
  let f = first.flows;
  const nw = d.net_worth, liq = d.liquidity, rk = d.risk;
  const tile = (k, v, sub, cls = "") => `<div class="kpi"><div class="k">${k}</div><div class="v ${cls}">${v}</div><div class="s">${sub}</div></div>`;
  const badge = (s) => `<span class="badge ${(STATUS[s] || [""])[0]}">${esc((STATUS[s] || ["", s])[1])}</span>`;

  // Wealth Map: assets by class (cash folded into deposits), each opening to its holdings
  const groups = {};
  for (const h of d.holdings.filter(h => h.kind === "asset" && h.value > 0)) {
    const g = GROUP[h.class] || h.class;
    (groups[g] ||= {key: g, value: 0, items: []}).value += h.value;
    groups[g].items.push(h);
  }
  const map = Object.values(groups).sort((a, b) => b.value - a.value);
  const assets = map.reduce((a, g) => a + g.value, 0);
  const gname = (g) => (g === "deposit" ? "Tiền & tiền gửi" : ASSET_CLASS[g] || g);

  box.innerHTML = `
    <div class="cols">
      <div class="c12 kpis" id="kpis"></div>
      <div class="panel c5">
        <h3>Bản đồ tài sản <span class="hint">${vnd(assets)} tài sản · giá ngày ${esc(d.as_of)} · bấm một nhóm để xem từng khoản</span></h3>
        <div class="wmap" id="wmap" role="list"></div>
        <div id="wmap-rows" class="wmap-rows"></div>
        <div class="footnote">Nợ ${vnd(nw.liabilities)} không nằm trong bản đồ; tài sản ròng = tài sản − nợ.</div>
      </div>
      <div class="panel c7">
        <h3>Dòng tiền <span class="hint" id="flow-of"></span>
          <select id="month" aria-label="Tháng" style="margin-left:auto"></select></h3>
        <div id="sankey"></div>
        <div id="flow-rows" class="mt"></div>
        <div class="footnote">Chỉ từ giao dịch tài khoản; không suy diễn dòng tiền đầu tư. Bấm một dải để xem các giao dịch tạo nên nó.</div>
      </div>
      <div class="c12 small"><a href="${ctx.href(ctx.role === "client" ? "tong-quan" : "khach-hang", ctx.role === "client" ? "chi-tiet" : "tong-quan")}">Xem đầy đủ: lãi/lỗ, rủi ro, thanh khoản, dòng tiền 12 tháng, tin nổi bật →</a></div>
    </div>`;

  const drawKpis = () => {
    $("#kpis", box).innerHTML = [
      tile("Tài sản ròng", vnd(nw.value), `<span class="${signClass(nw.month_change)}">${vnd(nw.month_change, true)} (${pct(nw.month_change_pct, true)})</span> so với tháng trước`),
      tile(`Tiền vào ${MONTH(f.month)}`, vnd(f.total_in), `${f.inflow.length} nguồn`),
      tile(`Tiền ra ${MONTH(f.month)}`, vnd(f.total_out), `${f.outflow.length} nhóm chi`),
      tile(f.left >= 0 ? "Còn lại" : "Thiếu hụt", vnd(Math.abs(f.left)), f.total_in ? `${pct(f.left / f.total_in)} tiền vào` : "—", f.left >= 0 ? "up" : "down"),
      tile("Thanh khoản dự phòng", vnd(liq.value), `đủ chi ${liq.months >= 24 ? Math.floor(liq.months / 12) + " năm" : Math.round(liq.months) + " tháng"} ${badge(liq.status)}`),
      tile("Rủi ro khi thị trường xấu", pct(rk.current), `ngưỡng ${pct(rk.limit, false, 0)} ${badge(rk.status)}`),
    ].join("");
  };

  const drawMap = () => {
    const bar = $("#wmap", box);
    bar.innerHTML = map.map(g => `<button type="button" class="wseg" role="listitem" data-g="${esc(g.key)}" style="flex:${g.value};background:${CLASS_COLOR[g.key] || "var(--other)"}" aria-label="${esc(gname(g.key))}: ${vnd(g.value)}, ${pct(g.value / assets)}"></button>`).join("");
    const legend = map.map(g => `<button type="button" class="wrow" data-g="${esc(g.key)}"><i style="background:${CLASS_COLOR[g.key] || "var(--other)"}"></i><span>${esc(gname(g.key))}</span><span class="num">${vnd(g.value)}</span><b class="num">${pct(g.value / assets, false, 0)}</b></button>`).join("");
    const rows = $("#wmap-rows", box);
    rows.innerHTML = `<div class="wlegend">${legend}</div><div id="wmap-open"></div>`;
    const open = (key) => {
      const g = groups[key];
      for (const b of box.querySelectorAll("[data-g]")) b.setAttribute("aria-pressed", String(b.dataset.g === key));
      $("#wmap-open", box).innerHTML = `<table class="table mt"><caption class="small muted" style="text-align:left">${esc(gname(key))} · ${g.items.length} khoản</caption><tbody>${
        g.items.sort((a, b) => b.value - a.value).map(h => `<tr><td>${esc(h.name)}${scope === "family" && h.owner_name ? `<div class="small muted">${esc(h.owner_name)}</div>` : ""}</td><td class="r num">${vnd(h.value)}</td><td class="r num muted">${pct(h.value / assets)}</td></tr>`).join("")}</tbody></table>`;
    };
    for (const b of box.querySelectorAll("[data-g]")) {
      b.onclick = () => open(b.dataset.g);
      if (b.classList.contains("wseg")) { const g = groups[b.dataset.g]; hover(b, `<b>${esc(gname(g.key))}</b><br>${vnd(g.value)} · ${pct(g.value / assets)}`); }
    }
  };

  const drawRows = (b, side) => {
    const el = $("#flow-rows", box);
    if (!b) {  // the table view of the chart: every band and its total
      const line = (x, sign) => `<tr class="click" data-cat="${esc(x.category)}" data-side="${sign}"><td>${esc(x.label)}</td><td class="r num">${sign === "in" ? "+" : "−"}${vnd(x.amount)}</td><td class="r small muted">${x.rows.length} giao dịch</td></tr>`;
      el.innerHTML = `<table class="table"><tbody>${f.inflow.map(x => line(x, "in")).join("")}${f.outflow.map(x => line(x, "out")).join("")}
        <tr><td><b>${f.left >= 0 ? "Còn lại" : "Thiếu hụt"}</b></td><td class="r num"><b class="${f.left >= 0 ? "up" : "down"}">${vnd(f.left, true)}</b></td><td></td></tr></tbody></table>`;
      for (const r of el.querySelectorAll("[data-cat]")) r.onclick = () => drawRows((r.dataset.side === "in" ? f.inflow : f.outflow).find(x => x.category === r.dataset.cat), r.dataset.side);
      return;
    }
    if (!b.rows) {  // Còn lại / Thiếu hụt: a difference, not rows
      el.innerHTML = `<p class="small">${esc(b.label)} = tiền vào ${vnd(f.total_in)} − tiền ra ${vnd(f.total_out)} = <b>${vnd(f.left, true)}</b>. <button type="button" class="linkbtn small" id="all-rows">Xem bảng tổng</button></p>`;
    } else {
      el.innerHTML = `<div class="row"><b>${esc(b.label)}</b><span class="muted small">${side === "in" ? "tiền vào" : "tiền ra"} · ${b.rows.length} giao dịch · ${vnd(b.amount)}</span><button type="button" class="linkbtn small" id="all-rows" style="margin-left:auto">← Bảng tổng</button></div>
        <table class="table"><tbody>${b.rows.map(r => `<tr><td class="num">${esc(r.date)}</td><td>${esc(r.desc)}${scope === "family" ? `<div class="small muted">${esc(r.owner_name)}</div>` : ""}</td><td class="r num">${vnd(r.amount)}</td></tr>`).join("")}</tbody></table>`;
    }
    $("#all-rows", box).onclick = () => drawRows(null);
  };

  const drawFlow = () => {
    $("#flow-of", box).textContent = `${MONTH(f.month)} · ${scope === "family" ? "gia đình" : "cá nhân"} · ${f.rows} giao dịch`;
    const sel = $("#month", box);
    sel.innerHTML = [...f.months].reverse().map(m => `<option value="${m}" ${m === f.month ? "selected" : ""}>${MONTH(m)}</option>`).join("");
    sel.onchange = async () => {
      try { f = (await post("/api/flows", {client_id: client, scope, month: sel.value})).flows; } catch (e) { $("#flow-rows", box).textContent = e.message; return; }
      drawKpis(); drawFlow();
    };
    sankey($("#sankey", box), f, {label: `Dòng tiền ${MONTH(f.month)}`, onPick: drawRows});
    drawRows(null);
  };

  drawKpis(); drawMap(); drawFlow();
}
