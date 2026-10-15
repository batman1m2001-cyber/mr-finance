/* OneWealth Copilot (kit K5, ADR-0012): a floating button and a side panel on every page. It sends the
   question, the page's route, the role and the picked client to POST /api/copilot; the server's router sees
   only the scrubbed question and the route, our code runs the tool and writes the answer. Writes wait for
   “Xác nhận”. The conversation is kept for this browser tab only. */
import {$, esc, post} from "./core/core.js";

const ROLE_LABEL = {client: "Khách hàng", rm: "RM", cio: "CIO", compliance: "Tuân thủ"};
const START = {
  client: ["Tài sản của tôi thế nào?", "Dòng tiền tháng này?", "Có gì cần chú ý?"],
  rm: ["Hôm nay cần gọi ai?", "Có gì cần chú ý với khách này?", "Duyệt đề xuất đang chờ"],
  cio: ["Hộp tin có bao nhiêu tin?", "Lấy tin mới"],
  compliance: ["Có bao nhiêu tin bị giữ?", "Mở tin bị giữ"],
};
const BADGE = {failed: ["bad", "Không thực hiện được"], forbidden: ["bad", "Không có quyền"], pending: ["warn", "Chờ xác nhận"]};

function context() {
  const role = (location.hash.replace(/^#\/?/, "").split("/")[0]) || "client";
  const client = (window.Legacy && window.Legacy.client && window.Legacy.client()) || ($("#client") || {}).value || null;
  const scope = (document.querySelector("[data-scope][aria-pressed=true]") || {dataset: {scope: "personal"}}).dataset.scope;
  return {role: ROLE_LABEL[role] ? role : "client", client_id: client, scope, route: location.hash};
}

const KEY = (role) => `mf.copilot.${role}`;
function load(role) { try { return JSON.parse(sessionStorage.getItem(KEY(role)) || "[]"); } catch (_) { return []; } }
function save(role, msgs) { try { sessionStorage.setItem(KEY(role), JSON.stringify(msgs.slice(-30))); } catch (_) { /* private mode */ } }

export function mount() {
  const btn = document.createElement("button");
  btn.type = "button"; btn.className = "cp-fab"; btn.setAttribute("aria-haspopup", "dialog");
  btn.innerHTML = `<span aria-hidden="true">✦</span> Hỏi OneWealth`;
  const panel = document.createElement("aside");
  panel.className = "cp-panel"; panel.hidden = true;
  panel.setAttribute("role", "dialog"); panel.setAttribute("aria-label", "OneWealth Copilot");
  panel.innerHTML = `<header class="cp-head"><b>OneWealth Copilot</b><span class="badge assumed" id="cp-router">bộ định tuyến từ khóa</span>
      <button type="button" class="linkbtn" id="cp-close" aria-label="Đóng">✕</button></header>
    <div class="cp-ctx small muted" id="cp-ctx"></div>
    <div class="cp-msgs" id="cp-msgs" aria-live="polite"></div>
    <div class="cp-sugg" id="cp-sugg"></div>
    <form class="cp-form" id="cp-form"><input id="cp-q" autocomplete="off" maxlength="500" placeholder="Hỏi về tài sản, dòng tiền, tin…" aria-label="Câu hỏi">
      <button type="submit" class="btn sm">Gửi</button></form>
    <div class="cp-foot small muted">Mô hình chỉ chọn công cụ trên câu hỏi đã che tên và số; câu trả lời viết từ kết quả công cụ theo mẫu. Không phải khuyến nghị đầu tư.</div>`;
  document.body.append(btn, panel);
  let msgs = [], role = null, busy = false;

  const drawCtx = () => {
    const c = context();
    if (c.role !== role) { role = c.role; msgs = load(role); }
    const page = (document.querySelector("#subnav:not([hidden]) [aria-current=page]") || document.querySelector("#nav [aria-current=page]") || {}).textContent || "";
    const name = (($("#client") || {}).selectedOptions || [])[0];
    $("#cp-ctx", panel).textContent = `Đang xem: ${page.trim() || "—"} · ${ROLE_LABEL[role]}${["client", "rm"].includes(role) && name ? " · " + name.textContent.split("·")[0].trim() : ""}`;
  };
  const sugg = (list) => {
    $("#cp-sugg", panel).innerHTML = (list || START[role] || []).map(s => `<button type="button" class="chip" data-s="${esc(s)}">${esc(s)}</button>`).join("");
    for (const b of panel.querySelectorAll("[data-s]")) b.onclick = () => send(b.dataset.s);
  };
  const draw = () => {
    const box = $("#cp-msgs", panel);
    box.innerHTML = msgs.length ? msgs.map((m, i) => m.me
      ? `<div class="cp-me">${esc(m.text)}</div>`
      : `<div class="cp-bot">${BADGE[m.status] ? `<span class="badge ${BADGE[m.status][0]}">${BADGE[m.status][1]}</span> ` : ""}${esc(m.text)}
          ${m.confirm && !m.done ? `<div class="row mt"><button type="button" class="btn sm" data-ok="${i}">Xác nhận</button><button type="button" class="btn sm ghostbtn" data-no="${i}">Huỷ</button></div>` : ""}
          ${m.evidence ? `<div class="mt"><a class="small" href="${esc(m.evidence.route)}">Mở ${esc(m.evidence.label)} →</a></div>` : ""}
          ${m.seen ? `<details class="small muted mt"><summary>Mô hình thấy gì</summary>“${esc(m.seen)}” · ${esc(m.router)}</details>` : ""}</div>`).join("")
      : `<div class="small muted">Hỏi về tài sản, dòng tiền, mục tiêu hay tin tác động của khách hàng đang chọn. Tôi chỉ dùng các chức năng sẵn có của ứng dụng.</div>`;
    if (busy) box.insertAdjacentHTML("beforeend", `<div class="cp-bot muted">Đang xử lý…</div>`);
    box.scrollTop = box.scrollHeight;
    for (const b of box.querySelectorAll("[data-ok]")) b.onclick = () => confirmIt(Number(b.dataset.ok));
    for (const b of box.querySelectorAll("[data-no]")) b.onclick = () => { msgs[b.dataset.no].done = true; msgs.push({text: "Đã huỷ, không có gì được ghi."}); save(role, msgs); draw(); };
  };
  const call = async (body) => {
    busy = true; draw();
    let a;
    try { a = (await post("/api/copilot", {...context(), ...body})).copilot; }
    catch (e) { a = {status: "failed", text: `Không gọi được trợ lý: ${e.message}`}; }
    busy = false;
    const r = a.router || {};
    $("#cp-router", panel).textContent = r.kind === "llm" ? `mô hình ${r.model || ""}` : "bộ định tuyến từ khóa";
    msgs.push({text: a.text, status: a.status, confirm: a.confirm, evidence: a.evidence, seen: a.seen,
      router: r.kind === "llm" ? `định tuyến bởi ${r.model}` : r.kind === "confirm" ? "bạn xác nhận" : "định tuyến từ khóa (mô phỏng)"});
    save(role, msgs); draw(); sugg(a.suggest);
    if (a.navigate) location.hash = a.navigate;
  };
  const send = (q) => {
    q = String(q || "").trim();
    if (!q || busy) return;
    msgs.push({me: true, text: q}); $("#cp-q", panel).value = "";
    call({question: q});
  };
  const confirmIt = (i) => { msgs[i].done = true; msgs.push({me: true, text: "Xác nhận"}); call({question: "", confirm: msgs[i].confirm}); };

  const open = () => { drawCtx(); draw(); sugg(); panel.hidden = false; btn.setAttribute("aria-expanded", "true"); $("#cp-q", panel).focus(); };
  const close = () => { panel.hidden = true; btn.setAttribute("aria-expanded", "false"); btn.focus(); };
  btn.onclick = () => (panel.hidden ? open() : close());
  $("#cp-close", panel).onclick = close;
  panel.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
  $("#cp-form", panel).onsubmit = (e) => { e.preventDefault(); send($("#cp-q", panel).value); };
  window.addEventListener("hashchange", () => { if (!panel.hidden) drawCtx(); });
}
