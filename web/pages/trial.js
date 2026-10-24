/* CIO · Mô hình · Thử nghiệm hằng ngày (BUSINESS_FEEDBACK_1021_PLAN B1, src/trial): the news agents run on their
   own each morning, nothing approved; how much news came in, how much of the important news, how fast the agents
   were, and how often their shadow forecasts were right — overall, per segment, per factor, the buy/sell readings
   and the scenarios. GET /api/trial (written every 15 minutes to out/trial/<day>.json as well).
   AGENT_EVALUATION_PLAN E5: two views. A · Thu thập tin: each ingest run's funnel and health by day (news/monitor.py).
   B · Hiệu quả agent: each move scored (trial/evaluate.py), its simulated VND (trial/finance.py), what the calls
   cost (trial/costs.py); a move opens from the news to the VND (GET /api/trial/move/<id>). Every rate shows k/n;
   what is unavailable says so, never 0. */
import {drawer, esc, get, n as how, pct, vnd, when} from "../core/core.js";

const H = [["3d", "3 ngày"], ["1w", "1 tuần"], ["3m", "3 tháng"]];
const HL = Object.fromEntries(H);
const STATUS = {PENDING_APPROVAL: "chờ CIO", AGENT_ERROR: "agent lỗi", APPROVED: "đã duyệt", REJECTED: "bị từ chối"};
let horizon = "1w";
let view = "a";

const day = (s) => (s ? s.split("-").reverse().join("/") : "—");
// a rate and how many it was counted over; it opens its “cách tính” (BRD-NFR-11)
const share = (x, n, m) => (x == null || !n ? "—" : `${how(pct(x, false, 0), m, {horizon: HL[horizon], n: String(n)})} <span class="muted small">(${n})</span>`);
const secs = (s) => (s == null ? "—" : s >= 90 ? `${(s / 60).toFixed(1).replace(".", ",")} phút` : `${Math.round(s)} giây`);
const num = (x) => (x == null ? "—" : x.toLocaleString("vi-VN"));
const hm = (t) => new Date(t * 1000).toLocaleTimeString("vi-VN", {hour: "2-digit", minute: "2-digit", timeZone: "Asia/Ho_Chi_Minh"});

function kpi(label, value, sub) {
  return `<div class="kpi"><div class="k">${label}</div><div class="v">${value}</div><div class="s">${sub}</div></div>`;
}

export async function render(box) {
  const d = await get("/api/trial");
  const draw = () => {
    paint(box, d);
    for (const b of box.querySelectorAll("[data-h]")) b.onclick = () => { horizon = b.dataset.h; draw(); };
    for (const b of box.querySelectorAll("[data-view]")) b.onclick = () => { view = b.dataset.view; draw(); };
    for (const b of box.querySelectorAll("[data-move]")) b.onclick = () => openMove(b.dataset.move);
  };
  draw();
}

// ── E5 · the two views ─────────────────────────────────────────────────────────────────────────────────
const VERDICT = {correct: ["good", "đúng"], incorrect: ["bad", "sai"], missed: ["warn", "bỏ lỡ"], quiet: ["", "lặng"],
  pending: ["", "chờ chấm"], excluded: ["", "loại ra"], failed: ["bad", "không chấm được"]};
const REASON = {not_due: "chưa đến hạn", waiting: "chờ số liệu thị trường", no_data: "không có số liệu thị trường",
  assumed: "yếu tố giả định, không có chuỗi giá", no_series: "không có chuỗi giá", leak: "bản nháp viết sau giá gốc",
  conflicting: "các bản nháp trái chiều", wrong_direction: "sai hướng", not_material: "thị trường không đi đủ mạnh",
  not_predicted: "agent không dự báo", no_run: "buổi sáng không chạy"};
const MORNING = {ran: ["good", "đã chạy"], no_drafts: ["warn", "không ra bản nháp"], failed: ["bad", "lỗi"],
  no_record: ["bad", "không có bản ghi"], not_live: ["warn", "agent không trực tuyến"], no_news: ["", "không có tin"]};
const MISS = {not_grouped: "agent không gom vào sự kiện", not_candidate: "bộ lọc tin loại", earlier_run: "đã có ở buổi trước",
  later_run: "đến sau giờ chạy", beyond_limit: "vượt giới hạn số tin"};
const RUN = {ok: "good", partial: "warn", failed: "bad"};
const badge = (pair, fallback) => `<span class="badge ${pair ? pair[0] : ""}">${esc(pair ? pair[1] : fallback)}</span>`;
// a rate as k/n: “—” with its n when nothing to divide, never 0 %
const rate = (r, metric) => (!r || !r.n ? `— <span class="muted small">(0)</span>`
  : `${how(pct(r.value, false, 0), metric, {hits: String(r.hits), n: String(r.n)})} <span class="muted small">(${r.hits}/${r.n})</span>`);
const money = (x, metric, n) => `${how(vnd(x.vnd, true), metric, {n: String(x.n)})} <span class="muted small">(${x.n})</span>`;
const usd = (x) => (x == null ? "chưa có" : `US$${x.toFixed(2)}`);

function paint(box, d) {
  const e = d.evaluation;
  const tabs = `<div class="seg" role="group" aria-label="Góc xem"><button type="button" data-view="a" aria-pressed="${view === "a"}">A · Thu thập tin</button><button type="button" data-view="b" aria-pressed="${view === "b"}">B · Hiệu quả agent</button></div>`;
  const seg = `<div class="seg" role="group" aria-label="Kỳ hạn">${H.map(([k, l]) => `<button type="button" data-h="${k}" aria-pressed="${horizon === k}">${l}</button>`).join("")}</div>`;
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO · Mô hình</div><h1 class="h1">Thử nghiệm hằng ngày</h1>
      <p class="lede">Mỗi sáng 08:30 agent tự gom tin thành sự kiện; Agent CIO và Agent Phản biện chạy trên từng sự kiện, không ai duyệt.
        ${d.days.length ? `${d.days.length} buổi sáng: ${day(d.days[0])} – ${day(d.days[d.days.length - 1])}.` : "Chưa có buổi sáng nào."}</p></div>
      <div class="row">${tabs}${view === "b" ? seg : ""}</div></div>
    ${e ? (view === "a" ? viewA(d, e.collection) : viewB(d, e)) : legacy(d)}`;
}

function viewA(d, m) {
  const last = m.last_run, today = m.days[0] || {}, r = d.recall;
  const rel = today.retained ? {value: today.relevant / today.retained, hits: today.relevant, n: today.retained} : null;
  const cats = Object.entries(m.categories);
  const opt = (x) => (x == null ? `<span class="muted">—</span>` : num(x));
  return `
    <div class="kpis">
      ${kpi("Lần lấy tin gần nhất", last ? `${badge([RUN[last.status], last.status === "ok" ? "ổn" : last.status === "partial" ? "một phần" : "lỗi"])}` : "—",
        last ? `${when(last.at)} · ${last.succeeded}/${last.attempted} nguồn · ${last.duration_s == null ? "thời gian chưa ghi" : secs(last.duration_s)}` : "chưa có lần nào")}
      ${kpi("Hôm nay giữ lại", num(today.retained), `${num(today.fetched)} tin đọc · ${num(today.duplicates)} trùng · ${today.runs || 0} lần lấy`)}
      ${kpi("Liên quan danh mục", rate(rel, "collect.relevant"), "mức liên quan cao hoặc vừa, không bị giữ")}
      ${kpi("Tin quan trọng thu được", r.share != null ? how(pct(r.share, false, 0), "trial.recall", {collected: String(r.collected), important: String(r.important)}) : "—", `${r.collected}/${r.important} tin của nguồn đối chiếu (KPI-02)`)}
    </div>

    <section class="panel mt"><h3>Theo ngày <span class="hint">ngày thu thập (giờ Việt Nam), không phải ngày đăng</span></h3>
      <div class="scrollx"><table class="table"><thead><tr><th>Ngày</th><th class="num">Lần lấy</th><th>Từ – đến</th><th class="num">Thời gian lấy</th><th class="num">Lỗi</th><th class="num">Đọc</th><th class="num">Trùng</th><th class="num">Mới</th><th class="num">Giữ lại</th><th class="num">Liên quan</th><th class="num">Tác động danh mục</th>
        ${cats.map(([, l]) => `<th class="num">${esc(l)}</th>`).join("")}<th class="num">Thiếu giờ đăng</th><th class="num">Trễ</th></tr></thead><tbody>
        ${m.days.map(x => `<tr><td>${day(x.day)}</td><td class="num">${x.runs}</td><td style="white-space:nowrap">${x.first_run ? `${hm(x.first_run)} – ${hm(x.last_run)}` : "—"}</td>
          <td class="num">${x.duration_s_total == null ? "—" : `${how(secs(x.duration_s_total), "collect.duration", {runs: String(x.duration_runs)})}${x.duration_runs < x.runs ? ` <span class="muted small">(${x.duration_runs}/${x.runs} lần)</span>` : ""}`}</td><td class="num">${x.runs_failed + x.runs_partial ? `<span class="bad-text">${x.runs_failed + x.runs_partial}</span>` : 0}</td>
          <td class="num">${opt(x.fetched)}</td><td class="num">${opt(x.duplicates)}</td><td class="num">${x.unique}</td><td class="num">${x.retained}</td>
          <td class="num">${x.retained ? rate({value: x.relevant / x.retained, hits: x.relevant, n: x.retained}, "collect.relevant") : "—"}</td>
          <td class="num">${how(num(x.portfolio), "collect.portfolio", {families: String(x.portfolio_families)})}${x.portfolio ? ` <span class="muted small">(${x.portfolio_families} gia đình)</span>` : ""}</td>
          ${cats.map(([k]) => `<td class="num">${x.by_category[k] || 0}</td>`).join("")}
          <td class="num">${x.missing.published}</td><td class="num">${x.lag_min_p50 == null ? "—" : `${Math.round(x.lag_min_p50)} phút`}</td></tr>`).join("")}
      </tbody></table></div>
      <p class="footnote">Lỗi: số lần lấy có ít nhất một nguồn lỗi. “—”: lần lấy trước ${m.full_since ? when(m.full_since) : "khi có bộ đếm"} không ghi số này (không có số liệu, không phải 0). Trễ: trung vị từ lúc báo đăng đến lúc ta thu. Tác động danh mục: tin thuộc sự kiện đã áp dụng lên ít nhất một gia đình; số này tăng sau ngày thu.</p>
    </section>

    <section class="panel mt"><h3>Nguồn <span class="hint">${m.sources.length} nguồn · ${m.days.length} ngày</span></h3>
      <div class="scrollx"><table class="table"><thead><tr><th>Nguồn</th><th class="num">Lần lấy</th><th class="num">Lỗi</th><th class="num">Tin đọc</th><th>Lỗi gần nhất</th></tr></thead><tbody>
        ${m.sources.map(s => `<tr><td>${esc(s.source)}</td><td class="num">${s.attempted}</td><td class="num">${s.failed ? `<span class="bad-text">${s.failed}</span>` : 0}</td><td class="num">${num(s.fetched)}</td>
          <td class="small muted">${s.last_error ? `${when(s.last_error.at)} · ${esc(String(s.last_error.error).slice(0, 80))}` : ""}</td></tr>`).join("")}
      </tbody></table></div>
    </section>`;
}

function viewB(d, e) {
  const a = e.accuracy.horizons[horizon], f = e.finance.horizons[horizon], c = a.coverage, ev = e.accuracy.event_recall;
  const fams = Object.entries(e.accuracy.families);
  const mine = e.moves.filter(x => x.horizon === horizon);
  const order = ["correct", "incorrect", "missed", "quiet", "failed", "pending", "excluded"];
  mine.sort((x, y) => order.indexOf(x.verdict) - order.indexOf(y.verdict) || (x.day < y.day ? 1 : -1));
  const missCount = {};
  for (const m of ev.misses) missCount[m.why] = (missCount[m.why] || 0) + 1;
  const late = Object.values(e.finance.snapshots).filter(s => s.late).length;
  return `
    <section class="panel mt"><h3>Các buổi sáng <span class="hint">${e.accuracy.mornings.length}</span></h3>
      <p class="small">${e.accuracy.mornings.map(m => `${day(m.day)} ${badge(MORNING[m.status], m.status)}${m.drafts ? ` <span class="muted">${m.drafts} bản nháp</span>` : ""}`).join(" · ") || "Chưa có."}</p>
    </section>

    <div class="kpis mt">
      ${kpi("Độ chính xác", rate(a.precision, "eval.precision"), "khi agent nói tăng hoặc giảm, thị trường đi đúng và đủ mạnh")}
      ${kpi("Độ phủ biến động lớn", rate(a.recall, "eval.recall"), `bỏ lỡ ${a.missed.not_predicted} · sai hướng ${a.missed.wrong_direction}${a.missed.no_run ? ` · không chạy ${a.missed.no_run}` : ""}`)}
      ${kpi("Đúng hướng", rate(a.direction, "eval.direction"), a.error_sd.n ? `sai số ${a.error_sd.value.toFixed(2).replace(".", ",")} lần biến động thường (${a.error_sd.n})` : "sai số: chưa có")}
      ${kpi("Đã chấm", `${c.scored}/${c.moves}`, `${c.pending} chờ · ${c.failed} không chấm được · ${c.excluded} loại ra${a.first_due ? ` · hạn đầu ${day(a.first_due)}` : ""}`)}
    </div>
    ${a.uncalibrated ? `<p class="small warn-text mt-xs">Kỳ 3 ngày chưa hiệu chỉnh: biến động ngắn phần lớn là nhiễu.</p>` : ""}
    ${c.scored ? "" : `<p class="small muted mt-xs">Chưa dự báo nào đến hạn chấm ở kỳ ${HL[horizon]}: các tỷ lệ hiện “—”, không phải 0.</p>`}

    <section class="panel mt"><h3>Theo nhóm tài sản <span class="hint">${HL[horizon]}</span></h3>
      <div class="scrollx"><table class="table"><thead><tr><th></th><th class="num">Độ chính xác</th><th class="num">Độ phủ</th><th class="num">Đúng hướng</th><th class="num">Đúng · sai · bỏ lỡ</th><th class="num">Chờ</th></tr></thead><tbody>
        ${fams.map(([k, l]) => { const x = a.by_family[k]; return `<tr><td>${esc(l)}</td><td class="num">${rate(x.precision, "eval.precision")}</td><td class="num">${rate(x.recall, "eval.recall")}</td>
          <td class="num">${rate(x.direction, "eval.direction")}</td><td class="num">${x.counts.correct} · ${x.counts.incorrect} · ${x.counts.missed}</td><td class="num">${x.counts.pending}</td></tr>`; }).join("")}
      </tbody></table></div>
    </section>

    <section class="panel mt"><h3>Lãi lỗ mô phỏng <span class="hint">${esc(e.finance.label)} · ${HL[horizon]}</span></h3>
      <div class="kpis">
        ${kpi("Gọi đúng", money(f.correct, "eval.vnd_correct"), "giá trị nếu theo các lần gọi đúng")}
        ${kpi("Gọi sai", money({...f.incorrect, vnd: -f.incorrect.vnd}, "eval.vnd_incorrect"), "thiệt nếu theo các lần gọi sai")}
        ${kpi("Ròng", money(f.net, "eval.vnd_net"), `cảnh báo giảm đúng ${money(f.negative_warnings, "eval.vnd_warning")}`)}
        ${kpi("Cơ hội bỏ lỡ", money(f.missed_opportunity, "eval.vnd_missed"), "không trừ vào ròng")}
      </div>
      <p class="footnote">Một phép giả định trên danh mục mô phỏng của ${Object.keys(e.finance.snapshots).length ? "các gia đình" : "—"}, không phải lãi lỗ thật và không chứng minh agent gây ra lãi lỗ.
        ${f.unavailable ? `${f.unavailable} dự báo đã chấm không có ảnh chụp danh mục: không tính (không phải 0). ` : ""}${late ? `${late} buổi sáng chụp danh mục muộn (ghi rõ trên từng dự báo).` : ""}</p>
      <details class="more"><summary>Theo nhóm tài sản</summary>
        <div class="scrollx"><table class="table"><thead><tr><th></th><th class="num">Đúng</th><th class="num">Sai</th><th class="num">Ròng</th><th class="num">Bỏ lỡ</th></tr></thead><tbody>
          ${fams.map(([k, l]) => { const x = f.by_family[k]; return `<tr><td>${esc(l)}</td><td class="num">${money(x.correct, "eval.vnd_correct")}</td><td class="num">${money({...x.incorrect, vnd: -x.incorrect.vnd}, "eval.vnd_incorrect")}</td>
            <td class="num">${money(x.net, "eval.vnd_net")}</td><td class="num">${money(x.missed_opportunity, "eval.vnd_missed")}</td></tr>`; }).join("")}
        </tbody></table></div></details>
    </section>

    <section class="panel mt"><h3>Agent chọn sự kiện <span class="hint">tin quan trọng của nguồn đối chiếu đã vào sự kiện</span></h3>
      <p class="small">${rate(ev, "eval.event_recall")} · ${ev.by_day.map(x => `${day(x.day)} ${x.in_events}/${x.important}`).join(" · ")}</p>
      ${ev.misses.length ? `<details class="more"><summary>${ev.misses.length} tin lọt: ${Object.entries(missCount).map(([k, n]) => `${esc(MISS[k] || k)} ${n}`).join(" · ")}</summary>
        <ul class="small">${ev.misses.map(m => `<li>${day(m.day)} · ${esc(m.title)} <span class="muted">— ${esc(MISS[m.why] || m.why)}</span></li>`).join("")}</ul></details>` : ""}
    </section>

    <section class="panel mt"><h3>Chi phí gọi mô hình <span class="hint">${e.costs.total.n_reported}/${e.costs.total.n_calls} lần gọi có chi phí · tổng ${usd(e.costs.total.cost_usd)}</span></h3>
      <div class="scrollx"><table class="table"><thead><tr><th>Agent</th><th class="num">Lần gọi</th><th class="num">Token</th><th class="num">Chi phí</th><th class="num">Thời gian</th><th class="num">Thử lại · lỗi</th><th>Mô hình</th></tr></thead><tbody>
        ${Object.entries(e.costs.agents).map(([k, x]) => `<tr><td>${esc(AGENT[k] || k)}</td><td class="num">${x.n_calls}</td><td class="num">${x.n_tokens ? num(x.tokens) : "—"}</td>
          <td class="num">${usd(x.cost_usd)} <span class="muted small">(${x.n_reported}/${x.n_calls})</span></td><td class="num">${x.ms_p50 == null ? "—" : `${secs(x.ms_p50 / 1000)} · ${secs(x.ms_p95 / 1000)}`}</td>
          <td class="num">${x.retries} · ${x.errors ? `<span class="bad-text">${x.errors}</span>` : 0}</td><td class="small muted">${x.models.map(esc).join(", ")}</td></tr>`).join("")}
      </tbody></table></div>
      <p class="footnote">Chi phí theo giá API của lần gọi qua gói Claude Code (ước tính, không phải hóa đơn). Thời gian: trung vị · p95. Lần gọi không báo chi phí hiện “chưa có”, không tính là 0.</p>
    </section>

    <section class="panel mt"><h3>Từng dự báo <span class="hint">${mine.length} · ${HL[horizon]} · bấm để xem từ tin đến kết quả</span></h3>
      <div class="scrollx"><table class="table"><thead><tr><th>Ngày</th><th>Yếu tố</th><th>Agent nói</th><th>Thị trường</th><th>Kết quả</th></tr></thead><tbody>
        ${mine.slice(0, 60).map(x => `<tr><td>${day(x.day)}</td><td><button type="button" class="linkbtn" data-move="${esc(x.id)}">${esc(x.factor_name || x.factor)}</button></td>
          <td>${esc(CLAIM[x.claim] || "không nói")}</td><td>${x.move ? esc(CLAIM[x.move]) : `<span class="muted">chưa có</span>`}</td>
          <td>${badge(VERDICT[x.verdict], x.verdict)} <span class="small muted">${esc(REASON[x.reason] || "")}</span></td></tr>`).join("")}
      </tbody></table></div>
      ${mine.length > 60 ? `<p class="small muted">${mine.length - 60} dự báo chờ chấm khác.</p>` : ""}
    </section>

    <details class="panel flat mt more"><summary>Số đo cũ của thử nghiệm (dự báo bóng, mua · bán · giữ, kịch bản, sự kiện)</summary>${legacy(d)}</details>`;
}

const AGENT = {cio: "Agent CIO", challenger: "Agent Phản biện", grouping: "Gom tin thành sự kiện"};
const CLAIM = {up: "tăng", down: "giảm", flat: "đứng", conflicting: "trái chiều"};

async function openMove(id) {
  const body = drawer("Một dự báo", `<p class="muted">Đang tải…</p>`);
  const s = await get(`/api/trial/move/${encodeURIComponent(id)}`);
  const unit = (x) => (x == null ? "—" : s.unit === "pct" ? how(pct(x, true, 1), "eval.move", {unit: s.unit}) : `${x > 0 ? "+" : ""}${x.toFixed(2).replace(".", ",")} ${esc(s.unit)}`);
  const fams = s.vnd ? Object.entries(s.vnd.families) : [];
  body.innerHTML = `
    <p><b>${esc(s.factor_name)}</b> · ${HL[s.horizon]} · từ giá đóng cửa ${day(s.origin)} đến ${day(s.due)}</p>
    <p class="small mt"><b>1 · Tin và sự kiện</b></p>
    ${s.drafts.length ? s.drafts.map(x => `<div class="mt-xs"><div class="small"><b>${esc(x.event || x.event_id)}</b> · <a href="#/cio/nhan-dinh/${esc(x.view_id)}">${esc(x.view_id)}</a></div>
      <ul class="small muted">${x.news.map(n => `<li>${esc(n.title)} <span class="muted">— ${esc(n.source || "")}</span></li>`).join("")}</ul></div>`).join("")
      : `<p class="small muted">Buổi sáng này không bản nháp nào nói về yếu tố này.</p>`}
    <p class="small mt"><b>2 · Agent nói</b></p>
    <p class="small">${esc(CLAIM[s.claim] || "không nói")} · kỳ vọng ${unit(s.expected)} · ngưỡng “nói” ${unit(s.claim_share * s.scale)}</p>
    <p class="small mt"><b>3 · Thị trường</b></p>
    <p class="small">${s.realised == null ? "chưa có số liệu" : `${unit(s.realised)} · ${s.material ? "biến động lớn" : "biến động nhỏ"} (ngưỡng ${unit(s.material_sigma * s.scale)})`}</p>
    <p class="small mt"><b>4 · Kết quả</b></p>
    <p>${badge(VERDICT[s.verdict], s.verdict)} <span class="small muted">${esc(REASON[s.reason] || "")}</span></p>
    <p class="small mt"><b>5 · Giá trị mô phỏng theo gia đình</b></p>
    ${s.vnd ? (fams.length ? `<table class="table"><tbody>${fams.map(([cid, x]) => `<tr><td>${esc(s.family_names[cid] || cid)}</td>
      <td class="num">${how(vnd(x.effect, true), "eval.vnd_effect")}</td><td class="num">${x.value ? how(vnd(x.value, true), "eval.vnd_net") : x.opportunity ? how(vnd(x.opportunity), "eval.vnd_missed") : "—"}</td></tr>`).join("")}</tbody></table>
      <p class="footnote">${esc(s.label)}${s.vnd.late ? " · danh mục chụp muộn" : ""}. Cột 1: biến động tác động lên danh mục; cột 2: giá trị của lần gọi.</p>` : `<p class="small muted">Không gia đình nào chịu tác động của yếu tố này.</p>`)
      : `<p class="small muted">Chưa có: ${s.realised == null ? "dự báo chưa chấm" : "không có ảnh chụp danh mục buổi sáng này"}.</p>`}`;
}

function accRow(label, a) {
  return `<tr><td>${label}</td><td class="num">${a.kept}</td><td class="num">${a.n}</td>
    <td class="num">${share(a.direction_hit, a.direction_n, "trial.direction")}</td><td class="num">${share(a.coverage, a.n, "trial.coverage")}</td></tr>`;
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
      Một lần đọc đầu, chưa phải bằng chứng: ${r.runs.drafts} sự kiện trong ba tuần của một mùa hè.
      <b>Các dự báo không độc lập:</b> mọi dự báo tháng 7 được chấm trên cùng một diễn biến (VN-Index giảm từ tháng 7 đến tháng 10), nên tỷ lệ đúng của VN-Index là một lần đoán đúng một xu hướng.</p>
    ${accTable([accRow("<b>Tất cả</b>", a),
      ...Object.entries(d.segments).map(([k, l]) => accRow(esc(l), a.by_segment[k])),
      ...(vn ? [accRow("<b>VN-Index</b>", vn)] : [])])}
    <p class="small mt-xs">Mua · bán · giữ: ${calls.map(x => `${esc(x.label)} ${share(x.share, x.n, "trial.call")}`).join(" · ")}.
      Kịch bản: ${sc && sc.judged ? `thị trường đi theo kịch bản agent cho là khả năng cao nhất ${sc.main_taken}/${sc.judged} lần (${share(sc.share, sc.judged, "trial.scenario")})` : "chưa đủ yếu tố đã chấm"}.</p>
  </section>`;
}

function legacy(d) {
  const c = d.collection, r = d.recall, runs = d.runs, a = d.accuracy[horizon];
  const perDay = Object.values(c.per_day || {});
  const avg = perDay.length ? Math.round(c.items / perDay.length) : null;
  const calls = (d.calls[horizon] || []);
  const sc = (d.scenarios || {})[horizon];
  return `

    <div class="kpis">
      ${kpi("Tin thu thập", num(c.items), avg != null ? `~${num(avg)} tin/ngày · ${how(pct(c.items ? c.typed / c.items : 0, false, 0), "trial.typed", {items: num(c.items)})} có loại sự kiện` : "chưa có tin")}
      ${kpi("Tin quan trọng thu được", r.share != null ? how(pct(r.share, false, 0), "trial.recall", {collected: String(r.collected), important: String(r.important)}) : "—", `${r.collected}/${r.important} tin của nguồn đối chiếu · mục tiêu ${how(pct(r.target, false, 0), "trial.recall_target")} (KPI-02)`)}
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
          <td class="num">${x.n}</td><td class="num">${share(x.share, x.n, "trial.call")}</td></tr>`).join("")}
      </tbody></table></div>
    </section>

    <section class="panel mt"><h3>Kịch bản <span class="hint">${HL[horizon]}</span></h3>
      <p class="small">${sc && sc.judged ? `Trong ${sc.judged} bản nháp đã chấm đủ, thị trường đi theo kịch bản agent cho là khả năng cao nhất <b>${sc.main_taken} lần</b> (${how(pct(sc.share, false, 0), "trial.scenario", {horizon: HL[horizon], n: String(sc.judged)})})${sc.tied ? `; ${sc.tied} lần hai kịch bản ngang nhau` : ""}.`
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
