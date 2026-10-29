/* The trial page's charts over days (NEWS_CHARTS_PLAN): the news kept each day stacked by group (view A), and lines
   over the scoring days — precision and recall, the simulated VND by group (view B). One axis; a 2px surface gap
   between stacked fills; 4px rounded data-ends; 2px lines with 8px markers; a legend beside, never colour alone; a
   tooltip on every column and point (charts.js::hover). The tables under each chart are its table view. */
import {LOCALE, esc} from "../core/core.js";
import {hover} from "./charts.js";

const NS = "http://www.w3.org/2000/svg";
const R4 = 4;

function svg(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v);
  if (parent) parent.append(e);
  return e;
}
function niceStep(span) {
  const raw = span / 4, p = Math.pow(10, Math.floor(Math.log10(Math.max(raw, 1e-9)))), m = raw / p;
  return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p;
}
const roundTop = (x, y, w, h) => {
  const r = Math.min(R4, h, w / 2);
  return `M${x},${y + h} V${y + r} Q${x},${y} ${x + r},${y} H${x + w - r} Q${x + w},${y} ${x + w},${y + r} V${y + h} Z`;
};
export const dm = (d) => `${d.slice(8, 10)}/${d.slice(5, 7)}`;
const swatch = (c) => `<span class="sw" style="background:${c}"></span>`;

export function legend(items) {
  return `<div class="legend">${items.map(i => `<span><i style="background:${i.color}"></i>${esc(i.label)}</span>`).join("")}</div>`;
}

/* One column per day, its groups stacked from the baseline. days: [{day, values: {key: n}}], oldest first;
   cats: [{key, label, color}] in their fixed order. */
export function stack(days, cats, width) {
  const W = Math.max(280, Math.round(width || 600)), H = 190, L = 40, R = 8, T = 10, B = 26;
  const total = (d) => cats.reduce((s, c) => s + (d.values[c.key] || 0), 0);
  const step = niceStep(Math.max(...days.map(total), 1)), top = Math.ceil(Math.max(...days.map(total), 1) / step) * step;
  const y = (v) => H - B - (H - T - B) * v / top;
  const s = svg("svg", {viewBox: `0 0 ${W} ${H}`, class: "viz chart", role: "img",
    "aria-label": days.map(d => `${dm(d.day)}: ${total(d)} tin`).join(", ")});
  const grid = svg("g", {class: "grid"}, s);
  for (let v = step; v <= top + 1e-9; v += step) {
    svg("line", {x1: L, x2: W - R, y1: y(v), y2: y(v)}, grid);
    svg("text", {x: L - 6, y: y(v) + 4, "text-anchor": "end", class: "lbl"}, s).textContent = v.toLocaleString(LOCALE);
  }
  svg("line", {x1: L, x2: W - R, y1: y(0), y2: y(0), class: "base"}, s);
  const band = (W - L - R) / days.length, bw = Math.min(24, band * 0.62);
  const every = Math.max(1, Math.ceil(days.length / Math.floor((W - L - R) / 44)));
  days.forEach((d, i) => {
    const cx = L + band * i + band / 2, col = svg("g", {class: "col", tabindex: "0", "data-day": d.day}, s);
    svg("rect", {x: L + band * i, y: T, width: band, height: H - T - B, class: "colhover"}, col);
    const parts = cats.filter(c => d.values[c.key] > 0);
    let acc = 0;
    parts.forEach((c, k) => {
      const v = d.values[c.key], y0 = y(acc), y1 = y(acc + v), gap = acc ? 2 : 0;  // 2px surface gap between fills
      const h = Math.max(0, y0 - y1 - gap);
      if (h > 0) svg(k === parts.length - 1 ? "path" : "rect", k === parts.length - 1
        ? {d: roundTop(cx - bw / 2, y1, bw, h), fill: c.color}
        : {x: cx - bw / 2, y: y1, width: bw, height: h, fill: c.color}, col);
      acc += v;
    });
    if ((days.length - 1 - i) % every === 0) svg("text", {x: cx, y: H - 8, "text-anchor": "middle", class: "lbl"}, s).textContent = dm(d.day);
    hover(col, `<b>${dm(d.day)} · ${total(d).toLocaleString(LOCALE)} tin</b>${cats.map(c => `<div class="row"><span>${swatch(c.color)}${esc(c.label)}</span><span>${(d.values[c.key] || 0).toLocaleString(LOCALE)}</span></div>`).join("")}`);
  });
  return s;
}

/* A few series over the same days. series: [{label, color, values: [number | null]}] (null: nothing to plot that
   day); fmt(v) labels the axis and the tooltips; pct: the axis is 0–100 %, else it holds 0 and every value. */
export function lines(days, series, width, {fmt = String, pct = false, tip = () => ""} = {}) {
  const W = Math.max(280, Math.round(width || 600)), H = 200, L = 64, R = 16, T = 12, B = 26;
  const vals = series.flatMap(sr => sr.values).filter(v => v != null);
  let lo = 0, hi = 1, step = 0.25;
  if (!pct) {
    step = niceStep(Math.max(Math.max(...vals, 0) - Math.min(...vals, 0), 1));
    lo = Math.floor(Math.min(...vals, 0) / step) * step; hi = Math.ceil(Math.max(...vals, 0) / step) * step;
    if (hi === lo) hi = lo + step;
  }
  const x = (i) => L + (W - L - R) * (days.length > 1 ? i / (days.length - 1) : 0.5);
  const y = (v) => T + (H - T - B) * (hi - v) / (hi - lo);
  const s = svg("svg", {viewBox: `0 0 ${W} ${H}`, class: "viz chart", role: "img",
    "aria-label": series.map(sr => `${sr.label}: ${sr.values.map((v, i) => `${dm(days[i])} ${v == null ? "—" : fmt(v)}`).join(", ")}`).join("; ")});
  const grid = svg("g", {class: "grid"}, s);
  for (let v = lo; v <= hi + 1e-9; v += step) {
    if (Math.abs(v) > 1e-9) svg("line", {x1: L, x2: W - R, y1: y(v), y2: y(v)}, grid);
    svg("text", {x: L - 6, y: y(v) + 4, "text-anchor": "end", class: "lbl"}, s).textContent = fmt(v);
  }
  svg("line", {x1: L, x2: W - R, y1: y(0), y2: y(0), class: "base"}, s);
  const every = Math.max(1, Math.ceil(days.length / Math.floor((W - L - R) / 48)));
  days.forEach((d, i) => {
    if ((days.length - 1 - i) % every) return;
    svg("text", {x: x(i), y: H - 8, "text-anchor": days.length === 1 ? "middle" : i === 0 ? "start" : i === days.length - 1 ? "end" : "middle", class: "lbl"}, s).textContent = dm(d);
  });
  for (const sr of series) {
    const pts = sr.values.map((v, i) => (v == null ? null : [x(i), y(v)]));
    let run = [];
    for (const p of [...pts, null]) {  // a gap where a day has nothing, never a line through it
      if (p) { run.push(p); continue; }
      if (run.length > 1) svg("polyline", {points: run.map(q => q.join(",")).join(" "), fill: "none", stroke: sr.color, "stroke-width": 2, "stroke-linejoin": "round"}, s);
      run = [];
    }
  }
  days.forEach((d, i) => {  // one hit target per day: every series' value that day
    const g = svg("g", {class: "col", tabindex: "0", "data-day": d}, s);
    svg("rect", {x: x(i) - (W - L - R) / Math.max(days.length, 1) / 2, y: T, width: (W - L - R) / Math.max(days.length, 1), height: H - T - B, class: "colhover"}, g);
    series.forEach((sr, j) => {  // series on the same value draw as rings, the first the widest: none hides another
      const v = sr.values[i];
      if (v == null) return;
      const under = series.slice(j + 1).filter(o => o.values[i] != null && Math.abs(y(o.values[i]) - y(v)) < 3).length;
      svg("circle", {cx: x(i), cy: y(v), r: 4 + 3 * under, fill: sr.color, stroke: "var(--surface)", "stroke-width": 2}, g);
    });
    hover(g, `<b>${dm(d)}</b>${series.map(sr => `<div class="row"><span>${swatch(sr.color)}${esc(sr.label)}</span><span>${sr.values[i] == null ? "—" : fmt(sr.values[i])}</span></div>`).join("")}${tip(i)}`);
  });
  return s;
}
