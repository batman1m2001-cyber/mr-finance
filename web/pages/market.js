/* CIO · Mô hình · Dữ liệu thị trường, and Quản trị (F1): every public source fetched on its own clock into the
   app's database — each job's cadence, last success and last error; where each factor of the model comes from;
   each series with its last value, source and the last 120 days. Read from SQLite only (GET /api/market). */
import {ago, esc, get, n as how, num} from "../core/core.js";

const SOURCE = {
  vndirect: "VNDirect", vietcap: "Vietcap", msn: "MSN Finance", binance: "Binance", vcb: "Vietcombank", pnj: "PNJ",
  hnx: "HNX", wgb: "worldgovernmentbonds", cafef: "cafef",
};
const UNIT = {pct: "%", bp: "điểm cơ bản", pp: "điểm %", sd: "độ lệch chuẩn"};

function cadence(j) { return j.at ? `hằng ngày ${j.at}` : `mỗi ${j.every.replace("h", " giờ").replace("m", " phút")}`; }

function spark(vals) {
  if (!vals || vals.length < 2) return `<span class="small muted">—</span>`;
  const w = 120, h = 28, lo = Math.min(...vals), hi = Math.max(...vals), span = hi - lo || 1;
  const pts = vals.map((v, i) => `${(i / (vals.length - 1) * (w - 4) + 2).toFixed(1)},${(h - 3 - (v - lo) / span * (h - 6)).toFixed(1)}`);
  const up = vals[vals.length - 1] >= vals[0];
  return `<svg class="mk-spark" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img"
    aria-label="120 ngày: từ ${num(vals[0], 2)} đến ${num(vals[vals.length - 1], 2)}">
    <polyline fill="none" stroke="var(${up ? "--good" : "--critical"})" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" points="${pts.join(" ")}"/></svg>`;
}

function value(s) {
  if (s.value == null) return "—";
  const big = s.unit === "VND" && Math.abs(s.value) >= 1e9, a = Math.abs(s.value);
  const d = big ? num(s.value / 1e9, 1) + " tỷ" : num(s.value, a < 10 ? 4 : a < 1000 ? 2 : 0);
  return `${how(d, "market.value", {date: s.last || "", source: s.source || (s.sources || [])[0] || ""})} <span class="small muted">${esc(big ? "VND" : s.unit)}</span>`;
}

export async function render(box) {
  const d = await get("/api/market");
  const late = d.jobs.filter(j => j.last_error_at && (!j.last_ok || j.last_error_at > j.last_ok));
  const fromData = d.factors.filter(f => f.series && f.months !== undefined && !f.provenance.startsWith("Giả định"));
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Mô hình · Dữ liệu thị trường</div>
      <h1 class="h1">Dữ liệu thị trường</h1>
      <p class="lede">Mỗi nguồn công khai được lấy theo lịch riêng vào cơ sở dữ liệu của ứng dụng; trang và mô hình chỉ đọc từ đó.
        ${fromData.length}/${d.factors.length} yếu tố có dữ liệu thật${late.length ? ` · <span class="bad-text">${late.length} nguồn đang lỗi</span>` : ""}.</p></div></div>

    <section class="panel"><div class="h3">Nguồn và lịch lấy</div>
      <div class="scrollx"><table class="table"><thead><tr><th>Việc</th><th>Lịch</th><th>Lần lấy được gần nhất</th><th>Lỗi gần nhất</th></tr></thead><tbody>
      ${d.jobs.map(j => `<tr><td><b>${esc(j.label)}</b><div class="small muted mono">${esc(j.id)}</div></td>
        <td>${esc(cadence(j))}<div class="small muted">${esc(j.why)}</div></td>
        <td>${j.last_ok ? esc(ago(j.last_ok)) : `<span class="muted">chưa chạy</span>`}</td>
        <td class="small">${j.last_error && (!j.last_ok || j.last_error_at > j.last_ok) ? `<span class="bad-text">${esc(j.last_error)}</span> <span class="muted">${esc(ago(j.last_error_at))}</span>`
          : j.last_error ? `<span class="muted">${esc(ago(j.last_error_at))}, đã ổn lại</span>` : `<span class="muted">—</span>`}</td></tr>`).join("")}
      </tbody></table></div></section>

    <section class="panel mt"><div class="h3">Yếu tố của mô hình lấy từ đâu</div>
      <div class="scrollx"><table class="table"><thead><tr><th>Yếu tố</th><th>Nguồn</th><th class="num">Số tháng</th><th>Tháng gần nhất</th></tr></thead><tbody>
      ${d.factors.map(f => `<tr><td><b>${esc(f.name)}</b><div class="small muted mono">${esc(f.id)} · ${esc(UNIT[f.unit] || f.unit)}</div></td>
        <td><span class="pill ${f.provenance.startsWith("Giả định") ? "warn" : "good"}">${esc(f.provenance)}</span>${f.note ? `<div class="small muted">${esc(f.note)}</div>` : ""}</td>
        <td class="num">${f.months || "—"}</td>
        <td class="num">${f.last_move ? `${esc(f.last_move.month)}: ${num(f.last_move.move, 2)}` : "—"}</td></tr>`).join("")}
      </tbody></table></div></section>

    <section class="panel mt"><div class="h3">Các chuỗi đang lưu</div>
      <div class="scrollx"><table class="table"><thead><tr><th>Chuỗi</th><th>Giá trị gần nhất</th><th>Nguồn (dự phòng)</th><th class="num">Số điểm</th><th>120 ngày</th></tr></thead><tbody>
      ${d.series.map(s => `<tr><td><b>${esc(s.name)}</b><div class="small muted mono">${esc(s.id)}</div></td>
        <td class="num">${value(s)}<div class="small muted">${esc(s.last || "chưa có")}</div></td>
        <td class="small">${s.sources.map((x, i) => i === 0 ? `<b>${esc(SOURCE[x] || x)}</b>` : esc(SOURCE[x] || x)).join(" → ")}
          ${s.source && s.source !== s.sources[0] ? `<div class="small" style="color:var(--warning)">đang dùng ${esc(SOURCE[s.source] || s.source)}</div>` : ""}</td>
        <td class="num">${s.n ? num(s.n) : "—"}<div class="small muted">${esc(s.first || "")}</div></td>
        <td>${spark(s.tail)}</td></tr>`).join("")}
      </tbody></table></div></section>
    <p class="small muted mt">Nguồn công khai, không cần tài khoản; không chính thức nên mỗi chuỗi có nguồn dự phòng.
      Danh sách nguồn là cấu hình “Nguồn dữ liệu thị trường” (Quản trị). Mỗi điểm lưu kèm nguồn, địa chỉ và lúc lấy.</p>`;
}
