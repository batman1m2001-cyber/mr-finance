/* Danh mục agent (BRD FR-703) and AI quality (RULE-MEAS-04): one card per language-model task, what it may read,
   who owns it, its risk, the BRD's default model and the one configured now, its latest run; then the week's
   figures from what is stored. */
import {esc, get, pct, when} from "../core/core.js";

const MODE = {live: ["good", "Trực tiếp"], mock: ["", "Mô phỏng"], keyword: ["", "Từ khóa (mô phỏng)"],
  template: ["", "Mẫu tất định"], not_built: ["warn", "Chưa xây"]};
const RISK = {"cao": "bad", "trung bình": "warn", "thấp": ""};

export async function render(box) {
  const d = await get("/api/agents/catalogue?days=7");
  const q = d.quality;
  const fig = (k, label, f = (x) => x) => `<tr><td>${label}</td><td class="r num">${q.recent[k] == null ? "—" : f(q.recent[k])}</td><td class="r num muted">${q.all_time[k] == null ? "—" : f(q.all_time[k])}</td></tr>`;
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Danh mục agent</div>
      <div class="h1">${d.agents.length} tác vụ dùng mô hình ngôn ngữ</div>
      <div class="lede small">Mục đích, chủ sở hữu, mức rủi ro, mô hình, lần chạy gần nhất (BRD FR-703). Phiên bản lời nhắc ${esc(d.prompt_version)}.</div></div></div>
    <div class="cols">
      ${d.agents.map(a => `<div class="panel c6">
        <h3>${esc(a.name)} <span class="badge ${MODE[a.mode] ? MODE[a.mode][0] : ""}">${esc(MODE[a.mode] ? MODE[a.mode][1] : a.mode)}</span></h3>
        <p style="margin:0 0 8px">${esc(a.purpose)}</p>
        <table class="table"><tbody>
          <tr><td class="muted">Chủ sở hữu</td><td>${esc(a.owner)}</td></tr>
          <tr><td class="muted">Mức rủi ro</td><td><span class="badge ${RISK[a.risk] || ""}">${esc(a.risk)}</span> <span class="small">${esc(a.risk_why)}</span></td></tr>
          <tr><td class="muted">Mô hình</td><td>${esc(a.model)}<div class="small muted">BRD: ${esc(a.brd_model)}${a.resource ? ` · tài nguyên ${esc(a.resource)}` : ""}</div></td></tr>
          <tr><td class="muted">Được đọc</td><td class="small">${esc(a.reads)}</td></tr>
          <tr><td class="muted">Lần chạy gần nhất</td><td class="small">${a.latest_run ? `${esc(a.latest_run.id)} · ${esc(a.latest_run.subject)} · ${when(a.latest_run.at)} · ${esc(a.latest_run.mode)} · ${esc(a.latest_run.status)}` : a.built ? "—" : "chưa xây (FEAT-16)"}</td></tr>
        </tbody></table></div>`).join("")}
      <div class="panel c6"><h3>Chất lượng AI <span class="hint">${q.days} ngày qua · từ đầu</span></h3>
        <table class="table"><thead><tr><th></th><th class="r">${q.days} ngày</th><th class="r">Từ đầu</th></tr></thead><tbody>
          ${fig("decided", "Nhận định đã quyết")}${fig("edited_share", "Tỷ lệ CIO sửa kịch bản", (x) => pct(x, false, 0))}
          ${fig("findings", "Phát hiện của phản biện")}${fig("critical_findings", "— trong đó nghiêm trọng")}
          ${fig("agent_runs", "Lần chạy agent")}${fig("failed_runs", "— lỗi")}${fig("format_retries", "Viết lại vì sai định dạng")}
        </tbody></table><div class="footnote">Đếm từ dữ liệu đã lưu (nhận định, phản biện, lần chạy agent); BRD §16.3.</div></div>
      <div class="panel c6"><h3>Tham khảo mã nguồn mở</h3>
        <ul>${d.references.map(r => `<li><b>${esc(r.name)}</b> (${esc(r.license)}): ${esc(r.use)}</li>`).join("")}</ul></div>
    </div>`;
}
