/* RM · Hôm nay: the families to look at first — flagged for pre-review by an effective run
   (3-month P10 at or below −5 % of net worth), worst first. */
import {internal, empty, esc, get, pct, signClass, vnd, n as how} from "../core/core.js";

const LEVEL = {contact_now: "bad", confirm_goal: "human", remind: "warn", note: ""};

export async function render(box, ctx) {
  const d = await get("/api/rm/today");
  // one row per family: an RM calls a family once, whatever the number of events
  const byFamily = {};
  for (const c of d.cases) {
    const f = byFamily[c.family_id] || (byFamily[c.family_id] = {family_id: c.family_id, name: c.name, net_worth: c.net_worth,
      expected_3m: 0, worst: c, events: []});
    f.expected_3m += c.expected_3m;
    f.events.push(c.event.title);
    if (c.p10_3m_pct < f.worst.p10_3m_pct) f.worst = c;
  }
  const cases = Object.values(byFamily).sort((a, b) => a.worst.p10_3m_pct - b.worst.p10_3m_pct);
  const families = new Set(cases.map(c => c.family_id));
  box.innerHTML = `${internal()}
    <div class="cols">
      <div class="panel hero-panel c4">
        <div class="eyebrow">Hôm nay · cần xem trước</div>
        <div class="hero" style="margin-top:10px">${families.size}</div>
        <div class="takeaway">gia đình có kịch bản xấu 3 tháng (P10) chạm ngưỡng ${how(pct(d.threshold_pct, true, 0), "threshold.pre_review")} tài sản ròng.</div>
        <div class="footnote">Chỉ tính các lần áp dụng đã qua hậu kiểm và đang hiệu lực. Liên hệ khách theo thứ tự dưới đây.</div>
      </div>
      <div class="panel c8">
        <h3>Danh sách <span class="hint">xấu nhất trước</span></h3>
        ${cases.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Gia đình</th><th>Sự kiện chạm ngưỡng</th><th class="r">Kỳ vọng 3 tháng</th><th class="r">P10 xấu nhất</th><th></th></tr></thead><tbody>
          ${cases.map(c => `<tr class="click" data-family="${esc(c.family_id)}" data-focus="family:${esc(c.family_id)}">
            <td><b>${esc(c.name)}</b><div class="small muted">${how(vnd(c.net_worth), "net_worth")} tài sản ròng</div></td>
            <td class="small" data-quote>${c.events.map(esc).join("<br>")}</td>
            <td class="r ${signClass(c.expected_3m)}">${how(vnd(c.expected_3m, true), "impact.expected_3m", {event: c.events.join(", ")})}<div class="small muted">${how(pct(c.net_worth ? c.expected_3m / c.net_worth : 0, true, 2), "impact.expected_3m", {event: c.events.join(", ")})}</div></td>
            <td class="r down"><b>${how(pct(c.worst.p10_3m_pct, true, 1), "impact.p10_3m", {event: c.worst.event.title})}</b><div class="small muted" data-quote>${esc(c.worst.event.title)}</div></td>
            <td><span class="btn sm">Mở</span></td></tr>`).join("")}
        </tbody></table></div>` : empty("Không có ca nào cần xem trước", `Khi một lần áp dụng có gia đình chạm ngưỡng ${how(pct(d.threshold_pct, true, 0), "threshold.pre_review")}, ca đó hiện ở đây.`)}
      </div>
      <div class="panel c12"><h3>Việc theo mục tiêu <span class="hint">quy định mới làm chậm mục tiêu chuyển tiền ra nước ngoài</span></h3>
        ${d.goal_tasks.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Mức</th><th>Gia đình · mục tiêu</th><th>Văn bản</th><th>Mốc chuẩn bị</th><th>Việc của RM</th></tr></thead><tbody>
          ${d.goal_tasks.map(t => `<tr class="click" data-family="${esc(t.family_id)}" data-focus="family:${esc(t.family_id)}"><td><span class="badge ${LEVEL[t.level]}">${esc(t.level_label)}</span></td>
            <td><b>${esc(t.family_name)}</b><div class="small">${esc(t.goal)} · ${esc(t.purpose_label)}${t.country ? ` · ${esc(t.country)}` : ""}</div></td>
            <td class="small">${esc(t.note_title)}<div class="muted">${t.note_status === "issued" ? "Đã ban hành" : "Dự thảo"}</div></td>
            <td class="num">${esc(t.milestone)}</td><td class="small">${esc(t.rm_hint || "")}</td></tr>`).join("")}
        </tbody></table></div>` : empty("Không có việc nào theo mục tiêu", "Khi Tuân thủ phát hành ghi chú quy định khớp mục tiêu của khách, việc hiện ở đây.")}
      </div>
    </div>`;
  box.querySelectorAll("[data-family]").forEach(r => {
    r.onclick = () => { ctx.setClient(r.dataset.family); ctx.go("#/rm/khach-hang/tac-dong"); };
  });
}
