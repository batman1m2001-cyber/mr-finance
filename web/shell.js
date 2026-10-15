/* The shell: roles, navigation, routing, theme. Each role sees its own pages (docs/NEWS_IMPACT_PLAN.md
   §5). A page is either one that came before the redesign (rendered by app.js into a #tab-* section)
   or a new module in pages/ rendered into #page-new. The address is the route: #/cio/nhan-dinh/VW-0001-v1.

   The role switcher is a demo: it sends a user id with each action and the server checks that id's
   role. It is not security, and the footer says so. */
import {$, $$, esc, failed, loading} from "./core/core.js";

const ROLES = {
  client: {
    label: "Khách hàng", user: null, clientPick: true,
    nav: [
      {id: "tong-quan", label: "Tổng quan", sub: [
        {id: "toan-canh", label: "Toàn cảnh", page: "pulse"}, {id: "chi-tiet", label: "Chi tiết", legacy: "overview"}]},
      {id: "tai-san", label: "Tài sản", legacy: "sources"},
      {id: "muc-tieu", label: "Mục tiêu & kịch bản", sub: [
        {id: "ke-hoach", label: "Kế hoạch", legacy: "scenarios"}, {id: "khau-vi", label: "Khẩu vị rủi ro", legacy: "risk"}]},
      {id: "tin", label: "Tin tác động", sub: [
        {id: "thi-truong", label: "Tác động thị trường", page: "impact"}, {id: "do-thi", label: "Đồ thị tác động", page: "graph"}, {id: "chinh-sach", label: "Chi phí chính sách", legacy: "alerts"}]},
      {id: "chuyen-gia", label: "Chuyên gia", legacy: "rm"},
    ],
  },
  rm: {
    label: "RM", user: "rm01",
    nav: [
      {id: "hom-nay", label: "Hôm nay", page: "today"},
      {id: "khach-hang", label: "Khách hàng", clientPick: true, sub: [
        {id: "tac-dong", label: "Tác động tin", page: "impact"}, {id: "do-thi", label: "Đồ thị tác động", page: "graph"},
        {id: "toan-canh", label: "Toàn cảnh", page: "pulse"},
        {id: "tong-quan", label: "Chi tiết", legacy: "overview"},
        {id: "tai-san", label: "Tài sản", legacy: "sources"}, {id: "ke-hoach", label: "Kế hoạch", legacy: "scenarios"},
        {id: "chinh-sach", label: "Chi phí chính sách", legacy: "alerts"}, {id: "hieu-qua", label: "Hiệu quả tư vấn", legacy: "performance"},
        {id: "duyet", label: "Duyệt đề xuất", legacy: "rm"}]},
      {id: "hieu-qua", label: "Hiệu quả tư vấn", legacy: "perfall"},
    ],
  },
  cio: {
    label: "CIO", user: "cio",
    nav: [
      {id: "hop-tin", label: "Hộp tin", page: "inbox"},
      {id: "nhan-dinh", label: "Sự kiện & nhận định", page: "events"},
      {id: "phoi-nhiem", label: "Phơi nhiễm", page: "exposure"},
      {id: "ap-dung", label: "Lần áp dụng", page: "runs"},
      {id: "nghien-cuu", label: "Nghiên cứu", page: "research"},
      {id: "mo-hinh", label: "Mô hình", page: "model"},
    ],
  },
  compliance: {
    label: "Tuân thủ", user: "compliance",
    nav: [
      {id: "giu", label: "Tin bị giữ", page: "held"},
      {id: "nghien-cuu", label: "Nghiên cứu", page: "research"},
      {id: "nhat-ky", label: "Nhật ký", page: "audit"},
    ],
  },
};
// legacy tab → where it lives for each role (for links inside the legacy pages)
const LEGACY_HOME = {};
for (const [role, r] of Object.entries(ROLES)) {
  for (const n of r.nav) {
    for (const s of n.sub || [n]) if (s.legacy) (LEGACY_HOME[role] ||= {})[s.legacy] = n.sub ? `#/${role}/${n.id}/${s.id}` : `#/${role}/${n.id}`;
  }
}

const state = {role: "client", users: {}, route: null, seq: 0};
const pages = {};

function parse(hash) {
  const parts = (hash || "").replace(/^#\/?/, "").split("/").filter(Boolean).map(decodeURIComponent);
  const role = ROLES[parts[0]] ? parts[0] : (localStore("mf.role") || "client");
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

export function go(hash) {
  if (location.hash === hash) route();
  else location.hash = hash;
}

function drawChrome(rt) {
  const r = ROLES[rt.role];
  $("#roles").innerHTML = Object.entries(ROLES).map(([k, v]) =>
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
  $("#client-pick").hidden = !pick;
  $("#scope-pick").hidden = !pick;
  const u = r.user && state.users[r.user];
  $("#whoami").innerHTML = u ? `Đang dùng: <b>${esc(u.name)}</b> · ${esc(u.title)} <span class="badge assumed" title="Không phải cơ chế bảo mật">demo</span>` : "";
}

async function route() {
  const rt = parse(location.hash);
  state.role = rt.role;
  state.route = rt;
  localStore("mf.role", rt.role);
  drawChrome(rt);
  window.Legacy && window.Legacy.setViewer(rt.role === "client" ? "client" : "staff", ROLES[rt.role].user);
  const target = rt.sub || rt.nav;
  const box = $("#page-new");
  if (target.legacy) {
    box.hidden = true;
    box.innerHTML = "";
    await window.Legacy.ready;
    window.Legacy.showTab(target.legacy);
    return;
  }
  for (const s of $$(".tab")) s.hidden = true;
  box.hidden = false;
  const seq = ++state.seq;
  box.innerHTML = loading();
  try {
    const mod = pages[target.page] || (pages[target.page] = await import(`./pages/${target.page}.js?v=20261016b`));
    if (seq !== state.seq) return;
    await mod.render(box, ctx(rt));
  } catch (e) {
    if (seq === state.seq) box.innerHTML = failed(e);
    console.error(e);
  }
}

function ctx(rt) {
  const r = ROLES[rt.role];
  return {
    role: rt.role,
    user: r.user,
    users: state.users,
    param: rt.param,
    client: () => (window.Legacy && window.Legacy.client()) || $("#client").value,
    scope: () => ($("[data-scope][aria-pressed=true]") || {dataset: {scope: "personal"}}).dataset.scope,
    go,
    href: (nav, sub, param) => `#/${rt.role}/${[nav, sub, param].filter(Boolean).map(encodeURIComponent).join("/")}`,
    isCurrent: (seq) => seq === state.seq,
    setClient: (id) => {
      const sel = $("#client");
      if (sel.value !== id) { sel.value = id; sel.dispatchEvent(new Event("change")); }
    },
  };
}

function theme() {
  const root = document.documentElement;
  const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
  localStore("mf.theme", root.dataset.theme);
  route(); // charts read their colours when drawn
}

async function start() {
  window.Shell = {
    openLegacy: (tab) => {
      const home = (LEGACY_HOME[state.role] || {})[tab] || (LEGACY_HOME.client || {})[tab];
      if (home) go(home);
      else window.Legacy.showTab(tab);
    },
  };
  $("#theme").onclick = theme;
  $("#roles").addEventListener("click", (e) => {
    const b = e.target.closest("[data-role]");
    if (b) go(`#/${b.dataset.role}`);
  });
  // a new page that depends on the client redraws when the client or the scope changes
  $("#client").addEventListener("change", () => { if (!$("#page-new").hidden) route(); });
  for (const b of $$("[data-scope]")) b.addEventListener("click", () => { if (!$("#page-new").hidden) setTimeout(route); });
  window.addEventListener("hashchange", route);
  try {
    const a = await (await fetch("/api/agents")).json();
    for (const u of a.users || []) state.users[u.id] = u;
  } catch (_) { /* the pages still work */ }
  await route();
}

start();
