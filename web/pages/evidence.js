/* CIO · Bằng chứng tin (NEWS_EVIDENCE_BRD §8.2): every news frame, the ones not approved and the ones with precedents
   lacking a source first. A row opens the same panel the client and the RM see, with the CIO's review under it. */
import {esc, post, pct, toast} from "../core/core.js";
import {openFrame} from "./policy.js?v=20261028e2";

const TONE = {positive: "good", negative: "bad", unclear: ""};
const BRANCH = {statistics: "Thống kê", qualitative: "Định tính"};

export async function render(box, ctx) {
  const {evidence: ev} = await post("/api/evidence", {role: "cio"});
  const order = (f) => [f.review.status === "approved" ? 1 : 0, -f.unsourced];
  const rows = [...ev.frames].sort((a, b) => order(a)[0] - order(b)[0] || order(a)[1] - order(b)[1]);
  const waiting = rows.filter(f => f.review.status !== "approved").length;
  const unsourced = rows.filter(f => f.unsourced).length;
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO</div><div class="h1">Bằng chứng tin</div>
      <div class="lede small">Mỗi tin có tác động: nhánh, chiều hướng, tiền lệ và duyệt của CIO.</div></div></div>
    <div class="row tight"><span class="chip">${rows.length} tin</span>
      ${waiting ? `<span class="pill warn">${waiting} chưa duyệt</span>` : ""}
      ${unsourced ? `<span class="pill warn">${unsourced} tin có tiền lệ chưa có nguồn</span>` : ""}</div>
    <div class="panel mt"><div class="scrollx"><table class="table"><thead><tr><th>Tin</th><th>Nhánh</th><th>Chiều hướng</th>
      <th>Bằng chứng</th><th>Duyệt</th></tr></thead><tbody>${rows.map(f => `
      <tr data-f="${esc(f.factor)}" tabindex="0" role="button" style="cursor:pointer">
        <td data-quote>${esc(f.title)}${f.event_label !== f.title ? `<div class="small muted">${esc(f.event_label)}</div>` : ""}</td>
        <td>${BRANCH[f.branch]}</td>
        <td><span class="pill ${TONE[f.direction]}">${esc(f.direction_label)}</span></td>
        <td>${esc(f.label)}${f.unsourced ? ` <span class="pill warn">${f.unsourced} chưa có nguồn</span>` : ""}</td>
        <td><span class="pill ${f.review.status === "approved" ? "good" : "warn"}">${esc(f.review.label)}</span></td></tr>`).join("")}
    </tbody></table></div></div>
    ${drafts(ev)}
    <details class="more mt"><summary>Ngưỡng</summary><p class="small muted" data-explains>Nhánh thống kê cần ít nhất ${ev.thresholds.min_precedents}
      tiền lệ, và tỷ lệ cùng chiều phải hơn tỷ lệ nền ${pct(ev.thresholds.min_edge, false, 0)}; thiếu thì đi nhánh định tính.</p></details>`;
  for (const row of box.querySelectorAll("[data-f]")) {
    const f = ev.frames.find(x => x.factor === row.dataset.f);
    const open = () => openFrame({factor: f.factor, title: f.title}, {...ctx, role: "cio"}, () => render(box, ctx));
    row.onclick = open;
    row.onkeydown = (e) => { if (e.key === "Enter") open(); };
  }
  const act = async (b, url, body, done) => {
    b.disabled = true;
    try { await post(url, {...body, by: ctx.user}); toast(done); render(box, ctx); }
    catch (e) { b.disabled = false; toast(e.message); }
  };
  box.querySelectorAll("[data-draft]").forEach(b => b.onclick = () => act(b, "/api/evidence/draft", {news_id: b.dataset.draft}, "Agent đã lập khung"));
  box.querySelectorAll("[data-dd]").forEach(b => b.onclick = () =>
    act(b, "/api/evidence/draft/decide", {news_id: b.closest("[data-nid]").dataset.nid, decision: b.dataset.dd}, "Đã ghi"));
}

// NEWS_EVIDENCE_BRD §4 (P1): the agent reads one news item and drafts its frame; the CIO approves, returns or rejects
const DECIDE = {approve: "Duyệt", return: "Trả lại agent", reject: "Từ chối"};
const STATUS = {pending: "warn", failed: "bad", approved: "good", returned: "warn", rejected: "bad"};
function drafts(ev) {
  const card = (d) => `<li data-nid="${esc(d.news_id)}" class="panel" style="margin:0">
    <div class="row" style="gap:8px;flex-wrap:wrap;align-items:baseline"><strong data-quote>${esc(d.news.title)}</strong>
      <span class="pill ${STATUS[d.review.status]}">${esc(d.review.label)}</span></div>
    <div class="row small muted" style="gap:4px 10px;flex-wrap:wrap;align-items:center"><span>${esc(d.event_label)}</span>
      <span class="pill ${TONE[d.direction]}">${esc(d.direction_label)}</span><span>${esc(d.timeframe_label)}</span>
      <span>${d.precedents} tiền lệ</span><span>${d.mode === "mock" ? "mô phỏng" : `trực tiếp, ${d.attempts} lần`}</span></div>
    <details class="more"><summary>Khung</summary><p class="small" data-quote>${esc(d.mechanism || "")}</p>
      <div class="small">${d.targets.map(t => `<span class="chip">${esc(t.name)}</span>`).join(" ")}</div>
      ${[...d.failed, ...d.notes].map(x => `<div class="small muted" data-explains>${esc(x)}</div>`).join("")}</details>
    ${d.review.status === "pending" || d.review.status === "failed" ? `<div class="row tight mt">${Object.entries(DECIDE)
      .filter(([k]) => !(k === "approve" && d.failed.length)).map(([k, v]) => `<button type="button" class="btn${k === "approve" ? " primary" : ""}" data-dd="${k}">${v}</button>`).join("")}</div>` : ""}
  </li>`;
  return `<section class="panel mt"><h3>Agent lập khung từ tin <span class="hint">agent chỉ đọc tin, không đọc dữ liệu khách; khung chờ CIO duyệt</span></h3>
    ${ev.suggested.length ? `<div class="small muted">Tin quan trọng chưa có khung</div><ul class="list" style="margin:6px 0 0;padding:0;list-style:none;display:grid;gap:6px">${ev.suggested.map(s => `
      <li class="row" style="gap:8px;justify-content:space-between;align-items:center"><span class="small" data-quote>${esc(s.title)}</span>
        <button type="button" class="btn" data-draft="${esc(s.id)}">Lập khung</button></li>`).join("")}</ul>` : ""}
    ${ev.drafts.length ? `<ol style="margin:12px 0 0;padding:0;list-style:none;display:grid;gap:8px">${ev.drafts.map(card).join("")}</ol>`
      : `<p class="small muted mt">Chưa có khung nào do agent lập.</p>`}
  </section>`;
}
