/* The workspace's bottom strip (FEAT-40, OWN-GW-04): the Toàn cảnh cards, compact — net worth and its month change,
   the month's cash flow with six months, the allocation, the stress loss against the limit, the reserve. The same
   numbers and “Cách tính” as Toàn cảnh (POST /api/dashboard, POST /api/flows); a card focuses its lens, but the cash-flow and
   allocation cards open the “Dòng tiền & phân bổ” view (owner, 2026-10-21); “Thu gọn”
   folds the strip to one line and is remembered. */
import {n, nAttrs, CLASS_COLOR, ASSET_CLASS, $, esc, pct, post, signClass, vnd} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {donut, gauge, ring} from "../charts/mini.js?v=20261016r2";

const STATUS = {ok: ["good", "An toàn"], near: ["warn", "Gần ngưỡng"], over: ["bad", "Vượt ngưỡng"], low: ["warn", "Thấp"], critical: ["bad", "Rất thấp"]};
const MONTH = (m) => `T${Number(m.slice(5))}/${m.slice(2, 4)}`;
const GROUP = {cash: "deposit"};

export function mount(el, {client, scope, lens, money}) {
  let key = null, data = null, folded = false;
  try { folded = localStorage.getItem("mf.ws.strip") === "folded"; } catch (_) { /* private mode */ }
  el.innerHTML = `<div class="ws-strip-h"><b>${icon("activity", {size: 14})} Tổng quan nhanh</b>
      <button type="button" class="linkbtn small" id="ws-strip-fold" aria-expanded="${!folded}" aria-controls="ws-strip-b">${folded ? "Mở rộng" : "Thu gọn"}</button></div>
    <div class="ws-strip-b" id="ws-strip-b"${folded ? " hidden" : ""}></div>`;
  const body = $("#ws-strip-b", el);
  el.classList.toggle("folded", folded);
  $("#ws-strip-fold", el).onclick = () => {
    folded = !folded;
    body.hidden = folded;
    el.classList.toggle("folded", folded);
    $("#ws-strip-fold", el).textContent = folded ? "Mở rộng" : "Thu gọn";
    $("#ws-strip-fold", el).setAttribute("aria-expanded", String(!folded));
    try { localStorage.setItem("mf.ws.strip", folded ? "folded" : ""); } catch (_) { /* private mode */ }
    window.dispatchEvent(new Event("resize"));  // the graph takes the room back
  };

  const pill = (s) => `<span class="pill ${(STATUS[s] || [""])[0]}">${esc((STATUS[s] || ["", s])[1])}</span>`;
  const card = (k, lensId, ic, tone, label, value, sub, viz = "", part = "") => `
    <button type="button" class="kpi scard" data-lens="${lensId}" ${k ? `data-focus="${k}"` : ""}${part ? ` data-money="${part}"` : ""} aria-label="${esc(label)}: ${part ? "xem Dòng tiền &amp; phân bổ" : "mở góc nhìn"}">
      <span class="pc-head"><span class="ic-chip sm" style="--tone:${tone}">${icon(ic, {size: 13})}</span><span class="k">${label}</span></span>
      <span class="pc-body"><span class="pc-main"><span class="v">${value}</span><span class="s">${sub}</span></span>${viz ? `<span class="pc-viz">${viz}</span>` : ""}</span></button>`;

  function draw() {
    if (!data) { body.innerHTML = `<div class="small muted">Đang tải…</div>`; return; }
    const {d, f} = data, nw = d.net_worth, liq = d.liquidity, rk = d.risk;
    const hist = (d.cashflow && d.cashflow.history) || [];
    const at = hist.findIndex(m => m.month === f.month), end = at >= 0 ? at : hist.length - 1;
    const last = hist.slice(Math.max(0, end - 5), end + 1), maxIO = Math.max(1, ...last.flatMap(m => [m.in, m.out]));
    const io = last.length ? `<svg class="mini" width="84" height="30" viewBox="0 0 84 30" role="img" aria-label="Tiền vào và ra ${last.length} tháng gần nhất">${last.map((m, i) => {
      const x = i * 14, hi = Math.max(1.5, (m.in / maxIO) * 28), ho = Math.max(1.5, (m.out / maxIO) * 28), on = m.month === f.month ? 1 : 0.4;
      return `<rect x="${x}" y="${30 - hi}" width="5" height="${hi}" rx="1.5" fill="var(--in)" opacity="${on}"/><rect x="${x + 6}" y="${30 - ho}" width="5" height="${ho}" rx="1.5" fill="var(--out)" opacity="${on}"/>`;
    }).join("")}</svg>` : "";
    const groups = {};
    for (const h of d.holdings.filter(h => h.kind === "asset" && h.value > 0)) { const g = GROUP[h.class] || h.class; groups[g] = (groups[g] || 0) + h.value; }
    const assets = Object.values(groups).reduce((a, v) => a + v, 0);
    const top = Object.entries(groups).sort((a, b) => b[1] - a[1]);
    const gname = (g) => (g === "deposit" ? "Tiền & tiền gửi" : ASSET_CLASS[g] || g);
    const months = liq.months >= 24 ? Math.floor(liq.months / 12) + " năm" : Math.round(liq.months) + " tháng";
    const share = assets ? liq.value / assets : 0;
    const chg = {now: vnd(nw.value), prev: vnd(nw.prev_value)};
    const fio = {total_in: vnd(f.total_in), total_out: vnd(f.total_out)};
    body.innerHTML = [
      card("kpi:net_worth", "tong-quan", "wallet", "var(--accent)", "Tài sản ròng", n(vnd(nw.value), "net_worth", {assets: vnd(nw.assets), liabilities: vnd(nw.liabilities)}),
        `<span class="${signClass(nw.month_change)}">${nw.month_change >= 0 ? "▲" : "▼"} ${n(pct(nw.month_change_pct, true), "net_worth.month_change", chg)}</span> so với tháng trước`),
      card(`flow:${f.month}`, "dong-tien", "flow", "var(--in)", `Dòng tiền ${MONTH(f.month)}`, n(`${f.left >= 0 ? "+" : "−"}${vnd(Math.abs(f.left))}`, "flow.left", fio),
        `vào ${n(vnd(f.total_in), "flow.in")} · ra ${n(vnd(f.total_out), "flow.out")}`, io, "cash"),
      card("", "tai-san", "layers", "var(--s1)", "Phân bổ tài sản", n(vnd(assets), "assets.total"),
        top.slice(0, 2).map(([g, v]) => `${esc(gname(g))} ${pct(v / assets, false, 0)}`).join(" · "),
        donut(top.map(([g, v]) => ({key: g, value: v, color: CLASS_COLOR[g] || "var(--other)", label: `${gname(g)}: ${vnd(v)}`})), {size: 46, stroke: 8, how: nAttrs("assets.total")}), "alloc"),
      card("kpi:risk", "rui-ro", "shield", "var(--warning)", "Rủi ro hiện tại", n(pct(rk.current), "risk.current", {loss: vnd(rk.stress_loss), net_worth: vnd(nw.value)}),
        `ngưỡng ${n(pct(rk.limit, false, 0), "risk.limit")} ${pill(rk.status)}`,
        gauge(rk.current, rk.limit, {status: rk.status, label: `Sụt giảm ước tính ${pct(rk.current)} so với ngưỡng ${pct(rk.limit, false, 0)}`})),
      card("kpi:liquidity", "dong-tien", "bank", "var(--s3)", "Thanh khoản dự phòng", n(vnd(liq.value), "liquidity.value", {count: String(liq.items.length)}),
        `đủ chi ${n(months, "liquidity.months", {value: vnd(liq.value), spending: vnd(liq.spending_monthly)})} ${pill(liq.status)}`,
        ring(share, {size: 40, color: "var(--s3)", label: `${pct(share, false, 0)} tổng tài sản`})),
    ].join("");
    for (const b of body.querySelectorAll("[data-lens]")) b.addEventListener("click", (e) => { if (!e.target.closest("[data-metric]")) b.dataset.money ? money(b.dataset.money) : lens(b.dataset.lens); });
  }

  return {
    async load() {
      const k = `${client()}|${scope()}`;
      if (k === key && data) return;
      key = k; data = null; draw();
      try {
        const [{dashboard: d}, {flows: f}] = await Promise.all([post("/api/dashboard", {client_id: client(), scope: scope()}), post("/api/flows", {client_id: client(), scope: scope()})]);
        if (k !== key) return;
        data = {d, f}; draw();
      } catch (e) { body.innerHTML = `<div class="small muted">Không tải được số liệu: ${esc(e.message)}</div>`; }
    },
    focus(lensId) { for (const b of body.querySelectorAll("[data-lens]")) b.classList.toggle("here", b.dataset.lens === lensId); },
    reset() { key = null; },
  };
}
