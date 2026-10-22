/* Thông tin — the workspace's inspector (FEAT-40, OWN-GW-03): the selected node's figures with their “Cách tính”,
   its links with the records they were read from, and the sheets that show it in full; with nothing selected, what
   the lens looks at first. Built from the overview page's side panel (map.js). */
import {formulaOf, n as how, esc, pct, post, signClass, vnd} from "../core/core.js";
import {timeline as drawTimeline} from "../charts/charts.js";
import {CLASS_ICON, icon} from "../core/icons.js?v=20261016r1";
import {LOOK, UNIT_WORD, certaintyOf, changeOf, changeText, changeTone, changeWord, figureOf, howOf, srcText} from "./graph.js?v=20261021t6";
import {PARTS, SHEETS} from "./lenses.js?v=20261022p1";
import {drawFeed} from "./feed.js?v=20261021t5";

const short = (s, k) => (s.length > k ? s.slice(0, k - 1) + "…" : s);
const titled = {event: "data-quote", alert: "data-explains"};  // a news event's title is the outlets' words
const nameOf = (n, text) => (n.id === "RK:drawdown" ? how(text, "risk.current") : titled[n.kind] ? `<span ${titled[n.kind]}>${text}</span>` : text);
const fig = (n, text) => (n.kind === "source" || !text ? text : how(text, ...howOf(n)));
const CERT_WORD = {actual: "thực tế", estimate: "ước tính", hypothetical: "giả định"};
// which page shows a kind in full, or which section of the Bảng số liệu (UX_TOOLBAR_PLAN T3+T4)
const SHEET_OF = {class: "tai-san", holding: "tai-san", source: "tai-san", goal: "ke-hoach", scenario: "ke-hoach", alert: "chinh-sach", event: "do-thi"};
const PART_OF = {category: "month", flow: "month", family: "nw", risk: "risk", liquidity: "liq"};

// the person's own what-if (F5, scenarios._sim.CUSTOM_LIMITS): each input a percentage, within the server's bounds
const CUSTOM = [["real_estate", "Bất động sản", -50, 50], ["stock", "Cổ phiếu và quỹ cổ phiếu", -50, 50], ["gold", "Vàng", -50, 50],
  ["rate", "Lãi vay thả nổi tăng (điểm %)", 0, 5], ["income", "Thu nhập hằng tháng", -50, 50]];
const SRC_WORD = {holding: "Khoản", risk: "Rủi ro", goal: "Mục tiêu", alert: "Chính sách", run: "Lần áp dụng tin", txn: "Giao dịch tháng", scenario: "Kịch bản"};
const GOAL_WORD = {on_track: "Đúng tiến độ", at_risk: "Cần chú ý", off_track: "Chậm tiến độ"};
// a node's money over time (NODE_TIMELINE_PLAN T4): the kinds that hold or move money, each fetched once per unit
const MONEY = new Set(["family", "class", "holding", "liquidity", "flow", "category"]);
const UNITS = [["day", "Ngày"], ["month", "Tháng"], ["year", "Năm"]];
const RANGE = {day: "90 ngày gần nhất", month: "từng tháng từ 2021", year: "từng năm từ 2021"};
const STEP = {day: "so với hôm trước", month: "so với tháng trước", year: "so với năm trước"};
const TONE = {up: "up", down: "down", out: "down", flat: ""};
const timelines = new Map();  // client|scope|node|unit → the promise of its points

export function render(el, {graph, lens, node, edge, kindLabel, openSheet, board, feed, client, scenario, timeline, page}) {
  const n = node;
  if (!n && !edge && page) {  // a page of its own is open (Chuyên gia, Bộ nhớ): nothing of the lens to say beside it
    el.innerHTML = `<div class="ws-ins-lens"><h3>${esc(page)}</h3><p class="small muted">Thông tin hiện số liệu, liên kết và nguồn của một nút trên đồ thị.
      Đóng trang ${esc(page)} để quay về đồ thị.</p></div>`;
    return;
  }
  if (!n && edge) { drawEdge(edge); wire(); return; }
  if (!n) {
    const g = graph.data();
    if (!g) { el.innerHTML = ""; return; }
    let body = "";
    if (lens.id === "tong-quan") {  // what Toàn cảnh led with: the feed, the most important first (T4)
      el.innerHTML = `<div class="ws-ins-lens"><div id="ws-feed"></div>
        <p class="small muted">Bấm một nút trên đồ thị để xem số liệu, liên kết và nguồn của nó.</p></div>`;
      drawFeed(el.querySelector("#ws-feed"), feed, {client, board});
      return;
    }
    if (lens.id === "tin") {
      const moving = g.nodes.filter(x => ["event", "alert"].includes(x.kind)).sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
      body = `<h3>Tin tức & chính sách <span class="hint">theo mức tác động</span></h3>${list(moving)}`;
    } else {
      const pick = {"tai-san": ["class"], "dong-tien": ["flow", "liquidity"], "muc-tieu": ["goal", "scenario"], "rui-ro": ["risk", "liquidity"]}[lens.id] || [];
      const rows = g.nodes.filter(x => pick.includes(x.kind));
      body = `<h3>${esc(lens.label)} <span class="hint">${rows.length}</span></h3>${lens.id === "muc-tieu" ? goalsTotal(g) : ""}${list(rows)}${lens.id === "tai-san" ? sourceList(g) : ""}`;
    }
    el.innerHTML = `<div class="ws-ins-lens">${body}
      <p class="small muted">Bấm một nút trên đồ thị để xem số liệu, liên kết và nguồn của nó.</p></div>`;
  } else {
    const es = graph.links(n.id);
    const g = graph.data();
    const kid = {class: "holding", flow: "category"}[n.kind];  // what it opens to, only where the lens shows those
    const kids = kid && lens.kinds.includes(kid) ? g.nodes.filter(x => x.parent === n.id && x.kind === kid).length : 0;
    const facts = [
      n.kind === "family" && `Tài sản ròng <b>${fig(n, vnd(n.value))}</b> · tài sản ${how(vnd(n.assets), "assets.total")} · nợ ${how(vnd(n.liabilities), "liabilities.total")}`,
      n.kind === "class" && `${n.liability ? "Dư nợ" : "Giá trị"} <b>${fig(n, vnd(n.value))}</b> · ${n.count} khoản`,
      n.kind === "class" && sourcesOf(n).length && `Nguồn: ${sourcesOf(n).map(([s, k]) => `${srcBtn(s)} · ${k} khoản`).join(" · ")}`,
      n.kind === "holding" && `Giá trị <b>${fig(n, vnd(n.value))}</b>${n.owner ? ` · ${esc(n.owner)}` : ""}`,
      n.kind === "source" && `${esc(n.what)} · ${n.count} khoản · ${esc((n.trust || []).join(", "))}`,
      n.kind === "goal" && n.pool && `<span data-explains>Nguồn ${esc(n.pool.label || n.have_label || "")}</span> ${how(vnd(n.pool.have), "goal.have")} dùng chung cho ${n.pool.goals.length} mục tiêu: tính một lần, không cộng dồn`,
      n.kind === "goal" && n.monthly > 0 && n.gap > 0 && `Cần để dành <b>${how(vnd(n.monthly), "goal.monthly", {need: vnd(n.need), have: vnd(n.have)})}</b>/tháng · bạn dư ${how(vnd(n.surplus || 0), "goal.surplus")}/tháng`,
      n.kind === "goal" && `Cần <b>${how(vnd(n.need), "goal.need")}</b> · đang có ${how(vnd(n.have), "goal.have")} · ${n.gap > 0 ? `thiếu ${how(vnd(n.gap), "goal.gap", {need: vnd(n.need), have: vnd(n.have)})}` : "đủ"}${n.by ? ` · mốc ${esc(n.by)}` : ""}`,
      n.kind === "risk" && `${fig(n, vnd(Math.abs(n.value)))} · <span data-explains>${esc(n.detail)}</span>`,
      n.kind === "alert" && `Tác động ước tính <b class="${signClass(n.value)}">${fig(n, vnd(n.value, true))}</b> · xác suất ${how(pct(n.probability, false, 0), "policy.probability")} · ${esc(n.status_label)}`,
      n.kind === "event" && `Tác động kỳ vọng 3 tháng <b class="${signClass(n.value)}">${fig(n, vnd(n.value, true))}</b>${n.approved_at ? ` · CIO duyệt ${new Date(n.approved_at * 1000).toLocaleDateString("vi-VN")}` : ""}`,
      n.kind === "event" && n.outlets && n.outlets.length && `Nguồn: ${n.outlets.map(esc).join(", ")}`,
      n.kind === "alert" && n.source_text && `Nguồn: ${esc(n.source_text)}`,
      n.kind === "flow" && `${n.side === "in" ? "Tiền vào" : "Tiền ra"} tháng ${esc(n.month || "")} <b>${fig(n, vnd(Math.abs(n.value)))}</b> · từ giao dịch đã ghi nhận`,
      n.kind === "flow" && (n.items || []).length && `Lớn nhất: ${n.items.slice(0, 3).map(i => `${esc(i.label)} ${vnd(Math.abs(i.value))}`).join(" · ")}`,
      n.kind === "flow" && n.rows && `${n.rows} giao dịch · <span class="cert c-actual">thực tế</span>`,
      n.kind === "category" && `${n.side === "in" ? "Tiền vào" : "Tiền ra"} tháng ${esc(n.month || "")} <b>${fig(n, vnd(Math.abs(n.value)))}</b> · ${n.rows} giao dịch · <span class="cert c-actual">thực tế</span>`,
      n.kind === "category" && (n.owners || []).length > 1 && `Của: ${n.owners.map(esc).join(", ")}`,
      n.kind === "liquidity" && (n.items || []).length && `Gồm: ${n.items.slice(0, 3).map(i => `${esc(i.label)} ${vnd(i.value)}`).join(" · ")}`,
      n.kind === "liquidity" && `Tài sản thanh khoản <b>${fig(n, vnd(n.value))}</b>${n.months != null ? ` · đủ chi tiêu <b>${String(n.months).replace(".", ",")} tháng</b> (mốc an toàn 6 tháng)` : ""}`,
      n.kind === "scenario" && `<span class="pill">giả định</span> ${esc(n.detail || "")}`,
      n.kind === "scenario" && (n.value == null ? `Chưa bật: kết quả không thay đổi tài sản thực của bạn.`
        : `${n.active ? "Phần của kịch bản này" : "Nếu xảy ra"}: <b class="${signClass(n.value)}">${vnd(n.value, true)}</b> — giả định, không cộng vào tài sản ròng.`),
      n.kind === "scenario" && (n.summary || []).length && `<span class="ws-sum">${n.summary.map(l => `<span>${esc(l.label)}</span><b class="${{bad: "down", good: "up"}[l.tone] || ""}">${esc(l.value)}</b>`).join("")}</span>`,
    ].filter(Boolean);
    const look = (n.kind === "flow" || n.kind === "category") && n.side === "out" ? ["var(--out)", "cart"] : LOOK[n.kind] || LOOK.class;
    const kindTone = look[0];
    const sheet = SHEET_OF[n.kind], part = PART_OF[n.kind];
    el.innerHTML = `<div class="row tight"><span class="ic-chip" style="--tone:${kindTone}">${icon(n.kind === "class" ? CLASS_ICON[n.ref] || "layers" : look[1], {size: 16})}</span>
        <div><div class="small muted">${esc(kindLabel(n.kind))}</div><b>${nameOf(n, esc(n.label))}</b></div>
        <button type="button" class="linkbtn small" id="ws-clear" style="margin-left:auto">Bỏ chọn</button></div>
      ${facts.map(f => `<p class="small mt-xs">${f}</p>`).join("")}${n.kind === "class" ? `<div id="ws-src"></div>` : ""}
      <div class="row tight mt">
        ${kids ? `<button type="button" class="btn sm" id="ws-open">${graph.isOpen(n.id) ? "Thu gọn" : `Mở rộng ${kids} ${kid === "category" ? "khoản thu chi" : "khoản"}`}</button>` : ""}
        ${n.kind === "scenario" && scenario && n.ref !== "custom" ? `<button type="button" class="btn sm ${n.active ? "" : "primary"}" id="ws-run" aria-pressed="${!!n.active}">${n.active ? "Tắt kịch bản" : "Bật kịch bản"}</button>` : ""}
        ${n.kind === "event" ? `<button type="button" class="btn sm primary" data-sheet="do-thi" data-param="${esc(n.ref)}" data-focus-key="event:${esc(n.ref)}">Xem đường đi của tin ${icon("arrow", {size: 14})}</button>`
          : sheet ? `<button type="button" class="btn sm" data-sheet="${sheet}">Mở ${esc(SHEETS[sheet].label)} ${icon("arrow", {size: 14})}</button>`
          : part && board ? `<button type="button" class="btn sm" data-board="${part}"${n.month ? ` data-month="${esc(n.month)}"` : ""}>Xem ${esc(PARTS[part].toLowerCase())} trong Bảng số liệu ${icon("arrow", {size: 14})}</button>` : ""}</div>
      ${MONEY.has(n.kind) && timeline ? timelineBlock(n) : ""}
      ${n.kind === "scenario" && scenario && n.ref === "custom" ? customForm(n) : ""}
      ${n.kind === "scenario" && n.active ? trace(n) : ""}
      <h3 class="mt">Liên kết <span class="hint">${es.length}</span></h3>
      <div class="mlist">${es.map(e => { const o = graph.other(e, n.id); const cert = certaintyOf(e, Object.fromEntries(g.nodes.map(x => [x.id, x]))); return `<button type="button" class="mrow" data-n="${esc(o.id)}">
        <span class="ic-chip sm" style="--tone:${(LOOK[o.kind] || LOOK.class)[0]}">${icon((LOOK[o.kind] || LOOK.class)[1], {size: 13})}</span>
        <span><b>${nameOf(o, esc(short(o.label, 60)))}</b><span class="small muted">${esc(e.label)} · <span class="cert c-${cert}">${CERT_WORD[cert]}</span> · ${srcText(e)}</span></span>
        <span class="num ${cert !== "actual" ? signClass(e.value) : ""}">${e.value == null ? "" : vnd(cert !== "actual" ? e.value : Math.abs(e.value), cert !== "actual")}</span></button>`; }).join("")}</div>`;
    el.querySelector("#ws-clear").onclick = () => graph.select(null);
    const open = el.querySelector("#ws-open");
    if (open) open.onclick = () => graph.toggle(n.id);
    if (MONEY.has(n.kind) && timeline) loadTimeline(n);
    const run = el.querySelector("#ws-run");
    if (run) run.onclick = () => { run.disabled = true; scenario.set(n.ref, !n.active); };
    const form = el.querySelector("#ws-what");
    if (form) {
      form.onsubmit = (ev) => {
        ev.preventDefault();
        const p = {};
        for (const [k, , lo, hi] of CUSTOM) {
          const v = Math.min(hi, Math.max(lo, Number(form.elements[k].value) || 0));
          if (v) p[k] = +(v / 100).toFixed(4);
        }
        if (!Object.keys(p).length) { form.querySelector(".ws-what-msg").textContent = "Nhập ít nhất một thay đổi."; return; }
        form.querySelector("button[type=submit]").disabled = true;
        scenario.set("custom", true, p);
      };
      const off = form.querySelector("[data-off]");
      if (off) off.onclick = () => { off.disabled = true; scenario.set("custom", false); };
    }
  }
  wire();

  // ── Diễn biến (T4): the change over the period picked, the chart, and its numbers as a table
  function timelineBlock(n) {
    const u = timeline.unit, v = changeOf(n, u);
    const say = v == null ? "" : `<p class="small mt-xs">${{day: "Hôm nay", month: "Tháng này", year: "Năm nay"}[u]}: <b class="${TONE[changeTone(n, v)]}">${changeText(v)}</b> ${esc(changeWord(n, u))}</p>`;
    return `<section class="ws-tl" aria-labelledby="ws-tl-h">
      <div class="ws-tl-head"><h3 id="ws-tl-h">Diễn biến <span class="pill" title="Lịch sử trước hôm nay là dữ liệu mô phỏng cho bản demo">mô phỏng</span></h3>
        <div class="seg" role="group" aria-label="Bước thời gian">${UNITS.map(([k, l]) => `<button type="button" data-tl="${k}" aria-pressed="${k === u}" title="${esc(UNIT_WORD[k])}">${l}</button>`).join("")}</div></div>
      ${say}
      <div class="ws-tl-chart" id="ws-tl-chart" aria-busy="true"><div class="skeleton" style="height:150px"></div></div>
      <p class="small muted" id="ws-tl-range"></p>
      <details class="more"><summary>Xem bảng số</summary><div class="scrollx" id="ws-tl-table"></div></details></section>`;
  }
  function loadTimeline(n) {
    const {client, scope, unit: u} = timeline, key = `${client}|${scope}|${n.id}|${u}`;
    for (const b of el.querySelectorAll("[data-tl]")) b.onclick = () => timeline.setUnit(b.dataset.tl);
    if (!timelines.has(key)) {
      const p = post("/api/timeline", {client_id: client, scope, node: n.id, unit: u}).then(r => r.timeline);
      p.catch(() => timelines.delete(key));  // a failure is tried again next time
      timelines.set(key, p);
    }
    const box = el.querySelector("#ws-tl-chart");
    timelines.get(key).then(t => {
      if (!box.isConnected) return;  // another pick drew the pane since
      box.removeAttribute("aria-busy");
      const ps = t.points, a = ps[0], z = ps[ps.length - 1];
      const flow = t.kind === "flow", total = ps.reduce((x, p) => x + p.value, 0);
      drawTimeline(box, t, {label: `${t.label}: ${RANGE[u]}`, versus: STEP[u]});
      el.querySelector("#ws-tl-range").innerHTML = flow
        ? `${esc(RANGE[u][0].toUpperCase() + RANGE[u].slice(1))}: tổng <b>${vnd(total, true)}</b> · ${esc(t.note)}`
        : `${esc(a.label)} → ${esc(z.label)}: ${vnd(a.value)} → <b>${vnd(z.value)}</b> (<span class="${signClass((t.liability ? -1 : 1) * (z.value - a.value))}">${vnd(z.value - a.value, true)}</span>) · ${esc(t.note)}`;
      el.querySelector("#ws-tl-table").innerHTML = `<table class="table small"><thead><tr><th>Kỳ</th><th class="r">${flow ? "Số tiền" : "Giá trị"}</th>${flow ? "" : `<th class="r">Thay đổi</th>`}</tr></thead><tbody>
        ${[...ps].reverse().map(p => `<tr><td>${esc(p.label)}</td><td class="r">${vnd(p.value, flow)}</td>${flow ? "" : `<td class="r">${changeText(p.change)}</td>`}</tr>`).join("")}</tbody></table>`;
    }).catch(e => { if (box.isConnected) { box.removeAttribute("aria-busy"); box.innerHTML = `<p class="small muted" role="alert">Không tải được diễn biến: ${esc(e.message || "")}</p>`; } });
  }

  function wire() {
    for (const b of el.querySelectorAll("[data-n]")) b.onclick = () => graph.select(b.dataset.n);
    for (const b of el.querySelectorAll("[data-sheet]")) b.onclick = () => openSheet(b.dataset.sheet, b.dataset.param || null, b.dataset.focusKey ? [b.dataset.focusKey] : null);
    for (const b of el.querySelectorAll("[data-board]")) b.onclick = () => board(b.dataset.board, b.dataset.month || null);
    for (const b of el.querySelectorAll("[data-src]")) b.onclick = () => {  // what came from a source, under it
      const box = el.querySelector("#ws-src"), id = b.dataset.src;
      if (!box) return;
      const open_ = box.dataset.src !== id;
      box.dataset.src = open_ ? id : "";
      box.innerHTML = open_ ? fromSource(id) : "";
      for (const x of el.querySelectorAll("[data-src]")) x.setAttribute("aria-expanded", String(x.dataset.src === box.dataset.src));
    };
  }

  // ── where the data comes from (T6): the sources are not on the ring; they are told beside the numbers ────────────
  function sourcesOf(cls) {  // [source node, holdings of this class it gave]
    const g = graph.data(), out = new Map();
    for (const e of g.edges) {
      const s = graph.node(e.from);
      if (s && s.kind === "source" && e.parent === cls.id) out.set(s, (out.get(s) || 0) + 1);
    }
    return [...out].sort((a, b) => b[1] - a[1]);
  }
  function srcBtn(s) {
    return `<button type="button" class="linkbtn small" data-src="${esc(s.id)}" aria-expanded="false" aria-controls="ws-src">${esc(s.label)}</button>`;
  }
  function sourceList(g) {
    const ss = g.nodes.filter(x => x.kind === "source");
    if (!ss.length) return "";
    const on = ss.filter(s => s.status === "connected").length;
    return `<h3 class="mt">Nguồn dữ liệu <span class="hint">${ss.length} nguồn · ${on} đã kết nối</span></h3>
      <div class="ws-srcs">${ss.map(s => `<div class="small"><span class="${s.status === "connected" ? "up" : "muted"}" aria-hidden="true">${s.status === "connected" ? "✓" : "○"}</span>
        ${srcBtn(s)} <span class="muted">· ${s.count} khoản · ${esc(s.what || "")}</span></div>`).join("")}</div><div id="ws-src"></div>`;
  }
  function fromSource(id) {  // the holdings a source gave, by class
    const g = graph.data(), s = graph.node(id);
    const hs = g.edges.filter(e => e.from === id && String(e.to).startsWith("HD:")).map(e => graph.node(e.to)).filter(Boolean);
    return `<div class="ws-srcbox"><b>${esc(s.label)}</b> <span class="small muted">${esc(s.what || "")} · ${esc((s.trust || []).join(", "))}</span>
      <table class="table small mt-xs"><tbody>${hs.map(h => `<tr><td>${esc(h.label)}</td><td class="r num">${fig(h, vnd(h.value))}</td></tr>`).join("")}</tbody></table></div>`;
  }

  // ── an edge picked (UNIFIED_FLOWS_PLAN F9, OWN-GW-46): what it joins and says, its amount and monthly rate, its
  // certainty, the records it was read from, how it is computed, its assumptions, its confidence where one is
  // recorded (none is invented), and what it reaches downstream
  function drawEdge(e) {
    const A = graph.node(e.from), B = graph.node(e.to), g = graph.data();
    if (!A || !B) { el.innerHTML = ""; return; }
    const cert = certaintyOf(e, {[A.id]: A, [B.id]: B});
    const kinds = [A.kind, B.kind], has = (k) => kinds.includes(k), far = A.id === "ME" ? B : A;
    const type = has("scenario") ? "scenario" : has("event") || (far.kind === "group" && far.of === "event") ? "event"
      : has("alert") ? "alert" : has("goal") ? "goal" : has("category") ? "category" : has("flow") ? "flow" : far.kind;
    const node = (k) => g.nodes.find(x => x.kind === k && kinds.includes(x.kind) && (x.id === A.id || x.id === B.id));
    const ev = node("event"), al = node("alert"), sc = node("scenario"), gl = node("goal"), fl = node("flow") || node("category");
    const [metric, inputs] = {
      event: ["impact.expected_3m", {event: ev ? ev.label : ""}], alert: ["policy.impact", al ? {probability: pct(al.probability, false, 0)} : {}],
      scenario: [e.cost ? "scenario.cost" : "scenario.effect", {scenario: sc ? sc.label : ""}],
      goal: ["goal.monthly", gl ? {need: vnd(gl.need), have: vnd(gl.have), ...(gl.pool ? {pool: vnd(gl.pool.have)} : {})} : {}],
      category: ["flow.category", {rows: String((node("category") || {}).rows || "")}], flow: [fl && fl.side === "out" ? "flow.out" : "flow.in", {}],
      class: ["class.value", {}], holding: ["holding.value", {}], liquidity: ["liquidity.value", {}], risk: ["risk.loss", {}],
    }[type] || [null, {}];
    const monthlyMetric = {event: "impact.monthly", goal: "goal.monthly", scenario: "scenario.cost"}[type] || metric;
    const signed = cert !== "actual";
    const money = (x, m = metric, i = inputs) => (m ? how(vnd(x, signed), m, i) : vnd(x, signed));
    const [src, dst] = e.dir === "back" ? [B, A] : [A, B];
    const amount = type === "goal" ? (e.value != null ? `Cần để dành <b>${how(vnd(e.value), metric, inputs)}</b>/tháng` : "Không cần để dành thêm") : [
      e.value != null && `${{event: "Tác động ước tính", alert: "Tác động ước tính", scenario: e.cost ? "Chi phí giả định một năm" : "Nếu xảy ra"}[type] || "Số tiền"} <b class="${signed ? signClass(e.value) : ""}">${money(e.value)}</b>`,
      e.monthly != null && e.monthly !== Math.abs(e.value) && `~<b>${how(vnd(e.monthly), monthlyMetric, inputs)}</b>/tháng`,
      e.repaid && `trả trong tháng <b>${how(vnd(e.repaid), "transaction.amount")}</b>`,
    ].filter(Boolean).join(" · ");
    const once = e.monthly == null && e.value != null ? " · một lần, không phải hằng tháng" : "";
    // a spoke to money (T3): its change over the period picked, as the edge shows it
    const dv = (A.id === "ME" || B.id === "ME") && timeline && ["class", "liquidity", "flow"].includes(far.kind) ? changeOf(far, timeline.unit) : null;
    const moved = dv == null ? "" : `Thay đổi <b class="${TONE[changeTone(far, dv)]}">${changeText(dv)}</b> ${esc(changeWord(far, timeline.unit))}${far.kind === "flow" ? "" : " · lịch sử mô phỏng"}`;
    const flowWords = !e.dir ? "Quan hệ: không có tiền chuyển"
      : cert === "actual" ? `Tiền đi: ${esc(src.label)} → ${esc(dst.label)}${once}`
        : `Chiều của dòng: ${esc(src.label)} → ${esc(dst.label)} · ${CERT_WORD[cert]}, không phải giao dịch${once}`;
    // the records, each linked to its node where the graph has one
    const NODE = {holding: "HD", risk: "RK", goal: "GL", alert: "AL", scenario: "SC"};
    const srcNode = (s) => (NODE[s.type] && graph.node(`${NODE[s.type]}:${s.id}`)) || (s.type === "run" && g.nodes.find(x => x.run === s.id))
      || (s.type === "txn" && graph.node(fl ? fl.id : "FL:out")) || null;
    const records = (e.sources || []).slice(0, 8).map(s => { const t = srcNode(s); return t
      ? `<button type="button" class="linkbtn small" data-n="${esc(t.id)}">${esc(SRC_WORD[s.type] || s.type)}: ${esc(short(t.label, 48))}</button>`
      : `<span class="small">${esc(SRC_WORD[s.type] || s.type)}: ${esc(s.id)}</span>`; }).join("<br>");
    const more = (e.sources || []).length > 8 ? `<br><span class="small muted">và ${(e.sources || []).length - 8} bản ghi khác</span>` : "";
    // assumptions, and confidence only where it is recorded
    const assume = {
      event: ev && `Theo nhận định CIO duyệt${ev.approved_at ? ` ngày ${new Date(ev.approved_at * 1000).toLocaleDateString("vi-VN")}` : ""}, tầm nhìn 3 tháng; nhịp mỗi tháng = tác động ÷ 3`,
      alert: al && `${esc(al.status_label || "")}${al.source_text ? ` · ${esc(al.source_text)}` : ""}`,
      scenario: sc && (sc.part ? (sc.part.assumptions || []).map(esc).join(" · ") : `${esc(sc.detail || "")} · chưa bật`),
      goal: gl && `Lãi tiền gửi ${gl.rate != null ? pct(gl.rate, false, 1) : "an toàn"}/năm${gl.by ? ` · đến ${esc(gl.by)}` : ""} · còn thiếu ${how(vnd(Math.max(0, gl.gap)), "goal.gap", {need: vnd(gl.need), have: vnd(gl.have)})}`,
    }[type] || (cert === "actual" ? "Không có giả định: số liệu đã ghi nhận" : "");
    const band = ev && ev.band ? `P10 ${how(vnd(ev.band.p10, true), "impact.band")} · P50 ${how(vnd(ev.band.p50, true), "impact.band")} · P90 ${how(vnd(ev.band.p90, true), "impact.band")}` : "";
    const conf = type === "event" ? [band, ev && ev.modelled_share != null ? `${how(pct(ev.modelled_share, false, 0), "impact.modelled_share")} tài sản tính bằng đại diện (càng lớn càng kém chắc)` : ""].filter(Boolean).join(" · ")
      : type === "alert" && al ? `Xác suất ${how(pct(al.probability, false, 0), "policy.probability")}`
        : cert === "actual" ? "Đã ghi nhận (giao dịch, số dư từ nguồn đã kết nối hoặc đã khai báo)" : "Không có độ tin cậy được ghi nhận cho mục này";
    el.innerHTML = `<div class="row tight"><span class="ic-chip" style="--tone:${(LOOK[far.kind] || LOOK.class)[0]}">${icon("link", {size: 16})}</span>
        <div><div class="small muted">Liên kết · <span class="cert c-${cert}">${CERT_WORD[cert]}</span></div>
          <b>${nameOf(A, esc(short(A.label, 40)))} → ${nameOf(B, esc(short(B.label, 40)))}</b></div>
        <button type="button" class="linkbtn small" id="ws-clear" style="margin-left:auto">Bỏ chọn</button></div>
      <p class="small mt-xs">${esc(e.label)}${e.derived ? ` · tổng hợp từ ${e.derived} liên kết` : ""}</p>
      ${amount ? `<p class="small mt-xs">${amount}</p>` : ""}
      ${moved ? `<p class="small mt-xs">${moved}</p>` : ""}
      <p class="small mt-xs">${flowWords}</p>
      <dl class="ws-edge">
        <dt>Nguồn</dt><dd>${records || `<span class="small muted">Không có bản ghi</span>`}${more}</dd>
        ${metric ? `<dt>Cách tính</dt><dd class="small" data-explains><span data-formula="${esc(metric)}">…</span> ${how("Xem chi tiết", metric, inputs)}</dd>` : ""}
        <dt>Giả định</dt><dd class="small">${assume || "—"}</dd>
        <dt>Độ tin cậy</dt><dd class="small">${conf}</dd>
        <dt>Ảnh hưởng tiếp theo</dt><dd class="small">${downstream(type, {ev, al, sc, gl, fl, A, B, e})}</dd>
      </dl>`;
    el.querySelector("#ws-clear").onclick = () => graph.selectEdge(`${e.from}>${e.to}`);
    const f = el.querySelector("[data-formula]");
    if (f) formulaOf(f.dataset.formula).then(m => { if (f.isConnected) f.textContent = m ? m.formula : "Chưa có cách tính cho mục này."; });
  }
  function downstream(type, {ev, al, sc, gl, fl, A, B, e}) {
    const g = graph.data(), label = (id) => esc((graph.node(id) || {label: id}).label);
    const classesOf = (id) => g.edges.filter(x => x.from === id && (graph.node(x.to) || {}).kind === "class" && x.value != null)
      .map(x => `${label(x.to)} <b class="${signClass(x.value)}">${vnd(x.value, true)}</b>`);
    if (type === "event" && ev) return `${classesOf(ev.id).join(" · ") || "—"} → Tài sản ròng: ước tính <b class="${signClass(ev.value)}">${vnd(ev.value, true)}</b> trong 3 tháng, không cộng vào tài sản ròng. Mục tiêu: xem “Kế hoạch”.`;
    if (type === "alert" && al) return `${classesOf(al.id).join(" · ") || "Nhiều lớp tài sản: chưa có số chia theo lớp"} → Tài sản ròng: ước tính <b class="${signClass(al.value)}">${vnd(al.value, true)}</b>, không cộng vào tài sản ròng.`;
    if (type === "scenario" && sc) {
      const r = graph.combined();
      if (!sc.active || !r) return "Bật kịch bản để xem nó đi tới đâu: lớp tài sản, chi tiêu, thanh khoản, tài sản ròng và mục tiêu.";
      const goals = r.goals.filter(x => x.before.status !== x.after.status).map(x => `${esc(x.title)}: ${GOAL_WORD[x.after.status] || x.after.status}`);
      return `${e.cost ? `Chi tiêu mỗi tháng +${vnd(e.cost.amount / 12)} → thanh khoản đủ ${r.after.liquid_months.toFixed(1).replace(".", ",")} tháng` : label(B.id)} → Tài sản ròng nếu xảy ra ${how(vnd(r.after.net_worth), "scenario.combined", {scenarios: r.scenarios.map(x => x.title).join(", ")})}${goals.length ? ` → ${goals.join(" · ")}` : " → mục tiêu không đổi trạng thái"}. Xem “Đường đi của kịch bản” ở nút kịch bản.`;
    }
    if (type === "goal" && gl) {
      const pool = gl.pool ? `Nguồn ${esc(gl.have_label || "")} ${how(vnd(gl.pool.have), "goal.have")} dùng chung cho ${gl.pool.goals.length} mục tiêu (${gl.pool.goals.map(label).join(", ")}): tính một lần, không mục tiêu nào được coi là có tiền mà mục tiêu khác đã tính. ` : "";
      const me = graph.node("ME") || {};
      return `${pool}Cả các mục tiêu cần ${how(vnd(me.goal_monthly || 0), "goals.saving")}/tháng · bạn dư ${how(vnd(me.surplus || 0), "goal.surplus")}/tháng.`;
    }
    if ((type === "flow" || type === "category") && fl) {
      const i = graph.node("FL:in"), o = graph.node("FL:out");
      return `${type === "category" ? `${label(fl.parent)} → ` : ""}Tài sản ròng tháng ${esc(fl.month || "")}: vào ${i ? how(vnd(Math.abs(i.value)), "flow.in") : "—"} − ra ${o ? how(vnd(Math.abs(o.value)), "flow.out") : "—"} = ${i && o ? how(vnd(Math.abs(i.value) - Math.abs(o.value), true), "flow.left") : "—"}.`;
    }
    if (A.id === "ME" || B.id === "ME") return `${(graph.node(A.id === "ME" ? B.id : A.id) || {}).liability ? "Trừ khỏi" : "Cộng vào"} tài sản ròng.`;
    return "—";
  }

  // the person's what-if: their inputs, the server's bounds; running it makes it active like any other
  function customForm(n) {
    const p = scenario.params("custom") || {};
    return `<form class="ws-what mt" id="ws-what" novalidate><h3>Giả định của bạn</h3>
      ${CUSTOM.map(([k, label, lo, hi]) => `<label class="ws-what-r"><span class="small">${esc(label)}</span>
        <span class="row tight"><input type="number" name="${k}" min="${lo}" max="${hi}" step="1" value="${p[k] != null ? Math.round(p[k] * 100) : 0}" inputmode="numeric"> <span class="small muted">${k === "rate" ? "điểm" : "%"}</span></span></label>`).join("")}
      <p class="small muted ws-what-msg">Từ ${CUSTOM[0][2]}% đến +${CUSTOM[0][3]}% (lãi vay 0–5 điểm). Chỉ là giả định: không thay đổi tài sản thực.</p>
      <div class="row tight"><button type="submit" class="btn sm primary">${n.active ? "Tính lại" : "Bật giả định"}</button>
        ${n.active ? `<button type="button" class="btn sm" data-off>Tắt</button>` : ""}</div></form>`;
  }
  // an active scenario's way to the money (OWN-GW-38): its assumptions → the classes it moves → debt and spending →
  // liquidity → projected net worth → the goals; the last three are all the active scenarios together (no double count)
  function trace(n) {
    const r = graph.combined(), s = n.part;
    if (!r || !s) return "";
    const many = r.scenarios.length > 1 ? ` <span class="hint">cùng ${r.scenarios.length} kịch bản đang bật</span>` : "";
    const cls = Object.entries(s.by_class || {}).filter(([, v]) => v).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
    const costs = r.costs.filter(c => c.by === s.id || c.also.includes(s.id));
    const step = (title, body, k) => `<li data-step="${k}"><b>${title}</b><div class="small">${body}</div></li>`;
    const goals = r.goals.filter(x => x.before.status !== x.after.status || Math.abs(x.before.gap - x.after.gap) >= 1);
    const goalLine = (x) => x.before.status !== x.after.status
      ? `${GOAL_WORD[x.before.status] || x.before.status} → <b>${GOAL_WORD[x.after.status] || x.after.status}</b>`
      : `${GOAL_WORD[x.after.status] || x.after.status} · thiếu ${vnd(Math.max(0, x.before.gap))} → <b>${vnd(Math.max(0, x.after.gap))}</b>`;
    return `<h3 class="mt">Đường đi của kịch bản</h3><ol class="ws-trace">
      ${step("Giả định", (s.assumptions || []).map(esc).join(" · ") || "—", "assumptions")}
      ${step("Lớp tài sản", cls.map(([c, v]) => `${esc((graph.node(`CL:${c}`) || {label: c}).label)} <b class="${signClass(v)}">${vnd(v, true)}</b>`).join(" · ") || "Không lớp nào thay đổi", "classes")}
      ${step("Nợ & chi tiêu", costs.map(c => `${esc(c.label)} <b class="down">${vnd(c.amount)}/năm</b> (~${vnd(c.amount / 12)}/tháng vào chi tiêu)${c.by !== s.id ? ` · tính ở “${esc(r.scenarios.find(x => x.id === c.by).title)}”` : c.also.length ? " · tính một lần" : ""}`).join("<br>") || "Không đổi", "costs")}
      ${step(`Thanh khoản${many}`, `${vnd(r.before.liquid)} → <b>${vnd(r.after.liquid)}</b> · đủ ${r.before.liquid_months.toFixed(1).replace(".", ",")} → <b>${r.after.liquid_months.toFixed(1).replace(".", ",")} tháng</b> chi tiêu`, "liquidity")}
      ${step(`Tài sản ròng dự kiến${many}`, `${vnd(r.before.net_worth)} → <b>${vnd(r.after.net_worth)}</b> (<b class="${signClass(r.change)}">${vnd(r.change, true)}</b>; phần của kịch bản này ${vnd(n.value, true)})`, "net_worth")}
      ${step(`Mục tiêu${many}`, goals.map(x => `${esc(x.title)}: ${goalLine(x)}`).join("<br>") || "Không mục tiêu nào đổi trạng thái", "goals")}
    </ol><p class="small muted">${esc(r.note)}</p>`;
  }

  // the goals' monthly saving against the surplus, and each shared pool said once (F3)
  function goalsTotal(g) {
    const me = g.nodes.find(x => x.id === "ME") || {}, pools = new Map();
    for (const x of g.nodes) if (x.kind === "goal" && x.pool) pools.set(Math.round(x.pool.have), x.pool);
    const line = me.goal_monthly ? `<p class="small">Các mục tiêu cần ${how(vnd(me.goal_monthly), "goals.saving", {surplus: vnd(me.surplus || 0)})}/tháng · bạn dư ${how(vnd(me.surplus || 0), "goal.surplus")}/tháng${me.goal_monthly > Math.max(0, me.surplus || 0) ? ` <span class="pill bad">thiếu ${how(vnd(me.goal_monthly - Math.max(0, me.surplus || 0)), "goals.saving")}/tháng</span>` : ""}</p>` : "";
    const shared = [...pools.values()].map(pl => `<p class="small muted"><span data-explains>Nguồn ${esc(pl.label || "")}</span> ${how(vnd(pl.have), "goal.have")} dùng chung cho ${pl.goals.length} mục tiêu: tính một lần.</p>`).join("");
    return line + shared;
  }
  function list(rows) {
    return `<div class="mlist">${rows.map(x => `<button type="button" class="mrow" data-n="${esc(x.id)}">
      <span class="ic-chip sm" style="--tone:${(LOOK[x.kind] || LOOK.class)[0]}">${icon((LOOK[x.kind] || LOOK.class)[1], {size: 13})}</span>
      <span><b>${nameOf(x, esc(short(x.label, 70)))}</b><span class="small muted">${esc(x.kind === "event" ? "Tin tức · CIO duyệt" : x.status_label || (x.liability ? "Nợ" : kindLabel(x.kind)))}</span></span>
      <span class="num ${["event", "alert", "scenario"].includes(x.kind) ? signClass(x.value) : ""}">${esc(figureOf(x))}</span></button>`).join("") || `<p class="muted small">Chưa có mục nào.</p>`}</div>`;
  }
}
