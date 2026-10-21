/* “Điều đáng chú ý” in Thông tin on the Tổng quan lens (UX_TOOLBAR_PLAN T4): the client's feed (POST /api/feed), the
   most important first, each with why and where it comes from — what Toàn cảnh showed, now beside the graph instead of
   a list Tin tức already has. A high item's evidence opened is recorded (BRD-KPI-07), as Toàn cảnh did. */
import {n, esc, post, vnd} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";

const SEV = {high: ["bad", "Cần xem"], medium: ["warn", "Đáng chú ý"], info: ["", "Thông tin"]};
const TYPE = {impact: ["Tác động tin", "news", "var(--s1)"], goal: ["Mục tiêu", "target", "var(--s3)"], risk: ["Ngưỡng", "alert", "var(--warning)"],
  change: ["Thay đổi", "activity", "var(--s7)"]};
const KIND = {run: "Lần áp dụng", regulation: "Ghi chú quy định", goal: "Mục tiêu", dashboard: "Tổng quan", transactions: "Giao dịch"};
const PART = {risk: "rủi ro", liquidity: "thanh khoản", net_worth: "tài sản ròng"};
const ROUTE = {impact: "#/client/tin/thi-truong", graph: "#/client/tin/do-thi"};
const source = (ev) => `${KIND[ev.kind] || ev.kind} ${ev.kind === "dashboard" ? PART[ev.id] || ev.id : ev.kind === "transactions" ? `${ev.category} ${ev.month}` : ev.id}`;

/* the list, into ``el``; ``feed`` is POST /api/feed's ``feed`` (or {error}); ``board(part, month)`` opens the dashboard */
export function drawFeed(el, feed, {client, board}) {
  if (!feed) { el.innerHTML = `<h3>Điều đáng chú ý</h3><p class="small muted">Đang tải…</p>`; return; }
  if (feed.error) { el.innerHTML = `<h3>Điều đáng chú ý</h3><p class="small muted">Không tải được: ${esc(feed.error)}</p>`; return; }
  const its = feed.items;
  el.innerHTML = `<h3>Điều đáng chú ý <span class="hint">${its.length ? `${its.length} mục · quan trọng trước` : ""}</span></h3>
    ${its.length ? `<div class="list">${its.map((i) => {
      const t = TYPE[i.type] || [i.type, "info", "var(--accent)"];
      const go = i.link === "flow" ? `<button type="button" class="linkbtn small" data-board="month" data-month="${esc(i.evidence.month)}">Xem dòng tiền →</button>`
        : ROUTE[i.link] ? `<a class="small" href="${ROUTE[i.link]}">Xem bằng chứng →</a>`
        : `<button type="button" class="linkbtn small" data-board="nw">Xem bằng chứng →</button>`;
      return `<div class="item feed-item" data-focus="${esc(i.key)}">
        <span class="ic-chip sm" style="--tone:${t[2]}">${icon(t[1], {size: 13})}</span>
        <div><div class="t" data-explains>${esc(i.title)}</div>
          <div class="row tight mt-xs"><span class="pill ${SEV[i.severity][0]}">${SEV[i.severity][1]}</span><span class="pill">${esc(t[0])}</span>${i.value != null && i.type === "impact" ? `<span class="pill ${i.value < 0 ? "bad" : "good"}">${n(vnd(i.value, true), "impact.expected_3m", {event: i.title})} · 3 tháng</span>` : ""}</div>
          <div class="m mt-xs small" data-explains>${esc(i.why)}</div>
          <div class="small muted">Nguồn: ${esc(source(i.evidence))}</div>
          <div class="mt-xs">${go}</div></div></div>`;
    }).join("")}</div>` : `<p class="small muted">Không có điều gì cần chú ý lúc này.</p>`}
    <div class="footnote" data-explains>Vì sao một mục hiện ở đây: ${esc(feed.rules)}</div>`;
  for (const a of el.querySelectorAll(".feed-item a, .feed-item [data-board]")) a.addEventListener("click", () => {
    const it = its.find(i => i.key === a.closest(".feed-item").dataset.focus);
    if (it && it.severity === "high") post("/api/feed/open", {client_id: client(), key: it.key}).catch(() => {});  // BRD-KPI-07
    if (a.dataset.board) board(a.dataset.board, a.dataset.month || null);
  });
}
