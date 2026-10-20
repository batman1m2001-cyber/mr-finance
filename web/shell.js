/* The shell: roles, navigation, routing, the client picker and scope, theme, demo reset. Each role sees its own
   pages (docs/NEWS_IMPACT_PLAN.md §5); every page is a module in pages/ rendered into #page (ADR-0019). The
   address is the route: #/cio/nhan-dinh/VW-0001-v1.

   Everyone signs in with their own account (BRD-RULE-SEC-01, pages/signin.js): the shell then shows only that
   person's role, and the client picker only the families they may see (a client: none, their own family). The
   server takes the user from the session, never from the page. Only with sign-in switched off (MF_AUTH=off, a
   developer's machine) does the old role switcher appear.

   The Customer has one page (FEAT-40, ADR-0035): the workspace — toolbar, the persistent graph, the dock, the
   strip — mounted once; a Customer route changes its lens, and a page of the old menu opens as a sheet over the
   graph, drawn into #page as before. A staff role with a desk (FEAT-41, ADR-0036: desk/roles.js) works the same way:
   its desk — the frame, the role's own centre, the docked assistant — is `#/<role>` (menu entry `ban`), and every
   other menu address opens its page, unchanged, as a sheet over it. */
import {$, $$, esc, explainOn, failed, howAudience, keep, loading} from "./core/core.js";
import {mount as mountCopilot} from "./copilot.js?v=20261018q1";
import {after, start as startMotion} from "./motion.js?v=20261016r1";
import {mount as mountHeader} from "./header.js?v=20261020u1";
import {LENSES, SHEETS, lensRoute} from "./workspace/lenses.js?v=20261018p3";
import {DESKS} from "./desk/roles.js?v=20261018q1";

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
      {id: "bo-nho", label: "Bộ nhớ", page: "memory", hidden: true},  // A4: linked from the header and the panel
    ],
  },
  rm: {
    label: "RM", user: "rm01",
    nav: [
      {id: "ban", label: "Sổ khách hàng", desk: true},  // FEAT-41: the RM's desk (SCR-RM-07)
      {id: "hom-nay", label: "Hôm nay", page: "today"},
      {id: "khach-hang", label: "Khách hàng", clientPick: true, sub: [
        {id: "tac-dong", label: "Tác động tin", page: "impact"}, {id: "do-thi", label: "Đồ thị tác động", page: "graph"},
        {id: "toan-canh", label: "Toàn cảnh", page: "pulse"}, {id: "ban-do", label: "Bản đồ tài chính", page: "map"},
        {id: "tong-quan", label: "Chi tiết", page: "detail"},
        {id: "tai-san", label: "Tài sản", page: "holdings"}, {id: "ke-hoach", label: "Kế hoạch", page: "plan"},
        {id: "chinh-sach", label: "Chi phí chính sách", page: "policy"}, {id: "hieu-qua", label: "Hiệu quả tư vấn", page: "performance"},
        {id: "duyet", label: "Duyệt đề xuất", page: "advisor"}]},
      {id: "hieu-qua", label: "Hiệu quả tư vấn", page: "perfall"},
      {id: "bo-nho", label: "Bộ nhớ", page: "memory", hidden: true},  // A4: linked from the header and the panel
    ],
  },
  cio: {
    label: "CIO", user: "cio",
    nav: [
      {id: "ban", label: "Bàn quyết định", desk: true},  // FEAT-41: the CIO's desk (SCR-CIO-15)
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
      {id: "viec-nen", label: "Việc nền", page: "jobs"},
      {id: "cau-hinh", label: "Cấu hình", page: "config"},
      {id: "bo-nho", label: "Bộ nhớ", page: "memory", hidden: true},  // A4: linked from the header and the panel
    ],
  },
  admin: {
    label: "Quản trị", user: "admin",
    nav: [
      {id: "ban", label: "Vận hành", desk: true},  // FEAT-41: Admin's desk (SCR-ADM-02)
      {id: "he-thong", label: "Hệ thống", page: "system"},
      {id: "du-lieu", label: "Dữ liệu thị trường", page: "market"},
      {id: "cau-hinh", label: "Cấu hình", page: "config"},
      {id: "tai-khoan", label: "Tài khoản và vai trò", page: "accounts"},
      {id: "agent", label: "Agent", page: "agents"},
      {id: "viec-nen", label: "Việc nền", page: "jobs"},
      {id: "nhat-ky", label: "Nhật ký", page: "audit"},
      {id: "bo-nho", label: "Bộ nhớ", page: "memory", hidden: true},  // A4: linked from the header and the panel
    ],
  },
  specialist: {
    label: "Chuyên gia", user: "sp_global",
    nav: [
      {id: "ban", label: "Bàn chuyên gia", desk: true},  // FEAT-41: the Expert's desk (SCR-SP-02)
      {id: "duyet", label: "Duyệt khuyến nghị", page: "specialist"},
      {id: "bo-nho", label: "Bộ nhớ", page: "memory", hidden: true},  // A4: linked from the header and the panel
    ],
  },
  compliance: {
    label: "Tuân thủ", user: "compliance",
    nav: [
      {id: "ban", label: "Bàn kiểm soát", desk: true},  // FEAT-41: Compliance's desk (SCR-CMP-06)
      {id: "giu", label: "Tin bị giữ", page: "held"},
      {id: "nghien-cuu", label: "Nghiên cứu", page: "research"},
      {id: "ban-tin", label: "Bản tin", page: "newsletter"},
      {id: "chinh-sach", label: "Chính sách", page: "radar"},
      {id: "do-luong", label: "Đo lường", page: "measure"},
      {id: "nhat-ky", label: "Nhật ký", page: "audit"},
      {id: "agent", label: "Agent", page: "agents"},
      {id: "viec-nen", label: "Việc nền", page: "jobs"},
      {id: "cau-hinh", label: "Cấu hình", page: "config"},
      {id: "bo-nho", label: "Bộ nhớ", page: "memory", hidden: true},  // A4: linked from the header and the panel
    ],
  },
};
const state = {role: "client", users: {}, clients: {}, route: null, seq: 0, me: null, auth: false, demo: false};
let leaving = false;
window.addEventListener("pagehide", () => { leaving = true; });
window.addEventListener("beforeunload", () => { leaving = true; });
const pages = {};  // page name → its module (a promise)

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
  if (role === "client") {  // the workspace: its lenses, then the views that open as sheets
    return [...LENSES.map(l => ({label: l.label, parent: "Đồ thị", route: lensRoute(l.id)})),
      ...Object.values(SHEETS).map(s => ({label: s.label, parent: s.lens ? "Xem đầy đủ" : "", route: s.route}))];
  }
  const out = [];
  for (const n of ROLES[role].nav) {
    if (n.sub) for (const s of n.sub) out.push({label: s.label, parent: n.label, route: `#/${role}/${n.id}/${s.id}`});
    else out.push({label: n.label, parent: "", route: `#/${role}/${n.id}`});
  }
  return out;
}
let header = null, copilot = null;

// the Customer's workspace: mounted on the first Customer route, kept until another role routes
let ws = null, wsLoad = null;
async function workspace() {
  if (ws) return ws;
  wsLoad ||= import("./workspace/workspace.js?v=20261020t1");
  const mod = await wsLoad;
  if (!ws) {
    ws = mod.mount($("#main"), {client, scope, go});
    document.body.classList.add("ws-on");
    copilot.dock(ws.dock, {onEvent: ws.live});  // the turn's events draw on the graph (FEAT-40)
  }
  return ws;
}
function leaveWorkspace() {
  if (!ws) return;
  ws.destroy(); ws = null;
  document.body.classList.remove("ws-on");
  copilot.undock();
}

// a staff role's desk (FEAT-41): mounted on the role's first route, kept while the role routes
let dk = null, dkRole = null, dkLoad = null;
async function desk(role) {
  if (dk && dkRole === role) return dk;
  leaveDesk();
  dkLoad ||= import("./desk/desk.js?v=20261020u1");
  const mod = await dkLoad;
  if (!dk) {
    dk = mod.mount($("#main"), {role, nav: ROLES[role].nav, go, client, setClient, user: () => (state.me ? state.me.id : ROLES[role].user)});
    dkRole = role;
    document.body.classList.add("ws-on");
    copilot.dock(dk.dock, {onEvent: dk.live});  // the role's own assistant, docked; its steps light the desk
  }
  return dk;
}
function leaveDesk() {
  if (!dk) return;
  dk.destroy(); dk = null; dkRole = null;
  document.body.classList.remove("ws-on");
  copilot.undock();
}

function drawChrome(rt) {
  const r = ROLES[rt.role];
  $(".rolebox").hidden = state.auth;
  if (!state.auth) $("#roles").innerHTML = Object.entries(ROLES).map(([k, v]) =>
    `<button type="button" data-role="${k}" aria-pressed="${k === rt.role}">${esc(v.label)}</button>`).join("");
  $("#nav").innerHTML = r.nav.filter(n => !n.hidden).map(n =>
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
  scopeSwitch(pick);
  if (state.me) {
    $("#whoami").innerHTML = `<span class="me"><b>${esc(state.me.name)}</b><span class="me-title">${esc(state.me.title || r.label)}</span>
      <a class="linkbtn" href="#/${rt.role}/bo-nho"${rt.nav.id === "bo-nho" ? ' aria-current="page"' : ""}>Bộ nhớ</a>
      <button type="button" class="linkbtn" id="signout">Đăng xuất</button>
      <button type="button" class="linkbtn me-theme" id="me-theme">Giao diện sáng / tối</button></span>`;
    $("#signout").onclick = signOut;
    $("#me-theme").onclick = theme;
    // a phone: the name row is a popover behind the initials (tokens.css .meopen)
    const words = String(state.me.name || "").trim().split(/\s+/).filter(Boolean);
    $("#me-open").textContent = words.length > 1 ? words[0][0] + words[words.length - 1][0] : (words[0] || "?").slice(0, 2);
    $("#me-open").title = state.me.name;
    $("#me-open").hidden = false;
    return;
  }
  $("#me-open").hidden = true;
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
  let target = rt.sub || rt.nav;
  const seq = ++state.seq;
  if (rt.role === "client") {
    leaveDesk();
    const w = await workspace();
    const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean).map(decodeURIComponent).slice(1);
    const sheet = await w.route(parts);
    if (seq !== state.seq) return;
    if (!sheet) {  // a lens: the graph is the page; nothing to draw into the sheet
      $("#page").replaceChildren();
      window.dispatchEvent(new CustomEvent("mf:page", {detail: {route: location.hash}}));
      warm(rt.role);
      return;
    }
    target = {page: sheet.page};
    rt.param = sheet.param;
  } else if (DESKS[rt.role]) {
    leaveWorkspace();
    const d = await desk(rt.role);
    if (seq !== state.seq) return;
    await d.route(rt.nav.desk ? null : {nav: rt.nav, sub: rt.sub});
    if (seq !== state.seq) return;
    if (rt.nav.desk) {  // the desk is the page: nothing to draw into the sheet
      $("#page").replaceChildren();
      window.dispatchEvent(new CustomEvent("mf:page", {detail: {route: location.hash}}));
      warm(rt.role);
      return;
    }
  } else { leaveWorkspace(); leaveDesk(); }
  const ok = await draw(target, rt, seq, false);
  // a page drawn from what was kept: its reads went to the server again; when an answer changed, it is drawn once
  // more from the new answers, unless the person has started using it (their next visit shows the new answers)
  if (ok && ok.changed && seq === state.seq && !used) {
    const y = scrollY;
    await draw(target, rt, seq, true);
    if (seq === state.seq) scrollTo(0, y);
  }
  // the route has rendered, or failed visibly: motion.js applies a waiting highlight; tests wait on it
  if (seq === state.seq) window.dispatchEvent(new CustomEvent("mf:page", {detail: {route: location.hash}}));
  warm(rt.role);
}

// a page module, imported once; a failed import is asked again next time
function page(name) {
  if (!pages[name]) pages[name] = import(`./pages/${name}.js?v=20261020u1`).catch((e) => { delete pages[name]; throw e; });
  return pages[name];
}

// every page of the role, imported while the browser is idle: a first visit then waits for its data only
const warmed = new Set();
function warm(role) {
  if (warmed.has(role)) return;
  warmed.add(role);
  const names = new Set();
  for (const n of ROLES[role].nav) {
    if (n.page) names.add(n.page);
    for (const s of n.sub || []) if (s.page) names.add(s.page);
  }
  const idle = window.requestIdleCallback || ((f) => setTimeout(f, 300));
  idle(() => { for (const name of names) page(name).catch(() => { /* drawn with its error when visited */ }); });
}

// whether the person has used the page drawn now: a click, a key or an input in it
let used = false;
for (const t of ["pointerdown", "keydown", "input"]) $("#page").addEventListener(t, () => { used = true; }, true);

async function draw(target, rt, seq, again) {
  // each drawing gets its own element: a page still drawing for an earlier route (a late fetch, a timer) writes
  // into a node that has left the document, never into the page shown now
  const box = document.createElement("div");
  $("#page").replaceChildren(box);
  if (!again) used = false;
  box.innerHTML = loading();
  const r = keep.begin(again);
  try {
    const mod = await page(target.page);
    if (seq !== state.seq) { keep.end(r); return null; }
    await mod.render(box, ctx(rt));
  } catch (e) {
    if (seq === state.seq) box.innerHTML = failed(e);
    // a fetch the browser cut because the document is being left is not a failure of the page
    if (box.isConnected && !leaving) console.error(e);
    keep.end(r);
    return null;
  }
  return {changed: await keep.end(r)};
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

// Cá nhân / Gia đình: only where the family has someone else to add; the “?” says whose assets each view counts
function scopeSwitch(pick) {
  const c = state.clients[client()] || {household: []};
  const show = !!pick && c.household.length > 0;
  $("#scope-wrap").hidden = !show;
  if (!show) {
    $("#scope-tip").hidden = true;
    if (scope() === "family") for (const o of $$("[data-scope]")) o.setAttribute("aria-pressed", String(o.dataset.scope === "personal"));
    return;
  }
  const inn = c.household.filter(m => m.counted), out = c.household.filter(m => !m.counted);
  const who = (ms) => ms.map(m => `<b>${esc(m.name)}</b> (${esc(m.relation)})`).join(", ");
  $("#scope-tip").innerHTML = `<div class="pop-head">Cá nhân và Gia đình</div><div class="tipbody">
    <p><b>Cá nhân</b>: chỉ tài sản, dòng tiền và mục tiêu đứng tên ${esc(c.name || "khách")}.</p>
    <p><b>Gia đình</b>: ${inn.length ? `cộng thêm của ${who(inn)}, người đã đồng ý chia sẻ.` : "giống Cá nhân, vì chưa có ai được cộng."}</p>
    ${out.length ? `<p>${who(out)} chưa đồng ý chia sẻ nên chưa được cộng; khi họ đồng ý, Gia đình sẽ có thêm tài sản của họ.</p>` : ""}
    <p class="muted">Mọi trang có số liệu đều đổi theo lựa chọn này.</p></div>`;
}

async function pickers() {
  const sel = $("#client");
  // a client gets only themselves (their family through the scope switch): the hidden picker holds just them
  const {clients} = await (await fetch("/api/clients")).json();
  for (const c of clients) state.clients[c.id] = c;
  sel.innerHTML = clients.map(c => `<option value="${esc(c.id)}">${esc(c.name)} · ${esc(c.persona_hint)}</option>`).join("");
  const saved = localStore("mf.client");
  sel.value = clients.some(c => c.id === saved) ? saved : (clients[0] || {}).id || "";
  sel.addEventListener("change", () => { localStore("mf.client", sel.value); scopeSwitch(true); header.refresh(); route(); });
  const help = $("#scope-help"), tip = $("#scope-tip"), wrap = $("#scope-wrap");
  let hover = 0, pinned = false;  // hover waits a little, so the pointer passing over does not flash it open
  const show = (on) => { tip.hidden = !on; help.setAttribute("aria-expanded", String(on)); if (!on) pinned = false; };
  // hover opens it; a click, a tap or Enter keeps it open (a phone has no hover), and a second one closes it;
  // leaving it unpinned, a click elsewhere or Escape closes it
  help.addEventListener("click", (e) => {
    e.stopPropagation();
    clearTimeout(hover);
    if (!tip.hidden && pinned) return show(false);
    show(true);
    pinned = true;
  });
  wrap.addEventListener("mouseenter", () => { if (matchMedia("(hover: hover)").matches) hover = setTimeout(() => show(true), 350); });
  wrap.addEventListener("mouseleave", () => { clearTimeout(hover); if (!pinned) show(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") show(false); });
  document.addEventListener("click", (e) => { if (!wrap.contains(e.target)) show(false); });
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
  const meOpen = $("#me-open"), top = $(".shell-top");
  const meShow = (on) => { top.classList.toggle("me-shown", on); meOpen.setAttribute("aria-expanded", String(on)); };
  meOpen.onclick = (e) => { e.stopPropagation(); meShow(!top.classList.contains("me-shown")); };
  document.addEventListener("click", (e) => { if (!e.target.closest("#whoami")) meShow(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") meShow(false); });
  window.addEventListener("hashchange", () => meShow(false));
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
  copilot = mountCopilot();
  await Promise.all([
    pickers(),
    state.me && (state.me.role === "client" || state.me.role === "specialist") ? null  // the staff list: desk and RMs
      : fetch("/api/agents").then(r => r.json()).then(a => { for (const u of a.users || []) state.users[u.id] = u; }).catch(() => { /* the pages still work */ }),
  ]);
  await route();
}

start();
