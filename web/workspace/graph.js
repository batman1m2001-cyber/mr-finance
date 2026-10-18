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
  liquidity: ["var(--t2)", "savings"], scenario: ["var(--s7)", "zap"], category: ["var(--in)", "list"],
};
// what a node opens to, behind it on the ring (OWN-GW-15, F11): a class to its holdings, money in or out to its categories
const KID = {class: "holding", flow: "category"};
const isKid = (n) => n.kind === "holding" || n.kind === "category";
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
    class: [`class:${n.ref}`], liquidity: ["kpi:liquidity"], flow: n.keys || [], category: n.keys || [], scenario: [`scenario:${n.ref}`], group: n.keys || []}[n.kind] || [];
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
    liquidity: ["liquidity.value", {}], flow: [n.side === "in" ? "flow.in" : "flow.out", {}], category: [n.side === "in" ? "flow.in" : "flow.out", {}],
    scenario: ["scenario.effect", {}],
  }[n.kind] || ["holding.value", {}]);
}
export const figureOf = (n) => (n.kind === "group" ? (n.value == null ? "" : ["event", "alert"].includes(n.of) ? vnd(n.value, true) : vnd(Math.abs(n.value)))
  : n.kind === "goal" ? `cần ${vnd(n.need)} · ${n.status_label}` : n.kind === "source" ? `${n.count} khoản`
  : n.kind === "liquidity" ? `${vnd(n.value)}${n.months != null ? ` · ${String(n.months).replace(".", ",")} tháng` : ""}`
    : n.kind === "scenario" ? (n.value == null ? "giả định · chưa bật" : `nếu xảy ra ${vnd(n.value, true)}`)
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
    // a news item's or policy item's total reaches “My Wealth” the way it goes (F2): news over its own horizon (3 months),
    // a policy item as a one-off (no monthly rate); a risk is a relation
    const flow = ["event", "alert"].includes(n.kind) && n.value ? {dir: n.value > 0 ? "fwd" : "back",
      ...(n.kind === "event" ? {monthly: Math.abs(n.value) / 3, horizon: n.horizon || "3m"} : {})} : {};
    return {from: n.id, to: "ME", label: SUMS[n.kind], value: n.value, derived: mine.length, ...flow,
      sources: mine.flatMap(e => e.sources || []).filter((x, i, a) => a.findIndex(y => y.type === x.type && y.id === x.id) === i)};
  });
}

export function createGraph(host, {onSelect, staffLabel} = {}) {
  let g = null, byId = {}, lens = null, st = null;
  const states = {};  // per client|scope: selection, opened classes, pan, zoom
  const svg = mk("svg", {class: "ws-svg", role: "group", "aria-label": "Đồ thị tài chính", tabindex: "-1"});
  const defs = mk("defs", {}, svg);
  // the centre's surfaces (OWN-GW-20, plan §3.1): gradients only, their colours CSS tokens on the stops (both themes)
  const grad = (tag, id, attrs, stops) => { const el = mk(tag, {id, ...attrs}, defs); for (const [o, c] of stops) mk("stop", {offset: o, class: c}, el); };
  grad("radialGradient", "ws-aura", {r: "50%"}, [["0.6", "c-aura"], ["1", "c-aura0"]]);
  grad("radialGradient", "ws-body", {cx: "50%", cy: "34%", r: "72%", fx: "50%", fy: "20%"}, [["0", "c-hi"], ["0.55", "c-mid"], ["1", "c-deep"]]);
  grad("linearGradient", "ws-bezel", {x1: 0, y1: 0, x2: 0, y2: 1}, [["0", "c-rim"], ["0.5", "c-rim2"], ["1", "c-rim0"]]);
  grad("radialGradient", "ws-inner", {r: "50%"}, [["0", "c-glow"], ["1", "c-glow0"]]);
  grad("radialGradient", "ws-spec", {r: "50%"}, [["0", "c-spec"], ["1", "c-spec0"]]);
  grad("radialGradient", "ws-face", {cy: "46%", r: "52%"}, [["0", "c-face"], ["1", "c-face2"]]);
  mk("circle", {r: ME_R - 1}, mk("clipPath", {id: "ws-core-clip"}, defs));
  const world = mk("g", {class: "ws-world"}, svg);
  const edgeLayer = mk("g", {class: "ws-edges"}, world);
  const fxLayer = mk("g", {class: "ws-fx", "aria-hidden": "true"}, world);
  const nodeLayer = mk("g", {class: "ws-nodes"}, world);
  host.appendChild(svg);
  // money in motion on its own layer over the graph, same viewBox and pan/zoom: a moving dash then repaints that layer
  // alone, not the edges, nodes and labels under it (measured: 40% less CPU for the same sparks)
  const fxSvg = mk("svg", {class: "ws-fxsvg", "aria-hidden": "true", focusable: "false"});
  const fxWorld = mk("g", {}, fxSvg);
  const sparkLayer = mk("g", {class: "ws-sparks"}, fxWorld);
  host.appendChild(fxSvg);
  const els = new Map();  // node id → its <g>, kept across draws
  let W = 1000, H = 640, pos = {}, edgeTimer = 0, narrow = false, hoverId = null, derived = [], layoutRun = 0;
  const hotEdges = new Map();  // "from>to" → "hot" | "bad": a relation a pulse runs along, drawn while it matters

  // ── view state (OWN-GW-15): three layers ──────────────────────────────────────────────────────────
  // a class opens to its holdings on demand, where the lens shows holdings; money in or out to its categories, where the
  // lens shows categories (F11): picked (or one of its own picked), or opened by hand (“Mở rộng”, double-click)
  const kidLens = (n) => !!lens && !!n && !!KID[n.kind] && lens.kinds.includes(KID[n.kind]);
  const opened = (id) => kidLens(byId[id]) && !st.shut.has(id) && (st.open.has(id) || st.sel === id || (!!st.sel && (byId[st.sel] || {}).parent === id));
  // a folded item hides behind its group node (OWN-GW-30); a group node shows while its fold holds
  let groupNodes = [], fold = new Map(), groupIds = new Set(), groupEdges = [];
  // the active stress tests (UNIFIED_FLOWS_PLAN F6): their hypothetical edges, and what they reach — on Mục tiêu the
  // classes and the spending they move, on Tổng quan the scenarios themselves — shown while they are active. Like a
  // news item, an active scenario reaches “My Wealth” on its own spoke, which carries its whole change (scnSpokes); its
  // fan of class and cost edges shows when it is picked or read, so it never cuts across the ring (OWN-GW-28)
  let scn = null, scnEdges = [], scnSpokes = new Map(), reach = new Set();
  const reached = (n) => reach.has(n.id) && (lens.kinds.includes("scenario") || (n.kind === "scenario" && lens.id === "tong-quan"));
  const shows = (n) => lens.kinds.includes(n.kind) || reached(n);
  const visible = (n) => !!lens && (n.kind === "group" ? groupIds.has(n.id)
    : shows(n) && !fold.has(n.id) && (!isKid(n) || opened(n.parent)));
  const shownAs = (id) => fold.get(id) || id;
  // the edges “My Wealth” has to the second layer are always drawn; any other edge only for what is picked, pointed at,
  // read by the assistant or kept by its answer, and a class's own holdings while it is open
  const spoke = (e) => e.from === "ME" || e.to === "ME";
  // … or the exact path a pulse is taking (a news item to the class it touches): one edge, not the item's whole fan
  const relates = (e, rv) => rv.has(e.from) || rv.has(e.to) || hotEdges.has(`${e.from}>${e.to}`)
    || (!!e.parent && opened(e.parent) && (byId[e.from].kind === "class" || byId[e.from].kind === "category" || byId[e.to].kind === "category"));
  const reveal = () => new Set([st.sel, hoverId].filter(Boolean));
  const allEdges = () => g.edges.map(e => (e.from === "ME" && scnSpokes.get(e.to)) || e).concat(derived, groupEdges, scnShown());
  // an active scenario's edge to a class folded behind “+n”: on the group's node, the same scenario's amounts summed
  function scnShown() {
    const out = new Map();
    for (const e of scnEdges) {
      const to = fold.get(e.to) || e.to, k = `${e.from}>${to}`, was = out.get(k);
      out.set(k, was ? {...was, value: was.value + e.value, monthly: was.monthly != null || e.monthly != null ? (was.monthly || 0) + (e.monthly || 0) : undefined,
        dir: was.value + e.value > 0 ? "fwd" : "back"} : (to === e.to ? e : {...e, to}));
    }
    return [...out.values()];
  }
  const drawable = (e) => byId[e.from] && byId[e.to] && visible(byId[e.from]) && visible(byId[e.to])
    && !(e.agg && opened(e.agg)) && !(e.parent && !opened(e.parent));
  const shownEdges = () => { const rv = reveal(); return allEdges().filter(e => drawable(e) && (spoke(e) || `${e.from}>${e.to}` === st.edge || relates(e, rv))); };
  const links = (id) => allEdges().filter(e => drawable(e) && (e.from === id || e.to === id));
  const other = (e, id) => byId[e.from === id ? e.to : e.from];

  // ── layout (OWN-GW-26…31, GRAPH_CORE_LAYOUT_PLAN.md §2): one ring, one node per slot ─────────────────
  // Every node joined to “My Wealth” sits on one ellipse, nothing between it and the centre, so no spoke crosses a
  // disc; its label sits outside the ring, so no spoke crosses a label. A slot is the room the node and its label take
  // along the ring at their place, in pixels; the ellipse is the largest that keeps every label on the canvas. When the
  // slots need more ring than there is, the smallest items of the most crowded group fold into one group node.
  const RING = ["flow_out", "risk", "alert", "event", "scenario", "goal", "liquidity", "source", "flow_in", "asset", "debt"];
  const HOME = {flow_out: 0, risk: 26, alert: 50, event: 74, scenario: 98, goal: 126, liquidity: 156, source: 112, flow_in: 180, asset: 255, debt: 322};
  const NEVER_FOLD = new Set(["flow_out", "flow_in", "liquidity"]);
  // which group folds first when the ring is short: news, policy and sources first, the assets last (OWN-GW-27)
  const FOLD_FIRST = {source: 1, event: 1, alert: 1, scenario: 0.8, goal: 0.7, risk: 0.6, debt: 0.45, asset: 0.3};
  // … and a lens's own subject folds last there: the news on Tin, the goals on Mục tiêu (OWN-GW-27)
  const SUBJECT = {"tin": ["event", "alert"], "muc-tieu": ["goal", "scenario"], "rui-ro": ["risk"], "tai-san": ["asset", "debt"], "dong-tien": ["liquidity"]};
  const foldWeight = (key) => (FOLD_FIRST[key] || 0.5) * ((SUBJECT[lens.id] || []).includes(key) ? 0.15 : 1);
  const GROUP_WORD = {risk: "rủi ro", alert: "chính sách", event: "tin tức", scenario: "kịch bản", goal: "mục tiêu", source: "nguồn dữ liệu", asset: "lớp tài sản", debt: "khoản nợ"};
  const SUMMABLE = new Set(["event", "alert", "asset", "debt", "risk"]);
  const groupOf = (n) => (n.kind === "flow" ? `flow_${n.side === "out" ? "out" : "in"}` : n.kind === "class" ? (n.liability ? "debt" : "asset") : n.kind === "group" ? n.group : n.kind);
  const weight = (n) => Math.abs(n.value ?? n.need ?? 0);
  const discR = (n) => (n.kind === "family" ? ME_R : isKid(n) ? 13 : 24);
  const FAN = 64;  // how far behind its class a holding sits

  // text widths, measured once per string on a canvas (no layout), with the label's real font
  let pen = null, family = "", sizes = null;
  const widths = new Map();
  function textW(text, px, weight_) {
    const k = `${px}|${weight_}|${text}`;
    let w = widths.get(k);
    if (w == null) {
      if (!pen) { pen = document.createElement("canvas").getContext("2d"); family = getComputedStyle(svg).fontFamily || "sans-serif"; }
      pen.font = `${weight_} ${px}px ${family}`;
      w = pen.measureText(text).width;
      widths.set(k, w);
    }
    return w;
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { widths.clear(); pen = null; if (g && lens) draw(); });
  function fontSizes() {  // the CSS decides (a phone's labels are larger): read once per draw from a label on screen
    const probe = nodeLayer.querySelector(".wnode:not(.k-family):not(.k-holding):not(.k-category) .wlbl");
    const fp = nodeLayer.querySelector(".wnode .wfig");
    const name = probe ? parseFloat(getComputedStyle(probe).fontSize) || 12 : narrow ? 14 : 12;
    const fig = fp ? parseFloat(getComputedStyle(fp).fontSize) || 11 : narrow ? 12.5 : 11;
    return {name, fig, line: Math.round(name * 1.3)};
  }
  // a label's lines and its box at one of four places around its disc (relative to the node's centre). Above or below
  // a node, where its width takes ring, a long name wraps onto two lines; a goal's figure says its status only when it
  // is off track (its halo says so too; the tooltip and the inspector keep the full figure)
  function wrap(text, px, limit) {
    if (text.length <= limit || !text.includes(" ")) return [text];
    let best = [text], w = Infinity;
    for (let i = text.indexOf(" "); i > 0; i = text.indexOf(" ", i + 1)) {
      const a = text.slice(0, i), b = text.slice(i + 1), m = Math.max(textW(a, px, 650), textW(b, px, 650));
      if (m < w) { w = m; best = [a, b]; }
    }
    return best;
  }
  function labelAt(n, where, r) {
    const max = narrow ? 22 : isKid(n) ? 20 : 28;
    const text = short(n.label, max), {name, fig: fpx, line} = sizes;
    const fig = n.kind === "source" || isKid(n) ? "" : n.kind === "goal"
      ? `cần ${vnd(n.need)}${n.status && n.status !== "on_track" ? ` · ${n.status_label}` : ""}` : figureOf(n);
    const lines = wrap(text, name, where === "above" || where === "below" ? (narrow ? 11 : 14) : narrow ? 12 : 16);
    const w = Math.max(...lines.map(t => textW(t, name, 650)), fig ? textW(fig, fpx, 400) : 0) + 2;
    const tag = n.kind === "scenario" ? 14 : 0, nl = lines.length;
    const asc = name * 0.95, under = fig ? line * nl + fpx * 0.3 : line * (nl - 1) + name * 0.3;  // below the first baseline
    const lx = where === "right" ? r + 8 : where === "left" ? -r - 8 : 0;
    const ly = where === "below" ? r + 4 + tag + asc : where === "above" ? -r - 5 - under : asc - (asc + under) / 2;
    const x0 = where === "right" ? lx : where === "left" ? lx - w : -w / 2;
    return {where, text, lines, fig, lx, ly, line, figY: ly + line * nl, box: [x0, ly - asc, x0 + w, ly + under]};
  }
  const lensShows = (n) => !!lens && shows(n);

  // the ring: a rounded square (a superellipse) inside the canvas — convex, so a spoke from the centre still meets
  // nothing before its node, and its corners hold nodes an ellipse would waste
  const SQ = 2 / 2.7;
  const ringAt = (t, rx, ry) => { const c = Math.cos(t), s = Math.sin(t); return [rx * Math.sign(c) * Math.abs(c) ** SQ, ry * Math.sign(s) * Math.abs(s) ** SQ]; };
  // the arc length of the ring, sampled once per size: positions along the ring are in pixels, not degrees
  function arcTable(rx, ry) {
    const N = 720, S = new Float64Array(N + 1);
    let [px, py] = ringAt(0, rx, ry);
    for (let k = 1; k <= N; k++) {
      const [x, y] = ringAt(2 * Math.PI * k / N, rx, ry);
      S[k] = S[k - 1] + Math.hypot(x - px, y - py); px = x; py = y;
    }
    const P = S[N];
    const phiAt = (s) => {
      s = ((s % P) + P) % P;
      let lo = 0, hi = N;
      while (hi - lo > 1) { const m = (lo + hi) >> 1; if (S[m] <= s) lo = m; else hi = m; }
      return 2 * Math.PI * (lo + (s - S[lo]) / Math.max(1e-9, S[hi] - S[lo])) / N;
    };
    const sAt = (phi) => { const u = ((phi / (2 * Math.PI)) % 1 + 1) % 1 * N, k = Math.floor(u); return S[k] + (S[Math.min(N, k + 1)] - S[k]) * (u - k); };
    return {P, phiAt, sAt};
  }

  // the synthetic node a folded group shows as (kind `group`), or the “Thu gọn” node of a group opened by hand
  function groupNode(key, members, close) {
    const of = members[0].kind, sum = members.reduce((t, n) => t + (n.value || 0), 0);
    return close
      ? {id: `GR:${key}:close`, kind: "group", group: key, of, close: true, label: "Thu gọn", title: `Thu gọn ${GROUP_WORD[key] || ""}`.trim(), members: [], keys: [], value: null}
      : {id: `GR:${key}`, kind: "group", group: key, of, label: `${members.length} ${GROUP_WORD[key] || "mục"} khác`, members: members.map(n => n.id),
        keys: [...new Set(members.flatMap(keysOf))], value: SUMMABLE.has(key) ? sum : null};
  }

  // the fold is decided on a canvas no larger than the reference (owner, 2026-10-18): a larger screen draws the
  // reference's fold bigger instead of unfolding every group, so “+4 mục tiêu khác” reads the same on a laptop and a
  // wall screen; a smaller canvas folds more, as before. REF_AREA: the canvas a 1440×900 window gives (992×563)
  const REF_AREA = 992 * 563;
  function layout() {
    if (narrow || W * H <= REF_AREA) return foldAndPlace();
    const w0 = W, h0 = H, s = Math.sqrt(REF_AREA / (W * H));
    let ref;
    try { W = Math.round(W * s); H = Math.round(H * s); ref = foldAndPlace(); } finally { W = w0; H = h0; }
    return foldAndPlace(ref.folded);
  }
  function foldAndPlace(seed = null) {
    const cx = W / 2, cy = H / 2, M = narrow ? 8 : 12;
    sizes = fontSizes();
    const out = {ME: {x: cx, y: cy, a: 0}};
    const byGroup = new Map();
    for (const n of g.nodes) {
      if (n.kind === "family" || isKid(n) || !lensShows(n)) continue;
      const k = groupOf(n);
      if (!byGroup.has(k)) byGroup.set(k, []);
      byGroup.get(k).push(n);
    }
    for (const list of byGroup.values()) list.sort((a, b) => weight(b) - weight(a) || (a.id < b.id ? -1 : 1));
    // what may not fold, by level: 0 nothing of an opened group; 1 a group opened earlier may fold again; 2 even the one
    // opened last folds its smallest (it opens partly: the rest stay behind “+n khác”), never the selection or an open class
    const keepOut = (n, level) => st.sel === n.id || opened(n.id) || !!n.active  // an active scenario stays in sight
      || (isOpen(groupOf(n)) && (level === 0 || (level === 1 && groupOf(n) === st.lastGroup)));
    const folded = new Map(seed || []);  // group key → members folded (the smallest first)
    let warm = null;  // each try starts from the last one's ring and angles: folding one item changes little
    let unpin = false;  // the flows leave their sides only when their half cannot hold what the person opened
    for (let tries = 0; tries < 400; tries++) {
      const items = [], made = [];
      for (const key of RING) {
        const list = byGroup.get(key);
        if (!list) continue;
        const gone = new Set((folded.get(key) || []).map(n => n.id));
        for (const n of list) if (!gone.has(n.id)) items.push(n);
        if (gone.size) { const gn = groupNode(key, folded.get(key)); gn.part = isOpen(key); items.push(gn); made.push(gn); }
        if (isOpen(key) && list.length > 1) { const gn = groupNode(key, list, true); items.push(gn); made.push(gn); }
      }
      const res = placeRing(items, cx, cy, M, false, warm, unpin);
      warm = res.warm || warm;
      if (res.ok || !items.length) return finish(out, res, made, folded);
      // fold one more: in the group taking the most ring per member, its smallest member not kept out; failing that,
      // from a group opened earlier; failing that (and the flows unpinned), from the one opened last
      let best = null;
      for (const level of unpin || !res.arc ? [0, 1, 2] : [0, 1]) {
        for (const key of RING) {
          const list = byGroup.get(key);
          if (!list || NEVER_FOLD.has(key) || (res.arc && !res.arc.has(key))) continue;
          const f = folded.get(key) || [], open_ = list.filter(n => !f.includes(n) && !keepOut(n, level));
          if (open_.length < (f.length ? 1 : 2)) continue;  // a group node takes a slot: folding one alone gains nothing
          const room = (res.demand[key] || 0) / Math.max(1, list.length - f.length) * foldWeight(key);  // ring per member
          if (!best || room > best.room) best = {key, room, open_, f};
        }
        if (best) break;
      }
      if (!best && res.arc && !unpin) { unpin = true; continue; }
      if (!best) return finish(out, placeRing(items, cx, cy, M, true, warm, true), made, folded);  // nothing left to fold: the best the ring can do
      const add = best.open_.slice(-(best.f.length ? 1 : 2));
      folded.set(best.key, [...best.f, ...add].sort((a, b) => weight(b) - weight(a)));
    }
    return finish(out, {ok: false, pos: {}}, [], folded);
  }
  function finish(out, res, made, folded) {
    Object.assign(out, res.pos || {});
    out.ring = res.rx ? {rx: res.rx, ry: res.ry} : null;
    out.groups = made;
    out.folded = folded;  // the reference's fold, for the larger canvas
    out.fold = new Map();
    for (const [key, list] of folded) for (const n of list) out.fold.set(n.id, `GR:${key}`);
    return out;
  }

  // the ring for these items, in order: their slots, labels and holdings, sized to the canvas
  function placeRing(items, cx, cy, M, force = false, warm = null, unpin = false) {
    const n = items.length;
    if (!n) return {ok: true, pos: {}, demand: {}};
    let rx = warm ? warm.rx : W / 2 - M - 40, ry = warm ? warm.ry : H / 2 - M - 30;
    const minR = ME_R + 70;
    const bump = new Float64Array(n);  // extra room asked for after a box overlapped, per pair (i, i+1)
    const gapBase = narrow ? 7 : 8;
    const gw = items.map((it, i) => (groupOf(it) !== groupOf(items[(i + 1) % n]) ? 1.8 : 1));
    // start from the last try's angles where the item was there, else between its neighbours, else evenly
    let phis = items.map((it, i) => (warm && warm.phi[it.id] != null ? warm.phi[it.id] : null));
    if (phis.every(v => v == null)) phis = items.map((_, i) => 2 * Math.PI * i / n);
    else phis = phis.map((v, i) => {
      if (v != null) return v;
      let a = i - 1, b = i + 1;
      while (phis[(a + n) % n] == null) a--;
      while (phis[b % n] == null) b++;
      const pa = phis[(a + n) % n], pb = phis[b % n], span = ((pb - pa) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI);
      return pa + span * (i - a) / (b - a);
    });
    let result = null;
    const keep = (rx_, ry_) => ({rx: rx_, ry: ry_, phi: Object.fromEntries(items.map((it, i) => [it.id, phis[i]]))});
    const passes = force ? 8 : 24;
    for (let pass = 0; pass < passes; pass++) {
      const last = pass === passes - 1;
      if (rx < minR || ry < minR * 0.8) {
        if (!force) return {ok: false, pos: {}, demand: result ? result.demand : {}};
        rx = Math.max(rx, minR); ry = Math.max(ry, minR * 0.8);
      }
      const T = arcTable(rx, ry);
      let s = null, place = null;
      for (let it = 0; it < 8; it++) {  // the angle decides the label's side, the side decides the slot: to a fixed point
        place = items.map((node, i) => slot(node, phis[i], rx, ry, cx, cy));
        const need = (i) => place[i].hi + place[(i + 1) % n].lo + gapBase * gw[i] + bump[i];
        s = allocate(items, need, T, gw, force, unpin);
        if (!s) {
          if (it < 3) { phis = phis.map((v, i) => v); continue; }  // a flipped label may make room on the next round
          const demand = {};
          items.forEach((node, i) => { const k = groupOf(node); demand[k] = (demand[k] || 0) + place[i].lo + place[i].hi + gapBase * gw[i]; });
          let total = 0; for (let i = 0; i < n; i++) total += need(i);
          return {ok: false, pos: {}, demand, short: total - T.P, arc: allocate.short, warm: keep(rx, ry)};
        }
        const next = s.map(T.phiAt);
        let moved = 0;
        phis = phis.map((v, i) => {  // damped: half way, the short way round
          const d = ((next[i] - v + 3 * Math.PI) % (2 * Math.PI)) - Math.PI;
          moved = Math.max(moved, Math.abs(d));
          return it < 2 ? next[i] : v + d / 2;
        });
        if (moved < 0.002) break;
      }
      place = items.map((node, i) => slot(node, phis[i], rx, ry, cx, cy));
      result = {demand: {}};
      items.forEach((node, i) => { const k = groupOf(node); result.demand[k] = (result.demand[k] || 0) + place[i].lo + place[i].hi; });
      // boxes on the canvas: from the centre's disc, every disc, label and holding
      const abs = place.map(p => p.boxes.map(b => [b[0] + p.x, b[1] + p.y, b[2] + p.x, b[3] + p.y]));
      let fixed = false;
      const depth = (a, b, m) => Math.max(0, Math.min(a[2] + m - b[0], b[2] + m - a[0], a[3] + m - b[1], b[3] + m - a[1]));
      const widen = (i, j, by) => {  // more room between items i and j, on the shorter way round
        const fwd = (j - i + n) % n <= n / 2, [p, q] = fwd ? [i, j] : [j, i];
        const steps = (q - p + n) % n;
        for (let k = 0; k < steps; k++) bump[(p + k) % n] += by / steps;
        fixed = true;
      };
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
        let d = 0;
        for (const a of abs[i]) for (const b of abs[j]) d = Math.max(d, depth(a, b, 3));
        if (d > 0) widen(i, j, d + 2);
      }
      // a spoke never crosses another node's disc or label (the slots between are widened instead)
      const meBox = [cx - ME_R - 10, cy - ME_R - 10, cx + ME_R + 10, cy + ME_R + 10];
      for (let j = 0; j < n; j++) {
        const pts = spokePts(cx, cy, place[j].x, place[j].y, discR(items[j]));
        for (let i = 0; i < n; i++) {
          if (i !== j && abs[i].some(b => pts.some(([x, y]) => x > b[0] - 2 && x < b[2] + 2 && y > b[1] - 2 && y < b[3] + 2))) widen(i, j, 6);
        }
      }
      if (fixed && !last) continue;
      // keep everything on the canvas: shrink the ellipse by what spills over
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      for (const bs of abs.concat([[meBox]], place.map(p => p.reserve ? [[p.reserve[0] + p.x, p.reserve[1] + p.y, p.reserve[2] + p.x, p.reserve[3] + p.y]] : []))) {
        for (const b of bs) { x0 = Math.min(x0, b[0]); y0 = Math.min(y0, b[1]); x1 = Math.max(x1, b[2]); y1 = Math.max(y1, b[3]); }
      }
      const dx = Math.max(0, M - x0, x1 - (W - M)), dy = Math.max(0, M - y0, y1 - (H - M));
      if ((dx > 0.5 || dy > 0.5) && !last) { rx -= dx + 1; ry -= dy + 1; continue; }
      const pos = {};
      items.forEach((node, i) => {
        const p = place[i];
        pos[node.id] = {x: p.x, y: p.y, a: phis[i] * 180 / Math.PI, label: p.label, ring: true, quiet: fixed && !!p.label.text};
        for (const k of p.kids) pos[k.id] = {x: k.x, y: k.y, a: phis[i] * 180 / Math.PI, kid: true, label: k.label};
      });
      return {ok: !fixed && !force, pos, demand: result.demand, rx, ry, warm: keep(rx, ry)};
    }
    return {ok: false, pos: {}, demand: result ? result.demand : {}};
  }

  // one node's slot at angle phi: its position, label, holdings, and the room it takes along the ring (lo before, hi after)
  function slot(node, phi, rx, ry, cx, cy) {
    const c = Math.cos(phi), s = Math.sin(phi), r = discR(node);
    const [ox0, oy0] = ringAt(phi, rx, ry), x = cx + ox0, y = cy + oy0;
    const [ax, ay] = ringAt(phi - 0.004, rx, ry), [bx, by] = ringAt(phi + 0.004, rx, ry);
    const tl = Math.hypot(bx - ax, by - ay) || 1, tx = (bx - ax) / tl, ty = (by - ay) / tl;  // the ring's direction here
    const open_ = !!KID[node.kind] && opened(node.id);
    // an opened class's holdings fan out behind it: its label runs along the ring instead (the side it points to)
    const along = Math.abs(tx) >= Math.abs(ty) ? (tx > 0 ? "right" : "left") : ty > 0 ? "below" : "above";
    const tag = node.kind === "scenario" ? 16 : 0;
    const boxes = [[-r - 2, -r - 2, r + 2, r + 2 + tag]];
    const kids = [];
    let reserve = null;
    if (kidLens(node)) {
      // the band behind a class where its holdings fan out: kept free on the canvas whether or not it is open
      const ox = ty, oy = -tx;  // outward (the ring runs clockwise)
      reserve = [ox * (FAN + 30) - 14, oy * (FAN + 30) - 14, ox * (FAN + 30) + 14, oy * (FAN + 30) + 14];
      if (open_) {
        const list = g.nodes.filter(h => h.parent === node.id && h.kind === KID[node.kind] && lensShows(h));
        const rows = list.length > 8 ? 2 : 1, per = Math.ceil(list.length / rows), step = 30;
        list.forEach((h, i) => {
          const row = rows === 2 ? i % 2 : 0, k = rows === 2 ? Math.floor(i / 2) : i;
          const along = (k - (per - 1) / 2) * step + (row ? step / 2 : 0), dist = FAN + (row ? 34 : 0);
          const kx = ox * dist + tx * along, ky = oy * dist + ty * along;
          const lbl = labelAt(h, ky + y < cy ? "above" : "below", 13);
          kids.push({id: h.id, x: x + kx, y: y + ky, label: lbl});
          boxes.push([kx - 15, ky - 15, kx + 15, ky + 15]);
        });
      }
    }
    // the label's side: an open class tries along the ring first, then the other sides, and takes the first clear of its
    // holdings (at a corner of the ring the side it points to is where a holding fans out)
    const flip = {right: "left", left: "right", above: "below", below: "above"};
    const sides = open_ ? [along, flip[along], ...["above", "below", "right", "left"].filter(w => w !== along && w !== flip[along])]
      : [!narrow && Math.abs(c) > 0.38 ? (c > 0 ? "right" : "left") : s < 0 ? "above" : "below"];
    const own = open_ ? spokePts(cx, cy, x, y, r).map(([px, py]) => [px - x, py - y]) : [];  // and of its own spoke
    const clear = (b) => boxes.slice(1).every(k => b[2] <= k[0] - 3 || b[0] >= k[2] + 3 || b[3] <= k[1] - 3 || b[1] >= k[3] + 3)
      && !own.some(([px, py]) => px > b[0] - 2 && px < b[2] + 2 && py > b[1] - 2 && py < b[3] + 2);
    const label = sides.map(w => labelAt(node, w, r)).find(l => clear(l.box)) || labelAt(node, sides[0], r);
    boxes.splice(1, 0, label.box);
    let lo = 0, hi = 0;
    for (const b of boxes) for (const [bx, by] of [[b[0], b[1]], [b[2], b[1]], [b[0], b[3]], [b[2], b[3]]]) {
      const t = bx * tx + by * ty;
      lo = Math.max(lo, -t); hi = Math.max(hi, t);
    }
    return {x, y, lo, hi, label, boxes, kids, reserve, kid: false};
  }

  // positions along the ring (pixels from the right, clockwise): money in and out pinned left and right when both
  // show; otherwise the ring is turned so its groups sit near their usual places. Null when the ring is too short.
  function allocate(items, need, T, gw, force = false, unpin = false) {
    allocate.short = null;
    const n = items.length, ids = items.map(groupOf);
    const iOut = ids.indexOf("flow_out"), iIn = ids.indexOf("flow_in");
    const spread = (from, to, start, len) => {  // pairs from..to-1 (cyclic), first item at `start`
      let req = 0, wsum = 0;
      for (let i = from; i !== to; i = (i + 1) % n) { req += need(i); wsum += gw[i]; }
      if (req > len + 0.01) return null;
      const slack = len - req, out = [[from, start]];
      let p = start;
      for (let i = from; i !== to; i = (i + 1) % n) { p += need(i) + slack * gw[i] / wsum; out.push([(i + 1) % n, p]); }
      return out;
    };
    const s = new Array(n);
    if (iOut >= 0 && iIn >= 0 && n > 2 && !unpin) {  // pinned, always: money in stays left and money out right (the mental map)
      const half = T.sAt(Math.PI);
      const a = spread(iOut, iIn, 0, half), b = spread(iIn, iOut, half, T.P - half);
      if (a && b) { for (const [i, p] of a.concat(b)) s[i] = p; return s; }
      if (!force) {  // say which arc is short: only its groups fold
        const arc = new Set();
        const [from, to] = a ? [iIn, iOut] : [iOut, iIn];
        for (let i = from; i !== to; i = (i + 1) % n) arc.add(ids[i]);
        allocate.short = arc;
        return null;
      }
    }
    if (n === 1) { s[0] = T.sAt(HOME[ids[0]] * Math.PI / 180); return s; }
    let req = 0, wsum = 0;
    for (let i = 0; i < n; i++) { req += need(i); wsum += gw[i]; }
    if (req > T.P + 0.01 && !force) return null;
    const squeeze = Math.min(1, T.P / req), slack = Math.max(0, T.P - req);  // forced: everything shrinks alike
    s[0] = 0;
    for (let i = 0; i < n - 1; i++) s[i + 1] = s[i] + need(i) * squeeze + slack * gw[i] / wsum;
    // turn: the circular mean of how far each item is from its group's usual place
    let sx = 0, sy = 0;
    for (let i = 0; i < n; i++) {  // money in and out weigh most: they keep near their sides
      const d = (T.sAt(HOME[ids[i]] * Math.PI / 180) - s[i]) / T.P * 2 * Math.PI, wt = ids[i].startsWith("flow_") ? 8 : 1;
      sx += wt * Math.cos(d); sy += wt * Math.sin(d);
    }
    const shift = Math.atan2(sy, sx) / (2 * Math.PI) * T.P;
    return s.map(v => v + shift);
  }

  // a spoke's points (the centre's rim to the node's inner side), for the layout's checks
  function spokePts(cx, cy, x, y, r) {
    const dx = x - cx, dy = y - cy, l = Math.hypot(dx, dy) || 1, ux = dx / l, uy = dy / l, out = [];
    const a = ME_R + 2, b = l - r - 2;
    for (let d = a; d <= b; d += 6) out.push([cx + ux * d, cy + uy * d]);
    return out;
  }

  // ── nodes: created once per id, moved and faded after ───────────────────────────────────────────
  function nodeEl(n) {
    let el = els.get(n.id);
    const sig = n.kind === "group" ? `${n.label}|${n.value}|${!!n.part}` : n.kind === "scenario" ? `${n.value}|${!!n.active}` : "";
    if (el && el.dataset.sig !== sig) { el.remove(); els.delete(n.id); el = null; }  // a group node that now folds another count
    if (el) return el;
    const me = n.kind === "family", r = discR(n);
    const [tone, ic] = (n.kind === "flow" || n.kind === "category") && n.side === "out" ? ["var(--out)", "cart"] : LOOK[n.kind === "group" ? n.of : n.kind] || LOOK.class;
    el = mk("g", {class: `wnode k-${n.kind}${n.active ? " live" : ""}`, tabindex: "0", role: "button", "data-n": n.id, "aria-pressed": "false",
      "aria-label": `${(g.kinds.find(k => k.kind === n.kind) || {}).label || n.kind}: ${n.label}`}, nodeLayer);
    el.style.setProperty("--tone", tone);
    el.dataset.r = r;
    el.dataset.sig = sig;
    const keys = keysOf(n);
    if (keys.length) el.setAttribute("data-focus", keys.join(" "));
    mk("circle", {r: r + 9, class: "wring", "aria-hidden": "true"}, el);  // the activity ring (transform/opacity)
    mk("circle", {r: r + 4, class: "wburst", "aria-hidden": "true"}, el);  // where a pulse arrives (OWN-GW-16)
    if (n.kind === "risk" || (n.kind === "goal" && n.status !== "on_track")) {
      mk("circle", {r: r + 5, class: "whalo", style: `--halo:${n.kind === "goal" && n.status === "at_risk" ? "var(--warning)" : "var(--critical)"}`}, el);
    }
    if (me) {  // the financial core (OWN-GW-20…25): aura, rings, bezel, glass body, inner light, face, figures
      const back = mk("g", {class: "wme-back", "aria-hidden": "true"}, el);
      mk("circle", {r: r + 34, class: "wme-aura", fill: "url(#ws-aura)"}, back);
      mk("circle", {r: r + 12, class: "wme-orbit"}, back);
      mk("circle", {r: r + 21, class: "wme-orbit o2"}, back);
      mk("circle", {r: r + 3, class: "wme-drift"}, back);
      mk("circle", {r: r + 3, class: "wme-drift d2"}, back);
    }
    mk("circle", {r, class: me ? "wcore me" : "wcore", fill: me ? "url(#ws-body)" : null}, el);
    if (me) {
      const glass = mk("g", {"clip-path": "url(#ws-core-clip)", "aria-hidden": "true"}, el);
      mk("ellipse", {cy: r * 0.48, rx: r * 0.82, ry: r * 0.44, class: "wme-inner", fill: "url(#ws-inner)"}, glass);
      mk("g", {class: "wme-bandhost"}, glass);  // the light a payment sends across (drawEdges, on the sparks' clock)
      mk("ellipse", {cy: -r * 0.56, rx: r * 0.62, ry: r * 0.3, class: "wme-spec", fill: "url(#ws-spec)"}, glass);
      const rim = mk("g", {"aria-hidden": "true"}, el);
      mk("circle", {r: r - 6, class: "wme-ticks"}, rim);
      mk("circle", {r: r + 1.5, class: "wme-bezel", stroke: "url(#ws-bezel)"}, rim);
      mk("circle", {r: r + 1.5, class: "wme-act"}, rim);
      mk("circle", {r: r + 5.5, class: "wme-sel"}, rim);
      mk("g", {class: "wme-ports"}, rim);  // where each money edge meets the rim (drawEdges)
      mk("g", {class: "wme-ripples"}, rim);
      mk("circle", {r: r * 0.86, class: "wme-face", fill: "url(#ws-face)", "aria-hidden": "true"}, el);  // a soft dark vignette under the figures
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
    } else if (n.kind === "group") {  // “+n”: what the ring folded, opened on a click
      mk("text", {y: 5, "text-anchor": "middle", class: "wcount"}, el).textContent = n.close ? "−" : `+${n.members.length}`;
      mk("text", {class: "wlbl"}, el);
      if (n.value != null) mk("text", {class: `wfig ${["event", "alert"].includes(n.of) ? signClass(n.value) : ""}`}, el);
    } else {
      const inner = mk("svg", {x: -r * 0.52, y: -r * 0.52, width: r * 1.04, height: r * 1.04, viewBox: "0 0 24 24", fill: "none",
        stroke: tone, "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round", class: "wicon"}, el);
      inner.innerHTML = iconPaths(n.kind === "class" ? CLASS_ICON[n.ref] || ic : ic);
      if (n.kind === "scenario") mk("text", {y: r + 13, "text-anchor": "middle", class: "wtag"}, el).textContent = "giả định";
      if (n.family) {  // another family member's (family scope, F1): their initial on the rim, never mixed up with the person's own
        const who = n.owner || (n.owners || []).filter(Boolean).join(", "), first = (n.owner || (n.owners || [])[0] || "?").trim().split(/\s+/).pop();
        const badge = mk("g", {class: "wown", transform: `translate(${(r * 0.72).toFixed(1)},${(-r * 0.72).toFixed(1)})`, role: "img", "aria-label": `Của ${who}`}, el);
        mk("title", {}, badge).textContent = `Của ${who}`;
        mk("circle", {r: 7.5}, badge);
        const many = !n.owner && (n.owners || []).filter(Boolean).length > 1;  // a category shared: how many, not one initial
        mk("text", {y: 3.2, "text-anchor": "middle"}, badge).textContent = many ? String(n.owners.filter(Boolean).length) : first.charAt(0).toUpperCase();
      }
      mk("text", {class: "wlbl"}, el);
      if (n.kind !== "source") {
        const f = mk("text", {class: `wfig ${["event", "alert", "scenario"].includes(n.kind) ? signClass(n.value) : ""}`}, el);
        const [m, i] = howOf(n);
        if (n.value != null) { f.setAttribute("data-metric", m); f.setAttribute("data-in", JSON.stringify(i)); f.setAttribute("tabindex", "0"); f.setAttribute("role", "button"); f.classList.add("num-svg"); }
      }
    }
    if (n.kind === "group") {
      // a group opened only partly (the ring cannot hold all of it): the rest stay here, listed, and Danh sách has them all
      el.setAttribute("aria-label", n.close ? n.title : n.part ? `${n.label}: không đủ chỗ trên đồ thị` : `${n.label}: mở nhóm`);
      el.setAttribute("aria-expanded", String(!!n.close || !!n.part));
      hover(el, n.close ? esc(n.title) : `<b>${esc(n.label)}</b><br>${n.members.slice(0, 6).map(id => esc(byId[id].label)).join("<br>")}${n.members.length > 6 ? "<br>…" : ""}<br><span class="muted">${n.part ? "Không đủ chỗ để mở hết · xem đủ trong Danh sách" : "Bấm để mở nhóm"}</span>`);
      if (!n.part) {
        el.addEventListener("click", () => openGroup(n));
        el.addEventListener("keydown", (ev) => { if (ev.target === el && (ev.key === "Enter" || ev.key === " ")) { ev.preventDefault(); openGroup(n); } });
      }
      els.set(n.id, el);
      return el;
    }
    hover(el, `<b>${esc(n.label)}</b><br>${esc((g.kinds.find(k => k.kind === n.kind) || {}).label || "")}${figureOf(n) ? " · " + esc(figureOf(n)) : ""}`);
    el.addEventListener("click", (ev) => { if (!ev.target.closest(".num-svg")) select(n.id); });
    el.addEventListener("dblclick", () => { if (KID[n.kind]) toggle(n.id); });
    // pointing at a node shows its relations (and only then): the web stays out of the way until asked for
    el.addEventListener("pointerenter", () => { if (hoverId !== n.id && n.id !== "ME") { hoverId = n.id; drawEdges(litSet()); } });
    el.addEventListener("pointerleave", () => { if (hoverId === n.id) { hoverId = null; drawEdges(litSet()); } });
    el.addEventListener("keydown", (ev) => {
      if (ev.target !== el) return;
      if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); select(n.id); }
      if ((ev.key === "+" || ev.key === "-") && KID[n.kind]) { ev.preventDefault(); toggle(n.id); }
    });
    els.set(n.id, el);
    return el;
  }

  // ── labels (OWN-GW-26): the ring gave each its place, outside the ring and clear of every disc, label and spoke
  function placeLabels(list) {
    for (const n of list) {
      if (n.kind === "family") continue;
      const el = els.get(n.id), q = pos[n.id], lbl = el && el.querySelector(".wlbl");
      if (!lbl || !q) continue;
      const L = q.label || labelAt(n, "below", discR(n)), f = el.querySelector(".wfig");
      const anchor = L.where === "right" ? "start" : L.where === "left" ? "end" : "middle";
      lbl.setAttribute("x", L.lx); lbl.setAttribute("y", L.ly); lbl.setAttribute("text-anchor", anchor);
      if (L.lines.length > 1) {
        lbl.replaceChildren(...L.lines.map((t, i) => { const sp = mk("tspan", {x: L.lx, dy: i ? L.line : 0}); sp.textContent = t; return sp; }));
      } else lbl.textContent = L.text;
      if (L.text !== n.label) lbl.setAttribute("data-full", n.label); else lbl.removeAttribute("data-full");
      if (f) { f.setAttribute("x", L.lx); f.setAttribute("y", L.figY); f.setAttribute("text-anchor", anchor); f.textContent = L.fig; }
      el.classList.toggle("quiet", !!q.quiet);  // only when even folding could not make room
    }
  }

  // group nodes and their spokes (one per group: the sum of what it folds, with all their records)
  function flowOf(es) {  // members' money as one edge: when the members that move money all go the same way (the rest add none)
    const moving = es.filter(e => e.dir && e.value != null);
    if (!moving.length) return {};
    const into = es[0].to === "ME", same = (e) => (e.to === "ME") === into;
    if (!es.every(same) || new Set(moving.map(e => e.dir)).size !== 1) return {};
    return {dir: moving[0].dir, monthly: moving.every(e => e.monthly != null) ? moving.reduce((t, e) => t + e.monthly, 0) : undefined};
  }
  function applyGroups(list, f) {
    for (const gn of groupNodes) if (!list.some(x => x.id === gn.id)) delete byId[gn.id];
    groupNodes = list; fold = f; groupIds = new Set(list.map(x => x.id));
    for (const gn of list) byId[gn.id] = gn;
    const base = g.edges.concat(derived);
    groupEdges = list.filter(x => !x.close).map(x => {
      const es = x.members.map(id => base.find(e => (e.from === id && e.to === "ME") || (e.from === "ME" && e.to === id))).filter(Boolean);
      const into = !es.length || es[0].to === "ME", vals = es.filter(e => e.value != null);
      return {from: into ? x.id : "ME", to: into ? "ME" : x.id, label: `${x.members.length} mục gộp`, derived: es.length,
        value: vals.length ? vals.reduce((t, e) => t + e.value, 0) : null, certainty: es.length ? certaintyOf(es[0], byId) : undefined,
        // folded debts still repay: their month's repayments run on the group's edge (money stays in motion, OWN-GW-16)
        repaid: es.reduce((t, e) => t + (e.repaid && certaintyOf(e, byId) === "actual" ? e.repaid : 0), 0) || undefined,
        // folded money edges keep moving: their monthly rates add up when they all go the same way (F2)
        ...(flowOf(es)),
        sources: es.flatMap(e => e.sources || []).filter((y, i, a) => a.findIndex(z => z.type === y.type && z.id === y.id) === i)};
    });
  }
  // a group opened by hand stays open in its lens (only there), the last one opened kept first
  const isOpen = (key) => !!lens && st.groups.has(`${lens.id}|${key}`);
  function openGroup(n) {
    const k = `${lens.id}|${n.group}`;
    if (n.close) st.groups.delete(k); else { st.groups.add(k); st.lastGroup = n.group; }
    draw({moved: true});
  }

  // the canvas size, kept by a ResizeObserver: reading it on every draw forced a layout per lens change
  let size = null;
  // off screen (scrolled away on a phone, behind a sheet) nothing of the graph runs (F8); a hidden tab is html[data-hidden]
  const sleepers = new Set();
  const sleep = (why, on) => { if (on) sleepers.add(why); else sleepers.delete(why); svg.classList.toggle("asleep", sleepers.size > 0); };
  if ("IntersectionObserver" in window) new IntersectionObserver(([e]) => sleep("off", !e.isIntersecting)).observe(host);
  // held (the dock's divider dragged): the SVG scales to its box as it is, and one layout follows the release — a
  // layout per frame of a drag was ~160 ms a frame on a dense graph (docs/brd/testing/panel_and_flows_report.md)
  let held = false, heldSize = false;
  new ResizeObserver(([e]) => { const r = e.contentRect; if (!r.width) return; /* hidden (a phone's sheet): keep the last size */ if (!size || r.width !== size.width || r.height !== size.height) { size = {width: r.width, height: r.height}; if (held) heldSize = true; else if (g && lens) draw(); } }).observe(host);
  function draw({moved = false} = {}) {
    if (!g) return;
    const box = size || host.getBoundingClientRect();
    // a phone's canvas is narrow and tall: the layout gets room in the height, the labels grow (CSS) to stay readable
    narrow = box.width > 0 && box.width < 600;
    W = Math.max(narrow ? 520 : 720, Math.round(box.width || 1000)); H = Math.max(narrow ? 640 : 520, Math.round(box.height || 640));
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    fxSvg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    pos = layout();
    ring = pos.ring;
    applyGroups(pos.groups, pos.fold);
    layoutRun++;
    routes = new Map(); obstacles = null;
    const lit = litSet();
    const back = [];  // nodes coming back into the lens: placed first, then one layout, then faded in together
    for (const n of g.nodes.concat(groupNodes)) {
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
    placeLabels(g.nodes.concat(groupNodes).filter(n => visible(n) && pos[n.id]));
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

  function litSet() {
    if (st.edge) return new Set(st.edge.split(">"));  // an edge picked (F9): its two ends
    return st.sel ? new Set([st.sel, ...links(st.sel).map(e => other(e, st.sel).id)]) : null;
  }
  // an edge is on when nothing is picked, it is the picked edge, or it joins the picked node to one of its links
  const isOn = (lit, f0, t0) => !lit || (st.edge ? `${f0}>${t0}` === st.edge : lit.has(f0) && lit.has(t0) && (f0 === st.sel || t0 === st.sel));

  // ── routing (OWN-GW-28, plan §2.6): one path per edge and layout, the first candidate clear of every other disc
  // (the centre with its aura) and every label. A spoke runs from the centre's rim to the node's inner side; a relation
  // leaves both nodes toward the centre (a node's relations share that first stretch: a trunk that splits) and bends
  // round the centre if it must, else follows the inside of the ring; a holding hangs off its class's outer side.
  let routes = new Map(), obstacles = null, ring = null;
  function obstaclesNow() {
    if (obstacles) return obstacles;
    const discs = [], boxes = [];
    for (const n of g.nodes.concat(groupNodes)) {
      const q = pos[n.id];
      if (!q || !visible(n)) continue;
      discs.push({id: n.id, x: q.x, y: q.y, r: n.kind === "family" ? ME_R + 12 : discR(n) + 3});
      if (q.label && !isKid(n) && n.kind !== "family" && !q.quiet) {
        const b = q.label.box;
        boxes.push({id: n.id, b: [b[0] + q.x - 2, b[1] + q.y - 2, b[2] + q.x + 2, b[3] + q.y + 2]});
      }
    }
    return (obstacles = {discs, boxes});
  }
  function hits(pts, ends) {
    const {discs, boxes} = obstaclesNow();
    let k = 0;
    for (const [x, y] of pts) {
      for (const d of discs) if (!ends.includes(d.id) && Math.hypot(x - d.x, y - d.y) < d.r) k++;
      for (const o of boxes) if (!ends.includes(o.id) && x > o.b[0] && x < o.b[2] && y > o.b[1] && y < o.b[3]) k++;
    }
    return k;
  }
  const bez = (ps) => {  // points every ~5 px along a quadratic or cubic Bézier
    const len = ps.slice(1).reduce((t, p, i) => t + Math.hypot(p[0] - ps[i][0], p[1] - ps[i][1]), 0), N = Math.max(6, Math.ceil(len / 5)), out = [];
    for (let i = 0; i <= N; i++) {
      const t = i / N, u = 1 - t;
      out.push(ps.length === 3
        ? [u * u * ps[0][0] + 2 * u * t * ps[1][0] + t * t * ps[2][0], u * u * ps[0][1] + 2 * u * t * ps[1][1] + t * t * ps[2][1]]
        : [u * u * u * ps[0][0] + 3 * u * u * t * ps[1][0] + 3 * u * t * t * ps[2][0] + t * t * t * ps[3][0],
          u * u * u * ps[0][1] + 3 * u * u * t * ps[1][1] + 3 * u * t * t * ps[2][1] + t * t * t * ps[3][1]]);
    }
    return out;
  };
  const xy = (p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`;
  function pick(cands, ends) {  // the first clear candidate, else the least crossed
    let best = null;
    for (const c of cands) {
      const k = hits(c.pts, ends);
      if (!k) return c;
      if (!best || k < best.k) best = {...c, k};
    }
    return best;
  }
  function route(e) {
    const key = `${e.from}>${e.to}`;
    if (routes.has(key)) return routes.get(key);
    const A = pos[e.from], B = pos[e.to], C = pos.ME, ends = [e.from, e.to];
    const unit = (dx, dy) => { const l = Math.hypot(dx, dy) || 1; return [dx / l, dy / l]; };
    let r;
    if (e.from === "ME" || e.to === "ME") {
      const id = e.from === "ME" ? e.to : e.from, N = pos[id], [ux, uy] = unit(N.x - C.x, N.y - C.y);
      const a = [C.x + ux * (ME_R + 2), C.y + uy * (ME_R + 2)], b = [N.x - ux * (discR(byId[id]) + 2), N.y - uy * (discR(byId[id]) + 2)];
      const len = Math.hypot(b[0] - a[0], b[1] - a[1]), m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
      const c = pick([0.07, -0.07, 0].map(k => { const q = [m[0] - uy * k * len, m[1] + ux * k * len]; return {q, pts: bez([a, q, b])}; }), ends);
      const [p0, p1] = e.from === "ME" ? [a, b] : [b, a];
      r = {d: `M${xy(p0)} Q${xy(c.q)} ${xy(p1)}`};
    } else if ((byId[e.to].kind === "holding" && byId[e.from].kind === "class") || (!!e.parent && [byId[e.from].kind, byId[e.to].kind].includes("category"))) {
      // a holding or category hangs off its parent's outer side (either way round: a category of money in flows into it)
      const [ux, uy] = unit(B.x - A.x, B.y - A.y), rA = discR(byId[e.from]) + 2, rB = discR(byId[e.to]) + 2;
      const a = [A.x + ux * rA, A.y + uy * rA], b = [B.x - ux * rB, B.y - uy * rB], m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
      const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const c = pick([0.1, -0.1, 0].map(k => { const q = [m[0] - uy * k * len, m[1] + ux * k * len]; return {q, pts: bez([a, q, b])}; }), ends);
      r = {d: `M${xy(a)} Q${xy(c.q)} ${xy(b)}`};
    } else {
      const rA = discR(byId[e.from]) + 2, rB = discR(byId[e.to]) + 2;
      const [ax, ay] = unit(C.x - A.x, C.y - A.y), [bx, by] = unit(C.x - B.x, C.y - B.y);
      const dA = Math.hypot(C.x - A.x, C.y - A.y), dB = Math.hypot(C.x - B.x, C.y - B.y);
      const kA = Math.max(28, Math.min(95, 0.32 * (dA - ME_R))), kB = Math.max(28, Math.min(95, 0.32 * (dB - ME_R)));
      const a = [A.x + ax * rA, A.y + ay * rA], b = [B.x + bx * rB, B.y + by * rB];
      const c1 = [A.x + ax * kA, A.y + ay * kA], c2 = [B.x + bx * kB, B.y + by * kB];
      const [px, py] = unit(-(B.y - A.y), B.x - A.x), side = ME_R + 34;
      const cands = [0, 1, -1].map(sg => {
        const q1 = [c1[0] + px * side * sg, c1[1] + py * side * sg], q2 = [c2[0] + px * side * sg, c2[1] + py * side * sg];
        return {d: `M${xy(a)} C${xy(q1)} ${xy(q2)} ${xy(b)}`, pts: bez([a, q1, q2, b])};
      });
      // inside the ring: the ring itself between the two, drawn in toward the centre (both ring nodes: their angle
      // on the ring is known), never outside it where the labels are
      // a sampled route trimmed at the discs starts at its first point outside them: begin and end it on the rims
      const onRim = (N, r, q) => { const [ux, uy] = unit(q[0] - N.x, q[1] - N.y); return [N.x + ux * r, N.y + uy * r]; };
      const rim = (pts) => (pts.length > 1 ? [onRim(A, rA, pts[0]), ...pts, onRim(B, rB, pts[pts.length - 1])] : pts);
      const inner = [];
      if (A.ring && B.ring && ring) {
        const ta = A.a * Math.PI / 180;
        let d0 = (B.a - A.a) * Math.PI / 180;
        d0 = ((d0 + 3 * Math.PI) % (2 * Math.PI)) - Math.PI;
        const depth = Math.min(80, (Math.min(ring.rx, ring.ry) - ME_R - 30) * 0.55) / Math.min(ring.rx, ring.ry);
        for (let i = 0; i <= 48; i++) {
          const t = i / 48, hump = Math.sin(Math.PI * Math.min(1, t / 0.2, (1 - t) / 0.2) / 2), at = ta + d0 * (t < 0.1 ? 0 : t > 0.9 ? 1 : (t - 0.1) / 0.8);
          const [ox, oy] = ringAt(at, ring.rx, ring.ry), f = 1 - depth * hump;
          inner.push([C.x + ox * f, C.y + oy * f]);
        }
      }
      const trimmed = rim(inner.filter(([x, y]) => Math.hypot(x - A.x, y - A.y) > rA && Math.hypot(x - B.x, y - B.y) > rB));
      if (trimmed.length > 1) cands.push({d: `M${xy(trimmed[0])} L${trimmed.slice(1).map(xy).join(" ")}`, pts: trimmed});
      // … and where the ring hugs the core (a phone), that dip still runs through the discs between: the same way round
      // at a fixed radius in the gap, just outside the core's rings (tried last)
      if (A.ring && B.ring && ring) {
        const rt = ME_R + 16 + Math.max(0, (Math.min(ring.rx, ring.ry) - ME_R - 46) * 0.3), ta = Math.atan2(A.y - C.y, A.x - C.x);
        let d1 = Math.atan2(B.y - C.y, B.x - C.x) - ta;
        d1 = ((d1 + 3 * Math.PI) % (2 * Math.PI)) - Math.PI;
        const tight = [];
        for (let i = 0; i <= 48; i++) {
          // straight in toward the centre first, then round: leaving a disc, it clears what sits beside it
          const t = i / 48, hump = Math.sin(Math.PI * Math.min(1, t / 0.2, (1 - t) / 0.2) / 2), at = ta + d1 * Math.min(1, Math.max(0, (t - 0.14) / 0.72));
          const P = t < 0.5 ? A : B, dP = Math.hypot(P.x - C.x, P.y - C.y), r = dP + (rt - dP) * hump;
          tight.push([C.x + Math.cos(at) * r, C.y + Math.sin(at) * r]);
        }
        const kept = rim(tight.filter(([x, y]) => Math.hypot(x - A.x, y - A.y) > rA && Math.hypot(x - B.x, y - B.y) > rB));
        if (kept.length > 1) cands.push({d: `M${xy(kept[0])} L${kept.slice(1).map(xy).join(" ")}`, pts: kept});
      }
      r = {d: pick(cands, ends).d};
    }
    routes.set(key, r);
    return r;
  }

  // ── edges (OWN-GW-16, 18): silk — a hairline whose width follows the value (Studio's data-flow wires); solid for
  // what is recorded, dashed for an estimate, dotted for a hypothesis; a knob where real money arrives (Studio's
  // bouton). A path the assistant reads glows (`hot`), or turns red if the read failed (`bad`).
  // Money in motion (Studio's data-flow spark, canvas.js dfComet; OWN-GW-41, UNIFIED_FLOWS_PLAN F7): every edge that
  // carries money (`dir` and an amount, from the server) runs sparks the way the money goes — income into “My Wealth”,
  // spending, repayments and goal savings out of it, a news or policy change into a class or out of it — and nothing
  // else does: a relation implies no transfer. How much a month sets how it moves: intensity i = √(monthly ÷ the
  // month's larger flow), 0.12…1 — sparks per beat 1…3, trail 5…16 px, speed 130…260 px/s, core 1.4…2.2 px, opacity
  // .6…1, so the smallest flow still reads. A one-off (a policy item, a scenario) has no monthly rate: its i is relative
  // to the largest of its kind, at most .5. A spark is a light core of its edge's own colour (the hue kept: in, out,
  // estimate, hypothesis, risk); an actual transfer's core carries a faint wider glow stroke under it, an estimate's is
  // dashed and unlit, a hypothesis's dots, only while it is active. No CSS filter: two drop-shadows per spark,
  // repainted every frame, were 61% of the graph's CPU (docs/brd/testing/panel_and_flows_report.md). At most 48 spark paths:
  // the weakest edges thin out first. Reduced motion stills them (tokens.css).
  const SPARK = [1, 2.5, 1.5, 2, 5];  // back to front: crackle, crackle, head (dash, gap)… — short, a bead of light
  const SPARK_LEN = SPARK.reduce((p, q) => p + q, 0);
  const DASHED = [2.2, 2.4, 2.2, 2.4, 2.8];  // an estimate: even dashes, no head
  const DOTS = [0.01, 3.6, 0.01, 3.6, 0.01];  // a hypothesis: round dots
  const BUDGET = 48;  // spark paths on screen, at most
  // The core's heartbeat (OWN-GW-22, plan §3.3): every money edge keeps one beat (or a half or third of it), so its
  // sparks reach “My Wealth” on the beat; where an edge meets the rim a port lights as a spark arrives or leaves, and
  // the main income's arrival sends a band of light across the core toward the money going out, whose sparks leave
  // just after. All CSS animations created in the same frame: one clock, no script per frame.
  const BEAT = 0.9;  // seconds
  const ACROSS = 0.36;  // the band's crossing: the out-flows leave this long after the income lands
  const mod = (x, m) => ((x % m) + m) % m;
  // the same wire walked the other way (M … Q|C|L …, as route() draws them)
  function reverseD(d) {
    const m = d.match(/^M(\S+) ([QCL])(.*)$/);
    if (!m) return d;
    const pts = [m[1], ...m[3].trim().split(/\s+/)];
    return `M${pts[pts.length - 1]} ${m[2]}${pts.slice(0, -1).reverse().join(" ")}`;
  }
  const pathLen = (d) => { const q = mk("path", {d}, edgeLayer); let l = 0; try { l = q.getTotalLength(); } catch (_) { l = 0; } q.remove(); return l; };
  // a spark plan for one edge: how many beads a beat, how fast, how long a trail, how bright
  function plan(d, i, cert, m) {
    const len = pathLen(d);
    if (len < 16) return null;  // a category hangs ~25 px off its flow: still room for a bead
    const k = 1 + Math.round(2 * i), speed = 130 + 130 * i;
    const base = cert === "hypothetical" ? DOTS : cert === "estimate" ? DASHED : SPARK;
    const scale = (5 + 11 * i) / SPARK_LEN, pattern = cert === "hypothetical" ? base : base.map(x => +(x * scale).toFixed(2));
    return {d, len, i, cert, k, speed, pattern, m, sl: pattern.reduce((p, q) => p + q, 0), width: +(1.4 + 0.8 * i).toFixed(2),
      opacity: (0.6 + 0.4 * i) * (cert === "estimate" ? 0.7 : cert === "hypothetical" ? 0.8 : 1)};
  }
  const lanes = (pl) => Math.max(1, Math.round(pl.len / pl.speed / (BEAT / pl.k)));
  function sparks(pl, key, tone, offset = 0) {
    const per = BEAT / pl.k, n = lanes(pl), dur = n * per;
    for (let j = 0; j < n; j++) {
      const delay = `${(mod(offset - dur * j / n, dur) - dur).toFixed(3)}s`;
      // an actual transfer: the glow first (under), then the core — the same dash, clock and delay, so they move as one
      for (const cls of pl.cert === "actual" ? ["wglow", "wspark"] : ["wspark"]) {
        const q = mk("path", {d: pl.d, class: `${cls} c-${pl.cert}`, "data-e": key, "data-m": Math.round(pl.m)}, sparkLayer);
        q.style.strokeDasharray = `${pl.pattern.join(" ")} ${pl.len + 40}`;
        q.style.setProperty("--a", pl.sl);
        q.style.setProperty("--b", -pl.len);
        q.style.setProperty("--tone", tone);
        q.style.setProperty("--so", pl.opacity.toFixed(2));
        q.style.setProperty("--sw", pl.width);
        q.style.animationDuration = `${dur.toFixed(3)}s`;
        q.style.animationDelay = delay;
      }
    }
    // when a spark's head reaches the end (it moves len + its pattern in dur), and when one leaves the start
    return {per, arr: mod(dur * pl.len / (pl.len + pl.sl) + offset, per), dep: mod(offset, per)};
  }
  // the budget: the weakest edges go to one bead a beat, then (estimates and hypotheses only) to none
  function budget(queue) {
    const total = () => queue.reduce((t, q) => t + (q.pl ? lanes(q.pl) : 0), 0);
    const weakest = [...queue].filter(q => q.pl).sort((x, y) => x.pl.i - y.pl.i);
    for (const q of weakest) { if (total() <= BUDGET) break; q.pl.k = 1; }
    for (const q of weakest) { if (total() <= BUDGET) break; if (q.pl.cert !== "actual") q.pl = null; }
  }
  // a port: a short arc of the rim at the edge's angle, lit on the beat of its sparks
  function port(host, angle, tone, per, at, key) {
    const R = ME_R + 1.5, a0 = angle - 0.2, a1 = angle + 0.2;
    const q = mk("path", {d: `M${(R * Math.cos(a0)).toFixed(1)},${(R * Math.sin(a0)).toFixed(1)} A${R},${R} 0 0 1 ${(R * Math.cos(a1)).toFixed(1)},${(R * Math.sin(a1)).toFixed(1)}`,
      class: "wport", "data-e": key}, host);
    q.style.setProperty("--tone", tone);
    q.style.animationDuration = `${per.toFixed(3)}s`;
    q.style.animationDelay = `${(at - per).toFixed(3)}s`;
    return q;
  }
  const pathState = new Map();  // non-centre node id → "hot" | "bad": its edges wear it
  let drawn = "";  // the edges on screen and the layout they were drawn for: an event that changes neither only restyles
  function drawEdges(lit) {
    const es = shownEdges(), sig = `${layoutRun}|${es.map(e => `${e.from}>${e.to}`).join(",")}`;
    if (sig === drawn) {
      for (const p of edgeLayer.querySelectorAll(".wedge")) {
        const [f0, t0] = p.dataset.e.split(">"), e = {from: f0, to: t0};
        const on = isOn(lit, f0, t0);
        const state = spoke(e) ? pathState.get(f0 === "ME" ? t0 : f0) || "" : hotEdges.get(p.dataset.e) || "";
        for (const [c, v] of [["on", on && !!lit], ["faint", !on], ["hot", state === "hot"], ["bad", state === "bad"], ["picked", p.dataset.e === st.edge]]) p.classList.toggle(c, v);
      }
      for (const h of edgeLayer.querySelectorAll(".whit")) h.setAttribute("aria-pressed", String(h.dataset.e === st.edge));
      for (const q of [...svg.querySelectorAll(".wport"), ...sparkLayer.querySelectorAll(".wspark, .wglow")]) {
        const [f0, t0] = q.dataset.e.split(">");
        q.classList.toggle("faint", !isOn(lit, f0, t0));
      }
      flowState();
      return;
    }
    drawn = sig;
    edgeLayer.replaceChildren();
    sparkLayer.replaceChildren();
    const meEl = els.get("ME"), ports = meEl && meEl.querySelector(".wme-ports"), bandHost = meEl && meEl.querySelector(".wme-bandhost");
    if (ports) ports.replaceChildren();
    if (bandHost) bandHost.replaceChildren();
    const maxV = Math.max(1, ...es.filter(e => e.value != null).map(e => Math.abs(e.value)));
    const income = (e) => e.to === "ME" && byId[e.from].kind === "flow";
    es.sort((x, y) => (income(y) ? Math.abs(y.value || 0) + 1 : 0) - (income(x) ? Math.abs(x.value || 0) + 1 : 0));
    let beat = null;  // the main income's arrival: the core's beat
    const C = pos.ME;
    const rimAngle = (id) => Math.atan2(pos[id].y - C.y, pos[id].x - C.x);
    // intensity from the monthly rate against the month's larger flow; a one-off relative to its kind, capped at .5
    const R = Math.max(1, ...["FL:in", "FL:out"].map(id => (byId[id] ? Math.abs(byId[id].value || 0) : 0)));
    const oneOff = {};
    const moves = (e, cert) => !!e.dir && e.value != null && (cert !== "hypothetical" || !!e.active);
    for (const e of es) { const c = certaintyOf(e, byId); if (moves(e, c) && e.monthly == null) oneOff[c] = Math.max(oneOff[c] || 1, Math.abs(e.value)); }
    const intensity = (e, cert) => e.monthly != null ? Math.min(1, Math.max(0.12, Math.sqrt(Math.abs(e.monthly) / R)))
      : Math.min(0.5, Math.max(0.12, Math.sqrt(Math.abs(e.value) / oneOff[cert])));
    const queue = [];  // the sparks to draw, planned first so the budget can thin them
    for (const e of es) {
      const a = pos[e.from], b = pos[e.to];
      if (!a || !b) continue;
      const on = isOn(lit, e.from, e.to);
      const cert = certaintyOf(e, byId);
      const far = byId[e.to].kind === "family" ? byId[e.from] : byId[e.to];
      const tone = (far.kind === "flow" || far.kind === "category") && far.side === "out" ? "var(--out)" : (LOOK[far.kind === "group" ? far.of : far.kind] || LOOK.class)[0];
      const state = spoke(e) ? pathState.get(e.from === "ME" ? e.to : e.from) || "" : hotEdges.get(`${e.from}>${e.to}`) || "";
      const money = cert === "actual" && !!e.dir;
      const d = route(e).d;
      const p = mk("path", {d, class: `wedge c-${cert}${money ? " money" : ""}${on && lit ? " on" : ""}${on ? "" : " faint"}${state ? " " + state : ""}${e.derived ? " sum" : ""}${st.edge === `${e.from}>${e.to}` ? " picked" : ""}`,
        "data-e": `${e.from}>${e.to}`, "stroke-width": (e.value == null ? 1 : 0.9 + 1.5 * Math.sqrt(Math.abs(e.value) / maxV)).toFixed(2)}, edgeLayer);
      p.style.setProperty("--tone", tone);
      const key = `${e.from}>${e.to}`;
      if (moves(e, cert)) {
        const way = e.dir === "back" ? reverseD(d) : d;  // the way the money goes
        if (money) {  // the receiving end: where the money lands (into “My Wealth”, or out to spending)
          const [x, y] = way.split(" ").pop().split(",").map(Number);
          mk("circle", {cx: x, cy: y, r: 3, class: "wknob"}, edgeLayer).style.setProperty("--tone", tone);
        }
        const outTone = cert !== "actual" && e.value < 0 ? "var(--out)" : tone;  // an estimated or supposed loss: money leaving
        queue.push({e, key, on, tone: outTone, pl: plan(way, intensity(e, cert), cert, Math.abs(e.monthly ?? e.value)), money, into: e.to === "ME" && e.dir !== "back", from: e.from === "ME" && e.dir !== "back"});
      }
      if (e.repaid && cert === "actual") {  // a debt paid down this month: money runs from “My Wealth” out to it, on the beat
        const i = Math.min(1, Math.max(0.12, Math.sqrt(Math.abs(e.repaid) / R)));
        queue.push({e, key, on, tone: "var(--out)", pl: plan(reverseD(d), i, "actual", Math.abs(e.repaid)), money: true, repaid: true});
      }
      const word = {actual: "thực tế", estimate: "ước tính", hypothetical: "giả định"}[cert];
      const sum = e.derived ? ` · tổng hợp từ ${e.derived} liên kết` : "";
      const paid = e.repaid ? `<br>trả trong tháng: ${vnd(e.repaid)}` : "";
      const rate = e.monthly != null && e.monthly !== Math.abs(e.value) ? ` · ~${vnd(e.monthly)}/tháng` : "";
      // a wide, invisible stroke over it (F9): a click or Enter picks the edge; Thông tin shows where it comes from
      const hit = mk("path", {d, class: "whit", "data-e": key, tabindex: "0", role: "button", "aria-pressed": String(st.edge === key),
        "aria-label": `Liên kết ${byId[e.from].label} → ${byId[e.to].label}: ${e.label}`}, edgeLayer);
      hit.addEventListener("click", () => selectEdge(key));
      hit.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); selectEdge(key); } });
      hover(hit, `${esc(byId[e.from].label)} → ${esc(byId[e.to].label)}<br>${esc(e.label)}${e.value == null ? "" : " · " + vnd(e.value, cert !== "actual")}${rate}${paid}<br><span class="muted">${word} · ${srcText(e)}${sum}</span>`);
    }
    budget(queue);
    for (const q of queue) {  // in order: the main income first, so the beat is set before the out-flows take it
      if (!q.pl) continue;
      const t = sparks(q.pl, q.key, q.tone, q.into || !q.money ? 0 : (beat ? beat.at + ACROSS : 0));
      if (q.money && q.into && !beat) beat = {at: t.arr, angle: rimAngle(q.e.from)};
      if (q.money && ports && (q.into || q.from)) port(ports, rimAngle(q.into ? q.e.from : q.e.to), q.tone, t.per, q.into ? t.arr : t.dep, q.key);
      if (q.repaid && ports) port(ports, rimAngle(q.e.from), "var(--out)", t.per, t.dep, q.key);
      if (!q.on) for (const x of sparkLayer.querySelectorAll(`[data-e="${q.key}"]`)) x.classList.add("faint");
      if (!q.on && ports) for (const x of ports.querySelectorAll(`.wport[data-e="${q.key}"]`)) x.classList.add("faint");
    }
    if (beat && bandHost) {  // light crossing the core from where the income lands, once a beat
      const turn = mk("g", {transform: `rotate(${(beat.angle * 180 / Math.PI).toFixed(1)})`}, bandHost);
      const band = mk("g", {class: "wme-band"}, turn);
      for (const [rx, o] of [[18, 0.22], [10, 0.38], [4, 0.6]]) mk("ellipse", {rx, ry: ME_R * 0.92, "fill-opacity": o}, band);
      band.style.setProperty("--from", `${ME_R}px`);
      band.style.setProperty("--to", `${-ME_R}px`);
      band.style.animationDuration = `${BEAT}s`;
      band.style.animationDelay = `${(beat.at - BEAT).toFixed(3)}s`;
    }
    flowState();
  }
  // a money edge or a flow node pointed at or picked: the core leans toward that flow (OWN-GW-24)
  function flowState() {
    const me = els.get("ME");
    if (!me) return;
    const f = [st.sel, hoverId].map(i => byId[i]).find(n => n && n.kind === "flow");
    me.classList.toggle("flow", !!f);
    if (f) me.style.setProperty("--flow-tone", f.side === "out" ? "var(--out)" : "var(--in)");
  }

  // ── pan and zoom: one transform on the world group, set by the person's hand only ─────────────────
  const view = () => st.view;
  const applyView = () => {
    const t = `translate(${view().x.toFixed(1)} ${view().y.toFixed(1)}) scale(${view().k.toFixed(3)})`;
    world.setAttribute("transform", t);
    fxWorld.setAttribute("transform", t);
    svg.classList.toggle("near", view().k >= 1.3);  // zoomed in: the holdings' names show
  };
  function zoom(f, cx = W / 2, cy = H / 2) {
    const v = view(), k = Math.min(2.6, Math.max(0.45, v.k * f));
    v.x = cx - (cx - v.x) * (k / v.k); v.y = cy - (cy - v.y) * (k / v.k); v.k = k;
    applyView();
  }
  function fit() { st.view = {x: 0, y: 0, k: 1}; applyView(); }
  // Tập trung (OWN-GW-30): the view fits the selection, its neighbours and their labels; the rest stays drawn, dimmed
  function focus() {
    if (!st.sel || !pos[st.sel]) return false;
    const ids = [st.sel, ...links(st.sel).map(e => other(e, st.sel).id)].filter(id => pos[id]);
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const id of ids) {
      const q = pos[id], r = discR(byId[id]) + 6, b = q.label && id !== "ME" ? q.label.box : [-r, -r, r, r];
      x0 = Math.min(x0, q.x - r, q.x + b[0]); y0 = Math.min(y0, q.y - r, q.y + b[1]);
      x1 = Math.max(x1, q.x + r, q.x + b[2]); y1 = Math.max(y1, q.y + r, q.y + b[3]);
    }
    const k = Math.max(1, Math.min(1.8, 0.88 * Math.min(W / (x1 - x0), H / (y1 - y0))));
    st.view = {x: W / 2 - k * (x0 + x1) / 2, y: H / 2 - k * (y0 + y1) / 2, k};
    applyView();
    return true;
  }
  const toSvg = (ev) => { const r = svg.getBoundingClientRect(); return [(ev.clientX - r.left) * W / r.width, (ev.clientY - r.top) * H / r.height]; };
  let drag = null;
  svg.addEventListener("pointerdown", (ev) => {
    if (ev.button !== 0 || ev.target.closest(".wnode, .whit")) return;
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
    if (drag && !drag.moved && !ev.target.closest(".wnode, .whit")) {  // a click on the background clears: the pick, then the answer's focus
      if (st.sel || st.edge) select(null);
      else if (svg.classList.contains("focusing") && !running.size) activity.reset();
    }
    drag = null;
  });
  svg.addEventListener("wheel", (ev) => { ev.preventDefault(); const [x, y] = toSvg(ev); zoom(ev.deltaY < 0 ? 1.12 : 1 / 1.12, x, y); }, {passive: false});
  svg.addEventListener("keydown", (ev) => {
    if (!ev.ctrlKey && !ev.metaKey && !ev.altKey && (ev.key === "f" || ev.key === "0")) {  // on the canvas or a node
      if (ev.key === "0") fit(); else if (!focus()) return;
      ev.preventDefault();
      return;
    }
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
    const before = g.nodes.filter(n => KID[n.kind] && opened(n.id)).map(n => n.id).join();
    st.sel = id && st.sel === id ? null : id;
    st.edge = null;
    const after = g.nodes.filter(n => KID[n.kind] && opened(n.id)).map(n => n.id).join();
    draw({moved: before !== after});  // a class opening or closing moves the nodes: the edges follow
    if (onSelect) onSelect(st.sel ? byId[st.sel] : null);
  }
  // an edge picked (F9): both its ends lit, its details in Thông tin; the same edge again, or a node, unpicks it
  function selectEdge(key) {
    const before = g.nodes.filter(n => KID[n.kind] && opened(n.id)).map(n => n.id).join();
    st.edge = st.edge === key ? null : key;
    st.sel = null;
    const after = g.nodes.filter(n => KID[n.kind] && opened(n.id)).map(n => n.id).join();
    draw({moved: before !== after});
    if (onSelect) onSelect(null);
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
  let comets = 0, writingTimer = 0, lastRipple = 0;
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
    if (n.kind === "scenario" && n.active) {  // its read pulses along its hypothetical edges, then home (F10)
      const via = scnShown().filter(e => e.from === id && byId[e.to] && visible(byId[e.to])).sort((x, y) => Math.abs(y.value) - Math.abs(x.value)).slice(0, 3);
      if (via.length) {
        for (const e of via) { hotEdges.set(`${e.from}>${e.to}`, "hot"); pathState.set(e.to, "hot"); }
        drawEdges(litSet());
        for (const e of via) comet(id, e.to, {hollow, then: () => comet(e.to, "ME", {hollow})});
        return;
      }
    }
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
      const known = [...new Set((ids || []).filter(x => byId[x]).map(shownAs))];
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
      const now = performance.now(), host = me.querySelector(".wme-ripples");
      if (host && !reduced() && !document.hidden && now - lastRipple > 350) {  // the answer streaming: a ripple from the rim
        lastRipple = now;
        const c = mk("circle", {r: ME_R + 2, class: "wme-ripple"}, host);
        const a = track(c.animate([{transform: "scale(1)", opacity: 0.75}, {transform: "scale(1.42)", opacity: 0}], {duration: 1100, easing: "cubic-bezier(.2,.6,.3,1)"}));
        a.finished.then(() => c.remove(), () => c.remove());
      }
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
        else for (const n of g.nodes) if (n.kind === s0 && !isKid(n)) out.add(n.id);
      }
      return [...out];
    },
  };

  return {
    svg,
    activity,
    sleep,
    /* new data for a client and scope: their own kept state; the same SVG */
    load(overview, key) {
      g = overview; byId = Object.fromEntries(g.nodes.map(n => [n.id, n]));
      derived = spokesFor(g);
      st = states[key] ||= {sel: null, open: new Set(), shut: new Set(), groups: new Set(), view: {x: 0, y: 0, k: 1}};
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
    hold(on) { held = on; if (!on && heldSize) { heldSize = false; if (g && lens) draw(); } },
    /* the active stress tests combined (POST /api/scenario/combine, F6): each scenario's own part on its node, and its
       hypothetical edges — to the classes it moves (by sign) and to the spending its yearly cost adds (÷ 12). Net
       worth never changes: the combined figure is the bar's, “nếu xảy ra”. null clears them. */
    scenarios(res) {
      if (!g) return;
      for (const n of g.nodes) if (n.kind === "scenario" && n.active) { n.active = false; n.value = null; n.part = null; }
      scn = res && res.scenarios && res.scenarios.length ? res : null;
      scnEdges = []; scnSpokes = new Map(); reach = new Set();
      for (const s of scn ? scn.scenarios : []) {
        const id = `SC:${s.id}`, n = byId[id];
        if (!n) continue;
        const costs = Object.values(s.costs || {}).reduce((t, x) => t + x, 0);
        Object.assign(n, {active: true, value: s.change - costs, part: s});
        reach.add(id);
        const src = [{type: "scenario", id: s.id}];
        const fan = Object.values(s.by_class || {}).filter(Boolean).length + scn.costs.filter(x => x.by === s.id).length;
        scnSpokes.set(id, {from: "ME", to: id, label: "nếu xảy ra", value: n.value, dir: n.value < 0 ? "fwd" : "back",
          certainty: "hypothetical", active: true, derived: fan, sources: src});
        for (const [c, v] of Object.entries(s.by_class || {})) {
          if (!byId[`CL:${c}`] || !v) continue;
          scnEdges.push({from: id, to: `CL:${c}`, label: "nếu xảy ra", value: v, dir: v > 0 ? "fwd" : "back", certainty: "hypothetical", active: true, sources: src});
          reach.add(`CL:${c}`);
        }
        for (const c of scn.costs.filter(x => x.by === s.id)) {
          if (!byId["FL:out"]) continue;
          scnEdges.push({from: id, to: "FL:out", label: `${c.label} (giả định)`, value: -c.amount, monthly: c.amount / 12, dir: "fwd",
            certainty: "hypothetical", active: true, sources: src, cost: c});
          reach.add("FL:out");
        }
      }
      draw({moved: true});
    },
    combined: () => scn,
    select, toggle, zoom, fit, focus,
    data: () => g,
    node: (id) => byId[id],
    selected: () => (st && st.sel ? byId[st.sel] : null),
    selectEdge,
    // the picked edge, as drawn (a folded item's edge is its group's): null when none, or when it left the lens
    selectedEdge: () => (st && st.edge ? shownEdges().find(e => `${e.from}>${e.to}` === st.edge) || null : null),
    isOpen: (id) => !!st && opened(id),
    links: (id) => links(id),
    other,
    visible: (id) => !!byId[id] && visible(byId[id]),
  };
}
