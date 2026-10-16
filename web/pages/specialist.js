/* Chuyên gia · Duyệt khuyến nghị (BRD-RULE-ROLE-05, WF-08; G8): the action recommendations an RM approved for the
   families assigned to this specialist, waiting for them; approve, or reject with a reason
   (POST /api/review/specialist). Only a specialist whose certificate is in force (configuration “Chứng nhận chuyên
   gia”, Compliance) may decide; the server checks it again. Data: GET /api/review. */
import {internal, esc, get, post, toast, when} from "../core/core.js";

const KIND = {rm_note: "Khuyến nghị của RM", plan: "Phương án khách gửi"};

export async function render(box, ctx) {
  const q = await get("/api/review");
  const me = ctx.user;
  // the families where this specialist approves: assigned and certified
  const mineFam = new Set(Object.entries(q.approvers).filter(([, a]) => a.some(x => x.id === me)).map(([c]) => c));
  const cert = Object.values(q.approvers).flat().find(a => a.id === me) || q.certificate;
  const waiting = q.items.filter(x => x.status === "pending_specialist" && mineFam.has(x.family_id));
  const decided = q.items.filter(x => x.data.specialist_by === me);

  const card = (x, decide) => `<div class="panel qitem" data-focus="review:${esc(x.id)}">
    <div class="row tight"><b>${esc(x.client_name)}</b><span class="small muted">${esc(KIND[x.kind] || KIND.plan)} · ${esc(when(x.created))}</span>
      <span class="pill ${decide ? "warn" : x.status === "approved" ? "good" : "bad"}" style="margin-left:auto">${decide ? "Chờ bạn duyệt" : x.status === "approved" ? "Đã duyệt" : "Từ chối"}</span></div>
    <div data-explains><h4>${esc(x.title)}</h4>
      <ul class="ul">${((x.data.option || {}).actions || []).map(a => `<li>${esc(a)}</li>`).join("")}</ul></div>
    <p class="small mt-xs">${x.kind === "rm_note" ? "Do RM" : "RM"} ${esc(x.data.decided_by || "")} ${x.kind === "rm_note" ? "viết" : "đã duyệt"}${x.note ? `: <span data-quote>${esc(x.note)}</span>` : ""}</p>
    ${decide ? `<div class="decide mt"><input id="sn-${esc(x.id)}" placeholder="Ghi chú (bắt buộc khi từ chối, từ 10 ký tự)" aria-label="Ghi chú cho ${esc(x.title)}">
        <button type="button" class="btn primary" data-ok="${esc(x.id)}">Duyệt</button><button type="button" class="btn danger" data-no="${esc(x.id)}">Từ chối</button></div>`
      : x.data.specialist_note ? `<p class="small" data-quote><b>Ghi chú của bạn:</b> ${esc(x.data.specialist_note)}</p>` : ""}</div>`;

  box.innerHTML = `${internal()}
    <div class="pagehead"><div><div class="eyebrow">Chuyên gia</div><h1 class="h1">Duyệt khuyến nghị</h1>
      <p class="lede">Khuyến nghị hành động RM đã duyệt cho các gia đình được giao bạn, chờ chuyên gia có chứng chỉ duyệt trước khi đến khách.</p></div></div>
    <div class="panel">${cert ? `<b>Chứng chỉ:</b> ${esc(cert.certificate)} · ${esc(cert.issuer)} · hiệu lực đến ${esc(cert.valid_until)}`
      : `<span class="bad-text"><b>Chưa có chứng chỉ còn hiệu lực</b></span> — bạn chưa duyệt được khuyến nghị. Tuân thủ cập nhật “Chứng nhận chuyên gia” trong Cấu hình.`}</div>
    <div class="sechead mt"><h2 class="h2">Chờ bạn duyệt</h2><span class="small muted"><b>${waiting.length}</b> khuyến nghị</span></div>
    <div class="cards2">${waiting.map(x => card(x, true)).join("") || `<div class="panel muted">Không có khuyến nghị nào chờ bạn.</div>`}</div>
    ${decided.length ? `<h3 class="subhead mt">Bạn đã xử lý</h3><div class="cards2">${decided.map(x => card(x, false)).join("")}</div>` : ""}`;

  const decide = async (id, decision, btn) => {
    const note = (box.querySelector(`#sn-${CSS.escape(id)}`) || {}).value || "";
    btn.disabled = true;
    try {
      await post("/api/review/specialist", {item_id: id, decision, note, by: me});
      toast(decision === "approved" ? "Đã duyệt" : "Đã từ chối");
    } catch (e) {
      toast("Không lưu được: " + e.message);
      btn.disabled = false;
      return;
    }
    if (box.isConnected) await render(box, ctx);
  };
  for (const b of box.querySelectorAll("[data-ok]")) b.onclick = () => decide(b.dataset.ok, "approved", b);
  for (const b of box.querySelectorAll("[data-no]")) b.onclick = () => decide(b.dataset.no, "rejected", b);
}
