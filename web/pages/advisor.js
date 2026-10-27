/* Chuyên gia (SCR-CL-07) and Duyệt đề xuất (SCR-RM-06); UI redesign R3, was the pre-redesign “rm” tab (FEAT-27,
   FEAT-28). The client sees the relationship specialist who looks after them (all contact details mock) and the
   approval queue read-only: what they sent from Kế hoạch, pending or decided with the note. The RM sees the same
   queue for the picked client and decides each pending proposal, with a note (POST /api/review/decide; the
   server checks the user's role). The RM's approval is the last (OWN-FB-18 retired the certified specialist; items
   kept from before may still say pending_specialist); the RM may also write a recommendation for the family (POST
   /api/review/recommend), which reaches the client at once. Data: GET /api/advisory?client_id=, GET /api/review. */
import {LOCALE, esc, get, n as how, post, toast} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";

const STATUS = {pending: ["ai", "Chờ RM duyệt"], pending_specialist: ["warn", "Chờ chuyên gia có chứng chỉ duyệt"],
  approved: ["good", "Đã duyệt"], rejected: ["bad", "Từ chối"]};

function person(p) {
  return `<div class="panel person">
    <div class="row tight"><span class="avatar" aria-hidden="true">${esc(p.name.split(" ").pop()[0])}</span>
      <div><b>${esc(p.name)}</b><div class="small">${esc(p.role)}</div><div class="small muted">${esc(p.role_vi)}</div></div>
      <span class="pill ai" style="margin-left:auto">Phụ trách chính cho bạn</span></div>
    <div class="contact">
      <a href="tel:${esc(p.phone.replace(/\s/g, ""))}">${icon("phone", {size: 15})} ${esc(p.phone)}</a>
      <a href="mailto:${esc(p.email)}">${icon("mail", {size: 15})} ${esc(p.email)}</a>
      <span>${icon("pin", {size: 15})} ${esc(p.office)}</span>
      ${p.hours ? `<span>${icon("clock", {size: 15})} ${esc(p.hours)}</span>` : ""}
    </div></div>`;
}

export async function render(box, ctx) {
  const client = ctx.client(), staff = ctx.role !== "client";
  const [adv, q] = await Promise.all([
    staff ? null : get(`/api/advisory?client_id=${encodeURIComponent(client)}`).catch((e) => ({error: e.message})),
    get("/api/review"),
  ]);
  const mine = q.items.filter(x => x.client_id === client && (staff || x.kind !== "rm_note" || x.status === "approved"));
  const open = (x) => x.status === "pending" || x.status === "pending_specialist";
  const pending = mine.filter(open), done = mine.filter(x => !open(x));

  const item = (x) => {
    const [tone, text] = STATUS[x.status] || STATUS.pending;
    const decide = staff && x.status === "pending" && x.kind !== "rm_note";
    return `<div class="panel qitem" data-focus="review:${esc(x.id)}">
      <div class="row tight"><b>${esc(x.client_name)}</b><span class="small muted">${new Date(x.created * 1000).toLocaleString(LOCALE)}</span>
        <span class="pill ${tone}" style="margin-left:auto">${text}</span></div>
      <div data-explains><h4>${esc(x.title)}</h4>
      <ul class="ul">${((x.data.option || {}).actions || []).map(a => `<li>${esc(a)}</li>`).join("")}</ul></div>
      ${(x.data.summary || []).slice(0, 4).map(l => `<div class="kv"><span data-explains>${esc(l.label)}</span><b>${how(esc(l.value), "scenario.line", {scenario: x.title, line: l.label})}</b></div>`).join("")}
      ${decide ? `<div class="decide mt"><input id="note-${esc(x.id)}" placeholder="Ghi chú cho khách hàng (không bắt buộc)" aria-label="Ghi chú cho ${esc(x.title)}">
          <button type="button" class="btn primary" data-ok="${esc(x.id)}">Duyệt</button><button type="button" class="btn danger" data-no="${esc(x.id)}">Từ chối</button></div>`
        : x.note ? `<p class="small mt-xs" data-quote><b>Ghi chú:</b> ${esc(x.note)}</p>` : ""}
      ${x.data.specialist_by ? `<p class="small mt-xs"><b>Chuyên gia ${x.status === "approved" ? "đã duyệt" : "từ chối"}</b> (${esc(x.data.certificate || "")})${x.data.specialist_note ? `: <span data-quote>${esc(x.data.specialist_note)}</span>` : ""}</p>` : ""}</div>`;
  };

  const team = staff ? "" : adv.error ? `<div class="notice bad" role="alert">Không tải được: ${esc(adv.error)}</div>`
    : `<div class="cards2">${person(adv.team.rm)}</div><p class="small muted mt-xs">${icon("info", {size: 14})} ${esc(adv.note)}</p>`;

  box.innerHTML = `
    <div class="pagehead"><div>${staff ? `<div class="eyebrow">Khách hàng</div>` : ""}
      <h1 class="h1">${staff ? "Duyệt đề xuất" : "Relationship specialist"}</h1>
      <p class="lede">${staff ? "Phương án khách hàng gửi từ Kế hoạch, chờ RM duyệt" : "Chuyên viên quan hệ khách hàng phụ trách bạn"}</p></div></div>
    ${team}
    <div class="sechead mt"><h2 class="h2">Hàng chờ duyệt</h2><span class="small muted">Hàng chờ ${staff ? "RM" : "chuyên gia"} duyệt · <b>${pending.length}</b> đang chờ ·
      mọi khuyến nghị từ Wealth Planning Advisor đều là mô phỏng cho đến khi ${staff ? "RM" : "chuyên gia"} duyệt</span></div>
    <div class="cards2">${pending.map(item).join("") || `<div class="panel muted">Không có đề xuất nào đang chờ.</div>`}</div>
    ${staff ? `<form class="panel mt" id="recommend" autocomplete="off"><h3>Khuyến nghị cho gia đình <span class="hint">RM viết · đến khách ngay</span></h3>
        <label class="small">Tiêu đề <input name="title" maxlength="200" style="width:100%" placeholder="Ví dụ: Cơ cấu lại tiền gửi"></label>
        <label class="small mt-xs" style="display:block">Việc cần làm, mỗi dòng một việc <textarea name="actions" rows="3" style="width:100%" placeholder="Chuyển 200 triệu sang kỳ hạn 12 tháng"></textarea></label>
        <label class="small mt-xs" style="display:block">Ghi chú cho khách <input name="note" maxlength="1000" style="width:100%"></label>
        <p class="small warn-text mt-xs">Không có người duyệt thứ hai: khuyến nghị này được tính là chưa có người duyệt ở BRD-KPI-05.</p>
        <div class="row mt-xs"><button type="submit" class="btn primary">Gửi khuyến nghị</button></div></form>` : ""}
    ${done.length ? `<h3 class="subhead mt">Đã xử lý</h3><div class="cards2">${done.map(item).join("")}</div>` : ""}`;

  const decide = async (id, decision, btn) => {
    const note = (box.querySelector(`#note-${CSS.escape(id)}`) || {}).value || "";
    btn.disabled = true;
    try {
      await post("/api/review/decide", {item_id: id, decision, note, by: ctx.user});
      toast(decision === "approved" ? "Đã duyệt" : "Đã từ chối");
    } catch (e) {
      toast("Không lưu được: " + e.message);
    }
    if (box.isConnected) await render(box, ctx);
  };
  for (const b of box.querySelectorAll("[data-ok]")) b.onclick = () => decide(b.dataset.ok, "approved", b);
  for (const b of box.querySelectorAll("[data-no]")) b.onclick = () => decide(b.dataset.no, "rejected", b);
  const form = box.querySelector("#recommend");
  if (form) form.onsubmit = async (e) => {
    e.preventDefault();
    const btn = form.querySelector("button[type=submit]");
    btn.disabled = true;
    try {
      await post("/api/review/recommend", {client_id: client, title: form.elements.title.value, note: form.elements.note.value,
        actions: form.elements.actions.value.split("\n"), by: ctx.user});
      toast("Đã gửi đến khách");
    } catch (err) { toast("Không gửi được: " + err.message); btn.disabled = false; return; }
    if (box.isConnected) await render(box, ctx);
  };
}
