/* Cấu hình (BRD FR-701): each kind of configuration, the version in force, a pending proposal, the history.
   The owner's role proposes; a user of the same role approves — a different person where §13.1 asks for two.
   “Duyệt với tư cách” picks which demo user of the role acts (the switcher is not security, ADR-0006). */
import {$, esc, get, post, toast, when} from "../core/core.js";

const STATUS = {ACTIVE: ["good", "Đang áp dụng"], PROPOSED: ["warn", "Chờ duyệt"], SUPERSEDED: ["", "Đã thay"], REJECTED: ["bad", "Từ chối"]};
const LABEL = {pre_review_pct: "RM xem trước khi P10 3 tháng ≤ (tỷ lệ tài sản ròng)", concentration_share: "Hậu kiểm: một tài sản chiếm >",
  modelled_share: "Hậu kiểm: phần tính theo mô hình >", implausible_share: "Hậu kiểm: tác động 3 tháng >"};

function summary(k, d) {
  if (k === "thresholds") return Object.entries(d).map(([x, v]) => `${LABEL[x] || x}: <b class="num">${v}</b>`).join("<br>");
  if (k === "restricted") return d.map(r => `${esc(r.name)} (${esc(r.ticker)})`).join(", ");
  if (k === "news_sources") return `${d.length} nguồn: ${d.map(s => esc(s.outlet || s.id)).join(", ")}`;
  if (k === "factor_model") return `Phiên bản ${esc(d.version || "—")} · ${(d.factors || []).length} yếu tố`;
  return "";
}

export async function render(box, ctx) {
  const {kinds, users} = await get("/api/config");

  const actors = (role) => users.filter(u => u.role === role);
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Cấu hình có phiên bản</div>
      <div class="h1">${kinds.length} loại cấu hình · ${kinds.filter(k => k.pending).length} đề xuất chờ duyệt</div>
      <div class="lede small">Đề xuất rồi duyệt (FR-701). Hai người cho mô hình yếu tố, ngưỡng cảnh báo và danh sách hạn chế (§13.1, F14; ADR-0016). Mỗi bước vào nhật ký.</div></div></div>
    <div class="cols">${kinds.map(k => {
      const own = k.owner === ctx.role, a = k.active, p = k.pending;
      const who = actors(k.owner).map(u => `<option value="${esc(u.id)}">${esc(u.name)}</option>`).join("");
      // two people: the proposer is not offered as approver (the server refuses it too)
      const approvers = actors(k.owner).filter(u => !(k.two_person && p && u.id === p.proposed_by))
        .map(u => `<option value="${esc(u.id)}">${esc(u.name)}</option>`).join("");
      return `<div class="panel c6" data-kind="${k.kind}">
        <h3>${esc(k.label)} <span class="hint">chủ sở hữu ${esc(k.owner_label)}${k.two_person ? " · hai người" : ""}</span></h3>
        <div class="small"><span class="badge good">v${a.version}</span> ${esc(a.id)} · <span class="muted num">${esc(a.hash.slice(0, 12))}</span>${a.decided_by ? ` · duyệt bởi ${esc(a.decided_by)}` : ` · ${esc(a.proposed_by)}`}</div>
        <div class="small mt">${summary(k.kind, a.data)}</div>
        ${p ? `<div class="card mt" style="padding:12px"><div><span class="badge warn">Chờ duyệt</span> v${p.version} · đề xuất bởi ${esc(p.proposed_by)} ${when(p.created)}${p.note ? ` · “${esc(p.note)}”` : ""}</div>
            <div class="small mt">${summary(k.kind, p.data)}</div>
            ${own ? `<div class="row mt"><select data-actor aria-label="Duyệt với tư cách">${approvers}</select>
              <button type="button" class="btn sm" data-decide="approve" data-id="${esc(p.id)}">Duyệt</button>
              <button type="button" class="btn sm ghostbtn" data-decide="reject" data-id="${esc(p.id)}">Từ chối</button></div>
              ${k.two_person ? `<div class="small muted">Người đề xuất (${esc(p.proposed_by)}) không tự duyệt: cần người thứ hai.</div>` : ""}` : `<div class="small muted mt">Chỉ ${esc(k.owner_label)} duyệt.</div>`}</div>`
          : own && ["thresholds", "restricted"].includes(k.kind) ? `<details class="more mt"><summary>Đề xuất thay đổi</summary>
            <textarea data-edit rows="${k.kind === "thresholds" ? 6 : 9}" style="width:100%;font-family:monospace;font-size:12px;margin-top:8px">${esc(JSON.stringify(a.data, null, 1))}</textarea>
            <div class="row mt"><input data-note placeholder="Lý do" style="flex:1"><select data-actor aria-label="Đề xuất với tư cách">${who}</select><button type="button" class="btn sm" data-propose>Gửi đề xuất</button></div></details>`
          : own ? `<div class="small muted mt">Đề xuất qua <code>POST /api/config/propose</code> (tệp lớn).</div>` : ""}
        <details class="more mt"><summary>Lịch sử (${k.versions.length})</summary><table class="table"><tbody>${k.versions.map(v => `<tr><td>v${v.version}</td><td><span class="badge ${(STATUS[v.status] || [""])[0]}">${(STATUS[v.status] || ["", v.status])[1]}</span></td><td class="small">${esc(v.proposed_by || "")}${v.decided_by ? " → " + esc(v.decided_by) : ""}</td><td class="small muted">${v.created ? when(v.created) : "tệp gốc"}</td></tr>`).join("")}</tbody></table></details>
      </div>`;
    }).join("")}</div>`;
  for (const b of box.querySelectorAll("[data-decide]")) b.onclick = async () => {
    const panel = b.closest("[data-kind]");
    try { await post("/api/config/decide", {version_id: b.dataset.id, action: b.dataset.decide, by: $("[data-actor]", panel).value}); toast(b.dataset.decide === "approve" ? "Đã duyệt" : "Đã từ chối"); }
    catch (e) { toast("Không thực hiện được: " + e.message); }
    render(box, ctx);
  };
  for (const b of box.querySelectorAll("[data-propose]")) b.onclick = async () => {
    const panel = b.closest("[data-kind]");
    let data;
    try { data = JSON.parse($("[data-edit]", panel).value); } catch (_) { toast("JSON không hợp lệ"); return; }
    try { await post("/api/config/propose", {kind: panel.dataset.kind, data, by: $("[data-actor]", panel).value, note: $("[data-note]", panel).value}); toast("Đã gửi đề xuất"); }
    catch (e) { toast("Không gửi được: " + e.message); }
    render(box, ctx);
  };
}
