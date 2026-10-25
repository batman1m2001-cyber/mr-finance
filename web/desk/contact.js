/* RM · Ghi liên hệ (OWN-FB-21): Hôm nay's contact log, now in the desk's Thông tin — the client, the signal it
   started from (the client's pre-review case or goal task, or none), how, a note, then the log; each contact counts
   towards “liên hệ bắt đầu từ tín hiệu hệ thống” (BRD-KPI-06, POST /api/rm/contacts). */
import {esc, get, post, toast, when} from "../core/core.js";

export async function contact(api, family, signal) {
  const d = await get("/api/rm/today");
  // the signals each client has: its worst pre-review case (one call per client, whatever the events) and its goal tasks
  const worst = {}, signals = {};
  for (const c of d.cases) if (!worst[c.family_id] || c.p10_3m_pct < worst[c.family_id].p10_3m_pct) worst[c.family_id] = c;
  for (const c of Object.values(worst)) (signals[c.family_id] ||= []).push({id: c.signal, label: `Cần xem trước: ${c.event.title}`});
  for (const t of d.goal_tasks) (signals[t.family_id] ||= []).push({id: t.signal, label: `${t.goal}: ${t.note_title}`});
  const names = Object.fromEntries(d.families.map(f => [f.id, f.name]));
  api.inspect(`<h3>Ghi liên hệ</h3>
    <p class="small muted">Ghi mỗi lần gọi, gặp, nhắn, kèm tín hiệu khởi đầu nếu có.</p>
    <form id="contact-form" class="dk-form" autocomplete="off">
      <label class="small">Khách hàng <select name="family">${d.families.map(f => `<option value="${esc(f.id)}">${esc(f.name)}</option>`).join("")}</select></label>
      <label class="small">Tín hiệu <select name="signal"></select></label>
      <label class="small">Cách <select name="channel">${Object.entries(d.channels).map(([k, v]) => `<option value="${k}">${esc(v)}</option>`).join("")}</select></label>
      <label class="small">Ghi chú <textarea name="note" rows="3" maxlength="500" placeholder="Nội dung chính của lần liên hệ"></textarea></label>
      <button type="submit" class="btn sm primary">Ghi liên hệ</button>
    </form>
    <h4 class="mt">Nhật ký liên hệ</h4>
    <div class="dk-list">${d.contacts.slice(0, 10).map(c => `<div class="dk-row"><span class="dk-row-t"><b>${esc(names[c.family_id] || c.family_id)}</b>
      <small>${esc(c.channel_label)} · ${esc(when(c.at))} · ${c.signal ? esc(c.signal.label) : "không từ tín hiệu"}${c.note ? ` · ${esc(c.note)}` : ""}</small></span></div>`).join("")
      || `<p class="small muted">Chưa ghi liên hệ nào.</p>`}</div>`, (pane) => {
    const form = pane.querySelector("#contact-form");
    const fill = (pick) => {
      const mine = signals[form.family.value] || [];
      form.signal.innerHTML = `<option value="">Không từ tín hiệu</option>` + mine.map(x => `<option value="${esc(x.id)}">${esc(x.label)}</option>`).join("");
      form.signal.value = pick != null && mine.some(x => x.id === pick) ? pick : mine.length ? mine[0].id : "";
    };
    if (family && names[family]) form.family.value = family;
    fill(signal);
    form.family.onchange = () => fill();
    form.onsubmit = async (e) => {
      e.preventDefault();
      const btn = form.querySelector("button[type=submit]");
      btn.disabled = true;
      try {
        await post("/api/rm/contacts", {family_id: form.family.value, channel: form.channel.value, signal: form.signal.value || null,
          note: form.note.value, by: api.user()});
        toast("Đã ghi liên hệ");
        await api.reload();
        await contact(api, form.family.value);
      } catch (err) { toast(err.message); btn.disabled = false; }
    };
    form.note.focus({preventScroll: true});
  });
}
