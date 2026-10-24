/* RM · Sổ khách hàng (SCR-RM-07, FEAT-41): the RM's families, the ones who need the RM sooner first — a family at
   the pre-review threshold of an effective run or with a goal task to contact now, then a proposal waiting for the RM
   or a goal to confirm, then a reminder, then nothing — each with why and its net worth at the newest effective run
   (the drawing around the RM went, OWN-FB-01). A family picked → Thông tin: its card, why, the news that moved it,
   and its pages (the client picker set first, as the header's picker would). Then Hôm nay's call list, goal tasks,
   proposals waiting, recent contacts.

   Every figure is GET /api/desk's, composed from Hôm nay, the approval queue and the contact log (an RM's own
   families only, BRD-RULE-ROLE-02). data-node marks what the RM's assistant reads (its step lights it). */
import {ago, esc, pct, signClass, vnd} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";

const TONE = {3: "bad", 2: "warn", 1: "human", 0: ""};
const PAGES = [["khach-hang/tong-quan", "Wealth view"], ["khach-hang/ke-hoach", "Wealth planning advisor"],
  ["khach-hang/chinh-sach", "Headline news"], ["khach-hang/hieu-qua", "Advisory performance"], ["khach-hang/tac-dong", "Tác động tin"]];

export function hint(d) {
  const soon = d.families.filter(f => f.level >= 2).length;
  return `<h3>Sổ khách hàng</h3>
    <p class="small">Các gia đình được giao cho bạn, ai cần bạn sớm nhất ở trên. Chọn một gia đình để xem vì sao, tin nào
      tác động, và mở các trang của họ.</p>
    <p class="small">${soon ? `<b>${soon}</b> gia đình cần bạn sớm.` : "Không gia đình nào cần gọi ngay hay chờ bạn duyệt."}
      Trợ lý bên cạnh đọc cùng sổ này: hỏi “Sổ khách hàng có gì cần làm?” hay “Hôm nay cần gọi ai?”.</p>`;
}

export function render(box, d, api) {
  const fams = [...d.families].sort((a, b) => b.level - a.level || (b.net_worth || 0) - (a.net_worth || 0));
  const soon = d.families.filter(f => f.level >= 3).length;
  box.innerHTML = `
    <header class="dk-head"><div><div class="eyebrow">RM</div><h1 class="ws-title" id="dk-title">Sổ khách hàng</h1>
      <p class="ws-sub small muted">${d.families.length} gia đình · ${soon ? `<b>${soon}</b> cần gọi ngay` : "không ai cần gọi ngay"} ·
        ${d.proposals.length} đề xuất chờ duyệt · ${d.tasks.length} việc theo mục tiêu</p></div></header>
    <section class="panel" data-node="book" aria-labelledby="rk-t"><div class="sechead"><h2 class="h3" id="rk-t">Gia đình của bạn</h2>
      <span class="small muted">${d.families.length}</span></div>
      <div class="dk-list">${fams.map(f => `<button type="button" class="dk-row" data-pick="${esc(f.id)}" data-fam="${esc(f.id)}" data-node="family:${esc(f.id)}">
        <span class="dk-row-t"><b>${esc(f.name)}</b><small>${f.why.length ? esc(f.why.map(w => w.text).join(" · ")) : "Không có tín hiệu nào cần bạn lúc này"}</small></span>
        <span class="rk-end">${f.level ? `<span class="badge ${TONE[f.level]}">${esc(f.level_label)}</span>` : ""}
          <span class="num small">${f.net_worth != null ? vnd(f.net_worth, true) : "—"}</span></span></button>`).join("")
        || `<p class="small muted">Chưa có gia đình nào được giao cho bạn.</p>`}</div>
      ${d.control.length ? `<p class="small muted">${d.control.length} gia đình trong nhóm đối chứng: không có tín hiệu cho họ.</p>` : ""}
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
          || `<p class="small muted">Không có việc nào theo mục tiêu: khi CIO phát hành ghi chú quy định khớp mục tiêu của khách, việc hiện ở đây.</p>`}</div></section>
      <section class="panel" data-node="contacts" aria-labelledby="rk-con"><div class="sechead"><h2 class="h3" id="rk-con">Liên hệ gần đây</h2>
        <a class="small" href="#/rm/hom-nay">Ghi liên hệ →</a></div>
        <div class="dk-list">${d.contacts.map(c => `<button type="button" class="dk-row" data-pick="${esc(c.family_id)}">
          <span class="dk-row-t"><b>${esc((d.families.find(f => f.id === c.family_id) || {name: c.family_id}).name)}</b><small>${esc(c.channel_label)} · ${esc(ago(c.at))}</small></span>
          ${c.from_signal ? '<span class="badge human">từ tín hiệu</span>' : ""}</button>`).join("") || `<p class="small muted">Chưa ghi liên hệ nào với các gia đình của bạn.</p>`}</div></section>
    </div>`;

  for (const b of box.querySelectorAll("[data-pick]")) b.onclick = () => pick(b.dataset.pick);
  for (const b of box.querySelectorAll("[data-open]")) b.onclick = () => api.open(b.dataset.open, b.dataset.href);

  function pick(id) {
    for (const r of box.querySelectorAll("[data-fam]")) r.classList.toggle("sel", r.dataset.fam === id);
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
