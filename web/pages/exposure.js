/* CIO · Phơi nhiễm toàn bộ khách (BR-13): for the latest effective run, every family's expected
   3-month change by factor (% of net worth), the total by factor, and the ranking. */
import {empty, esc, get, pct, signClass, vnd} from "../core/core.js";
import {diverging, heat} from "../charts/charts.js";

export async function render(box, ctx) {
  const [{runs}, model] = await Promise.all([get("/api/runs"), get("/api/model")]);
  const eff = runs.filter(r => r.status === "EFFECTIVE");
  if (!eff.length) {
    box.innerHTML = `<div class="panel">${empty("Chưa có lần áp dụng nào đang hiệu lực", "Duyệt một nhận định ở trang Sự kiện để máy tính cho mọi gia đình.")}</div>`;
    return;
  }
  const names = Object.fromEntries(model.factors.map(f => [f.id, f.name]));
  const pick = eff.find(r => r.id === ctx.param) || eff[0];
  const ex = pick.exposure;
  const used = ex.factors.filter(f => ex.rows.some(r => r.vnd[f]));
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO · Phơi nhiễm toàn bộ khách</div>
      <div class="h1"><span class="${signClass(pick.totals.expected_3m)}">${vnd(pick.totals.expected_3m, true)}</span> kỳ vọng 3 tháng trên ${pick.families} gia đình</div>
      <div class="lede small">${pick.totals.pre_review} gia đình chạm ngưỡng RM xem trước. Lần áp dụng ${esc(pick.id)} · giá ngày ${esc(pick.price_date)} · tham số mô hình giả định.</div></div>
      ${eff.length > 1 ? `<select id="pick" aria-label="Lần áp dụng">${eff.map(r => `<option value="${esc(r.id)}" ${r.id === pick.id ? "selected" : ""}>${esc(r.id)}</option>`).join("")}</select>` : ""}</div>
    <div class="cols">
      <div class="panel c5"><h3>Theo yếu tố <span class="hint">tổng mọi gia đình</span></h3><div id="total"></div></div>
      <div class="panel c7"><h3>Xếp hạng gia đình <span class="hint">tác động kỳ vọng 3 tháng, xấu nhất trước</span></h3>
        <div class="scrollx"><table class="table"><thead><tr><th>Gia đình</th><th class="r">Kỳ vọng</th><th class="r">% tài sản ròng</th><th class="r">P10</th></tr></thead><tbody>
        ${pick.ranking.map(r => `<tr><td>${esc(r.name)} ${r.pre_review ? '<span class="badge bad">xem trước</span>' : ""}</td><td class="r ${signClass(r.expected_3m)}">${vnd(r.expected_3m, true)}</td><td class="r">${pct(r.expected_3m_pct, true, 2)}</td><td class="r down">${pct(r.p10_3m_pct, true, 1)}</td></tr>`).join("")}
        </tbody></table></div></div>
      <div class="panel c12"><h3>Bản đồ nhiệt <span class="hint">% tài sản ròng mỗi gia đình theo yếu tố; đậm = lớn</span></h3><div id="heat"></div></div>
    </div>`;
  diverging(box.querySelector("#total"), used.map(f => ({label: names[f] || f, value: ex.total[f]})), {label: "Tổng theo yếu tố"});
  heat(box.querySelector("#heat"), used, ex.rows.map(r => ({label: r.name, values: r.pct})),
    {corner: "Gia đình", colLabel: (f) => (names[f] || f).replace(/^(Chênh lệch|Lợi suất|Lãi suất|Giá) /, "").slice(0, 14), colTitle: (f) => names[f] || f});
  const sel = box.querySelector("#pick");
  if (sel) sel.onchange = () => ctx.go(ctx.href("phoi-nhiem", sel.value));
}
