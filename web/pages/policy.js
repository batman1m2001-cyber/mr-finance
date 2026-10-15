/* Chi phí chính sách (SCR-CL-06; UI redesign R3, was the pre-redesign “alerts” tab; FEAT-25). On top a wealth
   check: the return this year against the benchmark, the followed goals behind, and what to do first (the full
   plan is on Kế hoạch). Then what each policy, macro and infrastructure item does to net worth — impact =
   holding × sensitivity × probability, the probability by legal status — as diverging bars that filter to risks
   or opportunities; the house views (mock research-house forecasts) matched to the client's holdings; and one
   card per item, grouped by kind. Data: POST /api/alerts, POST /api/dashboard, POST /api/goals, GET /api/views. */
import {internal, esc, followedIds, get, pct, post, vnd} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {hover} from "../charts/charts.js";

const SEV = {high: ["bad", "cao"], medium: ["warn", "trung bình"], low: ["", "thấp"]};
const KIND = {
  policy: ["Policy headlines", "Chính sách, pháp luật", "scale"],
  macro: ["Market & macro headlines", "Thị trường, lãi suất, tỷ giá", "activity"],
  infrastructure: ["Infrastructure headlines", "Hạ tầng, quy hoạch", "building"],
};
const STANCE = {positive: ["good", "Tích cực"], neutral: ["", "Trung tính"], cautious: ["warn", "Thận trọng"]};
const RANK = {on_track: 0, at_risk: 1, off_track: 2};
const view = {filter: "all", allViews: false};  // for this page's life

const sevPill = (a) => (a.opportunity
  ? `<span class="pill good">Cơ hội · ${SEV[a.severity][1]}</span>`
  : `<span class="pill ${SEV[a.severity][0]}">Rủi ro · ${SEV[a.severity][1]}</span>`);

// which of the client's holdings a house view is about
function touches(v, holdings) {
  const t = v.touches || {};
  return holdings.filter(h => {
    if (h.detail && h.detail.ticker && (t.tickers || []).includes(h.detail.ticker)) return true;
    if (h.class === "real_estate" && t.areas) return t.areas.includes(h.detail.area);
    return (t.classes || []).includes(h.class);
  });
}

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope(), staff = ctx.role !== "client";
  const [{report: rep}, {dashboard: d}, gout, vs] = await Promise.all([
    post("/api/alerts", {client_id: client, scope}),
    post("/api/dashboard", {client_id: client, scope}),
    post("/api/goals", {client_id: client, scope}).catch(() => ({goals: []})),
    get("/api/views").catch((e) => ({error: e.message})),
  ]);
  const planHref = staff ? ctx.href("khach-hang", "ke-hoach") : ctx.href("muc-tieu", "ke-hoach");

  // ── the wealth check ──────────────────────────────────────────────
  const pf = d.performance, rk = d.risk, behind = pf.vs_benchmark < 0;
  const worst = d.holdings.filter(h => h.kind === "asset" && ["stock", "fund"].includes(h.class) && h.cost)
    .map(h => ({name: h.name, ret: (h.value - h.cost) / h.cost})).sort((a, b) => a.ret - b.ret)[0];
  const set = followedIds(client);
  const goals = gout.goals.filter(g => (set ? set.includes(g.id) : g.followed));
  const short = goals.filter(g => g.goal.gap > 0 && g.goal.status !== "on_track");
  const gap = short.reduce((a, g) => a + g.goal.gap, 0);
  const first = [...short].sort((a, b) => RANK[b.goal.status] - RANK[a.goal.status] || b.goal.gap - a.goal.gap)[0];
  const acts = [];
  if (behind && worst && worst.ret < pf.benchmark_ytd) acts.push(`Xem lại ${esc(worst.name)} (${pct(worst.ret, true)} so với giá vốn)`);
  if (rk.status !== "ok") acts.push(`Giảm điểm nóng: mức sụt giảm ước tính ${pct(rk.current)} so với ngưỡng ${pct(rk.limit, false, 0)}`);
  if (first && first.goal.actions[0]) acts.push(`${esc(first.title)}: ${esc(first.goal.actions[0].text)}`);

  box.innerHTML = `${staff ? internal() : ""}
    <div class="pagehead"><div><div class="eyebrow">Tin tác động</div><h1 class="h1">Chi phí chính sách</h1>
      <p class="lede">Chính sách, vĩ mô và hạ tầng đang làm tài sản ròng ${rep.scope === "family" ? "gia đình" : "của bạn"} tăng hay giảm bao nhiêu</p></div></div>
    <div class="cols">
      <div class="panel c12" data-focus="policy:check">
        <h3>Wealth check <span class="hint">chênh lệch mục tiêu và hiệu quả so với benchmark</span></h3>
        <div class="kpis three">
          <div class="kpi"><div class="k">Lợi nhuận từ đầu năm</div><div class="v">${pct(pf.ytd_return, true)}</div>
            <div class="s ${behind ? "down" : "up"}">${behind ? "▼ kém" : "▲ hơn"} ${esc(pf.benchmark_name)} ${pct(Math.abs(pf.vs_benchmark))} <span class="muted">(${esc(pf.benchmark_name)} ${pct(pf.benchmark_ytd, true)})</span></div></div>
          <div class="kpi"><div class="k">Mục tiêu đang theo dõi</div><div class="v">${goals.length ? `${short.length}/${goals.length}` : "—"}</div>
            <div class="s muted">${short.length ? `cần chú ý · thiếu tổng ${vnd(gap)}` : goals.length ? "đều đúng tiến độ" : "chưa đặt mục tiêu"}</div></div>
          <div class="kpi"><div class="k">Việc nên làm trước</div>
            ${acts.length ? `<ol class="ul">${acts.slice(0, 3).map(a => `<li>${a}</li>`).join("")}</ol>` : `<p class="muted">Không có việc gấp.</p>`}</div>
        </div>
        <a class="btn sm mt" href="${planHref}">Mở Wealth Planning Advisor ${icon("arrow", {size: 14})}</a>
      </div>
      <div class="panel c12" id="impact"></div>
      <div class="c12" id="views"></div>
      <div class="notice warn c12">${icon("alert", {size: 15})} ${esc(rep.note)}</div>
      <div class="c12" id="sections"></div>
    </div>`;

  const drawImpact = () => {
    const f = view.filter;
    const list = rep.alerts.filter(a => f === "all" || (f === "opp" ? a.opportunity : !a.opportunity));
    const maxAbs = Math.max(1, ...rep.alerts.map(a => Math.abs(a.impact)));
    const el = box.querySelector("#impact");
    el.innerHTML = `<h3>Tác động lên tài sản ròng <span class="hint">${rep.scope === "family" ? "gia đình" : "cá nhân"} · tài sản ròng ${vnd(rep.net_worth)}</span></h3>
      <p class="small muted">Tác động (VND) = Mức nắm giữ × Độ nhạy × Xác suất xảy ra · xác suất theo trạng thái: dự thảo thấp, đang lấy ý kiến trung bình, đã thông qua cao.</p>
      <div class="row spread"><div class="legend"><span><i style="background:var(--out)"></i>Rủi ro (giảm tài sản)</span><span><i style="background:var(--in)"></i>Cơ hội (tăng tài sản)</span></div>
        <div class="seg" role="group" aria-label="Lọc">${[["all", "Tất cả"], ["risk", "Rủi ro"], ["opp", "Cơ hội"]].map(([k, t]) => `<button type="button" data-af="${k}" aria-pressed="${f === k}">${t}</button>`).join("")}</div></div>
      <div class="dbars mt">${list.slice(0, 10).map(a => `<div class="dbar" tabindex="0" data-a="${esc(a.id)}" data-focus="policy:${esc(a.id)}"><span class="dl">${esc(a.title)}</span>
        <span class="dt"><span class="dneg">${a.impact < 0 ? `<span style="width:${Math.abs(a.impact) / maxAbs * 100}%"></span>` : ""}</span><span class="dpos">${a.impact > 0 ? `<span style="width:${a.impact / maxAbs * 100}%"></span>` : ""}</span></span>
        <span class="dv ${a.impact >= 0 ? "up" : "down"}">${vnd(a.impact, true)}</span></div>`).join("") || `<p class="muted">Không có mục nào.</p>`}</div>`;
    for (const b of el.querySelectorAll("[data-af]")) b.onclick = () => { view.filter = b.dataset.af; drawImpact(); drawSections(); };
    for (const row of el.querySelectorAll("[data-a]")) {
      const a = rep.alerts.find(x => x.id === row.dataset.a);
      hover(row, `<b>${esc(a.title)}</b><div>${esc(a.message)}</div><div class="row"><span>Tác động</span><span>${vnd(a.impact, true)}</span></div>`);
    }
  };

  const drawViews = () => {
    const el = box.querySelector("#views");
    if (vs.error) { el.innerHTML = `<div class="notice bad" role="alert">Không tải được house views: ${esc(vs.error)}</div>`; return; }
    const rows = vs.views.map(v => {
      const hit = touches(v, d.holdings);
      return {v, hit, exposure: hit.reduce((a, h) => a + h.value, 0)};
    }).sort((a, b) => (b.hit.length > 0) - (a.hit.length > 0) || b.exposure - a.exposure);
    const mine = rows.filter(r => r.hit.length).length;
    const card = ({v, hit, exposure}) => {
      const [tone, text] = STANCE[v.stance] || STANCE.neutral;
      return `<div class="panel vcard${hit.length ? "" : " far"}">
        <div class="row tight"><b>${esc(v.house)}</b><span class="chip">${esc(v.kind)}</span><span class="small muted">${esc(v.date)}</span>
          <span class="pill ${tone}" style="margin-left:auto">${text}</span></div>
        <h4>${esc(v.title)}</h4>
        <p class="small">${esc(v.summary)}</p>
        <div class="kv"><span>Dự báo / mục tiêu</span><b>${esc(v.target)}</b></div>
        <div class="kv"><span>Chủ đề · kỳ hạn</span><b>${esc(v.topic)} · ${esc(v.horizon)}</b></div>
        <div class="kv"><span>Liên quan danh mục của bạn</span><b>${hit.length
          ? `${hit.slice(0, 4).map(h => esc(h.name)).join(", ")}${hit.length > 4 ? ` +${hit.length - 4}` : ""} · ${hit.some(h => h.kind === "asset") ? vnd(exposure) : "khoản nợ"}`
          : `<span class="muted">không trực tiếp</span>`}</b></div></div>`;
    };
    el.innerHTML = `<div class="sechead"><h2 class="h2">House views</h2><span class="small muted">Dự báo từ quỹ, công ty chứng khoán, hãng tin và nghiên cứu nội bộ ·
        ${rows.length} góc nhìn · <b>${mine}</b> liên quan danh mục của bạn</span></div>
      <div class="cards2">${(view.allViews ? rows : rows.slice(0, 2)).map(card).join("")}</div>
      ${rows.length > 2 ? `<button type="button" class="btn sm mt" id="views-more">${view.allViews ? "Thu gọn" : `Xem thêm ${rows.length - 2} góc nhìn khác`}</button>` : ""}
      <p class="small muted mt-xs">${icon("info", {size: 14})} ${esc(vs.note)}</p>`;
    const more = el.querySelector("#views-more");
    if (more) more.onclick = () => { view.allViews = !view.allViews; drawViews(); };
  };

  const drawSections = () => {
    const f = view.filter;
    const list = rep.alerts.filter(a => f === "all" || (f === "opp" ? a.opportunity : !a.opportunity));
    const card = (a) => `<div class="panel acard" data-focus="policy:${esc(a.id)}">
        <div class="row tight">${sevPill(a)}<span class="chip">${esc(a.status_label)}</span></div>
        <h4>${esc(a.title)}</h4>
        <p class="small">${esc(a.message)}</p>
        <div class="kv"><span>Tác động ước tính (đã tính xác suất)</span><b class="${a.impact >= 0 ? "up" : "down"}">${vnd(a.impact, true)} · ${pct(a.impact_pct, true, 2)} tài sản ròng</b></div>
        <div class="kv"><span>Mức nắm giữ × Độ nhạy × Xác suất</span><b>${vnd(a.exposure)} × ${pct(a.sensitivity, true, 2)} × ${pct(a.probability, false, 0)}</b></div>
        <div class="kv"><span>Khoản bị ảnh hưởng</span><b>${a.affected.map(esc).join(", ")}</b></div>
        <div class="small muted mt-xs">Nguồn: ${esc(a.source)}</div></div>`;
    box.querySelector("#sections").innerHTML = Object.entries(KIND).map(([k, [en, vi, ic]]) => {
      const items = list.filter(a => a.kind === k);
      if (!items.length) return "";
      const net = items.reduce((t, a) => t + a.impact, 0);
      return `<section class="mt"><div class="sechead"><h2 class="h2"><span class="ic-chip sm">${icon(ic, {size: 14})}</span> ${en}</h2>
        <span class="small muted">${vi} · ${items.length} tin · tổng tác động <b class="${net >= 0 ? "up" : "down"}">${vnd(net, true)}</b></span></div>
        <div class="cards2">${items.map(card).join("")}</div></section>`;
    }).join("");
  };

  drawImpact();
  drawViews();
  drawSections();
}
