/* A staff role's desk (FEAT-41, ADR-0036): the Customer workspace's frame — the rail of the role's groups on the
   left, the role's own centre, the dock (Trợ lý · Thông tin) on the right, every page of the role's menu as a sheet
   over the centre at its old address. The shell mounts it once per role and hands it each route; the centre is the
   role's module (desk/<role>.js), drawn from GET /api/desk, the read the role's assistant also uses.

   Same classes and ids as the workspace (only one of the two is ever mounted), so the frame, the dock's divider and
   fold (workspace/dock.js) and the phone layout are the Customer's. */
import {$, esc, get} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {reduced} from "../motion.js?v=20261016r1";
import {dockFrame} from "../workspace/dock.js?v=20261018m0";
import {DESKS} from "./roles.js?v=20261018m5";

export function mount(main, {role, nav, go, client = () => null, setClient = () => {}}) {
  const cfg = DESKS[role];
  const label = (id) => { const n = nav.find(x => x.id === id); return n ? n.label : id; };
  const pagesOf = (g) => g.nav.flatMap(id => {  // a group's pages, in menu order: a menu item with a sub-menu is its pages
    const n = nav.find(x => x.id === id);
    if (!n) return [];
    return n.sub ? n.sub.map(s => ({key: `${id}/${s.id}`, label: s.label, href: `#/${role}/${id}/${s.id}`})) : [{key: id, label: n.label, href: `#/${role}/${id}`}];
  });
  const groups = cfg.groups.map(g => ({...g, pages: pagesOf(g)}));
  const tool = (g, cls = "") => {
    const first = g.desk ? `#/${role}` : (g.pages[0] || {}).href;
    return `<a class="ws-tool${cls}" href="${first}" data-tool="${esc(g.id)}" aria-label="${esc(g.label)}" data-tip="${esc(g.tip || g.label)}">
      ${icon(g.icon, {size: 20})}<span class="ws-tool-l">${esc(g.label)}</span></a>`;
  };
  const root = document.createElement("div");
  root.className = `ws desk desk-${role}`;
  root.innerHTML = `
    <nav class="ws-bar" aria-label="Các nhóm trang">${groups.filter(g => !g.foot).map(g => tool(g)).join("")}
      ${groups.filter(g => g.foot).map((g, i) => tool(g, i ? "" : " ws-foot")).join("")}
      <button type="button" class="ws-tool ws-ask" aria-label="Hỏi trợ lý">${icon("sparkles", {size: 20})}<span class="ws-tool-l">Trợ lý</span></button></nav>
    <section class="ws-center dk-center" aria-labelledby="dk-title">
      <div class="dk-body" id="dk-body"><p class="small muted">Đang tải…</p></div>
      <section class="ws-sheet" id="ws-sheet" hidden aria-labelledby="ws-sheet-t">
        <header class="ws-sheet-h"><button type="button" class="linkbtn" id="ws-sheet-back">${icon("chevron", {size: 16})} ${esc(cfg.title)}</button>
          <b id="ws-sheet-t"></b><nav class="dk-tabs" id="dk-tabs" aria-label="Các trang trong nhóm"></nav>
          <button type="button" class="iconbtn" id="ws-sheet-x" aria-label="Đóng">✕</button></header>
        <div class="ws-sheet-b" id="ws-sheet-b"></div>
      </section>
    </section>
    <aside class="ws-dock" id="ws-dock" aria-label="Trợ lý và thông tin">
      <div class="ws-split" id="ws-split" role="separator" aria-orientation="vertical" aria-controls="ws-dock" tabindex="0"
        aria-label="Độ rộng bảng Trợ lý: kéo, hoặc dùng phím mũi tên; nhấp đúp để về mặc định" title="Kéo để đổi độ rộng · nhấp đúp: mặc định"></div>
      <div class="ws-tabs" role="tablist"><button type="button" role="tab" id="ws-tab-a" aria-selected="true" aria-controls="ws-pane-a">${icon("sparkles", {size: 15})} Trợ lý</button>
        <button type="button" role="tab" id="ws-tab-i" aria-selected="false" aria-controls="ws-pane-i">${icon("info", {size: 15})} Thông tin</button>
        <button type="button" class="iconbtn ws-dockreset" id="ws-dock-reset" title="Về độ rộng mặc định" aria-label="Về độ rộng mặc định của bảng" hidden>${icon("undo", {size: 15})}</button>
        <button type="button" class="iconbtn ws-fold" id="ws-fold" aria-label="Thu gọn bảng bên" aria-expanded="true">${icon("chevron", {size: 15})}</button></div>
      <div class="ws-pane" id="ws-pane-a" role="tabpanel" aria-labelledby="ws-tab-a"></div>
      <div class="ws-pane ws-ins" id="ws-pane-i" role="tabpanel" aria-labelledby="ws-tab-i" hidden></div>
    </aside>`;
  main.prepend(root);
  $("#ws-sheet-b", root).appendChild($("#page"));  // the shell's #page is the sheet's body: the pages draw as before

  // ── the dock ──────────────────────────────────────────────────────────────────────────────────────
  const tab = (which) => {
    for (const [t, p] of [["a", "ws-pane-a"], ["i", "ws-pane-i"]]) {
      $(`#ws-tab-${t}`, root).setAttribute("aria-selected", String(t === which));
      $(`#${p}`, root).hidden = t !== which;
    }
    try { sessionStorage.setItem("mf.desk.tab", which); } catch (_) { /* private mode */ }
  };
  $("#ws-tab-a", root).onclick = () => tab("a");
  $("#ws-tab-i", root).onclick = () => tab("i");
  $(".ws-ask", root).onclick = () => {  // a phone: the dock is below the centre — go to it, ready to type
    tab("a");
    $(".ws-dock", root).scrollIntoView({behavior: reduced() ? "auto" : "smooth", block: "start"});
    const q = document.querySelector("#cp-q");
    if (q) q.focus({preventScroll: true});
  };
  const frame = dockFrame(root, {key: "mf.desk", canvas: $("#dk-body", root)});

  // ── the centre: the role's module over its desk read ─────────────────────────────────────────────
  let view = null, data = null, loading = null, sheet = null;
  const info = $("#ws-pane-i", root);
  const api = {
    role, go, tab, client,
    /* open a page for a family: the client picker set first, as the header's picker would */
    open(family, href) { setClient(family); go(href); },
    /* the inspector: the module draws a pick into Thông tin and shows it */
    inspect(html, bind) { info.innerHTML = html; if (bind) bind(info); tab("i"); },
    reload: () => load(true),
  };
  async function load(again) {
    if (loading && !again) return loading;
    loading = (async () => {
      const [mod, got] = await Promise.all([import(`./${cfg.view}.js?v=20261018m5`), get("/api/desk")]);
      data = got;
      view = mod;
      mod.render($("#dk-body", root), data, api);
      if (!info.innerHTML) info.innerHTML = mod.hint ? mod.hint(data) : "";
    })().catch((e) => {
      loading = null;
      $("#dk-body", root).innerHTML = `<div class="panel"><b>Không tải được bàn làm việc</b><p class="small muted">${esc(e.message)}</p></div>`;
    });
    return loading;
  }

  const close = () => go(`#/${role}`);
  $("#ws-sheet-x", root).onclick = close;
  $("#ws-sheet-back", root).onclick = close;
  const onKey = (e) => {  // Escape closes the sheet, unless it belongs to the Copilot, a drawer or a popup
    if (e.key === "Escape" && sheet && !e.defaultPrevented && !e.target.closest(".ws-dock, .drawer, .pop, [role=dialog], input, textarea, select")) close();
  };
  document.addEventListener("keydown", onKey);
  $(".ws-bar", root).addEventListener("keydown", (e) => {  // arrow keys move between the rail's links
    if (!["ArrowDown", "ArrowUp", "ArrowRight", "ArrowLeft"].includes(e.key)) return;
    const tools = [...root.querySelectorAll(".ws-tool")], i = tools.indexOf(document.activeElement);
    if (i < 0) return;
    e.preventDefault();
    tools[(i + (e.key === "ArrowDown" || e.key === "ArrowRight" ? 1 : tools.length - 1)) % tools.length].focus();
  });
  const fit = () => root.style.setProperty("--ws-top", `${Math.round(($(".shell-top") || {getBoundingClientRect: () => ({bottom: 0})}).getBoundingClientRect().bottom)}px`);
  const onResize = () => { fit(); frame.resize(); };
  window.addEventListener("resize", onResize);
  fit();
  setTimeout(fit, 600);
  try { tab(sessionStorage.getItem("mf.desk.tab") || "a"); } catch (_) { tab("a"); }

  // ── the assistant's turn on the centre: a step lights what it reads (data-node), an answer keeps it ────
  let lit = new Set();
  const mark = (ids, cls, on = true) => {
    for (const id of ids || []) for (const el of root.querySelectorAll(`.dk-center [data-node="${CSS.escape(id)}"]`)) el.classList.toggle(cls, on);
  };
  const live = (e) => {
    if (e.type === "reset") { for (const c of ["act", "lit", "bad"]) for (const el of root.querySelectorAll(`.dk-center .${c}`)) el.classList.remove(c); lit = new Set(); return; }
    if (e.type === "step" && e.phase === "start") { mark(e.nodes, "act"); (e.nodes || []).forEach(n => lit.add(n)); }
    else if (e.type === "step" && e.phase === "end") { mark([...lit], "act", false); if (!e.ok) mark([...lit], "bad"); }
    else if (e.type === "answer") { mark([...lit], "act", false); mark([...lit], "lit"); if (view && view.answered) view.answered(api); }
  };

  return {
    live,
    dock: $("#ws-pane-a", root),
    tab,
    /* a route: null → the desk; {nav, sub} → that page's sheet (the shell draws the page into #page) */
    async route(target) {
      if (!target && sheet) load(true);  // back from a page: what it did may change the desk's counts
      await load();
      const navId = target ? target.nav.id : null;
      const group = groups.find(g => (navId ? g.nav.includes(navId) : g.desk));
      for (const a of root.querySelectorAll("[data-tool]")) a.toggleAttribute("aria-current", !!group && a.dataset.tool === group.id);
      sheet = target ? navId : null;
      $("#ws-sheet", root).hidden = !sheet;
      root.classList.toggle("sheeted", !!sheet);
      if (!sheet) return;
      const key = target.sub ? `${navId}/${target.sub.id}` : navId;
      const here = group ? group.pages.find(p => p.key === key) : null;
      $("#ws-sheet-t", root).textContent = here ? here.label : label(navId);
      const tabs = group && group.pages.length > 1 ? group.pages : [];
      $("#dk-tabs", root).innerHTML = tabs.map(p => `<a href="${p.href}"${p.key === key ? ' aria-current="page"' : ""}>${esc(p.label)}</a>`).join("");
    },
    /* the desk's read again (a page changed something the desk counts) */
    refresh() { if (!sheet) load(true); },
    destroy() {
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("resize", onResize);
      main.appendChild($("#page"));
      root.remove();
    },
  };
}
