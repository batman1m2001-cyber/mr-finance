/* RM · Hôm nay: the families to look at first — flagged for pre-review by an effective run
   (3-month P10 at or below −5 % of net worth), worst first. */
import {empty, esc, get, pct, signClass, vnd} from "../core/core.js";

export async function render(box, ctx) {
  const d = await get("/api/rm/today");
  const cases = d.cases;
  const families = new Set(cases.map(c => c.family_id));
  box.innerHTML = `
    <div class="cols">
      <div class="panel hero-panel c4">
        <div class="eyebrow">Hôm nay · cần xem trước</div>
        <div class="hero" style="margin-top:10px">${families.size}</div>
        <div class="takeaway">gia đình có kịch bản xấu 3 tháng (P10) chạm ngưỡng ${pct(d.threshold_pct, true, 0)} tài sản ròng.</div>
        <div class="footnote">Chỉ tính các lần áp dụng đã qua hậu kiểm và đang hiệu lực. Liên hệ khách theo thứ tự dưới đây.</div>
      </div>
      <div class="panel c8">
        <h3>Danh sách <span class="hint">xấu nhất trước</span></h3>
        ${cases.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Gia đình</th><th>Sự kiện</th><th class="r">Kỳ vọng 3 tháng</th><th class="r">P10 3 tháng</th><th></th></tr></thead><tbody>
          ${cases.map(c => `<tr class="click" data-family="${esc(c.family_id)}">
            <td><b>${esc(c.name)}</b><div class="small muted">${vnd(c.net_worth)} tài sản ròng</div></td>
            <td>${esc(c.event.title)}</td>
            <td class="r ${signClass(c.expected_3m)}">${vnd(c.expected_3m, true)}<div class="small muted">${pct(c.expected_3m_pct, true, 2)}</div></td>
            <td class="r down"><b>${pct(c.p10_3m_pct, true, 1)}</b><div class="small muted">${vnd(c.p10_3m, true)}</div></td>
            <td><span class="btn sm">Mở</span></td></tr>`).join("")}
        </tbody></table></div>` : empty("Không có ca nào cần xem trước", "Khi một lần áp dụng có gia đình chạm ngưỡng −5%, ca đó hiện ở đây.")}
      </div>
    </div>`;
  box.querySelectorAll("[data-family]").forEach(r => {
    r.onclick = () => { ctx.setClient(r.dataset.family); ctx.go("#/rm/khach-hang/tac-dong"); };
  });
}
