/* Tuân thủ · Nhật ký (FR-702): the append-only chain of every action, and its check. */
import {esc, get, when} from "../core/core.js";

const ACTION = {
  "news.add": "Nạp tin", "news.grouped": "Gom tin", "news.dismissed": "Bỏ tin", "news.release": "Cho phép tin bị giữ",
  "event.create": "Lập sự kiện", "view.create": "Tạo nhận định", "view.save": "Đổi nhận định", "agent.start": "Agent bắt đầu",
  "agent.finish": "Agent xong", "challenge.add": "Phản biện", "run.create": "Tạo lần áp dụng", "run.computed": "Tính xong",
  "run.status": "Đổi trạng thái lần áp dụng",
};

export async function render(box) {
  const [v, {rows}] = await Promise.all([get("/api/audit/verify"), get("/api/audit?limit=200")]);
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Tuân thủ · Nhật ký</div>
      <div class="h1">${v.ok ? '<span class="up">✓</span> Chuỗi toàn vẹn' : '<span class="down">✕</span> Chuỗi bị gãy'} · ${v.count} dòng</div>
      <div class="lede small">${v.ok ? `Mỗi dòng chứa mã băm của dòng trước (${esc((v.algorithms || []).join(", ") || "sha256")}); cơ sở dữ liệu chặn sửa và xóa.` : `Gãy ở dòng ${v.broken_at}: ${esc(v.reason)}`}</div></div></div>
    <div class="panel"><div class="scrollx"><table class="table"><thead><tr><th>#</th><th>Lúc</th><th>Ai</th><th>Việc</th><th>Đối tượng</th><th>Mã băm</th></tr></thead><tbody>
      ${rows.map(r => `<tr><td class="num">${r.seq}</td><td class="small num">${when(r.ts)}</td><td>${esc(r.actor)}</td><td>${esc(ACTION[r.action] || r.action)}${r.action.startsWith("decision.") ? ` <span class="badge human">${esc(r.action.slice(9))}</span>` : ""}</td>
        <td class="small">${esc(r.object.length > 40 ? r.object.slice(0, 40) + "…" : r.object)}</td><td class="small muted num">${esc(r.hash.slice(0, 12))}</td></tr>`).join("")}
    </tbody></table></div></div>`;
}
