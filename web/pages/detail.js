/* Chi tiết (SCR-CL-01): the full former overview, rebuilt in the board's look (UI redesign R3). Every block of
   the pre-redesign page is here: net worth with the members it counts, assets by the three tiers of sources (each
   opening onto its sources), allocation with profit against cost and the debts under it, risk against the
   accepted drawdown with concentration warnings, the liquidity reserve, cash flow (six months past, 12/24/36 ahead) with large payments and recurring items. Assets, debt and net worth are three
   tiles; the portfolio's profit and the policy items left it (business feedback 2026-10-29). The client's
   workspace draws it as its dashboard (ctx.board, UX_TOOLBAR_PLAN T3+T4): the overview first, then cash flow and the
   month's flows. */
import {n, nAttrs, $, esc, pct, post, vnd} from "../core/core.js";
import {CLASS_ICON, icon} from "../core/icons.js?v=20261016r1";
import {gauge} from "../charts/mini.js?v=20261016r2";
import {monthsText} from "../charts/money.js?v=20261016r4";
import {cashBody, drawAlloc as allocInto, drawCash as cashInto} from "../charts/panels.js?v=20261021m1";
import {monthFlows} from "../charts/month.js?v=20261021t3";

const STATUS = {ok: ["good", "An toàn"], near: ["warn", "Gần ngưỡng"], over: ["bad", "Vượt ngưỡng"], low: ["warn", "Thấp"], critical: ["bad", "Rất thấp"]};
const TIERS = [
  {n: 1, title: "Our Wealth at Techcombank", vi: "Tại hệ sinh thái Techcombank", color: "var(--s1)", icon: "bank"},
  {n: 2, title: "Custody around the world", vi: "Lưu ký bên ngoài", color: "var(--s7)", icon: "link"},
  {n: 3, title: "Self-managed", vi: "Bạn tự quản lý", color: "var(--s4)", icon: "user"},
];
const pill = (s) => `<span class="pill ${(STATUS[s] || [""])[0]}">${(STATUS[s] || ["", s])[1]}</span>`;
const store = (k, v) => { try { if (v === undefined) return sessionStorage.getItem(k); sessionStorage.setItem(k, v); } catch (_) { /* private mode */ } return null; };

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope(), staff = ctx.role !== "client";
  const months = Number(store("mf.detail.months")) || 12;
  const [{dashboard: d}, fl] = await Promise.all([
    post("/api/dashboard", {client_id: client, scope, months}),
    ctx.board ? post("/api/flows", {client_id: client, scope}).catch((e) => ({error: e.message})) : null,
  ]);
  const nw = d.net_worth, rk = d.risk, lq = d.liquidity, cf = d.cashflow;
  const up = nw.month_change >= 0;
  const chg = {now: vnd(nw.value), prev: vnd(nw.prev_value)};
  const holdingsHref = staff ? ctx.href("khach-hang", "tai-san") : ctx.href("tai-san");
  const who = d.members.map(m => `<span class="chip">${esc(m.name)} · ${esc(m.relation)}</span>`).join("")
    + d.waiting.map(m => `<span class="chip" title="Chưa đồng ý chia sẻ dữ liệu">${esc(m.name)} · chưa đồng ý chia sẻ</span>`).join("");

  // the blocks; the client's dashboard (ctx.board, the workspace's Bảng số liệu) leads with the overview — net worth and
  // its sources, then allocation and profit and loss — and cash flow second (business feedback 2026-10-22: "the
  // overview must meet the eye first"), then the month's money in and out (Toàn cảnh's)
  const B = {
    hero: `      <div class="panel c12 nwhero" id="d-nw" data-focus="kpi:net_worth">
        <div>
          <div class="nwtiles">
            <div class="nwtile"><div class="pc-head"><span class="ic-chip sm" style="--tone:var(--s1)">${icon("wallet", {size: 14})}</span><span class="k">Tổng tài sản</span></div>
              <div class="v">${n(vnd(nw.assets), "assets.total")}</div></div>
            <div class="nwtile"><div class="pc-head"><span class="ic-chip sm" style="--tone:var(--critical)">${icon("loan", {size: 14})}</span><span class="k">Tổng nợ</span></div>
              <div class="v">${nw.liabilities ? "−" : ""}${n(vnd(nw.liabilities), "liabilities.total")}</div></div>
            <div class="nwtile main"><div class="pc-head"><span class="ic-chip sm" style="--tone:var(--accent)">${icon("target", {size: 14})}</span><span class="k">Tài sản ròng · ${d.scope === "family" ? "gia đình" : "cá nhân"}</span></div>
              <div class="v">${n(vnd(nw.value), "net_worth", {assets: vnd(nw.assets), liabilities: vnd(nw.liabilities)})}</div>
              <div class="small"><span class="${up ? "up" : "down"}">${up ? "▲" : "▼"} ${n(pct(nw.month_change_pct, true), "net_worth.month_change", chg)}</span> <span class="muted">so với tháng trước (${n(vnd(nw.month_change, true), "net_worth.month_change", chg)})</span></div></div>
          </div>
          <div class="small muted mt-xs">Tài sản ròng = tổng tài sản − tổng nợ · cập nhật ${esc(d.as_of)}</div>
          <div class="row tight mt">${who}</div>
        </div>
        <div id="srcmix"></div>
      </div>
    `,
    alloc: `      <div class="panel c12" id="d-alloc"><h3>Phân bổ tài sản và khoản nợ <span class="hint">xếp theo mức thanh khoản · lãi/lỗ: % so với giá vốn</span></h3><div id="alloc"></div></div>
    `,
    risk: `      <div class="panel c6" id="d-risk" data-focus="kpi:risk"><h3>Rủi ro</h3>
        ${d.profile.risk_profile ? `<div class="kv"><span>Hồ sơ rủi ro (bài test)</span><b>${esc(d.profile.risk_profile)} · ${esc(d.profile.risk_persona)}</b></div>` : `<p class="small muted" style="margin:0 0 8px">Chưa làm bài test rủi ro: ngưỡng lấy theo hồ sơ.</p>`}
        <div class="kv"><span>Ngưỡng sụt giảm chấp nhận</span><b>${n(pct(rk.limit, false, 0), "risk.limit")}</b></div>
        <div class="kv"><span>Mức sụt giảm ước tính khi thị trường xấu</span><b>${n(pct(rk.current), "risk.current", {loss: vnd(rk.stress_loss), net_worth: vnd(nw.value)})}</b></div>
        ${gauge(rk.current, rk.limit, {status: rk.status, max: Math.max(rk.limit * 1.6, rk.current * 1.1), label: `Sụt giảm ước tính ${pct(rk.current)} so với ngưỡng ${pct(rk.limit, false, 0)}`})}
        <div class="mt-xs">${pill(rk.status)} <span class="muted small">mất ${n(vnd(rk.stress_loss), "risk.loss")} trong kịch bản xấu</span></div>
        ${d.concentration.warnings.length ? `<ul class="warns">${d.concentration.warnings.map(w => `<li>${icon("alert", {size: 14})}<span data-explains>Tập trung: ${esc(w)}</span></li>`).join("")}</ul>` : `<p class="small muted">Không có khoản nào tập trung quá ngưỡng.</p>`}
      </div>
    `,
    liq: `      <div class="panel c6" id="d-liq" data-focus="kpi:liquidity"><h3>Thanh khoản dự phòng</h3>
        <div class="row spread"><span>${n(vnd(lq.value), "liquidity.value", {count: String(lq.items.length)})} tiền và tài sản rút được ngay</span><b>đủ chi ${n(monthsText(lq.months), "liquidity.months", {value: vnd(lq.value), spending: vnd(lq.spending_monthly)})} ${pill(lq.status)}</b></div>
        ${gauge(Math.min(lq.months, Math.max(12, Math.min(lq.months, 36))), 6, {status: lq.status === "ok" ? "ok" : lq.status === "low" ? "near" : "over", max: Math.max(12, Math.min(lq.months, 36)), label: `Đủ chi ${monthsText(lq.months)}, mốc an toàn 6 tháng`})}
        <div class="small muted">Chi tiêu ${n(vnd(lq.spending_monthly), "spending.monthly")}/tháng · mốc an toàn: 6 tháng</div>
      </div>
    `,
    cash: `      <div class="panel c12" id="d-cash">
        ${cashBody(cf, months)}
      </div>
    `,
    month: `<div class="panel c12" id="d-month"></div>`,
  };

  // a part of it as its own page (ctx.board.only: the client's Dòng tiền, B3.1): the other blocks are drawn as always,
  // out of sight, so every step below finds its element
  const only = ctx.board && ctx.board.only, shown = (k) => !only || only.includes(k);
  box.innerHTML = `
    <div class="cols">
${(ctx.board ? ["hero", "alloc", "cash", "month", "risk", "liq"] : ["hero", "alloc", "risk", "liq", "cash"]).map(k => (shown(k) ? B[k] : `<div hidden>${B[k]}</div>`)).join("")}
    </div>`;

  // assets by the tier of their source; a tier opens onto its sources
  let open = Number(store("mf.detail.tier")) || null;
  const drawTiers = () => {
    const total = nw.assets || 1;
    const tiers = TIERS.map(t => {
      const src = d.sources.filter(s => s.tier === t.n);
      return {...t, src, value: src.reduce((a, s) => a + s.assets, 0), on: src.filter(s => s.count).length};
    });
    const share = (v) => pct(v / total, false, v / total < 0.1 ? 1 : 0);
    $("#srcmix", box).innerHTML = `<div class="k">Tài sản theo nguồn dữ liệu <span class="hint">% tổng tài sản ${n(vnd(nw.assets), "assets.total")} · bấm để xem từng nguồn</span></div>
      <div class="sbar mt-xs">${tiers.filter(t => t.value > 0).map(t => `<button type="button" data-tier="${t.n}" style="flex:${t.value / total} 1 0;background:${t.color}" aria-label="${esc(t.vi)} ${share(t.value)}"></button>`).join("")}</div>
      <div class="tiers">${tiers.map(t => `<div class="tier${open === t.n ? " on" : ""}">
        <button type="button" class="tierhead" data-tier="${t.n}" aria-expanded="${open === t.n}">
          <span class="ic-chip sm" style="--tone:${t.color}">${icon(t.icon, {size: 13})}</span>
          <span class="pop-t"><b>${esc(t.vi)}</b><small><span lang="en">${esc(t.title)}</span> · ${t.on}/${t.src.length} nguồn đã kết nối</small></span>
          <span class="tv"><b>${n(share(t.value), "tier.value", {assets: vnd(nw.assets)})}</b><small class="muted">${n(vnd(t.value), "tier.value", {assets: vnd(nw.assets)})}</small></span>
          <span aria-hidden="true">${icon("chevron", {size: 14})}</span></button>
        ${open === t.n ? `<div class="tierlist">${t.src.map(s => `<div class="srcrow">
            <span class="${s.status === "connected" ? "up" : "muted"}" aria-hidden="true">${s.status === "connected" ? "✓" : "○"}</span>
            <span><b>${esc(s.label)}</b><div class="small muted">${esc(s.what)} · ${s.count ? `${s.count} khoản · ${s.trust.map(esc).join(", ")}` : "chưa có dữ liệu"}</div></span>
            <span class="r">${s.count ? `${n(vnd(s.assets - s.liabilities), "source.net")} <span class="muted small">· ${n(share(s.assets), "source.net")}</span>` : "—"}</span></div>`).join("")}
          <a class="small" href="${holdingsHref}">Xem từng khoản →</a></div>` : ""}
      </div>`).join("")}</div>`;
    for (const b of box.querySelectorAll("[data-tier]")) b.onclick = () => {
      const n = Number(b.dataset.tier); open = open === n ? null : n; store("mf.detail.tier", String(open || "")); drawTiers();
    };
  };

  // allocation (a donut and the table with profit against cost) and the cash-flow chart: charts/panels.js
  const drawAlloc = () => allocInto($("#alloc", box), d);
  const drawCash = () => cashInto(box, cf);

  drawTiers(); drawAlloc(); drawCash();
  if (ctx.board) {
    const el = $("#d-month", box);
    if (fl && fl.flows) ctx.board.month = monthFlows(el, {client, scope, first: fl.flows});
    else el.innerHTML = `<h3>Tiền vào và ra trong tháng</h3><p class="small muted">Không tải được: ${esc((fl || {}).error || "")}</p>`;
  }
  for (const b of box.querySelectorAll("[data-months]")) b.onclick = () => { store("mf.detail.months", b.dataset.months); ctx.go(location.hash); };
  if (ctx.board && !only) { ctx.board.redraw = drawCash; return; }  // the dashboard is drawn again in place: its view redraws it
  // a chart drawn at the width it is shown at: again after a resize
  let t = null;
  const again = () => { clearTimeout(t); t = setTimeout(() => { if (box.isConnected) drawCash(); else removeEventListener("resize", again); }, 150); };
  addEventListener("resize", again);
}
