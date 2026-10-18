/* Quản trị · Vận hành (SCR-ADM-02, FEAT-41): the system as a map, left to right — where data comes from (news
   feeds, market jobs, the AI zone), where it is kept (the schedule, the audit chain, availability), the AI (the
   agents, their queue and evaluations), the people (accounts, configuration waiting) — each node green, amber or red
   from its last record, its error on hover and in Thông tin. Below: the alerts the bell holds for Admin, the jobs
   failing, configuration waiting, people and roles, the chain.

   Every figure is GET /api/desk's, which is Hệ thống's own read (GET /api/system) — the same composition, so the desk
   never says a number Hệ thống would not. Read-only: alerts are acknowledged from the bell, configuration decided on
   Cấu hình, the history loaded on Hệ thống (BRD-RULE-ROLE-04). data-node marks what the assistant reads. */
import {ago, esc} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {JOB} from "../pages/system.js?v=20261018q1";  // the jobs' names as Hệ thống says them

const LANES = [["sources", "Nguồn"], ["store", "Lưu trữ"], ["ai", "AI"], ["people", "Con người"]];
const STATE = {ok: ["good", "Ổn"], warn: ["warn", "Cần xem"], bad: ["bad", "Lỗi"], idle: ["", "Chưa chạy"]};
const SEVERITY = {high: "bad", medium: "warn", low: ""};
const ROLE = {cio: "CIO", rm: "RM", compliance: "Tuân thủ", admin: "Quản trị", specialist: "Chuyên gia"};

export function hint(d) {
  const bad = d.nodes.filter(n => n.state === "bad").length, warn = d.nodes.filter(n => n.state === "warn").length;
  return `<h3>Vận hành</h3>
    <p class="small">Bản đồ đọc từ trái sang phải: dữ liệu đến từ đâu, được giữ ở đâu, AI dùng nó ra sao, ai làm việc trên nó.
      Mỗi nút xanh, vàng hay đỏ theo lần chạy gần nhất; chọn một nút để xem chi tiết và mở trang của nó.</p>
    <p class="small">${bad ? `<b>${bad}</b> nút đang lỗi` : "Không nút nào lỗi"}${warn ? `, <b>${warn}</b> cần xem` : ""}.
      Trợ lý bên cạnh đọc cùng bản đồ: hỏi “Hệ thống có gì bất thường?” hay “Chuỗi nhật ký còn nguyên không?”.</p>`;
}

export function render(box, d, api) {
  const bad = d.nodes.filter(n => n.state === "bad").length;
  const node = (n) => `<button type="button" class="ad-node ${esc(n.state)}" data-n="${esc(n.id)}" data-node="node:${esc(n.id)}"
      title="${esc(n.error || n.note || "")}" aria-label="${esc(n.label)}: ${esc(STATE[n.state][1])}, ${esc(n.value)}">
      <span class="ad-dot" aria-hidden="true"></span><span class="ad-node-l">${esc(n.label)}</span>
      <span class="ad-node-v num">${esc(n.value)}</span>${n.note || n.at ? `<span class="ad-node-u small muted">${esc([n.note, n.at ? ago(n.at) : ""].filter(Boolean).join(" "))}</span>` : ""}</button>`;
  box.innerHTML = `
    <header class="dk-head"><div><div class="eyebrow">Quản trị</div><h1 class="ws-title" id="dk-title">Vận hành</h1>
      <p class="ws-sub small muted">${bad ? `<b>${bad}</b> nút lỗi` : "Không nút nào lỗi"} · ${d.alerts.filter(a => a.status === "open").length} cảnh báo đang mở ·
        ${d.failing.length} việc lỗi · ${d.config.length} cấu hình chờ duyệt</p></div>
      <span class="pill ${d.chain.ok ? "good" : "bad"}">Chuỗi nhật ký: ${d.chain.ok ? "nguyên vẹn" : "gãy"}</span></header>
    <ol class="ad-map" data-node="ops" aria-label="Hệ thống: nguồn, lưu trữ, AI, con người">${LANES.map(([id, label]) => `<li class="ad-lane">
      <h2 class="ad-lane-t">${esc(label)}</h2>${d.nodes.filter(n => n.lane === id).map(node).join("")}</li>`).join("")}</ol>
    <div class="dk-grid mt">
      <section class="panel" data-node="alerts" aria-labelledby="ad-al"><div class="sechead"><h2 class="h3" id="ad-al">Cảnh báo</h2>
        <span class="small muted">xem ở chuông để đánh dấu đã xem</span></div>
        <div class="dk-list">${d.alerts.map(a => `<div class="dk-row"><span class="dk-row-t"><b>${esc(a.title)}</b>
          <small>${esc(a.label || a.kind)} · ${a.count > 1 ? `${a.count} lần · ` : ""}${esc(ago(a.last_at))}${a.detail ? ` · ${esc(a.detail)}` : ""}</small></span>
          <span class="badge ${a.status === "open" ? SEVERITY[a.severity] || "" : ""}">${a.status === "open" ? "Đang mở" : "Đã xem"}</span></div>`).join("")
          || `<p class="small muted">Không có cảnh báo nào đang mở hay chờ xử lý.</p>`}</div></section>
      <section class="panel" data-node="jobs" aria-labelledby="ad-jobs"><div class="sechead"><h2 class="h3" id="ad-jobs">Việc đang lỗi</h2>
        <a class="small" href="#/admin/he-thong">Hệ thống →</a></div>
        <div class="dk-list">${d.failing.map(j => `<a class="dk-row" href="${esc(j.route)}"><span class="dk-row-t"><b>${esc(JOB[j.id] || j.id)}</b>
          <small>${esc(j.id)} · ${esc(ago(j.at))} · ${esc(j.error || "")}</small></span><span class="badge bad">Lỗi</span></a>`).join("")
          || `<p class="small muted">Mọi việc đã chạy đều ổn ở lần gần nhất.</p>`}</div></section>
      <section class="panel" data-node="config" aria-labelledby="ad-cfg"><div class="sechead"><h2 class="h3" id="ad-cfg">Cấu hình chờ duyệt</h2>
        <a class="small" href="#/admin/cau-hinh">Cấu hình →</a></div>
        <div class="dk-list">${d.config.map(c => `<a class="dk-row" href="#/admin/cau-hinh"><span class="dk-row-t"><b>${esc(c.label)}</b>
          <small>${esc(c.id)}${c.by ? ` · đề xuất bởi ${esc(c.by)}` : ""}${c.two_person ? " · cần người thứ hai duyệt" : ""}</small></span>
          <span class="pill warn">Chờ duyệt</span></a>`).join("") || `<p class="small muted">Không cấu hình nào chờ duyệt.</p>`}
          ${d.evals.length ? `<p class="small mt-xs">${d.evals.length} đề xuất lời nhắc hay mô hình chờ bộ đánh giá.</p>` : ""}</div></section>
      <section class="panel" data-node="people" aria-labelledby="ad-ppl"><div class="sechead"><h2 class="h3" id="ad-ppl">Người dùng và vai trò</h2>
        <a class="small" href="#/admin/tai-khoan">Tài khoản và vai trò →</a></div>
        <dl class="dk-kv">${Object.entries(d.roles).map(([r, n]) => `<dt>${esc(ROLE[r] || r)}</dt><dd class="num">${n}</dd>`).join("")}
          <dt>Khách hàng</dt><dd class="num">${d.clients}</dd><dt>Chưa đặt mật khẩu</dt><dd class="num">${d.no_password}</dd>
          <dt>Yêu cầu tài khoản chờ duyệt</dt><dd class="num">${d.account_requests || 0}</dd></dl>
        <p class="small muted mt-xs">Thêm tài khoản, đổi vai trò, khoá, mở lại, đặt lại mật khẩu: một Quản trị đề xuất, một Quản trị khác duyệt (Q-25).
          Phân công RM cho khách hàng là một cấu hình hai người duyệt: <a href="#/admin/cau-hinh">Cấu hình →</a></p></section>
      <section class="panel dk-wide" data-node="chain" aria-labelledby="ad-chain"><div class="sechead"><h2 class="h3" id="ad-chain">Chuỗi nhật ký</h2>
        <a class="small" href="#/admin/nhat-ky">Nhật ký →</a></div>
        <dl class="dk-kv"><dt>Kiểm tra băm</dt><dd><span class="badge ${d.chain.ok ? "good" : "bad"}">${d.chain.ok ? "Nguyên vẹn" : `Gãy ở dòng ${esc(d.chain.broken_at)}`}</span></dd>
          <dt>Số dòng</dt><dd class="num">${d.chain.count}</dd><dt>Đoạn chỉ-ghi-một-lần</dt><dd>${d.worm.on ? `${d.worm.segments} đoạn · ${d.worm.ok ? "khớp" : "lệch"}` : "tắt"}</dd>
          <dt>Đầu chuỗi</dt><dd class="num small">${esc(String(d.chain.head || "").slice(0, 16))}…</dd></dl></section>
    </div>`;

  for (const b of box.querySelectorAll("[data-n]")) b.onclick = () => pick(b.dataset.n);
  function pick(id) {
    for (const b of box.querySelectorAll("[data-n]")) b.classList.toggle("sel", b.dataset.n === id);
    const n = d.nodes.find(x => x.id === id);
    const [tone, word] = STATE[n.state];
    api.inspect(`<h3>${esc(n.label)}</h3><p><span class="badge ${tone}">${esc(word)}</span> <span class="num">${esc(n.value)}</span></p>
      ${n.note ? `<p class="small">${esc(n.note)}</p>` : ""}${n.error ? `<p class="small bad-text">${esc(n.error)}</p>` : ""}
      ${n.items && n.items.length ? `<div class="dk-list">${n.items.map(x => `<div class="dk-row"><span class="dk-row-t"><b>${esc((x.job && JOB[x.job]) || x.title)}</b>
        ${x.sub || x.at ? `<small>${esc([x.sub, x.at ? ago(x.at) : ""].filter(Boolean).join(" · "))}</small>` : ""}</span>${x.state ? `<span class="badge ${STATE[x.state][0]}">${esc(STATE[x.state][1])}</span>` : ""}</div>`).join("")}</div>` : ""}
      <p class="mt"><a class="btn" href="${esc(n.route)}">${icon("arrow", {size: 14})} Mở ${esc(n.page)}</a></p>`);
  }
}
