/* CIO · Tin bị giữ (BR-04; Compliance's until OWN-FB-18): news that names someone on the restricted list waits here; releasing
   it needs a reason, kept in the audit chain. The list itself is a mock (invented names). */
import {empty, esc, get, post, toast, when} from "../core/core.js";

export async function render(box, ctx) {
  const [{items}, cfg] = await Promise.all([get("/api/news/inbox?held=1"), get("/api/news/config")]);
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO · Danh sách hạn chế</div><div class="h1">${items.length} tin đang bị giữ</div>
      <div class="lede small">Sự kiện chứa tin này không chạy được Agent CIO cho tới khi một CIO cho đi tiếp.</div></div></div>
    <div class="cols">
      <div class="panel c8">${items.length ? items.map(i => `
        <div style="padding:10px 0;border-bottom:1px solid var(--hair)">
          <div><b>${esc(i.title)}</b></div>
          <div class="small muted">${esc(i.outlet)} · ${when(i.published)} · nhắc tới ${i.restricted.map(r => `<span class="badge bad">${esc(r)}</span>`).join(" ")}</div>
          <div class="row" style="margin-top:8px"><input data-note="${esc(i.id)}" placeholder="Lý do cho phép (bắt buộc)" style="flex:1;min-width:200px;padding:7px 10px;border:1px solid var(--axis);border-radius:9px;background:var(--surface);color:var(--ink)">
            <button type="button" class="btn sm primary" data-release="${esc(i.id)}">Cho phép</button></div>
        </div>`).join("") : empty("Không có tin nào bị giữ")}</div>
      <div class="panel c4"><h3>Danh sách hạn chế <span class="badge assumed">giả lập</span></h3>
        ${cfg.restricted.map(r => `<div style="margin:6px 0"><b>${esc(r.name)}</b> <span class="small muted">${esc(r.ticker)}</span><div class="small muted">${r.aliases.map(esc).join(", ")}</div></div>`).join("")}
        <div class="footnote">Tên tự đặt cho demo; danh sách thật của ngân hàng không nằm trong mã nguồn này.</div>
        <h3 style="margin-top:16px">Danh sách trắng <span class="hint">${cfg.sources.length} nguồn công khai</span></h3>
        ${cfg.sources.map(s => `<div class="small" style="margin:3px 0">${esc(s.outlet)} · ${esc(s.section)}</div>`).join("")}</div>
    </div>`;
  box.querySelectorAll("[data-release]").forEach(b => {
    b.onclick = async () => {
      const note = box.querySelector(`[data-note="${CSS.escape(b.dataset.release)}"]`).value.trim();
      try { await post("/api/news/release", {item_id: b.dataset.release, by: ctx.user, note}); toast("Đã cho phép"); }
      catch (e) { toast(e.message); }
      render(box, ctx);
    };
  });
}
