/* Thông tin — the workspace's inspector (FEAT-40, OWN-GW-03): the selected node's figures with their “Cách tính”,
   its links with the records they were read from, and the sheets that show it in full; with nothing selected, what
   the lens looks at first. Built from the overview page's side panel (map.js). */
import {n as how, esc, pct, signClass, vnd} from "../core/core.js";
import {CLASS_ICON, icon} from "../core/icons.js?v=20261016r1";
import {LOOK, certaintyOf, figureOf, howOf, srcText} from "./graph.js?v=20261017u3";
import {SHEETS} from "./lenses.js?v=20261017w3";

const short = (s, k) => (s.length > k ? s.slice(0, k - 1) + "…" : s);
const titled = {event: "data-quote", alert: "data-explains"};  // a news event's title is the outlets' words
const nameOf = (n, text) => (n.id === "RK:drawdown" ? how(text, "risk.current") : titled[n.kind] ? `<span ${titled[n.kind]}>${text}</span>` : text);
const fig = (n, text) => (n.kind === "source" || !text ? text : how(text, ...howOf(n)));
const CERT_WORD = {actual: "thực tế", estimate: "ước tính", hypothetical: "giả định"};
// which sheet shows a kind in full
const SHEET_OF = {family: "chi-tiet", class: "tai-san", holding: "tai-san", source: "tai-san", goal: "ke-hoach", scenario: "ke-hoach",
  risk: "chi-tiet", liquidity: "chi-tiet", alert: "chinh-sach", event: "do-thi", flow: "toan-canh"};

// the person's own what-if (F5, scenarios._sim.CUSTOM_LIMITS): each input a percentage, within the server's bounds
const CUSTOM = [["real_estate", "Bất động sản", -50, 50], ["stock", "Cổ phiếu và quỹ cổ phiếu", -50, 50], ["gold", "Vàng", -50, 50],
  ["rate", "Lãi vay thả nổi tăng (điểm %)", 0, 5], ["income", "Thu nhập hằng tháng", -50, 50]];
const GOAL_WORD = {on_track: "Đúng tiến độ", at_risk: "Cần chú ý", off_track: "Chậm tiến độ"};

export function render(el, {graph, lens, node, kindLabel, openSheet, scenario}) {
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
      n.kind === "scenario" && (n.value == null ? `Chưa bật: kết quả không thay đổi tài sản thực của bạn.`
        : `${n.active ? "Phần của kịch bản này" : "Nếu xảy ra"}: <b class="${signClass(n.value)}">${vnd(n.value, true)}</b> — giả định, không cộng vào tài sản ròng.`),
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
        ${n.kind === "scenario" && scenario && n.ref !== "custom" ? `<button type="button" class="btn sm ${n.active ? "" : "primary"}" id="ws-run" aria-pressed="${!!n.active}">${n.active ? "Tắt kịch bản" : "Bật kịch bản"}</button>` : ""}
        ${n.kind === "event" ? `<button type="button" class="btn sm primary" data-sheet="do-thi" data-param="${esc(n.ref)}" data-focus-key="event:${esc(n.ref)}">Xem đường đi của tin ${icon("arrow", {size: 14})}</button>`
          : sheet ? `<button type="button" class="btn sm" data-sheet="${sheet}">Mở ${esc(SHEETS[sheet].label)} ${icon("arrow", {size: 14})}</button>` : ""}</div>
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
  for (const b of el.querySelectorAll("[data-n]")) b.onclick = () => graph.select(b.dataset.n);
  for (const b of el.querySelectorAll("[data-sheet]")) b.onclick = () => openSheet(b.dataset.sheet, b.dataset.param || null, b.dataset.focusKey ? [b.dataset.focusKey] : null);

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

  function list(rows) {
    return `<div class="mlist">${rows.map(x => `<button type="button" class="mrow" data-n="${esc(x.id)}">
      <span class="ic-chip sm" style="--tone:${(LOOK[x.kind] || LOOK.class)[0]}">${icon((LOOK[x.kind] || LOOK.class)[1], {size: 13})}</span>
      <span><b>${nameOf(x, esc(short(x.label, 70)))}</b><span class="small muted">${esc(x.kind === "event" ? "Tin tức · CIO duyệt" : x.status_label || kindLabel(x.kind))}</span></span>
      <span class="num ${["event", "alert", "scenario"].includes(x.kind) ? signClass(x.value) : ""}">${esc(figureOf(x))}</span></button>`).join("") || `<p class="muted small">Chưa có mục nào.</p>`}</div>`;
  }
}
