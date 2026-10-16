/* Cấu hình (BRD FR-701, SEC-05): each kind of configuration, the version in force, a pending proposal, the history.
   The owner's role proposes; a user of the same role approves — another person where §13.1 asks for two. Everyone
   acts as themselves (signed in). A prompt or model proposal shows the fixed eval set's result: it is approved only
   when the set passed (MEAS-07). */
import {esc, get, n as how, post, toast, when} from "../core/core.js";

const STATUS = {ACTIVE: ["good", "Đang áp dụng"], PROPOSED: ["warn", "Chờ duyệt"], SUPERSEDED: ["", "Đã thay"], REJECTED: ["bad", "Từ chối"]};
const LABEL = {pre_review_pct: "RM xem trước khi P10 3 tháng ≤ (tỷ lệ tài sản ròng)", concentration_share: "Hậu kiểm: một tài sản chiếm >",
  modelled_share: "Hậu kiểm: phần tính theo mô hình >", implausible_share: "Hậu kiểm: tác động 3 tháng >",
  safe: "Tiền gửi 12 tháng", growth: "Danh mục cân bằng, dài hạn", inflation: "Lạm phát", withdrawal: "Tỷ lệ rút an toàn",
  rental_yield: "Lợi suất cho thuê BĐS", best_deposit: "Lãi tiền gửi tốt nhất"};
const pc = (x) => `${(x * 100).toLocaleString("vi-VN", {maximumFractionDigits: 2})} %`;
const MODE = {live: "Chạy thật trong TCB (live)", inbox: "Hộp chờ: vùng AI chạy, TCB nhập gói đã ký", mock: "Mô phỏng, không gọi mô hình"};
const NO_EDIT = ["factor_model"];  // proposed from Mô hình (estimate) or by the API: too large to edit here

function summary(k, d) {
  if (!d) return "";
  if (k === "thresholds") return Object.entries(d).map(([x, v]) => `${LABEL[x] || x}: <b class="num">${v}</b>`).join("<br>");
  if (k === "return_assumptions") return Object.entries(d).map(([x, v]) => `${LABEL[x] || x}: <b class="num">${how(pc(v), "setting.return", {key: LABEL[x] || x})}</b>`).join("<br>");
  if (k === "restricted") return d.map(r => `${esc(r.name)} (${esc(r.ticker)})`).join(", ");
  if (k === "forbidden_phrases") return `Khuyến nghị mua/bán: ${d.recommendation.length} cụm (${d.recommendation.slice(0, 4).map(esc).join(", ")}…)<br>Ghi chú quy định: ${d.compliance.length} cụm`;
  if (k === "consent") return `Mẫu ${esc(d.version)} · cần đồng ý cho: ${[d.require.open_api && "Open API", d.require.family_member && "thành viên gia đình"].filter(Boolean).join(", ") || "không"}<div class="muted">${esc(d.text)}</div>`;
  if (k === "news_sources") return `${d.length} nguồn: ${d.map(s => esc(s.outlet || s.id)).join(", ")}`;
  if (k === "price_sources") return `${(d.series || []).length} chuỗi · ${Object.keys(d.jobs || {}).length} việc lấy dữ liệu`;
  if (k === "ticker_map") return `${Object.keys(d).length} mã`;
  if (k === "factor_model") return `Phiên bản ${esc(d.version || "—")} · ${(d.factors || []).length} yếu tố${(d.loadings || {}).classes ? ` · ${Object.keys(d.loadings.classes).length} loại tài sản khai báo` : ""}`;
  if (k === "prompts") return `${Object.keys(d.lenses || {}).length} nhóm phân tích (${Object.values(d.lenses || {}).map(l => esc(l.label)).join(", ")}) · lời nhắc: ${["analyst", "debate", "synthesize", "challenge"].map(x => `${x} ${(d[x] || "").length} ký tự`).join(", ")}`;
  if (k === "ai_mode") return `<b>${esc(MODE[d.mode] || d.mode)}</b>`;
  if (k === "rm_assignment") return Object.entries(Object.entries(d).reduce((m, [f, rm]) => ((m[rm] = (m[rm] || 0) + 1), m), {}))
    .map(([rm, n]) => `${esc(rm)}: <b class="num">${n}</b> gia đình`).join(" · ");
  if (k === "models") return `Agent CIO: <b>${esc(d.cio || "chưa đặt")}</b> · Agent Phản biện: <b>${esc(d.challenger || "chưa đặt")}</b>`;
  return "";
}

function changed(now, next) {  // what a proposal changes, by field (an object's keys; a list compares whole)
  if (!now || !next || Array.isArray(next) || typeof next !== "object") return "";
  const same = (x, y) => JSON.stringify(x) === JSON.stringify(y);
  const out = [];
  for (const k of new Set([...Object.keys(now), ...Object.keys(next)])) {
    if (same(now[k], next[k])) continue;
    const sub = now[k] && next[k] && typeof next[k] === "object" && !Array.isArray(next[k])
      ? [...new Set([...Object.keys(now[k]), ...Object.keys(next[k])])].filter(x => !same(now[k][x], next[k][x])) : [];
    out.push(sub.length ? `${k} (${sub.join(", ")})` : k);
  }
  return `<div class="small mt">Thay đổi: <b>${out.length ? out.map(esc).join(", ") : "không có"}</b></div>`;
}

function evalBox(ev) {
  if (!ev) return `<div class="small mt"><span class="badge">Bộ đánh giá</span> đang chờ chạy (mỗi phút).</div>`;
  if (ev.status === "running") return `<div class="small mt"><span class="badge warn">Bộ đánh giá</span> đang chạy từ ${when(ev.started)}…</div>`;
  return `<div class="small mt"><span class="badge ${ev.passed ? "good" : "bad"}">${ev.passed ? "Đạt bộ đánh giá" : "Không đạt"}</span> ${esc(ev.summary || "")}</div>
    ${ev.samples ? `<table class="table mt"><tbody>${ev.samples.map(r => `<tr><td class="small">${esc(r.id)} · ${esc(r.title)}</td>
      <td class="small">${r.valid ? "hợp lệ" : `<span class="bad-text">không hợp lệ</span>`}${r.challenged ? " · có phản biện" : ""}</td>
      <td class="small">${r.direction_hit ? "đúng hướng" : `<span class="bad-text">sai hướng</span>`} ${esc(r.expect.factor)} ${r.expect.direction === "up" ? "▲" : "▼"}</td></tr>`).join("")}</tbody></table>` : ""}`;
}

export async function render(box, ctx) {
  const {kinds} = await get("/api/config");
  const me = ctx.user;
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Cấu hình có phiên bản</div>
      <div class="h1">${kinds.length} loại cấu hình · ${kinds.filter(k => k.pending).length} đề xuất chờ duyệt</div>
      <div class="lede small">Đề xuất rồi duyệt (FR-701). Hai người cho mô hình yếu tố, ngưỡng cảnh báo, danh sách hạn chế, lời nhắc và mô hình AI (§13.1; ADR-0016).
        Lời nhắc và mô hình AI chỉ được duyệt khi đạt bộ đánh giá cố định (MEAS-07). Mỗi bước vào nhật ký.</div></div></div>
    <div class="cols">${kinds.map(k => {
      const own = k.owner === ctx.role, a = k.active, p = k.pending;
      const mine = p && p.proposed_by === me;
      const blocked = k.eval && p && !(p.eval && p.eval.status === "done" && p.eval.passed);
      return `<div class="panel c6" data-kind="${k.kind}">
        <h3>${esc(k.label)} <span class="hint">chủ sở hữu ${esc(k.owner_label)}${k.two_person ? " · hai người" : ""}${k.eval ? " · bộ đánh giá" : ""}</span></h3>
        <div class="small"><span class="badge good">v${a.version}</span> ${esc(a.id)} · <span class="muted num">${esc(a.hash.slice(0, 12))}</span>${a.decided_by ? ` · duyệt bởi ${esc(a.decided_by)}` : ` · ${esc(a.proposed_by)}`}</div>
        <div class="small mt">${summary(k.kind, a.data)}</div>
        ${p ? `<div class="card mt" style="padding:12px"><div><span class="badge warn">Chờ duyệt</span> v${p.version} · đề xuất bởi ${esc(p.proposed_by)} ${when(p.created)}${p.note ? ` · “${esc(p.note)}”` : ""}</div>
            <div class="small mt">${summary(k.kind, p.data)}</div>
            ${changed(a.data, p.data)}
            ${k.eval ? evalBox(p.eval) : ""}
            ${own && !(k.two_person && mine) ? `<div class="row mt">
              <button type="button" class="btn sm" data-decide="approve" data-id="${esc(p.id)}" ${blocked ? "disabled" : ""}>Duyệt</button>
              <button type="button" class="btn sm ghostbtn" data-decide="reject" data-id="${esc(p.id)}">Từ chối</button></div>`
            : own ? `<div class="small muted mt">Bạn đã đề xuất: cần một ${esc(k.owner_label)} khác duyệt (§13.1).</div>`
            : `<div class="small muted mt">Chỉ ${esc(k.owner_label)} duyệt.</div>`}</div>`
          : own && !NO_EDIT.includes(k.kind) ? `<details class="more mt"><summary>Đề xuất thay đổi</summary>
            <textarea data-edit rows="${["thresholds", "return_assumptions", "models"].includes(k.kind) ? 7 : 12}" style="width:100%;font-family:monospace;font-size:12px;margin-top:8px">${esc(JSON.stringify(a.data, null, 1))}</textarea>
            <div class="row mt"><input data-note placeholder="Lý do" style="flex:1"><button type="button" class="btn sm" data-propose>Gửi đề xuất</button></div></details>`
          : own ? `<div class="small muted mt">Đề xuất từ trang Mô hình (ước lượng) hoặc qua <code>POST /api/config/propose</code>.</div>` : ""}
        <details class="more mt"><summary>Lịch sử (${k.versions.length})</summary><table class="table"><tbody>${k.versions.map(v => `<tr><td>v${v.version}</td><td><span class="badge ${(STATUS[v.status] || [""])[0]}">${(STATUS[v.status] || ["", v.status])[1]}</span></td><td class="small">${esc(v.proposed_by || "")}${v.decided_by ? " → " + esc(v.decided_by) : ""}${v.eval && v.eval.status === "done" ? ` · đánh giá ${v.eval.passed ? "đạt" : "không đạt"}` : ""}</td><td class="small muted">${v.created ? when(v.created) : "tệp gốc"}</td></tr>`).join("")}</tbody></table></details>
      </div>`;
    }).join("")}</div>`;
  for (const b of box.querySelectorAll("[data-decide]")) b.onclick = async () => {
    try { await post("/api/config/decide", {version_id: b.dataset.id, action: b.dataset.decide, by: me}); toast(b.dataset.decide === "approve" ? "Đã duyệt" : "Đã từ chối"); }
    catch (e) { toast("Không thực hiện được: " + e.message); }
    render(box, ctx);
  };
  for (const b of box.querySelectorAll("[data-propose]")) b.onclick = async () => {
    const panel = b.closest("[data-kind]");
    let data;
    try { data = JSON.parse(panel.querySelector("[data-edit]").value); } catch (_) { toast("JSON không hợp lệ"); return; }
    try { await post("/api/config/propose", {kind: panel.dataset.kind, data, by: me, note: panel.querySelector("[data-note]").value}); toast("Đã gửi đề xuất"); }
    catch (e) { toast("Không gửi được: " + e.message); }
    render(box, ctx);
  };
}
