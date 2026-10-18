/* Tuân thủ · Bàn kiểm soát (SCR-CMP-06, FEAT-41): every control Compliance owns as a flow, one lane each, with what
   waits at each step — news held for the restricted list → let through with a reason (BRD-BR-04); research waiting →
   released by another person after its release time, or rejected (BR-03); letters waiting → approved or returned
   (FR-801); policy documents added → verified by a second person → summarised by the policy agent (FR-306);
   configuration waiting (FR-701); the audit chain (FR-702). Below: one queue of everything waiting for Compliance,
   oldest first, each opening its page, and the alerts the bell holds for Compliance.

   Every figure is GET /api/desk's, composed from the stores those pages read. Read-only: each decision stays on its
   page with its rule (a reason, a second person, the release time). data-node marks what the assistant reads. */
import {ago, esc} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";

const ICON = {held: "lock", research: "file", letters: "mail", policy: "scale", config: "sliders"};  // the rail's icons where it has them
const SEVERITY = {high: "bad", medium: "warn", low: ""};

export function hint(d) {
  const waiting = d.queue.length;
  return `<h3>Bàn kiểm soát</h3>
    <p class="small">Mỗi dòng là một chốt kiểm soát của Tuân thủ, đọc từ trái sang phải: việc đang chờ ở bước đầu, rồi những gì đã
      qua chốt. Chọn một dòng để xem từng việc đang chờ và mở trang của nó; quyết định vẫn làm ở trang đó, với quy tắc của nó.</p>
    <p class="small">${waiting ? `<b>${waiting}</b> việc chờ Tuân thủ.` : "Không việc nào chờ Tuân thủ."}
      Trợ lý bên cạnh đọc cùng bàn: hỏi “Có gì chờ Tuân thủ?” hay “Chuỗi nhật ký còn nguyên không?”.</p>`;
}

export function render(box, d, api) {
  const lane = (c) => {
    const wait = c.steps[0].count;
    return `<li><button type="button" class="cm-lane${wait ? " waits" : ""}" data-c="${esc(c.id)}" data-node="${esc(c.id)}"
        aria-label="${esc(c.label)}: ${c.steps.map(s => `${s.count} ${s.label.toLowerCase()}`).join(", ")}">
      <span class="cm-lane-h"><span class="cm-lane-i" aria-hidden="true">${icon(ICON[c.id], {size: 18})}</span>
        <span><b>${esc(c.label)}</b><small class="muted">${esc(c.rule)}</small></span></span>
      <span class="cm-steps">${c.steps.map((s, i) => `<span class="cm-step${i === 0 && s.count ? " waits" : ""}">
        <span class="cm-step-n num">${s.count}</span><span class="cm-step-l small">${esc(s.label)}</span></span>`).join("")}</span></button></li>`;
  };
  const chain = d.chain;
  box.innerHTML = `
    <header class="dk-head"><div><div class="eyebrow">Tuân thủ</div><h1 class="ws-title" id="dk-title">Bàn kiểm soát</h1>
      <p class="ws-sub small muted"><b>${d.queue.length}</b> việc chờ Tuân thủ · ${d.alerts.filter(a => a.status === "open").length} cảnh báo đang mở</p></div>
      <span class="pill ${chain.ok ? "good" : "bad"}">Chuỗi nhật ký: ${chain.ok ? "nguyên vẹn" : "gãy"}</span></header>
    <ol class="cm-flows" data-node="controls" aria-label="Các chốt kiểm soát">${d.controls.map(lane).join("")}
      <li><a class="cm-lane cm-chain${chain.ok ? "" : " bad"}" href="#/compliance/nhat-ky" data-node="chain">
        <span class="cm-lane-h"><span class="cm-lane-i" aria-hidden="true">${icon("history", {size: 18})}</span>
          <span><b>Chuỗi nhật ký</b><small class="muted">BRD-FR-702</small></span></span>
        <span class="cm-steps"><span class="cm-step"><span class="cm-step-n num">${chain.count}</span><span class="cm-step-l small">dòng</span></span>
          <span class="cm-step${chain.ok ? "" : " bad"}"><span class="cm-step-n">${chain.ok ? icon("check", {size: 18}) : "!"}</span>
            <span class="cm-step-l small">${chain.ok ? "băm khớp" : `gãy ở dòng ${esc(chain.broken_at)}`}</span></span>
          <span class="cm-step"><span class="cm-step-n">${d.worm.on ? esc(d.worm.segments) : "—"}</span>
            <span class="cm-step-l small">${d.worm.on ? `đoạn chỉ-ghi-một-lần · ${d.worm.ok ? "khớp" : "lệch"}` : "chỉ-ghi-một-lần tắt"}</span></span></span></a></li></ol>
    <div class="dk-grid mt">
      <section class="panel" data-node="queue" aria-labelledby="cm-q"><div class="sechead"><h2 class="h3" id="cm-q">Chờ Tuân thủ</h2>
        <span class="small muted">cũ nhất trước</span></div>
        <div class="dk-list">${d.queue.map(x => `<a class="dk-row" href="${esc(x.route)}" data-node="item:${esc(x.id)}"><span class="dk-row-t"><b>${esc(x.title)}</b>
          <small>${esc(d.controls.find(c => c.id === x.control).label)} · ${esc(x.sub)} · ${esc(ago(x.at))}</small></span>
          <span class="pill ${x.ready ? "warn" : ""}">${x.ready ? "Chờ bạn" : "Chưa tới giờ"}</span></a>`).join("")
          || `<p class="small muted">Không việc nào chờ Tuân thủ.</p>`}</div></section>
      <section class="panel" data-node="alerts" aria-labelledby="cm-al"><div class="sechead"><h2 class="h3" id="cm-al">Cảnh báo</h2>
        <span class="small muted">xem ở chuông để đánh dấu đã xem</span></div>
        <div class="dk-list">${d.alerts.map(a => `<div class="dk-row"><span class="dk-row-t"><b>${esc(a.title)}</b>
          <small>${esc(a.label || a.kind)} · ${esc(ago(a.last_at))}${a.detail ? ` · ${esc(a.detail)}` : ""}</small></span>
          <span class="badge ${a.status === "open" ? SEVERITY[a.severity] || "" : ""}">${a.status === "open" ? "Đang mở" : "Đã xem"}</span></div>`).join("")
          || `<p class="small muted">Không có cảnh báo nào cho Tuân thủ.</p>`}</div></section>
    </div>`;

  for (const b of box.querySelectorAll("[data-c]")) b.onclick = () => pick(b.dataset.c);
  function pick(id) {
    for (const b of box.querySelectorAll("[data-c]")) b.classList.toggle("sel", b.dataset.c === id);
    const c = d.controls.find(x => x.id === id);
    api.inspect(`<h3>${esc(c.label)}</h3><p class="small muted">${esc(c.rule)} · ${c.steps.map(s => `${s.count} ${esc(s.label.toLowerCase())}`).join(" · ")}</p>
      ${c.items.length ? `<div class="dk-list">${c.items.map(x => `<a class="dk-row" href="${esc(x.route)}"><span class="dk-row-t"><b>${esc(x.title)}</b>
        <small>${esc(x.sub)} · ${esc(ago(x.at))}</small></span></a>`).join("")}</div>` : `<p class="small">Không việc nào đang chờ ở chốt này.</p>`}
      <p class="mt"><a class="btn" href="${esc(c.route)}">${icon("arrow", {size: 14})} Mở ${esc(c.page)}</a></p>`);
  }
}
