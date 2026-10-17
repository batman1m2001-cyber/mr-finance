/* The Customer's workspace (FEAT-40, ADR-0035, OWN-GW-01…05): one page — the toolbar of lenses on the left, the graph
   in the centre, the dock (Trợ lý · Thông tin) on the right, the strip of overview cards at the bottom. The shell
   mounts it once for the client and hands it each route; a route changes the lens and opens or closes a sheet (an
   existing page module, drawn by the shell into #page, which lives inside the sheet). Nothing here re-renders the
   graph on navigation. */
import {$, esc, followedIds, post, signClass, vnd, workspaceContext} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {reduced} from "../motion.js?v=20261016r1";
import {createGraph} from "./graph.js?v=20261018p1";
import {render as inspect} from "./inspector.js?v=20261018p1";
import {LENS, SHEETS, TOOLBAR, lensRoute, resolve} from "./lenses.js?v=20261018p1";
import {mount as mountStrip} from "./strip.js?v=20261018p1";

export function mount(main, {client, scope, go, page}) {
  const root = document.createElement("div");
  root.className = "ws";
  root.innerHTML = `
    <nav class="ws-bar" aria-label="Các góc nhìn">${TOOLBAR.map(t => `<a class="ws-tool" href="${t.href}" data-tool="${t.id}" aria-label="${esc(t.label)}" data-tip="${esc(t.tip)}">
      ${icon(t.icon, {size: 20})}<span class="ws-tool-l">${esc(t.label)}</span></a>`).join("")}
      <button type="button" class="ws-tool ws-ask" aria-label="Hỏi trợ lý">${icon("sparkles", {size: 20})}<span class="ws-tool-l">Trợ lý</span></button></nav>
    <section class="ws-center" aria-label="Đồ thị tài chính">
      <div class="ws-head"><div><h1 class="ws-title" id="ws-title">Tổng quan tài chính</h1>
        <p class="ws-sub small muted" id="ws-sub"></p>
        <div class="ws-scn" id="ws-scn" role="region" aria-label="Kịch bản đang bật" aria-live="polite" hidden></div></div>
        <div class="ws-legend small" aria-label="Chú giải"><span class="lg c-actual">Thực tế</span><span class="lg c-estimate">Ước tính · tác động</span><span class="lg c-hypothetical">Giả định</span><span class="lg c-pulse" title="Xung sáng chạy khi trợ lý đọc dữ liệu theo đường đó; không phải một giao dịch">Xung sáng: trợ lý đọc dữ liệu, không phải giao dịch</span></div>
      </div>
      <div class="ws-canvas" id="ws-canvas"></div>
      <div class="ws-list" id="ws-list" hidden></div>
      <div class="ws-ctl" role="toolbar" aria-label="Điều khiển đồ thị">
        <div class="seg" role="group" aria-label="Cách xem"><button type="button" data-v="graph" aria-pressed="true">Đồ thị</button><button type="button" data-v="list" aria-pressed="false">Danh sách</button></div>
        <button type="button" class="iconbtn" data-z="in" aria-label="Phóng to">+</button>
        <button type="button" class="iconbtn" data-z="out" aria-label="Thu nhỏ">−</button>
        <button type="button" class="iconbtn" data-z="focus" aria-label="Tập trung vào mục đang chọn (f)" title="Tập trung (f)" disabled>${icon("target", {size: 15})}</button>
        <button type="button" class="iconbtn" data-z="fit" aria-label="Vừa khung (0)" title="Vừa khung (0)">${icon("eye", {size: 15})}</button>
      </div>
      <div class="ws-strip" id="ws-strip"></div>
      <section class="ws-sheet" id="ws-sheet" hidden aria-labelledby="ws-sheet-t">
        <header class="ws-sheet-h"><button type="button" class="linkbtn" id="ws-sheet-back">${icon("chevron", {size: 16})} Đồ thị</button>
          <b id="ws-sheet-t"></b><button type="button" class="iconbtn" id="ws-sheet-x" aria-label="Đóng">✕</button></header>
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
  // the shell's #page is the sheet's body: the page modules and their styles stay as they are (ADR-0035 §3)
  $("#ws-sheet-b", root).appendChild($("#page"));

  const kindLabel = (k) => ((graph.data() || {kinds: []}).kinds.find(x => x.kind === k) || {label: k}).label;
  let lens = LENS["tong-quan"], sheet = null, key = null, loading = null, view = "graph";
  const graph = createGraph($("#ws-canvas", root), {onSelect: (n) => { drawInspector(); if (n || graph.selectedEdge()) tab("i"); $("[data-z=focus]", root).disabled = !n; }});
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
  const setFold = (folded) => {
    root.classList.toggle("folded", folded);
    $("#ws-fold", root).setAttribute("aria-expanded", String(!folded));
    try { localStorage.setItem("mf.ws.fold", folded ? "1" : ""); } catch (_) { /* private mode */ }
    dockAria();
    requestAnimationFrame(() => graph.redraw());
  };
  $("#ws-fold", root).onclick = () => setFold(!root.classList.contains("folded"));

  // the dock's width (panel UX, 2026-10-18): the divider on its left edge drags it, between a width the conversation
  // reads in and one that leaves the graph its room; arrows move it, Shift faster, Home/End to the ends; a drag past
  // the narrow end folds the dock, a drag on a folded one opens it; a double-click or ↺ goes back to the screen's
  // default. Kept per browser like the fold. While dragging, the graph is held: its SVG scales, one layout follows.
  const DOCK_MIN = 300, DOCK_MAX = 720, GRAPH_MIN = 420, FOLD_AT = 220;
  const split = $("#ws-split", root), dockReset = $("#ws-dock-reset", root);
  let dockW = null;  // the person's width (px), or null: the screen's default (CSS)
  try { dockW = +localStorage.getItem("mf.ws.dockw") || null; } catch (_) { /* private mode */ }
  const dockDefault = () => parseFloat(getComputedStyle(root).getPropertyValue("--dock-def")) || 384;
  const dockMax = () => Math.max(DOCK_MIN, Math.min(DOCK_MAX, root.clientWidth - (parseFloat(getComputedStyle(root).getPropertyValue("--bar-w")) || 64) - GRAPH_MIN));
  const clampDock = (w) => Math.round(Math.min(dockMax(), Math.max(DOCK_MIN, w)));
  function dockAria() {
    const folded = root.classList.contains("folded"), w = folded ? 0 : dockW == null ? dockDefault() : clampDock(dockW);
    split.setAttribute("aria-valuemin", "0");
    split.setAttribute("aria-valuemax", String(dockMax()));
    split.setAttribute("aria-valuenow", String(w));
    split.setAttribute("aria-valuetext", folded ? "Thu gọn" : `${w} điểm ảnh`);
    dockReset.hidden = folded || dockW == null;
  }
  const setDock = (w, keep = true) => {  // the width asked for is kept; what shows is clamped to this window
    dockW = w == null ? null : Math.round(Math.min(DOCK_MAX, Math.max(DOCK_MIN, w)));
    if (dockW == null) root.style.removeProperty("--dock-pick"); else root.style.setProperty("--dock-pick", `${clampDock(dockW)}px`);
    if (keep) try { if (dockW == null) localStorage.removeItem("mf.ws.dockw"); else localStorage.setItem("mf.ws.dockw", String(dockW)); } catch (_) { /* private mode */ }
    dockAria();
  };
  setDock(dockW, false);
  dockReset.onclick = () => { setDock(null); requestAnimationFrame(() => graph.redraw()); split.focus(); };
  split.ondblclick = () => { if (root.classList.contains("folded")) setFold(false); setDock(null); };
  split.addEventListener("keydown", (e) => {
    const step = e.shiftKey ? 64 : 16, now = dockW == null ? dockDefault() : clampDock(dockW);
    const to = {ArrowLeft: now + step, ArrowRight: now - step, Home: DOCK_MIN, End: dockMax()}[e.key];
    if (to == null && e.key !== "Enter") return;
    e.preventDefault();
    if (e.key === "Enter") { setFold(!root.classList.contains("folded")); return; }
    if (root.classList.contains("folded")) setFold(false);
    setDock(to);
  });
  split.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    split.setPointerCapture(e.pointerId);
    const right = root.getBoundingClientRect().right, was = dockW, wasFolded = root.classList.contains("folded");
    let want = null, frame = 0;
    // the graph stays the picture it was, scaled on the compositor: a re-rasterised SVG per frame was the drag's cost
    const canvas = $("#ws-canvas", root), box0 = canvas.getBoundingClientRect(), dock0 = $(".ws-dock", root).getBoundingClientRect().width;
    const layers = [...canvas.querySelectorAll(".ws-svg, .ws-fxsvg")];
    for (const el of layers) { el.style.width = `${box0.width}px`; el.style.height = `${box0.height}px`; }
    // the conversation keeps its width while the pointer moves and reflows once it rests (a long one reflowed per frame
    // was ~60 ms a frame); the dock's edge and the divider follow the pointer every frame
    const panes = [...$(".ws-dock", root).querySelectorAll(".ws-pane")];
    let frozen = false, rest = 0;
    const freeze = (on) => { frozen = on; for (const el of panes) el.style.width = on ? `${el.getBoundingClientRect().width}px` : ""; };
    graph.hold(true);
    root.classList.add("resizing");
    const paint = () => {
      frame = 0;
      const fold = want < FOLD_AT;
      root.classList.toggle("fold-intent", fold);
      if (fold) return;
      if (root.classList.contains("folded")) root.classList.remove("folded");
      if (!frozen) freeze(true);
      clearTimeout(rest);
      rest = setTimeout(() => freeze(false), 120);
      setDock(want, false);
      const w = box0.width + dock0 - clampDock(want), k = Math.min(1, w / box0.width);  // the graph's new room
      for (const el of layers) el.style.transform = `translate(${((w - box0.width * k) / 2).toFixed(1)}px, ${((box0.height * (1 - k)) / 2).toFixed(1)}px) scale(${k.toFixed(4)})`;
    };
    const move = (ev) => { want = right - ev.clientX; if (!frame) frame = requestAnimationFrame(paint); };
    const end = (ev) => {
      split.removeEventListener("pointermove", move);
      split.removeEventListener("pointerup", end);
      split.removeEventListener("pointercancel", end);
      if (frame) cancelAnimationFrame(frame);
      root.classList.remove("resizing", "fold-intent");
      for (const el of layers) { el.style.width = ""; el.style.height = ""; el.style.transform = ""; }
      clearTimeout(rest);
      freeze(false);
      if (ev.type === "pointercancel" || want == null) {  // nothing moved, or the drag was taken away: as it was
        setDock(was, false);
        root.classList.toggle("folded", wasFolded);
      } else if (want < FOLD_AT) {
        setDock(was, false);
        setFold(true);
      } else {
        setDock(clampDock(want));
        if (wasFolded) setFold(false);
      }
      graph.hold(false);
    };
    split.addEventListener("pointermove", move);
    split.addEventListener("pointerup", end);
    split.addEventListener("pointercancel", end);
  });
  try { if (localStorage.getItem("mf.ws.fold")) { root.classList.add("folded"); $("#ws-fold", root).setAttribute("aria-expanded", "false"); dockAria(); } } catch (_) { /* private mode */ }

  const drawInspector = () => inspect($("#ws-pane-i", root), {graph, lens, node: graph.selected(), edge: graph.selectedEdge(), kindLabel, openSheet,
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
      recombine();
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
  window.addEventListener("resize", () => { fit_(); if (dockW != null) setDock(dockW, false); else dockAria(); });  // the graph redraws from its own ResizeObserver; a kept width still leaves the graph its room
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
      if (r.lens) setLens(r.lens);
      else setLens(lens.id);
      const el = $("#ws-sheet", root);
      el.hidden = !sheet;
      root.classList.toggle("sheeted", !!sheet);
      graph.sleep("sheet", !!sheet);  // a sheet over the graph: its motion stops (F8)
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
