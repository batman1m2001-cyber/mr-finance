/* OneWealth Copilot (kit K5): a floating button and a side panel on every page, the assistant's front end
   (ASSISTANT_PLAN A2). It sends the message, the page's route, the role and the picked client to
   POST /api/assistant: the role's tools in as many steps as the question needs, writes waiting for “Xác nhận”
   (the run parks on the server; the answer resumes it). Each answer says how it was written (mode): the model
   reading the tools' results, the tools' own texts (the barrier keeps client data from the model), or the
   Copilot's keyword path when no model answers (POST /api/copilot, whose confirm it still uses).

   Conversations live on the server (A3, POST /api/assistant/conversations): opening the panel resumes the
   person's latest conversation in this role when it moved in the last day — on any device. Sessions (OWN-SS,
   SESSIONS_PLAN.md S4): the bar under the header names the session (rename in place), its goal and its context
   summary, with “Trò chuyện mới” beside it; the clock button lists the sessions (search, Gần đây / Lưu trữ, grouped
   by day; rename, archive, restore, delete). A turn still running after a refresh shows what has run and is
   followed until it ends. Nothing is kept in the browser.

   Living Interface (B-01): the button and panel show the request's real state (data-state: idle, busy while
   the request is in flight, ok, error, pending a confirmation), and an answer marks the page elements it
   was read from (its `focus` keys) on this page, or on the evidence page once it opens.

   Docked (FEAT-40, OWN-GW-03): in the Customer's workspace the panel lives in the dock's Trợ lý tab, always open,
   no floating button; dock(host, {onEvent}) moves it there and undock() gives it back to the page corner. Docked, a
   question goes to POST /api/assistant/stream: each real event of the turn (a tool starting and ending, the model's
   words, a write waiting) shows in the panel as it happens and goes to onEvent, which the graph draws (OWN-GW-06…10);
   a stream that breaks is said, never papered over. */
import {$, esc, followedIds, post, stream, workspaceContext} from "./core/core.js";
import {icon} from "./core/icons.js?v=20261017s1";
import {progress} from "./charts/mini.js?v=20261016r2";
import {after, focus, present} from "./motion.js?v=20261016r1";

const DESK = new Set(["cio", "compliance", "admin"]);  // A7: the panel links to the Agent page's map
const ROLE_LABEL = {client: "Khách hàng", rm: "RM", cio: "CIO", compliance: "Tuân thủ", specialist: "Chuyên gia", admin: "Quản trị"};
const START = {
  client: ["Tài sản của tôi thế nào?", "Vì sao tin này ảnh hưởng tới tôi?", "Tạo kịch bản VN-Index giảm mạnh", "Có gì cần chú ý?"],
  rm: ["Sổ khách hàng có gì cần làm?", "Hôm nay cần gọi ai?", "Điều tra tin lớn nhất", "Duyệt đề xuất đang chờ"],
  cio: ["Có gì chờ tôi duyệt?", "Phơi nhiễm lớn nhất ở đâu?", "Lần áp dụng nào đang hiệu lực?", "Hộp tin có bao nhiêu tin?"],
  compliance: ["Có bao nhiêu tin bị giữ?", "Mở tin bị giữ"],
  specialist: ["Khuyến nghị nào đang chờ tôi duyệt?", "Hồ sơ của gia đình này thế nào?", "Chứng chỉ của tôi còn hiệu lực không?"],
  admin: ["Hệ thống có gì bất thường?", "Chuỗi nhật ký còn nguyên không?", "Có cảnh báo hệ thống nào?", "Cấu hình nào chờ duyệt?"],
};
// what each role's own assistant is for (FEAT-41): the line before the first question, and the box's hint
const INTRO = {
  client: "Hỏi về tài sản, dòng tiền, mục tiêu hay tin tác động của khách hàng đang chọn.",
  rm: "Hỏi về sổ khách hàng của bạn — ai cần gọi trước, đề xuất chờ duyệt, liên hệ — hay tài sản, dòng tiền, tin tác động của khách hàng đang chọn.",
  cio: "Hỏi về việc chờ bạn quyết định, phơi nhiễm, lần áp dụng, hộp tin hay độ chính xác của mô hình.",
  compliance: "Hỏi về tin bị giữ, nghiên cứu và bản tin chờ duyệt, chính sách hay chuỗi nhật ký.",
  admin: "Hỏi về tình trạng hệ thống, nguồn dữ liệu, cảnh báo, cấu hình chờ duyệt hay chuỗi nhật ký.",
  specialist: "Hỏi về khuyến nghị chờ bạn duyệt và hồ sơ của gia đình được giao.",
};
const ASK = {client: "Hỏi về tài sản, dòng tiền, tin…", rm: "Hỏi về sổ khách hàng, khách đang chọn…", cio: "Hỏi về nhận định, phơi nhiễm, tin…",
  compliance: "Hỏi về tin bị giữ, bản tin, nhật ký…", admin: "Hỏi về hệ thống, cảnh báo, cấu hình…", specialist: "Hỏi về khuyến nghị, hồ sơ khách…"};
const MODE = {  // how the answer was written: the badge and the line under the form
  model: (a) => [`mô hình ${String(a.model || "").split("/").pop()}`.trim(), "Mô hình đọc kết quả công cụ của ứng dụng (chế độ demo) và viết câu trả lời; số liệu lấy từ công cụ. Không phải khuyến nghị đầu tư."],
  template: () => ["mẫu cố định", "Mô hình chỉ thấy câu hỏi đã che tên và số, không thấy số liệu; câu trả lời ghép từ kết quả công cụ theo mẫu. Không phải khuyến nghị đầu tư."],
  fallback: () => ["dự phòng: từ khóa", "Chế độ dự phòng: bộ định tuyến từ khóa chọn một công cụ; câu trả lời viết theo mẫu. Không phải khuyến nghị đầu tư."],
};
const BADGE = {failed: ["bad", "Không thực hiện được"], forbidden: ["bad", "Không có quyền"], pending: ["warn", "Chờ xác nhận"], interrupted: ["warn", "Bị ngắt"]};
const STATE = {idle: "Sẵn sàng", busy: "Đang xử lý", ok: "Đã trả lời", error: "Không thực hiện được", pending: "Chờ bạn xác nhận"};
const FOR = {ok: "ok", pending: "pending", failed: "error", forbidden: "error", unknown: "idle"};
const STEP = {ok: "✓", failed: "✕", declined: "–", forbidden: "✕"};

function context() {
  const role = (location.hash.replace(/^#\/?/, "").split("/")[0]) || "client";
  const client = ($("#client") || {}).value || null;
  const scope = (document.querySelector("[data-scope][aria-pressed=true]") || {dataset: {scope: "personal"}}).dataset.scope;
  const graph = role === "client" ? workspaceContext.get() : null;  // the Customer's workspace (F10)
  return {role: ROLE_LABEL[role] ? role : "client", client_id: client, scope, route: location.hash, goals: client ? followedIds(client) : null,
    ...(graph ? {graph} : {})};
}

const RESUME_S = 24 * 3600;  // the latest conversation is picked up again when it moved within a day
function dropOld() {  // before A3 the conversation lived in this tab's sessionStorage: no longer read or kept
  try { for (const k of Object.keys(sessionStorage)) if (k.startsWith("mf.copilot.")) sessionStorage.removeItem(k); } catch (_) { /* private mode */ }
}

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
const when = (t) => { const x = new Date(t * 1000); const d = new Date(); return x.toDateString() === d.toDateString() ? clock(t) : `${String(x.getDate()).padStart(2, "0")}/${String(x.getMonth() + 1).padStart(2, "0")} ${clock(t)}`; };
function meta(m) {
  const bits = [m.as_of && `Số liệu ${day(m.as_of)}`, m.at && `trả lời lúc ${clock(m.at)}`].filter(Boolean).join(" · ");
  // a web source (A5) is a link showing its host; anything else is text
  const host = (u) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return u; } };
  const source = (s) => /^https?:\/\//.test(s) ? `<a href="${esc(s)}" target="_blank" rel="noopener noreferrer" title="${esc(s)}">${esc(host(s))}</a>` : esc(s);
  const src = (m.sources || []).length ? `<div>Nguồn: ${m.sources.map(source).join(" · ")}</div>` : "";
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
      <span class="cp-tools"><button type="button" class="linkbtn" id="cp-hist" title="Các cuộc trò chuyện" aria-pressed="false">${icon("history", {size: 18})}<span class="sr-only">Các cuộc trò chuyện</span></button>
      <button type="button" class="linkbtn" id="cp-close" aria-label="Đóng">✕</button></span></header>
    <div class="cp-sess" id="cp-sess"><div class="cp-sess-main" id="cp-sess-main"></div>
      <button type="button" class="cp-new" id="cp-new" title="Bắt đầu cuộc trò chuyện mới: bộ nhớ của bạn vẫn giữ, các cuộc trước vẫn còn">${icon("plus", {size: 16})}<span>Trò chuyện mới</span></button></div>
    <div class="cp-ctx small muted" id="cp-ctx"></div>
    <div class="cp-msgs" id="cp-msgs" aria-live="polite"></div>
    <div class="cp-sugg" id="cp-sugg"></div>
    <form class="cp-form" id="cp-form"><input id="cp-q" autocomplete="off" maxlength="2000" placeholder="Hỏi về tài sản, dòng tiền, tin…" aria-label="Câu hỏi">
      <button type="submit" class="btn sm">Gửi</button></form>
    <div class="cp-foot small muted" id="cp-foot">Trợ lý chỉ dùng các chức năng sẵn có của ứng dụng; việc ghi luôn chờ bạn xác nhận. Không phải khuyến nghị đầu tư.</div>`;
  document.body.append(btn, panel);
  dropOld();
  let msgs = [], role = null, busy = false, shown = 0, settle = null, later = null;
  let cid = null, resumed = false, listing = null;  // the conversation on screen; the history list when it shows
  let sess = null, poll = 0;  // the session on screen as the server names it; the timer following a running turn
  let docked = false, live = null, run = null;  // run: the turn in flight, as its events tell it
  const covers = () => !docked && !panel.hidden && matchMedia("(max-width: 560px)").matches;  // phone: the panel hides the page

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
    if (c.role !== role) {  // another role: its own conversations
      const had = role; role = c.role; msgs = []; shown = 0; cid = null; sess = null; resumed = false; listing = null; drawSess();
      $("#cp-q", panel).placeholder = ASK[role] || ASK.client;
      if (had && !panel.hidden) { draw(); sugg(); resume(); }
    }
    const page = (docked ? document.querySelector("#ws-sheet:not([hidden]) #ws-sheet-t") || document.querySelector("#ws-title, #dk-title") || {}
      : document.querySelector("#subnav:not([hidden]) [aria-current=page]") || document.querySelector("#nav [aria-current=page]") || {}).textContent || "";
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
    $("#cp-hist", panel).setAttribute("aria-pressed", String(!!listing));
    $("#cp-sugg", panel).style.display = listing ? "none" : "";  // the history needs the room; the chips are for asking
    if (listing) { drawList(box); box.scrollTop = 0; return; }
    const fresh = (i) => (i >= shown ? " cp-in" : "");
    box.innerHTML = msgs.length ? msgs.map((m, i) => m.me
      ? `<div class="cp-me${fresh(i)}">${esc(m.text)}</div>`
      : m.status === "running"  // a turn still answering on the server (the page was reloaded): what has run so far
      ? `<div class="cp-bot cp-think" data-running><span class="cp-dots" aria-hidden="true"><i></i><i></i><i></i></span> Vẫn đang trả lời…${(m.steps || []).length ? `<div class="cp-steps small">${m.steps.map(x => `<span class="chip ${x.status === "ok" ? "" : "bad"}">${esc(x.label || x.tool)} ${STEP[x.status] || ""}</span>`).join(" ")}</div>` : ""}</div>`
      : `<div class="cp-bot${fresh(i)}${m.status === "failed" || m.status === "forbidden" ? " cp-err" : ""}">${BADGE[m.status] ? `<span class="badge ${BADGE[m.status][0]}">${BADGE[m.status][1]}</span> ` : ""}${m.mode === "model" ? prose(m.text) : esc(m.text)}
          ${(m.waits || []).length > 1 ? `<ul class="cp-notes">${m.waits.map(w => `<li>${esc(w.summary)}</li>`).join("")}</ul>` : ""}
          ${(m.cards || []).map(card).join("")}${m.status === "ok" ? meta(m) : ""}
          ${(m.steps || []).length > 1 || m.status === "interrupted" || (m.steps || []).some(s => s.status !== "ok") ? `<div class="cp-steps small muted">Các bước: ${m.steps.map(s => `<span class="chip ${s.status === "ok" ? "" : "bad"}" title="${esc(s.text || "")}">${esc(s.label || s.tool)} ${STEP[s.status] || ""}</span>`).join(" ")}</div>` : ""}
          ${(m.confirm || (m.waits || []).length) && !m.done ? `<div class="row mt"><button type="button" class="btn sm" data-ok="${i}">Xác nhận</button><button type="button" class="btn sm ghostbtn" data-no="${i}">Huỷ</button></div>` : ""}
          ${(m.citations || []).length || m.here ? `<div class="mt row">${m.here ? `<button type="button" class="linkbtn small" data-here="${i}">Chỉ trên trang</button>` : ""}${(m.citations || []).filter(c => !(m.here && c.route === location.hash)).map(c => `<a class="small" data-ev="${i}" href="${esc(c.route)}">Mở ${esc(c.label)} →</a>`).join("")}</div>` : ""}
          ${m.compacted ? `<div class="small muted mt">Các lượt trước đã được tóm tắt để trợ lý nhớ gọn; cuộc trò chuyện vẫn được lưu đủ.</div>` : ""}
          ${m.seen ? `<details class="small muted mt"><summary>Mô hình thấy gì</summary>“${esc(m.seen)}” · ${esc(m.router)}</details>` : ""}</div>`).join("")
      : `<div class="small muted">${esc(INTRO[role] || INTRO.client)} Tôi chỉ dùng các chức năng sẵn có của ứng dụng.</div>`;
    shown = msgs.length;
    box.setAttribute("aria-busy", String(busy));
    box.dataset.conversation = cid || "";
    if (busy) box.insertAdjacentHTML("beforeend", `<div class="cp-bot cp-in cp-think" data-busy>${liveHtml()}</div>`);
    box.scrollTop = box.scrollHeight;
    for (const li of box.querySelectorAll("[data-mark]")) li.onclick = () => { if (present([li.dataset.mark])) focus([li.dataset.mark]); };
    for (const b of box.querySelectorAll("[data-here]")) b.onclick = () => { show(msgs[b.dataset.here]); if (covers()) close(); };
    for (const a of box.querySelectorAll("[data-ev]")) a.onclick = () => after(msgs[a.dataset.ev].focus);
    for (const b of box.querySelectorAll("[data-ok]")) b.onclick = () => confirmIt(Number(b.dataset.ok));
    for (const b of box.querySelectorAll("[data-no]")) b.onclick = () => declineIt(Number(b.dataset.no));
  };
  // the turn in flight, as what is happening now: the question being understood, each step as the server says it
  // (“Đang xem tiền vào, tiền ra tháng 09/2026”, then done, and how long), then the results read and the answer
  // written, its words below as they come. The sentences are the server's (assistant/progress.py): never a tool's
  // id, its arguments or its result.
  const STEP_ST = {run: "đang chạy", ok: "xong", bad: "không thực hiện được"};
  const secs = (ms) => `${(ms / 1000).toFixed(1).replace(".", ",")} s`;
  const liveHtml = () => {
    const dots = `<span class="cp-dots" aria-hidden="true"><i></i><i></i><i></i></span>`;
    const row = (st, label, ms) => `<li class="cp-prog-r ${st}"><span class="cp-prog-i" aria-hidden="true">${st === "run" ? dots : st === "ok" ? "✓" : "✕"}</span><span>${esc(label)}<span class="sr-only"> · ${STEP_ST[st]}</span></span>${ms != null ? `<span class="cp-prog-t">${secs(ms)}</span>` : ""}</li>`;
    if (!run) return `<ol class="cp-prog">${row("run", "Đang hiểu câu hỏi")}</ol>`;
    const rows = [];
    // words before any step are the answer or a lead-in to a tool call: which, only the next event says
    if (!run.steps.length) rows.push(row("run", run.waiting ? "Chờ bạn xác nhận" : run.text ? "Đang trả lời" : "Đang hiểu câu hỏi"));
    else {
      rows.push(row("ok", "Đã hiểu câu hỏi", run.steps[0].at - run.t0));
      for (const x of run.steps) rows.push(row(x.st, x[x.st], x.ms));
      if (run.waiting) rows.push(row("run", "Chờ bạn xác nhận"));
      else if (run.steps.every(x => x.st !== "run")) rows.push(row("run", run.text ? "Đang viết câu trả lời" : "Đang đọc kết quả để trả lời"));
    }
    return `<ol class="cp-prog">${rows.join("")}</ol>${run.text ? `<div class="cp-live-text">${prose(run.text)}</div>` : ""}`;
  };
  // at most one redraw every 60 ms: each one lays the list out again (a burst of 37 events cost 1.2 s, one per event);
  // the graph still hears every event as it comes (tell)
  let liveTimer = 0;
  const drawLiveNow = () => { liveTimer = 0; const el = $("#cp-msgs [data-busy]", panel); if (el) el.innerHTML = liveHtml(); $("#cp-msgs", panel).scrollTop = 1e9; };
  const drawLive = () => { if (!liveTimer) liveTimer = setTimeout(drawLiveNow, 60); };
  // docked: the turn as it happens; returns the assistant's answer, or a failure that says what broke
  const streamed = async (body) => {
    run = {steps: [], text: "", waiting: false, t0: performance.now()};
    let answer = null, broke = null;
    const tell = (e) => { try { live && live.onEvent && live.onEvent(e); } catch (err) { console.error(err); } };
    tell({type: "reset"});
    try {
      await stream("/api/assistant/stream", body, (e) => {
        // words before a tool call are a lead-in (“Tôi xem dòng tiền…”), not the answer: the step says it from here,
        // and the answer streams on its own, as it will be kept
        if (e.type === "step" && e.phase === "start") {
          const name = e.label || "một chức năng";  // a server without the sentences: the step's panel name
          run.text = "";
          run.steps.push({id: e.call_id, st: "run", at: performance.now(), run: e.doing || `Đang dùng: ${name}`, ok: e.done || name, bad: e.failed || `Không thực hiện được: ${name}`});
        }
        else if (e.type === "step" && e.phase === "end") { const x = run.steps.find(s => s.id === e.call_id && s.st === "run"); if (x) { x.st = e.ok ? "ok" : "bad"; x.ms = e.ms; } }
        else if (e.type === "text") run.text += e.text;
        else if (e.type === "wait") run.waiting = true;
        else if (e.type === "answer") answer = e.assistant;
        else if (e.type === "error") broke = e.text;
        tell(e);
        if (e.type !== "answer") drawLive();
      });
    } catch (err) { broke = `Mất kết nối với trợ lý giữa chừng (${err.message}); hãy kiểm tra trên trang trước khi hỏi lại.`; }
    if (!answer && !broke) broke = "Trợ lý dừng giữa chừng, không có câu trả lời; hãy hỏi lại.";
    if (!answer) tell({type: "fail"});
    run = null;
    if (!answer) throw new Error(broke);
    return answer;
  };

  // the Copilot's answer (the fallback's confirm runs there) and the assistant's, as one message
  const fromCopilot = (a) => ({text: a.text, status: a.status, confirm: a.confirm, citations: a.evidence ? [a.evidence] : [], seen: a.seen,
    focus: a.focus || [], cards: a.card ? [a.card] : [], as_of: a.as_of, sources: a.sources, at: a.answered_at, mode: "fallback",
    router: (a.router || {}).kind === "confirm" ? "bạn xác nhận" : "định tuyến từ khóa (dự phòng)", suggest: a.suggest, navigate: a.navigate});
  const fromAssistant = (a) => ({text: a.text, status: a.status, confirm: a.confirm, waits: a.waits, turn_id: a.turn_id, steps: a.steps || [],
    citations: a.citations || [], seen: a.seen, focus: a.focus || [], cards: (a.steps || []).map(s => s.card).filter(Boolean),
    as_of: a.as_of, sources: a.sources, at: a.answered_at, mode: a.mode, model: a.model, suggest: a.suggest, navigate: a.navigate, compacted: a.compacted,
    router: a.mode === "template" ? "mô hình chỉ thấy trạng thái công cụ" : a.mode === "fallback" ? `định tuyến từ khóa (dự phòng: ${a.why || ""})` : ""});
  const mode = (m) => {  // the badge and the line under the form: how the answer was written
    if (!m || !m.mode) return;
    const [badge, foot] = (MODE[m.mode] || MODE.fallback)(m);
    const el = $("#cp-router", panel);
    el.textContent = badge; el.title = m.model || badge; $("#cp-foot", panel).textContent = foot;
  };
  const call = async (body) => {
    busy = true; listing = null; setState("busy"); draw();
    let m;
    try {
      if (body.confirm) m = fromCopilot((await post("/api/copilot", {...context(), question: "", confirm: body.confirm})).copilot);
      else {
        const req = {...context(), conversation_id: body.approvals ? null : cid, ...body};
        const a = docked && live ? await streamed(req) : (await post("/api/assistant", req)).assistant;
        if (a.conversation_id) cid = a.conversation_id;
        m = fromAssistant(a);
        named(a);
      }
    } catch (e) { m = {status: "failed", text: docked && live ? e.message : `Không gọi được trợ lý: ${e.message}`}; }
    busy = false;
    mode(m);
    msgs.push(m);
    setState(FOR[m.status] || "error");
    if (m.navigate) { after(m.focus); location.hash = m.navigate; }
    else m.here = show(m) > 0;  // on this page: mark it now, and keep a button to mark it again
    draw(); sugg(m.suggest);
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
    if (m.confirm) { msgs.push({text: "Đã huỷ, không có gì được ghi."}); setState("idle"); draw(); return; }
    msgs.push({me: true, text: "Huỷ"}); call({turn_id: m.turn_id, approvals: answers(m, "deny")});  // the run ends, nothing written
  };

  // -- the session bar (S4): its name (renamed in place), its goal, its context summary --------------------------
  const drawSess = () => {
    const box = $("#cp-sess-main", panel);
    if (!sess) {
      box.innerHTML = `<span class="cp-sess-t is-new">Cuộc trò chuyện mới</span><span class="cp-sess-goal small muted">Câu hỏi đầu tiên sẽ đặt tên cho nó · bộ nhớ của bạn vẫn dùng</span>`;
      return;
    }
    box.innerHTML = `<button type="button" class="cp-sess-t" id="cp-title" title="Đổi tên cuộc trò chuyện">${esc(sess.title || "Cuộc trò chuyện")}<i>${icon("edit", {size: 13})}</i></button>
      ${sess.goal ? `<span class="cp-sess-goal small muted" title="${esc(sess.goal)}">Mục tiêu: ${esc(sess.goal)}</span>` : ""}
      ${sess.summary ? `<details class="cp-sum small"><summary>Tóm tắt phiên</summary><div class="cp-sum-t">${prose(sess.summary)}</div><div class="muted">Các lượt cũ đã được tóm tắt để trợ lý nhớ gọn; nguyên văn vẫn lưu đủ và trợ lý đọc lại được.</div></details>` : ""}`;
    $("#cp-title", panel).onclick = () => renameHere();
  };
  const renameHere = () => {
    if (!sess || busy) return;
    const box = $("#cp-sess-main", panel);
    box.innerHTML = `<form class="cp-ren" id="cp-ren"><input id="cp-ren-q" maxlength="80" aria-label="Tên cuộc trò chuyện" value="${esc(sess.title || "")}"><button type="submit" class="linkbtn small">Lưu</button><button type="button" class="linkbtn small" id="cp-ren-x">Huỷ</button></form>`;
    const q = $("#cp-ren-q", panel); q.focus(); q.select();
    $("#cp-ren-x", panel).onclick = drawSess;
    q.onkeydown = (e) => { if (e.key === "Escape") { e.stopPropagation(); drawSess(); } };
    $("#cp-ren", panel).onsubmit = async (e) => {
      e.preventDefault();
      try { sess = (await convs("rename", sess.id, {title: q.value})).conversation; } catch (err) { alert(`Không đổi tên được: ${err.message}`); }
      drawSess();
    };
  };
  // after an answer: the session it is in, and its generated title and goal when the server says they are due
  const named = (a) => {
    if (!a.session) return;
    sess = a.session; drawSess();
    if (!a.describe) return;
    const id = sess.id;
    convs("describe", id).then((got) => { if (cid === id && got.conversation) { sess = got.conversation; drawSess(); } }).catch(() => {});
  };
  // a turn still running on the server after a reload: open the session again every 2 s until it ends
  const follow = () => {
    clearTimeout(poll);
    const last = msgs[msgs.length - 1];
    if (!cid || !last || last.status !== "running") return;
    const id = cid;
    poll = setTimeout(async () => {
      if (cid !== id) return;
      if (busy || listing) { follow(); return; }
      try {
        const got = await convs("open", id);
        if (cid !== id) return;
        msgs = replay(got.turns, got.waiting || []); sess = got.conversation; shown = msgs.length;
        draw(); drawSess();
        const end = msgs[msgs.length - 1];
        if (end && end.status !== "running") { mode(end); sugg(end.suggest); }
      } catch (_) { /* the server is restarting: try again */ }
      follow();
    }, 2000);
  };

  // -- conversations on the server (A3) ---------------------------------------------------------------------------
  const convs = async (action, conversation_id, extra = {}) =>
    (await post("/api/assistant/conversations", {role, client_id: context().client_id, action, conversation_id, ...extra})).conversations;
  // a stored turn as the panel draws it: the question, then the answer (a write still waiting keeps its buttons)
  const replay = (turns, waiting) => {
    const out = [];
    for (const t of turns) {
      const a = t.answer || {};
      if (t.question) out.push({me: true, text: t.question});
      else out.push({me: true, text: (a.steps || []).some(s => s.status === "declined") ? "Huỷ" : "Xác nhận"});
      if (t.status === "running") { out.push({status: "running", steps: a.steps || []}); continue; }
      const m = fromAssistant(a);
      if ((m.waits || []).length && !waiting.includes(a.turn_id)) m.done = true;  // answered, or too late
      if (m.confirm) m.done = true;  // the keyword path's confirm is not kept on the server
      out.push(m);
    }
    return out;
  };
  const openConv = async (id) => {
    busy = true; listing = null; draw();
    try {
      const got = await convs("open", id);
      cid = got.conversation.id; sess = got.conversation; msgs = replay(got.turns, got.waiting || []);
    } catch (e) { msgs = [{status: "failed", text: `Không mở được cuộc trò chuyện: ${e.message}`}]; cid = null; sess = null; }
    busy = false; shown = msgs.length; draw(); drawSess(); follow();
    const last = msgs[msgs.length - 1];
    mode([...msgs].reverse().find(m => m.mode));
    sugg(last && last.suggest);
  };
  const resume = async () => {  // the latest conversation, when it moved within a day
    if (resumed) return;
    resumed = true;
    try {
      const items = (await convs("list")).items || [];
      if (items[0] && Date.now() / 1000 - items[0].updated < RESUME_S && !msgs.length) await openConv(items[0].id);
    } catch (_) { /* signed out, or the server is down: start fresh */ }
  };
  const fresh = () => { clearTimeout(poll); cid = null; sess = null; msgs = []; shown = 0; listing = null; setState("idle"); draw(); drawSess(); sugg(); $("#cp-q", panel).focus(); };
  // the history (S4): search, recent or archived, grouped by day; each row opens, renames, archives or restores, deletes
  const GROUPS = [["Hôm nay", 0], ["Hôm qua", 1], ["7 ngày qua", 7], ["Cũ hơn", Infinity]];
  const groupOf = (t) => {
    const d0 = new Date(); d0.setHours(0, 0, 0, 0);
    const days = Math.ceil((d0.getTime() / 1000 - t) / 86400);  // 0 today, 1 yesterday…
    return GROUPS.find(([, n]) => days <= n)[0];
  };
  const fold = (t) => String(t || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();
  const drawList = (box) => {
    const arch = listing.view === "archived";
    box.innerHTML = `<div class="cp-hist">
      <div class="cp-hist-top"><input type="search" id="cp-hq" placeholder="Tìm cuộc trò chuyện…" aria-label="Tìm cuộc trò chuyện" value="${esc(listing.q || "")}">
        <a class="small" href="#/${role}/bo-nho" data-memory>Bộ nhớ →</a>${DESK.has(role) ? `<a class="small" href="#/${role}/agent" data-memory>Bản đồ agent →</a>` : ""}</div>
      <div class="cp-tabs" role="tablist"><button type="button" role="tab" data-view="recent" aria-selected="${!arch}">Gần đây (${listing.items.length})</button><button type="button" role="tab" data-view="archived" aria-selected="${arch}">${icon("archive", {size: 14})} Lưu trữ (${listing.archived.length})</button></div>
      <div id="cp-hl"></div></div>`;
    drawRows();
    const q = $("#cp-hq", panel);
    q.oninput = () => { listing.q = q.value; drawRows(); };
    for (const b of box.querySelectorAll("[data-view]")) b.onclick = () => { listing.view = b.dataset.view; draw(); };
    for (const a of box.querySelectorAll("[data-memory]")) a.onclick = () => { if (covers()) close(); };  // phone: the page shows
  };
  const drawRows = () => {
    const arch = listing.view === "archived";
    const words = fold(listing.q).split(/\s+/).filter(Boolean);
    const rows = (arch ? listing.archived : listing.items).filter(c => words.every(w => fold(`${c.title} ${c.goal || ""}`).includes(w)));
    const el = $("#cp-hl", panel);
    if (!rows.length) {
      el.innerHTML = `<div class="small muted cp-hist-none">${words.length ? "Không có cuộc trò chuyện nào khớp." : arch ? "Chưa lưu trữ cuộc trò chuyện nào." : "Chưa có cuộc trò chuyện nào. Hỏi một câu để bắt đầu."}</div>`;
      return;
    }
    let html = "", last = null;
    for (const c of rows) {
      const g = groupOf(c.updated);
      if (g !== last) { if (last) html += "</ul>"; html += `<div class="cp-grp">${g}</div><ul class="cp-convs">`; last = g; }
      html += `<li${c.id === cid ? ' aria-current="true"' : ""} data-row="${esc(c.id)}"><button type="button" class="cp-conv" data-open="${esc(c.id)}"><b>${esc(c.title || "Cuộc trò chuyện")}</b>${c.goal ? `<span class="cp-conv-goal">${esc(c.goal)}</span>` : ""}<small>${esc(when(c.updated))} · ${c.turns} lượt</small></button>
        <span class="cp-row-acts"><button type="button" class="linkbtn small" data-ren="${esc(c.id)}" title="Đổi tên">${icon("edit", {size: 15})}<span class="sr-only">Đổi tên</span></button>
        ${arch ? `<button type="button" class="linkbtn small" data-res="${esc(c.id)}" title="Khôi phục về Gần đây">${icon("undo", {size: 15})}<span class="sr-only">Khôi phục</span></button>`
               : `<button type="button" class="linkbtn small" data-arc="${esc(c.id)}" title="Lưu trữ (ẩn khỏi danh sách, không xoá)">${icon("archive", {size: 15})}<span class="sr-only">Lưu trữ</span></button>`}
        <button type="button" class="linkbtn small" data-del="${esc(c.id)}" title="Xoá hẳn">${icon("x", {size: 15})}<span class="sr-only">Xoá</span></button></span></li>`;
    }
    el.innerHTML = html + "</ul>";
    for (const b of el.querySelectorAll("[data-open]")) b.onclick = () => openConv(b.dataset.open);
    for (const b of el.querySelectorAll("[data-arc]")) b.onclick = () => act("archive", b.dataset.arc);
    for (const b of el.querySelectorAll("[data-res]")) b.onclick = () => act("restore", b.dataset.res);
    for (const b of el.querySelectorAll("[data-ren]")) b.onclick = () => renameRow(b.dataset.ren);
    for (const b of el.querySelectorAll("[data-del]")) b.onclick = async () => {
      if (!confirm("Xoá hẳn cuộc trò chuyện này? Không lấy lại được. (Lưu trữ thì chỉ ẩn đi.)")) return;
      try { await convs("delete", b.dataset.del); } catch (e) { alert(`Không xoá được: ${e.message}`); }
      if (b.dataset.del === cid) { cid = null; sess = null; msgs = []; shown = 0; drawSess(); }
      showList();
    };
  };
  const act = async (action, id) => {
    try {
      const got = (await convs(action, id)).conversation;
      if (id === cid) { sess = got; drawSess(); }
    } catch (e) { alert(`Không thực hiện được: ${e.message}`); }
    showList();
  };
  const renameRow = (id) => {
    const li = $(`[data-row="${CSS.escape(id)}"]`, panel);
    const c = [...listing.items, ...listing.archived].find(x => x.id === id);
    if (!li || !c) return;
    li.innerHTML = `<form class="cp-ren"><input maxlength="80" aria-label="Tên cuộc trò chuyện" value="${esc(c.title || "")}"><button type="submit" class="linkbtn small">Lưu</button><button type="button" class="linkbtn small" data-x>Huỷ</button></form>`;
    const q = li.querySelector("input"); q.focus(); q.select();
    li.querySelector("[data-x]").onclick = drawRows;
    q.onkeydown = (e) => { if (e.key === "Escape") { e.stopPropagation(); drawRows(); } };
    li.querySelector("form").onsubmit = async (e) => {
      e.preventDefault();
      try {
        const got = (await convs("rename", id, {title: q.value})).conversation;
        Object.assign(c, got);
        if (id === cid) { sess = got; drawSess(); }
      } catch (err) { alert(`Không đổi tên được: ${err.message}`); }
      drawRows();
    };
  };
  const showList = async () => {
    if (busy) return;
    const keep = listing ? {view: listing.view, q: listing.q} : {view: "recent", q: ""};
    try {
      const [a, b] = await Promise.all([convs("list"), convs("list_archived")]);
      listing = {...keep, items: a.items || [], archived: b.items || []};
    } catch (e) { listing = {...keep, items: [], archived: []}; }
    draw();
  };
  $("#cp-new", panel).onclick = () => { if (!busy) fresh(); };
  // the Bộ nhớ page opens a conversation here (A4)
  window.addEventListener("mf:open-conversation", (e) => {
    if (busy) return;
    drawCtx(); resumed = true;
    if (panel.hidden) { panel.hidden = false; btn.setAttribute("aria-expanded", "true"); }
    openConv(e.detail.id);
  });
  $("#cp-hist", panel).onclick = () => { if (listing) { listing = null; draw(); } else showList(); };

  const open = () => { drawCtx(); draw(); drawSess(); sugg(); panel.hidden = false; btn.setAttribute("aria-expanded", "true"); $("#cp-q", panel).focus(); resume(); };
  const close = () => { if (docked) return; panel.hidden = true; btn.setAttribute("aria-expanded", "false"); if (btn.dataset.state === "error") setState("idle"); btn.focus();
    if (later) { const k = later; later = null; focus(k); } };
  btn.onclick = () => (panel.hidden ? open() : close());
  $("#cp-close", panel).onclick = close;
  panel.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
  $("#cp-form", panel).onsubmit = (e) => { e.preventDefault(); send($("#cp-q", panel).value); };
  window.addEventListener("hashchange", () => { if (!panel.hidden) setTimeout(drawCtx); });  // after the route names its view
  let watched = false;

  return {
    dock(host, hooks) {
      if (docked) return;
      docked = true; live = hooks || null;
      panel.classList.add("cp-docked"); panel.setAttribute("role", "region");
      host.appendChild(panel);
      btn.hidden = true;
      if (!watched) {  // the lens or the sheet changes without a route change, or after it: name what is on screen (D30)
        watched = true;
        const redraw = new MutationObserver(() => { if (docked) drawCtx(); });
        for (const el of [document.querySelector("#ws-title"), document.querySelector("#ws-sheet")]) {
          if (el) redraw.observe(el, { childList: true, characterData: true, subtree: true, attributes: true, attributeFilter: ["hidden"] });
        }
      }
      drawCtx(); draw(); drawSess(); sugg(); panel.hidden = false; resume();
    },
    undock() {
      if (!docked) return;
      docked = false; live = null;
      panel.classList.remove("cp-docked"); panel.setAttribute("role", "dialog");
      document.body.appendChild(panel);
      panel.hidden = true; btn.hidden = false; btn.setAttribute("aria-expanded", "false");
    },
  };
}
