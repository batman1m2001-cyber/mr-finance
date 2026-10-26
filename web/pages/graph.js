/* Đồ thị tác động (redesign kit K3): news → event → scenario → factor → asset → family → goal for one family,
   drawn in columns from GET /api/families/{id}/graph. Every edge shows the stored records it came from. Click
   (or Enter on) a node to light its path and read its details; the list view is the same graph as a table. */
import {internal, $, empty, esc, get, n as how, pct, signClass, vnd} from "../core/core.js";
import {hover} from "../charts/charts.js";

const COLOR = {news: "var(--s7)", event: "var(--s1)", branch: "var(--s4)", factor: "var(--s5)", asset: "var(--s2)",
  family: "var(--ink-2)", goal: "var(--s3)"};
const KIND = {news: "Tin", event: "Sự kiện", branch: "Kịch bản", factor: "Yếu tố", asset: "Tài sản", family: "Gia đình", goal: "Mục tiêu"};
const SRC = {event: "Sự kiện", view: "Nhận định", run: "Lần áp dụng"};
const NS = "http://www.w3.org/2000/svg";
// Living Interface (B-01): a Copilot answer about an event lights that event's path, as a click would
let onFocus = null;
window.addEventListener("mf:focus", (e) => onFocus && onFocus(e.detail.keys || []));

const mk = (tag, attrs, parent) => {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) n.setAttribute(k, v);
  if (parent) parent.appendChild(n);
  return n;
};

export async function render(box, ctx) {
  const client = ctx.client(), staff = ctx.role !== "client", cio = ctx.role === "cio";
  let g;
  if (cio) {  // the CIO's whole run (UI redesign R4): the run named in the address, else the latest
    const {runs} = await get("/api/runs");
    const run = runs.find(r => r.id === ctx.param) || runs.find(r => r.status === "EFFECTIVE") || runs[0];
    if (!run) { box.innerHTML = `<div class="panel">${empty("Chưa có lần áp dụng", "Một lần áp dụng được tạo khi CIO duyệt nhận định.")}</div>`; return; }
    g = await get(`/api/runs/${encodeURIComponent(run.id)}/graph`);
    g.runsList = runs;
  } else {
    g = await get(`/api/families/${encodeURIComponent(client)}/graph?role=${staff ? "rm" : "client"}`);
  }
  if (!g.nodes.length) {
    box.innerHTML = `<div class="panel">${empty("Chưa có tin nào được CIO duyệt áp dụng cho gia đình này",
      "Khi một nhận định được duyệt và có hiệu lực, đồ thị cho thấy tin đi tới tài sản và mục tiêu của gia đình thế nào.")}</div>`;
    return;
  }
  const narrow = (box.clientWidth || window.innerWidth) < 760;
  const state = {view: narrow ? "list" : "graph", hidden: new Set(), sel: null};
  const byId = Object.fromEntries(g.nodes.map(n => [n.id, n]));
  const src = (e) => e.sources.map(s => `${SRC[s.type] || s.type} ${esc(s.id)}`).join(" · ");
  const val = (e) => (e.value == null ? "" : how(vnd(e.value, true), "impact.edge"));

  box.innerHTML = `${cio ? internal() : ""}
    <div class="panel">
      <h3>${cio ? `Đồ thị lần áp dụng <span class="hint">${esc(g.run_id)} · ${g.families} gia đình · 3 tháng</span>`
        : `Đồ thị tác động <span class="hint">${esc(g.family || "")} · ${g.runs.length} lần áp dụng đang hiệu lực · 3 tháng</span>`}</h3>
      ${cio ? `<div class="row tight"><label class="small muted" for="g-run">Lần áp dụng</label><select id="g-run">${g.runsList.map(r => `<option value="${esc(r.id)}" ${r.id === g.run_id ? "selected" : ""}>${esc(r.id)} · ${esc(r.status_label)}</option>`).join("")}</select>
        <a class="btn sm" href="#/cio/ap-dung/${esc(g.run_id)}">Mở lần áp dụng</a></div>` : ""}
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
      n.expected_3m != null && `Tác động kỳ vọng 3 tháng: <b class="${signClass(n.expected_3m)}">${how(vnd(n.expected_3m, true), "impact.expected_3m", {event: n.label})}</b>`,
      n.probability != null && `Xác suất: <b>${how(pct(n.probability, false, 0), "scenario.probability")}</b>`,
      n.family_expected != null && `Gia đình trong nhánh này: <b class="${signClass(n.family_expected)}">${how(vnd(n.family_expected, true), "impact.branch", {branch: n.label})}</b>`,
      n.contribution != null && `Đóng góp cho gia đình: <b class="${signClass(n.contribution)}">${how(vnd(n.contribution, true), "impact.holding")}</b>`,
      n.net_worth != null && `Tài sản ròng: <b>${how(vnd(n.net_worth), "net_worth")}</b>`,
      n.pre_review && `<span class="badge bad">RM xem trước</span>`,
      n.before && `Mức đáp ứng: <b>${esc(n.before)} → ${esc(n.after)}</b> (hạn ${esc(n.date)})`,
      n.url && `<a href="${esc(n.url)}" target="_blank" rel="noopener">Mở bài gốc (${esc(n.outlet || "")})</a>`,
    ].filter(Boolean);
    const rel = g.edges.filter(e => e.from === n.id || e.to === n.id);
    if (n.kind === "event" && !cio) { el.innerHTML = impactCard(n, rel); $("#g-clear", box).onclick = () => select(null); bindJumps(el); return; }
    el.innerHTML = `<div class="card" style="padding:14px 16px"><div class="row"><span class="badge" style="border-color:${COLOR[n.kind]}">${KIND[n.kind]}</span><b ${n.kind === "branch" ? "data-explains" : "data-quote"}>${esc(n.label)}</b>
        <button type="button" class="linkbtn small" id="g-clear" style="margin-left:auto">Bỏ chọn</button></div>
      ${facts.length ? `<div class="small mt">${facts.join(" · ")}</div>` : ""}
      <table class="table mt"><tbody>${rel.map(e => `<tr><td data-quote>${esc(byId[e.from].label)} → ${esc(byId[e.to].label)}</td><td class="small muted">${esc(e.label)}</td><td class="r num ${signClass(e.value || 0)}">${val(e)}</td><td class="small muted">${src(e)}</td></tr>`).join("")}</tbody></table></div>`;
    $("#g-clear", box).onclick = () => select(null);
  };

  // News Impact (board panel 4): the event, its direction, the chain it travels, the assets it may move — the
  // assets' figures are this event's own share of each edge (``by_run``), against the family's net worth
  const impactCard = (n, rel) => {
    const on = path(n.id);
    const fam = g.nodes.find(x => x.kind === "family");
    const chain = g.columns.filter(c => g.nodes.some(x => x.kind === c.kind && on.has(x.id)));
    const assets = g.edges.filter(e => on.has(e.from) && byId[e.from].kind === "asset" && byId[e.to].kind === "family" && e.by_run && e.by_run[n.run] != null)
      .map(e => ({n: byId[e.from], v: e.by_run[n.run]})).sort((a, b) => Math.abs(b.v) - Math.abs(a.v));
    const news = g.nodes.filter(x => x.kind === "news" && on.has(x.id));
    const branches = g.nodes.filter(x => x.kind === "branch" && on.has(x.id)).sort((a, b) => b.probability - a.probability);
    const goals = g.nodes.filter(x => x.kind === "goal" && on.has(x.id));
    const v = n.expected_3m || 0;
    return `<div class="card impactcard" style="padding:16px 18px">
      <div class="row tight"><span class="pill ${v < 0 ? "bad" : v > 0 ? "good" : ""}">${v < 0 ? "Tiêu cực" : v > 0 ? "Tích cực" : "Trung tính"}</span>
        <span class="small muted">${news.length} tin · ${branches.length} kịch bản CIO duyệt</span>
        <button type="button" class="linkbtn small" id="g-clear" style="margin-left:auto">Bỏ chọn</button></div>
      <h4 data-quote>${esc(n.label)}</h4>
      <div class="kv"><span>Tác động kỳ vọng 3 tháng</span><b class="${signClass(v)}">${how(vnd(v, true), "impact.expected_3m", {event: n.label})}${fam && fam.net_worth ? ` · ${how(pct(v / fam.net_worth, true, 2), "impact.expected_3m", {event: n.label})} tài sản ròng` : ""}</b></div>
      ${branches[0] ? `<div class="kv"><span>Kịch bản chính</span><b data-explains>${esc(branches[0].label)}</b></div>` : ""}
      <div class="subhead mt">Chuỗi tác động</div>
      <div class="chainrow">${chain.map((c, i) => `${i ? `<span class="muted" aria-hidden="true">→</span>` : ""}<span class="chip"><i class="legend-dot" style="background:${COLOR[c.kind]}"></i>${esc(c.label)} · ${g.nodes.filter(x => x.kind === c.kind && on.has(x.id)).length}</span>`).join("")}</div>
      <div class="subhead mt">${staff ? "Khoản" : "Nhóm tài sản"} có thể bị ảnh hưởng</div>
      <div class="mlist">${assets.map(a => `<button type="button" class="mrow" data-jump="${esc(a.n.id)}"><span><b>${esc(a.n.label)}</b></span>
        <span class="num ${signClass(a.v)}">${how(vnd(a.v, true), "impact.by_class", {part: a.n.label, event: n.label})}${fam && fam.net_worth ? ` <span class="small muted">${how(Math.abs(a.v / fam.net_worth) < 5e-5 ? "≈0%" : pct(a.v / fam.net_worth, true, 2), "impact.by_class", {part: a.n.label, event: n.label})}</span>` : ""}</span></button>`).join("") || `<p class="small muted">Không khoản nào.</p>`}</div>
      ${goals.length ? `<div class="subhead mt">Mục tiêu</div>${goals.map(x => `<div class="kv"><span>${esc(x.label)}</span><b>${esc(x.before)} → ${esc(x.after)}</b></div>`).join("")}` : ""}
      <div class="small muted mt">“Có thể ảnh hưởng” theo kịch bản CIO duyệt, không phải quan hệ nhân quả · nguồn: ${news.map(x => esc(x.outlet || x.label)).slice(0, 3).join(", ")}</div></div>`;
  };
  const bindJumps = (el) => { for (const b of el.querySelectorAll("[data-jump]")) b.onclick = () => select(b.dataset.jump); };

  const select = (id) => { state.sel = state.sel === id ? null : id; state.flash = !!state.sel; draw(); };
  onFocus = (keys) => {
    if (!box.isConnected) { onFocus = null; return; }
    const id = keys.map(k => k.startsWith("event:") && `EV:${k.slice(6)}`).find(x => x && byId[x]);
    if (id && state.view === "graph" && state.sel !== id) { state.hidden.delete("event"); state.sel = id; state.flash = true; draw(); }
  };
  const focusKey = (e) => [byId[e.from], byId[e.to]].filter(n => n.kind === "event").map(n => `event:${n.ref}`).join(" ") || null;

  const drawList = (el) => {
    const es = shownEdges();
    if ((el.clientWidth || window.innerWidth) < 640) {  // a phone: one stacked line per edge
      el.innerHTML = `<div class="list">${es.map(e => `<div class="gedge"${focusKey(e) ? ` data-focus="${esc(focusKey(e))}"` : ""}>
        <button type="button" class="linkbtn" data-n="${esc(e.from)}">${esc(byId[e.from].label)}</button> → <button type="button" class="linkbtn" data-n="${esc(e.to)}">${esc(byId[e.to].label)}</button>
        <div class="small muted">${esc(e.label)}${e.value == null ? "" : ` · <span class="num ${signClass(e.value)}">${val(e)}</span>`} · ${src(e)}</div></div>`).join("")}</div>`;
      for (const b of el.querySelectorAll("[data-n]")) b.onclick = () => select(b.dataset.n);
      return;
    }
    el.innerHTML = `<table class="table"><thead><tr><th>Từ</th><th>Đến</th><th>Quan hệ</th><th class="r">3 tháng</th><th>Nguồn</th></tr></thead><tbody>${
      es.map(e => `<tr${focusKey(e) ? ` data-focus="${esc(focusKey(e))}"` : ""}><td><button type="button" class="linkbtn" data-n="${esc(e.from)}">${esc(byId[e.from].label)}</button><div class="small muted">${KIND[byId[e.from].kind]}</div></td>
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
    const flash = state.flash; state.flash = false;  // the path just chosen fades in column by column, once
    const col = Object.fromEntries(cols.map((c, i) => [c.kind, i]));
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
        "stroke-width": e.value == null ? 1.5 : 1.5 + 5 * Math.abs(e.value) / maxV, "stroke-opacity": on ? 0.75 : 0.08,
        class: flash && lit && on ? "mf-lit" : null, style: flash && lit && on ? `--i:${col[byId[e.from].kind]}` : null}, svg);
      hover(p, `${esc(byId[e.from].label)} → ${esc(byId[e.to].label)}<br>${esc(e.label)}${e.value == null ? "" : " · " + val(e)}<br><span class="muted">${src(e)}</span>`);
    }
    for (const n of g.nodes) {
      const q = pos[n.id];
      if (!q) continue;
      const on = !lit || lit.has(n.id);
      const grp = mk("g", {tabindex: 0, role: "button", class: flash && lit && on ? "gnode mf-lit" : "gnode", "aria-label": `${KIND[n.kind]}: ${n.label}`,
        "aria-pressed": String(state.sel === n.id), opacity: on ? 1 : 0.2, style: flash && lit && on ? `--i:${col[n.kind]}` : null,
        "data-focus": n.kind === "event" ? `event:${n.ref}` : null}, svg);
      mk("rect", {x: q.x, y: q.y, width: nodeW, height: 28, rx: 7, fill: "var(--surface)", stroke: COLOR[n.kind],
        "stroke-width": state.sel === n.id ? 2.5 : 1.5}, grp);
      const t = mk("text", {x: q.x + 9, y: q.y + 18, class: "lbl"}, grp);
      const max = Math.floor((nodeW - 16) / 7);
      t.textContent = n.label.length > max ? n.label.slice(0, max - 1) + "…" : n.label;
      // headlines are the outlets' words; a branch's label carries its probability, explained in the node's panel
      if (["news", "event"].includes(n.kind)) t.setAttribute("data-quote", "");
      if (n.kind === "branch") t.setAttribute("data-explains", "");
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
  const pick = $("#g-run", box);
  if (pick) pick.onchange = () => ctx.go(ctx.href("do-thi", pick.value));
  draw();
}
