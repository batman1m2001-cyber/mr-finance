/* The shared core of the new pages: the API client, number formats, small DOM helpers and the
   components every page uses (states, badges, drawer, toast). Business rules live on the server:
   pages receive status, severity and labels already decided. */

// ── api ──────────────────────────────────────────────────────────────────────
export async function get(path) {
  const r = await fetch(path);
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.error || `${path}: ${r.status}`);
  return body;
}

export async function post(path, body) {
  const r = await fetch(path, {method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify(body || {})});
  const out = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(errorText(out) || `${path}: ${r.status}`);
  if (out && out.$errors) throw new Error(errorText(out));
  return out;
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

// ── formats (Vietnamese) ─────────────────────────────────────────────────────
const TY = 1e9, TR = 1e6;
const vn = (x, d) => {
  let s = x.toFixed(d).replace(".", ",");
  if (s.includes(",")) s = s.replace(/0+$/, "").replace(/,$/, "");
  const [int, frac] = s.split(",");
  return int.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + (frac ? "," + frac : "");
};
export function vnd(a, signed) {
  if (a == null || Number.isNaN(a)) return "—";
  const sign = signed && a > 0 ? "+" : a < 0 ? "−" : "";
  const x = Math.abs(a);
  if (x >= TY) return sign + vn(x / TY, x < 10 * TY ? 2 : 1) + " tỷ";
  if (x >= TR) return sign + vn(x / TR, x >= 100 * TR ? 0 : 1) + " triệu";
  return sign + vn(x, 0) + " đ";
}
export function pct(x, signed, digits) {
  if (x == null || Number.isNaN(x)) return "—";
  const sign = signed && x > 0 ? "+" : x < 0 ? "−" : "";
  return sign + vn(Math.abs(x) * 100, digits == null ? 1 : digits) + "%";
}
export function num(x, d) { return x == null ? "—" : (x < 0 ? "−" : "") + vn(Math.abs(x), d == null ? 0 : d); }
export function when(ts) {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getHours())}:${p(d.getMinutes())} ${p(d.getDate())}/${p(d.getMonth() + 1)}`;
}
export function ago(ts) {
  if (!ts) return "—";
  const s = Math.max(0, Date.now() / 1000 - ts);
  if (s < 90) return "vừa xong";
  if (s < 3600) return `${Math.round(s / 60)} phút trước`;
  if (s < 86400) return `${Math.round(s / 3600)} giờ trước`;
  return `${Math.round(s / 86400)} ngày trước`;
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
export function followedIds(client) {
  try { return JSON.parse(localStorage.getItem(`mf.goals.${client}`) || "null"); } catch (_) { return null; }
}
