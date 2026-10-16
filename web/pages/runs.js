/* CIO · Lần áp dụng: every run, its post-check, and what the CIO can do with it — verify (recompute
   from the frozen snapshot), recompute on today's data, make a held run effective, withdraw. */
import {empty, esc, get, post, runBadge, severity, signClass, toast, vnd, when} from "../core/core.js";

export async function render(box, ctx) {
  const {runs} = await get("/api/runs");
  if (!runs.length) {
    box.innerHTML = `<div class="panel">${empty("Chưa có lần áp dụng", "Một lần áp dụng được tạo khi CIO duyệt nhận định.")}</div>`;
    return;
  }
  const run = runs.find(r => r.id === ctx.param) || runs[0];
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO · Lần áp dụng</div><div class="h1">${esc(run.id)} ${runBadge(run.status, run.status_label)}</div>
      <div class="lede small">Nhận định <a href="#/cio/nhan-dinh/${esc(run.view_id)}">${esc(run.view_id)}</a> · ${run.families} gia đình · giá ngày ${esc(run.price_date || "—")} · mô hình ${esc(run.model ? run.model.version : "—")} · ${esc(run.engine_version || "")}</div></div>
      <div class="row">
        <a class="btn" href="#/cio/do-thi/${esc(run.id)}">Xem đồ thị</a>
        <button type="button" class="btn" id="verify">Kiểm tra tính lại</button>
        <button type="button" class="btn" id="recompute">Thẩm định lại với dữ liệu mới</button></div></div>
    <div class="cols">
      <div class="panel c4"><div class="eyebrow">Tổng kỳ vọng 3 tháng</div>
        <div class="hero md ${signClass(run.totals && run.totals.expected_3m)}" style="margin-top:8px">${run.totals ? vnd(run.totals.expected_3m, true) : "—"}</div>
        <div class="takeaway">${run.totals ? run.totals.pre_review : 0} gia đình cần RM xem trước.</div>
        <div class="footnote num" style="word-break:break-all">Ảnh chụp ${esc(run.snapshot_id || "—")}<br>SHA-256 ${esc(run.snapshot_hash || "—")}</div>
        <div id="verify-out" class="small" style="margin-top:8px"></div></div>
      <div class="panel c8"><h3>Hậu kiểm <span class="hint">${run.postcheck ? esc(run.postcheck.summary) : ""}</span></h3>
        ${run.postcheck && run.postcheck.findings.length ? run.postcheck.findings.map(f => `<div style="padding:6px 0;border-bottom:1px solid var(--hair)">${severity(f.severity)} <b>${esc(f.title)}</b>${f.family_id ? ` · ${esc(f.family_id)}` : ""}<div class="small muted">${esc(f.detail)}</div></div>`).join("") : '<div class="small muted">Không có phát hiện.</div>'}
        ${["NEEDS_CIO_REVIEW", "EFFECTIVE"].includes(run.status) ? `<label class="field" style="margin-top:12px">Lý do<textarea id="reason"></textarea></label>
        <div class="row" style="margin-top:8px">${run.status === "NEEDS_CIO_REVIEW" ? '<button type="button" class="btn primary" data-act="make_effective">Cho hiệu lực</button>' : ""}
        <button type="button" class="btn danger" data-act="withdraw">Thu hồi lần áp dụng</button></div>` : ""}</div>
      <div class="panel c12"><h3>Lịch sử trạng thái</h3>${(run.history || []).map(h => `<div class="row" style="gap:10px;margin:4px 0"><span class="small muted num">${when(h.at)}</span>${runBadge(h.status, h.status)}<span class="small">${esc(h.by)}${h.note ? ` · ${esc(h.note)}` : ""}</span></div>`).join("")}</div>
      <div class="panel c12"><h3>Mọi lần áp dụng</h3><div class="scrollx"><table class="table"><thead><tr><th>Mã</th><th>Trạng thái</th><th class="r">Kỳ vọng 3 tháng</th><th class="r">Xem trước</th><th>Lúc</th></tr></thead><tbody>
        ${runs.map(r => `<tr class="click" data-id="${esc(r.id)}"><td>${esc(r.id)}</td><td>${runBadge(r.status, r.status_label)}</td><td class="r ${signClass(r.totals && r.totals.expected_3m)}">${r.totals ? vnd(r.totals.expected_3m, true) : "—"}</td><td class="r">${r.totals ? r.totals.pre_review : "—"}</td><td class="small">${when(r.created)}</td></tr>`).join("")}
      </tbody></table></div></div>
    </div>`;
  box.querySelectorAll("[data-id]").forEach(r => { r.onclick = () => ctx.go(ctx.href("ap-dung", r.dataset.id)); });
  box.querySelector("#verify").onclick = async () => {
    const out = box.querySelector("#verify-out");
    out.textContent = "Đang tính lại từ ảnh chụp…";
    try {
      const v = await get(`/api/runs/${encodeURIComponent(run.id)}/verify`);
      out.innerHTML = v.ok ? `<span class="badge good">Khớp tới từng đồng</span> ${v.families} gia đình` : `<span class="badge bad">Lệch</span> ${esc(v.differences.slice(0, 5).join("; "))}`;
    } catch (e) { out.textContent = e.message; }
  };
  box.querySelector("#recompute").onclick = async (e) => {
    e.target.disabled = true;
    try {
      const r = await post("/api/runs/recompute", {run: run.id, by: ctx.user});
      const moved = r.compare.filter(c => c.delta).length;
      toast(`Tạo ${r.run.id}; ${moved} gia đình thay đổi`);
      ctx.go(ctx.href("ap-dung", r.run.id));
    } catch (err) { toast(err.message); e.target.disabled = false; }
  };
  box.querySelectorAll("[data-act]").forEach(b => {
    b.onclick = async () => {
      try { await post("/api/runs/decide", {run: run.id, action: b.dataset.act, by: ctx.user, reason: box.querySelector("#reason").value.trim()}); toast("Đã ghi"); }
      catch (e) { toast(e.message); }
      ctx.go(location.hash);
    };
  });
}
