/* CIO · Sự kiện & nhận định: events, the CIO agent's view of each, the independent challenge, and the
   decision. The page shows what the server decided (status, checks, findings); it decides nothing. */
import {ASSET_CLASS, EVENT_TYPE, HORIZON, empty, esc, get, post, pct, toast, viewBadge, viewLabel, when, runBadge, severity, signClass, vnd, n as how} from "../core/core.js";
import {moves, probBar, slot} from "../charts/charts.js";

const STEPS = [["DRAFTING", "Agent soạn"], ["PENDING_CHALLENGE", "Phản biện"], ["PENDING_APPROVAL", "CIO duyệt"], ["APPROVED", "Đã duyệt"]];
const SIZE = {S: "nhỏ", M: "vừa", L: "lớn"};
const UNIT = {pct: "%", bp: " đcb", pp: " điểm %", sd: " độ lệch chuẩn"};
const TARGET_TYPE = {asset_class: "Loại tài sản", sector: "Ngành", ticker: "Mã", fx: "Tỷ giá"};
const target = (r) => (r.target_type === "asset_class" ? ASSET_CLASS[r.target] || r.target : r.target);

export async function render(box, ctx) {
  const p = ctx.param || "";
  if (p.startsWith("VW-")) return renderView(box, ctx, p);
  if (p.startsWith("EV-")) return renderEvent(box, ctx, p);
  return renderList(box, ctx);
}

async function renderList(box, ctx) {
  const d = await get("/api/events");
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO · Sự kiện & nhận định</div><div class="h1">${d.events.length} sự kiện</div>
      <div class="lede small">Gom tin ở Hộp tin để lập sự kiện; chạy Agent CIO; đọc phản biện; duyệt.</div></div>
      <a class="btn" href="${ctx.href("hop-tin")}">Mở Hộp tin</a></div>
    <div class="panel" style="padding:8px">${d.events.length ? `<div class="list">${d.events.map(e => {
      const v = e.views[e.views.length - 1];
      return `<a class="item" href="${ctx.href("nhan-dinh", v ? v.id : e.id)}" style="text-decoration:none;color:inherit">
        <span class="badge">${esc(e.id.slice(-4))}</span>
        <div><div class="t" data-quote>${esc(e.title)}</div><div class="m">${esc(EVENT_TYPE[e.type] || "Chưa phân loại")} · ${e.news_ids.length} tin · ${when(e.created)}${e.blocked ? ' · <span class="badge bad">bị giữ</span>' : ""}${urgentBadge(e)}</div></div>
        <span>${v ? viewBadge(v.status) : '<span class="badge">Chưa chạy agent</span>'}</span></a>`;
    }).join("")}</div>` : empty("Chưa có sự kiện", "Vào Hộp tin, chọn vài tin cùng nói về một chuyện, rồi bấm “Gom thành sự kiện”.")}</div>`;
}

async function renderEvent(box, ctx, id) {
  const [{event: ev, views, jobs}, agents] = await Promise.all([get(`/api/events/${encodeURIComponent(id)}`), get("/api/agents")]);
  const job = jobs[jobs.length - 1], busy = job && ["queued", "running"].includes(job.status);
  box.innerHTML = `
    <div class="pagehead"><div><a class="small" href="${ctx.href("nhan-dinh")}">← Sự kiện</a>
      <div class="eyebrow" style="margin-top:6px">${esc(ev.id)} · ${esc(EVENT_TYPE[ev.type] || "Chưa phân loại")}</div><div class="h1" data-quote>${esc(ev.title)}</div></div></div>
    <div class="cols">
      <div class="panel c7"><h3>Tin nguồn <span class="hint">${ev.news.length} tin</span></h3>
        ${ev.news.map(n => `<div style="margin:8px 0"><a href="${esc(n.url)}" target="_blank" rel="noopener noreferrer" data-quote>${esc(n.title)}</a>
          <div class="small muted">${esc(n.outlet)} · ${esc(n.label)} · ${when(n.published)}${n.held ? ' · <span class="badge bad">bị giữ chờ Tuân thủ</span>' : ""}</div></div>`).join("")}</div>
      <div class="panel c5"><h3>Agent CIO</h3>
        ${ev.blocked ? `<div class="notice bad">Sự kiện đang bị giữ vì tin nhắc tới tổ chức trong danh sách hạn chế. Tuân thủ cần cho phép trước khi chạy agent.</div>` : `
        <div class="small">Chế độ hiện có: ${agents.mode === "live" ? `<span class="badge ai">Trực tiếp</span> ${esc(agents.models.cio)} soạn, ${esc(agents.models.challenger)} phản biện`
          : agents.mode === "inbox" ? `<span class="badge ai">Hộp chờ</span> nhận định đến từ vùng AI, qua hộp chờ có chữ ký` : `<span class="badge">Mô phỏng</span> theo từ khóa, không gọi AI`}</div>
        ${agents.mode === "inbox" ? "" : `<div class="row" style="margin-top:12px"><button type="button" class="btn primary" id="run" ${busy ? "disabled" : ""}>${busy ? "Agent đang chạy…" : "Chạy Agent CIO"}</button></div>`}
        <div class="small" style="margin-top:8px" id="job">${job ? jobLine(job) : ""}</div>
        <div class="small muted" style="margin-top:8px">Bốn nhóm phân tích chạy song song → tranh luận → tổng hợp và kiểm tra định dạng → Agent Phản biện. Agent chỉ đọc tin và danh mục thị trường, không đọc dữ liệu khách.</div>`}
        ${views.length ? `<h3 style="margin-top:16px">Các phiên bản</h3>${views.map(v => `<div class="row spread" style="margin:6px 0"><a href="${ctx.href("nhan-dinh", v.id)}">${esc(v.id)}</a><span>${viewBadge(v.status)} <span class="badge">${MODE_LABEL[v.mode] || "mô phỏng"}</span></span></div>`).join("")}` : ""}
      </div>
      <div class="panel c12" id="urgent">${urgentPanel(ev)}</div>
    </div>`;
  wireUrgent(box, ctx, ev);
  const run = box.querySelector("#run");
  if (run) run.onclick = async () => {
    run.disabled = true; run.textContent = "Agent đang chạy…";
    try {
      const r = await post("/api/events/run-agent", {event_id: ev.id, by: ctx.user});
      follow(box, ctx, ev.id, r.job.id);
    } catch (e) { toast(e.message); run.disabled = false; run.textContent = "Chạy Agent CIO"; }
  };
  if (busy) follow(box, ctx, ev.id, job.id);
}

// Urgent (BRD-KPI-01, news/urgent.py): the CIO's flag, with a reason; what the product proposes. Our reading,
// labelled “Đề xuất” until the bank defines urgent news.
function urgentBadge(e) {
  if (e.urgent && e.urgent.flag) return ' · <span class="badge bad">khẩn</span>';
  return (e.urgent_proposed || []).length ? ' · <span class="badge warn">đề xuất khẩn</span>' : "";
}

function urgentPanel(ev) {
  const u = ev.urgent, props = ev.urgent_proposed || [];
  return `<h3>Tin khẩn <span class="hint">BRD-KPI-01 · Đề xuất</span></h3>
    <p class="small muted">Sự kiện CIO đánh dấu khẩn được đo theo mục tiêu ≤ 30 phút, từ tin sớm nhất đến lúc lần áp dụng có hiệu lực cho RM. Hệ thống đề xuất khẩn khi NHNN quyết định lãi suất điều hành hoặc biên độ tỷ giá, hoặc khi một yếu tố biến động quá 3 lần độ lệch chuẩn trong ngày — cách hiểu của chúng tôi cho tới khi ngân hàng định nghĩa.</p>
    ${props.length ? `<div class="small" style="margin:8px 0"><b>Hệ thống đề xuất khẩn:</b><ul>${props.map(x => `<li data-explains>${esc(x.reason)}</li>`).join("")}</ul></div>` : `<div class="small muted" style="margin:8px 0">Hệ thống không đề xuất khẩn cho sự kiện này.</div>`}
    ${u && u.flag
      ? `<div class="notice bad"><b>Đã đánh dấu khẩn</b> · ${esc(u.by)} · ${when(u.at)}<div data-quote>${esc(u.reason)}</div></div>
         <div class="row" style="margin-top:8px"><button type="button" class="btn" id="unflag">Bỏ đánh dấu khẩn</button></div>`
      : `<label class="small" for="urgent-reason">Lý do</label>
         <div class="row" style="margin-top:4px"><input id="urgent-reason" style="flex:1;min-width:0" maxlength="300" value="${esc(props.map(x => x.reason).join("; "))}">
         <button type="button" class="btn" id="flag">Đánh dấu khẩn</button></div>`}`;
}

function wireUrgent(box, ctx, ev) {
  const send = async (urgent, reason) => {
    try {
      const r = await post("/api/events/urgent", {event_id: ev.id, urgent, reason, by: ctx.user});
      box.querySelector("#urgent").innerHTML = urgentPanel(r.event);
      wireUrgent(box, ctx, r.event);
      toast(urgent ? "Đã đánh dấu khẩn" : "Đã bỏ đánh dấu khẩn");
    } catch (e) { toast(e.message); }
  };
  const flag = box.querySelector("#flag"), unflag = box.querySelector("#unflag");
  if (flag) flag.onclick = () => send(true, box.querySelector("#urgent-reason").value);
  if (unflag) unflag.onclick = () => send(false, "");
}

const MODE_LABEL = {live: "AI", inbox: "vùng AI", mock: "mô phỏng"};
const JOB = {queued: "Đang chờ trong hàng đợi", running: "Agent đang chạy", done: "Xong", failed: "Lỗi"};

function jobLine(j) {
  const tone = {done: "good", failed: "bad"}[j.status] || "warn";
  return `<span class="badge ${tone}">${JOB[j.status]}</span> ${esc(j.id)} · ${MODE_LABEL[j.mode] || "mô phỏng"} · ${when(j.created)}${j.error ? `<div class="bad-text">${esc(j.error)}</div>` : ""}`;
}

// The run is queued (AI-13): follow the job until the worker is done, then open the view it wrote.
async function follow(box, ctx, eventId, jobId) {
  const here = location.hash;
  for (let i = 0; i < 900 && location.hash === here; i++) {
    const {jobs} = await get(`/api/events/${encodeURIComponent(eventId)}`);
    const j = jobs.find(x => x.id === jobId);
    const line = box.querySelector("#job");
    if (line && j) line.innerHTML = jobLine(j);
    if (j && j.status === "done" && j.view_id) return ctx.go(ctx.href("nhan-dinh", j.view_id));
    if (j && j.status === "failed") { toast("Agent không chạy xong: " + (j.error || "")); return renderEvent(box, ctx, eventId); }
    await new Promise(r => setTimeout(r, 2000));
  }
}

function stepper(status) {
  const order = STEPS.map(s => s[0]);
  const at = order.indexOf(status);
  const failed = ["AGENT_ERROR", "REJECTED", "WITHDRAWN"].includes(status);
  return `<div class="stepper" aria-label="Vòng đời nhận định">${STEPS.map(([k, label], i) => {
    const cls = failed && i === Math.max(0, at) ? "fail" : at > i || status === "APPROVED" ? "done" : at === i ? "now" : "";
    return `<span class="st ${cls}"><span class="dot"></span>${label}</span>`;
  }).join("")}${failed || ["REWORK_REQUESTED", "SUPERSEDED"].includes(status) ? `<span class="st now">${viewBadge(status)}</span>` : ""}</div>`;
}

const LEVEL_COLOR = (l) => l === 0 ? "var(--surface-2)" : `color-mix(in srgb, ${l < 0 ? "var(--down)" : "var(--up)"} ${20 + Math.abs(l) * 22}%, transparent)`;

async function renderView(box, ctx, id) {
  const [d, model] = await Promise.all([get(`/api/views/${encodeURIComponent(id)}`), get("/api/model")]);
  const v = d.view, cur = v.current;
  const names = Object.fromEntries(model.factors.map(f => [f.id, f]));
  const ch = d.challenges[d.challenges.length - 1];
  const answered = ch ? ((v.responses || {})[ch.id] || {}) : {};
  const editable = ["PENDING_CHALLENGE", "PENDING_APPROVAL"].includes(v.status);
  const allOk = d.checks.length && d.checks.every(c => c.ok);
  // once decided, “Đang chờ duyệt” is not a failed condition: the view is past it (R7: it showed a red ✕ on APPROVED)
  const decided = !["DRAFTING", "PENDING_CHALLENGE", "PENDING_APPROVAL", "AGENT_ERROR"].includes(v.status);
  const checks = decided ? d.checks.filter(c => c.code !== "a") : d.checks;

  box.innerHTML = `
    <div class="pagehead"><div><a class="small" href="${ctx.href("nhan-dinh", v.event_id)}">← ${esc(v.event_id)}</a>
      <div class="eyebrow" style="margin-top:6px">Nhận định ${esc(v.id)} · ${v.mode === "live" ? `AI: ${esc(v.models.cio)}` : v.mode === "inbox" ? `Từ vùng AI qua hộp chờ có chữ ký · ${v.models.cio === "mock" ? "vùng AI chạy mô phỏng" : `AI: ${esc(v.models.cio)}`}` : "Mô phỏng, không gọi AI"}</div>
      <div style="margin-top:8px">${stepper(v.status)}</div></div>
      <div>${viewBadge(v.status)}</div></div>
    ${v.status === "AGENT_ERROR" ? `<div class="notice bad" style="margin-bottom:16px"><b>Agent lỗi:</b> ${esc((v.error || []).join("; "))}. Chạy lại ở trang sự kiện để tạo phiên bản mới.</div>` : ""}
    ${v.challenge_error ? `<div class="notice warn" style="margin-bottom:16px"><b>Agent Phản biện lỗi:</b> ${esc(v.challenge_error)} <button type="button" class="btn sm" id="rechallenge">Chạy lại phản biện</button></div>` : ""}
    ${cur ? `
    <div class="cols">
      <div class="panel c7"><h3>Nhận định <span class="badge ai">${v.mode === "live" ? "AI soạn" : v.mode === "inbox" ? "vùng AI soạn" : "mô phỏng"}</span></h3>
        <div style="font-size:15px" data-quote>${esc(cur.summary)}</div>
        <div class="small muted" style="margin-top:8px">Đã vào giá: <b>${{none: "chưa", partial: "một phần", full: "đã hết"}[cur.scenarios.priced_in]}</b> · nội dung ${esc(v.content_hash.slice(0, 10))}</div></div>
      <div class="panel c5"><h3>Điều kiện duyệt${decided ? ` <span class="hint">đã quyết: ${esc(viewLabel(v.status))}</span>` : ""}</h3>
        <div class="list">${checks.map(c => `<div class="check"><span class="${c.ok ? "up" : "down"}" aria-hidden="true">${c.ok ? "✓" : "✕"}</span><div><div>${esc(c.label)}</div>${c.ok ? "" : `<div class="small muted">${esc(c.detail)}</div>`}</div></div>`).join("")}</div>
        ${v.status === "PENDING_APPROVAL" || v.status === "PENDING_CHALLENGE" ? `
        <label class="field" style="margin-top:12px">Lý do (bắt buộc)<textarea id="reason" placeholder="Ví dụ: Đồng ý kịch bản; nhánh căng thẳng giữ để đo rủi ro"></textarea></label>
        <div class="row" style="margin-top:10px"><button type="button" class="btn primary" data-act="approve" ${allOk ? "" : "disabled"}>Duyệt và áp dụng</button>
          <button type="button" class="btn" data-act="return">Trả lại agent</button><button type="button" class="btn danger" data-act="reject">Bác</button></div>` : ""}
        ${v.status === "APPROVED" ? `<label class="field" style="margin-top:12px">Lý do thu hồi<textarea id="reason"></textarea></label>
          <div class="row" style="margin-top:10px"><button type="button" class="btn danger" data-act="withdraw">Thu hồi nhận định</button></div>` : ""}
      </div>
      <div class="panel c12" id="scen"><h3>Kịch bản <span class="hint">CIO chọn cú sốc lõi và cỡ; máy suy ra phần còn lại</span>
        ${editable ? '<button type="button" class="btn sm" id="toggle-edit" style="margin-left:auto">Sửa kịch bản</button>' : ""}</h3>
        <div id="prob"></div>
        <div class="cols" style="margin-top:12px">${cur.scenarios.branches.map((b, i) => `
          <div class="c4 panel flat" style="border-top:3px solid ${slot(i)}">
            <div class="row spread"><b>${esc(b.name)}</b><span class="num">${how(pct(b.probability, false, 0), "scenario.probability", {event: v.event_id})}</span></div>
            <div class="small muted">${b.regime === "stressed" ? "Chế độ căng thẳng" : "Chế độ bình thường"}</div>
            <div class="row" style="margin:8px 0;gap:6px">${b.core_shocks.map(s => `<span class="chip">${esc(names[s.factor] ? names[s.factor].name : s.factor)} ${s.direction === "up" ? "▲" : "▼"} ${SIZE[s.size]}</span>`).join("")}</div>
            <details class="more"><summary>Lan truyền ra thị trường</summary><div data-moves="${i}"></div><div class="small muted" style="margin-top:4px">Độ dài thanh: so với biến động 1 tháng thường thấy.</div></details>
            <details class="more"><summary>Lập luận</summary><div class="small" data-quote>${esc(b.rationale)}</div></details>
            ${editable ? `<div class="editing-only"><div class="row" style="margin-top:8px;gap:6px"><label class="field">Xác suất<input type="number" min="5" max="95" step="5" data-prob="${i}" value="${Math.round(b.probability * 100)}" style="width:72px"></label>
              <label class="field">Chế độ<select data-regime="${i}"><option value="normal" ${b.regime === "normal" ? "selected" : ""}>bình thường</option><option value="stressed" ${b.regime === "stressed" ? "selected" : ""}>căng thẳng</option></select></label></div>
              ${b.core_shocks.map((s, j) => `<label class="field" style="margin-top:6px">${esc(names[s.factor] ? names[s.factor].name : s.factor)}<span class="row" style="gap:6px"><select data-dir="${i}-${j}"><option value="up" ${s.direction === "up" ? "selected" : ""}>tăng</option><option value="down" ${s.direction === "down" ? "selected" : ""}>giảm</option></select><select data-size="${i}-${j}">${["S", "M", "L"].map(z => `<option value="${z}" ${s.size === z ? "selected" : ""}>${SIZE[z]} (${z})</option>`).join("")}</select><button type="button" class="linkbtn small" data-drop="${i}-${j}">bỏ</button></span></label>`).join("")}</div>` : ""}
          </div>`).join("")}</div>
        ${editable ? `<div class="row editing-only" style="margin-top:12px"><input id="edit-reason" placeholder="Lý do sửa (bắt buộc)" style="flex:1;min-width:200px;padding:7px 10px;border:1px solid var(--axis);border-radius:9px;background:var(--surface);color:var(--ink)"><button type="button" class="btn" id="save-edit">Lưu bản sửa → phản biện lại</button></div>` : ""}
      </div>
      <div class="panel c6"><h3>Dòng tác động <span class="hint">−3 đến +3 · ${HORIZON["3m"]} trừ khi ghi khác</span></h3>
        <table class="table"><tbody>${cur.impacts.map(r => `<tr><td>${esc(target(r))}<div class="small muted">${esc(TARGET_TYPE[r.target_type] || r.target_type)} · ${esc(HORIZON[r.horizon] || r.horizon)} · tin cậy ${esc({low: "thấp", medium: "vừa", high: "cao"}[r.confidence] || r.confidence)}</div></td>
          <td class="r"><span class="chip num" style="background:${LEVEL_COLOR(r.level)};border-color:transparent;font-weight:700">${r.level > 0 ? "+" : ""}${r.level}</span></td></tr>`).join("")}</tbody></table>
        ${(v.restricted_rows || []).length ? `<div class="small muted">${v.restricted_rows.length} dòng bị loại vì mã trong danh sách hạn chế.</div>` : ""}</div>
      <div class="panel c6"><h3>Phản biện độc lập <span class="hint">${ch ? `${esc(ch.model)} · ${ch.findings.length} phát hiện` : "chưa có"}</span></h3>
        ${ch ? ch.findings.map(f => `<div style="padding:8px 0;border-bottom:1px solid var(--hair)">
          <div class="row spread"><span>${severity(f.severity)} <b>${esc(f.title)}</b></span><span class="badge ${f.source === "model" ? "ai" : ""}">${f.source === "model" ? "AI" : "quy tắc"}</span></div>
          <div class="small" style="margin-top:4px" data-explains>${esc(f.detail)}</div>
          ${answered[f.id] ? `<div class="small" style="margin-top:4px"><span class="badge human">CIO ${answered[f.id].decision === "accept" ? "chấp nhận" : "bác"}</span> ${esc(answered[f.id].reason)}</div>` :
            v.status === "PENDING_APPROVAL" ? `<div class="row" style="margin-top:6px;gap:6px"><input data-resp="${esc(f.id)}" placeholder="Trả lời (từ 10 ký tự)" style="flex:1;min-width:160px;padding:6px 9px;border:1px solid var(--axis);border-radius:9px;background:var(--surface);color:var(--ink)">
              <button type="button" class="btn sm" data-answer="${esc(f.id)}" data-decision="accept">Chấp nhận</button><button type="button" class="btn sm" data-answer="${esc(f.id)}" data-decision="reject">Bác</button></div>` : ""}
        </div>`).join("") || '<div class="small muted">Không có phát hiện.</div>' : ""}</div>
      ${d.application_runs.length ? `<div class="panel c12"><h3>Lần áp dụng</h3>${d.application_runs.map(r => `<div class="row spread" style="margin:6px 0"><a href="#/cio/ap-dung/${esc(r.id)}">${esc(r.id)}</a><span>${runBadge(r.status, r.status_label)} <span class="num ${signClass(r.totals && r.totals.expected_3m)}">${r.totals ? how(vnd(r.totals.expected_3m, true), "run.expected_3m", {families: String(r.families || "")}) : ""}</span> ${r.totals ? `· ${r.totals.pre_review} gia đình cần RM xem trước` : ""}</span></div>`).join("")}</div>` : ""}
    </div>` : ""}
    <div class="panel flat" style="margin-top:16px"><details class="more"><summary>Vết chạy agent (từng bước)</summary>
      ${d.runs.map(r => `<div style="margin-top:8px"><b>${esc(r.id)}</b> · ${esc(r.agent)} · ${esc(r.mode)} · ${esc(r.status)}${r.error ? ` · <span class="down">${esc(r.error)}</span>` : ""}
        <div class="scrollx"><table class="table"><thead><tr><th>#</th><th>Bước</th><th>Mô hình</th><th class="r">ms</th><th class="r">token vào/ra</th><th>Lỗi</th></tr></thead><tbody>${r.nodes.map(n => `<tr><td>${n.seq}</td><td>${esc(n.node)}${n.attempt > 1 ? ` (lần ${n.attempt})` : ""}</td><td class="small">${esc(n.model)}</td><td class="r">${n.ms}</td><td class="r">${n.tokens_in == null ? "—" : `${n.tokens_in}/${n.tokens_out}`}</td><td class="small down">${esc(n.error || "")}</td></tr>`).join("")}</tbody></table></div></div>`).join("")}
    </details></div>`;

  if (cur) {
    probBar(box.querySelector("#prob"), cur.scenarios.branches);
    const prev = Object.fromEntries((d.preview || []).map(p => [p.id, p]));
    cur.scenarios.branches.forEach((b, i) => {
      const pv = prev[b.id];
      const node = box.querySelector(`[data-moves="${i}"]`);
      if (!pv || !node) return;
      moves(node, pv.moves.slice(0, 7).map(m => ({
        name: m.name, core: m.core, z: m.move / (names[m.factor] ? names[m.factor].vol_month : 1),
        text: `${m.move > 0 ? "+" : ""}${m.unit === "bp" ? Math.round(m.move) : m.move.toFixed(2)}${UNIT[m.unit]}`,
      })), {metric: "scenario.move", inputs: {branch: b.name}});
    });
  }
  const act = async (body, msg) => {
    try { await post("/api/views/decide", {view_id: v.id, by: ctx.user, ...body}); toast(msg); } catch (e) { toast(e.message); }
    ctx.go(location.hash);
  };
  box.querySelectorAll("[data-act]").forEach(b => {
    b.onclick = async () => {
      const reason = (box.querySelector("#reason") || {value: ""}).value.trim();
      b.disabled = true;
      const msg = {approve: "Đã duyệt; máy đã tính cho mọi gia đình", return: "Đã trả lại agent", reject: "Đã bác", withdraw: "Đã thu hồi"}[b.dataset.act];
      await act({action: b.dataset.act, reason, idem_key: `${b.dataset.act}:${v.id}:${v.content_hash.slice(0, 12)}`}, msg);
    };
  });
  box.querySelectorAll("[data-answer]").forEach(b => {
    b.onclick = () => {
      const input = box.querySelector(`[data-resp="${CSS.escape(b.dataset.answer)}"]`);
      act({action: "respond", responses: {[b.dataset.answer]: {decision: b.dataset.decision, reason: input.value.trim()}}}, "Đã ghi câu trả lời");
    };
  });
  const re = box.querySelector("#rechallenge");
  if (re) re.onclick = () => act({action: "challenge"}, "Đã chạy lại phản biện");
  const tog = box.querySelector("#toggle-edit");
  if (tog) tog.onclick = () => {
    const on = box.querySelector("#scen").classList.toggle("editing");
    tog.textContent = on ? "Đóng sửa" : "Sửa kịch bản";
  };
  const save = box.querySelector("#save-edit");
  if (save) {
    const branches = JSON.parse(JSON.stringify(cur.scenarios.branches));
    box.querySelectorAll("[data-drop]").forEach(b => {
      b.onclick = () => {
        const [i, j] = b.dataset.drop.split("-").map(Number);
        branches[i].core_shocks[j] = null;
        b.closest("label").style.opacity = .35;
      };
    });
    save.onclick = () => {
      branches.forEach((b, i) => {
        b.probability = Number(box.querySelector(`[data-prob="${i}"]`).value) / 100;
        b.regime = box.querySelector(`[data-regime="${i}"]`).value;
        b.core_shocks = b.core_shocks.map((s, j) => s && {...s, direction: box.querySelector(`[data-dir="${i}-${j}"]`).value,
          size: box.querySelector(`[data-size="${i}-${j}"]`).value}).filter(Boolean);
      });
      act({action: "edit", reason: box.querySelector("#edit-reason").value.trim(),
        edits: {scenarios: {...cur.scenarios, branches}}}, "Đã lưu bản sửa; phản biện chạy lại");
    };
  }
}
