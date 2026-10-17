/* The workspace graph (FEAT-40): "My Wealth" in the centre of everything POST /api/overview returns, drawn once and
   kept. A lens moves nodes (transform) and fades what it hides (opacity); the SVG, the selection, the opened classes,
   pan and zoom survive every lens, sheet and answer. Built from the overview page's graph (map.js, FEAT-30): the same
   kinds, sources, wording and "Cách tính" on every figure.

   Activity (OWN-GW-06…10) is driven from outside, one call per real event: run(id, nodeIds) when a tool starts,
   end(id, ok, keys) when it ends, light(keys) when an answer names them, keep(keys) when it completes, reset() on the
   next question. Motion is transform and opacity only; particles are Web Animations tracked by motion.js. */
import {n as how, esc, pct, signClass, vnd} from "../core/core.js";
import {CLASS_ICON, iconPaths} from "../core/icons.js?v=20261016r1";
import {hover} from "../charts/charts.js";
import {reduced, track} from "../motion.js?v=20261016r1";

const NS = "http://www.w3.org/2000/svg";
export const LOOK = {  // colour, icon; the colour follows the kind, status colours stay for status
  family: ["var(--accent)", "user"], class: ["var(--s1)", "layers"], holding: ["var(--s1)", "wallet"],
  source: ["var(--s7)", "link"], goal: ["var(--s3)", "target"], risk: ["var(--critical)", "alert"],
  alert: ["var(--s4)", "scale"], event: ["var(--s5)", "news"], flow: ["var(--in)", "salary"],
  liquidity: ["var(--t2)", "savings"], scenario: ["var(--s7)", "zap"],
};
// where a kind sits: [from°, to°, radius] (0° = right, clockwise); a lens may move a kind (LAYOUT_BY_LENS)
const SECTOR = {flow_out: [0, 0, 0.9], risk: [26, 48, 0.74], goal: [62, 118, 0.96], liquidity: [140, 140, 0.72],
  scenario: [165, 225, 1], flow_in: [166, 166, 0.9], event: [188, 208, 0.96], alert: [134, 178, 0.98],
  class: [222, 328, 0.8], source: [236, 304, 1.12]};
const NARROW = {class: [198, 342, 0.86], source: [38, 142, 0.98]};  // a phone's tall canvas: the arcs open wider
const LAYOUT_BY_LENS = {"tai-san": {source: [64, 116, 0.96], class: [188, 352, 0.62]}, "rui-ro": {class: [200, 340, 0.74]},
  "muc-tieu": {goal: [28, 152, 0.95], scenario: [212, 328, 0.95]}, "dong-tien": {class: [215, 325, 0.72]}};
const WORDING = "có thể ảnh hưởng";  // a news event's edge: a potential impact under the CIO's scenarios, never a cause
const SRC = {holding: "khoản", risk: "rủi ro", goal: "mục tiêu", alert: "chính sách", run: "lần áp dụng", txn: "giao dịch", scenario: "kịch bản"};
// certainty (OWN-GW-12): an edge's own, else what its kind implies
const CERTAIN = {event: "estimate", alert: "estimate", scenario: "hypothetical"};
export const certaintyOf = (e, byId) => e.certainty || CERTAIN[(byId[e.to] || {}).kind] || CERTAIN[(byId[e.from] || {}).kind] || "actual";
const MAX_PARTICLES = 6;

const mk = (tag, attrs, parent) => {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) el.setAttribute(k, v);
  if (parent) parent.appendChild(el);
  return el;
};
const short = (s, k) => (s.length > k ? s.slice(0, k - 1) + "…" : s);

// the focus keys a node answers to (FEAT-33): what the assistant's tools name
export function keysOf(n) {
  const k = {family: ["kpi:net_worth"], goal: [`goal:${n.ref}`], event: [`event:${n.ref}`], alert: [`policy:${n.ref}`],
    class: [`class:${n.ref}`], liquidity: ["kpi:liquidity"], flow: n.keys || [], scenario: [`scenario:${n.ref}`]}[n.kind] || [];
  if (n.id === "RK:drawdown") k.push("kpi:risk");
  if (n.id === "RK:liquidity") k.push("kpi:liquidity");
  return k;
}

// BRD-NFR-11: which formula a node's number follows, and its inputs
export function howOf(n) {
  return ({
    family: ["net_worth", {assets: vnd(n.assets), liabilities: vnd(n.liabilities)}],
    class: [n.liability ? "liabilities.total" : "class.value", {count: String(n.count)}],
    holding: ["holding.value", {}], goal: ["goal.need", {}], event: ["impact.expected_3m", {event: n.label}],
    alert: ["policy.impact", {probability: pct(n.probability, false, 0)}],
    risk: [n.id === "RK:drawdown" ? "risk.loss" : n.id === "RK:liquidity" ? "liquidity.value" : "concentration.value", {}],
    liquidity: ["liquidity.value", {}], flow: [n.side === "in" ? "flow.in" : "flow.out", {}], scenario: ["scenario.effect", {}],
  }[n.kind] || ["holding.value", {}]);
}
export const figureOf = (n) => (n.kind === "goal" ? `cần ${vnd(n.need)} · ${n.status_label}` : n.kind === "source" ? `${n.count} khoản`
  : n.kind === "liquidity" ? `${vnd(n.value)}${n.months != null ? ` · ${String(n.months).replace(".", ",")} tháng` : ""}`
    : n.kind === "scenario" ? (n.value == null ? "giả định · chưa chạy" : `nếu xảy ra ${vnd(n.value, true)}`)
      : n.value == null ? "" : ["event", "alert"].includes(n.kind) ? vnd(n.value, true) : vnd(Math.abs(n.value)));
export const srcText = (e) => [...new Set((e.sources || []).map(s => SRC[s.type] || s.type))].join(", ") + ` · ${(e.sources || []).length} bản ghi`;

export function createGraph(host, {onSelect, staffLabel} = {}) {
  let g = null, byId = {}, lens = null, st = null;
  const states = {};  // per client|scope: selection, opened classes, pan, zoom
  const svg = mk("svg", {class: "ws-svg", role: "group", "aria-label": "Đồ thị tài chính", tabindex: "-1"});
  const defs = mk("defs", {}, svg);
  const grad = mk("radialGradient", {id: "ws-me", cx: "50%", cy: "40%", r: "65%"}, defs);
  mk("stop", {offset: "0", "stop-color": "#8b76ff"}, grad);
  mk("stop", {offset: "1", "stop-color": "#3a2aa8"}, grad);
  const world = mk("g", {class: "ws-world"}, svg);
  const edgeLayer = mk("g", {class: "ws-edges"}, world);
  const fxLayer = mk("g", {class: "ws-fx", "aria-hidden": "true"}, world);
  const nodeLayer = mk("g", {class: "ws-nodes"}, world);
  host.appendChild(svg);
  const els = new Map();  // node id → its <g>, kept across draws
  let W = 1000, H = 640, pos = {}, edgeTimer = 0, narrow = false;

  // ── view state ───────────────────────────────────────────────────────────────────────────────────
  // a class is open only where its holdings can show: the Tài sản lens opens them all, the others leave them closed
  const opened = (id) => !!lens && lens.kinds.includes("holding") && st.open.has(id);
  const visible = (n) => !!lens && lens.kinds.includes(n.kind) && (n.kind !== "holding" || opened(n.parent));
  const shownEdges = () => g.edges.filter(e => byId[e.from] && byId[e.to] && visible(byId[e.from]) && visible(byId[e.to])
    && !(e.agg && opened(e.agg)) && !(e.parent && !opened(e.parent)));
  const links = (id) => shownEdges().filter(e => e.from === id || e.to === id);
  const other = (e, id) => byId[e.from === id ? e.to : e.from];

  function layout() {
    const cx = W / 2, cy = H / 2, rx = W / 2 - Math.min(170, W * (narrow ? (lens.openAll ? 0.22 : 0.3) : 0.24)), ry = H / 2 - 70;
    const out = {ME: {x: cx, y: cy, a: 0}};
    const at = (deg, r) => ({x: cx + Math.cos(deg * Math.PI / 180) * rx * r, y: cy + Math.sin(deg * Math.PI / 180) * ry * r, a: deg});
    const sectors = {...SECTOR, ...(LAYOUT_BY_LENS[lens.id] || {})};
    if (narrow && lens.openAll && st.open.size <= 1) Object.assign(sectors, NARROW);  // a phone: wider sweeps
    const place = (list, [a0, a1, r], stagger) => list.forEach((n, i) => {
      const rr = stagger && i % 2 ? r - 0.14 : r;
      out[n.id] = {...at(list.length === 1 ? (a0 + a1) / 2 : a0 + (a1 - a0) * i / (list.length - 1), rr), inner: rr < r};
    });
    for (const kind of ["class", "source", "goal", "risk", "event", "alert", "scenario", "liquidity"]) {
      const list = g.nodes.filter(n => n.kind === kind && visible(n));
      if (list.length) place(list, sectors[kind], ["goal", "source", "scenario"].includes(kind));
    }
    place(g.nodes.filter(n => n.kind === "flow" && n.side === "in" && visible(n)), sectors.flow_in);
    place(g.nodes.filter(n => n.kind === "flow" && n.side === "out" && visible(n)), sectors.flow_out);
    const open = [...st.open].filter(opened).filter(cid => out[cid]).sort((a, b) => out[a].a - out[b].a);
    if (lens.openAll && open.length > 1) {  // classes open together: they step inward, all holdings share the arc
      const kids = open.flatMap(cid => g.nodes.filter(n => n.parent === cid && visible(n)));
      for (const cid of open) Object.assign(out[cid], at(out[cid].a, 0.5));
      const [a0, a1] = sectors.class;
      kids.forEach((n, i) => { out[n.id] = {...at(a0 - 14 + (a1 - a0 + 28) * i / Math.max(1, kids.length - 1), i % 2 ? 0.98 : 1.2), kid: true}; });
    } else for (const cid of open) {  // one class open: its holdings fan out behind it, the class stepping inward
      const kids = g.nodes.filter(n => n.parent === cid && visible(n)), p = out[cid];
      if (!kids.length) continue;
      Object.assign(p, at(p.a, 0.5));
      const spread = Math.min(8, 64 / Math.max(1, kids.length));
      kids.forEach((n, i) => { out[n.id] = {...at(p.a + (i - (kids.length - 1) / 2) * spread, i % 2 ? 0.98 : 1.14), kid: true}; });
    }
    return out;
  }

  // ── nodes: created once per id, moved and faded after ───────────────────────────────────────────
  function nodeEl(n) {
    let el = els.get(n.id);
    if (el) return el;
    const me = n.kind === "family", r = me ? 58 : n.kind === "holding" ? 13 : 24;
    const [tone, ic] = n.kind === "flow" && n.side === "out" ? ["var(--out)", "cart"] : LOOK[n.kind] || LOOK.class;
    el = mk("g", {class: `wnode k-${n.kind}`, tabindex: "0", role: "button", "data-n": n.id, "aria-pressed": "false",
      "aria-label": `${(g.kinds.find(k => k.kind === n.kind) || {}).label || n.kind}: ${n.label}`}, nodeLayer);
    el.style.setProperty("--tone", tone);
    el.dataset.r = r;
    const keys = keysOf(n);
    if (keys.length) el.setAttribute("data-focus", keys.join(" "));
    mk("circle", {r: r + 9, class: "wring", "aria-hidden": "true"}, el);  // the activity ring (transform/opacity)
    if (n.kind === "risk" || (n.kind === "goal" && n.status !== "on_track")) {
      mk("circle", {r: r + 5, class: "whalo", style: `--halo:${n.kind === "goal" && n.status === "at_risk" ? "var(--warning)" : "var(--critical)"}`}, el);
    }
    mk("circle", {r, class: me ? "wcore me" : "wcore", fill: me ? "url(#ws-me)" : null}, el);
    if (me) {
      const t1 = mk("text", {y: -14, "text-anchor": "middle", class: "wme-l"}, el); t1.textContent = staffLabel || "Tài sản ròng";
      const t2 = mk("text", {y: 10, "text-anchor": "middle", class: "wme-v num-svg", "data-metric": "net_worth", tabindex: "0", role: "button",
        "data-in": JSON.stringify(howOf(n)[1])}, el);
      t2.textContent = vnd(n.value);
      const t3 = mk("text", {y: 30, "text-anchor": "middle", class: "wme-s"}, el);
      t3.textContent = `tài sản ${vnd(n.assets)} · nợ ${vnd(n.liabilities)}`;
    } else {
      const inner = mk("svg", {x: -r * 0.52, y: -r * 0.52, width: r * 1.04, height: r * 1.04, viewBox: "0 0 24 24", fill: "none",
        stroke: tone, "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round", class: "wicon"}, el);
      inner.innerHTML = iconPaths(n.kind === "class" ? CLASS_ICON[n.ref] || ic : ic);
      if (n.kind === "scenario") mk("text", {y: r + 3, "text-anchor": "middle", class: "wtag"}, el).textContent = "giả định";
      mk("text", {class: "wlbl"}, el);
      if (n.kind !== "source") {
        const f = mk("text", {class: `wfig ${["event", "alert", "scenario"].includes(n.kind) ? signClass(n.value) : ""}`}, el);
        const [m, i] = howOf(n);
        if (n.value != null) { f.setAttribute("data-metric", m); f.setAttribute("data-in", JSON.stringify(i)); f.setAttribute("tabindex", "0"); f.setAttribute("role", "button"); f.classList.add("num-svg"); }
      }
    }
    hover(el, `<b>${esc(n.label)}</b><br>${esc((g.kinds.find(k => k.kind === n.kind) || {}).label || "")}${figureOf(n) ? " · " + esc(figureOf(n)) : ""}`);
    el.addEventListener("click", (ev) => { if (!ev.target.closest(".num-svg")) select(n.id); });
    el.addEventListener("dblclick", () => { if (n.kind === "class") toggle(n.id); });
    el.addEventListener("keydown", (ev) => {
      if (ev.target !== el) return;
      if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); select(n.id); }
      if ((ev.key === "+" || ev.key === "-") && n.kind === "class") { ev.preventDefault(); toggle(n.id); }
    });
    els.set(n.id, el);
    return el;
  }

  function placeLabel(el, n, q) {
    const lbl = el.querySelector(".wlbl");
    if (!lbl) return;
    const r = Number(el.dataset.r);
    const c = Math.cos(q.a * Math.PI / 180), side = Math.abs(c) > 0.38 ? Math.sign(c) : 0;
    const below = side === 0 && (q.y >= H / 2) !== !!q.inner;
    const lx = side * (r + 9), ly = side ? -3 : below ? r + 16 : -r - 22;
    const anchor = side > 0 ? "start" : side < 0 ? "end" : "middle";
    lbl.setAttribute("x", lx); lbl.setAttribute("y", ly); lbl.setAttribute("text-anchor", anchor);
    lbl.textContent = short(n.label, narrow ? 15 : n.kind === "holding" ? 20 : n.kind === "goal" ? 24 : 28);
    const f = el.querySelector(".wfig");
    if (f) { f.setAttribute("x", lx); f.setAttribute("y", ly + 15); f.setAttribute("text-anchor", anchor); f.textContent = figureOf(n); }
  }

  // the canvas size, kept by a ResizeObserver: reading it on every draw forced a layout per lens change
  let size = null;
  new ResizeObserver(([e]) => { const r = e.contentRect; if (!size || r.width !== size.width || r.height !== size.height) { size = {width: r.width, height: r.height}; if (g && lens) draw(); } }).observe(host);
  function draw({moved = false} = {}) {
    if (!g) return;
    const box = size || host.getBoundingClientRect();
    // a phone's canvas is narrow and tall: the layout gets room in the height, the labels grow (CSS) to stay readable
    narrow = box.width > 0 && box.width < 600;
    W = Math.max(narrow ? 520 : 720, Math.round(box.width || 1000)); H = Math.max(narrow ? 640 : 520, Math.round(box.height || 640));
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    pos = layout();
    const lit = st.sel ? new Set([st.sel, ...links(st.sel).map(e => other(e, st.sel).id)]) : null;
    const back = [];  // nodes coming back into the lens: placed first, then one layout, then faded in together
    for (const n of g.nodes) {
      const el = nodeEl(n), q = pos[n.id], on = visible(n) && q;
      el.setAttribute("aria-hidden", String(!on));
      el.tabIndex = on ? 0 : -1;
      if (!on) {  // faded out, then out of the layout: a hidden node is never found, marked or tabbed to
        if (!el.classList.contains("off")) { el.classList.add("off"); setTimeout(() => { if (el.classList.contains("off")) el.classList.add("gone"); }, reduced() ? 0 : 400); }
        continue;
      }
      if (el.classList.contains("gone")) { el.classList.remove("gone"); back.push(el); }
      el.style.transform = `translate(${q.x.toFixed(1)}px, ${q.y.toFixed(1)}px)`;
      if (!back.includes(el)) el.classList.remove("off");
      el.classList.toggle("dim", !!lit && !lit.has(n.id));
      el.classList.toggle("sel", st.sel === n.id);
      el.setAttribute("aria-pressed", String(st.sel === n.id));
      placeLabel(el, n, q);
    }
    if (back.length) {  // styled once in place, still faded, then faded in: no forced layout (one cost ~60 ms)
      requestAnimationFrame(() => requestAnimationFrame(() => { for (const el of back) if (!el.classList.contains("gone")) el.classList.remove("off"); }));
    }
    for (const [id, el] of els) if (!byId[id]) { el.remove(); els.delete(id); }
    // the edges follow the nodes: faded while they move, drawn again where they arrive
    clearTimeout(edgeTimer);
    if (moved && !reduced()) {
      edgeLayer.classList.add("moving");
      edgeTimer = setTimeout(() => { drawEdges(lit); edgeLayer.classList.remove("moving"); }, 420);
    } else drawEdges(lit);
  }

  function curve(a, b) {  // a gentle arc: the control point off the chord's middle, bent the same way round
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2, dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy) || 1;
    const bend = Math.min(60, len * 0.16);
    return `M${a.x.toFixed(1)},${a.y.toFixed(1)} Q${(mx - dy / len * bend).toFixed(1)},${(my + dx / len * bend).toFixed(1)} ${b.x.toFixed(1)},${b.y.toFixed(1)}`;
  }

  function drawEdges(lit) {
    edgeLayer.replaceChildren();
    const es = shownEdges();
    const maxV = Math.max(1, ...es.filter(e => e.value != null).map(e => Math.abs(e.value)));
    for (const e of es) {
      const a = pos[e.from], b = pos[e.to];
      if (!a || !b) continue;
      const on = !lit || (lit.has(e.from) && lit.has(e.to) && (e.from === st.sel || e.to === st.sel));
      const cert = certaintyOf(e, byId);
      const tone = (LOOK[(byId[e.to].kind === "family" ? byId[e.from] : byId[e.to]).kind] || LOOK.class)[0];
      const p = mk("path", {d: curve(a, b), class: `wedge c-${cert}${on && lit ? " on" : ""}${on ? "" : " faint"}`, "data-e": `${e.from}>${e.to}`,
        "stroke-width": (e.value == null ? 1.2 : 1.2 + 3.2 * Math.abs(e.value) / maxV).toFixed(2)}, edgeLayer);
      p.style.setProperty("--tone", tone);
      const word = {actual: "thực tế", estimate: "ước tính", hypothetical: "giả định"}[cert];
      hover(p, `${esc(byId[e.from].label)} → ${esc(byId[e.to].label)}<br>${esc(e.label)}${e.value == null ? "" : " · " + vnd(e.value, cert !== "actual")}<br><span class="muted">${word} · ${srcText(e)}</span>`);
    }
  }

  // ── pan and zoom: one transform on the world group, set by the person's hand only ─────────────────
  const view = () => st.view;
  const applyView = () => {
    world.setAttribute("transform", `translate(${view().x.toFixed(1)} ${view().y.toFixed(1)}) scale(${view().k.toFixed(3)})`);
    svg.classList.toggle("near", view().k >= 1.3);  // zoomed in: the holdings' names show
  };
  function zoom(f, cx = W / 2, cy = H / 2) {
    const v = view(), k = Math.min(2.6, Math.max(0.45, v.k * f));
    v.x = cx - (cx - v.x) * (k / v.k); v.y = cy - (cy - v.y) * (k / v.k); v.k = k;
    applyView();
  }
  function fit() { st.view = {x: 0, y: 0, k: 1}; applyView(); }
  const toSvg = (ev) => { const r = svg.getBoundingClientRect(); return [(ev.clientX - r.left) * W / r.width, (ev.clientY - r.top) * H / r.height]; };
  let drag = null;
  svg.addEventListener("pointerdown", (ev) => {
    if (ev.button !== 0 || ev.target.closest(".wnode")) return;
    const [x, y] = toSvg(ev); drag = {x, y, vx: view().x, vy: view().y, moved: false};
    svg.setPointerCapture(ev.pointerId);
  });
  svg.addEventListener("pointermove", (ev) => {
    if (!drag) return;
    const [x, y] = toSvg(ev);
    if (Math.abs(x - drag.x) + Math.abs(y - drag.y) > 3) drag.moved = true;
    view().x = drag.vx + x - drag.x; view().y = drag.vy + y - drag.y; applyView();
  });
  svg.addEventListener("pointerup", (ev) => {
    if (drag && !drag.moved && !ev.target.closest(".wnode") && st.sel) select(null);  // a click on the background clears
    drag = null;
  });
  svg.addEventListener("wheel", (ev) => { ev.preventDefault(); const [x, y] = toSvg(ev); zoom(ev.deltaY < 0 ? 1.12 : 1 / 1.12, x, y); }, {passive: false});
  svg.addEventListener("keydown", (ev) => {
    if (ev.target !== svg) return;
    const step = 40, v = view();
    if (ev.key === "ArrowLeft") v.x += step; else if (ev.key === "ArrowRight") v.x -= step;
    else if (ev.key === "ArrowUp") v.y += step; else if (ev.key === "ArrowDown") v.y -= step;
    else if (ev.key === "+" || ev.key === "=") return zoom(1.15); else if (ev.key === "-") return zoom(1 / 1.15);
    else return;
    ev.preventDefault(); applyView();
  });

  // ── selection and classes ─────────────────────────────────────────────────────────────────────────
  function select(id) {
    st.sel = id && st.sel === id ? null : id;
    draw();
    if (onSelect) onSelect(st.sel ? byId[st.sel] : null);
  }
  function toggle(id) { st.open.has(id) ? st.open.delete(id) : st.open.add(id); draw({moved: true}); if (onSelect) onSelect(st.sel ? byId[st.sel] : null); }

  // ── activity: each call answers one real event ────────────────────────────────────────────────────
  const running = new Map();  // call id → node ids
  let particles = 0;
  function particle(toId, failed) {
    if (reduced() || particles >= MAX_PARTICLES) return;
    const edge = edgeLayer.querySelector(`[data-e="ME>${CSS.escape(toId)}"], [data-e="${CSS.escape(toId)}>ME"]`);
    const a = pos.ME, b = pos[toId];
    if (!a || !b) return;
    const path = edge || mk("path", {d: curve(a, b)});
    const len = path.getTotalLength ? path.getTotalLength() : 0;
    if (!len) return;
    const back = edge && edge.dataset.e.startsWith(toId);
    const frames = [];
    for (let i = 0; i <= 16; i++) {
      const p = path.getPointAtLength(len * (back ? 1 - i / 16 : i / 16));
      frames.push({transform: `translate(${p.x.toFixed(1)}px, ${p.y.toFixed(1)}px)`, opacity: i === 0 || i === 16 ? 0 : 1});
    }
    const dot = mk("circle", {r: 4, class: `wspark${failed ? " bad" : ""}`}, fxLayer);
    particles++;
    const anim = track(dot.animate(frames, {duration: 900, easing: "cubic-bezier(.45,0,.55,1)"}));
    const done = () => { dot.remove(); particles--; };
    anim.finished.then(done, done);
  }
  const nodeEls = (ids) => ids.map(id => els.get(id)).filter(el => el && !el.classList.contains("off"));
  const byKeys = (keys) => [...new Set((keys || []).flatMap(k => [...nodeLayer.querySelectorAll(`[data-focus~="${CSS.escape(k)}"]`)]))]
    .filter(el => !el.classList.contains("off"));
  const activity = {
    // a tool started: its nodes work, a spark runs to each from the centre
    run(id, ids) {
      const known = (ids || []).filter(x => byId[x]);
      running.set(id, known);
      for (const el of nodeEls(known)) { el.classList.remove("ok", "bad"); el.classList.add("act"); }
      for (const x of known) particle(x, false);
      svg.classList.add("busy");
      return known.length;
    },
    // a tool ended: its nodes settle; what its result named lights
    end(id, ok, keys) {
      const ids = running.get(id) || [];
      running.delete(id);
      for (const el of nodeEls(ids)) { el.classList.remove("act"); el.classList.add(ok ? "ok" : "bad"); }
      if (!running.size) svg.classList.remove("busy");
      return ok ? activity.light(keys) : 0;
    },
    // an answer names these: lit now (a sentence arriving, a finished step)
    light(keys) {
      const hit = byKeys(keys);
      for (const el of hit) el.classList.add("lit");
      return hit.length;
    },
    // the answer is complete: what it rests on stays marked until the next question
    keep(keys) {
      for (const el of nodeLayer.querySelectorAll(".wnode.act")) el.classList.remove("act");
      svg.classList.remove("busy");
      running.clear();
      const hit = byKeys(keys);
      for (const el of hit) el.classList.add("kept");
      return hit.length;
    },
    fail() {
      for (const el of nodeLayer.querySelectorAll(".wnode.act")) { el.classList.remove("act"); el.classList.add("bad"); }
      svg.classList.remove("busy");
      running.clear();
    },
    reset() {
      running.clear();
      svg.classList.remove("busy");
      for (const el of nodeLayer.querySelectorAll(".wnode")) el.classList.remove("act", "ok", "bad", "lit", "kept");
    },
    // the graph's node ids for a tool's kinds (the stream's `nodes` may name kinds or ids)
    ids(spec) {
      if (!g) return [];
      const out = new Set();
      for (const s of spec || []) {
        if (byId[s]) out.add(s);
        else for (const n of g.nodes) if (n.kind === s && n.kind !== "holding") out.add(n.id);
      }
      return [...out];
    },
  };

  return {
    svg,
    activity,
    /* new data for a client and scope: their own kept state; the same SVG */
    load(overview, key) {
      g = overview; byId = Object.fromEntries(g.nodes.map(n => [n.id, n]));
      st = states[key] ||= {sel: null, open: new Set(), view: {x: 0, y: 0, k: 1}};
      if (st.sel && !byId[st.sel]) st.sel = null;
      for (const el of els.values()) el.remove();
      els.clear();
      applyView();
      if (lens) draw();
    },
    setLens(next) {
      const first = !lens;
      lens = next;
      if (!g) return;
      // every class open where there is room; a phone opens one at a time (the inspector's “Mở rộng”)
      if (next.openAll && !narrow) for (const n of g.nodes) if (n.kind === "class" && g.nodes.some(x => x.parent === n.id)) st.open.add(n.id);
      if (st.sel && !visible(byId[st.sel])) { st.sel = null; if (onSelect) onSelect(null); }
      draw({moved: !first});
    },
    redraw: () => draw(),
    select, toggle, zoom, fit,
    data: () => g,
    node: (id) => byId[id],
    selected: () => (st && st.sel ? byId[st.sel] : null),
    isOpen: (id) => !!st && opened(id),
    links: (id) => links(id),
    other,
    visible: (id) => !!byId[id] && visible(byId[id]),
  };
}
