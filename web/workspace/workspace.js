/* The Customer's workspace (FEAT-40, ADR-0035, OWN-GW-01…05): one page — the toolbar of lenses on the left, the graph
   in the centre, the dock (Trợ lý · Thông tin) on the right, the strip of overview cards at the bottom. The shell
   mounts it once for the client and hands it each route; a route changes the lens and opens or closes a sheet (an
   existing page module, drawn by the shell into #page, which lives inside the sheet). Nothing here re-renders the
   graph on navigation. */
import {$, esc, followedIds, post} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {reduced} from "../motion.js?v=20261016r1";
import {createGraph} from "./graph.js?v=20261017w1";
import {render as inspect} from "./inspector.js?v=20261017w1";
import {LENS, SHEETS, TOOLBAR, lensRoute, resolve} from "./lenses.js?v=20261017w1";
import {mount as mountStrip} from "./strip.js?v=20261017w1";

export function mount(main, {client, scope, go, page}) {
  const root = document.createElement("div");
  root.className = "ws";
  root.innerHTML = `
    <nav class="ws-bar" aria-label="Các góc nhìn">${TOOLBAR.map(t => `<a class="ws-tool" href="${t.href}" data-tool="${t.id}" aria-label="${esc(t.label)}" data-tip="${esc(t.tip)}">
      ${icon(t.icon, {size: 20})}<span class="ws-tool-l">${esc(t.label)}</span></a>`).join("")}
      <button type="button" class="ws-tool ws-ask" aria-label="Hỏi trợ lý">${icon("sparkles", {size: 20})}<span class="ws-tool-l">Trợ lý</span></button></nav>
    <section class="ws-center" aria-label="Đồ thị tài chính">
      <div class="ws-head"><div><h1 class="ws-title" id="ws-title">Tổng quan tài chính</h1>
        <p class="ws-sub small muted" id="ws-sub"></p></div>
        <div class="ws-legend small" aria-label="Chú giải"><span class="lg c-actual">Thực tế</span><span class="lg c-estimate">Ước tính · tác động</span><span class="lg c-hypothetical">Giả định</span></div>
      </div>
      <div class="ws-canvas" id="ws-canvas"></div>
      <div class="ws-list" id="ws-list" hidden></div>
      <div class="ws-ctl" role="toolbar" aria-label="Điều khiển đồ thị">
        <div class="seg" role="group" aria-label="Cách xem"><button type="button" data-v="graph" aria-pressed="true">Đồ thị</button><button type="button" data-v="list" aria-pressed="false">Danh sách</button></div>
        <button type="button" class="iconbtn" data-z="in" aria-label="Phóng to">+</button>
        <button type="button" class="iconbtn" data-z="out" aria-label="Thu nhỏ">−</button>
        <button type="button" class="iconbtn" data-z="fit" aria-label="Vừa khung">${icon("eye", {size: 15})}</button>
      </div>
      <div class="ws-strip" id="ws-strip"></div>
      <section class="ws-sheet" id="ws-sheet" hidden aria-labelledby="ws-sheet-t">
        <header class="ws-sheet-h"><button type="button" class="linkbtn" id="ws-sheet-back">${icon("chevron", {size: 16})} Đồ thị</button>
          <b id="ws-sheet-t"></b><button type="button" class="iconbtn" id="ws-sheet-x" aria-label="Đóng">✕</button></header>
        <div class="ws-sheet-b" id="ws-sheet-b"></div>
      </section>
    </section>
    <aside class="ws-dock" aria-label="Trợ lý và thông tin">
      <div class="ws-tabs" role="tablist"><button type="button" role="tab" id="ws-tab-a" aria-selected="true" aria-controls="ws-pane-a">${icon("sparkles", {size: 15})} Trợ lý</button>
        <button type="button" role="tab" id="ws-tab-i" aria-selected="false" aria-controls="ws-pane-i">${icon("info", {size: 15})} Thông tin</button>
        <button type="button" class="iconbtn ws-fold" id="ws-fold" aria-label="Thu gọn bảng bên" aria-expanded="true">${icon("chevron", {size: 15})}</button></div>
      <div class="ws-pane" id="ws-pane-a" role="tabpanel" aria-labelledby="ws-tab-a"></div>
      <div class="ws-pane ws-ins" id="ws-pane-i" role="tabpanel" aria-labelledby="ws-tab-i" hidden></div>
    </aside>`;
  main.prepend(root);
  // the shell's #page is the sheet's body: the page modules and their styles stay as they are (ADR-0035 §3)
  $("#ws-sheet-b", root).appendChild($("#page"));

  const kindLabel = (k) => ((graph.data() || {kinds: []}).kinds.find(x => x.kind === k) || {label: k}).label;
  let lens = LENS["tong-quan"], sheet = null, key = null, loading = null, view = "graph";
  const graph = createGraph($("#ws-canvas", root), {onSelect: (n) => { drawInspector(); if (n) tab("i"); }});
  const strip = mountStrip($("#ws-strip", root), {client, scope, lens: (id) => go(lensRoute(id))});

  // ── the dock ──────────────────────────────────────────────────────────────────────────────────────
  const tab = (which) => {
    for (const [t, p] of [["a", "ws-pane-a"], ["i", "ws-pane-i"]]) {
      $(`#ws-tab-${t}`, root).setAttribute("aria-selected", String(t === which));
      $(`#${p}`, root).hidden = t !== which;
    }
    try { sessionStorage.setItem("mf.ws.tab", which); } catch (_) { /* private mode */ }
  };
  $("#ws-tab-a", root).onclick = () => tab("a");
  $(".ws-ask", root).onclick = () => {  // a phone: the dock is below the graph — go to it, ready to type
    tab("a");
    $(".ws-dock", root).scrollIntoView({behavior: reduced() ? "auto" : "smooth", block: "start"});
    const q = document.querySelector("#cp-q");
    if (q) q.focus({preventScroll: true});
  };
  $("#ws-tab-i", root).onclick = () => tab("i");
  $("#ws-fold", root).onclick = () => {
    const folded = root.classList.toggle("folded");
    $("#ws-fold", root).setAttribute("aria-expanded", String(!folded));
    try { localStorage.setItem("mf.ws.fold", folded ? "1" : ""); } catch (_) { /* private mode */ }
    requestAnimationFrame(() => graph.redraw());
  };
  try { if (localStorage.getItem("mf.ws.fold")) { root.classList.add("folded"); $("#ws-fold", root).setAttribute("aria-expanded", "false"); } } catch (_) { /* private mode */ }

  const drawInspector = () => inspect($("#ws-pane-i", root), {graph, lens, node: graph.selected(), kindLabel, openSheet,
    runScenario: async (n, btn) => {
      btn.disabled = true; btn.textContent = "Đang chạy…";
      try {
        // POST /api/scenario: before and after the shock, and its summary lines — kept on the node, never on net worth
        const got = await post("/api/scenario", {client_id: client(), scenario: n.ref, params: {}, scope: scope()});
        const r = got.result || got, nw = (x) => (x && typeof x.net_worth === "number" ? x.net_worth : null);
        n.value = nw(r.after) != null && nw(r.before) != null ? nw(r.after) - nw(r.before) : null;
        n.summary = (r.summary || []).slice(0, 4);
      } catch (e) { n.detail = `Không chạy được kịch bản: ${e.message}`; }
      graph.redraw(); drawInspector();
    }});

  // ── controls ──────────────────────────────────────────────────────────────────────────────────────
  for (const b of root.querySelectorAll("[data-z]")) b.onclick = () => (b.dataset.z === "in" ? graph.zoom(1.2) : b.dataset.z === "out" ? graph.zoom(1 / 1.2) : graph.fit());
  for (const b of root.querySelectorAll("[data-v]")) b.onclick = () => setView(b.dataset.v);
  const setView = (v) => {
    view = v;
    for (const b of root.querySelectorAll("[data-v]")) b.setAttribute("aria-pressed", String(b.dataset.v === v));
    $("#ws-canvas", root).hidden = v !== "graph";
    $("#ws-list", root).hidden = v !== "list";
    if (v === "list") drawList();
  };
  const drawList = () => {
    const g = graph.data();
    if (!g) return;
    const el = $("#ws-list", root);
    const kinds = g.kinds.filter(k => k.kind !== "family" && lens.kinds.includes(k.kind) && g.nodes.some(n => n.kind === k.kind && graph.visible(n.id)));
    el.innerHTML = kinds.map(k => `<div class="mgroup"><div class="subhead">${esc(k.label)}</div><div class="mlist">${g.nodes.filter(n => n.kind === k.kind && graph.visible(n.id)).map(n =>
      `<button type="button" class="mrow" data-n="${esc(n.id)}"><span><b>${esc(n.label)}</b><span class="small muted">${graph.links(n.id).length} liên kết</span></span></button>`).join("")}</div></div>`).join("");
    for (const b of el.querySelectorAll("[data-n]")) b.onclick = () => graph.select(b.dataset.n);
  };

  // ── data: the overview, once per client and scope ─────────────────────────────────────────────────
  async function load() {
    const k = `${client()}|${scope()}`;
    if (k === key) return loading;
    key = k;
    loading = (async () => {
      $("#ws-sub", root).textContent = "Đang tải…";
      const {overview} = await post("/api/overview", {client_id: client(), scope: scope(), role: "client", goals: followedIds(client())});
      if (k !== key) return;
      graph.load(overview, k);
      graph.setLens(lens);
      $("#ws-sub", root).textContent = `Tài sản, dòng tiền, mục tiêu, rủi ro và tin tức quanh bạn · số liệu ngày ${overview.as_of}`;
      drawInspector();
      strip.load();
    })().catch((e) => { key = null; $("#ws-sub", root).textContent = `Không tải được đồ thị: ${e.message}`; });
    return loading;
  }

  function setLens(id) {
    const next = LENS[id] || LENS["tong-quan"];
    lens = next;
    for (const a of root.querySelectorAll("[data-tool]")) a.toggleAttribute("aria-current", a.dataset.tool === (sheet && !SHEETS[sheet].lens ? sheet : lens.id));
    $("#ws-title", root).textContent = lens.id === "tong-quan" ? "Tổng quan tài chính" : lens.label;
    graph.setLens(lens);
    strip.focus(lens.id);
    drawInspector();
    if (view === "list") drawList();
  }

  function openSheet(id, param, focusKeys) {
    const s = SHEETS[id];
    go(param ? `${s.route}/${encodeURIComponent(param)}` : s.route, focusKeys || undefined);
  }
  const closeSheet = () => go(lensRoute(lens.id));
  $("#ws-sheet-x", root).onclick = closeSheet;
  $("#ws-sheet-back", root).onclick = closeSheet;
  const onKey = (e) => {  // Escape closes the sheet, unless it belongs to the Copilot, a drawer or a popup
    if (e.key === "Escape" && sheet && !e.defaultPrevented && !e.target.closest(".ws-dock, .drawer, .pop, [role=dialog], input, textarea, select")) closeSheet();
  };
  document.addEventListener("keydown", onKey);

  // the toolbar is a list of links (the address is the state); arrow keys move between them
  $(".ws-bar", root).addEventListener("keydown", (e) => {
    if (!["ArrowDown", "ArrowUp", "ArrowRight", "ArrowLeft"].includes(e.key)) return;
    const tools = [...root.querySelectorAll(".ws-tool")], i = tools.indexOf(document.activeElement);
    if (i < 0) return;
    e.preventDefault();
    tools[(i + (e.key === "ArrowDown" || e.key === "ArrowRight" ? 1 : tools.length - 1)) % tools.length].focus();
  });

  // the workspace fills the window under the header
  const fit_ = () => {
    root.style.setProperty("--ws-top", `${Math.round(($(".shell-top") || {getBoundingClientRect: () => ({bottom: 0})}).getBoundingClientRect().bottom)}px`);
  };
  window.addEventListener("resize", fit_);  // the graph redraws from its own ResizeObserver
  fit_();
  setTimeout(fit_, 600);  // once the header has its names (whoami, scope) and its final height
  try { tab(sessionStorage.getItem("mf.ws.tab") || "a"); } catch (_) { tab("a"); }

  // ── the assistant's turn, as it happens (OWN-GW-06…10): each call answers one real event of the stream ──────────
  let lit = [];  // what the turn's steps named: kept marked when the answer completes
  const pinged = new Set();
  const ping = (ids) => {  // the step reads nodes this lens hides: the lens that shows them says so, once per turn
    const kinds = new Set(ids.map(id => (graph.node(id) || {}).kind).filter(Boolean));
    const where = Object.values(LENS).find(l => l.id !== lens.id && [...kinds].some(k => l.kinds.includes(k)));
    const tool = where && root.querySelector(`.ws-tool[data-tool="${where.id}"]`);
    if (!tool || pinged.has(where.id)) return;
    pinged.add(where.id);
    tool.classList.remove("ping"); void tool.offsetWidth; tool.classList.add("ping");
    if (reduced()) setTimeout(() => tool.classList.remove("ping"), 2000);  // no animation: an outline, for a moment
    else tool.addEventListener("animationend", () => tool.classList.remove("ping"), {once: true});
  };
  const live = (e) => {
    const a = graph.activity;
    if (e.type === "reset") { a.reset(); lit = []; pinged.clear(); return; }
    if (e.type === "step" && e.phase === "start") {
      const ids = a.ids(e.nodes);
      a.run(e.call_id, ids);
      if (ids.length && !ids.some(id => graph.visible(id))) ping(ids);
    } else if (e.type === "step" && e.phase === "end") {
      if (e.scenario) {  // a stress test's result goes on its node: hypothetical, beside the net worth, never in it
        const n = graph.node(`SC:${e.scenario.id}`);
        if (n) { n.value = e.scenario.effect; graph.redraw(); }
      }
      a.end(e.call_id, e.ok, e.focus);
      if (e.ok) lit.push(...(e.focus || []));
    } else if (e.type === "answer") {
      const ans = e.assistant || {};
      if (ans.status === "failed" || ans.status === "forbidden") a.fail();
      else a.keep([...lit, ...(ans.focus || [])]);
      if (graph.selected()) drawInspector();
    } else if (e.type === "error" || e.type === "fail") a.fail();
  };

  return {
    graph,
    live,
    dock: $("#ws-pane-a", root),
    tab,
    /* a route's parts after the role → the lens and the sheet; returns the sheet to draw (or null) */
    async route(parts) {
      const r = resolve(parts);
      await load();
      sheet = r.sheet;
      if (r.lens) setLens(r.lens);
      else setLens(lens.id);
      const el = $("#ws-sheet", root);
      el.hidden = !sheet;
      root.classList.toggle("sheeted", !!sheet);
      if (!sheet) return null;
      $("#ws-sheet-t", root).textContent = SHEETS[sheet].label;
      const s = SHEETS[sheet];
      return {page: s.page, nav: s.nav, param: r.param};
    },
    /* the scope or the client changed: new data, the same graph element */
    reload() { key = null; strip.reset(); return load(); },
    destroy() { document.removeEventListener("keydown", onKey); main.appendChild($("#page")); root.remove(); },  // #page back where the other roles draw
  };
}
