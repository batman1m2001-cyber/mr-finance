/* Hiệu quả tư vấn for one client (SCR-RM-04; UI redesign R3, was the pre-redesign “performance” tab; FEAT-28).
   Staff only. What the AI advised and what came of it over twelve months: the counts and money (right, wrong,
   missed, news missed), each AI in the pipeline with its score, metrics and a twelve-month accuracy line, the
   advice log, the important news it missed, how much the client reads, and the risk tests over time (tolerance
   against capacity). Data: GET /api/advisory?client_id=. perfall.js shows the same over every client. */
import {internal, esc, get, n as how, pct, vnd} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {columns, lines, sparkline} from "../charts/money.js?v=20261016r4";

export const OUTCOME = {right: ["good", "Đúng"], wrong: ["bad", "Sai"], missed: ["warn", "Bỏ lỡ"], avoided: ["", "Không làm · đúng"], open: ["ai", "Đang theo dõi"]};
const AGENT_NAME = {news: "AI đọc tin", impact: "AI đánh giá tác động", planner: "AI tư vấn kế hoạch", chat: "AI trò chuyện với khách"};
const AGENT_ICON = {news: "news", impact: "zap", planner: "target", chat: "bot"};
export const ENG = [["minutes", "Phút đọc / tuần", "phút / tuần"], ["days", "Ngày đọc / tháng", "ngày / tháng"]];
export const eng = {view: "minutes"};  // shared by both pages for this page's life

const kpi = (ic, tone, label, value, sub, cls = "") => `<div class="kpi pcard">
  <div class="pc-head"><span class="ic-chip sm" style="--tone:${tone}">${icon(ic, {size: 14})}</span><span class="k">${label}</span></div>
  <div class="v ${cls}">${value}</div><div class="s muted">${sub}</div></div>`;

export function tiles(sm, newsSub) {
  const decided = sm.right + sm.wrong;
  return `<div class="kpis six">
    ${kpi("list", "var(--accent)", "Khuyến nghị", sm.advice, `${sm.right} đúng · ${sm.wrong} sai · ${sm.open} đang theo dõi`)}
    ${kpi("target", "var(--accent)", "Tỷ lệ đúng", decided ? how(pct(sm.right / decided, false, 0), "advisory.hit_rate", {right: String(sm.right), wrong: String(sm.wrong)}) : "—", "trên các khuyến nghị đã thực hiện")}
    ${kpi("stock", "var(--good)", "Tiền mang lại", how(vnd(sm.gained, true), "advisory.value", {count: String(sm.right)}), "từ các khuyến nghị đúng", "up")}
    ${kpi("down", "var(--critical)", "Sai, thiệt hại", how(vnd(sm.lost, true), "advisory.value", {count: String(sm.wrong)}), `${sm.wrong} khuyến nghị sai`, "down")}
    ${kpi("clock", "var(--warning)", "Hành động bỏ lỡ", sm.missed, `khách hàng không thực hiện · đã có thể thêm ${how(vnd(sm.missed_value), "advisory.value", {count: String(sm.missed)})}`)}
    ${kpi("news", "var(--warning)", "Tin quan trọng bị bỏ sót", sm.missed_news, newsSub)}
  </div>`;
}

// the AI pipeline: one card per AI, in order; sub(g) is what goes under its line
export function pipeline(agents, hint, sub) {
  return `<div class="panel mt"><h3>Chuỗi AI <span class="hint">${hint}</span></h3>
    <div class="pipe">${agents.map((g, i) => `<div class="agent">
      <div class="row tight one"><span class="ic-chip sm">${icon(AGENT_ICON[g.id] || "bot", {size: 14})}</span>
        <div><b>${i + 1}. ${esc(g.name)}</b><div class="small muted">${esc(g.name_vi)}</div></div><span class="score">${how(String(g.score), "advisory.agent_metric")}</span></div>
      <div class="spark" data-spark="${i}"></div>${sub(g)}</div>`).join("")}</div></div>`;
}

export function adviceTable(rows, who) {
  return `<table class="table"><thead><tr><th>Ngày</th><th>Khuyến nghị</th><th>Kết quả</th><th class="r">Giá trị</th></tr></thead><tbody>
    ${rows.map(x => `<tr><td class="nowrap">${esc(x.date)}</td><td><span data-explains>${esc(x.text)}</span><div class="small muted">${who ? esc(x.client) + " · " : ""}${esc(AGENT_NAME[x.agent] || x.agent)}</div></td>
      <td><span class="pill ${OUTCOME[x.outcome][0]}">${OUTCOME[x.outcome][1]}</span></td>
      <td class="r ${x.value > 0 && x.outcome === "right" ? "up" : x.value < 0 ? "down" : ""}">${x.value ? how(vnd(x.value, x.outcome !== "missed"), "advisory.value") : "—"}</td></tr>`).join("")}
  </tbody></table>`;
}

export function missedList(news) {
  return `<ul class="missed">${news.map(n => `<li><div class="row spread"><b data-quote>${esc(n.title)}</b><span class="down nowrap">${how(vnd(n.impact, true), "advisory.missed_news")}</span></div>
    <div class="small"><span class="muted">Xảy ra:</span> ${esc(n.date)} · <span class="muted">Tín hiệu sớm:</span> <span data-quote>${esc(n.signal)}</span></div>
    ${n.clients ? `<div class="small"><span class="muted">Khách hàng bị ảnh hưởng:</span> ${n.clients.map(esc).join(", ")}</div>` : ""}
    <div class="small muted" data-explains>Vì sao bỏ lỡ: ${esc(n.why)}</div></li>`).join("")}</ul>`;
}

export const engSeg = () => `<div class="seg" role="group" aria-label="Chỉ số">${ENG.map(([k, l]) => `<button type="button" data-eng="${k}" aria-pressed="${eng.view === k}">${l}</button>`).join("")}</div>`;

// the drawings that need the width they are shown at: after the HTML is in the page
export function drawSparks(box, agents, label) {
  agents.forEach((g, i) => box.querySelector(`[data-spark="${i}"]`).append(sparkline(g.trend.map(v => Math.round(v * 100)), `${g.name}: ${label}`)));
}
export function drawEngagement(box, e) {
  const el = box.querySelector("#eng-chart");
  const [, , unit] = ENG.find(x => x[0] === eng.view);
  el.replaceChildren(columns(e.months, e[eng.view], el.clientWidth, unit));
  for (const b of box.querySelectorAll("[data-eng]")) {
    b.onclick = () => {
      eng.view = b.dataset.eng;
      for (const o of box.querySelectorAll("[data-eng]")) o.setAttribute("aria-pressed", String(o === b));
      drawEngagement(box, e);
    };
  }
}

export async function render(box, ctx) {
  const client = ctx.client();
  const a = await get(`/api/advisory?client_id=${encodeURIComponent(client)}`);
  const me = await get("/api/clients").then(c => c.clients.find(x => x.id === client) || {}).catch(() => ({}));
  const t = a.tracking, e = t.engagement, tests = t.risk_tests;
  const avg = (xs) => Math.round(xs.reduce((x, y) => x + y, 0) / xs.length);
  const first = tests[0], last = tests[tests.length - 1];
  const drift = last.tolerance - first.tolerance, over = last.tolerance - last.capacity;

  box.innerHTML = `${internal()}
    <div class="pagehead"><div><div class="eyebrow">Khách hàng · <span lang="en">Advisory performance</span></div><h1 class="h1">Hiệu quả tư vấn</h1>
      <p class="lede">Hiệu quả tư vấn và AI cho khách hàng ${esc(me.name || client)} · 12 tháng</p></div>
      <a class="btn sm" href="#/rm/hieu-qua">Tất cả khách hàng ${icon("arrow", {size: 14})}</a></div>
    ${tiles(t.summary, `đã có tín hiệu sớm · tác động ${how(vnd(t.summary.missed_news_value, true), "advisory.missed_news")}`)}
    ${pipeline(t.agents, "hiệu quả từng AI · điểm 0–100 · xu hướng độ chính xác 12 tháng",
      g => g.metrics.map(m => `<div class="kv"><span>${esc(m.label)}</span><b class="${m.tone === "bad" ? "down" : ""}">${how(esc(m.value), "advisory.agent_metric")}</b></div>`).join(""))}
    <div class="cols mt">
      <div class="panel c7"><h3>Nhật ký khuyến nghị <span class="hint">${t.advice.length} khuyến nghị</span></h3>${adviceTable(t.advice)}</div>
      <div class="panel c5"><h3>Tin quan trọng bị bỏ lỡ <span class="hint">đã có thể dự đoán</span></h3>${missedList(t.missed_news)}</div>
      <div class="panel c6"><h3>Mức độ theo dõi tin của khách hàng</h3>
        <div class="kpis three">
          <div class="kpi"><div class="k">Thời gian đọc</div><div class="v">${avg(e.minutes)} phút</div><div class="s muted">trung bình mỗi tuần</div></div>
          <div class="kpi"><div class="k">Số ngày đọc</div><div class="v">${avg(e.days)} ngày</div><div class="s muted">trung bình mỗi tháng</div></div>
          <div class="kpi"><div class="k">Cảnh báo đã mở</div><div class="v">${how(esc(e.alerts_opened), "advisory.alerts_opened")}</div><div class="s muted">chuỗi ${e.streak} ngày liền</div></div>
        </div>
        <div class="mt">${engSeg()}</div><div id="eng-chart" class="mt"></div></div>
      <div class="panel c6"><h3>Khẩu vị rủi ro theo thời gian <span class="hint">${tests.length} lần làm bài test</span></h3>
        <div class="legend"><span><i style="background:var(--s2)"></i>Mức chấp nhận rủi ro (khách hàng muốn)</span><span><i style="background:var(--s1)"></i>Khả năng chịu rủi ro (dữ liệu cho thấy)</span></div>
        <div id="risk-chart" class="mt"></div>
        <p class="small">Mức chấp nhận ${drift >= 0 ? "tăng" : "giảm"} <b>${Math.abs(drift)} điểm</b> từ ${esc(first.date)} · hồ sơ hiện tại <b>${esc(last.profile || "—")}</b>${last.live ? " (bài test vừa làm)" : ""}.</p>
        ${over > 15 ? `<div class="notice warn" data-explains>${icon("alert", {size: 15})} Khách hàng muốn chịu rủi ro cao hơn khả năng ${over} điểm: chuyên gia nên trao đổi lại trước khi tăng tỷ trọng rủi ro.</div>` : ""}</div>
    </div>
    <p class="small muted mt">${icon("info", {size: 14})} ${esc(a.note)}</p>`;
  drawSparks(box, t.agents, "độ chính xác 12 tháng");
  drawEngagement(box, e);
  const rc = box.querySelector("#risk-chart");
  rc.replaceChildren(lines(tests.map(x => x.date), [
    {name: "Mức chấp nhận rủi ro", color: "var(--s2)", values: tests.map(x => x.tolerance)},
    {name: "Khả năng chịu rủi ro", color: "var(--s1)", values: tests.map(x => x.capacity)},
  ], rc.clientWidth));
}
