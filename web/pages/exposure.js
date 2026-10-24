/* CIO · Tác động danh mục (BR-13, OWN-FB-14): for an effective run, said as a scenario (its news and its date),
   every family's expected 3-month change by factor (% of net worth), the total by factor, and the ranking. */
import {empty, esc, get, n as how, pct, signClass, vnd, words} from "../core/core.js";
import {diverging, heat} from "../charts/charts.js";

export async function render(box, ctx) {
  const [{runs}, model, {events}] = await Promise.all([get("/api/runs"), get("/api/model"), get("/api/events")]);
  const eff = runs.filter(r => r.status === "EFFECTIVE");
  if (!eff.length) {
    box.innerHTML = `<div class="panel">${empty("Chưa có lần áp dụng nào đang hiệu lực", "Duyệt một nhận định ở trang Sự kiện để máy tính cho mọi gia đình.")}</div>`;
    return;
  }
  const names = Object.fromEntries(model.factors.map(f => [f.id, f.name]));
  const title = Object.fromEntries(events.map(e => [e.id, e.title]));
  const scenario = (r) => `${title[r.event_id] || r.event_id} · ${r.price_date}`;  // never the run's id (OWN-FB-14)
  const pick = eff.find(r => r.id === ctx.param) || eff[0];
  const ex = pick.exposure;
  const used = ex.factors.filter(f => ex.rows.some(r => r.vnd[f]));
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO · Tác động danh mục</div>
      <div class="h1 long">Nếu kịch bản “${esc(title[pick.event_id] || pick.event_id)}” xảy ra</div>
      <div class="lede small">${pick.families} gia đình dự kiến <b class="${signClass(pick.totals.expected_3m)}">${how(vnd(pick.totals.expected_3m, true), "run.expected_3m", {families: String(pick.families)})}</b> trong 3 tháng; ${pick.totals.pre_review} gia đình cần RM xem trước. Giá ngày ${esc(pick.price_date)}.</div></div>
      ${eff.length > 1 ? `<label class="small muted pick">Kịch bản <select id="pick">${eff.map(r => `<option value="${esc(r.id)}" ${r.id === pick.id ? "selected" : ""}>${esc(scenario(r))}</option>`).join("")}</select></label>` : ""}</div>
    <div class="cols">
      <div class="panel c5"><h3>Theo yếu tố <span class="hint">tổng mọi gia đình</span></h3><div id="total"></div></div>
      <div class="panel c7"><h3>Xếp hạng gia đình <span class="hint">tác động kỳ vọng 3 tháng, xấu nhất trước</span></h3>
        <div class="scrollx"><table class="table"><thead><tr><th>Gia đình</th><th class="r">Kỳ vọng</th><th class="r">% tài sản ròng</th><th class="r">P10 ${how("?", "impact.p10_3m")}</th></tr></thead><tbody>
        ${pick.ranking.map(r => `<tr><td>${esc(r.name)} ${r.pre_review ? '<span class="badge bad">RM xem trước</span>' : ""}</td><td class="r ${signClass(r.expected_3m)}">${how(vnd(r.expected_3m, true), "impact.expected_3m", {event: pick.view_id})}</td><td class="r">${how(pct(r.expected_3m_pct, true, 2), "impact.expected_3m", {event: pick.view_id})}</td><td class="r down">${how(pct(r.p10_3m_pct, true, 1), "impact.p10_3m", {event: pick.view_id})}</td></tr>`).join("")}
        </tbody></table></div>
        <p class="small muted">P10: 1 trong 10 khả năng kết quả 3 tháng xấu hơn mức này.</p></div>
      <div class="panel c12"><h3>Bản đồ nhiệt <span class="hint">% tài sản ròng mỗi gia đình theo yếu tố; đậm = lớn</span></h3><div id="heat"></div></div>
    </div>`;
  diverging(box.querySelector("#total"), used.map(f => ({label: names[f] || f, value: ex.total[f]})), {label: "Tổng theo yếu tố", metric: "impact.by_factor"});
  heat(box.querySelector("#heat"), used, ex.rows.map(r => ({label: r.name, values: r.pct})),
    {corner: "Gia đình", metric: "impact.by_factor", inputs: (r, f) => ({part: names[f] || f, family: r.label, exact: pct(r.values[f], true, 3)}), colLabel: (f) => words((names[f] || f).replace(/^(Chênh lệch|Lợi suất|Lãi suất|Giá) /, "").replace(/^./, (c) => c.toUpperCase()), 16), colTitle: (f) => names[f] || f});
  const sel = box.querySelector("#pick");
  if (sel) sel.onchange = () => ctx.go(ctx.href("phoi-nhiem", sel.value));
}
