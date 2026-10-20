/* Chi tiết (SCR-CL-01): the full former overview, rebuilt in the board's look (UI redesign R3). Every block of
   the pre-redesign page is here: net worth with the members it counts, assets by the three tiers of sources (each
   opening onto its sources), allocation with profit against cost, portfolio profit and loss against the
   benchmark, risk against the accepted drawdown with concentration warnings, the liquidity reserve, cash flow
   (six months past, 12/24/36 ahead) with large payments and recurring items, and the top news by impact. */
import {internal, n, nAttrs, $, esc, pct, post, vnd} from "../core/core.js";
import {CLASS_ICON, icon} from "../core/icons.js?v=20261016r1";
import {hover} from "../charts/charts.js";
import {donut, gauge} from "../charts/mini.js?v=20261016r2";
import {cashSeries, cashflow, monthName, monthsText} from "../charts/money.js?v=20261016r4";

const GROUP_COLOR = {
  "Bất động sản": "var(--s1)", "Cổ phiếu": "var(--s2)", "Tiền & tiền gửi": "var(--s3)", "Vàng": "var(--s4)",
  "Chứng chỉ quỹ": "var(--s5)", "Cổ phần DN": "var(--s6)", "Trái phiếu": "var(--s7)", "Tài sản số": "var(--s8)",
};
const GROUP_ICON = {"Bất động sản": "home", "Cổ phiếu": "stock", "Tiền & tiền gửi": "bank", "Vàng": "gold", "Chứng chỉ quỹ": "fund",
  "Cổ phần DN": "business", "Trái phiếu": "bond", "Tài sản số": "crypto", "Bảo hiểm": "shield"};
const STATUS = {ok: ["good", "An toàn"], near: ["warn", "Gần ngưỡng"], over: ["bad", "Vượt ngưỡng"], low: ["warn", "Thấp"], critical: ["bad", "Rất thấp"]};
const TIERS = [
  {n: 1, title: "Our Wealth at Techcombank", vi: "Tại hệ sinh thái Techcombank", color: "var(--s1)", icon: "bank"},
  {n: 2, title: "Custody around the world", vi: "Lưu ký bên ngoài", color: "var(--s7)", icon: "link"},
  {n: 3, title: "Self-managed", vi: "Bạn tự quản lý", color: "var(--s4)", icon: "user"},
];
const PAST = 6;
const SEV = {high: "Cao", medium: "Trung bình", low: "Thấp"};
const pill = (s) => `<span class="pill ${(STATUS[s] || [""])[0]}">${(STATUS[s] || ["", s])[1]}</span>`;
const store = (k, v) => { try { if (v === undefined) return sessionStorage.getItem(k); sessionStorage.setItem(k, v); } catch (_) { /* private mode */ } return null; };

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope(), staff = ctx.role !== "client";
  const months = Number(store("mf.detail.months")) || 12;
  const [{dashboard: d}, al] = await Promise.all([
    post("/api/dashboard", {client_id: client, scope, months}),
    post("/api/alerts", {client_id: client, scope}).catch((e) => ({error: e.message})),
  ]);
  const nw = d.net_worth, pf = d.performance, rk = d.risk, lq = d.liquidity, cf = d.cashflow;
  const up = nw.month_change >= 0;
  const chg = {now: vnd(nw.value), prev: vnd(nw.prev_value)};
  const holdingsHref = staff ? ctx.href("khach-hang", "tai-san") : ctx.href("tai-san");
  const policyHref = staff ? ctx.href("khach-hang", "chinh-sach") : ctx.href("tin", "chinh-sach");
  const who = d.members.map(m => `<span class="chip">${esc(m.name)} · ${esc(m.relation)}</span>`).join("")
    + d.waiting.map(m => `<span class="chip" title="Chưa đồng ý chia sẻ dữ liệu">${esc(m.name)} · chưa đồng ý chia sẻ</span>`).join("");

  box.innerHTML = `${staff ? internal() : ""}
    <div class="cols">
      <div class="panel c12 nwhero">
        <div>
          <div class="pc-head"><span class="ic-chip sm" style="--tone:var(--accent)">${icon("wallet", {size: 14})}</span><span class="k">Tài sản ròng · ${d.scope === "family" ? "gia đình" : "cá nhân"}</span></div>
          <div class="hero-v">${n(vnd(nw.value), "net_worth", {assets: vnd(nw.assets), liabilities: vnd(nw.liabilities)})}</div>
          <div><span class="${up ? "up" : "down"}">${up ? "▲" : "▼"} ${n(pct(nw.month_change_pct, true), "net_worth.month_change", chg)}</span> <span class="muted">so với tháng trước (${n(vnd(nw.month_change, true), "net_worth.month_change", chg)})</span></div>
          <div class="small muted mt-xs">Tài sản ${n(vnd(nw.assets), "assets.total")} · Nợ ${n(vnd(nw.liabilities), "liabilities.total")} · cập nhật ${esc(d.as_of)}</div>
          <div class="row tight mt">${who}</div>
        </div>
        <div id="srcmix"></div>
      </div>
      <div class="panel c6"><h3>Phân bổ tài sản <span class="hint">lãi/lỗ: % so với giá vốn</span></h3><div id="alloc"></div></div>
      <div class="panel c6"><h3>Lãi / lỗ danh mục <span class="hint">cổ phiếu, quỹ, trái phiếu</span></h3>
        <div class="kv"><span>Đã chốt (từ đầu năm)</span><b class="${pf.realized_ytd >= 0 ? "up" : "down"}">${n(vnd(pf.realized_ytd, true), "perf.realized_ytd")}</b></div>
        <div class="kv"><span>Chưa chốt</span><b>${n(vnd(pf.unrealized, true), "perf.unrealized", {cost: vnd(pf.invested_cost)})} <span class="muted">(${n(pct(pf.unrealized_pct, true), "perf.unrealized", {cost: vnd(pf.invested_cost)})})</span></b></div>
        <div class="kv"><span>Lợi nhuận từ đầu năm</span><b>${n(pct(pf.ytd_return, true), "perf.ytd_return")}</b></div>
        <div class="kv"><span>So với ${esc(pf.benchmark_name)} (${n(pct(pf.benchmark_ytd, true), "perf.benchmark_ytd", {benchmark: pf.benchmark_name})})</span><b class="${pf.vs_benchmark >= 0 ? "up" : "down"}">${n(pct(pf.vs_benchmark, true), "perf.vs_benchmark", {mine: pct(pf.ytd_return, true), bench: pct(pf.benchmark_ytd, true)})}</b></div>
        ${pf.by_class.length ? `<table class="table mt"><thead><tr><th>Loại</th><th class="r">Giá trị</th><th class="r">Lãi/lỗ</th></tr></thead><tbody>
          ${pf.by_class.map(c => `<tr><td>${esc(c.label)}</td><td class="r">${n(vnd(c.value), "class.value")}</td><td class="r"><span class="${c.pnl >= 0 ? "up" : "down"}">${n(vnd(c.pnl, true), "perf.class", {value: vnd(c.value), cost: vnd(c.cost)})}</span> <span class="muted small">${n(pct(c.return, true), "perf.class", {value: vnd(c.value), cost: vnd(c.cost)})}</span></td></tr>`).join("")}
        </tbody></table>` : ""}
      </div>
      <div class="panel c6"><h3>Rủi ro</h3>
        ${d.profile.risk_profile ? `<div class="kv"><span>Hồ sơ rủi ro (bài test)</span><b>${esc(d.profile.risk_profile)} · ${esc(d.profile.risk_persona)}</b></div>` : `<p class="small muted" style="margin:0 0 8px">Chưa làm bài test rủi ro: ngưỡng lấy theo hồ sơ.</p>`}
        <div class="kv"><span>Ngưỡng sụt giảm chấp nhận</span><b>${n(pct(rk.limit, false, 0), "risk.limit")}</b></div>
        <div class="kv"><span>Mức sụt giảm ước tính khi thị trường xấu</span><b>${n(pct(rk.current), "risk.current", {loss: vnd(rk.stress_loss), net_worth: vnd(nw.value)})}</b></div>
        ${gauge(rk.current, rk.limit, {status: rk.status, max: Math.max(rk.limit * 1.6, rk.current * 1.1), label: `Sụt giảm ước tính ${pct(rk.current)} so với ngưỡng ${pct(rk.limit, false, 0)}`})}
        <div class="mt-xs">${pill(rk.status)} <span class="muted small">mất ${n(vnd(rk.stress_loss), "risk.loss")} trong kịch bản xấu</span></div>
        ${d.concentration.warnings.length ? `<ul class="warns">${d.concentration.warnings.map(w => `<li>${icon("alert", {size: 14})}<span data-explains>Tập trung: ${esc(w)}</span></li>`).join("")}</ul>` : `<p class="small muted">Không có khoản nào tập trung quá ngưỡng.</p>`}
      </div>
      <div class="panel c6"><h3>Thanh khoản dự phòng</h3>
        <div class="row spread"><span>${n(vnd(lq.value), "liquidity.value", {count: String(lq.items.length)})} tiền và tài sản rút được ngay</span><b>đủ chi ${n(monthsText(lq.months), "liquidity.months", {value: vnd(lq.value), spending: vnd(lq.spending_monthly)})} ${pill(lq.status)}</b></div>
        ${gauge(Math.min(lq.months, Math.max(12, Math.min(lq.months, 36))), 6, {status: lq.status === "ok" ? "ok" : lq.status === "low" ? "near" : "over", max: Math.max(12, Math.min(lq.months, 36)), label: `Đủ chi ${monthsText(lq.months)}, mốc an toàn 6 tháng`})}
        <div class="small muted">Chi tiêu ${n(vnd(lq.spending_monthly), "spending.monthly")}/tháng · mốc an toàn: 6 tháng</div>
      </div>
      <div class="panel c12">
        <h3>Dòng tiền · ${PAST} tháng qua và ${cf.months.length} tháng tới <span class="hint">dự báo ${cf.months.length} tháng tới: vào ${n(vnd(cf.total_in), "cashflow.forecast", {months: String(cf.months.length)})} · ra ${n(vnd(cf.total_out), "cashflow.forecast", {months: String(cf.months.length)})}</span>
          <span class="seg" role="group" aria-label="Số tháng" style="margin-left:auto">${[12, 24, 36].map(n => `<button type="button" data-months="${n}" aria-pressed="${months === n}">${n} tháng</button>`).join("")}</span></h3>
        <div class="legend"><span><i style="background:var(--in)"></i>Tiền vào</span><span><i style="background:var(--out)"></i>Tiền ra</span>
          <span><i style="background:var(--in);opacity:.42"></i><i style="background:var(--out);opacity:.42"></i>Dự báo (màu nhạt)</span><span><b class="down">⚠</b> Khoản phải trả lớn</span></div>
        <div id="cash" class="mt"></div>
        <div class="cols mt">
          <div class="c6"><div class="subhead">Khoản phải trả lớn</div>${cf.large.length ? `<ul class="warns">${cf.large.map(l => `<li>${icon("alert", {size: 14})}<span><b>${monthName(l.month)}</b> · ${esc(l.label)} · ${n(vnd(l.amount), "cashflow.large", {month: monthName(l.month)})}</span></li>`).join("")}</ul>` : `<p class="small muted">Không có khoản lớn nào trong ${cf.months.length} tháng tới.</p>`}</div>
          <div class="c6"><div class="subhead">Khoản định kỳ tìm thấy trong giao dịch</div>
            <div class="list">${cf.recurring.map(r => `<div class="kv"><span><span class="legend-dot" style="background:${r.direction === "in" ? "var(--in)" : "var(--out)"}"></span> ${esc(r.label)} <span class="muted small">· ${r.cadence === "monthly" ? "hằng tháng" : "theo kỳ"}</span></span><b>${n(`${r.direction === "in" ? "+" : "−"}${vnd(r.amount)}`, "cashflow.recurring")}</b></div>`).join("")}</div></div>
        </div>
      </div>
      <div class="panel c12" id="news"></div>
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

  // allocation: a donut and the table with profit against cost
  const drawAlloc = () => {
    const rows = d.allocation;
    $("#alloc", box).innerHTML = `<div class="allocgrid"><div class="center">${donut(rows.map(a => ({key: a.group, value: a.value, color: GROUP_COLOR[a.group] || "var(--other)", label: `${a.group}: ${vnd(a.value)}, ${pct(a.share)}`})),
        {size: 148, stroke: 20, center: vnd(rows.reduce((x, a) => x + a.value, 0)), sub: "tài sản", label: "Phân bổ tài sản", how: nAttrs("assets.total")})}</div>
      <table class="table"><thead><tr><th>Loại tài sản</th><th class="r">Giá trị</th><th class="r">Tỷ trọng</th><th class="r">Lãi/lỗ</th></tr></thead><tbody>
      ${rows.map(a => `<tr><td><span class="ic-chip sm" style="--tone:${GROUP_COLOR[a.group] || "var(--other)"}">${icon(GROUP_ICON[a.group] || "wallet", {size: 12})}</span> ${esc(a.group)}</td>
        <td class="r">${n(vnd(a.value), "class.value")}</td><td class="r"><b>${n(pct(a.share, false, a.share < 0.1 ? 1 : 0), "class.share", {value: vnd(a.value), assets: vnd(nw.assets)})}</b></td>
        <td class="r">${a.return == null ? `<span class="muted" title="Chưa có giá vốn">—</span>` : `<span class="${a.return >= 0 ? "up" : "down"}" title="${vnd(a.pnl, true)} so với giá vốn">${n(pct(a.return, true), "class.return", {pnl: vnd(a.pnl, true)})}</span>`}</td></tr>`).join("")}</tbody></table></div>`;
    for (const s of box.querySelectorAll("#alloc .seg")) {
      const a = rows.find(x => x.group === s.dataset.key);
      hover(s, `<b>${esc(a.group)}</b><br>${vnd(a.value)} · ${pct(a.share)}`);
    }
  };

  const drawCash = () => {
    const host = $("#cash", box);
    if (host && host.clientWidth) host.replaceChildren(cashflow(cashSeries(cf, PAST, cf.months.length), cf.large, host.clientWidth));
  };

  // the top policy and project items by the brief's own rules (ADR-0007, Q-03): labelled as such, not as news impact,
  // which is the engine's and lives on Tác động thị trường; all of them on Chi phí chính sách
  const drawNews = () => {
    const el = $("#news", box);
    if (al.error) { el.innerHTML = `<h3>Chính sách và dự án</h3><p class="small down">Không tải được: ${esc(al.error)}</p>`; return; }
    const rep = al.report, top = rep.alerts.slice(0, 3);
    const marketHref = staff ? ctx.href("khach-hang", "tac-dong") : ctx.href("tin", "thi-truong");
    el.innerHTML = `<h3>Chính sách và dự án <span class="hint">${rep.risks} rủi ro · ${rep.opportunities} cơ hội</span><a class="small" style="margin-left:auto" href="${policyHref}">Xem tất cả ${rep.alerts.length} mục →</a></h3>
      <p class="small muted">Ước tính theo quy tắc riêng của từng chính sách (thuế, phí, vùng dự án), không phải bộ máy kịch bản. Tác động của tin thị trường: <a href="${marketHref}">Tác động thị trường</a>.</p>
      <div class="list">${top.map(a => `<div class="item"><span class="ic-chip" style="--tone:${a.opportunity ? "var(--good)" : "var(--critical)"}">${icon(a.opportunity ? "stock" : "down")}</span>
        <div><div class="t">${esc(a.title)}</div><div class="row tight mt-xs"><span class="pill ${a.opportunity ? "good" : "bad"}">${a.opportunity ? "Cơ hội" : "Rủi ro"} · ${SEV[a.severity].toLowerCase()}</span></div>
          <div class="m mt-xs" data-explains>${esc(a.message)}</div></div>
        <b class="num ${a.impact >= 0 ? "up" : "down"}">${n(vnd(a.impact, true), "policy.impact", {exposure: vnd(a.exposure), sensitivity: pct(a.sensitivity, false, 2), probability: pct(a.probability, false, 0)})}</b></div>`).join("")}</div>`;
  };

  drawTiers(); drawAlloc(); drawCash(); drawNews();
  for (const b of box.querySelectorAll("[data-months]")) b.onclick = () => { store("mf.detail.months", b.dataset.months); ctx.go(location.hash); };
  // a chart drawn at the width it is shown at: again after a resize
  let t = null;
  const again = () => { clearTimeout(t); t = setTimeout(() => { if (box.isConnected) drawCash(); else removeEventListener("resize", again); }, 150); };
  addEventListener("resize", again);
}
