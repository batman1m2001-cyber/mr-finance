/* CIO · Mô hình · Độ chính xác (FEAT-18; BR-15, KPI-03/04, MEAS-01/02): how often the realised move fell inside
   the forecast P10–P90 band, and how often the direction was right — the model walked forward over the stored
   history, and every approved view's own forecasts as their horizons pass (scored by the 18:30 job).
   GET /api/accuracy. */
import {esc, get, n as how, pct} from "../core/core.js";

const H = [["1w", "1 tuần"], ["3m", "3 tháng"], ["12m", "12 tháng"]];
const HL = Object.fromEntries(H);
const TONE = {"đạt": "good", "dải hẹp": "warn", "dải rộng": "warn"};
let horizon = "3m";

const day = (s) => s ? s.split("-").reverse().join("/") : "—";
const cov = (x) => (x == null ? "—" : how(pct(x, false, 0), "accuracy.coverage", {horizon: HL[horizon]}));
const hit = (x) => (x == null ? "—" : how(pct(x, false, 0), "accuracy.direction", {horizon: HL[horizon]}));

function covBar(share, accept) {
  if (share == null) return "";
  const left = accept[0] * 100, width = (accept[1] - accept[0]) * 100;
  return `<span class="cov" role="img" aria-label="${pct(share, false, 0)} trong dải; chấp nhận ${pct(accept[0], false, 0)}–${pct(accept[1], false, 0)}">
    <i class="zone" style="left:${left}%;width:${width}%"></i><i class="dot" style="left:${(share * 100).toFixed(1)}%"></i></span>`;
}

function verdictPill(v) {
  return `<span class="pill ${TONE[v] || ""}">${esc(v)}</span>`;
}

function kpi(label, value, sub) {
  return `<div class="kpi"><div class="k">${label}</div><div class="v">${value}</div><div class="s">${sub}</div></div>`;
}

function hitText(x, n, min, target) {
  if (x == null) return "—";
  const tone = n < min ? "" : x >= target ? "good-text" : "bad-text";
  return `<span class="${tone}">${how(pct(x, false, 0), "accuracy.direction", {horizon: HL[horizon]})}</span>`;
}

export async function render(box) {
  const d = await get("/api/accuracy");
  const draw = () => {
    paint(box, d);
    for (const b of box.querySelectorAll("[data-h]")) b.onclick = () => { horizon = b.dataset.h; draw(); };
  };
  draw();
}

function paint(box, d) {
  const hist = d.history, views = d.views, accept = d.accept, min = d.min_obs, target = d.direction_target;
  const hh = (hist.horizons || {})[horizon];
  const vh = (views.horizons || {})[horizon];
  const k3 = (hist.kpi03 || {})[horizon];
  const vk = (views.kpi03 || {})[horizon];
  const seg = `<div class="seg" role="group" aria-label="Kỳ hạn">${H.map(([k, l]) => `<button type="button" data-h="${k}" aria-pressed="${horizon === k}">${l}</button>`).join("")}</div>`;
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO · Mô hình</div><h1 class="h1">Độ chính xác theo thời gian</h1>
      <p class="lede">Biến động thực tế có nằm trong dải P10–P90 đã dự báo không, và hướng có đúng không — theo từng yếu tố và kỳ hạn.
        Chấp nhận ${how(`${pct(accept[0], false, 0)}–${pct(accept[1], false, 0)}`, "accuracy.threshold")} số lần nằm trong dải; cần ít nhất ${min} quan sát mới kết luận.</p></div>
      <div>${seg}</div></div>

    <div class="kpis">
      ${kpi(`Trong dải · lịch sử · ${HL[horizon]}`, hh ? how(pct(hh.pooled_coverage, false, 0), "accuracy.coverage", {horizon: HL[horizon]}) : "—", hh ? `${verdictPill(hh.pooled_verdict)} gộp các yếu tố` : "chưa có dữ liệu")}
      ${kpi(`Đúng hướng VN-Index · lịch sử`, k3 ? hitText(k3.hit, k3.n, min, target) : "—", k3 ? `${k3.n} lần · mục tiêu ≥ ${how(pct(target, false, 0), "accuracy.threshold")} (KPI-03)` : "chưa có dữ liệu")}
      ${kpi(`Nhận định đã duyệt`, String(views.views || 0), vh && vh.next_due ? `hạn chấm gần nhất ${day(vh.next_due)}` : "chưa có dự báo chờ chấm")}
      ${kpi(`Đúng hướng VN-Index · nhận định`, vk && vk.hit != null ? hitText(vk.hit, vk.n, min, target) : "—", vk ? `${vk.n} lần đã chấm${vk.n < min ? ` · cần ${min}` : ""}` : "chưa có lần nào đến hạn")}
    </div>

    <section class="panel mt"><h3>Mô hình chạy lại trên lịch sử <span class="hint">${HL[horizon]} · từ ${day(hist.from)} đến ${day(hist.to)}</span></h3>
      <p class="small" data-explains>Tại mỗi thời điểm, mô hình được ước lượng chỉ từ các tháng đã qua (55 tháng, tối thiểu 24) rồi dự báo kỳ tiếp theo.
        Dải: không có kịch bản, tâm 0, độ lệch = biến động tháng × √số tháng × tỷ lệ thể hiện. Hướng (mục tiêu ≥ 70 % chỉ đặt cho VN-Index, KPI-03): suy ra yếu tố này từ biến động thực tế của các yếu tố còn lại (bước 2 của động cơ) — hướng của động cơ khi CIO đoán đúng cú sốc lõi.
        ${hh ? `Điểm gốc ${esc(hh.step)}${hh.overlapping ? "; các kỳ chồng lên nhau nên các quan sát không độc lập" : ""}.` : ""}</p>
      ${hh && hh.factors.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Yếu tố</th><th class="num">Quan sát</th><th>Trong dải P10–P90</th><th>Kết luận</th><th class="num">Đúng hướng</th></tr></thead><tbody>
        ${hh.factors.map(f => `<tr><td><b>${esc(f.name)}</b><div class="small muted mono">${esc(f.id)}</div></td><td class="num">${f.n}</td>
          <td><div class="covcell">${covBar(f.coverage, accept)}<b class="num">${cov(f.coverage)}</b></div></td>
          <td>${verdictPill(f.verdict)}</td><td class="num">${f.id === "VNINDEX" ? hitText(f.direction_hit, f.direction_n, min, target) : hit(f.direction_hit)}</td></tr>`).join("")}
      </tbody></table></div>` : `<p class="muted">Chưa đủ dữ liệu thị trường để chạy lại (nạp lịch sử trong Dữ liệu thị trường).</p>`}
      <p class="footnote">Yếu tố giả định (chênh lệch tín dụng bất động sản, tài chính; giá nhà) không có chuỗi công khai nên không chấm được.</p>
    </section>

    <section class="panel mt"><h3>Dự báo của các nhận định đã duyệt <span class="hint">${HL[horizon]} · chấm lúc 18:30 mỗi ngày</span></h3>
      ${viewsTable(vh, accept, min, target)}
      ${recorded(d.recorded)}
    </section>`;
}

function viewsTable(vh, accept, min, target) {
  if (!vh || !vh.factors.length) return `<p class="muted">Chưa có nhận định nào được duyệt.</p>`;
  const scored = vh.factors.filter(f => f.n);
  if (!scored.length) {
    return `<p class="small">${vh.views} nhận định đã ghi dự báo; chưa đến hạn chấm kỳ ${HL[horizon]}${vh.next_due ? ` (hạn gần nhất ${day(vh.next_due)})` : ""}.</p>`;
  }
  return `<div class="scrollx"><table class="table"><thead><tr><th>Yếu tố</th><th class="num">Đã chấm</th><th class="num">Chờ</th><th>Trong dải</th><th>Kết luận</th><th class="num">Đúng hướng</th></tr></thead><tbody>
    ${scored.map(f => `<tr><td><b>${esc(f.name)}</b></td><td class="num">${f.n}</td><td class="num">${f.pending}</td>
      <td><div class="covcell">${covBar(f.coverage, accept)}<b class="num">${cov(f.coverage)}</b></div></td><td>${verdictPill(f.verdict)}</td>
      <td class="num">${f.id === "VNINDEX" ? hitText(f.direction_hit, f.direction_n, min, target) : hit(f.direction_hit)}</td></tr>`).join("")}
  </tbody></table></div>`;
}

function recorded(list) {
  if (!list || !list.length) return "";
  const fmt = (x) => x == null ? "—" : (x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(x).toLocaleString("vi-VN", {maximumFractionDigits: 1});
  return `<h3 class="mt">VN-Index trong từng nhận định <span class="hint">dự báo và kết quả, % · ${HL[horizon]}</span></h3>
    <div class="scrollx"><table class="table"><thead><tr><th>Nhận định</th><th>Ngày duyệt</th><th>Hạn</th><th class="num">Kỳ vọng</th><th class="num">P10 … P90</th><th class="num">Thực tế</th><th>Kết quả</th></tr></thead><tbody>
    ${list.map(v => {
      const f = v.forecasts.find(x => x.factor === "VNINDEX" && x.horizon === horizon);
      const fc = (text) => (text === "—" ? text : how(text, "accuracy.forecast", {view: v.view_id}));
      if (!f) return "";
      const res = f.result === "scored" ? `<span class="pill ${f.inside ? "good" : "warn"}">${f.inside ? "trong dải" : "ngoài dải"}</span>${f.direction_hit == null ? "" : f.direction_hit ? " đúng hướng" : " sai hướng"}`
        : f.result === "no_data" ? `<span class="muted">không có dữ liệu</span>` : `<span class="muted">chờ đến hạn</span>`;
      return `<tr><td><a href="#/cio/nhan-dinh/${esc(v.view_id)}">${esc(v.view_id)}</a>${v.late ? `<div class="small muted">ghi lại sau khi duyệt</div>` : ""}</td>
        <td>${day(v.origin)}</td><td>${day(f.due)}</td><td class="num">${fc(fmt(f.expected))}</td><td class="num">${fc(fmt(f.p10))} … ${fc(fmt(f.p90))}</td>
        <td class="num">${fc(fmt(f.realised))}</td><td>${res}</td></tr>`;
    }).join("")}
    </tbody></table></div>`;
}
