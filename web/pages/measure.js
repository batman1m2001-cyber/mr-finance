/* CIO and Admin · Đo lường (F3): the monthly measurement reports, read from what the product records —
   misses with causes (MEAS-03), rubber-stamping (MEAS-05), news to RM (KPI-01, WF-09), inbox and agent timing
   (NFR-02), availability in business hours (NFR-03), recommendations reviewed and logged (KPI-05), RM contacts from a
   signal (KPI-06), high-level alerts the client opened (KPI-07), the business effect against a control group
   (MEAS-06). GET /api/measure. */
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
  const m = d.misses, r = d.rubber_stamp, s = d.speed, t = d.timing, a = d.availability, im = d.important, u = s.urgent;
  const rv = d.reviewed, ct = d.contacts, op = d.opens, ef = d.effect;
  const n2 = (x, d) => x == null ? "—" : Number(x).toLocaleString("vi-VN", {maximumFractionDigits: d});
  const EFFECT = [["contacts", "Liên hệ mỗi gia đình mỗi tháng", (x) => n2(x, 2)], ["goals", "Mục tiêu “Đạt”", (x) => x == null ? "—" : pct(x, false, 0)],
    ["actions", "Khuyến nghị hành động được duyệt mỗi gia đình", (x) => n2(x, 2)]];
  const cell = (x, f, q, group) => x == null ? "—" : how(f(x), "measure.control_effect", {quarter: q, group});
  const band = (r, f, q) => r.low == null ? `<span class="muted">chưa đủ gia đình</span>`
    : how(`${f(r.diff)} [${f(r.low)}; ${f(r.high)}]`, "measure.control_effect", {quarter: q, tool: r.n_tool, control: r.n_control});
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
      <p class="small">Từ lúc tin sớm nhất của sự kiện được đăng đến lúc lần áp dụng có hiệu lực cho RM. Tin khẩn (mục tiêu ≤ ${n1(u.target_minutes)} phút) là sự kiện CIO đánh dấu khẩn kèm lý do; hệ thống đề xuất khẩn khi NHNN quyết định lãi suất điều hành, biên độ tỷ giá, hoặc khi một yếu tố biến động quá 3 lần độ lệch chuẩn trong ngày — <span class="badge warn">Đề xuất</span> cách hiểu của chúng tôi cho tới khi ngân hàng định nghĩa. ${u.flagged} sự kiện đã đánh dấu khẩn, ${u.proposed} sự kiện được đề xuất.</p>
      ${s.by_month.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Tháng</th><th class="num">Lần áp dụng</th><th>Thời gian (trung vị)</th><th class="num">Đạt ≤ ${n1(s.target_hours)} giờ</th></tr></thead><tbody>
        ${s.by_month.map(x => `<tr><td>${esc(x.month)}</td><td class="num">${x.hours.n}</td><td>${stats(x.hours, "giờ")}</td><td class="num">${met(x.met_share, {month: x.month, step: "Tin → RM"})}</td></tr>`).join("")}
      </tbody></table></div>` : empty("Chưa có lần áp dụng nào có hiệu lực.")}
      ${u.by_month.length ? `<div class="scrollx" style="margin-top:12px"><table class="table"><thead><tr><th>Tháng</th><th class="num">Sự kiện khẩn</th><th>Thời gian (trung vị)</th><th class="num">Đạt ≤ ${n1(u.target_minutes)} phút</th></tr></thead><tbody>
        ${u.by_month.map(x => `<tr><td>${esc(x.month)}</td><td class="num">${x.minutes.n}</td><td>${stats(x.minutes, "phút")}</td><td class="num">${met(x.met_share, {month: x.month, step: "Tin khẩn → RM"})}</td></tr>`).join("")}
      </tbody></table></div>` : `<p class="small muted">Chưa có sự kiện khẩn nào đến RM.</p>`}
    </section>

    <section class="panel mt"><h3>Tin quan trọng được thu thập <span class="hint">BRD-KPI-02 · mục tiêu ≥ ${how(pct(im.target, false, 0), "news.important_share")}</span></h3>
      <p class="small">Tin quan trọng: câu chuyện về các yếu tố của mô hình mà nguồn đối chiếu độc lập (${esc(im.reference)}) đưa từ ít nhất hai báo. Đã thu thập: trong vòng một ngày, Hộp tin có tin cùng câu chuyện. <span class="badge warn">Đề xuất</span> cách hiểu của chúng tôi cho tới khi ngân hàng định nghĩa. Cột “Báo đang theo dõi” chỉ tính câu chuyện có ít nhất một báo thuộc danh sách trắng.</p>
      ${im.by_day.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Ngày</th><th class="num">Tin quan trọng</th><th class="num">Đã thu thập</th><th class="num">Tỷ lệ</th><th class="num">Báo đang theo dõi</th></tr></thead><tbody>
        ${im.by_day.map(x => `<tr><td>${esc(x.period)}</td><td class="num">${x.important}</td><td class="num">${x.collected}</td>
          <td class="num"><span class="${x.share >= im.target ? "good-text" : "bad-text"}">${how(pct(x.share, false, 0), "news.important_share", {period: x.period, important: x.important, collected: x.collected})}</span></td>
          <td class="num">${x.followed ? how(pct(x.followed_share, false, 0), "news.important_share", {period: x.period, followed: x.followed}) : "—"}</td></tr>`).join("")}
      </tbody></table></div>
      ${im.misses.length ? `<details style="margin-top:8px"><summary class="small">Tin quan trọng chưa thu thập (${im.misses.length})</summary>
        <ul class="small">${im.misses.map(x => `<li><span data-quote>${esc(x.title)}</span> — <span class="muted">${esc(x.outlets.slice(0, 4).join(", "))}${x.followed ? "" : " · không báo nào trong danh sách trắng"}</span></li>`).join("")}</ul></details>` : ""}`
      : empty("Chưa có câu chuyện nào được chấm: việc đối chiếu chạy mỗi 2 giờ, mỗi câu chuyện được chấm một ngày sau khi xuất hiện.")}
    </section>

    <section class="panel mt"><h3>Khuyến nghị có người duyệt và nhật ký <span class="hint">BRD-KPI-05 · mục tiêu ${how(pct(rv.target, false, 0), "measure.reviewed_share")}</span></h3>
      <p class="small">Khuyến nghị đã đưa ra: lần áp dụng đã hiệu lực (RM và khách đọc tác động), bản tin đã duyệt, đề xuất của khách RM đã duyệt. Mỗi khuyến nghị cần một người duyệt (nhân viên, không phải agent, khác người soạn) và các dòng duyệt trong chuỗi nhật ký. <span class="badge warn">Đề xuất</span> cách hiểu của chúng tôi. Đề xuất RM duyệt trước ngày 16/10/2026 không ghi người duyệt nên được tính là thiếu.</p>
      ${rv.by_month.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Tháng</th><th class="num">Áp dụng</th><th class="num">Bản tin</th><th class="num">Đề xuất RM</th><th class="num">Đủ duyệt và nhật ký</th></tr></thead><tbody>
        ${rv.by_month.map(x => `<tr><td>${esc(x.month)}</td><td class="num">${x.by_kind.run}</td><td class="num">${x.by_kind.newsletter}</td><td class="num">${x.by_kind.rm_item}</td>
          <td class="num"><span class="${x.share >= rv.target ? "good-text" : "bad-text"}">${how(pct(x.share, false, 0), "measure.reviewed_share", {month: x.month, recommendations: x.recommendations, ok: x.ok})}</span></td></tr>`).join("")}
      </tbody></table></div>
      ${rv.misses.length ? `<details style="margin-top:8px"><summary class="small">Khuyến nghị thiếu người duyệt hoặc nhật ký (${rv.misses.length})</summary>
        <ul class="small">${rv.misses.map(x => `<li>${esc(x.kind_label)} <span class="mono">${esc(x.id)}</span> — <span class="bad-text">${esc(x.missing.join(", "))}</span></li>`).join("")}</ul></details>` : ""}`
      : empty("Chưa có khuyến nghị nào được đưa ra.")}
    </section>

    <section class="panel mt"><h3>Liên hệ bắt đầu từ tín hiệu hệ thống <span class="hint">BRD-KPI-06 · mục tiêu ≥ ${how(pct(ct.target, false, 0), "measure.contact_signal_share")}</span></h3>
      <p class="small">RM ghi mỗi lần liên hệ khách ở Tổng quan (Ghi liên hệ), kèm tín hiệu khởi đầu (gia đình cần xem trước, việc theo mục tiêu) hoặc không. Tín hiệu được kiểm khi ghi. Hành vi thật của RM chỉ đo được khi thí điểm.</p>
      ${ct.by_month.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Tháng</th><th class="num">Liên hệ</th><th class="num">Từ tín hiệu</th><th class="num">Tỷ lệ</th></tr></thead><tbody>
        ${ct.by_month.map(x => `<tr><td>${esc(x.month)}</td><td class="num">${x.contacts}</td><td class="num">${x.from_signal}</td>
          <td class="num"><span class="${x.share >= ct.target ? "good-text" : "bad-text"}">${how(pct(x.share, false, 0), "measure.contact_signal_share", {month: x.month, contacts: x.contacts, from_signal: x.from_signal})}</span></td></tr>`).join("")}
      </tbody></table></div>
      ${ct.by_rm.length > 1 ? `<p class="small muted">Theo RM: ${ct.by_rm.map(x => `${esc(x.by)} ${x.from_signal}/${x.contacts}`).join(" · ")}</p>` : ""}`
      : empty("Chưa có liên hệ nào được ghi.")}
    </section>

    <section class="panel mt"><h3>Khách mở cảnh báo mức cao <span class="hint">BRD-KPI-07 · mục tiêu ≥ ${how(pct(op.target, false, 0), "measure.alert_open_share")}</span></h3>
      <p class="small">Không gửi gì ra ngoài: cảnh báo đến khách trong ứng dụng, là mục mức cao của “Điều đáng chú ý” (chuông, Toàn cảnh). Đến: lần đầu chính khách xem thấy. Mở: khách bấm vào mục. Tháng gần nhất còn đang tính. Hành vi thật của khách chỉ đo được khi thí điểm.</p>
      ${op.by_month.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Tháng</th><th class="num">Đã đến khách</th><th class="num">Khách đã mở</th><th class="num">Tỷ lệ</th><th>Thời gian tới khi mở</th></tr></thead><tbody>
        ${op.by_month.map(x => `<tr><td>${esc(x.month)}</td><td class="num">${x.delivered}</td><td class="num">${x.opened}</td>
          <td class="num"><span class="${x.share >= op.target ? "good-text" : "bad-text"}">${how(pct(x.share, false, 0), "measure.alert_open_share", {month: x.month, delivered: x.delivered, opened: x.opened})}</span></td>
          <td>${stats(x.hours, "giờ")}</td></tr>`).join("")}
      </tbody></table></div>`
      : empty("Chưa có cảnh báo mức cao nào đến khách.")}
    </section>

    <section class="panel mt"><h3>Hiệu quả kinh doanh: có và không có công cụ <span class="hint">BRD-RULE-MEAS-06 · theo quý</span></h3>
      <p class="small">Nhóm đối chứng: ${how(pct(ef.share, false, 0), "measure.control_effect")} số gia đình, rút trong từng tầng (${esc(ef.strata.join(" × "))}) theo seed “${esc(ef.seed)}” — ai có cấu hình cũng rút lại được. RM không nhận tín hiệu nào cho nhóm này; khách vẫn được phục vụ đủ. Chênh lệch = có công cụ − đối chứng, trong ngoặc là khoảng tin cậy ${how("90 %", "measure.control_effect")}. Hiện có <b>${ef.control.length}</b> trên ${ef.families} gia đình${ef.control.length ? `: ${esc(ef.control.join(", "))}` : ""}.${ef.families < 50 ? " Với số gia đình của bản demo, chênh lệch không nói lên hiệu quả: cần thí điểm." : ""}</p>
      ${ef.quarters.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Quý</th><th>Chỉ số</th><th class="num">Có công cụ</th><th class="num">Đối chứng</th><th class="num">Chênh lệch [khoảng]</th></tr></thead><tbody>
        ${ef.quarters.map(q => EFFECT.map(([k, label, f], i) => `<tr>${i === 0 ? `<td rowspan="3">${esc(q.quarter)}</td>` : ""}<td>${label}</td>
          <td class="num">${cell(q[k].tool, f, q.quarter, "tool")}<div class="small muted">${q[k].n_tool} gia đình</div></td><td class="num">${cell(q[k].control, f, q.quarter, "control")}<div class="small muted">${q[k].n_control} gia đình</div></td>
          <td class="num">${band(q[k], f, q.quarter)}</td></tr>`).join("")).join("")}
      </tbody></table></div>` : empty("Chưa có quý nào có số liệu.")}
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
