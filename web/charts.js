/* The charts: a stacked share bar, meters, and the cash-flow columns. Plain SVG/HTML, a tooltip
   on every mark, colour by role from app.css tokens. */
(function (g) {
  "use strict";
  const {vnd, pct, monthName, esc} = g.Fmt;
  const NS = "http://www.w3.org/2000/svg";
  const tip = () => document.getElementById("tip");

  function showTip(ev, html) {
    const t = tip();
    t.innerHTML = html;
    t.hidden = false;
    const r = t.getBoundingClientRect();
    let x = ev.clientX + 14, y = ev.clientY + 14;
    if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - 14;
    if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - 14;
    t.style.left = Math.max(8, x) + "px";
    t.style.top = Math.max(8, y) + "px";
  }
  const hideTip = () => { tip().hidden = true; };
  function hover(el, html) {
    el.addEventListener("mousemove", (ev) => showTip(ev, typeof html === "function" ? html() : html));
    el.addEventListener("mouseleave", hideTip);
    el.addEventListener("focus", () => { const r = el.getBoundingClientRect(); showTip({clientX: r.left, clientY: r.bottom}, typeof html === "function" ? html() : html); });
    el.addEventListener("blur", hideTip);
  }

  /* Part of a whole: one bar, a 2px gap between segments, a legend with every value. */
  function shareBar(rows, colorOf) {
    const wrap = document.createElement("div");
    const bar = document.createElement("div");
    bar.className = "stack";
    bar.setAttribute("role", "img");
    bar.setAttribute("aria-label", rows.map(r => `${r.label} ${pct(r.share, false, 0)}`).join(", "));
    for (const r of rows) {
      if (r.share <= 0) continue;
      const s = document.createElement("span");
      s.style.flex = `${r.share} 1 0`;
      s.style.background = colorOf(r);
      s.tabIndex = 0;
      hover(s, `<b>${esc(r.label)}</b><div class="row"><span>${vnd(r.value)}</span><span>${pct(r.share)}</span></div>`);
      bar.append(s);
    }
    const ul = document.createElement("ul");
    ul.className = "legend";
    for (const r of rows) {
      const li = document.createElement("li");
      li.innerHTML = `<span class="sw" style="background:${colorOf(r)}"></span><span>${esc(r.label)}</span>`
        + `<span class="v">${vnd(r.value)}</span><span class="p">${pct(r.share, false, r.share < 0.1 ? 1 : 0)}</span>`;
      ul.append(li);
    }
    wrap.append(bar, ul);
    return wrap;
  }

  /* A ratio against a limit: the fill carries the status, a tick marks the limit. */
  function meter(value, max, limit, color, label) {
    const m = document.createElement("div");
    m.className = "meter";
    m.setAttribute("role", "meter");
    m.setAttribute("aria-valuemin", "0");
    m.setAttribute("aria-valuemax", String(max));
    m.setAttribute("aria-valuenow", String(value));
    m.setAttribute("aria-label", label);
    const f = document.createElement("span");
    f.className = "fill";
    f.style.width = `${Math.min(100, (value / max) * 100)}%`;
    f.style.background = color;
    m.append(f);
    if (limit != null) {
      const k = document.createElement("span");
      k.className = "mark";
      k.style.left = `calc(${Math.min(100, (limit / max) * 100)}% - 1px)`;
      m.append(k);
    }
    return m;
  }

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

  /* Money in above the line, out below it, one column pair per month; one axis. A month with a
     large payment gets a marker and its label. */
  function cashflow(months, large, width) {
    // drawn at the width it is shown at: a scaled viewBox would scale its text too
    const W = Math.max(300, Math.round(width || 760)), H = W < 520 ? 220 : 260, L = 64, R = 8, T = 14, B = 30;
    const maxIn = Math.max(...months.map(m => m.in), 0);
    const maxOut = Math.max(...months.map(m => m.out), 0);
    // one step for both sides, so the ticks are evenly spaced and never crowd
    const step = niceMax(Math.max(maxIn, maxOut, 1)) / 2;
    const top = Math.max(step, Math.ceil(maxIn / step) * step);
    const bot = maxOut > 0 ? Math.ceil(maxOut / step) * step : 0;
    const span = top + bot;
    const zero = T + (H - T - B) * (top / span);
    const y = (v) => zero - (H - T - B) * (v / span);
    const s = svg("svg", {viewBox: `0 0 ${W} ${H}`, class: "chart", role: "img",
      "aria-label": `Dòng tiền ${months.length} tháng tới: vào ${vnd(months.reduce((a, m) => a + m.in, 0))}, ra ${vnd(months.reduce((a, m) => a + m.out, 0))}`});
    const grid = svg("g", {class: "grid"}, s);
    const ticks = [];
    for (let v = top; v > 0; v -= step) ticks.push(v);
    for (let v = -step; v >= -bot; v -= step) ticks.push(v);
    for (const v of ticks) {
      const yy = y(v);
      svg("line", {x1: L, x2: W - R, y1: yy, y2: yy}, grid);
      const t = svg("text", {x: L - 8, y: yy + 4, "text-anchor": "end"}, s);
      t.textContent = (v > 0 ? "+" : v < 0 ? "−" : "") + vnd(Math.abs(v)).replace(" ", " ");
    }
    svg("line", {x1: L, x2: W - R, y1: zero, y2: zero, class: "base"}, s);
    const n = months.length, band = (W - L - R) / n, bw = Math.min(24, band * 0.62);
    const bigMonths = new Set((large || []).map(l => l.month));
    months.forEach((m, i) => {
      const cx = L + band * i + band / 2;
      const col = svg("g", {class: "col", tabindex: "0"}, s);
      svg("rect", {x: L + band * i, y: T, width: band, height: H - T - B, class: "colhover"}, col);
      if (m.in > 0) {
        const h = zero - y(m.in);
        svg("path", {d: roundTop(cx - bw / 2, zero - h, bw, h), fill: "var(--in)"}, col);
      }
      if (m.out > 0) {
        const h = y(-m.out) - zero;
        svg("path", {d: roundBottom(cx - bw / 2, zero, bw, h), fill: "var(--out)"}, col);
      }
      if (bigMonths.has(m.month)) {
        const t = svg("text", {x: cx, y: y(-m.out) + 14, "text-anchor": "middle", style: "fill:var(--critical);font-weight:700"}, col);
        t.textContent = "⚠";
      }
      const step = Math.max(1, Math.ceil(n / Math.max(4, Math.floor((W - L - R) / 52))));
      if (i % step === 0) {
        const t = svg("text", {x: cx, y: H - 12, "text-anchor": "middle"}, s);
        t.textContent = monthName(m.month);
      }
      hover(col, () => {
        const items = m.items.slice(0, 8).map(it => `<div class="row"><span>${it.direction === "in" ? "▲" : "▼"} ${esc(it.label)}</span><span>${vnd(it.amount)}</span></div>`).join("");
        const more = m.items.length > 8 ? `<div class="muted">… và ${m.items.length - 8} khoản khác</div>` : "";
        return `<b>${monthName(m.month)} · ròng ${vnd(m.net, true)}</b><div class="row"><span>Vào</span><span>${vnd(m.in)}</span></div><div class="row"><span>Ra</span><span>${vnd(m.out)}</span></div><hr style="border:0;border-top:1px solid var(--hair)">${items}${more}`;
      });
    });
    return s;
  }
  const r4 = 4;
  function roundTop(x, y, w, h) {
    const r = Math.min(r4, h, w / 2);
    return `M${x},${y + h} V${y + r} Q${x},${y} ${x + r},${y} H${x + w - r} Q${x + w},${y} ${x + w},${y + r} V${y + h} Z`;
  }
  function roundBottom(x, y, w, h) {
    const r = Math.min(r4, h, w / 2);
    return `M${x},${y} V${y + h - r} Q${x},${y + h} ${x + r},${y + h} H${x + w - r} Q${x + w},${y + h} ${x + w},${y + h - r} V${y} Z`;
  }

  g.Charts = {shareBar, meter, cashflow, hover, hideTip};
})(window);
