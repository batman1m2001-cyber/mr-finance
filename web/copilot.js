/* OneWealth Copilot (kit K5): a floating button and a side panel on every page, the assistant's front end
   (ASSISTANT_PLAN A2). It sends the message, the page's route, the role and the picked client to
   POST /api/assistant: the role's tools in as many steps as the question needs, writes waiting for “Xác nhận”
   (the run parks on the server; the answer resumes it). Each answer says how it was written (mode): the model
   reading the tools' results, the tools' own texts (the barrier keeps client data from the model), or the
   Copilot's keyword path when no model answers (POST /api/copilot, whose confirm it still uses). The
   conversation is kept for this browser tab only.

   Living Interface (B-01): the button and panel show the request's real state (data-state: idle, busy while
   the request is in flight, ok, error, pending a confirmation), and an answer marks the page elements it
   was read from (its `focus` keys) on this page, or on the evidence page once it opens. */
import {$, esc, followedIds, post} from "./core/core.js";
import {icon} from "./core/icons.js?v=20261016r1";
import {progress} from "./charts/mini.js?v=20261016r2";
import {after, focus, present} from "./motion.js?v=20261016r1";

const ROLE_LABEL = {client: "Khách hàng", rm: "RM", cio: "CIO", compliance: "Tuân thủ", specialist: "Chuyên gia", admin: "Quản trị"};
const START = {
  client: ["Tài sản của tôi thế nào?", "Vì sao tin này ảnh hưởng tới tôi?", "Tạo kịch bản VN-Index giảm mạnh", "Có gì cần chú ý?"],
  rm: ["Hôm nay cần gọi ai?", "Điều tra tin lớn nhất", "Kịch bản lãi suất tăng", "Duyệt đề xuất đang chờ"],
  cio: ["Hộp tin có bao nhiêu tin?", "Lấy tin mới"],
  compliance: ["Có bao nhiêu tin bị giữ?", "Mở tin bị giữ"],
  specialist: ["Khuyến nghị nào đang chờ tôi duyệt?"],
  admin: ["Có cảnh báo hệ thống nào?", "Mở trang Hệ thống"],
};
const MODE = {  // how the answer was written: the badge and the line under the form
  model: (a) => [`mô hình ${a.model || ""}`.trim(), "Mô hình đọc kết quả công cụ của ứng dụng (chế độ demo) và viết câu trả lời; số liệu lấy từ công cụ. Không phải khuyến nghị đầu tư."],
  template: () => ["mẫu cố định", "Mô hình chỉ thấy câu hỏi đã che tên và số, không thấy số liệu; câu trả lời ghép từ kết quả công cụ theo mẫu. Không phải khuyến nghị đầu tư."],
  fallback: () => ["dự phòng: từ khóa", "Chế độ dự phòng: bộ định tuyến từ khóa chọn một công cụ; câu trả lời viết theo mẫu. Không phải khuyến nghị đầu tư."],
};
const BADGE = {failed: ["bad", "Không thực hiện được"], forbidden: ["bad", "Không có quyền"], pending: ["warn", "Chờ xác nhận"]};
const STATE = {idle: "Sẵn sàng", busy: "Đang xử lý", ok: "Đã trả lời", error: "Không thực hiện được", pending: "Chờ bạn xác nhận"};
const FOR = {ok: "ok", pending: "pending", failed: "error", forbidden: "error", unknown: "idle"};
const STEP = {ok: "✓", failed: "✕", declined: "–", forbidden: "✕"};

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
// the model's prose: escaped first, then only bold, bullet lines and paragraphs (no links, no HTML from the model)
function prose(text) {
  const inline = (t) => esc(t).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  const out = []; let list = [];
  const flush = () => { if (list.length) { out.push(`<ul class="cp-prose">${list.map(x => `<li>${inline(x)}</li>`).join("")}</ul>`); list = []; } };
  for (const line of String(text || "").split("\n")) {
    const m = line.match(/^\s*(?:[-*•]|\d+[.)])\s+(.*)$/);
    if (m) { list.push(m[1]); continue; }
    flush();
    const t = line.replace(/^#+\s*/, "").trim();
    if (t) out.push(`<p class="cp-p">${inline(t)}</p>`);
  }
  flush();
  return out.join("");
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
  panel.innerHTML = `<header class="cp-head"><span class="cp-dot" id="cp-dot" aria-hidden="true"></span><b>OneWealth Copilot</b><span class="sr-only" id="cp-state">Sẵn sàng</span><span class="badge assumed" id="cp-router">trợ lý</span>
      <button type="button" class="linkbtn" id="cp-close" aria-label="Đóng">✕</button></header>
    <div class="cp-ctx small muted" id="cp-ctx"></div>
    <div class="cp-msgs" id="cp-msgs" aria-live="polite"></div>
    <div class="cp-sugg" id="cp-sugg"></div>
    <form class="cp-form" id="cp-form"><input id="cp-q" autocomplete="off" maxlength="2000" placeholder="Hỏi về tài sản, dòng tiền, tin…" aria-label="Câu hỏi">
      <button type="submit" class="btn sm">Gửi</button></form>
    <div class="cp-foot small muted" id="cp-foot">Trợ lý chỉ dùng các chức năng sẵn có của ứng dụng; việc ghi luôn chờ bạn xác nhận. Không phải khuyến nghị đầu tư.</div>`;
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
    if (c.role !== role) { const had = role; role = c.role; msgs = load(role); shown = msgs.length; if (had && !panel.hidden) { draw(); sugg(); } }
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
      : `<div class="cp-bot${fresh(i)}${m.status === "failed" || m.status === "forbidden" ? " cp-err" : ""}">${BADGE[m.status] ? `<span class="badge ${BADGE[m.status][0]}">${BADGE[m.status][1]}</span> ` : ""}${m.mode === "model" ? prose(m.text) : esc(m.text)}
          ${(m.waits || []).length > 1 ? `<ul class="cp-notes">${m.waits.map(w => `<li>${esc(w.summary)}</li>`).join("")}</ul>` : ""}
          ${(m.cards || []).map(card).join("")}${m.status === "ok" ? meta(m) : ""}
          ${(m.steps || []).length > 1 || (m.steps || []).some(s => s.status !== "ok") ? `<div class="cp-steps small muted">Các bước: ${m.steps.map(s => `<span class="chip ${s.status === "ok" ? "" : "bad"}" title="${esc(s.text || "")}">${esc(s.label || s.tool)} ${STEP[s.status] || ""}</span>`).join(" ")}</div>` : ""}
          ${(m.confirm || (m.waits || []).length) && !m.done ? `<div class="row mt"><button type="button" class="btn sm" data-ok="${i}">Xác nhận</button><button type="button" class="btn sm ghostbtn" data-no="${i}">Huỷ</button></div>` : ""}
          ${(m.citations || []).length || m.here ? `<div class="mt row">${m.here ? `<button type="button" class="linkbtn small" data-here="${i}">Chỉ trên trang</button>` : ""}${(m.citations || []).filter(c => !(m.here && c.route === location.hash)).map(c => `<a class="small" data-ev="${i}" href="${esc(c.route)}">Mở ${esc(c.label)} →</a>`).join("")}</div>` : ""}
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
    for (const b of box.querySelectorAll("[data-no]")) b.onclick = () => declineIt(Number(b.dataset.no));
  };
  // the Copilot's answer (the fallback's confirm runs there) and the assistant's, as one message
  const fromCopilot = (a) => ({text: a.text, status: a.status, confirm: a.confirm, citations: a.evidence ? [a.evidence] : [], seen: a.seen,
    focus: a.focus || [], cards: a.card ? [a.card] : [], as_of: a.as_of, sources: a.sources, at: a.answered_at, mode: "fallback",
    router: (a.router || {}).kind === "confirm" ? "bạn xác nhận" : "định tuyến từ khóa (dự phòng)", suggest: a.suggest, navigate: a.navigate});
  const fromAssistant = (a) => ({text: a.text, status: a.status, confirm: a.confirm, waits: a.waits, turn_id: a.turn_id, steps: a.steps || [],
    citations: a.citations || [], seen: a.seen, focus: a.focus || [], cards: (a.steps || []).map(s => s.card).filter(Boolean),
    as_of: a.as_of, sources: a.sources, at: a.answered_at, mode: a.mode, model: a.model, suggest: a.suggest, navigate: a.navigate,
    router: a.mode === "template" ? "mô hình chỉ thấy trạng thái công cụ" : a.mode === "fallback" ? `định tuyến từ khóa (dự phòng: ${a.why || ""})` : ""});
  const call = async (body) => {
    busy = true; setState("busy"); draw();
    let m;
    try {
      m = body.confirm ? fromCopilot((await post("/api/copilot", {...context(), question: "", confirm: body.confirm})).copilot)
        : fromAssistant((await post("/api/assistant", {...context(), ...body})).assistant);
    } catch (e) { m = {status: "failed", text: `Không gọi được trợ lý: ${e.message}`}; }
    busy = false;
    const [badge, foot] = (MODE[m.mode] || MODE.fallback)(m);
    if (m.mode) { $("#cp-router", panel).textContent = badge; $("#cp-foot", panel).textContent = foot; }
    msgs.push(m);
    setState(FOR[m.status] || "error");
    if (m.navigate) { after(m.focus); location.hash = m.navigate; }
    else m.here = show(m) > 0;  // on this page: mark it now, and keep a button to mark it again
    save(role, msgs); draw(); sugg(m.suggest);
  };
  const send = (q) => {
    q = String(q || "").trim();
    if (!q || busy) return;
    msgs.push({me: true, text: q}); $("#cp-q", panel).value = "";
    call({message: q});
  };
  const answers = (m, v) => Object.fromEntries(m.waits.map(w => [w.id, v]));
  const confirmIt = (i) => {
    const m = msgs[i]; m.done = true; msgs.push({me: true, text: "Xác nhận"});
    call(m.confirm ? {confirm: m.confirm} : {turn_id: m.turn_id, approvals: answers(m, "approve")});
  };
  const declineIt = (i) => {
    const m = msgs[i]; m.done = true;
    if (m.confirm) { msgs.push({text: "Đã huỷ, không có gì được ghi."}); save(role, msgs); setState("idle"); draw(); return; }
    msgs.push({me: true, text: "Huỷ"}); call({turn_id: m.turn_id, approvals: answers(m, "deny")});  // the run ends, nothing written
  };

  const open = () => { drawCtx(); draw(); sugg(); panel.hidden = false; btn.setAttribute("aria-expanded", "true"); $("#cp-q", panel).focus(); };
  const close = () => { panel.hidden = true; btn.setAttribute("aria-expanded", "false"); if (btn.dataset.state === "error") setState("idle"); btn.focus();
    if (later) { const k = later; later = null; focus(k); } };
  btn.onclick = () => (panel.hidden ? open() : close());
  $("#cp-close", panel).onclick = close;
  panel.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
  $("#cp-form", panel).onsubmit = (e) => { e.preventDefault(); send($("#cp-q", panel).value); };
  window.addEventListener("hashchange", () => { if (!panel.hidden) drawCtx(); });
}
