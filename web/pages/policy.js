/* Chi phí chính sách (SCR-CL-06; UI redesign R3, was the pre-redesign “alerts” tab; FEAT-25). On top a wealth
   check: the return this year against the benchmark, the followed goals behind, and what to do first (the full
   plan is on Kế hoạch). Then what each policy, macro and infrastructure item does to net worth — impact =
   holding × sensitivity × probability, the probability by legal status — as diverging bars that filter to risks
   or opportunities, each bar a stack of its parts by asset class (OWN-FB-17); the house views (mock research-house forecasts) matched to the client's holdings; and one
   card per item, grouped by kind. Each item opens its evidence (NEWS_EVIDENCE_BRD §8.2): the statistics or the
   qualitative frame, and for the CIO the review. Data: POST /api/alerts, POST /api/dashboard, POST /api/goals,
   GET /api/views, POST /api/evidence. */
import {ASSET_CLASS, CLASS_COLOR, closeDrawer, drawer, esc, followedIds, get, n as how, pct, post, toast, vnd} from "../core/core.js";
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
const view = {filter: "all", horizon: "all", allViews: false};  // for this page's life
// an alert's parts: the asset classes it moves, or a payment ahead / the salary when it moves no holding
const PART = {...ASSET_CLASS, outflow: "Khoản chi sắp tới", income: "Thu nhập"};
const partColor = (k) => CLASS_COLOR[k] || "var(--other)";
const parts = (a) => Object.entries(a.by_class || {[a.impact >= 0 ? "income" : "outflow"]: a.impact});

const sevPill = (a) => (a.sign_only
  ? `<span class="pill ${a.opportunity ? "good" : "bad"}">${a.opportunity ? "Tích cực" : "Tiêu cực"}</span>`
  : a.opportunity
    ? `<span class="pill good">Cơ hội · ${SEV[a.severity][1]}</span>`
    : `<span class="pill ${SEV[a.severity][0]}">Rủi ro · ${SEV[a.severity][1]}</span>`);
// the chart's impact (§8.2): a number that is certain if it happens (−1 triệu/tháng · từ kỳ điều chỉnh lãi tới); in VND
// for gold, bonds and the exchange rate (in_vnd), else the direction; with how soon and the evidence (−81 triệu ·
// 3 tháng · 2 tiền lệ, Tiêu cực · 1 tuần · 8/12 lần); an item on business equity only, good or bad news. An item the
// CIO has not approved has no evidence: its level and horizon, as before
const HORIZON = [["all", "Mọi thời gian"], ["1w", "1 tuần"], ["1m", "1 tháng"], ["3m", "3 tháng"], [">3m", "Trên 3 tháng"]];
const TONE = {positive: "good", negative: "bad", unclear: ""};
const LEVEL = {high: "Cao", medium: "Trung bình", low: "Thấp"};
const pin = (a) => ({exposure: vnd(a.exposure), sensitivity: pct(a.sensitivity, true, 2), probability: pct(a.probability, false, 0)});
const certain = (c, a) => `${how(vnd(c.amount, true), "policy.certain", {event: a.title})}/${esc(c.per)} · ${esc(c.from)}`;
function level(a) {
  const e = a.evidence, tone = a.opportunity ? "good" : SEV[a.severity][0];
  if (a.sign_only) return `<span class="pill ${a.opportunity ? "good" : "bad"}">${a.opportunity ? "Tích cực" : "Tiêu cực"}</span>`;
  if (!e) return `<span class="pill ${tone}">${a.in_vnd ? how(vnd(a.impact, true), "policy.impact", pin(a)) : LEVEL[a.severity]} · ${esc(a.horizon_label)}</span>`;
  if (a.certain) return `<span class="pill ${a.certain.amount >= 0 ? "good" : "bad"}">${certain(a.certain, a)}</span>`;
  return `<span class="pill ${a.in_vnd ? tone : TONE[e.direction]}">${a.in_vnd ? how(vnd(a.impact, true), "policy.impact", pin(a)) : esc(e.direction_label)} · ${esc(e.timeframe_label)} · ${esc(e.label)}</span>`;
}

// the evidence panel: why, through what, what changes, what to watch, the precedents (or the measured moves) folded;
// the CIO also reads the internal headline, the notes, which precedents have no source, and decides
// also the CIO's list of frames (web/pages/evidence.js), with no alert: ``a`` is then {factor, title}
export async function openFrame(a, ctx, again) {
  const body = drawer(a.title, `<p class="small muted">Đang tải…</p>`);
  let ev;
  try { ({evidence: ev} = await post("/api/evidence", {factor: a.factor, role: ctx.role})); }
  catch (e) { body.innerHTML = `<div class="notice bad" role="alert">${esc(e.message)}</div>`; return; }
  const f = ev.frames[0], cio = ev.role === "cio";
  if (!f) { body.innerHTML = `<p class="muted">Tin này chưa có bằng chứng được duyệt.</p>`; return; }
  const mine = f.targets.filter(t => (a.labels || []).includes(t.label)).map(t => t.name);
  const pc = (x) => pct(x, true, 1);
  const precedents = f.stats
    ? `<details><summary>Các lần đo (${f.stats.n})</summary><table class="table"><tbody>${f.stats.moves.map(m =>
        `<tr><td>${esc(m.date)}</td><td class="${m.change >= 0 ? "up" : "down"}">${pc(m.change)}</td></tr>`).join("")}</tbody></table></details>`
    : f.precedents.length
      ? `<details><summary>Tiền lệ (${f.precedents.length})</summary>${f.precedents.map(p => `<div class="small mt-xs" data-explains>
          <b>${esc(p.event)}</b> — ${esc(p.outcome)}<div class="muted">Khác lần này: ${esc(p.difference)}</div>
          ${p.source ? `<div class="muted">Nguồn: ${esc(p.source)}</div>` : cio ? `<span class="pill warn">chưa có nguồn</span>` : ""}</div>`).join("")}</details>`
      : `<p class="small muted">Chưa có tiền lệ</p>`;
  const review = cio ? `<div class="panel mt">
      <div class="row tight"><b>Duyệt của CIO</b><span class="pill ${f.review.status === "approved" ? "good" : "warn"}">${esc(f.review.label)}</span>
        ${f.unsourced ? `<span class="pill warn">${f.unsourced} tiền lệ chưa có nguồn</span>` : ""}</div>
      ${f.headline ? `<p class="small mt-xs" data-explains>Tiêu đề nội bộ: ${esc(f.headline)}</p>` : ""}
      ${f.notes.map(x => `<p class="small muted" data-explains>${esc(x)}</p>`).join("")}
      ${f.review.note ? `<p class="small muted" data-explains>Ghi chú: ${esc(f.review.note)}</p>` : ""}
      <label class="field mt-xs"><span>Ghi chú</span><input id="ev-note" placeholder="Không bắt buộc" maxlength="300"></label>
      <div class="row tight mt-xs">${[["approve", "Duyệt"], ["return", "Trả lại agent"], ["reject", "Từ chối"]].map(([k, t]) =>
        `<button type="button" class="btn sm" data-decide="${k}">${t}</button>`).join("")}</div></div>` : "";
  body.innerHTML = `<div class="row tight"><span class="pill ${TONE[f.direction]}">${esc(f.direction_label)}</span><span class="chip">${esc(f.timeframe_label)}</span>
      <span class="chip">${esc(f.label)}</span><span class="chip">${f.branch === "statistics" ? "Thống kê" : "Định tính"}</span></div>
    ${f.stats ? `<p class="small mt" data-explains>${esc(f.stats.sentence)}</p>` : ""}
    <p class="small mt" data-explains>${esc(f.mechanism)}</p>
    ${a.certain ? `<div class="kv"><span>Chắc chắn nếu xảy ra</span><b>${certain(a.certain, a)}</b></div>` : ""}
    <div class="kv"><span>Qua</span><b>${f.channels.map(esc).join(", ")}</b></div>
    <div class="kv"><span>Cái thay đổi</span><b>${f.changes.map(esc).join(", ")}</b></div>
    ${mine.length ? `<div class="kv"><span>Khớp với</span><b>${mine.map(esc).join(", ")}</b></div>` : ""}
    <div class="kv"><span>Theo dõi</span><b data-explains>${esc(f.watch)}</b></div>
    <div class="mt">${precedents}</div>${review}`;
  for (const b of body.querySelectorAll("[data-decide]")) b.onclick = async () => {
    b.disabled = true;
    try {
      const {review: r} = await post("/api/evidence/decide", {factor: a.factor, decision: b.dataset.decide, by: ctx.user, note: body.querySelector("#ev-note").value});
      toast(r.label);
      closeDrawer();
      again();
    } catch (e) { toast(e.message); b.disabled = false; }
  };
}

// which of the client's holdings a house view is about
function touches(v, holdings) {
  const t = v.touches || {};
  return holdings.filter(h => {
    if (h.detail && h.detail.ticker && (t.tickers || []).includes(h.detail.ticker)) return true;
    if (h.class === "real_estate" && t.areas) return t.areas.includes(h.detail.area);
    return (t.classes || []).includes(h.class);
  });
}

// an alert's precedents (or its measured moves) in brief: two lines in the chart's tip, every one on its card (scrolling
// inside the card when long); the whole frame stays one click away on the chart
function brief(e) {
  const ps = e.precedents || [];
  if (e.sentence) return `<hr><div data-explains>${esc(e.sentence)}</div>`;
  if (!ps.length) return "";
  return `<hr><div class="muted">Tiền lệ</div>${ps.slice(0, 2).map(p => `<div data-explains>• ${esc(p.event)}</div>`).join("")}
    ${ps.length > 2 ? `<div class="muted">… và ${ps.length - 2} tiền lệ khác</div>` : ""}`;
}
function precedents(e) {
  const ps = (e && e.precedents) || [];
  if (!e) return "";
  if (e.sentence) return `<div class="kv"><span>Thống kê</span><b data-explains>${esc(e.sentence)}</b></div>`;
  if (!ps.length) return "";
  return `<div class="prec mt-xs"><div class="small muted">Tiền lệ (${ps.length})</div>${ps.map(p => `<div class="small" data-explains>
      <b>${esc(p.event)}</b> — ${esc(p.outcome)}${p.source ? `<span class="muted"> · Nguồn: ${esc(p.source)}</span>` : ""}</div>`).join("")}</div>`;
}

// the parts the bars show, one entry per colour (a payment ahead and the salary share the grey; the tip names each)
function legend(alerts) {
  const by = new Map();
  for (const [k] of alerts.flatMap(parts)) {
    const c = partColor(k), names = by.get(c) || [];
    if (!names.includes(PART[k] || k)) names.push(PART[k] || k);
    by.set(c, names);
  }
  return [...by].map(([c, names]) => `<span><i style="background:${c}"></i>${esc(names.join(", "))}</span>`).join("");
}

// one bar: as long as the alert's impact, cut into its parts by asset class (largest at the axis)
function stack(a, maxAbs) {
  const total = Math.abs(a.impact) || 1;
  return `<span class="stk" style="width:${Math.abs(a.impact) / maxAbs * 100}%">${parts(a).map(([k, v]) =>
    `<i data-part="${esc(k)}" style="flex:${Math.abs(v) / total};background:${partColor(k)}"></i>`).join("")}</span>`;
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
  const again = () => render(box, ctx);

  // ── the wealth check ──────────────────────────────────────────────
  const pf = d.performance, rk = d.risk, behind = pf.vs_benchmark < 0;
  const worst = d.holdings.filter(h => h.kind === "asset" && ["stock", "fund"].includes(h.class) && h.cost)
    .map(h => ({name: h.name, ret: (h.value - h.cost) / h.cost, value: h.value, cost: h.cost})).sort((a, b) => a.ret - b.ret)[0];
  const set = followedIds(client);
  const goals = gout.goals.filter(g => (set ? set.includes(g.id) : g.followed));
  const short = goals.filter(g => g.goal.gap > 0 && g.goal.status !== "on_track");
  const gap = short.reduce((a, g) => a + g.goal.gap, 0);
  const first = [...short].sort((a, b) => RANK[b.goal.status] - RANK[a.goal.status] || b.goal.gap - a.goal.gap)[0];
  const acts = [];
  if (behind && worst && worst.ret < pf.benchmark_ytd) acts.push(`Xem lại ${esc(worst.name)} (${how(pct(worst.ret, true), "holding.pnl", {value: vnd(worst.value), cost: vnd(worst.cost)})} so với giá vốn)`);
  if (rk.status !== "ok") acts.push(`Giảm điểm nóng: mức sụt giảm ước tính ${how(pct(rk.current), "risk.current")} so với ngưỡng ${how(pct(rk.limit, false, 0), "risk.limit")}`);
  if (first && first.goal.actions[0]) acts.push(`${esc(first.title)}: <span data-explains>${esc(first.goal.actions[0].text)}</span>`);

  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Headline News</div><h1 class="h1">News and Prediction</h1>
      <p class="lede">Chính sách, vĩ mô và hạ tầng đang làm tài sản ròng ${rep.scope === "family" ? "gia đình" : "của bạn"} tăng hay giảm bao nhiêu</p></div></div>
    <div class="cols">
      <div class="panel c12" data-focus="policy:check">
        <h3>Kiểm tra tài sản <span class="hint">chênh lệch mục tiêu và hiệu quả so với benchmark</span></h3>
        <div class="kpis three">
          <div class="kpi"><div class="k">Lợi nhuận từ đầu năm</div><div class="v">${how(pct(pf.ytd_return, true), "perf.ytd_return")}</div>
            <div class="s ${behind ? "down" : "up"}">${behind ? "▼ kém" : "▲ hơn"} ${esc(pf.benchmark_name)} ${how(pct(Math.abs(pf.vs_benchmark)), "perf.vs_benchmark", {mine: pct(pf.ytd_return, true), bench: pct(pf.benchmark_ytd, true)})} <span class="muted">(${esc(pf.benchmark_name)} ${how(pct(pf.benchmark_ytd, true), "perf.benchmark_ytd", {benchmark: pf.benchmark_name})})</span></div></div>
          <div class="kpi"><div class="k">Mục tiêu đang theo dõi</div><div class="v">${goals.length ? `${short.length}/${goals.length}` : "—"}</div>
            <div class="s muted">${short.length ? `cần chú ý · thiếu tổng ${how(vnd(gap), "goals.gap_total", {count: String(short.length)})}` : goals.length ? "đều đúng tiến độ" : "chưa đặt mục tiêu"}</div></div>
          <div class="kpi"><div class="k">Việc nên làm trước</div>
            ${acts.length ? `<ol class="ul">${acts.slice(0, 3).map(a => `<li>${a}</li>`).join("")}</ol>` : `<p class="muted">Không có việc gấp.</p>`}</div>
        </div>
        <a class="btn sm mt" href="${planHref}">Mở Wealth Planning Advisor ${icon("arrow", {size: 14})}</a>
      </div>
      <div class="panel c12" id="impact"></div>
      <div class="c12" id="views"></div>
      <div class="notice warn c12" data-explains>${icon("alert", {size: 15})} ${esc(rep.note)}</div>
      <div class="c12" id="sections"></div>
    </div>`;

  const drawImpact = () => {
    const f = view.filter, hz = view.horizon;
    const list = rep.alerts.filter(a => (f === "all" || (f === "opp" ? a.opportunity : !a.opportunity))
      && (hz === "all" || (!a.sign_only && a.horizon === hz)));
    const maxAbs = Math.max(1, ...rep.alerts.map(a => Math.abs(a.impact)));
    const el = box.querySelector("#impact");
    el.innerHTML = `<h3>Tác động lên tài sản ròng <span class="hint">${rep.scope === "family" ? "gia đình" : "cá nhân"} · tài sản ròng ${how(vnd(rep.net_worth), "net_worth")}</span></h3>
      <div class="row spread"><div class="legend"><span class="muted">← Rủi ro · Cơ hội →</span>${legend(list.slice(0, 10))}</div>
        <div class="row tight"><div class="seg" role="group" aria-label="Lọc theo thời gian">${HORIZON.map(([k, t]) => `<button type="button" data-hz="${k}" aria-pressed="${hz === k}">${t}</button>`).join("")}</div>
        <div class="seg" role="group" aria-label="Lọc">${[["all", "Tất cả"], ["risk", "Rủi ro"], ["opp", "Cơ hội"]].map(([k, t]) => `<button type="button" data-af="${k}" aria-pressed="${f === k}">${t}</button>`).join("")}</div></div></div>
      <div class="dbars mt">${list.slice(0, 10).map(a => `<div class="dbar lv" tabindex="0" data-a="${esc(a.id)}" data-focus="policy:${esc(a.id)}"><span class="dl" data-explains>${esc(a.title)}</span>
        <span class="dt"><span class="dneg">${a.impact < 0 ? stack(a, maxAbs) : ""}</span><span class="dpos">${a.impact > 0 ? stack(a, maxAbs) : ""}</span></span>
        <span class="dv">${level(a)}</span></div>`).join("") || `<p class="muted">Không có mục nào.</p>`}</div>`;
    for (const b of el.querySelectorAll("[data-af]")) b.onclick = () => { view.filter = b.dataset.af; drawImpact(); drawSections(); };
    for (const b of el.querySelectorAll("[data-hz]")) b.onclick = () => { view.horizon = b.dataset.hz; drawImpact(); };
    for (const row of el.querySelectorAll("[data-a]")) {
      const a = rep.alerts.find(x => x.id === row.dataset.a);
      let on = null;  // the part under the pointer, bold in the tip
      for (const seg of row.querySelectorAll("[data-part]")) seg.addEventListener("mouseenter", () => { on = seg.dataset.part; });
      row.addEventListener("mouseleave", () => { on = null; });
      row.onclick = () => openFrame(a, ctx, again);
      row.onkeydown = (e) => { if (e.key === "Enter") openFrame(a, ctx, again); };
      hover(row, () => `<b>${esc(a.title)}</b><div data-explains>${esc(a.message)}</div>
        ${parts(a).map(([k, v]) => `<div class="row"${k === on ? ' style="font-weight:700"' : ""}><span><i class="sw" style="background:${partColor(k)}"></i>${esc(PART[k] || k)}</span>${a.in_vnd ? `<span>${vnd(v, true)}</span>` : ""}</div>`).join("")}
        ${a.sign_only
          ? `<div class="row"><span>Tác động</span><span>${a.opportunity ? "Tích cực" : "Tiêu cực"}</span></div>`
          : `<div class="row"><span>${a.in_vnd ? "Tác động" : "Mức tác động"}</span><span>${a.in_vnd ? how(vnd(a.impact, true), "policy.impact", pin(a)) : LEVEL[a.severity]}</span></div>
             <div class="row"><span>Thời gian</span><span>trong ${esc(a.horizon_label)}</span></div>`}
        ${a.evidence ? `<div class="row"><span>Bằng chứng</span><span>${esc(a.evidence.label)}</span></div>${brief(a.evidence)}` : ""}
        <div class="small muted">Bấm để xem bằng chứng</div>`);
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
        <div data-quote><h4>${esc(v.title)}</h4>
        <p class="small">${esc(v.summary)}</p>
        <div class="kv"><span>Dự báo / mục tiêu</span><b>${esc(v.target)}</b></div></div>
        <div class="kv"><span>Chủ đề · kỳ hạn</span><b>${esc(v.topic)} · ${esc(v.horizon)}</b></div>
        <div class="kv"><span>Liên quan danh mục của bạn</span><b>${hit.length
          ? `${hit.slice(0, 4).map(h => esc(h.name)).join(", ")}${hit.length > 4 ? ` +${hit.length - 4}` : ""} · ${hit.some(h => h.kind === "asset") ? how(vnd(exposure), "view.exposure", {count: String(hit.length)}) : "khoản nợ"}`
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
        <div class="row tight">${sevPill(a)}${a.sign_only ? "" : `<span class="chip">trong ${esc(a.horizon_label)}</span>`}<span class="chip">${esc(a.status_label)}</span>${a.evidence ? `<span class="chip">${esc(a.evidence.label)}</span>` : ""}</div>
        <h4 data-explains>${esc(a.title)}</h4>
        <p class="small" data-explains>${esc(a.message)}</p>
        ${a.in_vnd ? `<div class="kv"><span>Tác động ước tính (đã tính xác suất)</span><b class="${a.impact >= 0 ? "up" : "down"}">${how(vnd(a.impact, true), "policy.impact", pin(a))} · ${how(pct(a.impact_pct, true, 2), "policy.impact", pin(a))} tài sản ròng</b></div>
        <div class="kv"><span>Mức nắm giữ × Độ nhạy × Xác suất</span><b>${how(vnd(a.exposure), "policy.exposure", {count: String(a.affected.length)})} × ${how(pct(a.sensitivity, true, 2), "policy.sensitivity")} × ${how(pct(a.probability, false, 0), "policy.probability")}</b></div>`
        : `<div class="kv"><span>Mức tác động</span><b class="${a.impact >= 0 ? "up" : "down"}">${a.sign_only ? (a.opportunity ? "Tích cực" : "Tiêu cực") : a.impact === 0 ? "Không tính ra tiền" : LEVEL[a.severity]}</b></div>
        ${a.sign_only ? "" : `<div class="kv"><span>Thời gian</span><b>trong ${esc(a.horizon_label)}</b></div>`}`}
        <div class="kv"><span>Khoản bị ảnh hưởng</span><b>${a.affected.map(esc).join(", ")}</b></div>
        ${a.certain ? `<div class="kv"><span>Chắc chắn nếu xảy ra</span><b>${certain(a.certain, a)}</b></div>` : ""}
        ${precedents(a.evidence)}
        <div class="small muted mt-xs" data-explains>Nguồn: ${esc(a.source)}</div></div>`;
    box.querySelector("#sections").innerHTML = Object.entries(KIND).map(([k, [en, vi, ic]]) => {
      const items = list.filter(a => a.kind === k);
      if (!items.length) return "";
      const net = items.reduce((t, a) => t + a.impact, 0);
      return `<section class="mt"><div class="sechead"><h2 class="h2"><span class="ic-chip sm">${icon(ic, {size: 14})}</span> ${en}</h2>
        <span class="small muted">${vi} · ${items.length} tin · tổng tác động <b class="${net >= 0 ? "up" : "down"}">${how(vnd(net, true), "policy.net", {count: String(items.length)})}</b></span></div>
        <div class="cards2">${items.map(card).join("")}</div></section>`;
    }).join("");
  };

  drawImpact();
  drawViews();
  drawSections();
}
