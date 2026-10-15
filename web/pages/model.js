/* CIO · Mô hình: the 15 factors the engine runs on. Sizes and realisation are the BRD's; every
   volatility and correlation is an assumption until the model is estimated (blocker B1) — said here. */
import {esc, get, pct} from "../core/core.js";

const UNIT = {pct: "%", bp: "điểm cơ bản", pp: "điểm %", sd: "độ lệch chuẩn"};

export async function render(box) {
  const m = await get("/api/model");
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO · Mô hình yếu tố</div><div class="h1">${esc(m.version)} <span class="badge assumed">tham số giả định</span></div>
      <div class="lede small">${esc(m.note)}</div></div></div>
    <div class="cols">
      <div class="panel c4"><div class="eyebrow">Cách tính</div>
        <div class="small" style="margin-top:8px">Cú sốc lõi × mức đã vào giá (chưa ×${m.priced_in.none}, một phần ×${m.priced_in.partial}, hết ×${m.priced_in.full}). Các yếu tố khác suy ra bằng kỳ vọng có điều kiện. Dải gồm biến động còn lại × độ dài kỳ hạn, bất định cỡ cú sốc (${pct(m.core_uncertainty, false, 0)} cỡ), rủi ro riêng từng mã.</div>
        <div class="footnote">Chế độ căng thẳng: tương quan ×1,4, cắt ±0,85, ghi đè bốn cặp, nắn về xác định dương. Lần nắn này đổi tương quan nhiều nhất ${m.stressed_repair.max_change.toFixed(3)} (trị riêng nhỏ nhất trước khi nắn ${m.stressed_repair.min_eigenvalue_before.toFixed(3)}).</div>
        <div class="small muted" style="margin-top:8px">${esc(m.engine_version)} · ${esc(m.hash.slice(0, 16))}</div></div>
      <div class="panel c8"><h3>15 yếu tố <span class="hint">cỡ S/M/L và tỷ lệ thể hiện theo BRD; biến động là giả định</span></h3>
        <div class="scrollx"><table class="table"><thead><tr><th>Yếu tố</th><th>Đơn vị</th><th class="r">S / M / L</th><th class="r">1 tuần / 3 tháng / 12 tháng</th><th class="r">Biến động tháng</th></tr></thead><tbody>
        ${m.factors.map(f => `<tr><td>${esc(f.name)}<div class="small muted">${f.group === "intl" ? "Quốc tế" : "Trong nước"} · BRD: ${esc(f.brd_parameter)}</div></td><td class="small">${UNIT[f.unit]}</td>
          <td class="r num">${f.sizes.S} / ${f.sizes.M} / ${f.sizes.L}</td><td class="r num">${["1w", "3m", "12m"].map(h => pct(f.realisation[h], false, 0)).join(" / ")}</td>
          <td class="r num">${f.vol_month}<span class="small muted"> · căng ${f.vol_month_stressed}</span> <span class="badge assumed">giả định</span></td></tr>`).join("")}
        </tbody></table></div></div>
    </div>`;
}
