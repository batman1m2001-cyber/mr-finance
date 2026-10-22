/* Agent — the Agent Ecosystem Map (A7, ADR-0033; OWN-AS-20…22), then the agent checklist (BRD FR-703,
   AGENT_CHECKLIST_PLAN C3), the three evaluations and AI quality (RULE-MEAS-04). The map is one endpoint (GET /api/agents/map): the person, the assistant and its tools, the data,
   the CIO desk, the rules and the background agents; each line is something the code does (its file and symbol are
   in the drawer), each state is what the part's runs recorded. Overview first: select a part to light its lines, open
   it for what it does, its connections and its runs; a run opens its steps (ops, agent nodes or tools — never text).
   On a phone the map is a list per group. */
import {$, $$, ago, drawer, esc, get, n as how, pct, when} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";

const NS = "http://www.w3.org/2000/svg";
const STATE = {active: ["ai", "Đang chạy"], waiting: ["warn", "Đang chờ"], done: ["good", "Hoàn tất"],
  failed: ["bad", "Lỗi"], idle: ["", "Chưa chạy"]};
const TONE = {person: "var(--accent)", front: "var(--ai)", data: "var(--data)", cio: "var(--s7)", rules: "var(--s4)",
  background: "var(--s3)"};
const COLS = [["front"], ["data"], ["cio", "rules", "background"]];  // left to right: a question's way, then behind
const ROLES = "Khách hàng · RM · CIO · Tuân thủ · Chuyên gia · Quản trị";
const MODE = {live: ["good", "Trực tiếp"], mock: ["", "Mô phỏng"], keyword: ["", "Từ khóa (mô phỏng)"],
  template: ["", "Mẫu tất định"], not_built: ["warn", "Chưa xây"]};
const RISK = {"cao": "bad", "trung bình": "warn", "thấp": ""};

const pill = (s) => s ? `<span class="pill ${STATE[s][0]}${s === "active" ? " live" : ""}">${STATE[s][1]}</span>` : "";

function figure(n) {
  if (n.kinds) return `${n.tools} công cụ · ${n.kinds.write} ghi${n.kinds.paid ? ` · ${n.kinds.paid} trả phí` : ""}`;
  if (n.store) return esc(n.store);
  if (n.id === "person") return ROLES;
  const bits = [];
  if (n.waiting) bits.push(`${n.waiting} đang chờ`);
  if (n.day) bits.push(`${n.day.runs} lần/24 giờ${n.day.failed ? ` · ${n.day.failed} lỗi` : ""}`);
  return bits.join(" · ") || "—";
}

const card = (n, group) => `<button type="button" class="eco-node" data-node="${esc(n.id)}" style="--tone:${TONE[group]}"
    aria-label="${esc(n.label)}${n.state ? ": " + STATE[n.state][1] : ""}">
  <span class="ic-chip sm">${icon(n.icon, {size: 14})}</span>
  <span class="eco-t"><b>${esc(n.label)}</b><small>${figure(n)}</small></span>${pill(n.state)}</button>`;

export async function render(box) {
  const [m, d] = await Promise.all([get("/api/agents/map"), get("/api/agents/catalogue?days=7")]);
  const byId = Object.fromEntries(m.nodes.map(n => [n.id, n]));
  const inGroup = (g) => m.nodes.filter(n => n.group === g);
  const group = Object.fromEntries(m.groups.map(g => [g.id, g]));
  const narrow = (box.clientWidth || innerWidth) < 760;
  const counts = Object.fromEntries(Object.keys(STATE).map(s => [s, m.nodes.filter(n => n.state === s).length]));
  const list = checklist(box, d, narrow);
  const lane = (g) => `<section class="eco-lane" style="--tone:${TONE[g]}" aria-label="${esc(group[g].label)}">
      <div class="eco-lh"><b>${esc(group[g].label)}</b><span>${esc(group[g].note)}</span></div>
      ${inGroup(g).map(n => card(n, g)).join("")}</section>`;

  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Hệ sinh thái agent</div>
      <div class="h1">Trợ lý, các agent và luật — đang làm gì</div>
      <div class="lede small">Mỗi đường nối là một chỗ trong mã; trạng thái đọc từ bản ghi các lần chạy, không ước đoán.
        Chọn một phần để xem nó làm gì, nối với đâu và các lần chạy.</div></div></div>
    <div class="panel eco-panel">
      <div class="eco-bar">
        <ol class="eco-flow" aria-label="Đường đi của một câu hỏi">${m.flow.map((f, i) =>
          `<li><button type="button" data-flow="${i}"><b>${i + 1}</b> ${esc(f.step)}<small>${esc(f.note)}</small></button></li>`).join("")}</ol>
        <div class="eco-legend">${Object.entries(STATE).map(([k]) => `${pill(k)} <span class="num">${counts[k]}</span>`).join(" ")}
          <span class="small muted">· cập nhật ${when(m.as_of)}</span>
          <button type="button" class="btn ghostbtn sm" data-refresh>Làm mới</button></div>
      </div>
      ${narrow ? `<div class="eco-list">${m.groups.map(g => `<div class="mgroup"><div class="subhead"><span class="legend-dot" style="background:${TONE[g.id]}"></span><b>${esc(g.label)}</b><span class="small muted">${esc(g.note)}</span></div>
          <div class="mlist">${inGroup(g.id).map(n => card(n, g.id)).join("")}</div></div>`).join("")}</div>`
        : `<div class="eco" id="eco">
          <div class="eco-person">${card(byId.person, "person")}</div>
          ${COLS.map(c => `<div class="eco-col">${c.map(lane).join("")}</div>`).join("")}
          <svg class="eco-wires" aria-hidden="true"></svg></div>`}
      <div class="footnote">Trạng thái: Đang chạy — có lần chạy chưa xong; Đang chờ — trong hàng đợi, chờ người xác nhận
        hoặc chờ điều kiện; Hoàn tất / Lỗi — lần chạy gần nhất; Chưa chạy — chưa có lần nào. Lần chạy theo lịch đọc từ bản
        ghi của job (.operonx/jobs) và vết của nó; lượt hỏi trợ lý từ nhật ký kiểm toán, không lưu câu chữ.</div>
    </div>
    ${list.html}
    ${quality(d)}`;
  list.wire();

  $$("[data-node]", box).forEach(b => {
    b.onclick = () => openNode(byId[b.dataset.node], m, byId);
    b.onmouseenter = b.onfocus = () => light(box, m, new Set([b.dataset.node]));
    b.onmouseleave = b.onblur = () => light(box, m, null);
  });
  $$("[data-flow]", box).forEach(b => {
    b.onmouseenter = b.onfocus = () => light(box, m, new Set(m.flow[+b.dataset.flow].nodes), true);
    b.onmouseleave = b.onblur = () => light(box, m, null);
    b.onclick = () => light(box, m, new Set(m.flow[+b.dataset.flow].nodes), true);
  });
  $("[data-refresh]", box).onclick = () => render(box);
  const eco = $("#eco", box);
  if (eco) {
    wires(eco, m);
    const ro = new ResizeObserver(() => { if (!eco.isConnected) return ro.disconnect(); wires(eco, m); });
    ro.observe(eco);
  }
}

/* -- the lines: from the side facing the other part; within one column, along its outer gutter -------------------- */

function wires(eco, m) {
  const svg = $(".eco-wires", eco);
  const box = eco.getBoundingClientRect();
  svg.setAttribute("viewBox", `0 0 ${box.width} ${box.height}`);
  svg.setAttribute("width", box.width);
  svg.setAttribute("height", box.height);
  const head = (id) => `<marker id="${id}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L8,4 L0,8 z"/></marker>`;
  svg.innerHTML = `<defs>${head("eco-arrow")}${head("eco-arrow-on")}</defs>`;
  const rect = (id) => {
    const r = $(`[data-node="${id}"]`, eco).getBoundingClientRect();
    return {l: r.left - box.left, r: r.right - box.left, t: r.top - box.top, b: r.bottom - box.top,
      x: (r.left + r.right) / 2 - box.left, y: (r.top + r.bottom) / 2 - box.top};
  };
  const colOf = (id) => { const c = $(`[data-node="${id}"]`, eco).closest(".eco-col"); return c ? [...eco.children].indexOf(c) : -1; };
  const gutter = {};  // per column and side: how many lines run there already, so they do not overlap
  for (const e of m.edges) {
    const a = rect(e.from), b = rect(e.to), ca = colOf(e.from), cb = colOf(e.to);
    let d;
    if (e.from === "person" || e.to === "person") {
      const toPerson = e.to === "person", p = toPerson ? b : a, q = toPerson ? a : b, other = toPerson ? ca : cb;
      if (other === 3) {  // the right-hand column: round its outer side, so no line crosses a card
        const k = gutter.p = (gutter.p || 0) + 1, gx = Math.max(p.r, q.r) + 10 + 9 * k;
        const [s, t] = toPerson ? [q, p] : [p, q];
        d = `M${s.r},${s.y} C${gx},${s.y} ${gx},${s.y} ${gx},${(s.y + t.y) / 2} S${gx},${t.y} ${t.r},${t.y}`;
      } else {  // straight down from the person to the top of its column
        const qx = q.r - 28, sx = Math.min(Math.max(qx, p.l + 16), p.r - 16), ym = (p.b + q.t) / 2;  // beside the lane's label
        d = toPerson ? `M${qx},${q.t} C${qx},${ym} ${sx},${ym} ${sx},${p.b}` : `M${sx},${p.b} C${sx},${ym} ${qx},${ym} ${qx},${q.t}`;
      }
    } else if (ca === cb) {
      const right = ca === 3, side = right ? "r" : "l", k = gutter[side + ca] = (gutter[side + ca] || 0) + 1;
      const gx = right ? Math.max(a.r, b.r) + 8 + 9 * k : Math.min(a.l, b.l) - 8 - 9 * k;
      d = `M${a[side]},${a.y} C${gx},${a.y} ${gx},${a.y} ${gx},${(a.y + b.y) / 2} S${gx},${b.y} ${b[side]},${b.y}`;
    } else {
      const fwd = cb > ca, x1 = fwd ? a.r : a.l, x2 = fwd ? b.l : b.r, mx = (x1 + x2) / 2;
      d = `M${x1},${a.y} C${mx},${a.y} ${mx},${b.y} ${x2},${b.y}`;
    }
    const p = document.createElementNS(NS, "path");
    p.setAttribute("d", d);
    p.setAttribute("class", "eco-wire");
    p.dataset.from = e.from;
    p.dataset.to = e.to;
    const t = document.createElementNS(NS, "title");
    t.textContent = e.label;
    p.appendChild(t);
    svg.appendChild(p);
  }
}

function light(box, m, ids, path) {
  const on = (e) => ids && (path ? ids.has(e.dataset.from) && ids.has(e.dataset.to) : ids.has(e.dataset.from) || ids.has(e.dataset.to));
  const near = new Set(ids || []);
  if (ids && !path) for (const e of m.edges) if (ids.has(e.from) || ids.has(e.to)) { near.add(e.from); near.add(e.to); }
  $$(".eco-wire", box).forEach(w => { w.classList.toggle("on", !!on(w)); w.classList.toggle("dim", !!ids && !on(w)); });
  $$(".eco-node", box).forEach(n => n.classList.toggle("dim", !!ids && !near.has(n.dataset.node)));
}

/* -- drill-down: a part, then one of its runs --------------------------------------------------------------------- */

async function openNode(n, m, byId) {
  const body = drawer(n.label, `<div class="small muted">Đang tải…</div>`);
  const ins = m.edges.filter(e => e.to === n.id), outs = m.edges.filter(e => e.from === n.id);
  const line = (e, dir) => `<li><span class="muted">${dir}</span> <b>${esc(byId[dir === "→" ? e.to : e.from].label)}</b> — ${esc(e.label)}<div class="eco-code">${esc(e.code)}</div></li>`;
  const facts = [
    n.state ? ["Trạng thái", `${pill(n.state)} <span class="small muted">${n.at ? `lần gần nhất ${ago(n.at)} (${when(n.at)})` : ""}</span>`] : null,
    n.reads ? ["Được đọc", esc(n.reads)] : null,
    n.resource ? ["Mô hình", `${esc(n.model || "chưa cấu hình — chạy luật / mô phỏng")} <span class="small muted">· ${esc(n.resource)}</span>`] : null,
    n.jobs ? ["Job", n.jobs.map(esc).join(", ")] : null,
    n.cost != null ? ["Chi phí 24 giờ", `US$${n.cost.toFixed(5)}`] : null,
  ].filter(Boolean);
  const head = `<p style="margin:0">${esc(n.does)}</p>
    ${facts.length ? `<table class="table"><tbody>${facts.map(([k, v]) => `<tr><td class="muted">${k}</td><td>${v}</td></tr>`).join("")}</tbody></table>` : ""}
    <div><h4 class="eco-h">Nối với</h4><ul class="eco-links">${ins.map(e => line(e, "←")).join("")}${outs.map(e => line(e, "→")).join("")}</ul></div>`;
  if (n.state == null) { body.innerHTML = head; return; }
  let r;
  try { r = await get(`/api/agents/map/${encodeURIComponent(n.id)}`); } catch (e) { body.innerHTML = head + `<div class="small">${esc(e.message)}</div>`; return; }
  const runRows = (rows) => rows.length ? `<table class="table eco-runs"><thead><tr><th>Lúc</th><th>Lần chạy</th><th></th><th class="r">ms</th></tr></thead><tbody>
      ${rows.map(x => `<tr data-run="${esc(x.id)}" tabindex="0"><td class="num small">${when(x.at)}</td><td><b class="small">${esc(x.title)}</b><div class="small muted">${esc(x.sub || "")}</div></td><td>${pill(x.state)}</td><td class="r num small">${x.ms == null ? "—" : x.ms}</td></tr>`).join("")}</tbody></table>`
    : `<div class="small muted">Chưa có lần chạy nào.</div>`;
  const tools = r.tools ? `<div><h4 class="eco-h">Công cụ (${r.tools.length})</h4><table class="table"><tbody>${r.tools.map(t =>
      `<tr><td><b class="small">${esc(t.label)}</b><div class="eco-code">${esc(t.name)}</div></td><td>${t.write ? `<span class="pill warn">ghi, cần xác nhận</span>` : `<span class="pill">đọc</span>`}${t.paid ? ` <span class="pill">trả phí</span>` : ""}</td><td class="small muted">${esc(t.roles.join(", "))}</td></tr>`).join("")}</tbody></table></div>` : "";
  const convs = r.conversations ? `<div><h4 class="eco-h">Hội thoại đã tổng hợp</h4>${runRows(r.conversations).replace(/ data-run="[^"]*" tabindex="0"/g, "")}</div>` : "";
  body.innerHTML = head + tools + `<div><h4 class="eco-h">Lần chạy gần nhất</h4>${runRows(r.runs)}</div>` + convs;
  $$("[data-run]", body).forEach(tr => {
    const go = () => openRun(n, tr.dataset.run, m, byId);
    tr.onclick = go;
    tr.onkeydown = (e) => { if (e.key === "Enter") go(); };
  });
}

async function openRun(n, runId, m, byId) {
  const body = drawer(`${n.label} · ${runId}`, `<div class="small muted">Đang tải…</div>`);
  let r;
  try { r = await get(`/api/agents/map/${encodeURIComponent(n.id)}?run=${encodeURIComponent(runId)}`); } catch (e) { body.innerHTML = esc(e.message); return; }
  const steps = (xs) => `<table class="table"><tbody>${xs.map(s => `<tr><td><b class="small">${esc(s.name)}</b>${s.note ? `<div class="small muted">${esc(s.note)}</div>` : ""}</td><td>${pill(s.status)}</td><td class="r num small">${s.ms == null ? "—" : s.ms + " ms"}</td></tr>`).join("")}</tbody></table>`;
  const back = `<button type="button" class="btn ghostbtn sm eco-back" data-back>← ${esc(n.label)}</button>`;
  const run = r.run || {};
  const facts = [["Lúc", when(run.at)], ["Trạng thái", pill(r.state)],
    run.mode ? ["Chế độ", esc(run.mode)] : null, run.model ? ["Mô hình", esc(run.model)] : null,
    run.role ? ["Vai trò", esc(run.role)] : null, run.tokens != null ? ["Token", run.tokens] : null,
    run.cost_usd != null ? ["Chi phí", `US$${(+run.cost_usd).toFixed(5)}`] : null,
    run.subject ? ["Đối tượng", esc(run.subject)] : null, run.audit_seq ? ["Nhật ký", `#${run.audit_seq}`] : null,
    run.counts ? ["Mục", `${run.counts.ok || 0} ổn · ${run.counts.failed || 0} lỗi`] : null].filter(Boolean);
  body.innerHTML = `${back}<table class="table"><tbody>${facts.map(([k, v]) => `<tr><td class="muted">${k}</td><td>${v}</td></tr>`).join("")}</tbody></table>
    ${r.kind === "job" ? r.items.map(it => `<details class="eco-item" ${it.state === "failed" ? "open" : ""}><summary>${pill(it.state)} <b class="small">${esc(it.key)}</b> <span class="small muted">${it.ms} ms · vết ${esc((it.trace || "").slice(0, 8))}</span></summary>${steps(it.steps)}</details>`).join("")
      : `<div><h4 class="eco-h">${r.kind === "turn" ? "Công cụ đã gọi" : "Các bước"}</h4>${r.steps.length ? steps(r.steps) : `<div class="small muted">Không có bước nào.</div>`}</div>`}
    <div class="footnote">Chỉ tên bước, trạng thái và thời gian — không có lời nhắc, câu hỏi hay câu trả lời.</div>`;
  $("[data-back]", body).onclick = () => openNode(n, m, byId);
}

/* -- the checklist (AGENT_CHECKLIST_PLAN C3, FR-703): every part that calls a model, one name each; "Của tôi" is the
   parts the person's role owns; then the three evaluations with their latest result, and AI quality ---------------- */

const OWNED = {cio: "CIO", compliance: "Tuân thủ", admin: "Quản trị"};

function checklist(box, d, narrow) {
  const role = (location.hash.split("/")[1] || "").replace(/\W/g, "");
  const mine = d.agents.filter(a => (a.owner_roles || []).includes(role));
  const evalName = Object.fromEntries(d.evaluations.map(e => [e.id, e.name]));
  const agentName = Object.fromEntries(d.agents.map(a => [a.id, a.name]));
  const mode = (a) => `<span class="badge ${MODE[a.mode] ? MODE[a.mode][0] : ""}">${esc(MODE[a.mode] ? MODE[a.mode][1] : a.mode)}</span>`;
  const measured = (a) => a.measured.length ? a.measured.map(id => esc(evalName[id])).join(", ") : `<span class="muted">chưa đo</span>`;
  const rows = (xs) => narrow
    ? `<div class="mlist">${xs.map(a => `<button type="button" class="ag-card" data-agent="${esc(a.id)}">
        <span class="ag-h"><b>${esc(a.name)}</b>${mode(a)}</span><span class="small">${esc(a.purpose)}</span>
        <span class="small muted">${esc(a.owner)} · đo bằng: ${measured(a)}</span></button>`).join("")}</div>`
    : `<table class="table ag-table" data-cols="6"><thead><tr><th>Tên</th><th>Làm gì</th><th>Chủ sở hữu</th><th>Mô hình hiện tại</th><th>Đo bằng</th><th>Chạy khi</th></tr></thead><tbody>
        ${xs.map(a => `<tr class="click" data-agent="${esc(a.id)}" tabindex="0"><td><b>${esc(a.name)}</b><div class="small muted">${esc(a.name_en)}</div></td>
          <td class="small">${esc(a.purpose)}</td><td class="small">${esc(a.owner)}</td>
          <td>${mode(a)}<div class="small muted">${esc(a.model)}</div></td><td class="small">${measured(a)}</td><td class="small muted">${esc(a.runs)}</td></tr>`).join("")}</tbody></table>`;
  const latest = (e) => e.latest
    ? `<span class="badge ${e.latest.passed ? "good" : "bad"}">${e.latest.passed ? "Đạt" : "Không đạt"}</span> <span class="small">${esc(e.latest.summary)}</span>`
    : `<span class="small muted">chưa có lần chạy nào</span>`;
  const evals = `<div class="panel"><h3>Ba cách đo <span class="hint">mỗi cách một tên; không gọi chung là "benchmark"</span></h3>
    ${narrow ? `<div class="mlist">${d.evaluations.map(e => `<div class="ag-card"><span class="ag-h"><b>${esc(e.name)}</b></span>
        <span class="small">${esc(e.checks)}</span><span class="small muted">${esc(e.when)}</span><span>${latest(e)}</span>
        ${e.page ? `<a class="small" href="${esc(e.page)}">Mở trang →</a>` : ""}</div>`).join("")}</div>`
      : `<table class="table ag-table"><thead><tr><th>Tên</th><th>Kiểm tra gì</th><th>Đo agent</th><th>Khi nào</th><th>Lần gần nhất</th></tr></thead><tbody>
        ${d.evaluations.map(e => `<tr><td><b>${esc(e.name)}</b><div class="small muted">${esc(e.name_en)}</div>${e.page ? `<a class="small" href="${esc(e.page)}">Mở trang →</a>` : ""}</td>
          <td class="small">${esc(e.checks)}</td><td class="small">${e.agents.map(id => esc(agentName[id] || id)).join(", ")}</td>
          <td class="small muted">${esc(e.when)}</td><td>${latest(e)}</td></tr>`).join("")}</tbody></table>`}</div>`;
  const html = `
    <div class="pagehead" style="margin-top:28px"><div><div class="eyebrow">Danh sách agent</div>
      <div class="h1">${d.agents.length} phần dùng mô hình ngôn ngữ — mỗi phần một tên</div>
      <div class="lede small">Mọi chỗ ứng dụng gọi mô hình đều ở đây (một kiểm thử chặn chỗ mới không có tên). Chọn một dòng để
        xem nó đọc gì, ai kiểm tra, cấu hình và mã nguồn (BRD FR-703). Phiên bản lời nhắc ${esc(d.prompt_version)}.</div></div>
      ${mine.length ? `<div class="seg" role="group" aria-label="Lọc danh sách"><button type="button" data-mine="0" aria-pressed="true">Tất cả ${d.agents.length}</button><button type="button" data-mine="1" aria-pressed="false">Của tôi (${esc(OWNED[role] || role)}) ${mine.length}</button></div>` : ""}</div>
    <div class="panel" data-agents>${rows(d.agents)}</div>
    ${evals}`;
  const wire = (root) => {
    $$("[data-agent]", root).forEach(el => {
      const go = () => openAgent(d.agents.find(a => a.id === el.dataset.agent), d);
      el.onclick = go;
      el.onkeydown = (e) => { if (e.key === "Enter") go(); };
    });
  };
  return {html, wire: () => {
    wire(box);
    $$("[data-mine]", box).forEach(b => b.onclick = () => {
      $$("[data-mine]", box).forEach(x => x.setAttribute("aria-pressed", String(x === b)));
      const list = $("[data-agents]", box);
      list.innerHTML = rows(b.dataset.mine === "1" ? mine : d.agents);
      wire(list);
    });
  }};
}

function openAgent(a, d) {
  const evalName = Object.fromEntries(d.evaluations.map(e => [e.id, e.name]));
  const run = a.latest_run;
  const facts = [
    ["Làm gì", esc(a.purpose)],
    ["Chủ sở hữu", esc(a.owner)],
    ["Mức rủi ro", `<span class="badge ${RISK[a.risk] || ""}">${esc(a.risk)}</span> <span class="small">${esc(a.risk_why)}</span>`],
    ["Mô hình hiện tại", `<span class="badge ${MODE[a.mode] ? MODE[a.mode][0] : ""}">${esc(MODE[a.mode] ? MODE[a.mode][1] : a.mode)}</span> ${esc(a.model)}`],
    ["Cấu hình", (a.settings || []).map(esc).join(", ") || "— (không gọi mô hình)"],
    ["Mô hình theo BRD", esc(a.brd_model)],
    ["Được đọc", esc(a.reads)],
    ["Ai kiểm tra", esc(a.checks)],
    ["Đo bằng", a.measured.length ? a.measured.map(id => esc(evalName[id])).join(", ") : "chưa đo"],
    ["Chạy khi", esc(a.runs)],
    ["Lần chạy gần nhất", run ? `${esc(run.id)} · ${esc(run.subject)} · ${when(run.at)} · ${esc(run.mode)} · ${esc(run.status)}` : "—"],
  ];
  drawer(a.name, `<table class="table"><tbody>${facts.map(([k, v]) => `<tr><td class="muted">${k}</td><td class="small">${v}</td></tr>`).join("")}</tbody></table>
    ${a.parts ? `<div><h4 class="eco-h">Gồm cả</h4><ul class="small">${a.parts.map(x => `<li>${esc(x)}</li>`).join("")}</ul></div>` : ""}
    ${a.code.length ? `<div><h4 class="eco-h">Mã nguồn</h4>${a.code.map(f => `<div class="eco-code">${esc(f)}</div>`).join("")}</div>` : ""}`);
}

function quality(d) {
  const q = d.quality;
  const fig = (k, label, f = (x) => x) => `<tr><td>${label}</td><td class="r num">${q.recent[k] == null ? "—" : f(q.recent[k])}</td><td class="r num muted">${q.all_time[k] == null ? "—" : f(q.all_time[k])}</td></tr>`;
  return `
    <div class="cols">
      <div class="panel c6"><h3>Chất lượng AI <span class="hint">${q.days} ngày qua · từ đầu</span></h3>
        <table class="table"><thead><tr><th></th><th class="r">${q.days} ngày</th><th class="r">Từ đầu</th></tr></thead><tbody>
          ${fig("decided", "Nhận định đã quyết")}${fig("edited_share", "Tỷ lệ CIO sửa kịch bản", (x) => how(pct(x, false, 0), "agent.edited_share"))}
          ${fig("findings", "Phát hiện của phản biện")}${fig("critical_findings", "— trong đó nghiêm trọng")}
          ${fig("agent_runs", "Lần chạy agent")}${fig("failed_runs", "— lỗi")}${fig("format_retries", "Viết lại vì sai định dạng")}
        </tbody></table><div class="footnote">Đếm từ dữ liệu đã lưu (nhận định, phản biện, lần chạy agent); BRD §16.3.</div></div>
      <div class="panel c6"><h3>Tham khảo mã nguồn mở</h3>
        <ul>${d.references.map(r => `<li><b>${esc(r.name)}</b> (${esc(r.license)}): ${esc(r.use)}</li>`).join("")}</ul></div>
    </div>`;
}
