/* Kế hoạch — Wealth Planning Advisor (SCR-CL-03; UI redesign R3, was the pre-redesign “scenarios” tab). Life goals
   by stage of life (POST /api/goals), decisions and stress tests (GET /api/scenarios), one picked and simulated on
   the client's own holdings (POST /api/scenario): its status, the money needed against what is there, how it
   tracked this month and year, the actions ranked by how much they close the gap, the assumptions (edit and run
   again), before/after, and two options that can be sent to the RM (POST /api/review/propose). A wealth view on
   top sums the followed goals and the cash flow; after a decision or stress test it shows the picture after it.
   Regulation notes on the goals (FR-603) as the viewer may read them. Followed goals are kept in this browser. */
import {internal, $, esc, get, n as how, pct, post, vnd} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {progress} from "../charts/mini.js?v=20261016r2";
import {cashSeries, cashflow, monthsText} from "../charts/money.js?v=20261016r4";

const PARAMS = {
  per_year: ["Học phí mỗi năm", "tỷ"], years: ["Số năm", ""], start_year: ["Năm bắt đầu", ""], fx_rise: ["Tỷ giá tăng", "%"],
  retire_age: ["Tuổi nghỉ hưu", ""], spending_after: ["Chi tiêu mỗi tháng sau nghỉ hưu", "triệu"], price: ["Giá BĐS", "tỷ"],
  loan_ratio: ["Tỷ lệ vay", "%"], rate: ["Lãi suất vay", "%"], rent_monthly: ["Tiền thuê kỳ vọng mỗi tháng", "triệu"],
  share: ["Phần chuyển cho con", "%"], need: ["Số tiền cần", "tỷ"], cost: ["Chi phí điều trị", "tỷ"], cover: ["Bảo hiểm chi trả", "%"],
  usd: ["Số USD cần", "USD"], amount: ["Khoản rút ra", "tỷ"],
};
const UNIT = {"tỷ": 1e9, "triệu": 1e6, "%": 0.01, "": 1, "USD": 1};
const GOAL = {on_track: ["good", "Đúng tiến độ", "var(--good)"], at_risk: ["warn", "Cần chú ý", "var(--warning)"],
  off_track: ["bad", "Chậm tiến độ", "var(--critical)"], none: ["", "Chưa theo dõi", "var(--other)"]};
const RANK = {on_track: 0, at_risk: 1, off_track: 2};
const QUEUE = {pending: ["ai", "Chờ RM duyệt"], pending_specialist: ["warn", "Chờ chuyên gia có chứng chỉ duyệt"],
  approved: ["good", "Đã duyệt"], rejected: ["bad", "Từ chối"]};
const STAGE_ICON = {young: "user", family: "users", mid: "business", retire: "savings"};
const plans = {};  // per client, for this page's life: the pick, the last result, what was sent

const chip = (k) => `<span class="pill ${GOAL[k] ? GOAL[k][0] : ""}">${(GOAL[k] || GOAL.none)[1]}</span>`;
const gapIn = (g) => ({need: vnd(g.need), have: vnd(g.have)});
const gapLine = (g) => (g.gap > 0 ? `Thiếu ${vnd(g.gap)}` : g.gap < 0 ? `Dư ${vnd(-g.gap)}` : "Vừa đủ");
const gapHow = (g) => (g.gap ? how(gapLine(g), "goal.gap", gapIn(g)) : gapLine(g));

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope(), staff = ctx.role !== "client";
  const [{dashboard: d}, gout, reg, cat, q] = await Promise.all([
    post("/api/dashboard", {client_id: client, scope}),
    post("/api/goals", {client_id: client, scope}),
    get(`/api/goals/regulation?family_id=${encodeURIComponent(client)}${staff ? "" : "&role=client"}`).catch(() => ({matches: []})),
    get("/api/scenarios").catch(() => ({scenarios: []})),
    get("/api/review").catch(() => ({items: []})),
  ]);
  const goals = gout.goals, stages = gout.stages, catalog = cat.scenarios;
  let queue = q.items;
  const st = plans[`${client}|${scope}`] ||= {pick: null, result: null, sent: {}, busy: false};
  let set = null;
  try { set = JSON.parse(localStorage.getItem(`mf.goals.${client}`) || "null"); } catch (_) { /* private mode */ }
  const followed = (g) => (set ? set.includes(g.id) : g.followed);
  const mine = () => goals.filter(followed);
  const follow = (id, on) => {
    const now = new Set(set || goals.filter(g => g.followed).map(g => g.id));
    if (on) now.add(id); else now.delete(id);
    set = [...now];
    try { localStorage.setItem(`mf.goals.${client}`, JSON.stringify(set)); } catch (_) { /* private mode */ }
  };
  if (!st.pick || !goals.concat(catalog).some(x => x.id === st.pick)) {
    const top = mine().sort((a, b) => RANK[b.goal.status] - RANK[a.goal.status]);
    st.pick = (top[0] || goals[0] || {}).id || null;
    st.result = null;
  }

  box.innerHTML = `${staff ? internal() : ""}
    <div class="pagehead"><div><div class="eyebrow">Kế hoạch</div><h1 class="h1">Wealth Planning Advisor</h1>
      <p class="lede">Tư vấn kế hoạch tài chính theo mốc đời · mô phỏng trên chính tài sản của bạn</p></div></div>
    <div id="mini"></div><div id="reg"></div>
    <div class="plangrid mt"><div class="panel" id="list"></div><div id="panel"></div></div>`;

  const sentTag = (key) => {
    // what this page sent, else the newest queue item for the same option (sent before a reload or a new sign-in)
    const item = (st.sent[key] && queue.find(x => x.id === st.sent[key]))
      || queue.find(x => x.client_id === client && x.data && `${x.data.scenario}:${x.data.option?.title}` === key);
    if (!item) return "";
    const [cls, text] = QUEUE[item.status] || QUEUE.pending;
    return `<span class="pill ${cls}">${text}</span>`;
  };

  // ── the wealth view: what there is, the followed goals against it, the cash flow ────────────────
  const drawMini = () => {
    const nw = d.net_worth, pf = d.performance, cf = d.cashflow, gs = mine();
    const need = gs.reduce((a, g) => a + g.goal.need, 0), have = gs.reduce((a, g) => a + Math.min(g.goal.have, g.goal.need), 0);
    const short = gs.filter(g => g.goal.gap > 0), saving = short.reduce((a, g) => a + (g.goal.monthly || 0), 0);
    const unfunded = short.filter(g => g.goal.monthly == null);
    const past = (cf.history || []).filter(m => m.in || m.out);
    const pastNet = past.length ? past.reduce((a, m) => a + m.net, 0) / past.length : null;
    const ahead = cf.months.slice(0, 12);
    const aheadIn = ahead.reduce((a, m) => a + m.in, 0), aheadOut = ahead.reduce((a, m) => a + m.out, 0);
    const surplus = gs.length ? Math.max(0, gs[0].goal.surplus) : 0, left = surplus - saving;
    const sv = {surplus: vnd(surplus), count: String(short.length)};
    const r = st.result;
    const sc = r && !r.error && r.scenario === st.pick && r.before && r.after && !goals.some(g => g.id === r.scenario) ? r : null;
    const dNw = sc ? sc.after.net_worth - sc.before.net_worth : 0, dLq = sc ? sc.after.liquid - sc.before.liquid : 0;
    const was = (x) => `<span class="muted">trước ${x}</span>`;
    const ss = (text) => how(text, "scenario.state", {scenario: sc.title});
    const tot = {have: vnd(have), need: vnd(need), count: String(gs.length)};
    const ahd = {total_in: vnd(aheadIn), total_out: vnd(aheadOut)};
    const tile = (k, v, s) => `<div class="kpi"><div class="k">${k}</div><div class="v">${v}</div><div class="s">${s}</div></div>`;
    $("#mini", box).innerHTML = `<div class="panel">
      <h3>Wealth view <span class="hint">tóm tắt tài sản · so với mục tiêu đã đặt · ${d.scope === "family" ? "gia đình" : "cá nhân"}</span></h3>
      ${sc ? `<div class="notice row"><span class="pill ai">${sc.kind === "stress" ? "Stress test" : "Kịch bản"}</span><span>Số liệu bên dưới là <b>sau</b> kịch bản <b data-explains>${esc(sc.title)}</b></span>
        <button type="button" class="linkbtn" id="scen-off" style="margin-left:auto">Về hiện trạng</button></div>` : ""}
      <div class="kpis mt">
        ${sc ? tile("Tổng tài sản ròng · sau kịch bản", ss(vnd(sc.after.net_worth)), `<span class="${dNw >= 0 ? "up" : "down"}">${ss(vnd(dNw, true))} (${ss(pct(sc.before.net_worth ? dNw / sc.before.net_worth : 0, true))})</span> ${was(ss(vnd(sc.before.net_worth)))}`)
          : tile("Tổng tài sản ròng", how(vnd(nw.value), "net_worth", {assets: vnd(nw.assets), liabilities: vnd(nw.liabilities)}), `<span class="${nw.month_change >= 0 ? "up" : "down"}">${nw.month_change >= 0 ? "▲" : "▼"} ${how(pct(nw.month_change_pct, true), "net_worth.month_change", {now: vnd(nw.value)})}</span> tháng này · tài sản ${how(vnd(nw.assets), "assets.total")}, nợ ${how(vnd(nw.liabilities), "liabilities.total")}`)}
        ${sc ? tile("Thanh khoản · sau kịch bản", ss(vnd(sc.after.liquid)), `<span class="${dLq >= 0 ? "up" : "down"}">${ss(vnd(dLq, true))}</span> · đủ chi ${monthsText(sc.after.liquid_months)} ${was(monthsText(sc.before.liquid_months))}`)
          : tile("Lãi / lỗ danh mục đầu tư", `<span class="${pf.unrealized >= 0 ? "up" : "down"}">${how(pct(pf.unrealized_pct, true), "perf.unrealized")}</span>`,
            `${how(vnd(pf.unrealized, true), "perf.unrealized")} chưa chốt · từ đầu năm ${how(pct(pf.ytd_return, true), "perf.ytd_return")} <span class="${pf.vs_benchmark >= 0 ? "up" : "down"}">(${pf.vs_benchmark >= 0 ? "hơn" : "kém"} ${esc(pf.benchmark_name)} ${how(pct(Math.abs(pf.vs_benchmark)), "perf.vs_benchmark", {mine: pct(pf.ytd_return, true), bench: pct(pf.benchmark_ytd, true)})})</span>`)}
        ${tile("Mục tiêu đã đặt · đang có / cần có", gs.length ? how(pct(need ? have / need : 1, false, 0), "goals.total", tot) : "—",
          gs.length ? `${how(vnd(have), "goals.total", tot)} / ${how(vnd(need), "goals.total", tot)} · ${short.length}/${gs.length} mục tiêu còn thiếu` : "chưa đặt mục tiêu nào")}
        ${sc ? "" : tile("Dòng tiền ròng 12 tháng tới · dự báo", how(vnd(aheadIn - aheadOut, true), "cashflow.net_ahead", ahd),
          `vào ${how(vnd(aheadIn), "cashflow.forecast", {months: "12"})} · ra ${how(vnd(aheadOut), "cashflow.forecast", {months: "12"})}${pastNet != null ? ` · 12 tháng qua thực tế ${how(vnd(pastNet, true), "cashflow.past_net", {months: String(past.length)})}/tháng` : ""}`)}
      </div>
      <div class="cols mt">
        <div class="c7"><div class="subhead">Dòng tiền vào / ra · 12 tháng qua (thực tế) và 12 tháng tới (dự báo)</div>
          <div class="legend"><span><i style="background:var(--in)"></i>Tiền vào</span><span><i style="background:var(--out)"></i>Tiền ra</span><span><i style="background:var(--in);opacity:.42"></i><i style="background:var(--out);opacity:.42"></i>Dự báo</span></div>
          <div id="plan-cash"></div></div>
        <div class="c5"><div class="subhead">Cần có so với đang có · từng mục tiêu</div>
          ${gs.length ? `<div class="goals">${gs.map(g => {
            const x = g.goal, c = (GOAL[x.status] || GOAL.none)[2];
            return `<div class="goal"><div class="row spread"><b>${esc(g.title)}</b>${chip(x.status)}</div>
              ${progress(x.progress, {color: c, label: `${g.title}: đang có ${pct(x.progress, false, 0)} nhu cầu`})}
              <div class="small"><span class="muted">Đang có</span> ${how(vnd(Math.min(x.have, x.need)), "goal.have")} <span class="muted">/ cần</span> ${how(vnd(x.need), "goal.need")} <span class="muted">· ${esc(x.by)}</span> ·
                ${x.gap > 0 ? `<span class="down">thiếu ${how(vnd(x.gap), "goal.gap", gapIn(x))}</span>` : `<span class="up">đủ</span>`}</div></div>`;
          }).join("")}</div>
          <div class="notice mt ${left >= 0 && !unfunded.length ? "" : "bad"}"><b>${saving ? `Mục tiêu cần để dành ${how(vnd(saving), "goals.saving", sv)}/tháng` : short.length ? "Mục tiêu còn thiếu nguồn bù" : "Các mục tiêu đã đủ nguồn"}</b>
            <div class="small">Thu nhập trừ chi tiêu còn dư ${how(vnd(surplus), "goal.surplus")}/tháng${saving ? ` → ${left >= 0 ? `còn dư ${how(vnd(left), "goals.saving", sv)}/tháng sau khi để dành` : `thiếu ${how(vnd(-left), "goals.saving", sv)}/tháng`}` : ""}${unfunded.length ? ` · ${unfunded.length} mục tiêu chưa có nguồn bù: ${unfunded.map(g => esc(g.title)).join(", ")}` : ""}.</div></div>`
          : `<p class="small muted">Chọn một mục tiêu bên dưới và bấm <b>Đặt mục tiêu</b> để theo dõi ở đây.</p>`}
        </div>
      </div></div>`;
    const host = $("#plan-cash", box);
    if (host && host.clientWidth) host.replaceChildren(cashflow(cashSeries(cf, 12, 12), cf.large, host.clientWidth));
    const off = $("#scen-off", box);
    if (off) off.onclick = () => { const g = mine().sort((a, b) => RANK[b.goal.status] - RANK[a.goal.status])[0] || goals[0]; if (g) run(g.id, null); };
  };

  const drawReg = () => {
    const m = reg.matches || [];
    $("#reg", box).innerHTML = m.length ? `<div class="panel mt"><h3>Lưu ý quy định cho mục tiêu <span class="hint">nhánh mục tiêu: mốc thời gian và hồ sơ, không phải tiền</span></h3>
      <div class="list">${m.map(x => `<div class="item"><span class="ic-chip" style="--tone:var(--warning)">${icon("scale")}</span>
        <div><div class="t">${esc(x.goal)} · ${esc(x.level_label)}</div><div class="m">mốc ${esc(x.milestone)}</div><div class="small" data-explains>${esc(x.client_message || x.rm_hint || "")}</div></div><span></span></div>`).join("")}</div></div>` : "";
  };

  // ── the list: goals by stage, then decisions and stress tests ───────────────────────────────────
  const drawList = () => {
    const card = (e) => {
      const on = followed(e), g = e.goal;
      return `<button type="button" class="gitem${st.pick === e.id ? " on" : ""}" data-sim="${e.id}">
        <span class="row spread"><b>${esc(e.title)}</b>${chip(on ? g.status : "none")}</span>
        <span class="small ${on ? "" : "muted"}">${on ? gapHow(g) : "Chưa đặt mục tiêu"}</span></button>`;
    };
    const others = catalog.filter(c => !goals.some(g => g.id === c.id));
    $("#list", box).innerHTML = `<h3>Life goals <span class="hint">Mục tiêu theo giai đoạn đời</span></h3>
      ${Object.keys(stages).map(k => {
        const items = goals.filter(e => e.stage === k);
        return items.length ? `<div class="stage"><div class="subhead">${icon(STAGE_ICON[k] || "target", {size: 14})} ${esc(stages[k])}</div><div class="slist">${items.map(card).join("")}</div></div>` : "";
      }).join("")}
      <div class="stage"><div class="subhead">${icon("activity", {size: 14})} Quyết định & stress test</div><div class="slist">${others.map(c => `<button type="button" class="gitem${st.pick === c.id ? " on" : ""}" data-sim="${c.id}">
        <b data-explains>${esc(c.title)}</b><span class="small muted" data-explains>${esc(c.question)}</span></button>`).join("")}</div></div>`;
    for (const b of box.querySelectorAll("[data-sim]")) b.onclick = () => run(b.dataset.sim, null);
  };

  // ── the panel: a goal, or a decision / stress test ──────────────────────────────────────────────
  const simForm = (r) => {
    const f = Object.entries(r.params || {}).filter(([k]) => PARAMS[k]).map(([k, v]) => {
      const [label, unit] = PARAMS[k];
      const shown = typeof v === "number" ? +(v / UNIT[unit]).toFixed(unit === "%" ? 1 : 2) : v;
      return `<label class="field"><span>${label}${unit ? ` (${unit})` : ""}</span><input type="number" step="any" name="${k}" value="${shown}"></label>`;
    }).join("");
    return f ? `<form id="sim-form" class="simform">${f}<button type="submit" class="btn primary">Chạy lại</button></form>` : "";
  };
  const beforeAfter = (r) => `<table class="table mt"><thead><tr><th></th><th class="r">Trước</th><th class="r">Sau</th></tr></thead><tbody>
    <tr><td>Tài sản ròng</td><td class="r">${how(vnd(r.before.net_worth), "scenario.state", {scenario: r.title})}</td><td class="r">${how(vnd(r.after.net_worth), "scenario.state", {scenario: r.title})}</td></tr>
    <tr><td>Thanh khoản</td><td class="r">${how(vnd(r.before.liquid), "scenario.state", {scenario: r.title})}</td><td class="r">${how(vnd(r.after.liquid), "scenario.state", {scenario: r.title})}</td></tr>
    <tr><td>Đủ chi</td><td class="r">${monthsText(r.before.liquid_months)}</td><td class="r">${monthsText(r.after.liquid_months)}</td></tr></tbody></table>`;
  const summary = (r) => `<div class="stats mt">${r.summary.map(l => `<div class="stat"><span class="k" data-explains>${esc(l.label)}</span><span class="v">${how(esc(l.value), "scenario.line", {scenario: r.title, line: l.label})}</span></div>`).join("")}</div>`;
  const options = (r, key) => `<div class="cols mt">${(r.options || []).map(o => {
    const tag = sentTag(`${key}:${o.title}`);
    return `<div class="panel c6"><div class="row spread"><span class="pill">${o.id === "light" ? "Hướng nhẹ" : "Hướng mạnh"}</span>${tag}</div>
      <div data-explains><h3 style="margin:10px 0 6px">${esc(o.title)}</h3>
      <div class="small muted">Làm gì</div><ul class="ul">${o.actions.map(a => `<li>${esc(a)}</li>`).join("")}</ul>
      <div class="small muted">Kết quả</div><ul class="ul">${o.effect.map(a => `<li>${esc(a)}</li>`).join("")}</ul></div>
      ${tag ? "" : `<button type="button" class="btn" data-propose="${o.id}">Gửi chuyên gia duyệt</button>`}</div>`;
  }).join("")}</div>`;
  const tracking = (g) => {
    const t = g.tracking;
    if (!t) return "";
    const m = t.month, pf = d.performance, ex = {rate: pct(t.rate, false, 0), saving: vnd(t.saving)};
    const sign = (x, id = "track.actual", inp) => `<span class="${x >= 0 ? "up" : "down"}">${how(vnd(x, true), id, inp)}</span>`;
    const pc = (x, id = "track.actual") => `<span class="${x >= 0 ? "up" : "down"}">${how(pct(x, true), id, {pool: t.pool_label})}</span>`;
    const pt = (p, text) => how(text, "track.point", {point: p.label});
    const rows = t.points.map((p, i) => {
      const prev = i ? t.points[i - 1] : null, move = prev ? p.gap - prev.gap : null;
      return `<tr><td>${esc(p.label)}</td><td class="r">${pt(p, vnd(p.pool))}</td><td class="r">${pt(p, p.gap > 0 ? "Thiếu " + vnd(p.gap) : "Dư " + vnd(-p.gap))}</td>
        <td class="r">${move == null || Math.abs(move) < 1e6 ? "—" : `<span class="${move > 0 ? "down" : "up"}">${move > 0 ? "xấu đi " : "cải thiện "}${pt(p, vnd(Math.abs(move)))}</span>`}</td></tr>`;
    }).join("");
    return `<div class="panel mt"><h3>Performance tracking <span class="hint">Theo dõi so với danh mục · nguồn: ${esc(t.pool_label.toLowerCase())}</span></h3>
      <div class="notice ${t.behind ? "bad" : ""}"><b>${t.behind ? "▼ Tháng này kém kỳ vọng" : "▲ Tháng này đạt kỳ vọng"}</b><div class="small" data-explains>${esc(t.note)}</div></div>
      <div class="kpis mt three">
        <div class="kpi"><div class="k">Tháng này · thực tế</div><div class="v">${sign(m.actual, "track.actual", {pool: t.pool_label})}</div><div class="s">${pc(m.actual_pct)} nguồn tài sản</div></div>
        <div class="kpi"><div class="k">Tháng này · kỳ vọng</div><div class="v">${how(vnd(m.expected, true), "track.expected", ex)}</div><div class="s">lãi ${how(pct(t.rate, false, 0), "track.expected", ex)}/năm${t.saving ? ` + để dành ${how(vnd(t.saving), "track.expected", ex)}/tháng` : ""}</div></div>
        <div class="kpi"><div class="k">Hụt / vượt so với kỳ vọng</div><div class="v">${sign(m.short, "track.short", {actual: vnd(m.actual, true), expected: vnd(m.expected, true)})}</div><div class="s">từ đầu năm: ${pc(t.ytd.actual_pct)} so với kỳ vọng ${how(pct(t.ytd.expected_pct, true), "track.expected", ex)}</div></div>
      </div>
      <table class="table mt"><thead><tr><th>Mốc</th><th class="r">Nguồn cho mục tiêu</th><th class="r">Chênh lệch mục tiêu</th><th class="r">Thay đổi</th></tr></thead><tbody>${rows}</tbody></table>
      ${t.movers.length ? `<div class="subhead mt">Biến động lớn tháng này trong nguồn</div>${t.movers.map(x => `<div class="kv"><span><span class="legend-dot" style="background:${x.change >= 0 ? "var(--in)" : "var(--out)"}"></span> ${esc(x.name)}</span><b>${how(vnd(x.change, true), "track.mover")} <span class="muted">${how(pct(x.pct, true), "track.mover")}</span></b></div>`).join("")}` : ""}
      <p class="small muted mt">Toàn danh mục đầu tư từ đầu năm ${how(pct(pf.ytd_return, true), "perf.ytd_return")} so với ${esc(pf.benchmark_name)} ${how(pct(pf.benchmark_ytd, true), "perf.benchmark_ytd", {benchmark: pf.benchmark_name})}:
        <span class="${pf.vs_benchmark >= 0 ? "up" : "down"}">${pf.vs_benchmark >= 0 ? "hơn" : "kém"} ${how(pct(Math.abs(pf.vs_benchmark)), "perf.vs_benchmark", {mine: pct(pf.ytd_return, true), bench: pct(pf.benchmark_ytd, true)})}</span>.</p></div>`;
  };
  const goalPanel = (entry, r) => {
    const g = (r && r.goal) || entry.goal, on = followed(entry), key = on ? g.status : "none";
    const acts = g.actions.map((a, i) => {
      const tag = sentTag(`${entry.id}:${a.text}`);
      const worth = a.cut > 0 ? (g.gap > 0 ? `giảm chênh lệch ~${how(vnd(a.cut), "goal.action_cut")}` : `giá trị ~${how(vnd(a.cut), "goal.action_cut")}`) : `<span data-explains>${esc(a.effect)}</span>`;
      return `<div class="item"><span class="ic-chip sm">${i + 1}</span><div><div class="t" data-explains>${esc(a.text)}</div><div class="m">${worth} · ${a.option === "light" ? "Hướng nhẹ" : "Hướng mạnh"}</div></div>
        <div>${tag || `<button type="button" class="btn sm" data-act="${i}">Gửi chuyên gia duyệt</button>`}</div></div>`;
    }).join("");
    return `<div class="panel"><div class="row spread">${chip(key)}<span class="small muted">Mốc: ${esc(g.by)} · ${esc(entry.stage_label)}</span>
        ${on ? `<button type="button" class="linkbtn" data-unfollow="${entry.id}">Bỏ theo dõi</button>` : `<button type="button" class="btn primary sm" data-follow="${entry.id}">Đặt mục tiêu</button>`}</div>
        <h2 class="h2">${esc(entry.title)}</h2>${r ? `<p class="muted" style="margin:0" data-explains>${esc(r.question)}</p>` : ""}</div>
      <div class="panel mt"><h3>Goal status <span class="hint">Tình trạng mục tiêu</span></h3>
        <div class="kpis three">
          <div class="kpi"><div class="k">Cần có</div><div class="v">${how(vnd(g.need), "goal.need")}</div></div>
          <div class="kpi"><div class="k">${esc(g.have_label)}</div><div class="v">${how(vnd(g.have), "goal.have")}</div></div>
          <div class="kpi"><div class="k">Chênh lệch</div><div class="v ${g.gap > 0 ? "down" : "up"}">${how(g.gap > 0 ? "−" + vnd(g.gap) : "+" + vnd(-g.gap), "goal.gap", gapIn(g))}</div></div></div>
        <div class="mt">${progress(g.progress, {color: (GOAL[key] || GOAL.none)[2], label: `Tiến độ ${pct(g.progress, false, 0)}`})}</div>
        <div class="small muted mt-xs">Đã có ${how(pct(g.progress, false, 0), "goal.progress", gapIn(g))} nhu cầu</div>
        <p class="takeaway" data-explains>${esc(g.verdict)}</p></div>
      ${r ? tracking(g) : `<div class="panel mt muted">Đang tính diễn biến so với danh mục…</div>`}
      <div class="panel mt"><h3>Required action <span class="hint">Hành động cần làm · xếp theo mức giảm chênh lệch</span></h3>
        ${acts ? `<div class="list">${acts}</div>` : `<p class="muted">Không cần hành động thêm.</p>`}</div>
      ${r ? `<div class="panel mt"><h3>Calculation details <span class="hint">Chi tiết tính toán · đổi giả định rồi Chạy lại, mục tiêu cập nhật ngay · dữ liệu ngày ${esc(r.as_of)}</span></h3>
        ${simForm(r)}${summary(r)}${beforeAfter(r)}</div>${options(r, entry.id)}<p class="footnote" data-explains>${esc(r.note)}</p>` : ""}`;
  };
  const scenarioPanel = (r) => `<div class="panel"><div class="small muted">${r.kind === "stress" ? "Stress test thị trường · AI tự chạy" : "Quyết định tài sản"} · dữ liệu ngày ${esc(r.as_of)}</div>
      <h2 class="h2" data-explains>${esc(r.title)}</h2><p class="muted" data-explains>${esc(r.question)}</p>${simForm(r)}${summary(r)}${beforeAfter(r)}</div>
    ${options(r, r.scenario)}<p class="footnote" data-explains>${esc(r.note)}</p>`;

  const drawPanel = () => {
    const entry = goals.find(g => g.id === st.pick);
    const r = st.result && st.result.scenario === st.pick ? st.result : null;
    let html;
    if (st.result && st.result.error) html = `<div class="panel"><span class="down">Không mô phỏng được: ${esc(st.result.error)}</span></div>`;
    else if (entry) html = goalPanel(entry, r);
    else if (st.busy || !r) html = `<div class="panel muted">Đang mô phỏng…</div>`;
    else html = scenarioPanel(r);
    const el = $("#panel", box);
    el.className = st.busy ? "loading" : "";
    el.innerHTML = html;
    for (const b of el.querySelectorAll("[data-follow]")) b.onclick = () => { follow(b.dataset.follow, true); draw(); };
    for (const b of el.querySelectorAll("[data-unfollow]")) b.onclick = () => { follow(b.dataset.unfollow, false); draw(); };
    for (const b of el.querySelectorAll("[data-propose]")) b.onclick = () => propose(r.scenario, r.options.find(o => o.id === b.dataset.propose), r.title, r.summary);
    for (const b of el.querySelectorAll("[data-act]")) b.onclick = () => {
      const g = (r && r.goal) || entry.goal, a = g.actions[Number(b.dataset.act)];
      const opt = ((r && r.options) || []).find(o => o.id === a.option) || {};
      propose(entry.id, {id: a.option, title: a.text, actions: [a.text], effect: a.effect ? [a.effect] : (opt.effect || [])},
        entry.title, [{label: "Chênh lệch", value: gapLine(g)}, {label: "Giảm chênh lệch ước tính", value: vnd(a.cut)}]);
    };
    const form = $("#sim-form", el);
    if (form) form.onsubmit = (e) => {
      e.preventDefault();
      const prm = {...r.params};
      for (const i of form.querySelectorAll("input")) prm[i.name] = Number(i.value) * UNIT[PARAMS[i.name][1]];
      run(r.scenario, prm, true);
    };
  };
  const draw = () => { if (!box.isConnected) return; drawMini(); drawList(); drawPanel(); };

  const run = async (id, params, quiet) => {
    st.pick = id;
    const now = goals.find(g => g.id === id);
    st.busy = true;
    if (!quiet) draw();
    try {
      st.result = (await post("/api/scenario", {client_id: client, scenario: id, params: params || (now ? now.params : {}), scope})).result;
      if (now && st.result.goal) { now.goal = st.result.goal; now.params = st.result.params; }  // the goal follows the assumptions tried
    } catch (e) {
      st.result = {error: e.message};
    }
    st.busy = false;
    draw();
    if (!quiet && innerWidth <= 980) { const p = $("#panel", box); if (p) p.scrollIntoView({block: "start"}); }
  };
  const propose = async (scenario, option, title, summ) => {
    try {
      const item = (await post("/api/review/propose", {client_id: client, scenario, title, option, summary: summ})).item;
      st.sent[`${scenario}:${option.title}`] = item.id;
      queue = (await get("/api/review")).items;
    } catch (e) { alert("Không gửi được: " + e.message); }
    draw();
  };

  drawReg();
  draw();
  const again = st.result && !st.result.error && st.result.scenario === st.pick ? st.result : null;
  if (st.pick) run(st.pick, again && !again.goal ? again.params : null, true);
}
