/* Thông tin — the workspace's inspector (FEAT-40, OWN-GW-03): the selected node's figures with their “Cách tính”,
   its links with the records they were read from, and the sheets that show it in full; with nothing selected, what
   the lens looks at first. Built from the overview page's side panel (map.js). */
import {n as how, esc, pct, signClass, vnd} from "../core/core.js";
import {CLASS_ICON, icon} from "../core/icons.js?v=20261016r1";
import {LOOK, certaintyOf, figureOf, howOf, srcText} from "./graph.js?v=20261017u2";
import {SHEETS} from "./lenses.js?v=20261017w3";

const short = (s, k) => (s.length > k ? s.slice(0, k - 1) + "…" : s);
const titled = {event: "data-quote", alert: "data-explains"};  // a news event's title is the outlets' words
const nameOf = (n, text) => (n.id === "RK:drawdown" ? how(text, "risk.current") : titled[n.kind] ? `<span ${titled[n.kind]}>${text}</span>` : text);
const fig = (n, text) => (n.kind === "source" || !text ? text : how(text, ...howOf(n)));
const CERT_WORD = {actual: "thực tế", estimate: "ước tính", hypothetical: "giả định"};
// which sheet shows a kind in full
const SHEET_OF = {family: "chi-tiet", class: "tai-san", holding: "tai-san", source: "tai-san", goal: "ke-hoach", scenario: "ke-hoach",
  risk: "chi-tiet", liquidity: "chi-tiet", alert: "chinh-sach", event: "do-thi", flow: "toan-canh"};

export function render(el, {graph, lens, node, kindLabel, openSheet, runScenario}) {
  const n = node;
  const sheetBtns = (ids) => ids.map(id => `<button type="button" class="btn sm" data-sheet="${id}">${esc(SHEETS[id].label)} ${icon("arrow", {size: 14})}</button>`).join("");
  if (!n) {
    const g = graph.data();
    if (!g) { el.innerHTML = ""; return; }
    let body = "";
    if (lens.id === "tin" || lens.id === "tong-quan") {
      const moving = g.nodes.filter(x => ["event", "alert"].includes(x.kind)).sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
      body = `<h3>Tin tức & chính sách <span class="hint">theo mức tác động</span></h3>${list(moving)}`;
    } else {
      const pick = {"tai-san": ["class"], "dong-tien": ["flow", "liquidity"], "muc-tieu": ["goal", "scenario"], "rui-ro": ["risk", "liquidity"]}[lens.id] || [];
      const rows = g.nodes.filter(x => pick.includes(x.kind));
      body = `<h3>${esc(lens.label)} <span class="hint">${rows.length}</span></h3>${list(rows)}`;
    }
    el.innerHTML = `<div class="ws-ins-lens">${body}
      <p class="small muted">Bấm một nút trên đồ thị để xem số liệu, liên kết và nguồn của nó.</p>
      <div class="ws-ins-sheets"><div class="small muted">Xem đầy đủ</div><div class="row tight">${sheetBtns(lens.sheets)}</div></div></div>`;
  } else {
    const es = graph.links(n.id);
    const g = graph.data();
    const kids = n.kind === "class" && lens.kinds.includes("holding") ? g.nodes.filter(x => x.parent === n.id).length : 0;  // only where holdings show
    const facts = [
      n.kind === "family" && `Tài sản ròng <b>${fig(n, vnd(n.value))}</b> · tài sản ${how(vnd(n.assets), "assets.total")} · nợ ${how(vnd(n.liabilities), "liabilities.total")}`,
      n.kind === "class" && `${n.liability ? "Dư nợ" : "Giá trị"} <b>${fig(n, vnd(n.value))}</b> · ${n.count} khoản`,
      n.kind === "holding" && `Giá trị <b>${fig(n, vnd(n.value))}</b>${n.owner ? ` · ${esc(n.owner)}` : ""}`,
      n.kind === "source" && `${esc(n.what)} · ${n.count} khoản · ${esc((n.trust || []).join(", "))}`,
      n.kind === "goal" && `Cần <b>${how(vnd(n.need), "goal.need")}</b> · đang có ${how(vnd(n.have), "goal.have")} · ${n.gap > 0 ? `thiếu ${how(vnd(n.gap), "goal.gap", {need: vnd(n.need), have: vnd(n.have)})}` : "đủ"}${n.by ? ` · mốc ${esc(n.by)}` : ""}`,
      n.kind === "risk" && `${fig(n, vnd(Math.abs(n.value)))} · <span data-explains>${esc(n.detail)}</span>`,
      n.kind === "alert" && `Tác động ước tính <b class="${signClass(n.value)}">${fig(n, vnd(n.value, true))}</b> · xác suất ${how(pct(n.probability, false, 0), "policy.probability")} · ${esc(n.status_label)}`,
      n.kind === "event" && `Tác động kỳ vọng 3 tháng <b class="${signClass(n.value)}">${fig(n, vnd(n.value, true))}</b>${n.approved_at ? ` · CIO duyệt ${new Date(n.approved_at * 1000).toLocaleDateString("vi-VN")}` : ""}`,
      n.kind === "event" && n.outlets && n.outlets.length && `Nguồn: ${n.outlets.map(esc).join(", ")}`,
      n.kind === "alert" && n.source_text && `Nguồn: ${esc(n.source_text)}`,
      n.kind === "flow" && `${n.side === "in" ? "Tiền vào" : "Tiền ra"} tháng ${esc(n.month || "")} <b>${fig(n, vnd(Math.abs(n.value)))}</b> · từ giao dịch đã ghi nhận`,
      n.kind === "flow" && (n.items || []).length && `Lớn nhất: ${n.items.slice(0, 3).map(i => `${esc(i.label)} ${vnd(Math.abs(i.value))}`).join(" · ")}`,
      n.kind === "flow" && n.rows && `${n.rows} giao dịch · <span class="cert c-actual">thực tế</span>`,
      n.kind === "liquidity" && (n.items || []).length && `Gồm: ${n.items.slice(0, 3).map(i => `${esc(i.label)} ${vnd(i.value)}`).join(" · ")}`,
      n.kind === "liquidity" && `Tài sản thanh khoản <b>${fig(n, vnd(n.value))}</b>${n.months != null ? ` · đủ chi tiêu <b>${String(n.months).replace(".", ",")} tháng</b> (mốc an toàn 6 tháng)` : ""}`,
      n.kind === "scenario" && `<span class="pill">giả định</span> ${esc(n.detail || "")}`,
      n.kind === "scenario" && (n.value == null ? `Chưa chạy: kết quả không thay đổi tài sản thực của bạn.` : `Nếu xảy ra: <b class="${signClass(n.value)}">${vnd(n.value, true)}</b> — chỉ là ước tính, không cộng vào tài sản ròng.`),
      n.kind === "scenario" && (n.summary || []).length && `<span class="ws-sum">${n.summary.map(l => `<span>${esc(l.label)}</span><b class="${{bad: "down", good: "up"}[l.tone] || ""}">${esc(l.value)}</b>`).join("")}</span>`,
    ].filter(Boolean);
    const look = n.kind === "flow" && n.side === "out" ? ["var(--out)", "cart"] : LOOK[n.kind] || LOOK.class;
    const kindTone = look[0];
    const sheet = SHEET_OF[n.kind];
    el.innerHTML = `<div class="row tight"><span class="ic-chip" style="--tone:${kindTone}">${icon(n.kind === "class" ? CLASS_ICON[n.ref] || "layers" : look[1], {size: 16})}</span>
        <div><div class="small muted">${esc(kindLabel(n.kind))}</div><b>${nameOf(n, esc(n.label))}</b></div>
        <button type="button" class="linkbtn small" id="ws-clear" style="margin-left:auto">Bỏ chọn</button></div>
      ${facts.map(f => `<p class="small mt-xs">${f}</p>`).join("")}
      <div class="row tight mt">
        ${kids ? `<button type="button" class="btn sm" id="ws-open">${graph.isOpen(n.id) ? "Thu gọn" : `Mở rộng ${kids} khoản`}</button>` : ""}
        ${n.kind === "scenario" && runScenario ? `<button type="button" class="btn sm primary" id="ws-run">${n.value == null ? "Chạy kịch bản" : "Chạy lại"}</button>` : ""}
        ${n.kind === "event" ? `<button type="button" class="btn sm primary" data-sheet="do-thi" data-param="${esc(n.ref)}" data-focus-key="event:${esc(n.ref)}">Xem đường đi của tin ${icon("arrow", {size: 14})}</button>`
          : sheet ? `<button type="button" class="btn sm" data-sheet="${sheet}">Mở ${esc(SHEETS[sheet].label)} ${icon("arrow", {size: 14})}</button>` : ""}</div>
      <h3 class="mt">Liên kết <span class="hint">${es.length}</span></h3>
      <div class="mlist">${es.map(e => { const o = graph.other(e, n.id); const cert = certaintyOf(e, Object.fromEntries(g.nodes.map(x => [x.id, x]))); return `<button type="button" class="mrow" data-n="${esc(o.id)}">
        <span class="ic-chip sm" style="--tone:${(LOOK[o.kind] || LOOK.class)[0]}">${icon((LOOK[o.kind] || LOOK.class)[1], {size: 13})}</span>
        <span><b>${nameOf(o, esc(short(o.label, 60)))}</b><span class="small muted">${esc(e.label)} · <span class="cert c-${cert}">${CERT_WORD[cert]}</span> · ${srcText(e)}</span></span>
        <span class="num ${cert !== "actual" ? signClass(e.value) : ""}">${e.value == null ? "" : vnd(cert !== "actual" ? e.value : Math.abs(e.value), cert !== "actual")}</span></button>`; }).join("")}</div>`;
    el.querySelector("#ws-clear").onclick = () => graph.select(null);
    const open = el.querySelector("#ws-open");
    if (open) open.onclick = () => graph.toggle(n.id);
    const run = el.querySelector("#ws-run");
    if (run) run.onclick = () => runScenario(n, run);
  }
  for (const b of el.querySelectorAll("[data-n]")) b.onclick = () => graph.select(b.dataset.n);
  for (const b of el.querySelectorAll("[data-sheet]")) b.onclick = () => openSheet(b.dataset.sheet, b.dataset.param || null, b.dataset.focusKey ? [b.dataset.focusKey] : null);

  function list(rows) {
    return `<div class="mlist">${rows.map(x => `<button type="button" class="mrow" data-n="${esc(x.id)}">
      <span class="ic-chip sm" style="--tone:${(LOOK[x.kind] || LOOK.class)[0]}">${icon((LOOK[x.kind] || LOOK.class)[1], {size: 13})}</span>
      <span><b>${nameOf(x, esc(short(x.label, 70)))}</b><span class="small muted">${esc(x.kind === "event" ? "Tin tức · CIO duyệt" : x.status_label || kindLabel(x.kind))}</span></span>
      <span class="num ${["event", "alert", "scenario"].includes(x.kind) ? signClass(x.value) : ""}">${esc(figureOf(x))}</span></button>`).join("") || `<p class="muted small">Chưa có mục nào.</p>`}</div>`;
  }
}
