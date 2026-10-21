/* The Customer's workspace (FEAT-40, ADR-0035, OWN-GW-01…05): one page — the toolbar of lenses on the left, the graph
   in the centre (or its list, or the Bảng số liệu: the client's dashboard), the dock (Trợ lý · Thông tin) on the right, the strip
   of overview cards at the bottom. The shell mounts it once for the client and hands it each route; a route changes the lens and opens or closes a sheet (an
   existing page module, drawn by the shell into #page, which lives inside the sheet). Nothing here re-renders the
   graph on navigation.
   The classic app (BUSINESS_FEEDBACK_1021_PLAN B3.1, B3.2): each page under its section's tabs, with no way "back to
   the graph" (it is one of Tổng quan's tabs); the dock closed until the floating "Hỏi trợ lý" button opens it. */
import {$, esc, followedIds, post, signClass, vnd, workspaceContext} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {reduced} from "../motion.js?v=20261016r1";
import {UNIT_WORD, createGraph} from "./graph.js?v=20261021t6";
import {dockFrame} from "./dock.js?v=20261018m0";
import {render as inspect} from "./inspector.js?v=20261021b3";
import {LENS, SECTIONS, SHEETS, TOOLBAR, resolve} from "./lenses.js?v=20261021b3";
import {mount as mountMoney} from "./money.js?v=20261021b3";
import {mount as mountStrip} from "./strip.js?v=20261021t3";

const UNITS = [["day", "Ngày"], ["month", "Tháng"], ["year", "Năm"]];  // a spoke's change and the timeline's step (D2)

export function mount(main, {client, scope, go, page}) {
  const root = document.createElement("div");
  root.className = "ws";
  root.innerHTML = `
    <nav class="ws-bar" aria-label="Các góc nhìn">${TOOLBAR.map(t => `<a class="ws-tool" href="${t.href}" data-tool="${t.id}" aria-label="${esc(t.label)}" data-tip="${esc(t.tip)}">
      ${icon(t.icon, {size: 20})}<span class="ws-tool-l">${esc(t.short || t.label)}</span></a>`).join("")}</nav>
    <button type="button" class="ws-fab ws-ask" id="ws-fab" aria-controls="ws-dock" aria-expanded="false">${icon("sparkles", {size: 18})}<span>Hỏi trợ lý</span></button>
    <section class="ws-center" aria-label="Đồ thị tài chính">
      <div class="ws-head"><div><h1 class="ws-title" id="ws-title">Tổng quan tài chính</h1>
        <p class="ws-sub small muted" id="ws-sub"></p>
        <nav class="ws-pages" id="ws-pages" aria-label="Các trang của mục"></nav>
        <div class="ws-scn" id="ws-scn" role="region" aria-label="Kịch bản đang bật" aria-live="polite" hidden></div></div>
        <div class="ws-legend small" aria-label="Chú giải"><span class="lg c-actual">Thực tế</span><span class="lg c-estimate">Ước tính · tác động</span><span class="lg c-hypothetical">Giả định</span><span class="lg c-pulse" title="Xung sáng chạy khi trợ lý đọc dữ liệu theo đường đó; không phải một giao dịch">Xung sáng: trợ lý đọc dữ liệu, không phải giao dịch</span></div>
      </div>
      <div class="ws-canvas" id="ws-canvas"></div>
      <div class="ws-list" id="ws-list" hidden></div>
      <div class="ws-cashview" id="ws-cashview" hidden></div>
      <div class="ws-ctl" role="toolbar" aria-label="Điều khiển đồ thị">
        <div class="seg" role="group" aria-label="Thay đổi trên các cạnh: so với hôm qua, tháng trước hay năm trước" id="ws-unit">${UNITS.map(([u, l]) => `<button type="button" data-u="${u}" aria-pressed="false" title="${esc(UNIT_WORD[u])}">${l}</button>`).join("")}</div>
        <div class="seg" role="group" aria-label="Cách xem" id="ws-view"><button type="button" data-v="graph" aria-pressed="true">Đồ thị</button><button type="button" data-v="list" aria-pressed="false">Danh sách</button><button type="button" data-v="money" aria-pressed="false">Bảng số liệu</button></div>
        <button type="button" class="iconbtn" data-z="in" aria-label="Phóng to">+</button>
        <button type="button" class="iconbtn" data-z="out" aria-label="Thu nhỏ">−</button>
        <button type="button" class="iconbtn" data-z="focus" aria-label="Tập trung vào mục đang chọn (f)" title="Tập trung (f)" disabled>${icon("target", {size: 15})}</button>
        <button type="button" class="iconbtn" data-z="fit" aria-label="Vừa khung (0)" title="Vừa khung (0)">${icon("eye", {size: 15})}</button>
      </div>
      <div class="ws-strip" id="ws-strip"></div>
      <section class="ws-sheet" id="ws-sheet" hidden aria-labelledby="ws-sheet-t">
        <header class="ws-sheet-h"><b class="sr-only" id="ws-sheet-t"></b><nav class="ws-pages" id="ws-sheet-tabs" aria-label="Các trang của mục"></nav></header>
        <div class="ws-sheet-b" id="ws-sheet-b"></div>
      </section>
    </section>
    <aside class="ws-dock" id="ws-dock" aria-label="Trợ lý và thông tin">
      <div class="ws-split" id="ws-split" role="separator" aria-orientation="vertical" aria-controls="ws-dock" tabindex="0"
        aria-label="Độ rộng bảng Trợ lý: kéo, hoặc dùng phím mũi tên; nhấp đúp để về mặc định" title="Kéo để đổi độ rộng · nhấp đúp: mặc định"></div>
      <div class="ws-tabs" role="tablist"><button type="button" role="tab" id="ws-tab-a" aria-selected="true" aria-controls="ws-pane-a">${icon("sparkles", {size: 15})} Trợ lý</button>
        <button type="button" role="tab" id="ws-tab-i" aria-selected="false" aria-controls="ws-pane-i">${icon("info", {size: 15})} Thông tin</button>
        <button type="button" class="iconbtn ws-dockreset" id="ws-dock-reset" title="Về độ rộng mặc định" aria-label="Về độ rộng mặc định của bảng" hidden>${icon("undo", {size: 15})}</button>
        <button type="button" class="iconbtn ws-fold" id="ws-fold" aria-label="Thu gọn bảng bên" aria-expanded="true">${icon("chevron", {size: 15})}</button>
        <button type="button" class="iconbtn ws-close" id="ws-close" aria-label="Đóng trợ lý">✕</button></div>
      <div class="ws-pane" id="ws-pane-a" role="tabpanel" aria-labelledby="ws-tab-a"></div>
      <div class="ws-pane ws-ins" id="ws-pane-i" role="tabpanel" aria-labelledby="ws-tab-i" hidden></div>
    </aside>`;
  main.prepend(root);
  // the shell's #page is the sheet's body: the page modules and their styles stay as they are (ADR-0035 §3)
  $("#ws-sheet-b", root).appendChild($("#page"));

  const kindLabel = (k) => ((graph.data() || {kinds: []}).kinds.find(x => x.kind === k) || {label: k}).label;
  // view: what the centre shows; graphView: what the graph's page shows (Toàn cảnh's dashboard is not its choice)
  let lens = LENS["tong-quan"], sheet = null, key = null, loading = null, view = "graph", graphView = "graph", asOf = null, feed = null;
  const drawSub = () => { $("#ws-sub", root).textContent = `${lens.sub}${asOf ? ` · số liệu ngày ${asOf}` : ""}`; };
  const graph = createGraph($("#ws-canvas", root), {onSelect: (n) => { drawInspector(); if (n || graph.selectedEdge()) { tab("i"); openDock(true, false); } $("[data-z=focus]", root).disabled = !n; }});
  const money = mountMoney($("#ws-cashview", root), {client, scope});
  // the Bảng số liệu at a section (and the month's flows at a month): from a strip card, the inspector, the feed
  const board = (part, month, lensId) => {
    if (sheet || lensId && lensId !== lens.id) go(`#/client/xem/${lensId || lens.id}`);
    return setView("money", part).then(() => (month ? money.month(month) : null));
  };
  const strip = mountStrip($("#ws-strip", root), {client, scope, board: (part, id) => board(part, null, id)});

  // ── the dock ──────────────────────────────────────────────────────────────────────────────────────
  const tab = (which) => {
    for (const [t, p] of [["a", "ws-pane-a"], ["i", "ws-pane-i"]]) {
      $(`#ws-tab-${t}`, root).setAttribute("aria-selected", String(t === which));
      $(`#${p}`, root).hidden = t !== which;
    }
    try { sessionStorage.setItem("mf.ws.tab", which); } catch (_) { /* private mode */ }
  };
  $("#ws-tab-a", root).onclick = () => tab("a");
  // open or closed (B3.2): kept per person in this browser; closed until asked. A phone opens it over the page from
  // its button (over), below the page for a node picked (the graph stays usable), and always starts closed.
  const phone = () => matchMedia("(max-width: 760px)").matches;
  const dockKey = () => `mf.ws.dock.${client()}`;
  function openDock(on, keep = true, over = false) {
    root.classList.toggle("dock-off", !on);
    root.classList.toggle("dock-over", on && over && phone());
    $("#ws-fab", root).setAttribute("aria-expanded", String(on));
    if (keep) try { localStorage.setItem(dockKey(), on ? "open" : "closed"); } catch (_) { /* private mode */ }
    requestAnimationFrame(() => { frame.resize(); graph.redraw(); money.resize(); });
  }
  $("#ws-fab", root).onclick = () => {  // the panel beside the page (a phone: over it), ready to type
    openDock(true, true, true);
    tab("a");
    const q = document.querySelector("#cp-q");
    if (q) q.focus({preventScroll: true});
  };
  $("#ws-close", root).onclick = () => { openDock(false); $("#ws-fab", root).focus(); };
  $("#ws-tab-i", root).onclick = () => tab("i");
  const frame = dockFrame(root, {canvas: $("#ws-canvas", root), hold: (on) => graph.hold(on), redraw: () => graph.redraw()});

  const drawInspector = () => inspect($("#ws-pane-i", root), {graph, lens, node: graph.selected(), edge: graph.selectedEdge(), kindLabel, openSheet, board, feed, client,
    page: sheet && !SHEETS[sheet].lens ? SHEETS[sheet].label : null,
    timeline: {client: client(), scope: scope(), unit: graph.unit(), setUnit: (u) => setUnit(u)},
    scenario: {on: (id) => active().ids.includes(id), params: (id) => (active().params || {})[id] || null, set: setActive}});

  // what the assistant is told the person is looking at (F10): the lens, the pick, the active scenarios
  workspaceContext.get = () => {
    const n = graph.selected(), e = !n && graph.selectedEdge(), a = active();
    const label = (id) => (graph.node(id) || {label: id}).label;
    return {lens: lens.id, active: a.ids, params: a.params,
      selected: n ? {id: n.id, kind: n.kind, label: n.label} : e ? {id: `${e.from}>${e.to}`, kind: "edge", label: `${label(e.from)} → ${label(e.to)}`} : null};
  };

  // ── the active stress tests (UNIFIED_FLOWS_PLAN F6): kept per client in this browser (a convenience, like the
  // followed goals); the server combines them every time (POST /api/scenario/combine), never adding them to net worth
  const scnKey = () => `mf.ws.scn.${client()}`;
  const active = () => {
    try { const v = JSON.parse(localStorage.getItem(scnKey()) || "null"); if (v && Array.isArray(v.ids)) return {ids: v.ids, params: v.params || {}}; } catch (_) { /* private mode */ }
    return {ids: [], params: {}};
  };
  const keepActive = (v) => { try { localStorage.setItem(scnKey(), JSON.stringify(v)); } catch (_) { /* private mode */ } };
  let combining = 0;
  async function recombine() {
    const a = active(), t = ++combining;
    if (!a.ids.length) { graph.scenarios(null); drawBar(null); drawInspector(); return; }
    $("#ws-scn", root).classList.add("busy");
    try {
      const got = await post("/api/scenario/combine", {client_id: client(), scenarios: a.ids, params: a.params, scope: scope(), goals: followedIds(client())});
      if (t !== combining) return;
      graph.scenarios(got.result); drawBar(got.result);
    } catch (e) {
      if (t !== combining) return;
      graph.scenarios(null); drawBar(null, e.message);
    }
    drawInspector();
  }
  // id on or off (null: all off); the person's what-if keeps its inputs for next time
  function setActive(id, on, params) {
    const a = id == null ? {ids: [], params: active().params} : active();
    if (id != null) { a.ids = a.ids.filter(x => x !== id); if (on) a.ids.push(id); if (params) a.params[id] = params; }
    keepActive(a);
    return recombine();
  }
  function drawBar(r, err) {
    const el = $("#ws-scn", root);
    el.classList.remove("busy");
    el.hidden = !r && !err;
    if (el.hidden) { el.innerHTML = ""; return; }
    const off = `<button type="button" class="linkbtn small" data-off="*">Bỏ tất cả</button>`;
    el.innerHTML = err ? `<span class="small">Không tính được kịch bản: ${esc(err)}</span>${off}`
      : `<span class="pill">giả định</span>${r.scenarios.map(x => `<span class="ws-chip"><button type="button" class="linkbtn small" data-n="SC:${esc(x.id)}">${esc(x.title)}</button><button type="button" class="ws-chip-x" data-off="${esc(x.id)}" aria-label="Tắt kịch bản ${esc(x.title)}">✕</button></span>`).join("")}
        <span class="small ws-scn-nw">Nếu xảy ra: tài sản ròng <b class="num" data-scn="after" data-v="${Math.round(r.after.net_worth)}">${vnd(r.after.net_worth)}</b> <b class="num ${signClass(r.change)}" data-scn="change" data-v="${Math.round(r.change)}">${vnd(r.change, true)}</b></span>${off}
        ${r.warnings.length ? `<p class="small muted ws-scn-w">${r.warnings.map(esc).join(" · ")}</p>` : ""}`;
    for (const b of el.querySelectorAll("[data-off]")) b.onclick = () => setActive(b.dataset.off === "*" ? null : b.dataset.off, false);
    for (const b of el.querySelectorAll("[data-n]")) b.onclick = () => graph.select(b.dataset.n);
  }

  // ── controls ──────────────────────────────────────────────────────────────────────────────────────
  for (const b of root.querySelectorAll("[data-z]")) {
    b.onclick = () => (b.dataset.z === "in" ? graph.zoom(1.2) : b.dataset.z === "out" ? graph.zoom(1 / 1.2) : b.dataset.z === "focus" ? graph.focus() : graph.fit());
  }
  for (const b of root.querySelectorAll("#ws-view [data-v]")) b.onclick = () => setView(b.dataset.v);
  const setUnit = (u) => {
    graph.setUnit(u);
    for (const b of root.querySelectorAll("[data-u]")) b.setAttribute("aria-pressed", String(b.dataset.u === graph.unit()));
    drawInspector();
  };
  for (const b of root.querySelectorAll("[data-u]")) b.onclick = () => setUnit(b.dataset.u);
  for (const b of root.querySelectorAll("[data-u]")) b.setAttribute("aria-pressed", String(b.dataset.u === graph.unit()));
  // keep: the graph page's own choice (its buttons, a strip card), kept for the tab; Toàn cảnh's dashboard is not
  const setView = (v, part, keep = true) => {
    view = v;
    if (keep) graphView = v;
    root.classList.toggle("home", !keep && v === "money");  // Toàn cảnh: the dashboard as a page, not one of the graph's views
    root.dataset.view = v;
    for (const b of root.querySelectorAll("#ws-view [data-v]")) b.setAttribute("aria-pressed", String(b.dataset.v === v));
    $("#ws-canvas", root).hidden = v !== "graph";
    $("#ws-list", root).hidden = v !== "list";
    $("#ws-cashview", root).hidden = v !== "money";
    graph.sleep("view", v !== "graph");  // the graph out of sight: its motion stops
    if (v === "list") drawList();
    if (keep) try { sessionStorage.setItem("mf.ws.view", v); } catch (_) { /* private mode */ }
    drawPages();
    if (v !== "money") return Promise.resolve();
    // a section asked for: at the top of the view (the view scrolls, not the page)
    return money.load().then(() => { money.resize(); money.at(part, !reduced()); });
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
      recombine();
      asOf = overview.as_of;
      drawSub();
      drawInspector();
      strip.load();
      if (view === "money") money.load();
      feed = null;  // Tổng quan's Thông tin: what Toàn cảnh led with (T4)
      post("/api/feed", {client_id: client(), scope: scope(), role: "client"}).then((r) => r.feed, (e) => ({error: e.message}))
        .then((f) => { if (k === key) { feed = f; drawInspector(); } });
    })().catch((e) => { key = null; $("#ws-sub", root).textContent = `Không tải được đồ thị: ${e.message}`; });
    return loading;
  }

  function setLens(id) {
    const next = LENS[id] || LENS["tong-quan"];
    lens = next;
    for (const a of root.querySelectorAll("[data-tool]")) a.toggleAttribute("aria-current", a.dataset.tool === (sheet && !SHEETS[sheet].lens ? sheet : lens.id));
    $("#ws-title", root).textContent = lens.id === "tong-quan" ? "Tổng quan tài chính" : lens.label;
    if (asOf) drawSub();
    drawPages();
    graph.setLens(lens);
    strip.focus(lens.id);
    drawInspector();
    if (view === "list") drawList();
  }

  // the section's tabs (B3.1), over the graph's page and over a sheet: Tổng quan's are Toàn cảnh and Đồ thị tài chính;
  // a graph at another lens (a strip card, a citation, the assistant) is the section's page "on the graph" for now
  function drawPages() {
    const onGraph = !sheet, s = SECTIONS[sheet ? (SHEETS[sheet].lens || sheet) : lens.id] || {tabs: []};  // Bộ nhớ: none
    const here = (href, v) => (sheet ? href === SHEETS[sheet].route : !!v && (v === "money") === (view === "money"));
    const tabs = s.tabs.map(([label, href, v]) => [label, href, v || null, here(href, v)]);
    if (onGraph && !tabs.some(t => t[3])) tabs.push([view === "money" ? "Trong Bảng số liệu" : "Trên đồ thị", `#/client/xem/${lens.id}`, null, true]);
    for (const el of [$("#ws-pages", root), $("#ws-sheet-tabs", root)]) {
      el.innerHTML = tabs.length > 1 ? tabs.map(([label, href, , on]) => `<a class="ws-page" href="${href}"${on ? ' aria-current="page"' : ""}>${esc(label)}</a>`).join("") : "";
      el.hidden = tabs.length < 2;
    }
  }

  function openSheet(id, param, focusKeys) {
    const s = SHEETS[id];
    go(param ? `${s.route}/${encodeURIComponent(param)}` : s.route, focusKeys || undefined);
  }
  const onKey = (e) => {  // Escape closes the dock opened over a phone's page (a sheet is a page now: it stays)
    if (e.key === "Escape" && root.classList.contains("dock-over") && !e.defaultPrevented && !e.target.closest(".drawer, .pop, [role=dialog]")) openDock(false);
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
  window.addEventListener("resize", () => { fit_(); frame.resize(); money.resize(); });  // the graph redraws from its own ResizeObserver; a kept width still leaves the graph its room
  fit_();
  setTimeout(fit_, 600);  // once the header has its names (whoami, scope) and its final height
  try { tab(sessionStorage.getItem("mf.ws.tab") || "a"); } catch (_) { tab("a"); }
  try { const v = sessionStorage.getItem("mf.ws.view"); if (v === "list" || v === "money") setView(v); } catch (_) { /* private mode */ }
  let kept = null, shown = null;
  try { kept = localStorage.getItem(dockKey()); } catch (_) { /* private mode */ }
  openDock(kept === "open" && !phone(), false);

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
        if (n && !n.active) { n.value = e.scenario.effect; graph.redraw(); }  // an active one shows its part in the combination
      }
      a.end(e.call_id, e.ok, e.focus);
      if (e.ok) lit.push(...(e.focus || []));
    } else if (e.type === "answer") {
      const ans = e.assistant || {};
      if (ans.status === "failed" || ans.status === "forbidden") a.fail();
      else a.keep([...lit, ...(ans.focus || [])]);
      if (graph.selected()) drawInspector();
    } else if (e.type === "text") a.writing();
    else if (e.type === "error" || e.type === "fail") a.fail();
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
      const at = sheet || (r.part || r.home ? "home" : "graph");
      if (at !== shown) {  // another page: at its top, as a page opens (a section asked for scrolls below)
        if (shown && root.classList.contains("dock-over")) openDock(false, false);  // a phone: the page asked for, not the panel over it
        shown = at;
        $("#ws-sheet-b", root).scrollTop = 0;
        $("#ws-cashview", root).scrollTop = 0;
        if (phone()) scrollTo(0, 0);
      }
      if (r.lens) setLens(r.lens);
      else setLens(lens.id);
      if (r.part || r.home) await setView("money", r.part, false);  // the home, Toàn cảnh's and Chi tiết's addresses: the dashboard (T4)
      else if (!sheet && (r.view || graphView) !== view) await setView(r.view || graphView);  // the graph's page as it was left
      const el = $("#ws-sheet", root);
      el.hidden = !sheet;
      root.classList.toggle("sheeted", !!sheet);
      graph.sleep("sheet", !!sheet);  // a sheet over the graph: its motion stops (F8)
      if (!sheet) return null;
      $("#ws-sheet-t", root).textContent = SHEETS[sheet].label;
      const s = SHEETS[sheet];
      return {page: s.page, nav: s.nav, param: r.param, board: s.board || null};
    },
    /* the scope or the client changed: new data, the same graph element */
    reload() { key = null; strip.reset(); money.reset(); return load(); },
    destroy() { document.removeEventListener("keydown", onKey); main.appendChild($("#page")); root.remove(); },  // #page back where the other roles draw
  };
}
