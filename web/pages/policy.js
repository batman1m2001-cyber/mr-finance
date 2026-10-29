/* News and Prediction (SCR-CL-06; was Chi phí chính sách, FEAT-25). What moves the client's wealth, read as news
   (business feedback 2026-10-29): on top every item with only its direction — positive, negative or neutral, no
   amount, not even on hover — filtered by how soon and by direction; then the items in three sections: global
   news (world and macro), local news (Vietnam, its infrastructure) and exclusive contents (laws at every stage, and
   the house views' analysis). Each card is a short summary, why it matters to someone who holds what it touches,
   its precedents and its source, each linked. Each item opens its evidence (NEWS_EVIDENCE_BRD §8.2): the statistics
   or the qualitative frame, and for the CIO the review. Data: POST /api/alerts, POST /api/dashboard, GET /api/views,
   POST /api/evidence. */
import {closeDrawer, drawer, esc, get, n as how, pct, post, toast, vnd} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {hover} from "../charts/charts.js";

const SECTIONS = [
  ["global", "Tin quốc tế", "Tin thế giới và vĩ mô toàn cầu", "activity"],
  ["local", "Tin trong nước", "Việt Nam, hạ tầng và thị trường trong nước", "building"],
  ["exclusive", "Nội dung độc quyền", "Luật và chính sách (dự thảo, đã ban hành, đang thực hiện) và phân tích chuyên sâu", "scale"],
];
const STANCE = {positive: ["good", "Tích cực"], neutral: ["", "Trung tính"], cautious: ["warn", "Thận trọng"]};
const DIR = {positive: ["good", "Tích cực"], negative: ["bad", "Tiêu cực"], neutral: ["", "Trung tính"]};
const view = {filter: "all", horizon: "all", allViews: false};  // for this page's life
const HORIZON = [["all", "Mọi thời gian"], ["1w", "1 tuần"], ["1m", "1 tháng"], ["3m", "3 tháng"], [">3m", "Trên 3 tháng"]];
const TONE = {positive: "good", negative: "bad", unclear: ""};
const certain = (c, a) => `${how(vnd(c.amount, true), "policy.certain", {event: a.title})}/${esc(c.per)} · ${esc(c.from)}`;
// an item's direction: its approved evidence's, else the sign of its impact; nothing to say either way is neutral
const dir = (a) => {
  const e = a.evidence && a.evidence.direction;
  if (e === "unclear" || (!e && !a.impact)) return "neutral";
  return e ? (e === "positive" ? "positive" : "negative") : a.opportunity ? "positive" : "negative";
};
const dirPill = (a) => `<span class="pill ${DIR[dir(a)][0]}">${DIR[dir(a)][1]}</span>`;
// a source's address: its own when stable, else a search for it; an assumption made for the demo has none
const SEARCH = "https://www.google.com/search?q=";
const linkOf = (text, url) => url || (!text || /giả định/i.test(text) ? null : SEARCH + encodeURIComponent(text));
const linked = (html, url) => (url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${html}</a>` : html);

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


// an item's precedents, each linked to its own source or a search for it (or the statistics' sentence)
function precedents(e) {
  if (!e) return "";
  if (e.sentence) return `<div class="nblock"><div class="nhead">Thống kê</div><p class="small" data-explains>${esc(e.sentence)}</p></div>`;
  const ps = e.precedents || [];
  if (!ps.length) return "";
  return `<div class="nblock"><div class="nhead">Tiền lệ (${ps.length})</div><ul class="nprec">${ps.map(p =>
    `<li class="small">${linked(`<b>${esc(p.event)}</b>`, linkOf(p.event, p.url))}<div class="muted" data-explains>${esc(p.outcome)}</div></li>`).join("")}</ul></div>`;
}

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope();
  const [{report: rep}, {dashboard: d}, vs] = await Promise.all([
    post("/api/alerts", {client_id: client, scope}),
    post("/api/dashboard", {client_id: client, scope}),
    get("/api/views").catch((e) => ({error: e.message})),
  ]);
  const again = () => render(box, ctx);
  // one item per news: a rule that hits twice (a loan and a bond) is one row and one card naming both
  const items = [];
  for (const a of rep.alerts) {
    const had = items.find(x => x.factor === a.factor);
    if (had) had.affected = [...new Set([...had.affected, ...a.affected])];
    else items.push({...a, affected: [...a.affected]});
  }
  const keep = (a) => view.filter === "all" || dir(a) === view.filter;

  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Wealth Advisor</div><h1 class="h1">News and Prediction</h1></div></div>
    <div class="cols">
      <div class="panel c12" id="impact"></div>
      <div class="notice warn c12" data-explains>${icon("alert", {size: 15})} ${esc(rep.note)}</div>
      <div class="c12" id="sections"></div>
    </div>`;

  // every item and its direction only: no bar, no amount (business feedback 2026-10-29)
  const drawImpact = () => {
    const hz = view.horizon;
    const list = items.filter(a => keep(a) && (hz === "all" || (!a.sign_only && a.horizon === hz)));
    const el = box.querySelector("#impact");
    el.innerHTML = `<h3>Tác động lên tài sản ròng <span class="hint">${rep.scope === "family" ? "gia đình" : "cá nhân"}</span></h3>
      <div class="row tight"><div class="seg" role="group" aria-label="Lọc theo thời gian">${HORIZON.map(([k, t]) => `<button type="button" data-hz="${k}" aria-pressed="${hz === k}">${t}</button>`).join("")}</div>
        <div class="seg" role="group" aria-label="Lọc">${[["all", "Tất cả"], ["negative", "Tiêu cực"], ["positive", "Tích cực"], ["neutral", "Trung tính"]].map(([k, t]) => `<button type="button" data-af="${k}" aria-pressed="${view.filter === k}">${t}</button>`).join("")}</div></div>
      <div class="nrows mt">${list.map(a => `<div class="nrow" tabindex="0" data-a="${esc(a.id)}" data-focus="policy:${esc(a.id)}"><span data-explains>${esc(a.title)}</span>${dirPill(a)}</div>`).join("") || `<p class="muted">Không có mục nào.</p>`}</div>`;
    for (const b of el.querySelectorAll("[data-af]")) b.onclick = () => { view.filter = b.dataset.af; drawImpact(); drawSections(); };
    for (const b of el.querySelectorAll("[data-hz]")) b.onclick = () => { view.horizon = b.dataset.hz; drawImpact(); };
    for (const row of el.querySelectorAll("[data-a]")) {
      const a = items.find(x => x.id === row.dataset.a);
      row.onclick = () => openFrame(a, ctx, again);
      row.onkeydown = (e) => { if (e.key === "Enter") openFrame(a, ctx, again); };
      hover(row, () => `<b>${esc(a.title)}</b>
        <div class="row"><span>Tác động</span><span>${DIR[dir(a)][1]}</span></div>
        ${a.sign_only ? "" : `<div class="row"><span>Thời gian</span><span>${esc((a.evidence && a.evidence.timeframe_label) || a.horizon_label)}</span></div>`}
        ${a.affected.length ? `<div class="row"><span>Khoản liên quan</span><span>${a.affected.map(esc).join(", ")}</span></div>` : ""}
        <div class="small muted">Bấm để xem bằng chứng</div>`);
    }
  };

  // one item as a news card: summary, why it matters to you, precedents, source (business feedback 2026-10-29)
  const card = (a) => {
    const src = linkOf(a.source, a.source_url), sum = a.summary || [];
    return `<div class="panel acard" data-focus="policy:${esc(a.id)}">
      <div class="row tight">${dirPill(a)}</div>
      <h4 data-explains>${esc(a.title)}</h4>
      ${sum.length
        ? `<div class="nblock"><div class="nhead tab">Tóm tắt</div><ul class="nsum">${sum.map(s => `<li data-explains>${esc(s)}</li>`).join("")}</ul></div>`
        : `<p class="small" data-explains>${esc(a.message)}</p>`}
      ${a.why || a.affected.length ? `<div class="nblock"><div class="nhead">Ý nghĩa với bạn</div>${a.why ? `<p class="small" data-explains>${esc(a.why)}</p>` : ""}
        ${a.affected.length ? `<div class="row tight">${a.affected.map(x => `<span class="chip">${esc(x)}</span>`).join("")}</div>` : ""}</div>` : ""}
      ${precedents(a.evidence)}
      <div class="small muted mt-xs"><span>Trích nguồn:</span> ${linked(`<span data-explains>${esc(a.source)}</span>`, src)}</div></div>`;
  };

  // the house views (mock research-house forecasts) matched to the client's holdings: the analysis in Exclusive contents
  const views = () => {
    if (vs.error) return `<div class="notice bad" role="alert">Không tải được house views: ${esc(vs.error)}</div>`;
    const rows = vs.views.map(v => {
      const hit = touches(v, d.holdings);
      return {v, hit, exposure: hit.reduce((a, h) => a + h.value, 0)};
    }).sort((a, b) => (b.hit.length > 0) - (a.hit.length > 0) || b.exposure - a.exposure);
    const mine = rows.filter(r => r.hit.length).length;
    const vcard = ({v, hit, exposure}) => {
      const [tone, text] = STANCE[v.stance] || STANCE.neutral;
      return `<div class="panel vcard${hit.length ? "" : " far"}">
        <div class="row tight"><b>${esc(v.house)}</b><span class="chip">${esc(v.kind)}</span><span class="small muted">${esc(v.date)}</span>
          <span class="pill ${tone}" style="margin-left:auto">${text}</span></div>
        <div data-quote><h4>${esc(v.title)}</h4>
        <p class="small">${esc(v.summary)}</p>
        <div class="kv"><span>Dự báo / mục tiêu</span><b>${esc(v.target)}</b></div></div>
        <div class="kv"><span>Chủ đề · kỳ hạn</span><b><span>${esc(v.topic)}</span> · <span>${esc(v.horizon)}</span></b></div>
        <div class="kv"><span>Liên quan danh mục của bạn</span><b>${hit.length
          ? `${hit.slice(0, 4).map(h => esc(h.name)).join(", ")}${hit.length > 4 ? ` +${hit.length - 4}` : ""} · ${hit.some(h => h.kind === "asset") ? how(vnd(exposure), "view.exposure", {count: String(hit.length)}) : "khoản nợ"}`
          : `<span class="muted">không trực tiếp</span>`}</b></div></div>`;
    };
    return `<div class="sechead mt"><h3 class="h3">House views</h3><span class="small muted">Dự báo từ quỹ, công ty chứng khoán, hãng tin và nghiên cứu nội bộ ·
        ${rows.length} góc nhìn · <b>${mine}</b> liên quan danh mục của bạn</span></div>
      <div class="cards2">${(view.allViews ? rows : rows.slice(0, 2)).map(vcard).join("")}</div>
      ${rows.length > 2 ? `<button type="button" class="btn sm mt" id="views-more">${view.allViews ? "Thu gọn" : `Xem thêm ${rows.length - 2} góc nhìn khác`}</button>` : ""}
      <p class="small muted mt-xs">${icon("info", {size: 14})} <span>${esc(vs.note)}</span></p>`;
  };

  const drawSections = () => {
    const list = items.filter(keep);
    const el = box.querySelector("#sections");
    el.innerHTML = SECTIONS.map(([k, name, sub, ic]) => {
      const items = list.filter(a => a.section === k);
      const extra = k === "exclusive" ? views() : "";
      if (!items.length && !extra) return "";
      return `<section class="mt"><div class="sechead"><h2 class="h2"><span class="ic-chip sm">${icon(ic, {size: 14})}</span> ${name}</h2>
        <span class="small muted">${sub} · ${items.length} tin</span></div>
        ${items.length ? `<div class="cards2">${items.map(card).join("")}</div>` : ""}${extra}</section>`;
    }).join("");
    const more = el.querySelector("#views-more");
    if (more) more.onclick = () => { view.allViews = !view.allViews; drawSections(); };
  };

  drawImpact();
  drawSections();
}
