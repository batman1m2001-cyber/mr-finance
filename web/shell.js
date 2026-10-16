/* The shell: roles, navigation, routing, the client picker and scope, theme, demo reset. Each role sees its own
   pages (docs/NEWS_IMPACT_PLAN.md §5); every page is a module in pages/ rendered into #page (ADR-0019). The
   address is the route: #/cio/nhan-dinh/VW-0001-v1.

   Everyone signs in with their own account (BRD-RULE-SEC-01, pages/signin.js): the shell then shows only that
   person's role, and the client picker only the families they may see (a client: none, their own family). The
   server takes the user from the session, never from the page. Only with sign-in switched off (MF_AUTH=off, a
   developer's machine) does the old role switcher appear. */
import {$, $$, esc, explainOn, failed, howAudience, loading} from "./core/core.js";
import {mount as mountCopilot} from "./copilot.js?v=20261016r1";
import {after, start as startMotion} from "./motion.js?v=20261016r1";
import {mount as mountHeader} from "./header.js?v=20261016r25";

const ROLES = {
  client: {
    label: "Khách hàng", user: null, clientPick: true,
    nav: [
      {id: "tong-quan", label: "Tổng quan", sub: [
        {id: "toan-canh", label: "Toàn cảnh", page: "pulse"}, {id: "ban-do", label: "Bản đồ tài chính", page: "map"},
        {id: "chi-tiet", label: "Chi tiết", page: "detail"}]},
      {id: "tai-san", label: "Tài sản", page: "holdings"},
      {id: "muc-tieu", label: "Mục tiêu & kịch bản", sub: [
        {id: "ke-hoach", label: "Kế hoạch", page: "plan"}, {id: "khau-vi", label: "Khẩu vị rủi ro", page: "risktest"}]},
      {id: "tin", label: "Tin tác động", sub: [
        {id: "thi-truong", label: "Tác động thị trường", page: "impact"}, {id: "do-thi", label: "Đồ thị tác động", page: "graph"}, {id: "chinh-sach", label: "Chi phí chính sách", page: "policy"}]},
      {id: "chuyen-gia", label: "Chuyên gia", page: "advisor"},
    ],
  },
  rm: {
    label: "RM", user: "rm01",
    nav: [
      {id: "hom-nay", label: "Hôm nay", page: "today"},
      {id: "khach-hang", label: "Khách hàng", clientPick: true, sub: [
        {id: "tac-dong", label: "Tác động tin", page: "impact"}, {id: "do-thi", label: "Đồ thị tác động", page: "graph"},
        {id: "toan-canh", label: "Toàn cảnh", page: "pulse"}, {id: "ban-do", label: "Bản đồ tài chính", page: "map"},
        {id: "tong-quan", label: "Chi tiết", page: "detail"},
        {id: "tai-san", label: "Tài sản", page: "holdings"}, {id: "ke-hoach", label: "Kế hoạch", page: "plan"},
        {id: "chinh-sach", label: "Chi phí chính sách", page: "policy"}, {id: "hieu-qua", label: "Hiệu quả tư vấn", page: "performance"},
        {id: "duyet", label: "Duyệt đề xuất", page: "advisor"}]},
      {id: "hieu-qua", label: "Hiệu quả tư vấn", page: "perfall"},
    ],
  },
  cio: {
    label: "CIO", user: "cio",
    nav: [
      {id: "hop-tin", label: "Hộp tin", page: "inbox"},
      {id: "nhan-dinh", label: "Sự kiện & nhận định", page: "events"},
      {id: "phoi-nhiem", label: "Phơi nhiễm", page: "exposure"},
      {id: "ap-dung", label: "Lần áp dụng", page: "runs"},
      {id: "do-thi", label: "Đồ thị lần áp dụng", page: "graph"},
      {id: "nghien-cuu", label: "Nghiên cứu", page: "research"},
      {id: "ban-tin", label: "Bản tin", page: "newsletter"},
      {id: "chinh-sach", label: "Chính sách", page: "radar"},
      {id: "mo-hinh", label: "Mô hình", sub: [
        {id: "tham-so", label: "Tham số", page: "model"}, {id: "du-lieu", label: "Dữ liệu thị trường", page: "market"},
        {id: "do-chinh-xac", label: "Độ chính xác", page: "accuracy"}]},
      {id: "do-luong", label: "Đo lường", page: "measure"},
      {id: "agent", label: "Agent", page: "agents"},
      {id: "cau-hinh", label: "Cấu hình", page: "config"},
    ],
  },
  admin: {
    label: "Quản trị", user: "admin",
    nav: [
      {id: "he-thong", label: "Hệ thống", page: "system"},
      {id: "du-lieu", label: "Dữ liệu thị trường", page: "market"},
      {id: "cau-hinh", label: "Cấu hình", page: "config"},
      {id: "agent", label: "Agent", page: "agents"},
      {id: "nhat-ky", label: "Nhật ký", page: "audit"},
    ],
  },
  specialist: {
    label: "Chuyên gia", user: "sp_global",
    nav: [
      {id: "duyet", label: "Duyệt khuyến nghị", page: "specialist"},
    ],
  },
  compliance: {
    label: "Tuân thủ", user: "compliance",
    nav: [
      {id: "giu", label: "Tin bị giữ", page: "held"},
      {id: "nghien-cuu", label: "Nghiên cứu", page: "research"},
      {id: "ban-tin", label: "Bản tin", page: "newsletter"},
      {id: "chinh-sach", label: "Chính sách", page: "radar"},
      {id: "do-luong", label: "Đo lường", page: "measure"},
      {id: "nhat-ky", label: "Nhật ký", page: "audit"},
      {id: "agent", label: "Agent", page: "agents"},
      {id: "cau-hinh", label: "Cấu hình", page: "config"},
    ],
  },
};
const state = {role: "client", users: {}, route: null, seq: 0, me: null, auth: false, demo: false};
let leaving = false;
window.addEventListener("pagehide", () => { leaving = true; });
window.addEventListener("beforeunload", () => { leaving = true; });
const pages = {};

function parse(hash) {
  const parts = (hash || "").replace(/^#\/?/, "").split("/").filter(Boolean).map(decodeURIComponent);
  const role = state.me ? state.me.role : ROLES[parts[0]] ? parts[0] : (localStore("mf.role") || "client");
  const r = ROLES[role];
  const nav = r.nav.find(n => n.id === parts[1]) || r.nav[0];
  let sub = null, param = null;
  if (nav.sub) {
    sub = nav.sub.find(s => s.id === parts[2]) || nav.sub[0];
    param = nav.sub.find(s => s.id === parts[2]) ? parts[3] || null : parts[2] || null;
  } else {
    param = parts[2] || null;
  }
  return {role, nav, sub, param};
}

function localStore(k, v) {
  try {
    if (v === undefined) return localStorage.getItem(k);
    localStorage.setItem(k, v);
  } catch (_) { /* private mode */ }
  return null;
}

export function go(hash, focus) {
  if (focus) after(focus);  // motion.js marks these once the page has rendered
  if (location.hash === hash) route();
  else location.hash = hash;
}

// every page of a role, for the header search: label, its parent's label, its route
function pagesFor(role) {
  const out = [];
  for (const n of ROLES[role].nav) {
    if (n.sub) for (const s of n.sub) out.push({label: s.label, parent: n.label, route: `#/${role}/${n.id}/${s.id}`});
    else out.push({label: n.label, parent: "", route: `#/${role}/${n.id}`});
  }
  return out;
}
let header = null;

function drawChrome(rt) {
  const r = ROLES[rt.role];
  $(".rolebox").hidden = state.auth;
  if (!state.auth) $("#roles").innerHTML = Object.entries(ROLES).map(([k, v]) =>
    `<button type="button" data-role="${k}" aria-pressed="${k === rt.role}">${esc(v.label)}</button>`).join("");
  $("#nav").innerHTML = r.nav.map(n =>
    `<a href="#/${rt.role}/${n.id}" ${n === rt.nav ? 'aria-current="page"' : ""}>${esc(n.label)}${n.count ? `<span class="count">${n.count}</span>` : ""}</a>`).join("");
  const sub = $("#subnav");
  if (rt.nav.sub) {
    sub.hidden = false;
    sub.innerHTML = rt.nav.sub.map(s =>
      `<a href="#/${rt.role}/${rt.nav.id}/${s.id}" ${s === rt.sub ? 'aria-current="page"' : ""}>${esc(s.label)}</a>`).join("");
  } else {
    sub.hidden = true;
    sub.innerHTML = "";
  }
  const pick = r.clientPick || rt.nav.clientPick;
  $("#client-pick").hidden = !pick || (state.me && state.me.role === "client");
  $("#scope-pick").hidden = !pick;
  if (state.me) {
    $("#whoami").innerHTML = `<span class="me"><b>${esc(state.me.name)}</b><span class="me-title">· ${esc(state.me.title || r.label)}</span>
      <button type="button" class="linkbtn" id="signout">Đăng xuất</button></span>`;
    $("#signout").onclick = signOut;
    return;
  }
  const u = r.user && state.users[r.user];
  $("#whoami").innerHTML = u ? `Đang dùng: <b>${esc(u.name)}</b> · ${esc(u.title)} <span class="badge assumed" title="Không phải cơ chế bảo mật">demo</span>` : "";
}

async function route() {
  if (state.auth && !state.me) return signInPage();
  const rt = parse(location.hash);
  const want = (location.hash.replace(/^#\/?/, "").split("/")[0]) || "";
  if (state.me && want !== state.me.role) { location.replace(`#/${state.me.role}`); return; }
  state.role = rt.role;
  howAudience.staff = rt.role !== "client";
  state.route = rt;
  localStore("mf.role", rt.role);
  drawChrome(rt);
  if (header) header.refresh();
  const target = rt.sub || rt.nav;
  // each render gets its own element: a page still drawing for an earlier route (a late fetch, a timer) writes
  // into a node that has left the document, never into the page shown now
  const box = document.createElement("div");
  $("#page").replaceChildren(box);
  const seq = ++state.seq;
  box.innerHTML = loading();
  try {
    const mod = pages[target.page] || (pages[target.page] = await import(`./pages/${target.page}.js?v=20261016r25`));
    if (seq !== state.seq) return;
    await mod.render(box, ctx(rt));
  } catch (e) {
    if (seq === state.seq) box.innerHTML = failed(e);
    // a fetch the browser cut because the document is being left is not a failure of the page
    if (box.isConnected && !leaving) console.error(e);
  }
  // the route has rendered, or failed visibly: motion.js applies a waiting highlight; tests wait on it
  if (seq === state.seq) window.dispatchEvent(new CustomEvent("mf:page", {detail: {route: location.hash}}));
}

// the picked client and scope: every page reads them through ctx; a change redraws the page
const client = () => $("#client").value;
const scope = () => ($("[data-scope][aria-pressed=true]") || {dataset: {scope: "personal"}}).dataset.scope;
function setClient(id) {
  const sel = $("#client");
  if (sel.value !== id && [...sel.options].some(o => o.value === id)) { sel.value = id; sel.dispatchEvent(new Event("change")); }
}

function ctx(rt) {
  const r = ROLES[rt.role];
  return {
    role: rt.role,
    user: state.me ? state.me.id : r.user,
    users: state.users,
    param: rt.param,
    client,
    scope,
    go,
    href: (nav, sub, param) => `#/${rt.role}/${[nav, sub, param].filter(Boolean).map(encodeURIComponent).join("/")}`,
    isCurrent: (seq) => seq === state.seq,
    setClient,
  };
}

function theme() {
  const root = document.documentElement;
  const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
  localStore("mf.theme", root.dataset.theme);
  route(); // charts read their colours when drawn
}

async function pickers() {
  const sel = $("#client");
  // a client sees only themselves (their family through the scope switch): the hidden picker holds just them
  const {clients} = state.me && state.me.role === "client"
    ? {clients: [{id: state.me.id, name: state.me.name, persona_hint: state.me.title}]}
    : await (await fetch("/api/clients")).json();
  sel.innerHTML = clients.map(c => `<option value="${esc(c.id)}">${esc(c.name)} · ${esc(c.persona_hint)}</option>`).join("");
  const saved = localStore("mf.client");
  sel.value = clients.some(c => c.id === saved) ? saved : (clients[0] || {}).id || "";
  sel.addEventListener("change", () => { localStore("mf.client", sel.value); header.refresh(); route(); });
  for (const b of $$("[data-scope]")) {
    b.addEventListener("click", () => {
      for (const o of $$("[data-scope]")) o.setAttribute("aria-pressed", String(o === b));
      header.refresh();
      route();
    });
  }
}

// “Làm lại demo”: the server forgets what was uploaded, declared, tested and proposed; this browser forgets the
// followed goals and what each page kept for the tab; the page loads again from nothing
async function reset() {
  if (!confirm("Xóa mọi dữ liệu đã tải lên, đã khai, bài test, mục tiêu và hàng chờ duyệt để làm lại demo?")) return;
  await fetch("/api/reset", {method: "POST", headers: {"content-type": "application/json"}, body: "{}"});
  try {
    for (const k of Object.keys(localStorage)) if (k.startsWith("mf.goals.")) localStorage.removeItem(k);
    for (const k of Object.keys(sessionStorage)) if (k.startsWith("mf.")) sessionStorage.removeItem(k);
  } catch (_) { /* private mode */ }
  location.reload();
}

function signInPage() {
  document.body.classList.add("signed-out");
  $("#nav").innerHTML = "";
  $("#subnav").hidden = true;
  $("#whoami").innerHTML = "";
  const box = document.createElement("div");
  $("#page").replaceChildren(box);
  import("./pages/signin.js?v=20261016r5").then(mod => mod.render(box, {demo: state.demo, signedIn: () => { location.hash = ""; location.reload(); }}))
    .catch(e => { box.innerHTML = failed(e); });
}

async function signOut() {
  await fetch("/api/auth/logout", {method: "POST"});
  try { for (const k of Object.keys(sessionStorage)) if (k.startsWith("mf.")) sessionStorage.removeItem(k); } catch (_) { /* private mode */ }
  location.replace(location.pathname);  // one full load, no hash: the old role's page never routes again
}

async function start() {
  const me = await (await fetch("/api/auth/me")).json().catch(() => ({auth: false}));
  state.auth = !!me.auth;
  state.demo = !!me.demo_accounts;
  state.me = me.user || null;
  if (state.me && ROLES[state.me.role]) ROLES[state.me.role].user = state.me.id;
  $("#theme").onclick = theme;
  if (state.auth && !state.me) { $("#reset").hidden = true; signInPage(); return; }
  $("#reset").onclick = reset;
  $("#roles").addEventListener("click", (e) => {
    const b = e.target.closest("[data-role]");
    if (b) go(`#/${b.dataset.role}`);
  });
  window.addEventListener("hashchange", route);
  explainOn(document);  // BRD-NFR-11: any [data-metric] opens its “Cách tính”
  startMotion();
  header = mountHeader({role: () => state.role, user: () => (state.me ? state.me.id : ROLES[state.role].user), client, scope, pages: pagesFor, go, setClient});
  mountCopilot();
  await Promise.all([
    pickers(),
    state.me && (state.me.role === "client" || state.me.role === "specialist") ? null  // the staff list: desk and RMs
      : fetch("/api/agents").then(r => r.json()).then(a => { for (const u of a.users || []) state.users[u.id] = u; }).catch(() => { /* the pages still work */ }),
  ]);
  await route();
}

start();
