/* Small charts for cards (UI redesign R1, R-D3): spark bars, a ring, a donut, a gauge and a progress bar.
   Each returns an HTML/SVG string drawn only from the numbers it is given — no smoothing, no invented points —
   with an aria-label that says the same thing in words. Static: no animation. */
import {esc} from "../core/core.js";

const f = (x) => Math.round(x * 100) / 100;

/* Bars for a short series, the last one in the accent (e.g. income per month). values: numbers ≥ 0. */
export function sparkBars(values, {w = 96, h = 32, color = "var(--series)", label = ""} = {}) {
  const n = values.length;
  if (!n) return "";
  const max = Math.max(...values, 1), gap = 2, bw = (w - gap * (n - 1)) / n;
  const bars = values.map((v, i) => {
    const bh = Math.max(1.5, (v / max) * (h - 1));
    return `<rect x="${f(i * (bw + gap))}" y="${f(h - bh)}" width="${f(bw)}" height="${f(bh)}" rx="1.5" fill="${color}" opacity="${i === n - 1 ? 1 : 0.35}"/>`;
  }).join("");
  return `<svg class="mini" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(label)}">${bars}</svg>`;
}

/* A ring for one share (0…1), with the share written in the middle. */
// how: the text's “cách tính” attributes (core.nAttrs), BRD-NFR-11
export function ring(frac, {size = 56, stroke = 7, color = "var(--series)", text = null, label = "", how = ""} = {}) {
  const r = (size - stroke) / 2, c = 2 * Math.PI * r, x = Math.max(0, Math.min(1, frac || 0));
  const t = text == null ? `${Math.round(x * 100)}%` : text;
  return `<svg class="mini" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" role="img" aria-label="${esc(label)}">
    <circle class="track" cx="${size / 2}" cy="${size / 2}" r="${f(r)}" stroke-width="${stroke}"/>
    <circle cx="${size / 2}" cy="${size / 2}" r="${f(r)}" fill="none" stroke="${color}" stroke-width="${stroke}" stroke-linecap="round"
      stroke-dasharray="${f(c * x)} ${f(c)}" transform="rotate(-90 ${size / 2} ${size / 2})"/>
    <text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" font-size="${Math.round(size / 4.4)}" font-weight="700" fill="var(--ink)"${how}>${esc(t)}</text></svg>`;
}

/* A donut of parts [{key, value, color, label}], a 2 px gap between parts, the total (or `center`) inside.
   Each part carries data-key so the page can open it; the page supplies the legend. */
export function donut(parts, {size = 176, stroke = 24, center = "", sub = "", label = "", how = ""} = {}) {
  const total = parts.reduce((a, p) => a + Math.max(0, p.value), 0);
  if (!total) return "";
  const r = (size - stroke) / 2, cx = size / 2, gapA = parts.length > 1 ? 2 / r : 0;
  let a0 = -Math.PI / 2;
  const arcs = parts.filter(p => p.value > 0).map(p => {
    const span = (p.value / total) * 2 * Math.PI, a1 = a0 + span;
    const s = a0 + gapA / 2, e = Math.max(s + 0.001, a1 - gapA / 2);
    const large = e - s > Math.PI ? 1 : 0;
    const pt = (a) => `${f(cx + r * Math.cos(a))},${f(cx + r * Math.sin(a))}`;
    a0 = a1;
    return `<path class="seg" data-key="${esc(p.key)}" tabindex="0" role="button" aria-label="${esc(p.label)}"
      d="M${pt(s)}A${f(r)},${f(r)} 0 ${large} 1 ${pt(e)}" fill="none" stroke="${p.color}" stroke-width="${stroke}"/>`;
  }).join("");
  return `<svg class="mini donut" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" role="group" aria-label="${esc(label)}">${arcs}
    <text x="50%" y="${sub ? "46%" : "50%"}" dominant-baseline="central" text-anchor="middle" font-size="${Math.round(size / 8)}" font-weight="750" fill="var(--ink)"${how}>${esc(center)}</text>
    ${sub ? `<text x="50%" y="60%" dominant-baseline="central" text-anchor="middle" font-size="${Math.round(size / 15)}" fill="var(--muted)">${esc(sub)}</text>` : ""}</svg>`;
}

/* A value against a limit on one bar (e.g. stress loss vs the accepted drawdown): fill to the value, a tick at
   the limit, coloured by the status the server decided. */
export function gauge(value, limit, {status = "ok", max = null, label = ""} = {}) {
  const top = max || Math.max(value, limit) * 1.25 || 1;
  const color = {ok: "var(--good)", near: "var(--warning)", over: "var(--critical)"}[status] || "var(--series)";
  return `<div class="gauge" role="img" aria-label="${esc(label)}"><div class="bar-track"><i style="width:${f(Math.min(1, value / top) * 100)}%;background:${color}"></i></div>
    <span class="gauge-tick" style="left:${f(Math.min(1, limit / top) * 100)}%"></span></div>`;
}

/* A progress bar for a share (0…1). */
export function progress(frac, {color = "var(--series)", label = ""} = {}) {
  const x = Math.max(0, Math.min(1, frac || 0));
  return `<div class="bar-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(x * 100)}" aria-label="${esc(label)}"><i style="width:${f(x * 100)}%;background:${color}"></i></div>`;
}
