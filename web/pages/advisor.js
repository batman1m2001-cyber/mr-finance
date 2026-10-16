/* Chuyên gia (SCR-CL-07) and Duyệt đề xuất (SCR-RM-06); UI redesign R3, was the pre-redesign “rm” tab (FEAT-27,
   FEAT-28). The client sees the relationship specialist who looks after them (all contact details mock) and the
   approval queue read-only: what they sent from Kế hoạch, pending or decided with the note. The RM sees the same
   queue for the picked client and decides each pending proposal, with a note (POST /api/review/decide; the
   server checks the user's role). Data: GET /api/advisory?client_id=, GET /api/review. */
import {internal, esc, get, n as how, post, toast} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";

const STATUS = {pending: ["ai", "Chờ chuyên gia duyệt"], approved: ["good", "Đã duyệt"], rejected: ["bad", "Từ chối"]};

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
  const mine = q.items.filter(x => x.client_id === client);
  const pending = mine.filter(x => x.status === "pending"), done = mine.filter(x => x.status !== "pending");

  const item = (x) => {
    const [tone, text] = STATUS[x.status] || STATUS.pending;
    const decide = staff && x.status === "pending";
    return `<div class="panel qitem" data-focus="review:${esc(x.id)}">
      <div class="row tight"><b>${esc(x.client_name)}</b><span class="small muted">${new Date(x.created * 1000).toLocaleString("vi-VN")}</span>
        <span class="pill ${tone}" style="margin-left:auto">${text}</span></div>
      <div data-explains><h4>${esc(x.title)}</h4>
      <ul class="ul">${((x.data.option || {}).actions || []).map(a => `<li>${esc(a)}</li>`).join("")}</ul></div>
      ${(x.data.summary || []).slice(0, 4).map(l => `<div class="kv"><span data-explains>${esc(l.label)}</span><b>${how(esc(l.value), "scenario.line", {scenario: x.title, line: l.label})}</b></div>`).join("")}
      ${decide ? `<div class="decide mt"><input id="note-${esc(x.id)}" placeholder="Ghi chú cho khách hàng (không bắt buộc)" aria-label="Ghi chú cho ${esc(x.title)}">
          <button type="button" class="btn primary" data-ok="${esc(x.id)}">Duyệt</button><button type="button" class="btn danger" data-no="${esc(x.id)}">Từ chối</button></div>`
        : x.note ? `<p class="small mt-xs" data-quote><b>Ghi chú:</b> ${esc(x.note)}</p>` : ""}</div>`;
  };

  const team = staff ? "" : adv.error ? `<div class="notice bad" role="alert">Không tải được: ${esc(adv.error)}</div>`
    : `<div class="cards2">${person(adv.team.rm)}</div><p class="small muted mt-xs">${icon("info", {size: 14})} ${esc(adv.note)}</p>`;

  box.innerHTML = `${staff ? internal() : ""}
    <div class="pagehead"><div><div class="eyebrow">${staff ? "Khách hàng" : "Chuyên gia"}</div>
      <h1 class="h1">${staff ? "Duyệt đề xuất" : "Relationship specialist"}</h1>
      <p class="lede">${staff ? "Phương án khách hàng gửi từ Kế hoạch, chờ RM duyệt" : "Chuyên viên quan hệ khách hàng phụ trách bạn"}</p></div></div>
    ${team}
    <div class="sechead mt"><h2 class="h2">Approval queue</h2><span class="small muted">Hàng chờ chuyên gia duyệt · <b>${pending.length}</b> đang chờ ·
      mọi khuyến nghị từ Wealth Planning Advisor đều là mô phỏng cho đến khi chuyên gia duyệt</span></div>
    <div class="cards2">${pending.map(item).join("") || `<div class="panel muted">Không có đề xuất nào đang chờ.</div>`}</div>
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
}
