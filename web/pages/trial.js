/* CIO · Mô hình · Thử nghiệm agent tin tức (BUSINESS_FEEDBACK_1021_PLAN B1, src/trial): the news agents run on their
   own each morning, nothing approved; how much news came in, how much of the important news, how fast the agents
   were, and how often their shadow forecasts were right — overall, per segment, per factor, the buy/sell readings
   and the scenarios. GET /api/trial (written every 15 minutes to out/trial/<day>.json as well). */
import {esc, get, pct} from "../core/core.js";

const H = [["3d", "3 ngày"], ["1w", "1 tuần"], ["3m", "3 tháng"]];
const HL = Object.fromEntries(H);
const STATUS = {PENDING_APPROVAL: "chờ CIO", AGENT_ERROR: "agent lỗi", APPROVED: "đã duyệt", REJECTED: "bị từ chối"};
let horizon = "1w";

const day = (s) => (s ? s.split("-").reverse().join("/") : "—");
const share = (x, n) => (x == null || !n ? "—" : `${pct(x, false, 0)} <span class="muted small">(${n})</span>`);
const secs = (s) => (s == null ? "—" : s >= 90 ? `${(s / 60).toFixed(1).replace(".", ",")} phút` : `${Math.round(s)} giây`);
const num = (x) => (x == null ? "—" : x.toLocaleString("vi-VN"));

function kpi(label, value, sub) {
  return `<div class="kpi"><div class="k">${label}</div><div class="v">${value}</div><div class="s">${sub}</div></div>`;
}

export async function render(box) {
  const d = await get("/api/trial");
  const draw = () => {
    paint(box, d);
    for (const b of box.querySelectorAll("[data-h]")) b.onclick = () => { horizon = b.dataset.h; draw(); };
  };
  draw();
}

function accRow(label, a) {
  return `<tr><td>${label}</td><td class="num">${a.kept}</td><td class="num">${a.n}</td>
    <td class="num">${share(a.direction_hit, a.direction_n)}</td><td class="num">${share(a.coverage, a.n)}</td></tr>`;
}

function accTable(rows) {
  return `<div class="scrollx"><table class="table"><thead><tr><th></th><th class="num">Dự báo</th><th class="num">Đã chấm</th>
    <th class="num">Đúng hướng</th><th class="num">Trong dải P10–P90</th></tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
}

// B1.5: July 2026's news played back morning by morning, each draft's forecasts scored against what happened by now
function replay(r, d) {
  if (!r) return "";
  const a = r.accuracy[horizon], sc = (r.scenarios || {})[horizon], calls = r.calls[horizon] || [];
  const vn = a.by_factor.find(f => f.id === "VNINDEX");
  return `<section class="panel mt"><h3>Chạy lại tháng 7/2026 <span class="hint">${HL[horizon]} · ${r.runs.drafts} bản nháp từ ${r.days.length} buổi sáng ${day(r.replay.first)} – ${day(r.replay.last)}</span></h3>
    <p class="small">Tin tháng 7 của bốn báo (VnEconomy, VnExpress, CafeF, Vietstock) được chạy lại từng buổi sáng qua đúng các bước của thử nghiệm, rồi chấm với diễn biến thị trường đến nay — câu trả lời nhanh cho kỳ 3 tháng.
      Hai mô hình chỉ biết đến khoảng tháng 6/2026 và không biết kết quả tháng 7–9; agent chỉ đọc tin và danh mục yếu tố, không có số liệu thị trường.
      Một lần đọc đầu, chưa phải bằng chứng: ${r.runs.drafts} sự kiện trong ba tuần của một mùa hè.</p>
    ${accTable([accRow("<b>Tất cả</b>", a),
      ...Object.entries(d.segments).map(([k, l]) => accRow(esc(l), a.by_segment[k])),
      ...(vn ? [accRow("<b>VN-Index</b>", vn)] : [])])}
    <p class="small mt-xs">Mua · bán · giữ: ${calls.map(x => `${esc(x.label)} ${share(x.share, x.n)}`).join(" · ")}.
      Kịch bản: ${sc && sc.judged ? `thị trường đi theo kịch bản agent cho là khả năng cao nhất ${sc.main_taken}/${sc.judged} lần (${pct(sc.share, false, 0)})` : "chưa đủ yếu tố đã chấm"}.</p>
  </section>`;
}

function paint(box, d) {
  const c = d.collection, r = d.recall, runs = d.runs, a = d.accuracy[horizon];
  const perDay = Object.values(c.per_day || {});
  const avg = perDay.length ? Math.round(c.items / perDay.length) : null;
  const seg = `<div class="seg" role="group" aria-label="Kỳ hạn">${H.map(([k, l]) => `<button type="button" data-h="${k}" aria-pressed="${horizon === k}">${l}</button>`).join("")}</div>`;
  const calls = (d.calls[horizon] || []);
  const sc = (d.scenarios || {})[horizon];
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO · Mô hình</div><h1 class="h1">Thử nghiệm agent tin tức</h1>
      <p class="lede">Mỗi sáng 08:30 agent tự gom tin thành sự kiện, Agent CIO và Agent Phản biện chạy trên từng sự kiện; không ai duyệt.
        Dự báo của từng bản nháp được giữ làm <b>dự báo bóng</b> và chấm khi đến hạn. ${d.days.length ? `${d.days.length} buổi sáng: ${day(d.days[0])} – ${day(d.days[d.days.length - 1])}.` : "Chưa có buổi sáng nào."}</p></div>
      <div>${seg}</div></div>

    <div class="kpis">
      ${kpi("Tin thu thập", num(c.items), avg != null ? `~${num(avg)} tin/ngày · ${pct(c.items ? c.typed / c.items : 0, false, 0)} có loại sự kiện` : "chưa có tin")}
      ${kpi("Tin quan trọng thu được", r.share != null ? pct(r.share, false, 0) : "—", `${r.collected}/${r.important} tin của nguồn đối chiếu · mục tiêu ${pct(r.target, false, 0)} (KPI-02)`)}
      ${kpi("Sự kiện · bản nháp", `${runs.events} · ${runs.drafts}`, runs.errors.length ? `<span class="bad-text">${runs.errors.length} lần lỗi</span>` : "không lần nào lỗi")}
      ${kpi("Agent mỗi sự kiện", secs(runs.agent_s_p50), `trung vị · lâu nhất ${secs(runs.agent_s_max)} · tin vào hộp sau ${c.ingest_lag_min_p50 == null ? "—" : `${Math.round(c.ingest_lag_min_p50)} phút`}`)}
    </div>

    ${replay(d.replay, d)}

    <section class="panel mt"><h3>Dự báo bóng đúng bao nhiêu <span class="hint">${HL[horizon]}${a.next_due ? ` · hạn chấm gần nhất ${day(a.next_due)}` : ""}</span></h3>
      ${a.uncalibrated ? `<p class="small warn-text">Kỳ 3 ngày không phải kỳ hạn của mô hình: dùng tỷ lệ thể hiện của kỳ 1 tuần, chưa hiệu chỉnh. Ở kỳ ngắn, biến động thị trường phần lớn là nhiễu.</p>` : ""}
      ${accTable([accRow("<b>Tất cả</b>", a),
        ...Object.entries(d.segments).map(([k, l]) => accRow(esc(l), a.by_segment[k])),
        ...Object.entries(d.regions).map(([k, l]) => accRow(`<span class="muted">${esc(l)}</span>`, a.by_region[k]))])}
      <p class="footnote">Mỗi số đi kèm số lần đã chấm. Một tuần buổi sáng là mẫu nhỏ: tỷ lệ chỉ để xem xu hướng, chưa đủ để kết luận (cần ≥ 24 lần).
        Gốc tính là giá đóng cửa trước khi agent chạy. Ý kiến của công ty chứng khoán sẽ là phân khúc thứ tư khi có nguồn.</p>
    </section>

    <section class="panel mt"><h3>Mua · bán · giữ <span class="hint">cách đọc dự báo, không phải khuyến nghị · ${HL[horizon]}</span></h3>
      <p class="small">“Mua” khi mức biến động kỳ vọng lớn hơn một phần tư biến động thông thường của kỳ, “bán” khi nhỏ hơn âm mức đó, còn lại “giữ”; đúng khi thị trường đi theo (giữ: đi không quá mức đó).</p>
      <div class="scrollx"><table class="table"><thead><tr><th>Tài sản</th><th class="num">Mua</th><th class="num">Bán</th><th class="num">Giữ</th><th class="num">Đã chấm</th><th class="num">Đúng</th></tr></thead><tbody>
        ${calls.map(x => `<tr><td>${esc(x.label)}</td><td class="num">${x.calls["mua"] || 0}</td><td class="num">${x.calls["bán"] || 0}</td><td class="num">${x.calls["giữ"] || 0}</td>
          <td class="num">${x.n}</td><td class="num">${share(x.share, x.n)}</td></tr>`).join("")}
      </tbody></table></div>
    </section>

    <section class="panel mt"><h3>Kịch bản <span class="hint">${HL[horizon]}</span></h3>
      <p class="small">${sc && sc.judged ? `Trong ${sc.judged} bản nháp đã chấm đủ, thị trường đi theo kịch bản agent cho là khả năng cao nhất <b>${sc.main_taken} lần</b> (${pct(sc.share, false, 0)})${sc.tied ? `; ${sc.tied} lần hai kịch bản ngang nhau` : ""}.`
        : "Chưa bản nháp nào có đủ yếu tố đã chấm (cần ít nhất 3 yếu tố có hướng)."}
        Kịch bản thị trường đi theo là kịch bản có hướng trùng với nhiều yếu tố đã chấm nhất.</p>
    </section>

    <section class="panel mt"><h3>Theo yếu tố <span class="hint">${HL[horizon]}</span></h3>
      ${a.by_factor.length ? accTable(a.by_factor.map(f => accRow(`<b>${esc(f.name)}</b>`, f))) : `<p class="muted">Chưa có dự báo bóng.</p>`}
    </section>

    <section class="panel mt"><h3>Tin thu thập <span class="hint">theo phân khúc, vùng và nguồn</span></h3>
      <p class="small">${Object.entries(d.segments).map(([k, l]) => `${esc(l)} <b>${num(c.by_segment[k] || 0)}</b>`).join(" · ")} · chưa xếp được <b>${num(c.by_segment.none || 0)}</b>
        — ${Object.entries(d.regions).map(([k, l]) => `${esc(l)} <b>${num(c.by_region[k] || 0)}</b>`).join(" · ")}</p>
      <p class="small muted">${Object.entries(c.by_source).map(([s, n]) => `${esc(s)} ${num(n)}`).join(" · ")}</p>
    </section>

    <section class="panel mt"><h3>Các sự kiện <span class="hint">${d.events.length}</span></h3>
      ${d.events.length ? `<div class="scrollx"><table class="table"><thead><tr><th>Ngày</th><th>Sự kiện</th><th>Phân khúc</th><th>Bản nháp</th><th class="num">Agent</th></tr></thead><tbody>
        ${d.events.slice().reverse().map(e => `<tr><td>${day(e.day)}</td><td>${esc(e.title)}<div class="small muted mono">${esc(e.event_id)}</div></td>
          <td>${esc(d.segments[e.segment] || "—")}</td>
          <td>${e.view_id ? `<a href="#/cio/nhan-dinh/${esc(e.view_id)}">${esc(e.view_id)}</a> <span class="small muted">${esc(STATUS[e.status] || e.status || "")}</span>` : `<span class="bad-text">${esc(e.error || "không ra bản nháp")}</span>`}</td>
          <td class="num">${secs(e.agent_s)}</td></tr>`).join("")}
      </tbody></table></div>` : `<p class="muted">Buổi sáng đầu tiên chạy lúc 08:30.</p>`}
    </section>`;
}
