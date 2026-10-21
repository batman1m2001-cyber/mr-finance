/* RM · Sổ khách hàng (SCR-RM-07, FEAT-41): the RM's families around the RM, nearer when they need the RM sooner —
   a family at the pre-review threshold of an effective run or with a goal task to contact now (inner ring), a
   proposal waiting for the RM or a goal to confirm (middle), a reminder (outer), nothing (the edge) — sized by net
   worth at the newest effective run. A family picked → Thông tin: its card, why it is where it is, the news that
   moved it, and its pages (the client picker set first, as the header's picker would). Below: Hôm nay's call list,
   goal tasks, proposals waiting, recent contacts.

   Every figure is GET /api/desk's, composed from Hôm nay, the approval queue and the contact log (an RM's own
   families only, BRD-RULE-ROLE-02). data-node marks what the RM's assistant reads (its step lights it). */
import {ago, esc, pct, signClass, vnd} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";

const RING = {3: 92, 2: 124, 1: 150, 0: 170};  // how far from the RM: sooner is nearer
const TONE = {3: "bad", 2: "warn", 1: "human", 0: ""};
const PAGES = [["khach-hang/tac-dong", "Tác động tin"], ["khach-hang/toan-canh", "Toàn cảnh"], ["khach-hang/tong-quan", "Chi tiết tài sản"],
  ["khach-hang/tai-san", "Tài sản"], ["khach-hang/ke-hoach", "Kế hoạch"]];

/* the drawing's frame: wide on a desk, taller on a phone (the dots keep a size a finger can pick) */
const frame = (narrow) => (narrow ? {W: 420, H: 460, sx: 1.08, sy: 1.0} : {W: 680, H: 440, sx: 1.75, sy: 0.92});

function place(fams, g) {
  const max = Math.max(1, ...fams.map(f => f.net_worth || 0));
  const cx = g.W / 2, cy = g.H / 2;
  return fams.map((f, i) => {
    const a = -Math.PI / 2 + (2 * Math.PI * i) / Math.max(fams.length, 1) + (fams.length === 2 ? Math.PI / 4 : 0);
    const r = RING[f.level], s = f.net_worth ? 13 + 17 * Math.sqrt(f.net_worth / max) : 18;
    const x = cx + Math.cos(a) * r * g.sx, y = cy + Math.sin(a) * r * g.sy;
    const anchor = x > g.W * 0.72 ? "end" : x < g.W * 0.28 ? "start" : "middle";  // a name near an edge reads inward
    return {...f, x, y, s, ly: y < cy ? y - s - 8 : y + s + 17, lx: anchor === "end" ? x + s : anchor === "start" ? x - s : x, anchor};
  });
}

export function hint(d) {
  const soon = d.families.filter(f => f.level >= 2).length;
  return `<h3>Sổ khách hàng</h3>
    <p class="small">Bạn ở giữa; mỗi gia đình được giao là một chấm, càng gần càng cần bạn sớm, càng to tài sản ròng càng lớn.
      Chọn một gia đình để xem vì sao, tin nào tác động, và mở các trang của họ.</p>
    <p class="small">${soon ? `<b>${soon}</b> gia đình cần bạn sớm.` : "Không gia đình nào cần gọi ngay hay chờ bạn duyệt."}
      Trợ lý bên cạnh đọc cùng sổ này: hỏi “Sổ khách hàng có gì cần làm?” hay “Hôm nay cần gọi ai?”.</p>`;
}

export function render(box, d, api) {
  const g = frame(box.clientWidth < 560), W = g.W, H = g.H, CX = W / 2, CY = H / 2;
  const fams = place(d.families, g);
  const soon = d.families.filter(f => f.level >= 3).length;
  const sized = d.families.some(f => f.net_worth != null);
  box.innerHTML = `
    <header class="dk-head"><div><div class="eyebrow">RM</div><h1 class="ws-title" id="dk-title">Sổ khách hàng</h1>
      <p class="ws-sub small muted">${d.families.length} gia đình · ${soon ? `<b>${soon}</b> cần gọi ngay` : "không ai cần gọi ngay"} ·
        ${d.proposals.length} đề xuất chờ duyệt · ${d.tasks.length} việc theo mục tiêu</p></div></header>
    <section class="panel rk-map" data-node="book" aria-labelledby="rk-t"><h2 class="sr-only" id="rk-t">Bản đồ sổ khách hàng</h2>
      <svg viewBox="0 0 ${W} ${H}" role="group" aria-label="Các gia đình quanh bạn, gần hơn khi cần bạn sớm hơn">
        ${[3, 2, 1].map(l => `<ellipse class="rk-ring" cx="${CX}" cy="${CY}" rx="${RING[l] * g.sx}" ry="${RING[l] * g.sy}"/>`).join("")}
        ${fams.map(f => `<line class="rk-edge l${f.level}" x1="${CX}" y1="${CY}" x2="${f.x.toFixed(1)}" y2="${f.y.toFixed(1)}"/>`).join("")}
        <g class="rk-me" aria-hidden="true"><circle cx="${CX}" cy="${CY}" r="26"/><text x="${CX}" y="${CY + 5}">Bạn</text></g>
        ${fams.map(f => `<g class="rk-fam l${f.level}" data-fam="${esc(f.id)}" data-node="family:${esc(f.id)}" tabindex="0" role="button"
            aria-label="${esc(f.name)}: ${esc(f.level_label)}${f.why.length ? ` — ${esc(f.why.map(w => w.text).join(", "))}` : ""}">
          <circle class="rk-halo" cx="${f.x.toFixed(1)}" cy="${f.y.toFixed(1)}" r="${(f.s + 7).toFixed(1)}"/>
          <circle class="rk-dot" cx="${f.x.toFixed(1)}" cy="${f.y.toFixed(1)}" r="${f.s.toFixed(1)}"/>
          ${f.why.length ? `<g class="rk-n"><circle cx="${(f.x + f.s * 0.75).toFixed(1)}" cy="${(f.y - f.s * 0.75).toFixed(1)}" r="10"/>
            <text x="${(f.x + f.s * 0.75).toFixed(1)}" y="${(f.y - f.s * 0.75 + 4).toFixed(1)}">${f.why.length}</text></g>` : ""}
          <text class="rk-l" x="${f.lx.toFixed(1)}" y="${f.ly.toFixed(1)}" text-anchor="${f.anchor}">${esc(f.name)}</text></g>`).join("")}
      </svg>
      <p class="small muted rk-key"><span class="badge bad">Cần gọi ngay</span> vòng trong · <span class="badge warn">Cần xử lý</span> vòng giữa ·
        <span class="badge human">Nhắc</span> vòng ngoài · ổn: ở rìa. ${sized ? "Cỡ chấm: tài sản ròng tại lần áp dụng gần nhất." : "Chưa có lần áp dụng nào: các chấm cùng cỡ."}
        ${d.control.length ? ` ${d.control.length} gia đình trong nhóm đối chứng: không có tín hiệu cho họ.` : ""}</p>
    </section>
    <div class="dk-grid mt">
      <section class="panel" data-node="calls" aria-labelledby="rk-calls"><div class="sechead"><h2 class="h3" id="rk-calls">Cần gọi trước</h2>
        <a class="small" href="#/rm/hom-nay">Hôm nay →</a></div>
        <div class="dk-list">${d.calls.map(c => `<button type="button" class="dk-row" data-pick="${esc(c.family_id)}">
          <span class="dk-row-t"><b>${esc(c.name)}</b><small>${c.events.length} sự kiện · P10 3 tháng ${pct(c.p10_3m_pct, true, 1)} tài sản ròng</small></span>
          <span class="num small ${signClass(c.expected_3m)}">${vnd(c.expected_3m, true)}</span></button>`).join("")
          || `<p class="small muted">Không gia đình nào chạm ngưỡng xem trước (P10 3 tháng ≤ ${pct(d.threshold_pct, true, 0)} tài sản ròng).</p>`}</div></section>
      <section class="panel" data-node="proposals" aria-labelledby="rk-prop"><div class="sechead"><h2 class="h3" id="rk-prop">Đề xuất chờ duyệt</h2>
        <span class="small muted">${d.proposals.length}</span></div>
        <div class="dk-list">${d.proposals.map(p => `<button type="button" class="dk-row" data-open="${esc(p.family_id)}" data-href="#/rm/khach-hang/duyet">
          <span class="dk-row-t"><b>${esc(p.title)}</b><small>${esc(p.name)} · ${esc(p.id)} · ${esc(ago(p.created))}</small></span>
          <span class="pill warn">Chờ RM duyệt</span></button>`).join("") || `<p class="small muted">Không đề xuất nào chờ bạn duyệt.</p>`}</div></section>
      <section class="panel" data-node="tasks" aria-labelledby="rk-tasks"><div class="sechead"><h2 class="h3" id="rk-tasks">Việc theo mục tiêu</h2>
        <a class="small" href="#/rm/hom-nay">Hôm nay →</a></div>
        <div class="dk-list">${d.tasks.map(t => `<button type="button" class="dk-row" data-pick="${esc(t.family_id)}">
          <span class="dk-row-t"><b>${esc(t.family_name)} · ${esc(t.goal)}</b><small>${esc(t.note_title)}${t.milestone ? ` · mốc ${esc(t.milestone)}` : ""}</small></span>
          <span class="badge ${TONE[{contact_now: 3, confirm_goal: 2, remind: 1}[t.level] || 0]}">${esc(t.level_label)}</span></button>`).join("")
          || `<p class="small muted">Không có việc nào theo mục tiêu: khi Tuân thủ phát hành ghi chú quy định khớp mục tiêu của khách, việc hiện ở đây.</p>`}</div></section>
      <section class="panel" data-node="contacts" aria-labelledby="rk-con"><div class="sechead"><h2 class="h3" id="rk-con">Liên hệ gần đây</h2>
        <a class="small" href="#/rm/hom-nay">Ghi liên hệ →</a></div>
        <div class="dk-list">${d.contacts.map(c => `<button type="button" class="dk-row" data-pick="${esc(c.family_id)}">
          <span class="dk-row-t"><b>${esc((d.families.find(f => f.id === c.family_id) || {name: c.family_id}).name)}</b><small>${esc(c.channel_label)} · ${esc(ago(c.at))}</small></span>
          ${c.from_signal ? '<span class="badge human">từ tín hiệu</span>' : ""}</button>`).join("") || `<p class="small muted">Chưa ghi liên hệ nào với các gia đình của bạn.</p>`}</div></section>
    </div>`;

  const svg = box.querySelector("svg");
  for (const g of box.querySelectorAll("[data-fam]")) {
    g.addEventListener("click", () => pick(g.dataset.fam));
    g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(g.dataset.fam); } });
  }
  for (const b of box.querySelectorAll("[data-pick]")) b.onclick = () => pick(b.dataset.pick);
  for (const b of box.querySelectorAll("[data-open]")) b.onclick = () => api.open(b.dataset.open, b.dataset.href);

  function pick(id) {
    for (const g of svg.querySelectorAll("[data-fam]")) g.classList.toggle("sel", g.dataset.fam === id);
    const f = d.families.find(x => x.id === id);
    if (!f) return;
    const who = [f.segment, f.age ? `${f.age} tuổi` : "", f.occupation, f.city].filter(Boolean).map(esc).join(" · ");
    api.inspect(`<h3>${esc(f.name)}</h3><p class="small muted">${who}</p>
      <p><span class="badge ${TONE[f.level]}">${esc(f.level_label)}</span>${f.control ? ' <span class="badge">nhóm đối chứng</span>' : ""}</p>
      ${f.why.length ? `<ul class="small">${f.why.map(w => `<li>${esc(w.text)}</li>`).join("")}</ul>` : `<p class="small muted">Không có tín hiệu nào cần bạn lúc này.</p>`}
      <dl class="dk-kv">
        <dt>Tài sản ròng</dt><dd class="num">${f.net_worth != null ? `${vnd(f.net_worth)} <small class="muted">tại ${esc(f.net_worth_run)}</small>` : "—"}</dd>
        <dt>Đề xuất chờ duyệt</dt><dd class="num">${f.proposals}</dd>
        <dt>Liên hệ gần nhất</dt><dd>${f.last_contact ? `${esc(f.last_contact.channel_label)} · ${esc(ago(f.last_contact.at))}` : "chưa có"}</dd></dl>
      ${f.impacts.length ? `<h4 class="mt">Tin tác động</h4><div class="dk-list">${f.impacts.map(x => `<div class="dk-row"><span class="dk-row-t"><b>${esc(x.event)}</b>
        <small>${esc(x.run_id)} · kỳ vọng 3 tháng ${pct(x.expected_3m_pct, true, 2)}${x.pre_review ? " · chạm ngưỡng" : ""}</small></span>
        <span class="num small ${signClass(x.expected_3m)}">${vnd(x.expected_3m, true)}</span></div>`).join("")}</div>` : ""}
      <div class="rk-acts mt">${PAGES.map(([p, l]) => `<button type="button" class="btn sm" data-go="#/rm/${p}">${esc(l)}</button>`).join("")}
        <button type="button" class="btn sm${f.proposals ? " primary" : ""}" data-go="#/rm/khach-hang/duyet">Duyệt đề xuất${f.proposals ? ` (${f.proposals})` : ""}</button>
        <button type="button" class="btn sm" data-go="#/rm/hom-nay">Ghi liên hệ</button></div>`,
    (pane) => { for (const b of pane.querySelectorAll("[data-go]")) b.onclick = () => api.open(f.id, b.dataset.go); });
  }
}
