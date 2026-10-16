/* The charts of the new pages: one tooltip, one legend model, thin marks, a 2px surface gap between
   fills, direct labels on the few marks that matter, a table view next to every chart. Colours come
   from the tokens (validated palette); a sign is gain/loss, a series is its slot, never its rank. */
import {esc, n, vnd, pct} from "../core/core.js";
import {iconPaths} from "../core/icons.js?v=20261016r1";
import {track} from "../motion.js?v=20261016r1";

const NS = "http://www.w3.org/2000/svg";
// BRD-NFR-11: an SVG number opens its “cách tính” like any other (core.explainOn reads these attributes)
function howOn(node, metric, inputs) {
  node.setAttribute("data-metric", metric);
  if (inputs) node.setAttribute("data-in", JSON.stringify(inputs));
  node.setAttribute("tabindex", "0");
  node.setAttribute("role", "button");
  node.classList.add("num-svg");
  return node;
}

function el(tag, attrs, parent) {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs || {})) if (v != null) n.setAttribute(k, v);
  if (parent) parent.appendChild(n);
  return n;
}

// ── tooltip ──────────────────────────────────────────────────────────────────
function tip() {
  let t = document.getElementById("tip");
  if (!t) { t = document.createElement("div"); t.id = "tip"; t.className = "tip"; t.hidden = true; document.body.appendChild(t); }
  return t;
}
export function hover(node, html) {
  const show = (e) => {
    const t = tip();
    t.innerHTML = typeof html === "function" ? html() : html;
    t.hidden = false;
    const x = (e.touches ? e.touches[0].clientX : e.clientX), y = (e.touches ? e.touches[0].clientY : e.clientY);
    const w = t.offsetWidth, h = t.offsetHeight;
    t.style.left = Math.min(window.innerWidth - w - 8, Math.max(8, x + 12)) + "px";
    t.style.top = Math.max(8, y - h - 12) + "px";
  };
  node.addEventListener("mousemove", show);
  node.addEventListener("mouseleave", () => { tip().hidden = true; });
  node.addEventListener("touchstart", show, {passive: true});
  node.addEventListener("focus", (e) => show({clientX: e.target.getBoundingClientRect().x, clientY: e.target.getBoundingClientRect().y}));
  node.addEventListener("blur", () => { tip().hidden = true; });
}

function niceStep(span) {
  const raw = span / 4;
  const p = Math.pow(10, Math.floor(Math.log10(Math.max(raw, 1e-9))));
  const m = raw / p;
  return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p;
}

// ── fan chart: the band of outcomes at 1 week / 3 months / 12 months ─────────
export function fan(box, horizons, opts = {}) {
  // horizons: [{key, label, expected, p5, p10, p50, p90}] in time order; "Hôm nay" (0) is drawn first
  const width = Math.max(280, box.clientWidth || 600), height = opts.height || 230;
  const narrow = width < 520;
  const pad = {l: narrow ? 54 : 64, r: narrow ? 78 : 112, t: 14, b: 28};
  const short = (v) => (narrow ? vnd(v, true).replace(" triệu", " tr") : vnd(v, true));
  const pts = [{label: "Hôm nay", expected: 0, p5: 0, p10: 0, p50: 0, p90: 0}, ...horizons];
  let lo = Math.min(...pts.map(p => p.p5)), hi = Math.max(...pts.map(p => p.p90));
  if (lo === hi) { lo -= 1; hi += 1; }
  const step = niceStep(hi - lo);
  lo = Math.floor(lo / step) * step; hi = Math.ceil(hi / step) * step;
  const x = (i) => pad.l + (i * (width - pad.l - pad.r)) / (pts.length - 1);
  const y = (v) => pad.t + ((hi - v) * (height - pad.t - pad.b)) / (hi - lo);
  const svg = el("svg", {class: "viz", viewBox: `0 0 ${width} ${height}`, role: "img",
    "aria-label": opts.label || "Dải tác động theo kỳ hạn"});
  const grid = el("g", {class: "grid"}, svg);
  for (let v = lo; v <= hi + step / 2; v += step) {
    el("line", {x1: pad.l, x2: width - pad.r, y1: y(v), y2: y(v), class: Math.abs(v) < step / 2 ? "zero" : null,
      stroke: Math.abs(v) < step / 2 ? "var(--axis)" : null}, grid);
    el("text", {x: pad.l - 8, y: y(v) + 4, "text-anchor": "end", "data-axis": ""}, svg).textContent = vnd(v, true);
  }
  pts.forEach((p, i) => { el("text", {x: x(i), y: height - 8, "text-anchor": "middle"}, svg).textContent = p.label; });
  const path = (key) => pts.map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p[key])}`).join("");
  const area = pts.map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p.p90)}`).join("") +
    [...pts].reverse().map((p, j) => `L${x(pts.length - 1 - j)},${y(p.p10)}`).join("") + "Z";
  el("path", {d: area, fill: "var(--band-2)", stroke: "none"}, svg);
  el("path", {d: path("p5"), fill: "none", stroke: "var(--down)", "stroke-width": 1.5, "stroke-dasharray": "4 4"}, svg);
  el("path", {d: path("expected"), fill: "none", stroke: "var(--accent)", "stroke-width": 2.5, "stroke-linejoin": "round"}, svg);
  const last = pts[pts.length - 1], lx = x(pts.length - 1) + 8;
  const labels = [["P90", last.p90, "var(--ink-2)"], [narrow ? "KV" : "Kỳ vọng", last.expected, "var(--accent)"], ["P10", last.p10, "var(--ink-2)"], ["P5", last.p5, "var(--down)"]];
  // keep the direct labels apart
  const ys = labels.map(l => y(l[1]));
  for (let i = 1; i < ys.length; i++) if (ys[i] - ys[i - 1] < 13) ys[i] = ys[i - 1] + 13;
  const direct = [];
  labels.forEach((l, i) => {
    const t = el("text", {x: lx, y: ys[i] + 4, class: "lbl"}, svg);
    direct.push(t);
    t.textContent = `${l[0]} ${short(l[1])}`;
    t.style.fill = l[2];
    howOn(t, opts.metric || "impact.band", {...(opts.inputs || {}), stat: l[0], horizon: last.label});
  });
  pts.forEach((p, i) => {
    if (!i) return;
    el("circle", {cx: x(i), cy: y(p.expected), r: 4, fill: "var(--accent)", stroke: "var(--surface)", "stroke-width": 2}, svg);
    const hit = el("rect", {x: x(i) - 28, y: pad.t, width: 56, height: height - pad.t - pad.b, fill: "transparent", tabindex: 0}, svg);
    hover(hit, `<b>${esc(p.label)}</b><br>Kỳ vọng ${vnd(p.expected, true)}<br>P90 ${vnd(p.p90, true)} · P50 ${vnd(p.p50, true)}<br>P10 ${vnd(p.p10, true)} · P5 ${vnd(p.p5, true)}`);
  });
  for (const t of direct) svg.appendChild(t);  // above the hover strips
  box.innerHTML = "";
  box.appendChild(svg);
  const legend = document.createElement("div");
  legend.className = "legend";
  legend.innerHTML = `<span><i style="background:var(--accent)"></i>Kỳ vọng${narrow ? " (KV)" : ""}</span><span><i style="background:var(--band-2)"></i>P10–P90 (8/10 khả năng)</span><span><i class="dash"></i>P5 (rất xấu, tham khảo)</span>`;
  box.appendChild(legend);
}

// ── diverging bars: contributions that add up to a total ─────────────────────
export function diverging(box, rows, opts = {}) {
  // rows: [{label, value, color?, title?}] — sorted by |value| here
  const data = rows.filter(r => r.value).sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).slice(0, opts.max || 8);
  if (!data.length) { box.innerHTML = `<div class="small muted">Không có đóng góp khác 0.</div>`; return; }
  const width = Math.max(280, box.clientWidth || 520), row = 30, labelW = Math.min(150, width * 0.34), valW = 88;
  const height = data.length * row + 6;
  const maxAbs = Math.max(...data.map(r => Math.abs(r.value)));
  const span = width - labelW - valW;
  const hasNeg = data.some(r => r.value < 0), hasPos = data.some(r => r.value > 0);
  const zero = labelW + (hasNeg && hasPos ? span / 2 : hasNeg ? span : 0);
  const scale = (hasNeg && hasPos ? span / 2 : span) / maxAbs;
  const svg = el("svg", {class: "viz", viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": opts.label || "Đóng góp"});
  el("line", {x1: zero, x2: zero, y1: 0, y2: height, stroke: "var(--axis)"}, svg);
  data.forEach((r, i) => {
    const yy = i * row + 4, w = Math.max(2, Math.abs(r.value) * scale), xx = r.value < 0 ? zero - w : zero;
    const lab = el("text", {x: 0, y: yy + 16, class: "lbl"}, svg);
    lab.textContent = r.label.length > 22 ? r.label.slice(0, 21) + "…" : r.label;
    el("rect", {x: xx + (r.value < 0 ? 0 : 1), y: yy + 4, width: Math.max(1, w - 1), height: 18, rx: 4,
      fill: r.color || (r.value < 0 ? "var(--down)" : "var(--up)"), opacity: r.color ? 1 : 0.85}, svg);
    const v = el("text", {x: width, y: yy + 17, "text-anchor": "end", class: "val"}, svg);
    v.textContent = vnd(r.value, true);
    howOn(v, opts.metric || "impact.by_class", {...(opts.inputs || {}), part: r.label});
    const hit = el("rect", {x: 0, y: yy, width, height: row, fill: "transparent", tabindex: 0}, svg);
    hover(hit, `<b>${esc(r.label)}</b><br>${vnd(r.value, true)}${r.title ? "<br>" + esc(r.title) : ""}`);
    svg.appendChild(v);  // above the hover strip, so the value itself opens its “cách tính”
  });
  box.innerHTML = "";
  box.appendChild(svg);
}

// ── stacked probability bar: the scenario branches ───────────────────────────
const SLOTS = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s7)"];
export function probBar(box, branches) {
  const total = branches.reduce((s, b) => s + b.probability, 0) || 1;
  box.innerHTML = `<div style="display:flex;gap:2px;height:26px;border-radius:8px;overflow:hidden">${branches.map((b, i) =>
    `<div tabindex="0" data-i="${i}" style="flex:${b.probability / total};background:${SLOTS[i % 4]};min-width:4px;display:grid;place-items:center;color:#fff;font-size:12px;font-weight:700">${b.probability / total >= 0.12 ? n(pct(b.probability / total, false, 0), "scenario.probability") : ""}</div>`).join("")}</div>
    <div class="legend">${branches.map((b, i) => `<span><i style="background:${SLOTS[i % 4]}"></i>${esc(b.name)} ${n(pct(b.probability / total, false, 0), "scenario.probability")}${b.regime === "stressed" ? " · căng thẳng" : ""}</span>`).join("")}</div>`;
  box.querySelectorAll("[data-i]").forEach((n) => {
    const b = branches[+n.dataset.i];
    hover(n, `<b>${esc(b.name)}</b> · ${pct(b.probability / total, false, 0)}<br>${b.regime === "stressed" ? "Chế độ căng thẳng" : "Chế độ bình thường"}`);
  });
}
export const slot = (i) => SLOTS[i % 4];

// ── heat map: families × factors ─────────────────────────────────────────────
export function heat(box, cols, rows, opts = {}) {
  // rows: [{label, values: {col: number}, title?}], values as shares (−0.02 = −2 %)
  const maxAbs = Math.max(1e-9, ...rows.flatMap(r => cols.map(c => Math.abs(r.values[c] || 0))));
  // opts.metric: the cells' “cách tính” (opts.inputs(row, col) its inputs)
  const cell = (v, r, c) => {
    if (!v) return `<td class="cell muted">·</td>`;
    const a = Math.min(1, Math.abs(v) / maxAbs);
    const color = v < 0 ? "var(--down)" : "var(--up)";
    const text = opts.metric ? n(pct(v, true, 1), opts.metric, opts.inputs ? opts.inputs(r, c) : null) : pct(v, true, 1);
    return `<td class="cell" style="background:color-mix(in srgb, ${color} ${Math.round(8 + a * 52)}%, transparent)" title="${esc(pct(v, true, 2))}">${text}</td>`;
  };
  box.innerHTML = `<div class="scrollx"><table class="table heat"><thead><tr><th>${esc(opts.corner || "")}</th>${cols.map(c => `<th class="r" title="${esc(opts.colTitle ? opts.colTitle(c) : c)}">${esc(opts.colLabel ? opts.colLabel(c) : c)}</th>`).join("")}</tr></thead>
    <tbody>${rows.map(r => `<tr><td>${esc(r.label)}</td>${cols.map(c => cell(r.values[c], r, c)).join("")}</tr>`).join("")}</tbody></table></div>`;
}

// ── sparkline: items per hour ────────────────────────────────────────────────
export function spark(values, w = 96, h = 22) {
  const max = Math.max(1, ...values);
  const pts = values.map((v, i) => `${(i * (w - 2)) / Math.max(1, values.length - 1) + 1},${h - 2 - (v / max) * (h - 4)}`).join(" ");
  return `<svg class="viz" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="Số tin mỗi giờ, 24 giờ qua"><polyline points="${pts}" fill="none" stroke="var(--accent)" stroke-width="1.5"/></svg>`;
}

// ── factor moves of a branch, as a share of one month's usual move ───────────
export function moves(box, rows, opts = {}) {
  // rows: [{name, text, z, core}] — z = move / monthly volatility (comparable across units); opts.metric, opts.inputs
  const max = Math.max(1, ...rows.map(r => Math.abs(r.z)));
  box.innerHTML = rows.map(r => {
    const w = Math.round((Math.abs(r.z) / max) * 50);
    return `<div style="display:grid;grid-template-columns:minmax(0,1.3fr) 1fr 72px;gap:8px;align-items:center;font-size:12.5px;padding:2px 0">
      <span>${r.core ? "<b>" : ""}${esc(r.name)}${r.core ? "</b> <span class='badge human'>lõi</span>" : ""}</span>
      <span style="position:relative;height:12px;background:var(--surface-2);border-radius:6px">
        <span style="position:absolute;top:0;bottom:0;${r.z < 0 ? `right:50%` : `left:50%`};width:${w}%;background:${r.z < 0 ? "var(--down)" : "var(--up)"};border-radius:6px"></span>
        <span style="position:absolute;left:50%;top:-2px;bottom:-2px;width:1px;background:var(--axis)"></span></span>
      <span class="num" style="text-align:right">${opts.metric ? n(esc(r.text), opts.metric, opts.inputs) : esc(r.text)}</span></div>`;
  }).join("");
}

// ── sankey: a month's money in → the month → out (Money Flow, kit K2; board look R2) ─────────────
// A fixed colour per category (colour follows the entity, never its rank); bands fade from their node's colour
// toward the month; icon chips beside the labels on wide screens. Picking a band highlights it and sends three
// dots along it three times (transform only, paused with the tab, none under reduced motion), then stops.
const IN_COLOR = {salary: "var(--s1)", pension: "var(--s7)", rent: "var(--s6)", _short: "var(--down)"};
const OUT_COLOR = {living: "var(--s2)", card: "var(--s4)", loan: "var(--s8)", school: "var(--s7)", health: "var(--s5)",
  rent_out: "var(--s1)", _left: "var(--s3)"};
export function sankey(box, f, opts = {}) {
  // f: the /api/flows answer; both sides balance: a surplus is a “Còn lại” band out, a shortfall a
  // “Thiếu hụt” band in. Every band and node is focusable and opens its rows.
  const short = f.left < 0 ? [{category: "_short", label: "Thiếu hụt (từ tiền tích lũy)", amount: -f.left}] : [];
  const left = [...f.inflow, ...short].map(b => ({...b, color: IN_COLOR[b.category] || "var(--other)"}));
  const right = [...f.outflow, ...(f.left > 0 ? [{category: "_left", label: "Còn lại", amount: f.left}] : [])]
    .map(b => ({...b, color: OUT_COLOR[b.category] || "var(--other)"}));
  const total = Math.max(f.total_in, f.total_out);
  if (!total) { box.innerHTML = `<div class="small muted">Không có giao dịch trong tháng này.</div>`; return; }
  const width = Math.max(300, box.clientWidth || 640), narrow = width < 560;
  const lw = narrow ? 92 : 190, nodeW = 10, gap = 12, icons = !narrow && opts.icons !== false;
  const n = Math.max(left.length, right.length);
  const height = opts.height || Math.max(210, n * (narrow ? 46 : 44));
  const scale = (height - 8 - gap * (n - 1)) / total;
  const x0 = lw, xm = width / 2 - nodeW / 2, x1 = width - lw - nodeW;
  const svg = el("svg", {class: "viz sankey", viewBox: `0 0 ${width} ${height}`, role: "img",
    "aria-label": opts.label || "Dòng tiền trong tháng: tiền vào theo nhóm, tiền ra theo nhóm"});
  const defs = el("defs", {}, svg);
  const place = (nodes) => {
    const used = nodes.reduce((a, b) => a + b.amount * scale, 0) + gap * (nodes.length - 1);
    let y = (height - used) / 2;
    for (const b of nodes) { b.y = y; b.h = Math.max(2, b.amount * scale); y += b.h + gap; }
  };
  place(left); place(right);
  const mh = total * scale, my = (height - mh) / 2;
  const fmt = (v) => (narrow ? vnd(v).replace(" triệu", " tr") : vnd(v));
  const curve = (xa, ya, xb, yb, h) => {
    const c = (xa + xb) / 2;
    return `M${xa},${ya}C${c},${ya} ${c},${yb} ${xb},${yb}L${xb},${yb + h}C${c},${yb + h} ${c},${ya + h} ${xa},${ya + h}Z`;
  };
  const centre = (xa, ya, xb, yb, h) => {  // the band's middle line, sampled for the flow dots
    const c = (xa + xb) / 2, a = ya + h / 2, z = yb + h / 2, out = [];
    for (let i = 0; i <= 16; i++) {
      const t = i / 16, u = 1 - t;
      out.push([u * u * u * xa + 3 * u * u * t * c + 3 * u * t * t * c + t * t * t * xb, u * u * u * a + 3 * u * u * t * a + 3 * u * t * t * z + t * t * t * z]);
    }
    return out;
  };
  const bands = el("g", {}, svg), dots = el("g", {class: "flowdots"}, svg);
  let gid = 0;
  const grad = (color, side) => {  // one hue per band, strongest at its own node
    const id = `sk${Math.random().toString(36).slice(2, 7)}${gid++}`;
    const g = el("linearGradient", {id, x1: 0, x2: 1, y1: 0, y2: 0}, defs);
    el("stop", {offset: 0, "stop-color": color, "stop-opacity": side === "in" ? 0.5 : 0.16}, g);
    el("stop", {offset: 1, "stop-color": color, "stop-opacity": side === "in" ? 0.16 : 0.5}, g);
    return `url(#${id})`;
  };
  const flow = (pts, color) => {
    dots.innerHTML = "";
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const frames = pts.map(([x, y]) => ({transform: `translate(${x}px, ${y}px)`}));
    for (let i = 0; i < 3; i++) {
      const d = el("circle", {r: 3.2, cx: 0, cy: 0, fill: color, stroke: "var(--surface)", "stroke-width": 1.5}, dots);
      track(d.animate(frames, {duration: 1800, delay: i * 600, iterations: 3, easing: "linear", fill: "backwards"}))
        .finished.then(() => d.remove(), () => d.remove());
    }
  };
  const band = (d, b, side, pts) => {
    const p = el("path", {d, fill: grad(b.color, side), tabindex: 0,
      role: "button", class: "band", "data-focus": `flow:${f.month}:${side}:${b.category}`,
      "aria-label": `${b.label}: ${vnd(b.amount)}`}, bands);
    p.style.setProperty("--c", b.color);
    hover(p, `<b>${esc(b.label)}</b><br>${vnd(b.amount)} · ${pct(b.amount / total)}${b.rows ? `<br>${b.rows.length} giao dịch` : ""}`);
    const pick = () => {
      for (const q of bands.querySelectorAll(".band")) q.classList.toggle("on", q === p);
      svg.classList.add("picked");
      flow(pts, b.color);
      opts.onPick && opts.onPick(b, side);
    };
    p.addEventListener("click", pick);
    p.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(); } });
  };
  let at = my;
  for (const b of left) { band(curve(x0 + nodeW, b.y, xm, at, b.h), b, "in", centre(x0 + nodeW, b.y, xm, at, b.h)); at += b.h; }
  at = my;
  for (const b of right) { band(curve(xm + nodeW, at, x1, b.y, b.h), b, "out", centre(xm + nodeW, at, x1, b.y, b.h)); at += b.h; }
  const chip = (x, y, b, side) => {
    const name = (side === "in" ? {salary: "salary", pension: "pension", rent: "rent", _short: "alert"}
      : {living: "cart", card: "card", loan: "loan", school: "school", health: "health", rent_out: "rent", _left: "savings"})[b.category] || "wallet";
    el("rect", {x, y: y - 11, width: 22, height: 22, rx: 6, fill: b.color, "fill-opacity": 0.14}, svg);
    const ic = el("svg", {x: x + 4, y: y - 7, width: 14, height: 14, viewBox: "0 0 24 24", fill: "none", stroke: b.color,
      "stroke-width": 2.2, "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true"}, svg);
    ic.innerHTML = iconPaths(name);
  };
  const label = (x, y, anchor, b) => {
    const t = el("text", {x, y, "text-anchor": anchor, class: "lbl"}, svg);
    const max = narrow ? 12 : 22;
    t.textContent = b.label.length > max ? b.label.slice(0, max - 1) + "…" : b.label;
    const v = el("text", {x, y: y + 15, "text-anchor": anchor, class: "val"}, svg);
    v.textContent = fmt(b.amount);
    howOn(v, b.rows ? "flow.band" : "flow.left", b.rows ? {rows: String(b.rows.length)} : {total_in: vnd(f.total_in), total_out: vnd(f.total_out)});
  };
  for (const b of left) {
    el("rect", {x: x0, y: b.y, width: nodeW, height: b.h, rx: 4, fill: b.color}, svg);
    const cy = b.y + b.h / 2;
    if (icons) chip(x0 - 30, cy, b, "in");
    label(x0 - (icons ? 38 : 8), cy - 2, "end", b);
  }
  for (const b of right) {
    el("rect", {x: x1, y: b.y, width: nodeW, height: b.h, rx: 4, fill: b.color}, svg);
    const cy = b.y + b.h / 2;
    if (icons) chip(x1 + nodeW + 8, cy, b, "out");
    label(x1 + nodeW + (icons ? 38 : 8), cy - 2, "start", b);
  }
  el("rect", {x: xm, y: my, width: nodeW, height: mh, rx: 4, fill: "var(--axis)"}, svg);
  box.innerHTML = "";
  box.appendChild(svg);
  const legend = document.createElement("div");
  legend.className = "legend";
  legend.innerHTML = `<span>← Tiền vào theo nguồn</span><span>Tháng ${esc(f.month.slice(5))}/${esc(f.month.slice(0, 4))}</span><span>Tiền ra theo nhóm${f.left > 0 ? " và phần còn lại" : ""} →</span>`;
  box.appendChild(legend);
}
