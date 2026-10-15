/* OneWealth Copilot (kit K5, ADR-0012): a floating button and a side panel on every page. It sends the
   question, the page's route, the role and the picked client to POST /api/copilot; the server's router sees
   only the scrubbed question and the route, our code runs the tool and writes the answer. Writes wait for
   “Xác nhận”. The conversation is kept for this browser tab only.

   Living Interface (B-01): the button and panel show the request's real state (data-state: idle, busy while
   the request is in flight, ok, error, pending a confirmation), and an answer marks the page elements it
   was read from (its `focus` keys) on this page, or on the evidence page once it opens. */
import {$, esc, post} from "./core/core.js";
import {icon} from "./core/icons.js?v=20261016r1";
import {after, focus, present} from "./motion.js?v=20261016r1";

const ROLE_LABEL = {client: "Khách hàng", rm: "RM", cio: "CIO", compliance: "Tuân thủ"};
const START = {
  client: ["Tài sản của tôi thế nào?", "Dòng tiền tháng này?", "Có gì cần chú ý?"],
  rm: ["Hôm nay cần gọi ai?", "Có gì cần chú ý với khách này?", "Duyệt đề xuất đang chờ"],
  cio: ["Hộp tin có bao nhiêu tin?", "Lấy tin mới"],
  compliance: ["Có bao nhiêu tin bị giữ?", "Mở tin bị giữ"],
};
const BADGE = {failed: ["bad", "Không thực hiện được"], forbidden: ["bad", "Không có quyền"], pending: ["warn", "Chờ xác nhận"]};
const STATE = {idle: "Sẵn sàng", busy: "Đang xử lý", ok: "Đã trả lời", error: "Không thực hiện được", pending: "Chờ bạn xác nhận"};
const FOR = {ok: "ok", pending: "pending", failed: "error", forbidden: "error", unknown: "idle"};

function context() {
  const role = (location.hash.replace(/^#\/?/, "").split("/")[0]) || "client";
  const client = (window.Legacy && window.Legacy.client && window.Legacy.client()) || ($("#client") || {}).value || null;
  const scope = (document.querySelector("[data-scope][aria-pressed=true]") || {dataset: {scope: "personal"}}).dataset.scope;
  return {role: ROLE_LABEL[role] ? role : "client", client_id: client, scope, route: location.hash};
}

const KEY = (role) => `mf.copilot.${role}`;
function load(role) { try { return JSON.parse(sessionStorage.getItem(KEY(role)) || "[]"); } catch (_) { return []; } }
function save(role, msgs) { try { sessionStorage.setItem(KEY(role), JSON.stringify(msgs.slice(-30).map(({here, ...m}) => m))); } catch (_) { /* private mode */ } }

export function mount() {
  const btn = document.createElement("button");
  btn.type = "button"; btn.className = "cp-fab"; btn.setAttribute("aria-haspopup", "dialog");
  btn.innerHTML = `<span class="cp-glyph" aria-hidden="true"><i class="cp-star">${icon("sparkles", {size: 24})}</i><i class="cp-tick">${icon("check", {size: 24})}</i></span><span class="sr-only">Hỏi OneWealth</span>`;
  btn.title = "Hỏi OneWealth (Copilot)";
  const panel = document.createElement("aside");
  panel.className = "cp-panel"; panel.hidden = true;
  panel.setAttribute("role", "dialog"); panel.setAttribute("aria-label", "OneWealth Copilot");
  panel.innerHTML = `<header class="cp-head"><span class="cp-dot" id="cp-dot" aria-hidden="true"></span><b>OneWealth Copilot</b><span class="sr-only" id="cp-state">Sẵn sàng</span><span class="badge assumed" id="cp-router">bộ định tuyến từ khóa</span>
      <button type="button" class="linkbtn" id="cp-close" aria-label="Đóng">✕</button></header>
    <div class="cp-ctx small muted" id="cp-ctx"></div>
    <div class="cp-msgs" id="cp-msgs" aria-live="polite"></div>
    <div class="cp-sugg" id="cp-sugg"></div>
    <form class="cp-form" id="cp-form"><input id="cp-q" autocomplete="off" maxlength="500" placeholder="Hỏi về tài sản, dòng tiền, tin…" aria-label="Câu hỏi">
      <button type="submit" class="btn sm">Gửi</button></form>
    <div class="cp-foot small muted">Mô hình chỉ chọn công cụ trên câu hỏi đã che tên và số; câu trả lời viết từ kết quả công cụ theo mẫu. Không phải khuyến nghị đầu tư.</div>`;
  document.body.append(btn, panel);
  let msgs = [], role = null, busy = false, shown = 0, settle = null, later = null;
  const covers = () => !panel.hidden && matchMedia("(max-width: 560px)").matches;  // phone: the panel hides the page

  // one state for the button and the panel, set only by what the request did
  const setState = (st) => {
    clearTimeout(settle);
    btn.dataset.state = panel.dataset.state = st;
    $("#cp-dot", panel).title = $("#cp-state", panel).textContent = STATE[st];
    if (st === "ok") settle = setTimeout(() => setState("idle"), 1600);  // the tick shows once, then rest
  };
  setState("idle");
  // the answer's evidence on this page now, or on its evidence page once that renders
  const show = (m) => {
    const n = m.focus && m.focus.length ? present(m.focus) : 0;
    if (n && covers()) later = m.focus;  // marked when the panel closes
    else if (n) focus(m.focus);
    return n;
  };

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
    const fresh = (i) => (i >= shown ? " cp-in" : "");
    box.innerHTML = msgs.length ? msgs.map((m, i) => m.me
      ? `<div class="cp-me${fresh(i)}">${esc(m.text)}</div>`
      : `<div class="cp-bot${fresh(i)}${m.status === "failed" || m.status === "forbidden" ? " cp-err" : ""}">${BADGE[m.status] ? `<span class="badge ${BADGE[m.status][0]}">${BADGE[m.status][1]}</span> ` : ""}${esc(m.text)}
          ${m.confirm && !m.done ? `<div class="row mt"><button type="button" class="btn sm" data-ok="${i}">Xác nhận</button><button type="button" class="btn sm ghostbtn" data-no="${i}">Huỷ</button></div>` : ""}
          ${m.evidence || m.here ? `<div class="mt row">${m.here ? `<button type="button" class="linkbtn small" data-here="${i}">Chỉ trên trang</button>` : ""}${m.evidence && !(m.here && m.evidence.route === location.hash) ? `<a class="small" data-ev="${i}" href="${esc(m.evidence.route)}">Mở ${esc(m.evidence.label)} →</a>` : ""}</div>` : ""}
          ${m.seen ? `<details class="small muted mt"><summary>Mô hình thấy gì</summary>“${esc(m.seen)}” · ${esc(m.router)}</details>` : ""}</div>`).join("")
      : `<div class="small muted">Hỏi về tài sản, dòng tiền, mục tiêu hay tin tác động của khách hàng đang chọn. Tôi chỉ dùng các chức năng sẵn có của ứng dụng.</div>`;
    shown = msgs.length;
    box.setAttribute("aria-busy", String(busy));
    if (busy) box.insertAdjacentHTML("beforeend", `<div class="cp-bot cp-in cp-think" data-busy><span class="cp-dots" aria-hidden="true"><i></i><i></i><i></i></span> Đang xử lý…</div>`);
    box.scrollTop = box.scrollHeight;
    for (const b of box.querySelectorAll("[data-here]")) b.onclick = () => { show(msgs[b.dataset.here]); if (covers()) close(); };
    for (const a of box.querySelectorAll("[data-ev]")) a.onclick = () => after(msgs[a.dataset.ev].focus);
    for (const b of box.querySelectorAll("[data-ok]")) b.onclick = () => confirmIt(Number(b.dataset.ok));
    for (const b of box.querySelectorAll("[data-no]")) b.onclick = () => { msgs[b.dataset.no].done = true; msgs.push({text: "Đã huỷ, không có gì được ghi."}); save(role, msgs); setState("idle"); draw(); };
  };
  const call = async (body) => {
    busy = true; setState("busy"); draw();
    let a;
    try { a = (await post("/api/copilot", {...context(), ...body})).copilot; }
    catch (e) { a = {status: "failed", text: `Không gọi được trợ lý: ${e.message}`}; }
    busy = false;
    const r = a.router || {};
    $("#cp-router", panel).textContent = r.kind === "llm" ? `mô hình ${r.model || ""}` : "bộ định tuyến từ khóa";
    const m = {text: a.text, status: a.status, confirm: a.confirm, evidence: a.evidence, seen: a.seen, focus: a.focus || [],
      router: r.kind === "llm" ? `định tuyến bởi ${r.model}` : r.kind === "confirm" ? "bạn xác nhận" : "định tuyến từ khóa (mô phỏng)"};
    msgs.push(m);
    setState(FOR[a.status] || "error");
    if (a.navigate) { after(m.focus); location.hash = a.navigate; }
    else m.here = show(m) > 0;  // on this page: mark it now, and keep a button to mark it again
    save(role, msgs); draw(); sugg(a.suggest);
  };
  const send = (q) => {
    q = String(q || "").trim();
    if (!q || busy) return;
    msgs.push({me: true, text: q}); $("#cp-q", panel).value = "";
    call({question: q});
  };
  const confirmIt = (i) => { msgs[i].done = true; msgs.push({me: true, text: "Xác nhận"}); call({question: "", confirm: msgs[i].confirm}); };

  const open = () => { drawCtx(); draw(); sugg(); panel.hidden = false; btn.setAttribute("aria-expanded", "true"); $("#cp-q", panel).focus(); };
  const close = () => { panel.hidden = true; btn.setAttribute("aria-expanded", "false"); if (btn.dataset.state === "error") setState("idle"); btn.focus();
    if (later) { const k = later; later = null; focus(k); } };
  btn.onclick = () => (panel.hidden ? open() : close());
  $("#cp-close", panel).onclick = close;
  panel.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
  $("#cp-form", panel).onsubmit = (e) => { e.preventDefault(); send($("#cp-q", panel).value); };
  window.addEventListener("hashchange", () => { if (!panel.hidden) drawCtx(); });
}
