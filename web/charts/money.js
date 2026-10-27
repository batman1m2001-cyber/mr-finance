/* Charts of the rebuilt pages (UI redesign R3), ported from the pre-redesign web/charts.js (deleted in R3): the cash-flow columns
   (what happened solid, the forecast lighter, a “Hôm nay” line, ⚠ on a month with a large payment), month
   columns, lines over dates (0–100) and a sparkline. SVG drawn at the width it is shown at; one axis; a tooltip
   on every mark (charts.js::hover). */
import {DECIMAL, esc, vnd} from "../core/core.js";
import {hover} from "./charts.js";

const NS = "http://www.w3.org/2000/svg";
export const FORECAST_OPACITY = 0.42;
export const monthName = (ym) => "T" + Number(ym.slice(5, 7)) + "/" + ym.slice(2, 4);

function svg(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v);
  if (parent) parent.append(e);
  return e;
}
function niceMax(v) {
  if (v <= 0) return 1;
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  for (const k of [1, 2, 2.5, 5, 10]) if (k * p >= v) return k * p;
  return 10 * p;
}
const R4 = 4;
const roundTop = (x, y, w, h) => {
  const r = Math.min(R4, h, w / 2);
  return `M${x},${y + h} V${y + r} Q${x},${y} ${x + r},${y} H${x + w - r} Q${x + w},${y} ${x + w},${y + r} V${y + h} Z`;
};
const roundBottom = (x, y, w, h) => {
  const r = Math.min(R4, h, w / 2);
  return `M${x},${y} V${y + h - r} Q${x},${y + h} ${x + r},${y + h} H${x + w - r} Q${x + w},${y + h} ${x + w},${y + h - r} V${y} Z`;
};

/* Money in above the line, out below it, one column pair per month. months: [{month, in, out, net, items, phase}]
   with phase "past" (solid) or "now" / "next" (forecast, lighter); large: [{month}] marked ⚠. */
export function cashflow(months, large, width) {
  const W = Math.max(300, Math.round(width || 760)), H = W < 520 ? 220 : 260, L = 64, R = 8, T = 14, B = 30;
  const maxIn = Math.max(...months.map(m => m.in), 0), maxOut = Math.max(...months.map(m => m.out), 0);
  const step = niceMax(Math.max(maxIn, maxOut, 1)) / 2;
  const top = Math.max(step, Math.ceil(maxIn / step) * step);
  const bot = maxOut > 0 ? Math.ceil(maxOut / step) * step : 0;
  const span = top + bot, zero = T + (H - T - B) * (top / span);
  const y = (v) => zero - (H - T - B) * (v / span);
  const s = svg("svg", {viewBox: `0 0 ${W} ${H}`, class: "viz chart", role: "img",
    "aria-label": `Dòng tiền ${months.length} tháng: vào ${vnd(months.reduce((a, m) => a + m.in, 0))}, ra ${vnd(months.reduce((a, m) => a + m.out, 0))}`});
  const grid = svg("g", {class: "grid"}, s);
  const ticks = [];
  for (let v = top; v > 0; v -= step) ticks.push(v);
  for (let v = -step; v >= -bot; v -= step) ticks.push(v);
  for (const v of ticks) {
    svg("line", {x1: L, x2: W - R, y1: y(v), y2: y(v)}, grid);
    svg("text", {x: L - 8, y: y(v) + 4, "text-anchor": "end", class: "lbl", "data-axis": ""}, s).textContent = (v > 0 ? "+" : "−") + vnd(Math.abs(v));
  }
  svg("line", {x1: L, x2: W - R, y1: zero, y2: zero, class: "base"}, s);
  const n = months.length, band = (W - L - R) / n, bw = Math.min(22, band * 0.6);
  const big = new Set((large || []).map(l => l.month));
  const today = months.findIndex(m => m.phase && m.phase !== "past");
  if (today > 0) {
    const xx = L + band * today;
    svg("line", {x1: xx, x2: xx, y1: T - 4, y2: H - B, class: "today"}, s);
    svg("text", {x: xx + 4, y: T + 6, "text-anchor": "start", class: "lbl todaytext"}, s).textContent = "Hôm nay · dự báo →";
  }
  const every = Math.max(1, Math.ceil(n / Math.max(4, Math.floor((W - L - R) / 52))));
  months.forEach((m, i) => {
    const cx = L + band * i + band / 2, fc = !!m.phase && m.phase !== "past";
    const col = svg("g", {class: "col", tabindex: "0"}, s);
    svg("rect", {x: L + band * i, y: T, width: band, height: H - T - B, class: "colhover"}, col);
    if (m.in > 0) svg("path", {d: roundTop(cx - bw / 2, y(m.in), bw, zero - y(m.in)), fill: "var(--in)", "fill-opacity": fc ? FORECAST_OPACITY : 1}, col);
    if (m.out > 0) svg("path", {d: roundBottom(cx - bw / 2, zero, bw, y(-m.out) - zero), fill: "var(--out)", "fill-opacity": fc ? FORECAST_OPACITY : 1}, col);
    if (big.has(m.month)) svg("text", {x: cx, y: y(-m.out) + 14, "text-anchor": "middle", class: "warnmark"}, col).textContent = "⚠";
    if (i % every === 0) svg("text", {x: cx, y: H - 12, "text-anchor": "middle", class: "lbl"}, s).textContent = monthName(m.month);
    hover(col, () => {
      const items = m.items.slice(0, 8).map(it => `<div class="row"><span>${it.direction === "in" ? "▲" : "▼"} ${esc(it.label)}</span><span>${vnd(it.amount)}</span></div>`).join("");
      const more = m.items.length > 8 ? `<div class="muted">… và ${m.items.length - 8} khoản khác</div>` : "";
      const what = m.phase === "past" ? "thực tế" : m.phase === "now" ? "tháng này · dự báo" : m.phase ? "dự báo" : "";
      return `<b>${monthName(m.month)}${what ? " · " + what : ""} · ròng ${vnd(m.net, true)}</b><div class="row"><span>Vào</span><span>${vnd(m.in)}</span></div><div class="row"><span>Ra</span><span>${vnd(m.out)}</span></div>${items ? `<hr>${items}${more}` : ""}`;
    });
  });
  return s;
}

/* What happened (solid), this month and the forecast (lighter): one series for cashflow(). */
export function cashSeries(cf, past, ahead) {
  return [...(cf.history || []).slice(-past).map(m => ({...m, phase: "past"})),
    ...(cf.current ? [{...cf.current, phase: "now"}] : []),
    ...cf.months.slice(0, ahead).map(m => ({...m, phase: "next"}))];
}

/* One column per month (e.g. minutes read per week). */
export function columns(months, values, width, unit, color = "var(--s1)") {
  const W = Math.max(280, Math.round(width || 600)), H = 180, L = 40, R = 8, T = 10, B = 26;
  const top = niceMax(Math.max(...values, 1));
  const y = (v) => H - B - (H - T - B) * v / top;
  const s = svg("svg", {viewBox: `0 0 ${W} ${H}`, class: "viz chart", role: "img", "aria-label": months.map((m, i) => `${monthName(m)} ${values[i]} ${unit}`).join(", ")});
  const grid = svg("g", {class: "grid"}, s);
  for (const v of [top / 2, top]) {
    svg("line", {x1: L, x2: W - R, y1: y(v), y2: y(v)}, grid);
    svg("text", {x: L - 6, y: y(v) + 4, "text-anchor": "end", class: "lbl"}, s).textContent = String(v);
  }
  svg("line", {x1: L, x2: W - R, y1: y(0), y2: y(0), class: "base"}, s);
  const band = (W - L - R) / months.length, bw = Math.min(22, band * 0.6);
  const every = Math.max(1, Math.ceil(months.length / Math.floor((W - L - R) / 44)));
  months.forEach((m, i) => {
    const cx = L + band * i + band / 2;
    const col = svg("g", {class: "col", tabindex: "0"}, s);
    svg("rect", {x: L + band * i, y: T, width: band, height: H - T - B, class: "colhover"}, col);
    const h = y(0) - y(values[i]);
    if (h > 0) svg("path", {d: roundTop(cx - bw / 2, y(values[i]), bw, h), fill: color}, col);
    if (i % every === 0) svg("text", {x: cx, y: H - 8, "text-anchor": "middle", class: "lbl"}, s).textContent = monthName(m);
    hover(col, `<b>${monthName(m)}</b><div class="row"><span>${esc(unit)}</span><span>${values[i]}</span></div>`);
  });
  return s;
}

/* A few series over the same dates on 0–100 (the risk tests over time). */
export function lines(dates, series, width) {
  const W = Math.max(280, Math.round(width || 600)), H = 200, L = 34, R = 16, T = 12, B = 26;
  const x = (i) => L + (W - L - R) * (dates.length > 1 ? i / (dates.length - 1) : 0.5);
  const y = (v) => T + (H - T - B) * (1 - v / 100);
  const s = svg("svg", {viewBox: `0 0 ${W} ${H}`, class: "viz chart", role: "img", "aria-label": series.map(sr => `${sr.name}: ${sr.values.join(", ")}`).join("; ")});
  const grid = svg("g", {class: "grid"}, s);
  for (const v of [0, 25, 50, 75, 100]) {
    svg("line", {x1: L, x2: W - R, y1: y(v), y2: y(v)}, grid);
    svg("text", {x: L - 6, y: y(v) + 4, "text-anchor": "end", class: "lbl"}, s).textContent = String(v);
  }
  dates.forEach((d, i) => {
    svg("text", {x: x(i), y: H - 8, "text-anchor": i === 0 ? "start" : i === dates.length - 1 ? "end" : "middle", class: "lbl"}, s)
      .textContent = d.slice(5, 7) + "/" + d.slice(2, 4);
  });
  for (const sr of series) {
    svg("polyline", {points: sr.values.map((v, i) => `${x(i)},${y(v)}`).join(" "), fill: "none", stroke: sr.color, "stroke-width": 2.5, "stroke-linejoin": "round"}, s);
    sr.values.forEach((v, i) => {
      const c = svg("circle", {cx: x(i), cy: y(v), r: 5, fill: sr.color, stroke: "var(--surface)", "stroke-width": 2, tabindex: "0"}, s);
      hover(c, `<b>${esc(sr.name)}</b><div class="row"><span>${esc(dates[i])}</span><span>${v}/100</span></div>`);
    });
  }
  return s;
}

/* A small trend line without axes (an agent's accuracy over twelve months). */
export function sparkline(values, label, w = 132, h = 32) {
  const lo = Math.min(...values), hi = Math.max(...values), span = hi - lo || 1;
  const x = (i) => 2 + (w - 4) * i / Math.max(1, values.length - 1);
  const y = (v) => h - 3 - (h - 6) * (v - lo) / span;
  const s = svg("svg", {viewBox: `0 0 ${w} ${h}`, width: w, height: h, class: "mini", role: "img", "aria-label": label});
  svg("polyline", {points: values.map((v, i) => `${x(i)},${y(v)}`).join(" "), fill: "none", stroke: "var(--series)", "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round"}, s);
  svg("circle", {cx: x(values.length - 1), cy: y(values[values.length - 1]), r: 3, fill: "var(--series)"}, s);
  return s;
}

/* Months of spending as the old pages said it: years from 36 months, one decimal below 10. */
export function monthsText(m) {
  const vn = (x, d) => x.toFixed(d).replace(".", DECIMAL).replace(/,0$/, "");
  return m >= 36 ? vn(m / 12, 0) + " năm" : vn(m, m >= 10 ? 0 : 1) + " tháng";
}
