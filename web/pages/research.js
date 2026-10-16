/* Nghiên cứu: the research side uploads reports, house views and regulation notes; Compliance
   releases or rejects them (another person, after the release time, with a note). A released report
   reaches the CIO's inbox as "Độc quyền"; a regulation note goes to the goal branch. */
import {empty, esc, get, post, toast, when} from "../core/core.js";

const STATUS = {PENDING_RELEASE: ["warn", "Chờ Tuân thủ"], RELEASED: ["good", "Đã phát hành"], REJECTED: ["bad", "Từ chối"]};
const LEVEL = {contact_now: "bad", confirm_goal: "human", remind: "warn", note: ""};

export async function render(box, ctx) {
  const [{items, kinds}, reg] = await Promise.all([get("/api/research"), get("/api/goals/regulation")]);
  const purposes = reg.purposes;
  const isCompliance = ctx.role === "compliance";
  const byNote = {};
  for (const m of reg.matches) (byNote[m.note_id] ||= []).push(m);
  const pending = items.filter(i => i.status === "PENDING_RELEASE").length;
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">${isCompliance ? "Tuân thủ" : "CIO"} · Nghiên cứu và ghi chú quy định</div>
      <div class="h1">${pending} chờ phát hành · ${items.length - pending} đã xử lý</div>
      <div class="lede small">Chỉ nạp sau giờ phát hành chính thức. Người phát hành phải khác người nạp. Ghi chú quy định không đổi giá tài sản: nó đi nhánh mục tiêu (mốc chuẩn bị, hồ sơ, mức khẩn).</div></div></div>
    ${isCompliance ? "" : `<div class="panel" style="margin-bottom:16px"><details class="more"><summary>Nạp báo cáo mới</summary>
      <form id="up" class="cols" style="margin-top:8px">
        <label class="field c3">Loại<select name="kind">${Object.entries(kinds).map(([k, v]) => `<option value="${k}">${esc(v)}</option>`).join("")}</select></label>
        <label class="field c3">Số báo cáo<input name="report_no" required></label>
        <label class="field c3">Giờ phát hành<input name="release_at" type="datetime-local" required></label>
        <label class="field c3">Xung đột lợi ích<select name="related"><option value="">Không liên quan bên liên quan</option><option value="1">Có: liên quan bên liên quan của ngân hàng</option></select></label>
        <fieldset class="c12 coi" style="border:1px dashed var(--axis);border-radius:10px;padding:10px 12px" hidden>
          <legend class="small muted">Công bố xung đột lợi ích (khách hàng đọc nguyên văn)</legend>
          <div class="cols">
            <label class="field c4">Bên liên quan<input name="parties" placeholder="Techcombank, TCBS"></label>
            <label class="field c8">Lời công bố (từ 20 ký tự)<input name="statement" placeholder="Báo cáo nhắc tới TCBS, công ty con của ngân hàng."></label>
          </div></fieldset>
        <label class="field c12">Tiêu đề<input name="title" required></label>
        <label class="field c12">Tóm tắt luận điểm<textarea name="summary" required></textarea></label>
        <fieldset class="c12 reg" style="border:1px dashed var(--axis);border-radius:10px;padding:10px 12px" hidden>
          <legend class="small muted">Ghi chú quy định</legend>
          <div class="cols">
            <label class="field c4">Tên văn bản<input name="document"></label>
            <label class="field c2">Trạng thái<select name="status"><option value="draft">Dự thảo</option><option value="issued">Đã ban hành</option></select></label>
            <label class="field c3">Ngày hiệu lực<input name="effective_date" type="date"></label>
            <label class="field c3">Số tuần chuẩn bị thêm<input name="prep_weeks" type="number" min="0" value="8"></label>
            <div class="field c12">Loại mục tiêu bị ảnh hưởng<div class="row">${Object.entries(purposes).map(([k, v]) => `<label class="chip"><input type="checkbox" name="purposes" value="${k}"> ${esc(v)}</label>`).join("")}</div></div>
            <label class="field c6">Nước đến (để trống = mọi nước)<input name="countries" placeholder="Úc, Mỹ"></label>
            <label class="field c6">Hồ sơ cần chuẩn bị<input name="documents" placeholder="Thư mời nhập học, Xác nhận học phí"></label>
            <label class="field c6">Thông điệp cho khách (chung cho mọi khách cùng loại mục tiêu)<textarea name="client_message"></textarea></label>
            <label class="field c6">Gợi ý cho RM<textarea name="rm_hint"></textarea></label>
          </div></fieldset>
        <div class="c12 row"><button class="btn primary" type="submit">Nạp, chờ Tuân thủ</button></div>
      </form></details></div>`}
    <div class="panel" style="padding:8px">${items.length ? items.map(i => {
      const st = STATUS[i.status] || ["", i.status];
      const m = byNote[i.id] || [];
      return `<div class="item" style="grid-template-columns:auto 1fr auto">
        <span class="badge">${esc(kinds[i.kind] || i.kind)}</span>
        <div><div class="t">${esc(i.title)}</div>
          <div class="m">${esc(i.report_no)} · phát hành ${when(i.release_at)} · nạp bởi ${esc(i.uploaded_by)}${i.decided_by ? ` · xử lý bởi ${esc(i.decided_by)}` : ""}</div>
          <div class="small" style="margin-top:4px">${esc(i.summary)}</div>
          <div class="small ${i.conflict && i.conflict.related ? "warn-text" : "muted"}" style="margin-top:4px">${i.conflict && i.conflict.related ? `Xung đột lợi ích (${esc(i.conflict.parties.join(", "))}): ${esc(i.conflict.statement)}` : "Không có xung đột lợi ích cần công bố"}</div>
          ${i.regulation ? `<div class="small muted" style="margin-top:4px">${esc(i.regulation.status === "issued" ? "Đã ban hành" : "Dự thảo")} · ${i.regulation.purposes.map(p => esc(purposes[p])).join(", ")} · chuẩn bị thêm ${i.regulation.prep_weeks} tuần</div>` : ""}
          ${m.length ? `<details class="more"><summary>${m.length} mục tiêu bị ảnh hưởng</summary>${m.map(x => `<div class="small" style="margin:4px 0"><span class="badge ${LEVEL[x.level]}">${esc(x.level_label)}</span> ${esc(x.family_name)} · ${esc(x.goal)} · mốc ${esc(x.milestone)}</div>`).join("")}</details>` : ""}
          ${isCompliance && i.status === "PENDING_RELEASE" ? `<div class="row" style="margin-top:8px"><input data-note="${esc(i.id)}" placeholder="Ghi chú của Tuân thủ (từ 20 ký tự)" style="flex:1;min-width:200px;padding:7px 10px;border:1px solid var(--axis);border-radius:9px;background:var(--surface);color:var(--ink)">
            <button type="button" class="btn sm primary" data-decide="release" data-id="${esc(i.id)}">Phát hành</button><button type="button" class="btn sm danger" data-decide="reject" data-id="${esc(i.id)}">Từ chối</button></div>` : ""}
        </div>
        <span class="badge ${st[0]}">${st[1]}</span></div>`;
    }).join("") : empty("Chưa có báo cáo nào", isCompliance ? "Báo cáo do bên nghiên cứu nạp sẽ chờ ở đây." : "Mở “Nạp báo cáo mới” để nạp.")}</div>`;

  const form = box.querySelector("#up");
  if (form) {
    const kind = form.querySelector("[name=kind]");
    kind.onchange = () => { form.querySelector(".reg").hidden = kind.value !== "regulation"; };
    const rel = form.querySelector("[name=related]");
    rel.onchange = () => { form.querySelector(".coi").hidden = !rel.value; };
    form.onsubmit = async (e) => {
      e.preventDefault();
      const f = new FormData(form);
      const local = f.get("release_at");
      const item = {kind: f.get("kind"), report_no: f.get("report_no"), title: f.get("title"), summary: f.get("summary"),
        release_at: local ? `${local}:00+07:00` : "",
        conflict: {related: !!f.get("related"), parties: String(f.get("parties") || "").split(",").map(s => s.trim()).filter(Boolean), statement: f.get("statement") || ""}};
      if (item.kind === "regulation") {
        const list = (k) => String(f.get(k) || "").split(",").map(s => s.trim()).filter(Boolean);
        item.regulation = {document: f.get("document"), status: f.get("status"), effective_date: f.get("effective_date") || null,
          prep_weeks: Number(f.get("prep_weeks") || 0), purposes: f.getAll("purposes"), countries: list("countries"),
          documents: list("documents"), client_message: f.get("client_message"), rm_hint: f.get("rm_hint")};
      }
      try { const r = await post("/api/research", {item, by: ctx.user}); toast(`Đã nạp ${r.item.id}; chờ Tuân thủ`); render(box, ctx); }
      catch (err) { toast(err.message); }
    };
  }
  box.querySelectorAll("[data-decide]").forEach(b => {
    b.onclick = async () => {
      const note = box.querySelector(`[data-note="${CSS.escape(b.dataset.id)}"]`).value.trim();
      try { await post("/api/research/release", {item_id: b.dataset.id, decision: b.dataset.decide, by: ctx.user, note}); toast("Đã ghi"); }
      catch (e) { toast(e.message); }
      render(box, ctx);
    };
  });
}
