/* CIO and Tuân thủ · Đo lường (F3): the monthly measurement reports, read from what the product records —
   misses with causes (MEAS-03), rubber-stamping (MEAS-05), news to RM (KPI-01, WF-09), inbox and agent timing
   (NFR-02), availability in business hours (NFR-03). GET /api/measure. */
import {esc, get, n as how, num, pct} from "../core/core.js";

const n1 = (x) => x == null ? "—" : Number(x).toLocaleString("vi-VN", {maximumFractionDigits: 1});
const met = (share, inputs) => share == null ? "—" : `<span class="${share >= 1 ? "good-text" : share === 0 ? "bad-text" : ""}">${how(pct(share, false, 0), "measure.on_time", inputs)}</span>`;

const stamp = (t) => new Date(t * 1000).toLocaleString("vi-VN", {timeZone: "Asia/Ho_Chi_Minh", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit"});

function empty(text) { return `<p class="muted small">${text}</p>`; }

function stats(s, unit) {
  return s && s.n ? `${n1(s.median)} ${unit}<span class="small muted"> · P90 ${n1(s.p90)} · lâu nhất ${n1(s.max)}</span>` : "—";
}

export async function render(box) {
  const d = await get("/api/measure");
  const m = d.misses, r = d.rubber_stamp, s = d.speed, t = d.timing, a = d.availability;
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Đo lường</div><h1 class="h1">Báo cáo đo lường hằng tháng</h1>
      <p class="lede">Đọc từ những gì hệ thống ghi lại: tin và sự kiện bị bỏ sót, thời gian CIO xem trước khi duyệt, thời gian từ tin đến RM, tốc độ hộp tin và Agent, mức sẵn sàng trong giờ làm việc.</p></div></div>

    <section class="panel"><h3>Bỏ sót <span class="hint">BRD-RULE-MEAS-03 · theo tháng, kèm nguyên nhân</span></h3>
      <p class="small">Tin quan trọng (mức liên quan “cao” — cách hiểu của chúng tôi, Q-07) không thành sự kiện; sự kiện không đến được các gia đình.</p>
      ${m.by_month.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Tháng</th><th class="num">Tin</th><th class="num">Sự kiện</th><th>Nguyên nhân</th></tr></thead><tbody>
        ${m.by_month.map(x => `<tr><td>${esc(x.month)}</td><td class="num">${x.news}</td><td class="num">${x.events}</td>
          <td class="small">${Object.entries(x.causes).map(([k, v]) => `${esc(k)}: ${v}`).join(" · ")}</td></tr>`).join("")}
      </tbody></table></div>` : empty("Chưa có tin hay sự kiện nào bị bỏ sót (tin mới dưới 1 ngày chưa tính).")}
      ${m.events.length ? `<div class="scrollx mt"><table class="table"><thead><tr><th>Sự kiện</th><th>Nguyên nhân</th></tr></thead><tbody>
        ${m.events.map(e => `<tr><td><b data-quote>${esc(e.title || e.id)}</b><div class="small muted mono">${esc(e.id)}</div></td><td>${esc(e.cause)}</td></tr>`).join("")}
      </tbody></table></div>` : ""}
      ${m.news.length ? `<details class="mt"><summary class="small">${m.news.length} tin quan trọng bị bỏ sót</summary>
        <ul class="small">${m.news.slice(0, 50).map(n => `<li><span data-quote>${esc(n.title || n.id)}</span> — <span class="muted">${esc(n.cause)}</span></li>`).join("")}</ul></details>` : ""}
    </section>

    <section class="panel mt"><h3>Duyệt cho có <span class="hint">BRD-RULE-MEAS-05 · theo tháng</span></h3>
      <p class="small">Thời gian CIO xem từ lúc nhận định sẵn sàng đến lúc duyệt, và tỷ lệ duyệt không sửa gì. “Duyệt rất nhanh” là dưới ${n1(r.fast_minutes)} phút — ngưỡng của chúng tôi, không phải của BRD.</p>
      ${r.by_month.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Tháng</th><th class="num">Đã duyệt</th><th>Thời gian xem (trung vị)</th><th class="num">Duyệt rất nhanh</th><th class="num">Không sửa</th></tr></thead><tbody>
        ${r.by_month.map(x => `<tr><td>${esc(x.month)}</td><td class="num">${x.approved}</td><td>${stats(x.minutes, "phút")}</td>
          <td class="num">${x.fast}</td><td class="num">${how(pct(x.no_edit_share, false, 0), "measure.no_edit", {month: x.month})}</td></tr>`).join("")}
      </tbody></table></div>` : empty("Chưa có nhận định nào được duyệt.")}
    </section>

    <section class="panel mt"><h3>Từ tin đến RM <span class="hint">BRD-KPI-01 · BRD-RULE-WF-09 · mục tiêu ≤ ${n1(s.target_hours)} giờ</span></h3>
      <p class="small">Từ lúc tin sớm nhất của sự kiện được đăng đến lúc lần áp dụng có hiệu lực cho RM. “Tin khẩn ≤ 30 phút” chưa đo được: hệ thống chưa có định nghĩa tin khẩn.</p>
      ${s.by_month.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Tháng</th><th class="num">Lần áp dụng</th><th>Thời gian (trung vị)</th><th class="num">Đạt ≤ ${n1(s.target_hours)} giờ</th></tr></thead><tbody>
        ${s.by_month.map(x => `<tr><td>${esc(x.month)}</td><td class="num">${x.hours.n}</td><td>${stats(x.hours, "giờ")}</td><td class="num">${met(x.met_share, {month: x.month, step: "Tin → RM"})}</td></tr>`).join("")}
      </tbody></table></div>` : empty("Chưa có lần áp dụng nào có hiệu lực.")}
    </section>

    <section class="panel mt"><h3>Tốc độ hộp tin và Agent <span class="hint">BRD-NFR-02</span></h3>
      <p class="small">Tin đăng → vào hộp tin, mục tiêu ≤ ${n1(t.inbox.target_minutes)} phút (chỉ tính tin đăng sau khi việc lấy tin đã chạy). Agent CIO chạy xong, mục tiêu ≤ ${n1(t.agent.target_minutes)} phút.</p>
      <div class="scrollx"><table class="table"><thead><tr><th>Tháng</th><th>Đo</th><th class="num">Số lần</th><th>Trung vị</th><th class="num">Đạt mục tiêu</th></tr></thead><tbody>
        ${t.inbox.by_month.map(x => `<tr><td>${esc(x.month)}</td><td>Tin → hộp tin</td><td class="num">${x.minutes.n}</td><td>${stats(x.minutes, "phút")}</td><td class="num">${met(x.met_share, {month: x.month, step: "Tin → hộp tin"})}</td></tr>`).join("")}
        ${t.agent.by_month.map(x => `<tr><td>${esc(x.month)}</td><td>Agent CIO</td><td class="num">${x.minutes.n}</td><td>${stats(x.minutes, "phút")}</td><td class="num">${met(x.met_share, {month: x.month, step: "Agent CIO"})}</td></tr>`).join("")}
        ${!t.inbox.by_month.length && !t.agent.by_month.length ? `<tr><td colspan="5" class="muted">Chưa có số liệu.</td></tr>` : ""}
      </tbody></table></div>
    </section>

    <section class="panel mt"><h3>Sẵn sàng trong giờ làm việc <span class="hint">BRD-NFR-03 · mục tiêu ≥ ${how(pct(a.target, false, 1), "uptime.availability")}</span></h3>
      <p class="small">Số phút làm việc (thứ Hai–thứ Sáu, 08:00–17:30 giờ Việt Nam) máy chủ ghi được nhịp ÷ số phút làm việc, từ nhịp đầu tiên. Khởi động lại khi triển khai tính là không sẵn sàng.</p>
      ${a.months.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Tháng</th><th class="num">Phút làm việc</th><th class="num">Phút có nhịp</th><th class="num">Sẵn sàng</th><th>Gián đoạn</th></tr></thead><tbody>
        ${a.months.map(x => `<tr><td>${esc(x.month)}</td><td class="num">${num(x.business_minutes)}</td><td class="num">${num(x.up_minutes)}</td>
          <td class="num"><span class="${x.met ? "good-text" : "bad-text"}">${how(pct(x.availability, false, 2), "uptime.availability", {month: x.month, business_minutes: x.business_minutes, up_minutes: x.up_minutes})}</span></td>
          <td class="small">${x.outages.length ? x.outages.slice(-5).reverse().map(o => `${stamp(o.from)} · ${num(o.minutes)} phút`).join("<br>") + (x.outages.length > 5 ? `<div class="muted">và ${x.outages.length - 5} lần khác</div>` : "") : `<span class="muted">không có</span>`}</td></tr>`).join("")}
      </tbody></table></div>` : empty("Chưa có nhịp nào: việc nhịp tim chạy cùng máy chủ.")}
    </section>`;
}
