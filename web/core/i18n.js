/* The language of the page (docs/LANGUAGE_PLAN.md): English unless the viewer picked Vietnamese (`mf.lang`). The
   pages are written in Vietnamese; in English each text and each label the browser draws is looked up in the phrase
   book, lang/en.js. A phrase with a value in it is a pattern — “{0} tài sản” → “{0} assets” — and the value is looked
   up too. Not in the book: shown as written, so news, names and what people typed stay as they are. Inputs, text
   areas and anything under [data-raw] are never touched. */

const KEY = "mf.lang";
function stored() { try { return localStorage.getItem(KEY); } catch (_) { return null; } }

export const lang = stored() === "vi" ? "vi" : "en";
export const english = lang === "en";

export function setLang(l) {
  try { localStorage.setItem(KEY, l === "vi" ? "vi" : "en"); } catch (_) { /* private mode: this page only */ }
  location.reload();  // every page and number drawn once in the new language
}

// the evidence frames' own book (written by scripts/make_evidence.py) sits beside the pages' one
const book = english ? {...(await import("./lang/en_evidence.js?v=20261030f5")).default, ...(await import("./lang/en.js?v=20261030f5")).default} : {};

// ── the book, indexed ───────────────────────────────────────────────────────
const VI = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i;
const exact = new Map();
const patterns = [];  // {re, slots, out, lit}, the most specific first
const reEsc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
for (const [k, v] of Object.entries(book)) {
  const key = k.replace(/\s+/g, " ").trim();
  if (!/\{=?\d+\}/.test(key)) { exact.set(key, v); continue; }
  // {0} is a value that must read as one (a phrase, a number, a name); {=0} is data — a headline, an asset's own name —
  // kept as written when it is not a phrase
  const parts = key.split(/\{(=?\d+)\}/), slots = [], loose = [];
  let re = "^";
  parts.forEach((p, i) => {
    if (i % 2) { re += "(.+?)"; slots.push(+p.replace("=", "")); loose.push(p[0] === "="); } else re += reEsc(p);
  });
  const lits = parts.filter((_, i) => i % 2 === 0);
  patterns.push({re: new RegExp(re + "$", "s"), slots, loose, out: v, lit: lits.reduce((a, b) => (b.length > a.length ? b : a), ""),
    size: lits.join("").length});
}
patterns.sort((a, b) => b.size - a.size);

// a number the server wrote the Vietnamese way (“1,2 tỷ”, “1.250”, “12,5%”) in the English way (“1.2 bn”, “1,250”)
const UNIT = {"tỷ": "bn", "triệu": "mn", "nghìn": "k", "đồng": "₫", "đ": "₫"};
const looksVi = (s) => /\d\.\d{3}(?!\d)/.test(s) || /\d,(\d{1,2}|\d{4,})(?!\d)/.test(s) || /\d\s?(tỷ|triệu|nghìn|đồng|đ)(?![\p{L}\d])/u.test(s);
export function numbers(s) {
  if (!looksVi(s)) return s;
  return s.replace(/(\d{1,3}(?:\.\d{3})+|\d+)(,\d+)?(?:(\s?)(tỷ|triệu|nghìn|đồng|đ)(?![\p{L}\d]))?/gu, (m, int, frac, sp, unit) =>
    int.replace(/\./g, ",") + (frac ? "." + frac.slice(1) : "") + (unit ? " " + UNIT[unit] : ""));
}

function lookup(core, depth) {
  const v = exact.get(core);
  if (v !== undefined) return v;
  if (!VI.test(core)) return null;
  // “Tài sản:” is “Tài sản” and its colon; “· hằng tháng” is a dot and “hằng tháng”
  const edge = core.match(/^([\s:·…,.;!?()–—-]*)(.*?)([\s:·…,.;!?()–—-]*)$/s);
  if (edge && (edge[1] || edge[3]) && exact.has(edge[2])) return edge[1] + exact.get(edge[2]) + edge[3];
  if (depth > 2) return null;
  for (const p of patterns) {
    if (!core.includes(p.lit)) continue;
    const m = p.re.exec(core);
    if (!m) continue;
    const vals = p.slots.map((_, at) => value(m[at + 1], depth + 1, p.loose[at]));
    if (vals.includes(null)) continue;  // a headline that only happens to contain “tháng” is not this pattern
    return p.out.replace(/\{(\d+)\}/g, (_, i) => {
      const at = p.slots.indexOf(+i);
      return at < 0 ? "" : vals[at];
    });
  }
  if (/^[\s\d.,%+\-−]*(tỷ|triệu|nghìn|đồng|đ)?$/u.test(core)) return numbers(core);
  // “Nhận định · 26/10 · Vàng · CafeF · Trong nước”: parts joined by dots, each a phrase or a value
  if (core.includes(" · ")) {
    const vals = core.split(" · ").map((x) => value(x, depth + 1));
    if (!vals.includes(null)) return vals.join(" · ");
  }
  // “summary: có từ ngữ…; impacts[3].rationale: …”: a list of checks, each a phrase of the book
  if (core.includes("; ")) {
    const parts = core.split("; ").map((x) => lookup(x, depth + 1));
    if (!parts.includes(null)) return parts.join("; ");
  }
  // “cổ phiếu & quỹ, trái phiếu, vàng”: a list whose every item is a phrase of the book
  if (core.includes(", ")) {
    const parts = core.split(", ").map((x) => lookup(x, depth + 1));
    if (!parts.includes(null)) return parts.join(", ");
  }
  return null;
}

// a value inside a pattern: a phrase of the book, or something that reads as a value — a number, a code, a name
// (“Nguyễn Minh Khoa”: every word capitalised). Any other Vietnamese is not a value: “Chủ tài khoản” is not
// “{0} khoản”, and a headline that contains “tháng” is not “{0} tháng”; the text is data and stays as written.
const NAME = /^[\p{Lu}\d][\p{L}\d.'-]*$/u;
function value(v, depth, loose = false) {
  const core = v.trim();
  const t = lookup(core, depth);
  if (t != null) return v.replace(core, t);
  const ws = core.split(" ");  // a name has two to five words: “Tài” alone is the start of “Tài khoản”, not a name
  if (VI.test(core) && !loose && !(ws.length >= 2 && ws.length <= 5 && ws.every((w) => NAME.test(w)))) return null;
  return numbers(v);
}

const memo = new Map();
// one phrase in the viewer's language (the leading and trailing spaces kept)
export function t(s) {
  if (!english || !s) return s;
  const hit = memo.get(s);
  if (hit !== undefined) return hit;
  const core = s.replace(/\s+/g, " ").trim();
  let out = s;
  if (core) {
    const tr = lookup(core, 0);
    if (tr != null) out = s.match(/^\s*/)[0] + tr + s.match(/\s*$/)[0];
    else if (!/\p{L}/u.test(core)) out = numbers(s);
  }
  if (memo.size > 20000) memo.clear();
  memo.set(s, out);
  return out;
}

// ── the page, as it is drawn ────────────────────────────────────────────────
const ATTRS = ["placeholder", "aria-label", "title", "alt", "data-tip"];
const SKIP = "script, style, textarea, [data-raw], [contenteditable]";

function text(n) {
  const p = n.parentElement;
  if (!p || p.closest(SKIP)) return;
  const s = n.data, o = t(s);
  if (o !== s) n.data = o;
  else if (VI.test(s)) split.add(p);
}

// A phrase split by markup — “dự báo 12 tháng tới: vào <b>…</b> · ra <b>…</b>” — misses as pieces. The element is
// then read as one phrase, each child element a value; the English puts the same child elements in its own order.
const split = new Set(), tok = (i) => String.fromCharCode(0xE000 + i), TOK = /([-])/;
function joined(el) {
  if (!el.isConnected || el.closest(SKIP) || el.childElementCount === 0 || el.childElementCount > 8) return;
  const kids = [];
  let s = "";
  for (const c of el.childNodes) {
    if (c.nodeType === 3) s += c.data;
    else if (c.nodeType === 1) { s += tok(kids.length); kids.push(c); }
  }
  if (s.length > 400 || !VI.test(s)) return;
  const o = t(s);
  if (o === s) return;
  const parts = o.split(TOK), used = new Set();
  const nodes = parts.map((x, i) => {
    if (i % 2 === 0) return x ? document.createTextNode(x) : null;
    const k = x.charCodeAt(0) - 0xE000;
    used.add(k);
    return kids[k];
  }).filter(Boolean);
  if (used.size !== kids.length || parts.length !== kids.length * 2 + 1) return;  // every child once, or leave it
  el.replaceChildren(...nodes);
}
function flush() { for (const el of split) joined(el); split.clear(); }

function attrs(el) {
  if (el.closest(SKIP)) return;
  for (const a of ATTRS) {
    const s = el.getAttribute(a);
    if (s) { const o = t(s); if (o !== s) el.setAttribute(a, o); }
  }
}

function apply(root) {
  if (root.nodeType === 3) return text(root);
  if (root.nodeType !== 1) return;
  attrs(root);
  const w = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) (n.nodeType === 3 ? text : attrs)(n);
}

if (english) {
  document.documentElement.lang = "en";
  apply(document.head);
  apply(document.body);
  flush();
  new MutationObserver((ms) => {
    for (const m of ms) {
      if (m.type === "characterData") text(m.target);
      else if (m.type === "attributes") attrs(m.target);
      else for (const n of m.addedNodes) apply(n);
    }
    flush();
  }).observe(document.documentElement, {subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRS});
  for (const f of ["alert", "confirm", "prompt"]) {
    const own = window[f].bind(window);
    window[f] = (msg, ...rest) => own(t(String(msg == null ? "" : msg)), ...rest);
  }
}
