/* OneWealth Copilot (kit K5, ADR-0012): a floating button and a side panel on every page. It sends the
   question, the page's route, the role and the picked client to POST /api/copilot; the server's router sees
   only the scrubbed question and the route, our code runs the tool and writes the answer. Writes wait for
   “Xác nhận”. The conversation is kept for this browser tab only.

   Living Interface (B-01): the button and panel show the request's real state (data-state: idle, busy while
   the request is in flight, ok, error, pending a confirmation), and an answer marks the page elements it
   was read from (its `focus` keys) on this page, or on the evidence page once it opens. */
import {$, esc, followedIds, post} from "./core/core.js";
import {icon} from "./core/icons.js?v=20261016r1";
import {progress} from "./charts/mini.js?v=20261016r1";
import {after, focus, present} from "./motion.js?v=20261016r1";

const ROLE_LABEL = {client: "Khách hàng", rm: "RM", cio: "CIO", compliance: "Tuân thủ"};
const START = {
  client: ["Tài sản của tôi thế nào?", "Vì sao tin này ảnh hưởng tới tôi?", "Tạo kịch bản VN-Index giảm mạnh", "Có gì cần chú ý?"],
  rm: ["Hôm nay cần gọi ai?", "Điều tra tin lớn nhất", "Kịch bản lãi suất tăng", "Duyệt đề xuất đang chờ"],
  cio: ["Hộp tin có bao nhiêu tin?", "Lấy tin mới"],
  compliance: ["Có bao nhiêu tin bị giữ?", "Mở tin bị giữ"],
};
const BADGE = {failed: ["bad", "Không thực hiện được"], forbidden: ["bad", "Không có quyền"], pending: ["warn", "Chờ xác nhận"]};
const STATE = {idle: "Sẵn sàng", busy: "Đang xử lý", ok: "Đã trả lời", error: "Không thực hiện được", pending: "Chờ bạn xác nhận"};
const FOR = {ok: "ok", pending: "pending", failed: "error", forbidden: "error", unknown: "idle"};

function context() {
  const role = (location.hash.replace(/^#\/?/, "").split("/")[0]) || "client";
  const client = ($("#client") || {}).value || null;
  const scope = (document.querySelector("[data-scope][aria-pressed=true]") || {dataset: {scope: "personal"}}).dataset.scope;
  return {role: ROLE_LABEL[role] ? role : "client", client_id: client, scope, route: location.hash, goals: client ? followedIds(client) : null};
}

const KEY = (role) => `mf.copilot.${role}`;
function load(role) { try { return JSON.parse(sessionStorage.getItem(KEY(role)) || "[]"); } catch (_) { return []; } }
function save(role, msgs) { try { sessionStorage.setItem(KEY(role), JSON.stringify(msgs.slice(-30).map(({here, ...m}) => m))); } catch (_) { /* private mode */ } }

// Copilot 2.0 (UI redesign R5): the tool's numbers as a card — figures, a list with chips, bars or a chain — and
// when the data is from and what it was read from. Every value comes from the server's tool result.
const TONE = {good: "up", bad: "down", warn: "warnc"};
function card(c) {
  if (!c) return "";
  const head = c.title ? `<div class="cp-ct">${esc(c.title)}</div>` : "";
  if (c.kind === "figures" || (c.kind === "bars" && c.figures)) {
    const figs = (c.kind === "figures" ? c.items : c.figures).map(f => `<div class="cp-fig"><span>${esc(f.label)}</span><b class="${TONE[f.tone] || ""}">${esc(f.value)}</b>${f.sub ? `<small>${esc(f.sub)}</small>` : ""}</div>`).join("");
    const notes = (c.notes || []).map(n => `<li>${esc(n)}</li>`).join("");
    const bars = c.kind === "bars" ? bars_(c) : "";
    return `<div class="cp-card">${head}<div class="cp-figs">${figs}</div>${notes ? `<ul class="cp-notes">${notes}</ul>` : ""}${bars}</div>`;
  }
  if (c.kind === "bars") return `<div class="cp-card">${head}${bars_(c)}</div>`;
  if (c.kind === "list") {
    return `<div class="cp-card">${head}<div class="cp-list">${c.items.map(x => `<div class="cp-li"${x.focus ? ` data-mark="${esc(x.focus)}"` : ""}>
      <div class="cp-lt"><b>${esc(x.title)}</b>${x.chip ? `<span class="pill ${esc(x.tone || "")}">${esc(x.chip)}</span>` : ""}${x.value ? `<b class="num ${TONE[x.tone] || ""}">${esc(x.value)}</b>` : ""}</div>
      ${x.sub ? `<small>${esc(x.sub)}</small>` : ""}${x.progress != null ? `<div class="cp-prog">${progress(x.progress, {label: x.title})}</div>` : ""}</div>`).join("")}</div></div>`;
  }
  if (c.kind === "chain") {
    return `<div class="cp-card">${head}<ol class="cp-chain">${c.steps.filter(s => s.items.length).map(s => `<li><span>${esc(s.label)}</span><div>${s.items.map(i => `<span class="chip">${esc(i)}</span>`).join("")}</div></li>`).join("")}</ol></div>`;
  }
  return "";
}
function bars_(c) {
  const max = Math.max(1, ...c.items.map(x => Math.abs(x.value)));
  return `${c.title && c.kind === "bars" && c.figures ? `<div class="cp-ct">${esc(c.title)}</div>` : ""}<div class="cp-bars">${c.items.map(x => `<div class="cp-bar"><span>${esc(x.label)}</span><i style="--w:${Math.round(Math.abs(x.value) / max * 100)}%"></i><b class="num">${esc(x.text)}</b></div>`).join("")}</div>`;
}
const day = (d) => (/^\d{4}-\d{2}-\d{2}$/.test(d) ? `${d.slice(8)}/${d.slice(5, 7)}/${d.slice(0, 4)}` : /^\d{4}-\d{2}$/.test(d) ? `tháng ${d.slice(5)}/${d.slice(0, 4)}` : d);
const clock = (t) => { const x = new Date(t * 1000); return `${String(x.getHours()).padStart(2, "0")}:${String(x.getMinutes()).padStart(2, "0")}`; };
function meta(m) {
  const bits = [m.as_of && `Số liệu ${day(m.as_of)}`, m.at && `trả lời lúc ${clock(m.at)}`].filter(Boolean).join(" · ");
  const src = (m.sources || []).length ? `<div>Nguồn: ${m.sources.map(esc).join(" · ")}</div>` : "";
  return bits || src ? `<div class="cp-meta">${bits ? `<div>${esc(bits)}</div>` : ""}${src}</div>` : "";
}

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
    const chips = (list || START[role] || []).map(s => `<button type="button" class="chip" data-s="${esc(s)}">${esc(s)}</button>`).join("");
    $("#cp-sugg", panel).innerHTML = chips ? `<span class="cp-st">Bạn có thể muốn:</span>${chips}` : "";
    for (const b of panel.querySelectorAll("[data-s]")) b.onclick = () => send(b.dataset.s);
  };
  const draw = () => {
    const box = $("#cp-msgs", panel);
    const fresh = (i) => (i >= shown ? " cp-in" : "");
    box.innerHTML = msgs.length ? msgs.map((m, i) => m.me
      ? `<div class="cp-me${fresh(i)}">${esc(m.text)}</div>`
      : `<div class="cp-bot${fresh(i)}${m.status === "failed" || m.status === "forbidden" ? " cp-err" : ""}">${BADGE[m.status] ? `<span class="badge ${BADGE[m.status][0]}">${BADGE[m.status][1]}</span> ` : ""}${esc(m.text)}
          ${card(m.card)}${m.status === "ok" ? meta(m) : ""}
          ${m.confirm && !m.done ? `<div class="row mt"><button type="button" class="btn sm" data-ok="${i}">Xác nhận</button><button type="button" class="btn sm ghostbtn" data-no="${i}">Huỷ</button></div>` : ""}
          ${m.evidence || m.here ? `<div class="mt row">${m.here ? `<button type="button" class="linkbtn small" data-here="${i}">Chỉ trên trang</button>` : ""}${m.evidence && !(m.here && m.evidence.route === location.hash) ? `<a class="small" data-ev="${i}" href="${esc(m.evidence.route)}">Mở ${esc(m.evidence.label)} →</a>` : ""}</div>` : ""}
          ${m.seen ? `<details class="small muted mt"><summary>Mô hình thấy gì</summary>“${esc(m.seen)}” · ${esc(m.router)}</details>` : ""}</div>`).join("")
      : `<div class="small muted">Hỏi về tài sản, dòng tiền, mục tiêu hay tin tác động của khách hàng đang chọn. Tôi chỉ dùng các chức năng sẵn có của ứng dụng.</div>`;
    shown = msgs.length;
    box.setAttribute("aria-busy", String(busy));
    if (busy) box.insertAdjacentHTML("beforeend", `<div class="cp-bot cp-in cp-think" data-busy><span class="cp-dots" aria-hidden="true"><i></i><i></i><i></i></span> Đang xử lý…</div>`);
    box.scrollTop = box.scrollHeight;
    for (const li of box.querySelectorAll("[data-mark]")) li.onclick = () => { if (present([li.dataset.mark])) focus([li.dataset.mark]); };
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
      card: a.card, as_of: a.as_of, sources: a.sources, at: a.answered_at,
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
