/* Quản trị · Hệ thống (BRD-RULE-ROLE-04, NFR-12; F5): the jobs and how each last went, the news feeds, the agents,
   the audit chain's check, a load of the market history on request, and the people with their accounts. Read from
   the stored records (GET /api/system); the load is queued for the market_load job (POST /api/market/load). */
import {ago, esc, get, n as how, num, pct, post, toast} from "../core/core.js";

const ROLE = {cio: "CIO", rm: "RM", compliance: "Tuân thủ", admin: "Quản trị"};
export const JOB = {  // what each job does (also the Admin desk's names, desk/admin.js), in the product's language (the declaration in app/main.py is for developers)
  policy_sweep: "Rà soát quy định mới cho từng khách hàng",
  news_ingest: "Lấy tin từ các nguồn trong danh sách trắng vào hộp tin (FR-101)",
  market_equity: "Giá đóng cửa VN-Index và cổ phiếu (VNDirect, dự phòng Vietcap)",
  market_flows: "Giao dịch ròng của khối ngoại trên HOSE (cafef)",
  market_yields: "Lợi suất trái phiếu chính phủ (HNX, dự phòng worldgovernmentbonds)",
  market_fx: "Tỷ giá USD/VND (Vietcombank, dự phòng MSN)",
  market_world: "Vàng, dầu Brent, chỉ số thế giới, lợi suất Mỹ 10 năm (MSN)",
  market_crypto: "Bitcoin và Ether (Binance)",
  market_gold: "Vàng miếng SJC (lịch sử giá PNJ)",
  market_load: "Lần nạp lại lịch sử mà Quản trị yêu cầu ở trang này",
  agent_worker: "Chạy lần lượt các yêu cầu “Chạy Agent CIO” đang xếp hàng (AI-13)",
  inbox_import: "Nhập các gói từ vùng AI qua cùng các kiểm tra, hoặc từ chối kèm lý do (ZONE-03)",
  zone_sync: "Gửi vùng AI danh mục đã duyệt và nghiên cứu đã phát hành (chế độ hộp chờ)",
  audit_check: "Kiểm tra chuỗi nhật ký kiểm toán và chép dòng mới vào đoạn chỉ-ghi-một-lần; gãy thì báo Tuân thủ và Quản trị",
  news_reference: "Đọc nguồn đối chiếu độc lập (Google News) mỗi 2 giờ; một ngày sau, chấm tin quan trọng đã thu thập hay chưa (KPI-02)",
  heartbeat: "Ghi nhịp của máy chủ; đo mức sẵn sàng trong giờ làm việc, dưới mục tiêu thì báo Quản trị (NFR-03)",
  agent_eval: "Bộ đánh giá cố định cho đề xuất lời nhắc và mô hình AI (MEAS-07)",
  accuracy_score: "Chấm độ chính xác các dự báo đã đến hạn (FEAT-18)",
  market_backfill: "Lịch sử mọi chuỗi từ 2020 (chạy bằng dòng lệnh)",
  statement_reading: "Đánh giá việc đọc sao kê (chạy bằng dòng lệnh)",
  assistant_retention: "Xoá các cuộc trò chuyện quá hạn lưu và các mục ghi nhớ đã hết hạn của trợ lý (A4)",
  assistant_consolidate: "Tóm các cuộc trò chuyện đã ngừng 15 phút vào bộ nhớ của từng người (A6)",
};
const ALERT = {open: ["bad", "Đang mở"], acked: ["warn", "Đã xem"], resolved: ["good", "Đã hết"]};
const MODE = {live: "Mô hình thật", mock: "Mô phỏng", inbox: "Hộp chờ (vùng AI)"};
const INBOX = {READY: ["warn", "Chờ nhập"], PROCESSING: ["warn", "Đang nhập"], IMPORTED: ["good", "Đã nhập"], REJECTED: ["bad", "Từ chối"]};
const LOAD = {asked: ["warn", "Đang chờ"], running: ["warn", "Đang nạp"], done: ["good", "Xong"], failed: ["bad", "Lỗi"]};

function when(w) {
  if (w.at) return `hằng ngày ${esc(w.at)}`;
  if (w.every) return `mỗi ${esc(w.every.replace("h", " giờ").replace("m", " phút"))}`;
  return `<span class="muted">khi được yêu cầu</span>`;
}

function last(l) {
  if (!l) return `<span class="small muted">không ghi lại ở đây</span>`;
  return `<span class="badge ${l.ok ? "good" : "bad"}">${l.ok ? "ổn" : "lỗi"}</span> <span class="small">${esc(ago(l.at))}</span>
    ${l.error ? `<div class="small ${l.ok ? "muted" : "bad-text"}">${esc(l.error)}</div>` : ""}`;
}

function tile(label, value, note, tone = "", span = "c3") {
  return `<div class="panel ${span}"><div class="small muted">${label}</div><div class="h2 ${tone}">${value}</div><div class="small muted">${note}</div></div>`;
}

// BRD-NFR-03: business minutes with a heartbeat ÷ business minutes, this month (control/uptime.py)
function availability(a) {
  if (!a || !a.measured || a.availability == null) return tile("Sẵn sàng (giờ làm việc)", "Chưa đo", "chưa có nhịp nào trong giờ làm việc", "", "c4");
  const value = how(pct(a.availability, false, 2), "uptime.availability", {month: a.month, business_minutes: a.business_minutes, up_minutes: a.up_minutes});
  const note = `tháng ${esc(a.month)} · mục tiêu ${how(pct(a.target, false, 1), "uptime.availability", {month: a.month})} · ${a.outages.length ? `${a.outages.length} lần gián đoạn, ${num(a.down_minutes)} phút` : "không gián đoạn"}`;
  return tile("Sẵn sàng (giờ làm việc)", value, note, a.met ? "" : "bad-text", "c4");
}

export async function render(box, ctx) {
  const d = await get("/api/system");
  const failing = d.jobs.filter(j => j.last && !j.last.ok);
  const running = d.loads.find(l => l.status === "asked" || l.status === "running");
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Quản trị</div>
      <h1 class="h1">Hệ thống</h1>
      <p class="lede">${d.jobs.length} việc chạy nền${failing.length ? ` · <span class="bad-text">${failing.length} đang lỗi</span>` : " · không việc nào đang lỗi"}
        · ${d.alerts_open ? `<span class="bad-text">${d.alerts_open} cảnh báo đang mở</span>` : "không có cảnh báo mở"}
        · chuỗi nhật ký ${d.chain.ok ? "toàn vẹn" : `<span class="bad-text">gãy ở dòng ${d.chain.broken_at}</span>`}.</p></div></div>

    <div class="cols">
      ${tile("Chuỗi nhật ký", d.chain.ok && d.worm.ok ? "Toàn vẹn" : "Gãy", `${num(d.chain.count)} dòng${d.chain.ok ? "" : " · " + esc(d.chain.reason)}${!d.worm.on ? "" : d.worm.ok ? ` · ${num(d.worm.segments)} đoạn chỉ-ghi-một-lần tới dòng ${num(d.worm.last)}` : ` · <span class="bad-text">${esc(d.worm.reason)}</span>`}`, d.chain.ok && d.worm.ok ? "" : "bad-text", "c4")}
      ${availability(d.availability)}
      ${tile("Agent", MODE[d.agents.mode] || esc(d.agents.mode), `${esc(d.agents.reason || [d.agents.models?.cio, d.agents.models?.challenger].filter(Boolean).join(" · "))}${d.agent_queue ? ` · ${d.agent_queue} lần chạy đang xếp hàng` : ""}`, "", "c4")}
      ${tile("Tin tức", d.news_at ? esc(ago(d.news_at)) : "Chưa lấy", `${d.feeds.length} nguồn · ${d.feeds.filter(f => f.error).length} lỗi lần gần nhất`, "", "c6")}
      ${tile("Cấu hình chờ duyệt", d.config_waiting.length, d.config_waiting.map(c => esc(c.label)).join(", ") || "không có", "", "c6")}
    </div>

    <section class="panel mt" id="alerts"><div class="h3">Cảnh báo</div>
      <p class="small muted">Nguồn tin hay chuỗi thị trường không lấy được, agent lỗi, chuỗi nhật ký gãy, gói từ vùng AI bị từ chối, không gửi được vùng AI. Một cảnh báo cho mỗi việc: lỗi lại thì đếm thêm, chạy lại được thì tự hết. “Đã xem” được ghi vào nhật ký.</p>
      <div class="scrollx"><table class="table"><thead><tr><th>Cảnh báo</th><th>Trạng thái</th></tr></thead><tbody>
      ${d.alerts.map(a => `<tr><td><b>${esc(a.title)}</b><div class="small muted">${esc(a.label)} · <span class="mono">${esc(a.id)}</span> · ${a.count} lần, gần nhất ${esc(ago(a.last_at))}</div>${a.detail ? `<div class="small ${a.status === "resolved" ? "muted" : "bad-text"}">${esc(a.detail)}</div>` : ""}</td>
        <td><span class="badge ${ALERT[a.status][0]}">${ALERT[a.status][1]}</span>${a.history.filter(h => h.status === "acked").map(h => `<div class="small muted">${esc(h.by)}${h.note ? `: ${esc(h.note)}` : ""}</div>`).join("")}
          ${a.status === "open" ? `<div class="mt"><button type="button" class="btn sm" data-ack="${esc(a.id)}">Đã xem</button></div>` : ""}</td></tr>`).join("")
        || `<tr><td colspan="2" class="muted">Không có cảnh báo nào.</td></tr>`}
      </tbody></table></div></section>

    <section class="panel mt"><div class="h3">Việc chạy nền</div>
      <div class="scrollx"><table class="table"><thead><tr><th>Việc</th><th>Lịch</th><th>Lần gần nhất</th></tr></thead><tbody>
      ${d.jobs.map(j => `<tr><td><b class="mono">${esc(j.id)}</b><div class="small muted">${esc(JOB[j.id] || j.description || "")}</div></td>
        <td class="small">${when(j.when)}</td><td>${last(j.last)}</td></tr>`).join("")}
      </tbody></table></div>
      <p class="small muted">Việc thị trường: từng chuỗi ở trang Dữ liệu thị trường. Việc không ghi kết quả ở đây được xem trong nhật ký và dấu vết của operonx.</p></section>

    <section class="panel mt"><div class="h3">Nguồn tin, lần lấy gần nhất</div>
      <div class="scrollx"><table class="table"><thead><tr><th>Nguồn</th><th class="num">Lấy về</th><th class="num">Nhận</th><th class="num">Loại</th><th>Lỗi</th></tr></thead><tbody>
      ${d.feeds.map(f => `<tr><td class="mono">${esc(f.id)}</td><td class="num">${f.fetched}</td><td class="num">${f.accepted}</td><td class="num">${f.refused}</td>
        <td class="small">${f.error ? `<span class="bad-text">${esc(f.error)}</span>` : `<span class="muted">—</span>`}</td></tr>`).join("") || `<tr><td colspan="5" class="muted">Chưa lấy lần nào.</td></tr>`}
      </tbody></table></div></section>

    <section class="panel mt"><div class="h3">Agent, 7 ngày qua</div>
      <div class="scrollx"><table class="table"><thead><tr><th>Agent</th><th class="num">Lần chạy</th><th class="num">Lỗi</th><th>Lần gần nhất</th></tr></thead><tbody>
      ${d.agent_runs.map(a => `<tr><td class="mono">${esc(a.agent)}</td><td class="num">${a.runs}</td><td class="num ${a.failed ? "bad-text" : ""}">${a.failed}</td>
        <td class="small">${esc(ago(a.last))} · ${esc(a.last_status || "")}${a.last_error ? ` · <span class="bad-text">${esc(a.last_error)}</span>` : ""}</td></tr>`).join("") || `<tr><td colspan="4" class="muted">Không có lần chạy nào.</td></tr>`}
      </tbody></table></div>
      ${d.evals_waiting.length ? `<p class="small">Bộ đánh giá đang chờ chạy: ${d.evals_waiting.map(e => esc(e.id)).join(", ")}</p>` : ""}</section>

    <section class="panel mt" id="zone"><div class="h3">Vùng AI và hộp chờ</div>
      <p class="small muted">Chế độ chạy AI: <b>${esc(MODE[d.agents.configured] || d.agents.configured)}</b> (cấu hình “Chế độ chạy AI” ở trang <a href="#/admin/cau-hinh">Cấu hình</a>).
        Ở chế độ hộp chờ, vùng AI là một tiến trình riêng với cơ sở dữ liệu riêng, chỉ có tin công khai, nghiên cứu đã phát hành và danh mục đã duyệt; nó gửi gói đã ký vào hộp chờ và không đọc lại gì.</p>
      <div class="scrollx"><table class="table"><thead><tr><th>Gói</th><th>Nhận</th><th>Chữ ký</th><th>Trạng thái</th><th>Kết quả</th></tr></thead><tbody>
      ${d.inbox.map(p => `<tr><td class="mono">${esc(p.id)}</td><td class="small">${esc(ago(p.received))}</td>
        <td>${p.signed ? `<span class="badge good">hợp lệ</span>` : `<span class="badge bad">không</span>`}</td>
        <td><span class="badge ${INBOX[p.status][0]}">${INBOX[p.status][1]}</span></td>
        <td class="small">${p.view_id ? `<a href="#/cio/nhan-dinh/${esc(p.view_id)}">${esc(p.view_id)}</a> · ${esc(p.event_id)}` : p.error ? `<span class="bad-text">${esc(p.error)}</span>` : p.waiting ? `<span class="muted">${esc(p.waiting)}</span>` : "—"}</td></tr>`).join("")
        || `<tr><td colspan="5" class="muted">Chưa nhận gói nào.</td></tr>`}
      </tbody></table></div>
      ${d.zone_syncs.length ? `<p class="small mt">Lần gửi vùng AI gần nhất: ${d.zone_syncs[0].status === "ok" ? `<span class="badge good">ổn</span>` : `<span class="badge bad">lỗi</span> ${esc(d.zone_syncs[0].error || "")}`}
        ${esc(ago(d.zone_syncs[0].at))}${d.zone_syncs[0].applied?.length ? ` · áp dụng ${d.zone_syncs[0].applied.map(esc).join(", ")}` : ""}</p>` : ""}</section>

    <section class="panel mt" id="load"><div class="h3">Nạp lại lịch sử thị trường</div>
      <p class="small muted">Lấy lại mọi chuỗi từ ngày đã chọn (các nguồn công khai, có thể mất vài phút). Việc <span class="mono">market_load</span> chạy yêu cầu trong vòng một phút; mỗi lần một yêu cầu.</p>
      <div class="row mt"><label class="small" for="since">Từ ngày</label>
        <input id="since" type="date" value="2020-01-01" min="2015-01-01" max="${new Date().toISOString().slice(0, 10)}">
        <button type="button" class="btn sm" id="ask" ${running ? "disabled" : ""}>${running ? "Đang có một lần nạp" : "Nạp lại"}</button></div>
      ${d.loads.length ? `<div class="scrollx mt"><table class="table"><thead><tr><th>Lần</th><th>Người yêu cầu</th><th>Từ ngày</th><th>Trạng thái</th><th class="num">Điểm</th></tr></thead><tbody>
        ${d.loads.map(l => `<tr><td class="small">${esc(ago(l.asked))}</td><td>${esc(l.by)}</td><td class="mono">${esc(l.since)}</td>
          <td><span class="badge ${LOAD[l.status][0]}">${LOAD[l.status][1]}</span>${l.error ? `<div class="small muted">${esc(l.error)}</div>` : ""}</td>
          <td class="num">${l.points == null ? "—" : num(l.points)}</td></tr>`).join("")}</tbody></table></div>` : ""}</section>

    <section class="panel mt" id="log"><div class="h3">Nhật ký hệ thống</div>
      <p class="small muted">Nhật ký tập trung (một dòng JSON mỗi sự việc, cả ngân hàng và vùng AI): 30 dòng cảnh báo và lỗi gần nhất.</p>
      ${d.log.length ? `<div class="scrollx"><table class="table"><tbody>${d.log.map(l => `<tr><td class="small">${esc(ago(l.at))}</td>
        <td><span class="badge ${l.level === "error" ? "bad" : "warn"}">${esc(l.level)}</span></td><td class="small mono">${esc(l.process)} · ${esc(l.event)}</td>
        <td class="small">${esc(l.title || l.path || l.detail || "")}</td></tr>`).join("")}</tbody></table></div>` : `<p class="small muted">Chưa có dòng nào.</p>`}</section>

    <section class="panel mt"><div class="h3">Người dùng</div>
      <div class="scrollx"><table class="table"><thead><tr><th>Người</th><th>Vai trò</th><th>Đăng nhập</th><th>Gia đình phụ trách</th></tr></thead><tbody>
      ${d.people.map(p => `<tr><td><b>${esc(p.name)}</b><div class="small muted">${esc(p.title || "")}</div></td><td>${esc(ROLE[p.role] || p.role)}</td>
        <td class="small mono">${esc(p.login)}${p.has_password ? "" : ` <span class="badge warn">chưa có mật khẩu</span>`}</td>
        <td class="small">${p.families ? esc(p.families.join(", ") || "—") : `<span class="muted">—</span>`}</td></tr>`).join("")}
      </tbody></table></div>
      <p class="small muted">${d.clients} tài khoản khách hàng. Phân công RM cho từng gia đình là cấu hình “Phân công RM” ở trang <a href="#/admin/cau-hinh">Cấu hình</a>.</p></section>`;
  box.querySelectorAll("[data-ack]").forEach(b => b.onclick = async () => {
    const note = prompt("Ghi chú (không bắt buộc): đã làm gì hoặc sẽ làm gì") ?? null;
    if (note === null) return;
    b.disabled = true;
    try { await post("/api/system/alerts/ack", {alert_id: b.dataset.ack, by: ctx.user, note}); toast("Đã ghi nhận"); }
    catch (e) { toast("Không ghi được: " + e.message); }
    render(box, ctx);
  });
  const ask = box.querySelector("#ask");
  ask.onclick = async () => {
    ask.disabled = true;
    try {
      const r = await post("/api/market/load", {by: ctx.user, since: box.querySelector("#since").value});
      toast(r.load.queued ? "Đã gửi yêu cầu nạp" : "Đang có một lần nạp, chưa gửi thêm");
    } catch (e) { toast("Không gửi được: " + e.message); }
    render(box, ctx);
  };
}
