/* The shared core of the new pages: the API client, number formats, small DOM helpers and the
   components every page uses (states, badges, drawer, toast). Business rules live on the server:
   pages receive status, severity and labels already decided. */
import {english, t as tr} from "./i18n.js?v=20261030f8";
export {english, lang, setLang, t} from "./i18n.js?v=20261030f8";

// ── api ──────────────────────────────────────────────────────────────────────
// What a page read is kept for the tab: going back to a page draws it at once from what it had, while the same reads
// go to the server again; when an answer differs, the shell draws the page once more (`keep`). A POST that is not a
// read forgets everything kept, so a page never shows what was true before the person's own change.
const READS = new Set(["/api/dashboard", "/api/overview", "/api/flows", "/api/feed", "/api/goals", "/api/alerts", "/api/scenario"]);
const KEPT_MAX = 80;
const kept = new Map();  // "GET /api/…" or "POST /api/…{body}" → the answer's JSON text, oldest first
let round = null;  // the page being drawn: {used, pending, changed, again}
let generation = 0;  // counts the changes: an answer asked for before one is never kept

function forget() {
  kept.clear();
  generation++;
}

function remember(key, text, gen) {
  if (gen !== generation) return;
  kept.delete(key);
  kept.set(key, text);
  if (kept.size > KEPT_MAX) kept.delete(kept.keys().next().value);
}

async function keptOr(key, load) {
  const r = round, gen = generation;
  // a page reads each thing once from what was kept, during its own drawing only: a later read (a poll, a click)
  // is always the server's answer
  if (r && !r.used.has(key) && kept.has(key)) {
    r.used.add(key);
    const text = kept.get(key);
    if (!r.again) {
      r.pending.push(load().then((fresh) => {
        const t = JSON.stringify(fresh);
        remember(key, t, gen);
        if (t !== text && gen === generation) r.changed = true;
      }, () => { /* the page already shows what it had; the next visit asks again */ }));
    }
    return JSON.parse(text);
  }
  if (r) r.used.add(key);
  const fresh = await load();
  remember(key, JSON.stringify(fresh), gen);
  return fresh;
}

// the shell around one drawing of a page: `begin` before it, `end` after it, which waits for the reads asked again
// and says whether any answer changed; `again` draws from what is kept, asking nothing (the redraw after a change)
export const keep = {
  begin(again = false) { round = {used: new Set(), pending: [], changed: false, again}; return round; },
  async end(r) {
    if (round === r) round = null;
    await Promise.all(r.pending);
    return r.changed;
  },
  forget,
};

async function fetchGet(path) {
  const r = await fetch(path);
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.error || `${path}: ${r.status}`);
  return body;
}

async function fetchPost(path, body) {
  const r = await fetch(path, {method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify(body || {})});
  const out = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(errorText(out) || `${path}: ${r.status}`);
  if (out && out.$errors) throw new Error(errorText(out));
  return out;
}

/* A POST answered as server-sent events (FEAT-40, POST /api/assistant/stream): each event to onEvent, in order, as it
   arrives; resolves when the stream ends, rejects when it breaks or is refused. It may have changed something (a
   confirmed write): nothing kept is sure any more. */
export async function stream(path, body, onEvent) {
  try {
    const r = await fetch(path, {method: "POST", headers: {"content-type": "application/json", accept: "text/event-stream"}, body: JSON.stringify(body || {})});
    if (!r.ok || !r.body || !(r.headers.get("content-type") || "").startsWith("text/event-stream")) {
      throw new Error(errorText(await r.json().catch(() => ({}))) || `${path}: ${r.status}`);
    }
    const reader = r.body.pipeThrough(new TextDecoderStream()).getReader();
    let buf = "";
    for (;;) {
      const {value, done} = await reader.read();
      if (done) break;
      buf = (buf + value).replace(/\r\n/g, "\n");
      for (let i = buf.indexOf("\n\n"); i >= 0; i = buf.indexOf("\n\n")) {
        const data = buf.slice(0, i).split("\n").filter(l => l.startsWith("data:")).map(l => l.slice(5).replace(/^ /, "")).join("\n");
        buf = buf.slice(i + 2);
        if (!data) continue;
        let item;
        try { item = JSON.parse(data); } catch (_) { continue; }
        onEvent(item && item.event && item.event.type ? item.event : item);
      }
    }
  } finally {
    forget();
  }
}

export function get(path) {
  return keptOr(`GET ${path}`, () => fetchGet(path));
}

// A POST that only reads the person's own records (the bell's follow-ups, the Bộ nhớ page's lists): not kept, since
// it changes elsewhere, and it forgets nothing.
export const read = (path, body) => fetchPost(path, body);

export async function post(path, body) {
  if (READS.has(path)) return keptOr(`POST ${path}${JSON.stringify(body || {})}`, () => fetchPost(path, body));
  try {
    return await fetchPost(path, body);
  } finally {
    forget();  // a change, made or tried: nothing kept is sure any more
  }
}

function errorText(out) {
  if (!out) return "";
  if (out.error) return String(out.error);
  const errs = out.$errors || out.errors;
  if (errs && typeof errs === "object") {
    const first = Object.values(errs)[0];
    const msg = (first && (first.message || first)) || "";
    // the op's own message, without the traceback
    const lines = String(msg).trim().split("\n");
    return lines[lines.length - 1].replace(/^\w+Error: /, "");
  }
  return out.detail ? String(out.detail) : "";
}

// ── formats (the viewer's language: “1,25 tỷ” / “1.25 bn”) ───────────────────
const TY = 1e9, TR = 1e6;
const [DOT, COMMA] = english ? [",", "."] : [".", ","];  // thousands, decimals
export const LOCALE = english ? "en-US" : "vi-VN", DECIMAL = COMMA;  // for toLocaleString and hand-made decimals
const UNITS = english ? [" bn", " mn", " k", " ₫"] : [" tỷ", " triệu", " nghìn", " đ"];
const vn = (x, d) => {
  let s = x.toFixed(d).replace(".", ",");
  if (s.includes(",")) s = s.replace(/0+$/, "").replace(/,$/, "");
  const [int, frac] = s.split(",");
  return int.replace(/\B(?=(\d{3})+(?!\d))/g, DOT) + (frac ? COMMA + frac : "");
};
export function vnd(a, signed) {
  if (a == null || Number.isNaN(a)) return "—";
  const sign = signed && a > 0 ? "+" : a < 0 ? "−" : "";
  const x = Math.abs(a);
  if (x >= TY) return sign + vn(x / TY, x < 10 * TY ? 2 : 1) + UNITS[0];
  if (x >= TR) return sign + vn(x / TR, x >= 100 * TR ? 0 : 1) + UNITS[1];
  if (x >= 1e3) return sign + vn(x / 1e3, x >= 1e5 ? 0 : 1) + UNITS[2];  // as src/wealth/money.py: “192 nghìn”
  return sign + vn(x, 0) + UNITS[3];
}
export function pct(x, signed, digits) {
  if (x == null || Number.isNaN(x)) return "—";
  const sign = signed && x > 0 ? "+" : x < 0 ? "−" : "";
  return sign + vn(Math.abs(x) * 100, digits == null ? 1 : digits) + "%";
}
export function num(x, d) { return x == null ? "—" : (x < 0 ? "−" : "") + vn(Math.abs(x), d == null ? 0 : d); }
// a name cut to k characters at a word boundary, with “…”; never half a word (the full name goes in a title)
export function words(s, k) {
  s = tr(String(s || ""));  // cut in the viewer's language
  if (s.length <= k) return s;
  const c = s.slice(0, k - 1), sp = s[k - 1] === " " ? c.length : c.lastIndexOf(" ");
  return (sp > 0 ? c.slice(0, sp) : c).replace(/[\s,.;:(–-]+$/, "") + "…";
}
export function when(ts) {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getHours())}:${p(d.getMinutes())} ${p(d.getDate())}/${p(d.getMonth() + 1)}`;
}
export function ago(ts) {
  if (!ts) return "—";
  const s = Math.max(0, Date.now() / 1000 - ts);
  if (s < 90) return english ? "just now" : "vừa xong";
  const [n, u] = s < 3600 ? [Math.round(s / 60), "phút"] : s < 86400 ? [Math.round(s / 3600), "giờ"] : [Math.round(s / 86400), "ngày"];
  if (!english) return `${n} ${u} trước`;
  return `${n} ${{"phút": "min", "giờ": "h", "ngày": n === 1 ? "day" : "days"}[u]} ago`;
}
export const signClass = (x) => (x > 0 ? "up" : x < 0 ? "down" : "flat");

// ── dom ──────────────────────────────────────────────────────────────────────
export const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
export const $ = (s, root) => (root || document).querySelector(s);
export const $$ = (s, root) => [...(root || document).querySelectorAll(s)];
export function on(root, sel, ev, fn) {
  root.addEventListener(ev, (e) => {
    const t = e.target.closest(sel);
    if (t && root.contains(t)) fn(e, t);
  });
}

// ── components ───────────────────────────────────────────────────────────────
export const loading = (rows = 3) =>
  `<div class="stack" aria-busy="true">${'<div class="skeleton" style="height:64px"></div>'.repeat(rows)}</div>`;
export const empty = (title, hint) =>
  `<div class="state"><div class="icon" aria-hidden="true">◌</div><div><b>${esc(title)}</b></div>${hint ? `<div class="small">${hint}</div>` : ""}</div>`;
export const failed = (e) =>
  `<div class="state error" role="alert"><div class="icon" aria-hidden="true">!</div><div>Không tải được: ${esc(e && e.message || e)}</div></div>`;

const SEV = {critical: ["bad", "Nghiêm trọng"], medium: ["warn", "Trung bình"], low: ["", "Thấp"]};
export const severity = (s) => `<span class="badge ${SEV[s] ? SEV[s][0] : ""}">${SEV[s] ? SEV[s][1] : esc(s)}</span>`;

const RUN = {EFFECTIVE: "good", NEEDS_CIO_REVIEW: "warn", FAILED: "bad", WITHDRAWN: "bad", SUPERSEDED: "", COMPUTING: "", POST_CHECKING: ""};
export const runBadge = (status, label) => `<span class="badge ${RUN[status] || ""}">${esc(label || status)}</span>`;

const VIEW = {
  DRAFTING: ["", "Đang soạn"], PENDING_CHALLENGE: ["ai", "Chờ phản biện"], PENDING_APPROVAL: ["human", "Chờ CIO duyệt"],
  APPROVED: ["good", "Đã duyệt"], AGENT_ERROR: ["bad", "Agent lỗi"], REWORK_REQUESTED: ["warn", "Trả lại"],
  REJECTED: ["bad", "Bác"], WITHDRAWN: ["bad", "Thu hồi"], SUPERSEDED: ["", "Đã thay thế"],
};
export const viewBadge = (s) => `<span class="badge ${VIEW[s] ? VIEW[s][0] : ""}">${VIEW[s] ? VIEW[s][1] : esc(s)}</span>`;
export const viewLabel = (s) => (VIEW[s] ? VIEW[s][1] : s);

export function toast(msg) {
  const t = document.createElement("div");
  t.className = "toast";
  t.setAttribute("role", "status");
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3200);
}

let drawerOpen = null;
export function drawer(title, html) {
  closeDrawer();
  const back = document.createElement("div");
  back.className = "drawer-back";
  const box = document.createElement("aside");
  box.className = "drawer";
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");
  box.setAttribute("aria-label", title);
  box.innerHTML = `<header><b>${esc(title)}</b><button type="button" class="iconbtn" aria-label="Đóng">✕</button></header><div class="body">${html}</div>`;
  document.body.append(back, box);
  const close = () => closeDrawer();
  back.onclick = close;
  box.querySelector("header button").onclick = close;
  const key = (e) => { if (e.key === "Escape") close(); };
  document.addEventListener("keydown", key);
  drawerOpen = {back, box, key};
  box.querySelector("header button").focus();
  return box.querySelector(".body");
}
export function closeDrawer() {
  if (!drawerOpen) return;
  drawerOpen.back.remove();
  drawerOpen.box.remove();
  document.removeEventListener("keydown", drawerOpen.key);
  drawerOpen = null;
}

export const ASSET_CLASS = {
  cash: "Tiền mặt", deposit: "Tiền gửi", stock: "Cổ phiếu", bond: "Trái phiếu", fund: "Chứng chỉ quỹ",
  real_estate: "Bất động sản", gold: "Vàng", business: "Cổ phần tư nhân", insurance: "Bảo hiểm", crypto: "Tiền số",
  loan: "Khoản vay", card: "Dư nợ thẻ", fx: "Ngoại tệ",
};
// colour follows the asset class, never its rank (the legacy pages use the same slots)
export const CLASS_COLOR = {
  real_estate: "var(--s1)", stock: "var(--s2)", deposit: "var(--s3)", cash: "var(--s3)", gold: "var(--s4)", fund: "var(--s5)",
  business: "var(--s6)", bond: "var(--s7)", crypto: "var(--s8)", loan: "var(--other)", card: "var(--other)",
  insurance: "var(--other)", fx: "var(--other)",
};
export const HORIZON = {"1w": "1 tuần", "3m": "3 tháng", "12m": "12 tháng"};

export const EVENT_TYPE = {
  monetary: "Chính sách tiền tệ", fx: "Tỷ giá", gold: "Vàng", credit: "Tín dụng, trái phiếu", real_estate: "Bất động sản",
  regulation: "Chính sách, quy định", commodity: "Hàng hóa", crypto: "Tiền số", equity: "Thị trường cổ phiếu",
  geopolitics: "Địa chính trị, thương mại",
};

// BRD §14 (RULE-SEC-03): staff screens say they are internal
export const internal = () => `<div class="internal" role="note"><span class="badge">Nội bộ</span> Chỉ nhân viên xem được; khách hàng không thấy trang này.</div>`;

// the goals the client follows on Kế hoạch, kept in this browser (null: the server's defaults)
// what the Customer's workspace shows, for the assistant's request (UNIFIED_FLOWS_PLAN F10): set by the workspace
export const workspaceContext = {get: () => null};

export function followedIds(client) {
  try { return JSON.parse(localStorage.getItem(`mf.goals.${client}`) || "null"); } catch (_) { return null; }
}

// ── cách tính (BRD-NFR-11): every number carries what it is; the drawer reads the formula from the server ─────
// n(text, metric, inputs): a number as a focusable control (a span, so it can sit inside a row that is itself a
// button or a link); inputs {key: shown value} come from the same server answer as the number.
export function n(text, metric, inputs) {
  const data = inputs ? ` data-in="${esc(JSON.stringify(inputs))}"` : "";
  return `<span class="how-n" role="button" tabindex="0" data-metric="${esc(metric)}"${data}>${text}</span>`;
}
// the same for an SVG <text>: attributes, focusable
export const nAttrs = (metric, inputs) =>
  ` data-metric="${esc(metric)}"${inputs ? ` data-in="${esc(JSON.stringify(inputs))}"` : ""} tabindex="0" role="button" class="num-svg"`;

export const howAudience = {staff: false};
let howCatalogue = null;
async function catalogue() {
  if (!howCatalogue) howCatalogue = get("/api/how").catch((e) => { howCatalogue = null; throw e; });
  return howCatalogue;
}
// one metric's entry (label, formula, inputs), from the same catalogue the drawer reads; null when it has none
export async function formulaOf(id) {
  try { return (await catalogue())[id] || null; } catch (_) { return null; }
}
async function openHowOf(el) {
  const id = el.dataset.metric;
  let inputs = {};
  try { inputs = JSON.parse(el.dataset.in || "{}"); } catch (_) { /* no inputs */ }
  const body = drawer("Cách tính", loading(2));
  try {
    const m = (await catalogue())[id];
    if (!m) throw new Error(`chưa có cách tính cho “${id}”`);
    const rows = Object.entries(m.inputs || {}).filter(([k]) => inputs[k] != null)
      .map(([k, label]) => `<tr><td>${esc(label)}</td><td class="r">${esc(inputs[k])}</td></tr>`).join("");
    const extra = Object.entries(inputs).filter(([k]) => !(m.inputs || {})[k])
      .map(([k, v]) => `<tr><td>${esc(k)}</td><td class="r">${esc(v)}</td></tr>`).join("");
    body.innerHTML = `<div class="how">
      <div class="small muted">${esc(m.label)}</div>
      <div class="how-value">${esc(el.textContent.trim())}</div>
      <h4>Công thức</h4><p data-explains>${esc(m.formula)}</p>
      ${rows || extra ? `<h4>Đầu vào</h4><table class="table" data-explains><tbody>${rows}${extra}</tbody></table>` : ""}
      ${howAudience.staff ? `<p class="small muted">Tính tại <code>${esc(m.code)}</code></p>` : ""}</div>`;
  } catch (e) {
    body.innerHTML = failed(e);
  }
}
export function explainOn(root) {
  root.addEventListener("click", (e) => {
    const el = e.target.closest("[data-metric]");
    if (el && !el.closest(".drawer")) { e.preventDefault(); e.stopPropagation(); openHowOf(el); }
  }, true);
  root.addEventListener("keydown", (e) => {
    const el = e.target.closest && e.target.closest("[data-metric]");
    if (el && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); openHowOf(el); }
  });
}
