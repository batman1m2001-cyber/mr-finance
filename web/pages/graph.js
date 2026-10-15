/* Đồ thị tác động (redesign kit K3): news → event → scenario → factor → asset → family → goal for one family,
   drawn in columns from GET /api/families/{id}/graph. Every edge shows the stored records it came from. Click
   (or Enter on) a node to light its path and read its details; the list view is the same graph as a table. */
import {$, empty, esc, get, pct, signClass, vnd} from "../core/core.js";
import {hover} from "../charts/charts.js";

const COLOR = {news: "var(--s7)", event: "var(--s1)", branch: "var(--s4)", factor: "var(--s5)", asset: "var(--s2)",
  family: "var(--ink-2)", goal: "var(--s3)"};
const KIND = {news: "Tin", event: "Sự kiện", branch: "Kịch bản", factor: "Yếu tố", asset: "Tài sản", family: "Gia đình", goal: "Mục tiêu"};
const SRC = {event: "Sự kiện", view: "Nhận định", run: "Lần áp dụng"};
const NS = "http://www.w3.org/2000/svg";
const mk = (tag, attrs, parent) => {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) n.setAttribute(k, v);
  if (parent) parent.appendChild(n);
  return n;
};

export async function render(box, ctx) {
  const client = ctx.client(), staff = ctx.role !== "client";
  const g = await get(`/api/families/${encodeURIComponent(client)}/graph?role=${staff ? "rm" : "client"}`);
  if (!g.nodes.length) {
    box.innerHTML = `<div class="panel">${empty("Chưa có tin nào được CIO duyệt áp dụng cho gia đình này",
      "Khi một nhận định được duyệt và có hiệu lực, đồ thị cho thấy tin đi tới tài sản và mục tiêu của gia đình thế nào.")}</div>`;
    return;
  }
  const narrow = (box.clientWidth || window.innerWidth) < 760;
  const state = {view: narrow ? "list" : "graph", hidden: new Set(), sel: null};
  const byId = Object.fromEntries(g.nodes.map(n => [n.id, n]));
  const src = (e) => e.sources.map(s => `${SRC[s.type] || s.type} ${esc(s.id)}`).join(" · ");
  const val = (e) => (e.value == null ? "" : vnd(e.value, true));

  box.innerHTML = `
    <div class="panel">
      <h3>Đồ thị tác động <span class="hint">${esc(g.family || "")} · ${g.runs.length} lần áp dụng đang hiệu lực · 3 tháng</span></h3>
      <div class="row" style="gap:6px;flex-wrap:wrap">
        <div class="seg" role="group" aria-label="Cách xem"><button type="button" data-v="graph">Đồ thị</button><button type="button" data-v="list">Danh sách</button></div>
        <span class="small muted" style="margin-left:8px">Hiện:</span>
        ${g.columns.map(c => `<button type="button" class="chip" data-k="${c.kind}" aria-pressed="true"><i style="display:inline-block;width:9px;height:9px;border-radius:3px;background:${COLOR[c.kind]};margin-right:6px"></i>${esc(c.label)}</button>`).join("")}
      </div>
      <div id="g-body" class="mt"></div>
      <div id="g-detail" class="mt"></div>
      <div class="footnote">${esc(g.note)}</div>
    </div>`;

  const visible = (n) => !state.hidden.has(n.kind);
  const shownEdges = () => g.edges.filter(e => visible(byId[e.from]) && visible(byId[e.to]));

  // the path through a node: everything upstream and downstream of it
  const path = (id) => {
    const keep = new Set([id]);
    const walk = (dir) => {
      const todo = [id];
      while (todo.length) {
        const cur = todo.pop();
        for (const e of g.edges) {
          const [a, b] = dir === "down" ? [e.from, e.to] : [e.to, e.from];
          if (a === cur && !keep.has(b)) { keep.add(b); todo.push(b); }
        }
      }
    };
    walk("down"); walk("up");
    return keep;
  };

  const detail = () => {
    const el = $("#g-detail", box);
    const n = state.sel && byId[state.sel];
    if (!n) { el.innerHTML = `<div class="small muted">Bấm một nút để xem đường đi và nguồn của nó.</div>`; return; }
    const facts = [
      n.expected_3m != null && `Tác động kỳ vọng 3 tháng: <b class="${signClass(n.expected_3m)}">${vnd(n.expected_3m, true)}</b>`,
      n.probability != null && `Xác suất: <b>${pct(n.probability, false, 0)}</b>`,
      n.family_expected != null && `Gia đình trong nhánh này: <b class="${signClass(n.family_expected)}">${vnd(n.family_expected, true)}</b>`,
      n.contribution != null && `Đóng góp cho gia đình: <b class="${signClass(n.contribution)}">${vnd(n.contribution, true)}</b>`,
      n.net_worth != null && `Tài sản ròng: <b>${vnd(n.net_worth)}</b>`,
      n.before && `Mức đáp ứng: <b>${esc(n.before)} → ${esc(n.after)}</b> (hạn ${esc(n.date)})`,
      n.url && `<a href="${esc(n.url)}" target="_blank" rel="noopener">Mở bài gốc (${esc(n.outlet || "")})</a>`,
    ].filter(Boolean);
    const rel = g.edges.filter(e => e.from === n.id || e.to === n.id);
    el.innerHTML = `<div class="card" style="padding:14px 16px"><div class="row"><span class="badge" style="border-color:${COLOR[n.kind]}">${KIND[n.kind]}</span><b>${esc(n.label)}</b>
        <button type="button" class="linkbtn small" id="g-clear" style="margin-left:auto">Bỏ chọn</button></div>
      ${facts.length ? `<div class="small mt">${facts.join(" · ")}</div>` : ""}
      <table class="table mt"><tbody>${rel.map(e => `<tr><td>${esc(byId[e.from].label)} → ${esc(byId[e.to].label)}</td><td class="small muted">${esc(e.label)}</td><td class="r num ${signClass(e.value || 0)}">${val(e)}</td><td class="small muted">${src(e)}</td></tr>`).join("")}</tbody></table></div>`;
    $("#g-clear", box).onclick = () => select(null);
  };

  const select = (id) => { state.sel = state.sel === id ? null : id; draw(); };

  const drawList = (el) => {
    const es = shownEdges();
    if ((el.clientWidth || window.innerWidth) < 640) {  // a phone: one stacked line per edge
      el.innerHTML = `<div class="list">${es.map(e => `<div class="gedge">
        <button type="button" class="linkbtn" data-n="${esc(e.from)}">${esc(byId[e.from].label)}</button> → <button type="button" class="linkbtn" data-n="${esc(e.to)}">${esc(byId[e.to].label)}</button>
        <div class="small muted">${esc(e.label)}${e.value == null ? "" : ` · <span class="num ${signClass(e.value)}">${val(e)}</span>`} · ${src(e)}</div></div>`).join("")}</div>`;
      for (const b of el.querySelectorAll("[data-n]")) b.onclick = () => select(b.dataset.n);
      return;
    }
    el.innerHTML = `<table class="table"><thead><tr><th>Từ</th><th>Đến</th><th>Quan hệ</th><th class="r">3 tháng</th><th>Nguồn</th></tr></thead><tbody>${
      es.map(e => `<tr><td><button type="button" class="linkbtn" data-n="${esc(e.from)}">${esc(byId[e.from].label)}</button><div class="small muted">${KIND[byId[e.from].kind]}</div></td>
        <td><button type="button" class="linkbtn" data-n="${esc(e.to)}">${esc(byId[e.to].label)}</button><div class="small muted">${KIND[byId[e.to].kind]}</div></td>
        <td class="small">${esc(e.label)}</td><td class="r num ${signClass(e.value || 0)}">${val(e)}</td><td class="small muted">${src(e)}</td></tr>`).join("")}</tbody></table>`;
    for (const b of el.querySelectorAll("[data-n]")) b.onclick = () => select(b.dataset.n);
  };

  const drawGraph = (el) => {
    const cols = g.columns.filter(c => !state.hidden.has(c.kind));
    const width = Math.max(720, el.clientWidth || 1100), colW = width / cols.length, nodeW = Math.min(170, colW - 26), rowH = 38;
    const per = cols.map(c => g.nodes.filter(n => n.kind === c.kind));
    const height = 30 + Math.max(...per.map(p => p.length)) * rowH + 10;
    const pos = {};
    per.forEach((list, i) => {
      const top = 30 + (height - 40 - list.length * rowH) / 2;
      list.forEach((n, j) => { pos[n.id] = {x: i * colW + (colW - nodeW) / 2, y: top + j * rowH}; });
    });
    const lit = state.sel ? path(state.sel) : null;
    const svg = mk("svg", {class: "viz igraph", viewBox: `0 0 ${width} ${height}`, role: "group", "aria-label": "Đồ thị tác động"});
    cols.forEach((c, i) => { const t = mk("text", {x: i * colW + colW / 2, y: 14, "text-anchor": "middle", class: "lbl"}, svg); t.textContent = c.label; });
    const es = shownEdges();
    const maxV = Math.max(1, ...es.filter(e => e.value != null).map(e => Math.abs(e.value)));
    for (const e of es) {
      const a = pos[e.from], b = pos[e.to];
      if (!a || !b) continue;
      const x1 = a.x + nodeW, y1 = a.y + 14, x2 = b.x, y2 = b.y + 14, cx = (x1 + x2) / 2;
      const on = !lit || (lit.has(e.from) && lit.has(e.to));
      const p = mk("path", {d: `M${x1},${y1}C${cx},${y1} ${cx},${y2} ${x2},${y2}`, fill: "none",
        stroke: e.value == null ? "var(--axis)" : e.value < 0 ? "var(--down)" : "var(--up)",
        "stroke-width": e.value == null ? 1.5 : 1.5 + 5 * Math.abs(e.value) / maxV, "stroke-opacity": on ? 0.75 : 0.08}, svg);
      hover(p, `${esc(byId[e.from].label)} → ${esc(byId[e.to].label)}<br>${esc(e.label)}${e.value == null ? "" : " · " + val(e)}<br><span class="muted">${src(e)}</span>`);
    }
    for (const n of g.nodes) {
      const q = pos[n.id];
      if (!q) continue;
      const on = !lit || lit.has(n.id);
      const grp = mk("g", {tabindex: 0, role: "button", class: "gnode", "aria-label": `${KIND[n.kind]}: ${n.label}`,
        "aria-pressed": String(state.sel === n.id), opacity: on ? 1 : 0.2}, svg);
      mk("rect", {x: q.x, y: q.y, width: nodeW, height: 28, rx: 7, fill: "var(--surface)", stroke: COLOR[n.kind],
        "stroke-width": state.sel === n.id ? 2.5 : 1.5}, grp);
      const t = mk("text", {x: q.x + 9, y: q.y + 18, class: "lbl"}, grp);
      const max = Math.floor((nodeW - 16) / 7);
      t.textContent = n.label.length > max ? n.label.slice(0, max - 1) + "…" : n.label;
      hover(grp, `<b>${esc(n.label)}</b><br>${KIND[n.kind]}`);
      grp.addEventListener("click", () => select(n.id));
      grp.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); select(n.id); } });
    }
    el.innerHTML = "";
    el.appendChild(svg);
  };

  const draw = () => {
    for (const b of box.querySelectorAll("[data-v]")) b.setAttribute("aria-pressed", String(b.dataset.v === state.view));
    for (const b of box.querySelectorAll("[data-k]")) b.setAttribute("aria-pressed", String(!state.hidden.has(b.dataset.k)));
    const el = $("#g-body", box);
    (state.view === "graph" ? drawGraph : drawList)(el);
    detail();
  };
  for (const b of box.querySelectorAll("[data-v]")) b.onclick = () => { state.view = b.dataset.v; draw(); };
  for (const b of box.querySelectorAll("[data-k]")) b.onclick = () => {
    const k = b.dataset.k;
    state.hidden.has(k) ? state.hidden.delete(k) : state.hidden.add(k);
    if (state.sel && state.hidden.has(byId[state.sel].kind)) state.sel = null;
    draw();
  };
  draw();
}
