/* The workspace graph (FEAT-40): "My Wealth" in the centre of everything POST /api/overview returns, drawn once and
   kept. A lens moves nodes (transform) and fades what it hides (opacity); the SVG, the selection, the opened classes,
   pan and zoom survive every lens, sheet and answer. Built from the overview page's graph (map.js, FEAT-30): the same
   kinds, sources, wording and "Cách tính" on every figure.

   Activity (OWN-GW-06…10) is driven from outside, one call per real event: run(id, nodeIds) when a tool starts,
   end(id, ok, keys) when it ends, light(keys) when an answer names them, keep(keys) when it completes, reset() on the
   next question; writing() while text streams. Motion is transform and opacity only; pulses are Web Animations tracked by
   motion.js (OWN-GW-16…19). */
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
const LAYOUT_BY_LENS = {"tai-san": {source: [36, 144, 0.96], class: [186, 354, 0.74]}, "rui-ro": {class: [200, 340, 0.74]},
  "muc-tieu": {goal: [28, 152, 0.95], scenario: [212, 328, 0.95]}, "dong-tien": {class: [215, 325, 0.72]}};
const WORDING = "có thể ảnh hưởng";  // a news event's edge: a potential impact under the CIO's scenarios, never a cause
const SRC = {holding: "khoản", risk: "rủi ro", goal: "mục tiêu", alert: "chính sách", run: "lần áp dụng", txn: "giao dịch", scenario: "kịch bản"};
// certainty (OWN-GW-12): an edge's own, else what its kind implies
const CERTAIN = {event: "estimate", alert: "estimate", scenario: "hypothetical"};
export const certaintyOf = (e, byId) => e.certainty || CERTAIN[(byId[e.to] || {}).kind] || CERTAIN[(byId[e.from] || {}).kind] || "actual";
const MAX_COMETS = 8;  // at once (4 elements each), OWN-GW-19
const ME_R = 62;  // “My Wealth”: the anchor's disc

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

// A second-layer node with no edge of its own to “My Wealth” (a news event, a policy item, a risk: they reach it through
// classes) gets one: its own figure, which is already its total effect on the family, with the records of the links it
// sums. Drawn instead of its fan of class edges, which show when it is picked (OWN-GW-15).
const SUMS = {event: "có thể ảnh hưởng", alert: "tác động ước tính", risk: "rủi ro trên tài sản"};
export function spokesFor(g) {
  const touches = new Set(g.edges.filter(e => e.from === "ME" || e.to === "ME").flatMap(e => [e.from, e.to]));
  return g.nodes.filter(n => SUMS[n.kind] && !touches.has(n.id)).map(n => {
    const mine = g.edges.filter(e => e.from === n.id || e.to === n.id);
    return {from: n.id, to: "ME", label: SUMS[n.kind], value: n.value, derived: mine.length,
      sources: mine.flatMap(e => e.sources || []).filter((x, i, a) => a.findIndex(y => y.type === x.type && y.id === x.id) === i)};
  });
}

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
  let W = 1000, H = 640, pos = {}, edgeTimer = 0, narrow = false, hoverId = null, derived = [], layoutRun = 0;
  const hotEdges = new Map();  // "from>to" → "hot" | "bad": a relation a pulse runs along, drawn while it matters

  // ── view state (OWN-GW-15): three layers ──────────────────────────────────────────────────────────
  // a class opens to its holdings on demand, where the lens shows holdings: picked (or one of its holdings picked), or
  // opened by hand (“Mở rộng”, double-click)
  const holdingLens = () => !!lens && lens.kinds.includes("holding");
  const opened = (id) => holdingLens() && !st.shut.has(id) && (st.open.has(id) || st.sel === id || (!!st.sel && (byId[st.sel] || {}).parent === id));
  const visible = (n) => !!lens && lens.kinds.includes(n.kind) && (n.kind !== "holding" || opened(n.parent));
  // the edges “My Wealth” has to the second layer are always drawn; any other edge only for what is picked, pointed at,
  // read by the assistant or kept by its answer, and a class's own holdings while it is open
  const spoke = (e) => e.from === "ME" || e.to === "ME";
  // … or the exact path a pulse is taking (a news item to the class it touches): one edge, not the item's whole fan
  const relates = (e, rv) => rv.has(e.from) || rv.has(e.to) || hotEdges.has(`${e.from}>${e.to}`)
    || (!!e.parent && opened(e.parent) && byId[e.from].kind === "class");
  const reveal = () => new Set([st.sel, hoverId].filter(Boolean));
  const allEdges = () => g.edges.concat(derived);
  const drawable = (e) => byId[e.from] && byId[e.to] && visible(byId[e.from]) && visible(byId[e.to])
    && !(e.agg && opened(e.agg)) && !(e.parent && !opened(e.parent));
  const shownEdges = () => { const rv = reveal(); return allEdges().filter(e => drawable(e) && (spoke(e) || relates(e, rv))); };
  const links = (id) => allEdges().filter(e => drawable(e) && (e.from === id || e.to === id));
  const other = (e, id) => byId[e.from === id ? e.to : e.from];

  function layout() {
    // the room kept for labels at the sides: less on a phone, where the labels find their own free place (placeLabels)
    const cx = W / 2, cy = H / 2, rx = W / 2 - Math.min(170, W * (narrow ? 0.17 : 0.24)), ry = H / 2 - 70;
    const out = {ME: {x: cx, y: cy, a: 0}};
    const at = (deg, r) => ({x: cx + Math.cos(deg * Math.PI / 180) * rx * r, y: cy + Math.sin(deg * Math.PI / 180) * ry * r, a: deg});
    const sectors = {...SECTOR, ...(LAYOUT_BY_LENS[lens.id] || {})};
    const nOpen = g.nodes.filter(n => n.kind === "class" && opened(n.id)).length;
    if (narrow && holdingLens() && nOpen <= 1) Object.assign(sectors, NARROW);  // a phone: wider sweeps
    const place = (list, [a0, a1, r], stagger) => list.forEach((n, i) => {
      const rr = stagger && i % 2 ? r - 0.17 : r;
      out[n.id] = {...at(list.length === 1 ? (a0 + a1) / 2 : a0 + (a1 - a0) * i / (list.length - 1), rr), inner: rr < r};
    });
    for (const kind of ["class", "source", "goal", "risk", "event", "alert", "scenario", "liquidity"]) {
      const list = g.nodes.filter(n => n.kind === kind && visible(n));
      // a crowded arc takes two rings, so neighbours' labels fall on opposite sides (OWN-GW-15)
      if (list.length) place(list, sectors[kind], ["goal", "source", "scenario"].includes(kind) || list.length >= 7);
    }
    place(g.nodes.filter(n => n.kind === "flow" && n.side === "in" && visible(n)), sectors.flow_in);
    place(g.nodes.filter(n => n.kind === "flow" && n.side === "out" && visible(n)), sectors.flow_out);
    const open = g.nodes.filter(n => n.kind === "class" && opened(n.id) && out[n.id]).map(n => n.id).sort((a, b) => out[a].a - out[b].a);
    if (open.length > 1) {  // classes open together: they step inward, all holdings share the arc
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
    return relax(out, cx, cy, rx, ry);
  }

  // no two nodes on top of each other, whatever the screen (OWN-GW-15): a few rounds pushing overlapping pairs apart,
  // “My Wealth” fixed, everything inside the canvas; the angle is read again for the label's side
  const radius = (id) => (id === "ME" ? ME_R : (byId[id] || {}).kind === "holding" ? 13 : 24) + 7;
  function relax(out, cx, cy, rx, ry) {
    const ids = Object.keys(out);
    for (let round = 0; round < 24; round++) {
      let moved = false;
      for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) {
        const a = out[ids[i]], b = out[ids[j]], need = radius(ids[i]) + radius(ids[j]);
        let dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy);
        if (d >= need) continue;
        if (d < 0.01) { dx = 1; dy = 0; d = 1; }
        const push = (need - d) / 2 + 0.5, ux = dx / d, uy = dy / d;
        const fa = ids[i] === "ME" ? 0 : ids[j] === "ME" ? 2 : 1, fb = 2 - fa;
        a.x -= ux * push * fa; a.y -= uy * push * fa; b.x += ux * push * fb; b.y += uy * push * fb;
        moved = true;
      }
      for (const id of ids) { const q = out[id], r = radius(id); q.x = Math.min(W - r, Math.max(r, q.x)); q.y = Math.min(H - r, Math.max(r, q.y)); }
      if (!moved) break;
    }
    for (const id of ids) if (id !== "ME") out[id].a = Math.atan2((out[id].y - cy) / ry, (out[id].x - cx) / rx) * 180 / Math.PI;
    return out;
  }

  // ── nodes: created once per id, moved and faded after ───────────────────────────────────────────
  function nodeEl(n) {
    let el = els.get(n.id);
    if (el) return el;
    const me = n.kind === "family", r = me ? ME_R : n.kind === "holding" ? 13 : 24;
    const [tone, ic] = n.kind === "flow" && n.side === "out" ? ["var(--out)", "cart"] : LOOK[n.kind] || LOOK.class;
    el = mk("g", {class: `wnode k-${n.kind}`, tabindex: "0", role: "button", "data-n": n.id, "aria-pressed": "false",
      "aria-label": `${(g.kinds.find(k => k.kind === n.kind) || {}).label || n.kind}: ${n.label}`}, nodeLayer);
    el.style.setProperty("--tone", tone);
    el.dataset.r = r;
    const keys = keysOf(n);
    if (keys.length) el.setAttribute("data-focus", keys.join(" "));
    mk("circle", {r: r + 9, class: "wring", "aria-hidden": "true"}, el);  // the activity ring (transform/opacity)
    mk("circle", {r: r + 4, class: "wburst", "aria-hidden": "true"}, el);  // where a pulse arrives (OWN-GW-16)
    if (n.kind === "risk" || (n.kind === "goal" && n.status !== "on_track")) {
      mk("circle", {r: r + 5, class: "whalo", style: `--halo:${n.kind === "goal" && n.status === "at_risk" ? "var(--warning)" : "var(--critical)"}`}, el);
    }
    mk("circle", {r, class: me ? "wcore me" : "wcore", fill: me ? "url(#ws-me)" : null}, el);
    if (me) {
      // four short lines, each narrower than the disc at its height (a 128 px line crossed the border)
      const t1 = mk("text", {y: -22, "text-anchor": "middle", class: "wme-l"}, el); t1.textContent = staffLabel || "Tài sản ròng";
      const t2 = mk("text", {y: 4, "text-anchor": "middle", class: "wme-v num-svg", "data-metric": "net_worth", tabindex: "0", role: "button",
        "data-in": JSON.stringify(howOf(n)[1])}, el);
      t2.textContent = vnd(n.value);
      mk("line", {x1: -26, x2: 26, y1: 15, y2: 15, class: "wme-rule"}, el);
      const t3 = mk("text", {y: 30, "text-anchor": "middle", class: "wme-s"}, el);
      t3.textContent = `tài sản ${vnd(n.assets)}`;
      const t4 = mk("text", {y: 44, "text-anchor": "middle", class: "wme-s"}, el);
      t4.textContent = `nợ ${vnd(n.liabilities)}`;
    } else {
      const inner = mk("svg", {x: -r * 0.52, y: -r * 0.52, width: r * 1.04, height: r * 1.04, viewBox: "0 0 24 24", fill: "none",
        stroke: tone, "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round", class: "wicon"}, el);
      inner.innerHTML = iconPaths(n.kind === "class" ? CLASS_ICON[n.ref] || ic : ic);
      if (n.kind === "scenario") mk("text", {y: r + 13, "text-anchor": "middle", class: "wtag"}, el).textContent = "giả định";
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
    // pointing at a node shows its relations (and only then): the web stays out of the way until asked for
    el.addEventListener("pointerenter", () => { if (hoverId !== n.id && n.id !== "ME") { hoverId = n.id; drawEdges(litSet()); } });
    el.addEventListener("pointerleave", () => { if (hoverId === n.id) { hoverId = null; drawEdges(litSet()); } });
    el.addEventListener("keydown", (ev) => {
      if (ev.target !== el) return;
      if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); select(n.id); }
      if ((ev.key === "+" || ev.key === "-") && n.kind === "class") { ev.preventDefault(); toggle(n.id); }
    });
    els.set(n.id, el);
    return el;
  }

  // ── labels (OWN-GW-15): each takes the first free place — its own side, the other side, below, above — clear of
  // every node and every label placed before it; with none free it is shortened. Widths are estimated from the
  // characters (measuring the text would force a layout per draw).
  const PRIORITY = {family: 0, class: 1, flow: 1, liquidity: 1, goal: 2, risk: 2, scenario: 3, event: 3, alert: 4, source: 5, holding: 6};
  function placeLabels(list) {
    const cw = narrow ? 8.4 : 7.2, fw = narrow ? 7.5 : 6.3, gap = narrow ? 18 : 15;  // a phone's labels are larger (CSS)
    const boxes = list.map(n => { const q = pos[n.id], r = Number(els.get(n.id).dataset.r) + 3; return [q.x - r, q.y - r, q.x + r, q.y + r]; });
    const free = (b) => b[0] > 2 && b[2] < W - 2 && b[1] > 2 && b[3] < H - 2 && !boxes.some(o => b[0] < o[2] && o[0] < b[2] && b[1] < o[3] && o[1] < b[3]);
    const order = list.filter(n => n.kind !== "family").sort((a, b) => (PRIORITY[a.kind] ?? 9) - (PRIORITY[b.kind] ?? 9) || Math.abs(b.value || 0) - Math.abs(a.value || 0));
    for (const n of order) {
      const el = els.get(n.id), lbl = el.querySelector(".wlbl"), f = el.querySelector(".wfig");
      if (!lbl) continue;
      const q = pos[n.id], r = Number(el.dataset.r), tag = n.kind === "scenario" ? 14 : 0;
      const c = Math.cos(q.a * Math.PI / 180), side = Math.abs(c) > 0.38 ? Math.sign(c) : 0;
      const below = side === 0 && (q.y >= H / 2) !== !!q.inner;
      const pref = side > 0 ? "right" : side < 0 ? "left" : below ? "below" : "above";
      const tries = [pref, ...{right: ["left", "below", "above"], left: ["right", "below", "above"], below: ["above", "right", "left"], above: ["below", "right", "left"]}[pref]];
      const full = f ? figureOf(n) : "", max = narrow ? 15 : n.kind === "holding" ? 20 : n.kind === "goal" ? 24 : 28;
      let fig = full;
      const at = (where, text) => {
        const w = Math.max(text.length * cw, fig.length * fw), h = fig ? gap + 16 : 17;
        const lx = where === "right" ? r + 9 : where === "left" ? -r - 9 : 0, ly = where === "below" ? r + 16 + tag : where === "above" ? -r - (fig ? 22 : 8) : -3;
        const x0 = where === "right" ? lx : where === "left" ? lx - w : -w / 2;
        return {where, text, lx, ly, box: [q.x + x0, q.y + ly - 13, q.x + x0 + w, q.y + ly - 13 + h]};
      };
      // no free place: drop the figure line (it stays in the tooltip and the inspector), then shorten the name
      let pick = null;
      for (const [text, withFig] of [[short(n.label, max), true], [short(n.label, max), false], [short(n.label, 12), false]]) {
        fig = withFig ? full : "";
        pick = tries.map(t => at(t, text)).find(p => free(p.box));
        if (pick) break;
      }
      // still none: the name waits to be asked for (pointed at, focused, picked, lit), like a holding's; the icon, the
      // tooltip and the accessible name stay
      const quiet = !pick;
      if (quiet) { fig = full; pick = at(pref, short(n.label, max)); }
      el.classList.toggle("quiet", quiet);
      if (n.kind !== "holding" && !quiet) boxes.push(pick.box);  // what shows on demand does not push the others
      const anchor = pick.where === "right" ? "start" : pick.where === "left" ? "end" : "middle";
      lbl.setAttribute("x", pick.lx); lbl.setAttribute("y", pick.ly); lbl.setAttribute("text-anchor", anchor);
      lbl.textContent = pick.text;
      if (pick.text !== n.label) lbl.setAttribute("data-full", n.label); else lbl.removeAttribute("data-full");
      if (f) { f.setAttribute("x", pick.lx); f.setAttribute("y", pick.ly + gap); f.setAttribute("text-anchor", anchor); f.textContent = fig; }
      el.classList.toggle("tight", !quiet && !!full && !fig);
    }
  }

  // the canvas size, kept by a ResizeObserver: reading it on every draw forced a layout per lens change
  let size = null;
  new ResizeObserver(([e]) => { const r = e.contentRect; if (!r.width) return; /* hidden (a phone's sheet): keep the last size */ if (!size || r.width !== size.width || r.height !== size.height) { size = {width: r.width, height: r.height}; if (g && lens) draw(); } }).observe(host);
  function draw({moved = false} = {}) {
    if (!g) return;
    const box = size || host.getBoundingClientRect();
    // a phone's canvas is narrow and tall: the layout gets room in the height, the labels grow (CSS) to stay readable
    narrow = box.width > 0 && box.width < 600;
    W = Math.max(narrow ? 520 : 720, Math.round(box.width || 1000)); H = Math.max(narrow ? 640 : 520, Math.round(box.height || 640));
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    pos = layout();
    layoutRun++;
    const lit = litSet();
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
    }
    placeLabels(g.nodes.filter(n => visible(n) && pos[n.id]));
    if (back.length) {  // styled once in place, still faded, then faded in: no forced layout (one cost ~60 ms)
      requestAnimationFrame(() => requestAnimationFrame(() => { for (const el of back) if (!el.classList.contains("gone")) el.classList.remove("off"); }));
    }
    for (const [id, el] of els) if (!byId[id]) { el.remove(); els.delete(id); }
    // the edges follow the nodes: faded while they move, drawn again where they arrive
    clearTimeout(edgeTimer);
    if (moved && !reduced()) {
      edgeLayer.classList.add("moving");
      edgeTimer = setTimeout(() => { drawEdges(lit); edgeLayer.classList.remove("moving"); }, 420);
    } else { edgeLayer.classList.remove("moving"); drawEdges(lit); }  // a draw inside a move's fade ends the fade too
  }

  function litSet() { return st.sel ? new Set([st.sel, ...links(st.sel).map(e => other(e, st.sel).id)]) : null; }

  // a gentle arc: the control point off the chord's middle, bent the same way round; with an edge, it starts and ends at
  // the two discs' borders (a wire into a port, not under the node)
  function curve(a, b, e) {
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2, dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy) || 1;
    const bend = Math.min(60, len * 0.16), qx = mx - dy / len * bend, qy = my + dx / len * bend;
    const trim = (p, id) => {
      const r = e ? radius(id) - 5 : 0, ux = qx - p.x, uy = qy - p.y, l = Math.hypot(ux, uy) || 1;
      return [p.x + ux / l * r, p.y + uy / l * r];
    };
    const [x0, y0] = trim(a, e && e.from), [x1, y1] = trim(b, e && e.to);
    return `M${x0.toFixed(1)},${y0.toFixed(1)} Q${qx.toFixed(1)},${qy.toFixed(1)} ${x1.toFixed(1)},${y1.toFixed(1)}`;
  }

  // ── edges (OWN-GW-16, 18): silk — a hairline whose width follows the value (Studio's data-flow wires); solid for
  // what is recorded, dashed for an estimate, dotted for a hypothesis; a knob where real money arrives (Studio's
  // bouton). A path the assistant reads glows (`hot`), or turns red if the read failed (`bad`).
  // Money in motion (Studio's data-flow spark, canvas.js dfComet): on every real money edge a crackle of dashes with a
  // bright head slides from where the money comes from to where it goes — income into “My Wealth” (green), spending
  // and debt out of it (orange) — all the time, as Studio's wires do. Bigger flows carry more sparks. A scenario's
  // edge never runs: nothing moved. Reduced motion stills them (tokens.css).
  const SPARK = [1, 2.5, 1.5, 2, 5];  // back to front: crackle, crackle, head (dash, gap)… — short, a bead of light
  const SPARK_LEN = SPARK.reduce((p, q) => p + q, 0);
  const MONEY_SPEED = 210;  // px per second: steady, readable; Studio's data runs at 560
  const SPARK_EVERY = 95;  // px between sparks on one edge: the stream reads as continuous
  function sparks(d, key, tone, share) {
    const probe = mk("path", {d}, edgeLayer);
    let total = 0;
    try { total = probe.getTotalLength(); } catch (_) { total = 0; }
    probe.remove();
    const n = Math.max(2, Math.round(total / SPARK_EVERY * (0.7 + 0.6 * Math.sqrt(share))));  // more for a bigger flow
    for (let i = 0; i < n; i++) {
      const q = mk("path", {d, class: "wspark", "data-e": key}, edgeLayer);
      let len = 0;
      try { len = q.getTotalLength(); } catch (_) { len = 0; }
      if (len < 30) { q.remove(); return; }
      const dur = Math.max(1.2, len / MONEY_SPEED);
      q.style.strokeDasharray = `${SPARK.join(" ")} ${len + 40}`;
      q.style.setProperty("--a", SPARK_LEN);
      q.style.setProperty("--b", -len);
      q.style.setProperty("--tone", tone);
      q.style.animationDuration = `${dur.toFixed(2)}s, .16s`;
      q.style.animationDelay = `${(-dur * i / n).toFixed(2)}s, ${(-Math.random() * .16).toFixed(2)}s`;
    }
  }
  const pathState = new Map();  // non-centre node id → "hot" | "bad": its edges wear it
  let drawn = "";  // the edges on screen and the layout they were drawn for: an event that changes neither only restyles
  function drawEdges(lit) {
    const es = shownEdges(), sig = `${layoutRun}|${es.map(e => `${e.from}>${e.to}`).join(",")}`;
    if (sig === drawn) {
      for (const p of edgeLayer.querySelectorAll(".wedge")) {
        const [f0, t0] = p.dataset.e.split(">"), e = {from: f0, to: t0};
        const on = !lit || (lit.has(f0) && lit.has(t0) && (f0 === st.sel || t0 === st.sel));
        const state = spoke(e) ? pathState.get(f0 === "ME" ? t0 : f0) || "" : hotEdges.get(p.dataset.e) || "";
        for (const [c, v] of [["on", on && !!lit], ["faint", !on], ["hot", state === "hot"], ["bad", state === "bad"]]) p.classList.toggle(c, v);
      }
      for (const q of edgeLayer.querySelectorAll(".wspark")) {
        const [f0, t0] = q.dataset.e.split(">");
        q.classList.toggle("faint", !!lit && !(lit.has(f0) && lit.has(t0) && (f0 === st.sel || t0 === st.sel)));
      }
      return;
    }
    drawn = sig;
    edgeLayer.replaceChildren();
    const maxV = Math.max(1, ...es.filter(e => e.value != null).map(e => Math.abs(e.value)));
    for (const e of es) {
      const a = pos[e.from], b = pos[e.to];
      if (!a || !b) continue;
      const on = !lit || (lit.has(e.from) && lit.has(e.to) && (e.from === st.sel || e.to === st.sel));
      const cert = certaintyOf(e, byId);
      const far = byId[e.to].kind === "family" ? byId[e.from] : byId[e.to];
      const tone = far.kind === "flow" && far.side === "out" ? "var(--out)" : (LOOK[far.kind] || LOOK.class)[0];
      const state = spoke(e) ? pathState.get(e.from === "ME" ? e.to : e.from) || "" : hotEdges.get(`${e.from}>${e.to}`) || "";
      const money = cert === "actual" && (byId[e.from].kind === "flow" || byId[e.to].kind === "flow");
      const d = curve(a, b, e);
      const p = mk("path", {d, class: `wedge c-${cert}${on && lit ? " on" : ""}${on ? "" : " faint"}${state ? " " + state : ""}${e.derived ? " sum" : ""}`,
        "data-e": `${e.from}>${e.to}`, "stroke-width": (e.value == null ? 1 : 0.9 + 1.5 * Math.sqrt(Math.abs(e.value) / maxV)).toFixed(2)}, edgeLayer);
      p.style.setProperty("--tone", tone);
      if (money) {  // the receiving end: where the money lands (into “My Wealth”, or out to spending)
        const [x, y] = d.split(" ").pop().split(",").map(Number);
        mk("circle", {cx: x, cy: y, r: 3, class: "wknob"}, edgeLayer).style.setProperty("--tone", tone);
        sparks(d, `${e.from}>${e.to}`, tone, e.value == null ? 0.3 : Math.abs(e.value) / maxV);
        if (!on) for (const q of edgeLayer.querySelectorAll(`.wspark[data-e="${e.from}>${e.to}"]`)) q.classList.add("faint");
      }
      if (e.repaid && cert === "actual") {  // a debt paid down this month: money runs from “My Wealth” out to it
        const [, p0, q, p1] = d.match(/^M(\S+) Q(\S+) (\S+)$/);  // the same wire, walked the other way
        sparks(`M${p1} Q${q} ${p0}`, `${e.from}>${e.to}`, "var(--out)", Math.min(1, Math.abs(e.repaid) / maxV));
        if (!on) for (const q of edgeLayer.querySelectorAll(`.wspark[data-e="${e.from}>${e.to}"]`)) q.classList.add("faint");
      }
      const word = {actual: "thực tế", estimate: "ước tính", hypothetical: "giả định"}[cert];
      const sum = e.derived ? ` · tổng hợp từ ${e.derived} liên kết` : "";
      const paid = e.repaid ? `<br>trả trong tháng: ${vnd(e.repaid)}` : "";
      hover(p, `${esc(byId[e.from].label)} → ${esc(byId[e.to].label)}<br>${esc(e.label)}${e.value == null ? "" : " · " + vnd(e.value, cert !== "actual")}${paid}<br><span class="muted">${word} · ${srcText(e)}${sum}</span>`);
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
    if (drag && !drag.moved && !ev.target.closest(".wnode")) {  // a click on the background clears: the pick, then the answer's focus
      if (st.sel) select(null);
      else if (svg.classList.contains("focusing") && !running.size) activity.reset();
    }
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
    const before = g.nodes.filter(n => n.kind === "class" && opened(n.id)).map(n => n.id).join();
    st.sel = id && st.sel === id ? null : id;
    const after = g.nodes.filter(n => n.kind === "class" && opened(n.id)).map(n => n.id).join();
    draw({moved: before !== after});  // a class opening or closing moves the nodes: the edges follow
    if (onSelect) onSelect(st.sel ? byId[st.sel] : null);
  }
  function toggle(id) {  // by hand: open stays open; closed stays closed even while picked
    if (opened(id)) { st.open.delete(id); st.shut.add(id); } else { st.shut.delete(id); st.open.add(id); }
    draw({moved: true});
    if (onSelect) onSelect(st.sel ? byId[st.sel] : null);
  }

  // ── activity (OWN-GW-17): each call answers one real event, and nothing moves without one ─────────────
  // A pulse (a comet: a bright head and a short trail, Studio's data-flow spark) means the assistant read data along
  // that path — never that money moved (OWN-GW-18). It runs from what was read back to “My Wealth” when a tool's
  // result arrives; news and policy go through the class they touch. Transform and opacity only (FEAT-33): the head
  // and its trail are moved along points of the curve as tracked Web Animations, paused in a hidden tab, none under
  // reduced motion.
  const running = new Map();  // call id → node ids
  let comets = 0, writingTimer = 0;
  const SPEED = 520;  // px per second (Studio: 560)
  const TRAIL = [[3.4, 1, 0], [2.5, 0.55, 34], [1.8, 0.32, 68], [1.2, 0.18, 102]];  // radius, opacity, delay ms
  const edgePath = (x, y) => edgeLayer.querySelector(`.wedge[data-e="${CSS.escape(x)}>${CSS.escape(y)}"], .wedge[data-e="${CSS.escape(y)}>${CSS.escape(x)}"]`);
  // one comet from node `from` to node `to` along their drawn edge; `then` when it arrives
  function comet(from, to, {hollow = false, then} = {}) {
    const path = edgePath(from, to);
    if (!path || reduced() || comets >= MAX_COMETS || document.hidden) { if (then) then(); return false; }
    const len = path.getTotalLength();
    if (len < 8) { if (then) then(); return false; }
    const back = path.dataset.e.startsWith(`${to}>`);
    const steps = Math.max(12, Math.min(40, Math.round(len / 14)));
    const pts = [];
    for (let i = 0; i <= steps; i++) { const p = path.getPointAtLength(len * (back ? 1 - i / steps : i / steps)); pts.push(`translate(${p.x.toFixed(1)}px, ${p.y.toFixed(1)}px)`); }
    const dur = Math.max(420, Math.min(1500, len / SPEED * 1000));
    const g0 = mk("g", {class: `wcomet${hollow ? " hollow" : ""}`}, fxLayer);
    comets++;
    let left = TRAIL.length;
    const done = () => { if (--left) return; g0.remove(); comets--; };
    TRAIL.forEach(([r, o, delay], i) => {
      const dot = mk("g", {}, g0), core = mk("circle", {r, class: i ? "wtrail" : "whead"}, dot);  // the group travels, the dot flickers
      const frames = pts.map((t, k) => ({transform: t, opacity: k === 0 ? 0 : k === pts.length - 1 ? o * 0.6 : o}));
      const anim = track(dot.animate(frames, {duration: dur, delay, easing: "cubic-bezier(.35,0,.25,1)", fill: "both"}));
      if (!i) {  // the head flickers a little, like the Studio's spark (opacity only)
        track(core.animate([{opacity: 1}, {opacity: 0.68}, {opacity: 1}], {duration: 150, iterations: Math.ceil(dur / 150)}));
        anim.finished.then(() => { arrive(to); if (then) then(); }, () => {});
      }
      anim.finished.then(done, done);
    });
    return true;
  }
  // where a pulse lands, the node answers once (a burst of its ring: transform and opacity)
  function arrive(id) {
    const el = els.get(id);
    if (!el || el.classList.contains("off")) return;
    el.classList.remove("hit"); void el.getBBox(); el.classList.add("hit");
    setTimeout(() => el.classList.remove("hit"), 700);
  }
  // the data a node gave goes home: along its spoke, or (news, policy) through up to two classes it touches
  function homeward(id) {
    const n = byId[id];
    if (!n || id === "ME" || !visible(n)) return;
    const hollow = n.kind === "scenario";
    if (["event", "alert"].includes(n.kind)) {
      const via = g.edges.filter(e => (e.from === id || e.to === id) && byId[other(e, id).id]?.kind === "class" && visible(byId[other(e, id).id]))
        .sort((x, y) => Math.abs(y.value || 0) - Math.abs(x.value || 0)).slice(0, 2);
      if (via.length) {
        for (const e of via) { hotEdges.set(`${e.from}>${e.to}`, "hot"); pathState.set(other(e, id).id, "hot"); }
        drawEdges(litSet());
        for (const e of via) { const c = other(e, id).id; comet(id, c, {then: () => comet(c, "ME")}); }
        return;
      }
    }
    comet(id, "ME", {hollow});
  }
  const focusOn = () => svg.classList.add("focusing");
  const nodeEls = (ids) => ids.map(id => els.get(id)).filter(el => el && !el.classList.contains("off"));
  const byKeys = (keys) => [...new Set((keys || []).flatMap(k => [...nodeLayer.querySelectorAll(`[data-focus~="${CSS.escape(k)}"]`)]))]
    .filter(el => !el.classList.contains("off"));
  const idsOf = (els_) => els_.map(el => el.dataset.n);
  const activity = {
    // a tool started: its nodes work, the paths to them glow, the rest steps back
    run(id, ids) {
      const known = (ids || []).filter(x => byId[x]);
      running.set(id, known);
      for (const el of nodeEls(known)) { el.classList.remove("ok", "bad"); el.classList.add("act"); }
      for (const x of known) pathState.set(x, "hot");
      svg.classList.add("busy");
      if (nodeEls(known).length) focusOn();  // nothing of it on screen (another lens): nothing to step back from
      drawEdges(litSet());
      return known.length;
    },
    // a tool ended: ok — its data runs home and what its result names lights; failed — red, and nothing runs
    end(id, ok, keys) {
      const ids = running.get(id) || [];
      running.delete(id);
      for (const el of nodeEls(ids)) { el.classList.remove("act"); el.classList.add(ok ? "ok" : "bad"); }
      for (const x of ids) pathState.set(x, ok ? "hot" : "bad");
      drawEdges(litSet());
      if (ok) for (const x of ids) homeward(x);
      if (!running.size) svg.classList.remove("busy");
      return ok ? activity.light(keys) : 0;
    },
    // an answer names these: lit now, with the paths to them
    light(keys) {
      const hit = byKeys(keys);
      for (const el of hit) { el.classList.add("lit"); if (el.dataset.n !== "ME") pathState.set(el.dataset.n, pathState.get(el.dataset.n) || "hot"); }
      if (hit.length) { focusOn(); drawEdges(litSet()); }
      return hit.length;
    },
    // the model is writing: “My Wealth” shows it while text keeps coming
    writing() {
      const me = els.get("ME");
      if (!me) return;
      me.classList.add("writing");
      clearTimeout(writingTimer);
      writingTimer = setTimeout(() => me.classList.remove("writing"), 1200);
    },
    // the answer is complete: what it rests on stays marked (and the rest dimmed) until the next question
    keep(keys) {
      for (const el of nodeLayer.querySelectorAll(".wnode.act")) el.classList.remove("act");
      svg.classList.remove("busy");
      running.clear();
      clearTimeout(writingTimer); els.get("ME")?.classList.remove("writing");
      const hit = byKeys(keys);
      for (const el of hit) el.classList.add("kept");
      const keep = new Set(idsOf(hit));
      for (const [x, v] of [...pathState]) if (v === "hot" && !keep.has(x) && !nodeLayer.querySelector(`.wnode.ok[data-n="${CSS.escape(x)}"]`)) pathState.delete(x);
      for (const x of keep) if (x !== "ME") pathState.set(x, "hot");
      if (!hit.length && !nodeLayer.querySelector(".wnode.ok")) svg.classList.remove("focusing");
      drawEdges(litSet());
      return hit.length;
    },
    fail() {
      for (const el of nodeLayer.querySelectorAll(".wnode.act")) { el.classList.remove("act"); el.classList.add("bad"); pathState.set(el.dataset.n, "bad"); }
      svg.classList.remove("busy");
      clearTimeout(writingTimer); els.get("ME")?.classList.remove("writing");
      running.clear();
      drawEdges(litSet());
    },
    reset() {
      running.clear();
      hotEdges.clear();
      pathState.clear();
      svg.classList.remove("busy", "focusing");
      clearTimeout(writingTimer);
      for (const el of nodeLayer.querySelectorAll(".wnode")) el.classList.remove("act", "ok", "bad", "lit", "kept", "writing", "hit");
      for (const c of fxLayer.querySelectorAll(".wcomet")) c.remove();
      comets = 0;
      if (g) drawEdges(litSet());
    },
    // the graph's node ids for a tool's kinds (the stream's `nodes` may name kinds or ids)
    ids(spec) {
      if (!g) return [];
      const out = new Set();
      for (const s0 of spec || []) {
        if (byId[s0]) out.add(s0);
        else for (const n of g.nodes) if (n.kind === s0 && n.kind !== "holding") out.add(n.id);
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
      derived = spokesFor(g);
      st = states[key] ||= {sel: null, open: new Set(), shut: new Set(), view: {x: 0, y: 0, k: 1}};
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
