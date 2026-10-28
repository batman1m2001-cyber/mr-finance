/* Tác động tin: what the approved news does to this family — one hero number, the band over time,
   where it comes from, and each event with its status. Client: asset classes only, with the labels
   flow 2 requires. RM: also factors, holdings, the pre-review flag and "cách tính". */
import {LOCALE, ASSET_CLASS, HORIZON, drawer, empty, esc, get, n as how, pct, post, runBadge, signClass, toast, vnd, when, $} from "../core/core.js";
import {diverging, fan} from "../charts/charts.js";
import {names, openTrace} from "./trace.js";

const LEVEL = {contact_now: "bad", confirm_goal: "human", remind: "warn", note: ""};
const FUND = {"Đạt": "good", "Theo dõi": "warn", "Thiếu": "bad"};  // FR-404 levels

export async function render(box, ctx) {
  const client = ctx.client();
  const staff = ctx.role !== "client";
  const [d, goals] = await Promise.all([
    get(`/api/families/${encodeURIComponent(client)}/impact?role=${staff ? "rm" : "client"}`),
    get(`/api/goals/regulation?family_id=${encodeURIComponent(client)}${staff ? "" : "&role=client"}`),
  ]);
  const goalBlock = goalsPanel(goals, staff);
  const items = d.items;
  const effective = items.filter(i => i.status === "EFFECTIVE");
  if (!items.length) {
    box.innerHTML = `<div class="cols"><div class="panel c12">${empty("Chưa có tin nào được CIO duyệt áp dụng cho gia đình này",
      staff ? "Khi CIO duyệt một nhận định, kết quả của mọi gia đình hiện ở đây sau hậu kiểm." : "Khi có tin đáng chú ý đã được kiểm duyệt, tác động lên tài sản của bạn sẽ hiện ở đây.")}</div>${goalBlock}</div>`;
    wireGoals(box, ctx, client);
    return;
  }
  const nw = items[0].net_worth;
  const total = d.effective_expected_3m;
  const classes = {};
  for (const i of effective) for (const [k, v] of Object.entries(i.by_class)) classes[k] = (classes[k] || 0) + v;
  const topClass = Object.entries(classes).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))[0];
  let sel = [...effective].sort((a, b) => Math.abs(b.horizons["3m"].expected) - Math.abs(a.horizons["3m"].expected))[0] || items[0];
  const flagged = staff && effective.some(i => i.pre_review);

  box.innerHTML = `
    <div class="cols">
      <div class="panel hero-panel c5">
        <div class="eyebrow">Tác động tin · 3 tháng tới</div>
        <div class="hero ${signClass(total)}" style="margin-top:10px">${how(vnd(total, true), "impact.expected_3m", {event: `${effective.length} sự kiện đang hiệu lực`})}</div>
        <div class="takeaway">${effective.length ? `${effective.length} sự kiện đang có hiệu lực${topClass ? `; chủ yếu qua <b>${esc(ASSET_CLASS[topClass[0]] || topClass[0])}</b> (${how(vnd(topClass[1], true), "impact.by_class", {part: ASSET_CLASS[topClass[0]] || topClass[0]})})` : ""}.` : "Chưa có sự kiện nào đang hiệu lực."}</div>
        <div class="row" style="margin-top:12px">
          <span class="chip">${how(pct(nw ? total / nw : 0, true, 2), "impact.expected_3m", {event: `${effective.length} sự kiện đang hiệu lực`})} tài sản ròng</span>
          ${flagged ? '<span class="badge bad" data-explains>RM xem trước: P10 3 tháng ≤ −5%</span>' : ""}
          <span class="badge ai">AI hỗ trợ · CIO duyệt</span>
        </div>
        <div class="footnote">Kỳ vọng = trung bình theo xác suất các kịch bản CIO duyệt. Giá ngày ${esc(sel.price_date || "—")} · ${sel.model && sel.model.assumed === false ? `mô hình ${esc(sel.model.version)} ước lượng từ dữ liệu thị trường` : "tham số mô hình là giả định"}${d.labels ? ` · ${esc(d.labels.responsible)}` : ""}.</div>
      </div>
      <div class="panel c7">
        <h3>Dải kết quả có thể <span class="hint" id="fan-of"></span></h3>
        <div id="fan"></div>
      </div>
      <div class="panel c5">
        <h3>Đến từ đâu <span class="hint">theo nhóm tài sản, 3 tháng</span></h3>
        <div id="by-class"></div>
      </div>
      <div class="panel c7">
        <h3>Sự kiện <span class="hint">mới nhất trước</span></h3>
        <div class="list" id="events"></div>
      </div>
      <div class="panel c12"><h3>Dòng thời gian <span class="hint">mỗi sự kiện từ tin đầu tiên tới khi có hiệu lực · giờ Việt Nam</span></h3>
        <div class="tline" id="timeline"></div></div>
      <div class="panel c12" id="goal-impact" hidden></div>
      ${staff ? `<div class="panel c12"><details class="more"><summary>Chi tiết cho RM: theo yếu tố và theo vị thế</summary>
        <div class="cols" style="margin-top:8px"><div class="c6"><div class="small muted">Theo yếu tố (3 tháng)</div><div id="by-factor"></div></div>
        <div class="c6"><div class="small muted">Vị thế góp phần nhiều nhất</div><div id="by-holding"></div></div></div></details></div>` : ""}
      ${goalBlock}
      ${d.labels ? `<div class="c12 notice small">${esc(d.labels.note)}<div style="margin-top:4px">${d.labels.conflicts.map(esc).join("<br>")}</div></div>` : ""}
    </div>`;
  wireGoals(box, ctx, client);

  const drawFan = (it) => {
    sel = it;
    $("#fan-of", box).textContent = `sự kiện “${it.event.title}” · bấm “Xem dải” để đổi`;
    fan($("#fan", box), ["1w", "3m", "12m"].map(h => ({label: HORIZON[h], ...it.horizons[h]})),
      {label: `Dải tác động của ${it.event.title}`});
    for (const b of box.querySelectorAll("[data-run]")) b.setAttribute("aria-pressed", String(b.dataset.run === it.run_id));
    for (const r of box.querySelectorAll("[data-tl]")) r.classList.toggle("on", r.dataset.tl === it.run_id);
    drawGoals($("#goal-impact", box), it);
  };
  // a gain or a loss, as its figure is written (a class colour read as a loss on the orange of Cổ phiếu)
  diverging($("#by-class", box), Object.entries(classes).map(([k, v]) => ({label: ASSET_CLASS[k] || k, value: v})),
    {label: "Đóng góp theo nhóm tài sản"});
  $("#events", box).innerHTML = items.map(i => {
    const e = i.horizons["3m"].expected;
    return `<div class="item" data-focus="event:${esc(i.event.id)}">
      <span class="badge ${i.status === "EFFECTIVE" ? "ai" : ""}" aria-hidden="true">${esc(i.event.id.slice(-4))}</span>
      <div><div class="t">${esc(i.event.title)}</div>
        <div class="m">${runBadge(i.status, i.status_label)} · duyệt ${when(i.approved_at)} ${staff && i.pre_review ? '· <span class="badge bad">xem trước</span>' : ""}</div>
        ${i.sources ? `<div class="small muted">Nguồn: ${esc(i.sources.outlets.join(", "))} (${i.sources.count} tin)</div>` : ""}
        <div class="row" style="margin-top:6px"><button type="button" class="btn sm" data-run="${esc(i.run_id)}" aria-pressed="false">Xem dải</button>
        ${staff ? `<button type="button" class="linkbtn small" data-trace="${esc(i.run_id)}">Cách tính</button>`
          : i.status === "EFFECTIVE" ? `<button type="button" class="linkbtn small" data-how="${esc(i.run_id)}">Cách tính</button>` : ""}</div></div>
      <div style="text-align:right"><div class="num ${signClass(e)}" style="font-weight:700">${how(vnd(e, true), "impact.expected_3m", {event: i.event.title})}</div><div class="small muted">${how(pct(i.pct["3m"].expected, true, 2), "impact.expected_3m", {event: i.event.title})}</div></div></div>`;
  }).join("");
  // the timeline: one row per event, its steps in order with their times, read from the stored records
  const at = (t) => {  // dd/mm hh:mm in Vietnam time
    const d = new Date((t + 7 * 3600) * 1000), z = (x) => String(x).padStart(2, "0");
    return `${z(d.getUTCDate())}/${z(d.getUTCMonth() + 1)} ${z(d.getUTCHours())}:${z(d.getUTCMinutes())}`;
  };
  $("#timeline", box).innerHTML = [...items].sort((a, b) => (b.timeline[0] || {}).at - (a.timeline[0] || {}).at).map(i => `
    <div class="trow" data-focus="event:${esc(i.event.id)}" data-tl="${esc(i.run_id)}">
      <div class="tlabel"><b>${esc(i.event.title)}</b><span class="small muted">${runBadge(i.status, i.status_label)}</span></div>
      <ol class="tsteps">${(i.timeline || []).map(x => `<li class="tstep ${esc(x.step)}"><i aria-hidden="true"></i><span>${esc(x.label)}</span><time class="small muted num" datetime="${new Date(x.at * 1000).toISOString()}">${at(x.at)}</time></li>`).join("")}</ol>
    </div>`).join("");
  box.querySelectorAll("[data-run]").forEach(b => { b.onclick = () => drawFan(items.find(i => i.run_id === b.dataset.run)); });
  box.querySelectorAll("[data-trace]").forEach(b => { b.onclick = () => openTrace(b.dataset.trace, client); });
  box.querySelectorAll("[data-how]").forEach(b => { b.onclick = () => openHow(b.dataset.how, client); });
  drawFan(sel);

  if (staff) {
    const nm = await names();
    const factors = {};
    for (const i of effective) for (const [k, v] of Object.entries(i.by_factor || {})) factors[k] = (factors[k] || 0) + v;
    diverging($("#by-factor", box), Object.entries(factors).map(([k, v]) => ({label: nm[k] || k, value: v})), {label: "Theo yếu tố", metric: "impact.by_factor"});
    const hold = {};
    for (const i of effective) for (const h of i.holdings || []) {
      if (!h.contribution) continue;
      const o = hold[h.key] || (hold[h.key] = {name: h.name, v: 0, modelled: h.modelled, method: h.method});
      o.v += h.contribution;
    }
    const rows = Object.entries(hold).sort((a, b) => Math.abs(b[1].v) - Math.abs(a[1].v)).slice(0, 8);
    $("#by-holding", box).innerHTML = rows.length ? `<table class="table"><tbody>${rows.map(([k, h]) =>
      `<tr class="click" data-key="${esc(k)}" title="${esc(h.method)}"><td>${esc(h.name)}${h.modelled ? ' <span class="badge assumed">mô hình</span>' : ""}</td><td class="r ${signClass(h.v)}">${how(vnd(h.v, true), "impact.holding")}</td></tr>`).join("")}</tbody></table>` : `<div class="small muted">—</div>`;
    box.querySelectorAll("[data-key]").forEach(r => { r.onclick = () => openTrace(sel.run_id, client, r.dataset.key); });
  }
}

function goalsPanel(g, staff) {
  const rows = g.matches || [];
  if (!staff) {
    if (!rows.length) return "";
    return `<div class="panel c12"><h3>Lưu ý cho mục tiêu của bạn <span class="hint">quy định mới về chuyển tiền ra nước ngoài</span></h3>
      ${rows.map(m => `<div style="padding:8px 0;border-bottom:1px solid var(--hair)"><b>${esc(m.goal)}</b> <span class="badge ${LEVEL[m.level]}">${esc(m.level_label)}</span>
        <div class="small" data-explains>${esc(m.client_message)}</div><div class="small muted">Nên chuẩn bị trước ${esc(m.milestone)}${m.documents.length ? ` · hồ sơ: ${m.documents.map(esc).join(", ")}` : ""}</div></div>`).join("")}</div>`;
  }
  const goalsList = g.goals || [];
  if (!goalsList.length && !rows.length) return "";
  const opts = Object.entries(g.purposes || {}).map(([k, v]) => `<option value="${k}">${esc(v)}</option>`).join("");
  return `<div class="panel c12"><h3>Mục tiêu và quy định <span class="hint">nhánh mục tiêu: mốc thời gian và hồ sơ, không phải tiền</span></h3>
    ${rows.length ? rows.map(m => `<div style="padding:6px 0"><span class="badge ${LEVEL[m.level]}">${esc(m.level_label)}</span> <b>${esc(m.goal)}</b> · ${esc(m.note_title)} · mốc <span class="num">${esc(m.milestone)}</span><div class="small muted" data-explains>${esc(m.rm_hint || "")}</div></div>`).join("") : '<div class="small muted">Chưa có ghi chú quy định nào khớp mục tiêu của gia đình này.</div>'}
    <details class="more" style="margin-top:8px"><summary>Khai dòng tiền ra nước ngoài cho mục tiêu (RM)</summary>
      ${goalsList.some(x => !x.declared) ? `<div class="row" style="margin:6px 0;gap:8px;align-items:center"><button type="button" class="btn sm" data-suggest>Gợi ý bằng AI</button>
        <span class="small muted">AI đọc tên mục tiêu chưa khai và điền sẵn; bấm Lưu để xác nhận.</span></div>` : ""}
      ${goalsList.map(x => `<div class="row" style="margin:6px 0"><span style="min-width:220px"><b>${esc(x.label)}</b><div class="small muted">${esc(x.date)}${x.declared ? ` · đã khai: ${esc((g.purposes || {})[x.declared.purpose] || x.declared.purpose)} ${esc(x.declared.country || "")}` : " · chưa khai"}</div></span>
        <select data-purpose="${esc(x.goal_id)}">${opts}</select><input data-country="${esc(x.goal_id)}" placeholder="Nước đến" style="width:110px;padding:6px 9px;border:1px solid var(--axis);border-radius:9px;background:var(--surface);color:var(--ink)">
        <button type="button" class="btn sm" data-declare="${esc(x.goal_id)}">Lưu</button><span class="small muted" data-hint="${esc(x.goal_id)}"></span></div>`).join("")}</details></div>`;
}

function wireGoals(box, ctx, client) {
  const ask = box.querySelector("[data-suggest]");
  if (ask) ask.onclick = async () => {
    ask.disabled = true;
    try {
      const r = await post("/api/goals/suggest", {family_id: client, by: ctx.user});
      Object.entries(r.suggestions).forEach(([id, s]) => {
        const hint = box.querySelector(`[data-hint="${CSS.escape(id)}"]`);
        if (s.purpose) {
          box.querySelector(`[data-purpose="${CSS.escape(id)}"]`).value = s.purpose;
          box.querySelector(`[data-country="${CSS.escape(id)}"]`).value = s.country;
        }
        if (hint) hint.innerHTML = `<span class="badge assumed">${s.purpose ? "gợi ý AI" : "AI: không chuyển ra nước ngoài"}</span> <span data-explains>${esc(s.why)}</span>`;
      });
      toast(Object.keys(r.suggestions).length ? "Đã điền gợi ý; kiểm tra rồi bấm Lưu" : "Không có mục tiêu nào cần gợi ý");
    } catch (e) { toast(e.message); }
    ask.disabled = false;
  };
  box.querySelectorAll("[data-declare]").forEach(b => {
    b.onclick = async () => {
      const id = b.dataset.declare;
      try {
        await post("/api/goals/outflow", {family_id: client, goal_id: id, by: ctx.user,
          purpose: box.querySelector(`[data-purpose="${CSS.escape(id)}"]`).value,
          country: box.querySelector(`[data-country="${CSS.escape(id)}"]`).value.trim()});
        toast("Đã lưu khai báo");
      } catch (e) { toast(e.message); }
      ctx.go(location.hash);
    };
  });
}

// FR-404: the selected event's effect on each dated goal — funding before and after, with its level
function drawGoals(el, it) {
  const g = it.goal_impact;
  el.hidden = !(g && g.goals.length);
  if (el.hidden) return;
  const fe = {event: it.event.title};
  const lvl = (x) => `<span class="num">${how(pct(x.ratio, false, 0), "goal.funding", fe)}</span> <span class="badge ${FUND[x.level] || ""}">${esc(x.level)}</span>`;
  el.innerHTML = `<h3>Mục tiêu <span class="hint">“${esc(it.event.title)}” · 3 tháng · mức đáp ứng trước → sau</span></h3>
    <table class="table"><thead><tr><th>Mục tiêu</th><th>Trước</th><th>Sau</th>${g.pool.bands ? "<th>Tác động 3 tháng (VND)</th>" : ""}</tr></thead><tbody>
    ${g.goals.map(x => `<tr><td>${esc(x.label)}${x.changed ? ' <span class="badge warn">đổi mức</span>' : ""}
      <div class="small muted num">hạn ${esc(x.date)} · cần ${how(vnd(x.amount), "goal.need")}</div></td><td>${lvl(x.before)}</td><td>${lvl(x.after)}</td>
      ${x.impact ? `<td class="num">${how(vnd(x.impact["3m"].expected, true), "goal.event_impact", {...fe, stat: "Kỳ vọng"})}<div class="small muted">P10 ${how(vnd(x.impact["3m"].p10, true), "goal.event_impact", {...fe, stat: "P10"})} · P90 ${how(vnd(x.impact["3m"].p90, true), "goal.event_impact", {...fe, stat: "P90"})}</div></td>` : g.pool.bands ? "<td></td>" : ""}</tr>`).join("")}</tbody></table>
    <div class="footnote">Mục tiêu lấy nguồn theo thứ tự hạn từ tài sản tài chính (tiền, tiền gửi, quỹ, trái phiếu, cổ phiếu, vàng, tiền số): ${how(vnd(g.pool.before), "goal.pool", fe)} → ${how(vnd(g.pool.after), "goal.pool", fe)} (${how(vnd(g.pool.change, true), "goal.pool", fe)}). Mức: tiền cần để dành mỗi tháng ÷ thặng dư hằng tháng — ≤ 0,6 Đạt, ≤ 1 Theo dõi, cao hơn Thiếu. Đây là quy tắc của bản demo, không phải chính sách của ngân hàng.${g.pool.bands ? ` Tác động theo mục tiêu: tác động của cả nhóm tài sản đó (cùng bộ máy, mọi kỳ hạn, kỳ vọng và P5–P90) chia theo phần mỗi mục tiêu đang chiếm trước sự kiện; phần chưa gắn mục tiêu ${how(pct(g.unallocated.share, false, 0), "goal.event_impact", fe)} (${how(vnd(g.unallocated.impact["3m"].expected, true), "goal.event_impact", {...fe, stat: "Kỳ vọng"})}).` : ""}</div>`;
}

// F-D9 (Q-14, NFR-11): the client's “cách tính” — the formula, the scenarios with the market's moves and the family's
// change in each, and the family's own asset-class sums; no holding is named (GET /api/families/{id}/how)
async function openHow(runId, client) {
  const body = drawer("Cách tính", `<p class="small muted">Đang tải…</p>`);
  try {
    const d = await get(`/api/families/${encodeURIComponent(client)}/how?run=${encodeURIComponent(runId)}`);
    const UNIT = {pct: "%", bp: " điểm cơ bản", pp: " điểm %", sd: " độ lệch chuẩn"};
    const n = d.number, mv = (m) => `${m.move > 0 ? "+" : "−"}${Math.abs(m.move).toLocaleString(LOCALE, {maximumFractionDigits: m.unit === "bp" ? 0 : 1})}${UNIT[m.unit] || ""}`;
    body.setAttribute("data-explains", "");
    body.innerHTML = `
      <div class="eyebrow">${esc(d.event)} · giá ngày ${esc(d.run.price_date)} · CIO duyệt ${when(d.approved)}</div>
      <div class="num ${signClass(n.value)}" style="font-size:28px;font-weight:700;margin-top:6px">${vnd(n.value, true)}</div>
      <div class="small muted">${esc(n.label)} · ${pct(n.pct, true, 2)} tài sản ròng · P10 ${vnd(n.band.p10, true)} · P90 ${vnd(n.band.p90, true)}</div>
      <h3 style="margin-top:16px">Công thức</h3><p class="small">${esc(d.formula)}</p>
      <h3 style="margin-top:16px">Theo kịch bản</h3>
      ${d.branches.map(b => `<div class="panel" style="padding:10px 12px;margin:8px 0"><div class="row" style="justify-content:space-between"><b>${esc(b.name)}</b><span class="num">${pct(b.probability, false, 0)}</span></div>
        <div class="small muted">${b.moves.map(m => `${esc(m.factor)} ${mv(m)}`).join(" · ")}</div>
        <div class="small">Gia đình trong kịch bản này: <b class="num ${signClass(b.family_expected)}">${vnd(b.family_expected, true)}</b></div></div>`).join("")}
      <h3 style="margin-top:16px">Theo nhóm tài sản</h3>
      <table class="table"><thead><tr><th>Nhóm</th><th>Giá trị</th><th>Đóng góp</th></tr></thead><tbody>
        ${d.classes.map(c => `<tr><td>${esc(c.label)}</td><td class="num">${vnd(c.value)}</td><td class="num ${signClass(c.contribution)}">${vnd(c.contribution, true)}</td></tr>`).join("")}</tbody></table>
      <div class="footnote">Nguồn tin: ${d.sources.map(esc).join(", ")}. Phần tài sản có mô hình: ${pct(d.modelled_share, false, 0)}. Không phải khuyến nghị đầu tư; câu hỏi về tài sản cụ thể: liên hệ RM.</div>`;
  } catch (e) { body.innerHTML = `<p class="small down">${esc(e.message)}</p>`; }
}
