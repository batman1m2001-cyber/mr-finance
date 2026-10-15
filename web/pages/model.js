/* CIO · Mô hình · Tham số: the 15 factors the engine runs on. Sizes and realisation are the BRD's; each volatility
   says whether it is estimated from market history (F2) or assumed. Below: what estimating now would give, the
   out-of-sample check (MEAS-08), and — for a CIO — proposing it as the next version, which a second CIO approves. */
import {esc, get, pct, post, toast} from "../core/core.js";

const UNIT = {pct: "%", bp: "điểm cơ bản", pp: "điểm %", sd: "độ lệch chuẩn"};
const n2 = (x) => x == null ? "—" : Number(x).toLocaleString("vi-VN", {maximumFractionDigits: 2});

function badge(f) {
  return f.assumed ? `<span class="badge assumed">giả định</span>`
    : `<span class="pill good" title="${esc(`${f.estimated.months} tháng ${f.estimated.from} → ${f.estimated.to}; ${f.estimated.source}`)}">ước lượng</span>`;
}

export async function render(box, ctx) {
  const [m, e] = await Promise.all([get("/api/model"), get("/api/model/estimate").catch(() => null)]);
  const est = m.factors.filter(f => !f.assumed).length;
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO · Mô hình yếu tố</div><div class="h1">${esc(m.version)}
      ${est ? `<span class="pill good">${est}/15 ước lượng</span>` : `<span class="badge assumed">tham số giả định</span>`}</div>
      <div class="lede small">${esc(m.note)}</div></div></div>
    <div class="cols">
      <div class="panel c4"><div class="eyebrow">Cách tính</div>
        <div class="small" style="margin-top:8px">Cú sốc lõi × mức đã vào giá (chưa ×${m.priced_in.none}, một phần ×${m.priced_in.partial}, hết ×${m.priced_in.full}). Các yếu tố khác suy ra bằng kỳ vọng có điều kiện. Dải gồm biến động còn lại × độ dài kỳ hạn, bất định cỡ cú sốc (${pct(m.core_uncertainty, false, 0)} cỡ), rủi ro riêng từng mã.</div>
        <div class="footnote">Chế độ căng thẳng: tương quan ×1,4, cắt ±0,85, ghi đè bốn cặp, nắn về xác định dương. Lần nắn này đổi tương quan nhiều nhất ${m.stressed_repair.max_change.toFixed(3)} (trị riêng nhỏ nhất trước khi nắn ${m.stressed_repair.min_eigenvalue_before.toFixed(3)}).</div>
        <div class="small muted" style="margin-top:8px">${esc(m.engine_version)} · ${esc(m.hash.slice(0, 16))}</div></div>
      <div class="panel c8"><h3>15 yếu tố <span class="hint">cỡ S/M/L và tỷ lệ thể hiện theo BRD</span></h3>
        <div class="scrollx"><table class="table"><thead><tr><th>Yếu tố</th><th>Đơn vị</th><th class="r">S / M / L</th><th class="r">1 tuần / 3 tháng / 12 tháng</th><th class="r">Biến động tháng</th></tr></thead><tbody>
        ${m.factors.map(f => `<tr><td>${esc(f.name)}<div class="small muted">${f.group === "intl" ? "Quốc tế" : "Trong nước"} · BRD: ${esc(f.brd_parameter)}</div></td><td class="small">${UNIT[f.unit]}</td>
          <td class="r num">${f.sizes.S} / ${f.sizes.M} / ${f.sizes.L}</td><td class="r num">${["1w", "3m", "12m"].map(h => pct(f.realisation[h], false, 0)).join(" / ")}</td>
          <td class="r num">${n2(f.vol_month)}<span class="small muted"> · căng ${n2(f.vol_month_stressed)}</span> ${badge(f)}</td></tr>`).join("")}
        </tbody></table></div></div>
    </div>
    ${e ? estimatePanel(e, ctx) : ""}`;
  const btn = box.querySelector("#est-propose");
  if (btn) btn.onclick = async () => {
    btn.disabled = true;
    try {
      const r = await post("/api/model/estimate", {by: ctx.user});
      toast(`Đã đề xuất phiên bản ${r.version.id} — chờ CIO thứ hai duyệt trong Cấu hình`);
      location.hash = "#/cio/cau-hinh";
    } catch (x) { toast("Không đề xuất được: " + x.message); btn.disabled = false; }
  };
}

function estimatePanel(e, ctx) {
  const r = e.report, v = e.validation;
  const ok = v.pooled_coverage_1m != null;
  return `<section class="panel mt"><h3>Ước lượng từ dữ liệu thị trường <span class="hint">${r.window} tháng đến ${esc(r.end)} · co tương quan ${Math.round(r.shrinkage * 100)} % · tối thiểu 24 tháng</span></h3>
    <p class="small">${r.estimated}/15 yếu tố đủ dữ liệu; ${r.correlation_pairs} cặp tương quan ước lượng${r.repair.max_change > 0.0005 ? `; nắn về xác định dương đổi tối đa ${r.repair.max_change.toFixed(3)}` : ""}.
      Kiểm tra ngoài mẫu (ước lượng đến ${esc(v.split)}, chấm ${esc(v.split)} → ${esc(v.test_to)}):
      ${ok ? `<b>${pct(v.pooled_coverage_1m, false, 0)}</b> số tháng nằm trong dải P10–P90 (kỳ vọng 80 %, chấp nhận 70–90 %) —
      <span class="pill ${v.pass ? "good" : "warn"}">${v.pass ? "đạt" : "chưa đạt"}</span>; tương quan lệch trung bình ${n2(v.correlation_drift)}.` : "chưa đủ dữ liệu."}</p>
    <div class="scrollx"><table class="table"><thead><tr><th>Yếu tố</th><th class="r">Số tháng</th><th class="r">Giả định</th><th class="r">Ước lượng</th><th class="r">Trong dải 1 tháng</th><th class="r">3 tháng</th><th>Ngoài mẫu</th></tr></thead><tbody>
    ${r.factors.map(f => { const t = v.factors.find(x => x.id === f.id);
      return `<tr><td>${esc(f.name)}<div class="small muted">${esc(f.source || "không có dữ liệu")}</div></td><td class="r num">${f.months}</td>
        <td class="r num">${n2(f.assumed_vol)}</td><td class="r num">${f.estimated_vol != null ? `<b>${n2(f.estimated_vol)}</b>` : "—"}</td>
        <td class="r num">${t ? pct(t.coverage_1m, false, 0) : "—"}</td><td class="r num">${t && t.coverage_3m != null ? pct(t.coverage_3m, false, 0) : "—"}</td>
        <td>${t ? `<span class="pill ${t.verdict === "đạt" ? "good" : "warn"}">${esc(t.verdict)}</span>` : ""}</td></tr>`; }).join("")}
    </tbody></table></div>
    ${ctx.role === "cio" && r.estimated ? `<div class="row mt"><button class="btn primary" id="est-propose" type="button">Đề xuất làm phiên bản mới</button>
      <span class="small muted">Một CIO đề xuất, CIO thứ hai duyệt trong Cấu hình; mô hình đang dùng không đổi cho đến khi duyệt.</span></div>` : ""}
  </section>`;
}
