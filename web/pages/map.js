/* Bản đồ tài chính — the Financial Intelligence Graph overview (UI redesign R4, R-D6; KIT-UX-04). The client in the
   centre; around them the asset classes they hold (each opens onto its holdings), the goals they follow, what puts
   the picture at risk, the policy items and the approved news events that may move it, and — on request — where
   the data comes from. From POST /api/overview: every edge names the records it was read from. Select a node to
   light its links and read them; a node opens its page; an event opens its path on Đồ thị tác động. The list view
   is the same graph as rows (the default on a phone). */
import {internal, $, esc, followedIds, pct, post, signClass, vnd} from "../core/core.js";
import {CLASS_ICON, icon, iconPaths} from "../core/icons.js?v=20261016r1";
import {hover} from "../charts/charts.js";

const NS = "http://www.w3.org/2000/svg";
const LOOK = {  // colour, icon; colour follows the kind, status colours stay for status
  family: ["var(--accent)", "user"], class: ["var(--s1)", "layers"], holding: ["var(--s1)", "wallet"],
  source: ["var(--s7)", "link"], goal: ["var(--s3)", "target"], risk: ["var(--critical)", "alert"],
  alert: ["var(--s4)", "scale"], event: ["var(--s5)", "news"],
};
// where a node sits: an angle range (degrees, 0 = right, clockwise) and a radius (share of the half-size)
const SECTOR = {class: [140, 220, 0.8], source: [226, 292, 1], event: [300, 322, 0.9], risk: [-25, 25, 0.55],
  alert: [-22, 40, 1], goal: [55, 125, 1]};
const STAGGER = new Set(["goal", "source"]);  // across the top and the bottom, neighbours take two rings
// progressive disclosure (KIT-UX-04): sources and policy items start hidden; the side list names the policy items
const DEFAULT_OFF = new Set(["source", "alert"]);
const WORDING = "có thể ảnh hưởng";  // a news event's edge: a potential impact under the CIO's scenarios, never a cause
const SRC = {holding: "khoản", risk: "rủi ro", goal: "mục tiêu", alert: "chính sách", run: "lần áp dụng"};
const views = {};  // per client: what was open, for this page's life

const mk = (tag, attrs, parent) => {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) n.setAttribute(k, v);
  if (parent) parent.appendChild(n);
  return n;
};
const short = (s, n) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope(), staff = ctx.role !== "client";
  const {overview: g} = await post("/api/overview", {client_id: client, scope, role: staff ? "rm" : "client", goals: followedIds(client)});
  const byId = Object.fromEntries(g.nodes.map(n => [n.id, n]));
  const KIND = Object.fromEntries(g.kinds.map(k => [k.kind, k.label]));
  const narrow = (box.clientWidth || innerWidth) < 760;
  const st = views[`${client}|${scope}`] ||= {view: narrow ? "list" : "graph", off: new Set(DEFAULT_OFF), open: new Set(), sel: null};
  if (st.sel && !byId[st.sel]) st.sel = null;
  const route = {
    family: staff ? ctx.href("khach-hang", "toan-canh") : ctx.href("tong-quan", "toan-canh"),
    class: staff ? ctx.href("khach-hang", "tai-san") : ctx.href("tai-san"),
    goal: staff ? ctx.href("khach-hang", "ke-hoach") : ctx.href("muc-tieu", "ke-hoach"),
    risk: staff ? ctx.href("khach-hang", "tong-quan") : ctx.href("tong-quan", "chi-tiet"),
    alert: staff ? ctx.href("khach-hang", "chinh-sach") : ctx.href("tin", "chinh-sach"),
    event: staff ? ctx.href("khach-hang", "do-thi") : ctx.href("tin", "do-thi"),
  };
  route.holding = route.source = route.class;
  const focusOf = (n) => (n.kind === "event" ? [`event:${n.ref}`] : n.kind === "alert" ? [`policy:${n.ref}`] : n.kind === "goal" ? [`goal:${n.ref}`] : null);

  // what is drawn: kinds switched on; a holding only under an open class; an edge between two drawn nodes, the
  // holding-level one when its class is open and the class-level one otherwise
  const shown = (n) => !st.off.has(n.kind === "holding" ? "class" : n.kind) && (n.kind !== "holding" || st.open.has(n.parent));
  const shownEdges = () => g.edges.filter(e => shown(byId[e.from]) && shown(byId[e.to])
    && !(e.agg && st.open.has(e.agg)) && !(e.parent && !st.open.has(e.parent)));
  const links = (id) => shownEdges().filter(e => e.from === id || e.to === id);
  const other = (e, id) => byId[e.from === id ? e.to : e.from];
  const srcText = (e) => [...new Set(e.sources.map(s => SRC[s.type] || s.type))].join(", ") + ` · ${e.sources.length} bản ghi`;
  const figure = (n) => (n.kind === "goal" ? `cần ${vnd(n.need)} · ${n.status_label}` : n.kind === "source" ? `${n.count} khoản · ${esc(n.status === "connected" ? "đã kết nối" : n.status)}`
    : n.value == null ? "" : ["event", "alert"].includes(n.kind) ? vnd(n.value, true) : vnd(Math.abs(n.value)));

  box.innerHTML = `${staff ? internal() : ""}
    <div class="pagehead"><div><div class="eyebrow">Tổng quan</div><h1 class="h1">Financial Intelligence Graph</h1>
      <p class="lede">Tài sản, mục tiêu, rủi ro, chính sách và tin tức quanh ${staff ? esc(byId.ME.label) : "bạn"} · số liệu ngày ${esc(g.as_of)}</p></div></div>
    <div class="cols">
      <div class="panel c8 mapwrap">
        <div class="row spread">
          <div class="row tight" role="group" aria-label="Hiện">${g.kinds.filter(k => !["family", "holding"].includes(k.kind)).map(k =>
            `<button type="button" class="chip" data-k="${k.kind}"><i class="legend-dot" style="background:${LOOK[k.kind][0]}"></i>${esc(k.label)}</button>`).join("")}</div>
          <div class="seg" role="group" aria-label="Cách xem"><button type="button" data-v="graph">Đồ thị</button><button type="button" data-v="list">Danh sách</button></div>
        </div>
        <div id="m-body" class="mt"></div>
        <div class="footnote">${esc(g.note)}</div>
      </div>
      <div class="panel c4" id="m-side"></div>
    </div>`;

  const select = (id) => { st.sel = st.sel === id ? null : id; draw(); };
  const toggle = (id) => { st.open.has(id) ? st.open.delete(id) : st.open.add(id); draw(); };

  // ── the side panel: what moves the picture, or the selected node and its links ──────────────────
  const side = () => {
    const el = $("#m-side", box);
    const n = st.sel && byId[st.sel];
    if (!n) {
      const moving = g.nodes.filter(x => ["event", "alert"].includes(x.kind)).sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
      el.innerHTML = `<h3>Tin tức & chính sách liên quan <span class="hint">theo mức tác động</span></h3>
        <div class="mlist">${moving.map(x => `<button type="button" class="mrow" data-n="${esc(x.id)}">
          <span class="ic-chip sm" style="--tone:${LOOK[x.kind][0]}">${icon(LOOK[x.kind][1], {size: 13})}</span>
          <span><b>${esc(short(x.label, 70))}</b><span class="small muted">${x.kind === "event" ? "Tin tức · CIO duyệt" : esc(x.status_label)}</span></span>
          <span class="num ${signClass(x.value)}">${vnd(x.value, true)}</span></button>`).join("") || `<p class="muted">Chưa có tin hay chính sách nào chạm tới tài sản này.</p>`}</div>
        <p class="small muted">Bấm một nút trên đồ thị để xem liên kết và nguồn của nó.</p>`;
    } else {
      const es = links(n.id);
      const kids = n.kind === "class" ? g.nodes.filter(x => x.parent === n.id).length : 0;
      const facts = [
        n.kind === "family" && `Tài sản ròng <b>${vnd(n.value)}</b> · tài sản ${vnd(n.assets)} · nợ ${vnd(n.liabilities)}`,
        n.kind === "class" && `${n.liability ? "Dư nợ" : "Giá trị"} <b>${vnd(n.value)}</b> · ${n.count} khoản`,
        n.kind === "holding" && `Giá trị <b>${vnd(n.value)}</b>${n.owner ? ` · ${esc(n.owner)}` : ""}`,
        n.kind === "source" && `${esc(n.what)} · ${n.count} khoản · ${esc((n.trust || []).join(", "))}`,
        n.kind === "goal" && `Cần <b>${vnd(n.need)}</b> · đang có ${vnd(n.have)} · ${n.gap > 0 ? `thiếu ${vnd(n.gap)}` : "đủ"}${n.by ? ` · mốc ${esc(n.by)}` : ""}`,
        n.kind === "risk" && esc(n.detail),
        n.kind === "alert" && `Tác động ước tính <b class="${signClass(n.value)}">${vnd(n.value, true)}</b> · xác suất ${pct(n.probability, false, 0)} · ${esc(n.status_label)}`,
        n.kind === "event" && `Tác động kỳ vọng 3 tháng <b class="${signClass(n.value)}">${vnd(n.value, true)}</b>${n.approved_at ? ` · CIO duyệt ${new Date(n.approved_at * 1000).toLocaleDateString("vi-VN")}` : ""}`,
        n.kind === "event" && n.outlets && n.outlets.length && `Nguồn: ${n.outlets.map(esc).join(", ")}`,
        n.kind === "alert" && n.source_text && `Nguồn: ${esc(n.source_text)}`,
      ].filter(Boolean);
      el.innerHTML = `<div class="row tight"><span class="ic-chip" style="--tone:${LOOK[n.kind][0]}">${icon(n.kind === "class" ? CLASS_ICON[n.ref] || "layers" : LOOK[n.kind][1], {size: 16})}</span>
          <div><div class="small muted">${esc(KIND[n.kind])}</div><b>${esc(n.label)}</b></div>
          <button type="button" class="linkbtn small" id="m-clear" style="margin-left:auto">Bỏ chọn</button></div>
        ${facts.map(f => `<p class="small mt-xs">${f}</p>`).join("")}
        <div class="row tight mt">
          ${kids ? `<button type="button" class="btn sm" id="m-open">${st.open.has(n.id) ? "Thu gọn" : `Mở rộng ${kids} khoản`}</button>` : ""}
          ${n.kind === "event" ? `<button type="button" class="btn sm primary" data-go="${esc(n.id)}">Xem đường đi của tin ${icon("arrow", {size: 14})}</button>`
            : `<button type="button" class="btn sm" data-go="${esc(n.id)}">Mở trang ${icon("arrow", {size: 14})}</button>`}</div>
        <h3 class="mt">Liên kết <span class="hint">${es.length}</span></h3>
        <div class="mlist">${es.map(e => { const o = other(e, n.id); return `<button type="button" class="mrow" data-n="${esc(o.id)}">
          <span class="ic-chip sm" style="--tone:${LOOK[o.kind][0]}">${icon(LOOK[o.kind][1], {size: 13})}</span>
          <span><b>${esc(short(o.label, 60))}</b><span class="small muted">${esc(e.label)} · ${srcText(e)}</span></span>
          <span class="num ${e.label === WORDING ? signClass(e.value) : ""}">${e.value == null ? "" : e.label === WORDING ? vnd(e.value, true) : vnd(Math.abs(e.value))}</span></button>`; }).join("")}</div>`;
      $("#m-clear", box).onclick = () => select(null);
      const open = $("#m-open", box);
      if (open) open.onclick = () => toggle(n.id);
    }
    for (const b of el.querySelectorAll("[data-n]")) b.onclick = () => { st.sel = null; select(b.dataset.n); };
    for (const b of el.querySelectorAll("[data-go]")) b.onclick = () => { const x = byId[b.dataset.go]; ctx.go(route[x.kind], focusOf(x)); };
  };
  // ── the radial view ─────────────────────────────────────────────────────────────────────────────
  const layout = (W, H) => {
    const cx = W / 2, cy = H / 2, rx = W / 2 - 150, ry = H / 2 - 44, pos = {ME: {x: cx, y: cy, a: 0}};
    const at = (deg, r) => ({x: cx + Math.cos(deg * Math.PI / 180) * rx * r, y: cy + Math.sin(deg * Math.PI / 180) * ry * r, a: deg});
    for (const [kind, [a0, a1, r0]] of Object.entries(SECTOR)) {
      const r = kind === "class" && st.open.size ? 0.6 : r0;  // an open class's holdings need the outer ring
      const list = g.nodes.filter(n => n.kind === kind && shown(n));
      // at the bottom, neighbours alternate between two rings so their labels (under them) do not meet
      const ring = (i) => (STAGGER.has(kind) && i % 2 ? r - 0.16 : r);
      list.forEach((n, i) => {
        pos[n.id] = {...at(list.length === 1 ? (a0 + a1) / 2 : a0 + (a1 - a0) * i / (list.length - 1), ring(i)), inner: ring(i) < r};
      });
    }
    for (const cid of st.open) {  // a class's holdings fan out behind it, the class stepping inward to make room
      const kids = g.nodes.filter(n => n.parent === cid && shown(n)), p = pos[cid];
      if (!p) continue;
      Object.assign(p, at(p.a, 0.45));
      const spread = Math.min(8, 64 / Math.max(1, kids.length));
      kids.forEach((n, i) => { pos[n.id] = at(p.a + (i - (kids.length - 1) / 2) * spread, 1.08); });
    }
    return pos;
  };

  const drawGraph = (el) => {
    const W = Math.max(640, Math.round(el.clientWidth || 860)), H = 620;
    const pos = layout(W, H);
    const es = shownEdges();
    const lit = st.sel ? new Set([st.sel, ...links(st.sel).map(e => other(e, st.sel).id)]) : null;
    const maxV = Math.max(1, ...es.filter(e => e.value != null).map(e => Math.abs(e.value)));
    const svg = mk("svg", {class: "viz mapsvg", viewBox: `0 0 ${W} ${H}`, role: "group", "aria-label": "Bản đồ tài chính"});
    const defs = mk("defs", {}, svg);
    const grad = mk("radialGradient", {id: "m-me"}, defs);
    mk("stop", {offset: "0", "stop-color": "#8b76ff"}, grad);
    mk("stop", {offset: "1", "stop-color": "#4a36c4"}, grad);
    for (const e of es) {
      const a = pos[e.from], b = pos[e.to];
      if (!a || !b) continue;
      const on = !lit || (lit.has(e.from) && lit.has(e.to) && (e.from === st.sel || e.to === st.sel));
      const potential = e.label === WORDING;
      const p = mk("line", {x1: a.x, y1: a.y, x2: b.x, y2: b.y, class: `medge${on && lit ? " on" : ""}`,
        "stroke-width": e.value == null ? 1.2 : 1.2 + 3.5 * Math.abs(e.value) / maxV,
        "stroke-dasharray": potential ? "5 4" : null, opacity: on ? null : 0.12}, svg);
      hover(p, `${esc(byId[e.from].label)} → ${esc(byId[e.to].label)}<br>${esc(e.label)}${e.value == null ? "" : " · " + vnd(e.value, potential)}<br><span class="muted">${srcText(e)}</span>`);
    }
    for (const n of g.nodes) {
      const q = pos[n.id];
      if (!q || !shown(n)) continue;
      const on = !lit || lit.has(n.id), me = n.kind === "family", r = me ? 34 : n.kind === "holding" ? 12 : 16;
      const grp = mk("g", {class: `mnode${st.sel === n.id ? " sel" : ""}`, tabindex: 0, role: "button", opacity: on ? 1 : 0.25,
        "aria-label": `${KIND[n.kind]}: ${n.label}`, "aria-pressed": String(st.sel === n.id), "data-n": n.id,
        "data-focus": n.kind === "event" ? `event:${n.ref}` : n.kind === "goal" ? `goal:${n.ref}` : null}, svg);
      const [tone, ic] = LOOK[n.kind];
      if (n.kind === "risk" || (n.kind === "goal" && n.status !== "on_track")) mk("circle", {cx: q.x, cy: q.y, r: r + 5, class: "mhalo", style: `--tone:${n.kind === "goal" && n.status === "at_risk" ? "var(--warning)" : "var(--critical)"}`}, grp);
      mk("circle", {cx: q.x, cy: q.y, r, fill: me ? "url(#m-me)" : "var(--surface)", stroke: me ? "none" : tone, "stroke-width": st.sel === n.id ? 3 : 1.6}, grp);
      const inner = mk("svg", {x: q.x - (me ? 0 : r * 0.55), y: q.y - (me ? 0 : r * 0.55), width: me ? 0 : r * 1.1, height: me ? 0 : r * 1.1,
        viewBox: "0 0 24 24", fill: "none", stroke: tone, "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round"}, grp);
      inner.innerHTML = me ? "" : iconPaths(n.kind === "class" ? CLASS_ICON[n.ref] || ic : ic);
      if (me) { const t = mk("text", {x: q.x, y: q.y + 5, "text-anchor": "middle", class: "mme"}, grp); t.textContent = staff ? "KH" : "Bạn"; }
      if (n.kind === "class" && g.nodes.some(x => x.parent === n.id)) {
        const plus = mk("g", {class: "mplus"}, grp);
        mk("circle", {cx: q.x + r * 0.75, cy: q.y - r * 0.75, r: 8}, plus);
        mk("text", {x: q.x + r * 0.75, y: q.y - r * 0.75 + 3.5, "text-anchor": "middle"}, plus).textContent = st.open.has(n.id) ? "−" : String(n.count);
      }
      // the label sits outward: beside a node on the left or right, under or over one at the bottom or top
      const c = Math.cos(q.a * Math.PI / 180), side = me || n.kind === "risk" ? 0 : Math.abs(c) > 0.42 ? Math.sign(c) : 0;
      // under the node at the bottom, over it at the top; an inner-ring node of a staggered row the other way round
      const below = side === 0 && (me || n.kind === "risk" || (q.y >= H / 2) !== !!q.inner);
      const lx = q.x + side * (r + 7), ly = side ? q.y - 1 : below ? q.y + r + 14 : q.y - r - 20;
      const anchor = side > 0 ? "start" : side < 0 ? "end" : "middle";
      const label = mk("text", {x: lx, y: ly, "text-anchor": anchor, class: `mlbl${me ? " me" : ""}`}, grp);
      // a node outside the selection keeps its mark but not its words: the lit links stay readable
      label.textContent = me ? (staff ? short(n.label, 26) : "") : on ? short(n.label, n.kind === "holding" ? 20 : n.kind === "source" ? 13 : 26) : "";
      if (!me && on && n.kind !== "source" && figure(n)) {  // a source's count is in its tooltip and panel
        const f = mk("text", {x: lx, y: ly + 13, "text-anchor": anchor, class: `mfig ${["event", "alert"].includes(n.kind) ? signClass(n.value) : ""}`}, grp);
        f.textContent = figure(n).replace(/<[^>]+>/g, "");
      }
      hover(grp, `<b>${esc(n.label)}</b><br>${esc(KIND[n.kind])}${figure(n) ? " · " + figure(n) : ""}`);
      grp.addEventListener("click", () => select(n.id));
      grp.addEventListener("dblclick", () => { if (n.kind === "class") toggle(n.id); });
      grp.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); select(n.id); }
        if ((ev.key === "+" || ev.key === "-") && n.kind === "class") { ev.preventDefault(); toggle(n.id); }
      });
    }
    el.replaceChildren(svg);
    const bb = svg.getBBox();  // crop to what is drawn: an empty sector leaves no empty band
    const x0 = Math.min(0, bb.x - 8), x1 = Math.max(W, bb.x + bb.width + 8);
    svg.setAttribute("viewBox", `${x0} ${bb.y - 10} ${x1 - x0} ${bb.height + 20}`);
    const f = st.sel && el.querySelector(`[data-n="${CSS.escape(st.sel)}"]`);
    if (f && document.activeElement && document.activeElement.closest && document.activeElement.closest(".mapsvg")) f.focus({preventScroll: true});
  };

  // ── the list view: the same nodes, grouped by kind, each with its links ──────────────────────────
  const drawList = (el) => {
    el.innerHTML = g.kinds.filter(k => k.kind !== "family" && g.nodes.some(n => n.kind === k.kind && shown(n))).map(k => `
      <div class="mgroup"><div class="subhead"><span class="ic-chip sm" style="--tone:${LOOK[k.kind][0]}">${icon(LOOK[k.kind][1], {size: 13})}</span> ${esc(k.label)}</div>
        <div class="mlist">${g.nodes.filter(n => n.kind === k.kind && shown(n)).map(n => `<button type="button" class="mrow${st.sel === n.id ? " on" : ""}" data-n="${esc(n.id)}"
          ${n.kind === "event" ? `data-focus="event:${esc(n.ref)}"` : ""}>
          <span><b>${esc(n.label)}</b><span class="small muted">${n.kind === "goal" ? `${esc(n.status_label)} · ` : ""}${links(n.id).length} liên kết${n.kind === "class" && g.nodes.some(x => x.parent === n.id) ? ` · ${n.count} khoản` : ""}</span></span>
          <span class="num ${["event", "alert"].includes(n.kind) ? signClass(n.value) : ""}">${n.kind === "goal" ? vnd(n.need) : figure(n)}</span></button>`).join("")}</div></div>`).join("");
    for (const b of el.querySelectorAll("[data-n]")) b.onclick = () => { select(b.dataset.n); if (narrow) $("#m-side", box).scrollIntoView({block: "start", behavior: "smooth"}); };
  };

  const draw = () => {
    for (const b of box.querySelectorAll("[data-v]")) b.setAttribute("aria-pressed", String(b.dataset.v === st.view));
    for (const b of box.querySelectorAll("[data-k]")) b.setAttribute("aria-pressed", String(!st.off.has(b.dataset.k)));
    if (st.sel && !shown(byId[st.sel])) st.sel = null;
    const el = $("#m-body", box);
    (st.view === "graph" ? drawGraph : drawList)(el);
    side();
  };
  for (const b of box.querySelectorAll("[data-v]")) b.onclick = () => { st.view = b.dataset.v; draw(); };
  for (const b of box.querySelectorAll("[data-k]")) b.onclick = () => { const k = b.dataset.k; st.off.has(k) ? st.off.delete(k) : st.off.add(k); draw(); };
  draw();
}
