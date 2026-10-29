/* Phân bổ tài sản — the three buckets (ASSET_ALLOCATION_BRD, SCR-CL-13): Liquidity, Legacy and Growth, each with its
   target, what is there and the gap (POST /api/allocation). Four numbered parts (feedback Chỉnh UI-UX ver2):
   01 the financial overview — net worth and liquidity in two figures, the client in one line, the full profile folded
      (risk appetite, risk capacity and the drawdown limit each said for what it is);
   02 the financial priorities — “what do I do now?”: each problem with its cause, its deadline and the action, the
      most urgent first;
   03 the three buckets as tabs (icon, what each is for); each tab shows how it is counted first — every figure with
      its source — then the changes to consider, classed Cần xử lý / Cân nhắc / Quyết định dài hạn by what they do,
      not by their amount; Growth with the rebalance before and after and where its money comes from, Legacy with the
      price-drop case spelled out and four ways to close the gap side by side;
   04 the what-if — move money between Growth and Liquidity, spend more or less, retire at another age: the same
      request with ``whatif`` (POST /api/allocation), the three goals now and in the scenario side by side, explained.
   Folded at the end: the assumptions (edit and run again), the reconciliation, for staff the bucket moves. The worked
   example K-7F3A (POST /api/allocation/example); an RM sends the actions to the review queue (POST
   /api/allocation/send); an RM moves an asset to another bucket with a reason (POST /api/allocation/override). */
import {$, esc, n as how, pct, post, toast, vnd} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {cashflow} from "../charts/money.js?v=20261016r4";

const CHECK = {PASS: ["good", "Phù hợp"], WARN: ["warn", "Cần lưu ý"], BLOCK: ["bad", "Bị chặn"]};
const BUCKET = {liquidity: "Thanh khoản", legacy: "Di sản", growth: "Tăng trưởng"};
// the three tabs: icon, what the bucket is for
const TABS = {
  liquidity: ["wallet", "Đáp ứng chi tiêu và nghĩa vụ tài chính trước mắt"],
  growth: ["stock", "Tích lũy cho nghỉ hưu và các mục tiêu dài hạn"],
  legacy: ["bank", "Chuyển giao tài sản theo kế hoạch gia đình"],
};
// which actions each tab lists: the loans sit with Liquidity (they cost cash each month), retirement with Growth
const TAB_ACTS = {liquidity: ["liquidity", "loans"], growth: ["growth", "retirement"], legacy: ["legacy"]};
// a change by what it does (feedback ver2): a threat to a goal or the risk limit, a better structure, a long-term choice
const KIND = {urgent: ["bad", "Cần xử lý"], improve: ["ai", "Cân nhắc"], long: ["", "Quyết định dài hạn"]};
const RANK = {urgent: 0, improve: 1, long: 2};
// the assumptions a person may change: [unit shown, factor to the engine's number]
const EDIT = {horizon_years: ["năm", 1], buffer_months: ["tháng", 1], inflation: ["%", 0.01], retirement_age: ["tuổi", 1],
  legacy_wish: ["tỷ", 1e9], survivor_share: ["%", 0.01]};
const SIM = "Hồ sơ giả lập";  // every action's warning when the level is simulated: said once, in the profile
const STEP = 50e6;  // the what-if's money moves in 50 triệu steps
const pages = {};  // per client, for this page's life: the method, the tab, the example toggle, the assumptions, the what-if

// an assumption as the form shows it: a share in percent to one decimal (⅔ → 66.7), any other number to two
const shown = (x, f) => +(x / f).toFixed(f < 1 ? 1 : 2);
const pill = (c) => `<span class="pill ${CHECK[c.status][0]}">${CHECK[c.status][1]}</span>`;
// every figure opens its formula (BRD-NFR-11): alloc.* in src/explain/metrics.py
const m = how;
const gap = (short, over) => (short > 0 ? `<span class="pill warn">Thiếu ${m(vnd(short), "alloc.liquidity")}</span>`
  : over > 0 ? `<span class="pill ai">Dư ${m(vnd(over), "alloc.liquidity")}</span>` : `<span class="pill good">Đủ</span>`);
const range = (a, b, metric) => m(b && Math.round(b) !== Math.round(a) ? `${vnd(a)}–${vnd(b)}` : vnd(a), metric);
const ym = (s) => (s ? `${s.slice(5, 7)}/${s.slice(0, 4)}` : "");
const more = (title, body, open) => `<details class="more mt"${open ? " open" : ""}><summary>${esc(title)}</summary>${body}</details>`;
const table = (head, rows, cls = "") => `<div class="scrollx"><table class="table ${cls}"><thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead>
  <tbody>${rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
const src = (s) => `<span class="small muted" data-explains>${s}</span>`;  // where a figure comes from: a few words, no formula
const names = (xs, k = 3) => esc(xs.slice(0, k).join(", ")) + (xs.length > k ? ` +${xs.length - k}` : "");
const section = (n, eyebrow, title, sub, body, id = "") => `<section class="panel mt sec"${id ? ` id="${id}"` : ""}>
  <div class="sec-eyebrow">${n} · ${esc(eyebrow)}</div><h2 class="sec-title">${esc(title)}</h2>
  ${sub ? `<p class="sec-sub">${sub}</p>` : ""}${body}</section>`;
const kindOf = (x, a) => {  // what an action does, by its bucket and kind (feedback ver2: never by its amount)
  if (x.bucket === "liquidity") return x.kind === "move" ? "improve" : "urgent";
  if (x.bucket === "growth") return a.growth.worst_before.share > (a.risk.drawdown_limit || 1) ? "urgent" : "improve";
  if (x.bucket === "legacy") return "urgent";
  if (x.bucket === "retirement") return "long";
  return "improve";
};

// ── 01 · the overview: net worth and liquidity, the client in one line, the profile folded ─────────────────

function overview(a, ctx, staff) {
  const c = a.client || {}, r = a.risk, s = a.assumptions, liq = a.liquidity, rc = a.reconcile;
  const kids = (c.dependents || []).filter(d => d.age != null);
  const plans = (c.plans || []).filter(p => p.amount >= 500e6);
  const done = [liq.short <= 0, a.retirement.status !== "short", a.legacy.gap <= 0].filter(Boolean).length;
  const line = [`${esc(c.name || "")}${c.age ? `, ${c.age} tuổi` : ""}`,
    kids.length ? `${kids.length} con (${kids.map(d => `${d.age} tuổi`).join(", ")})` : "",
    `nghỉ hưu ${s.retirement_age} tuổi${c.retirement_year ? ` (${c.retirement_year})` : ""}`,
    `rủi ro ${r.level}/5 · ${esc(r.name)}`, r.drawdown_limit != null ? `ngưỡng sụt giảm ${pct(r.drawdown_limit, false, 0)}` : ""].filter(Boolean);
  const test = ctx.role === "client" ? "#/client/muc-tieu/khau-vi" : ctx.href("khach-hang", "ke-hoach");
  const cell = (k, v, sub) => `<div><div class="k">${esc(k)}</div><div class="v">${v}</div>${sub ? `<div class="small muted" data-explains>${sub}</div>` : ""}</div>`;
  const profile = `<div class="who mt-xs">
      ${cell("Các con", kids.length ? kids.map(d => `${esc(d.name || "Con")} (${d.age} tuổi)`).join("<br>") : "Không khai")}
      ${cell("Kế hoạch lớn", plans.length ? plans.map(p => `${esc(p.label)} · ${ym(p.date)} · ${vnd(p.amount)}`).join("<br>") : "Chưa có")}
      ${cell("Thu nhập / chi tiêu mỗi tháng", `${vnd(c.income_monthly)} / ${vnd(c.spending_monthly)}`, `Chắc chắn ${vnd(c.income_certain_monthly)}/tháng (lương, lương hưu, tiền thuê)`)}
      ${cell("Nghề nghiệp", esc([c.occupation, c.segment].filter(Boolean).join(" · ")))}
    </div>
    <h3 class="mt">Rủi ro: ba con số, ba ý nghĩa</h3>
    <div class="who risk3">
      ${cell("Mức rủi ro dùng để phân bổ", `${r.level}/5 · ${esc(r.name)}`, "Mức thấp hơn giữa khẩu vị và khả năng: quyết định mô hình danh mục")}
      ${cell("Khẩu vị rủi ro", esc(r.tolerance || r.name), "Mức khách hàng muốn chấp nhận, từ câu trả lời bài test")}
      ${cell("Khả năng chịu rủi ro", esc(r.capacity || r.name), "Mức tài chính cho phép: thu nhập, nghĩa vụ, thời gian đến mục tiêu")}
      ${cell("Ngưỡng sụt giảm chịu được", r.drawdown_limit != null ? pct(r.drawdown_limit, false, 0) : "—", "Danh mục được phép giảm tối đa chừng này từ đỉnh trước khi phải điều chỉnh")}
    </div>
    <p class="small muted mt-xs">${r.source === "simulated"
      ? `Mức rủi ro ${r.level} (${esc(r.name)}) là giả lập từ hồ sơ, nên mọi đề xuất dưới đây đều cần lưu ý. <a href="${test}">${staff ? "Mời khách làm bài test" : "Làm bài test rủi ro"}</a>`
      : `Theo bài test rủi ro${r.at ? ` ngày ${esc(r.at)}` : ""}.`}</p>`;
  return section("01", "Tổng quan tài chính", "Sức khỏe tài chính tổng thể", "Tài sản ròng · Tài sản thanh khoản · Nợ · Mức độ hoàn thành các mục tiêu", `
    <div class="stats">
      <div class="stat"><div class="k">Tài sản ròng</div><div class="v">${m(vnd(rc.net_worth), "alloc.reconcile")}</div>
        <div class="small muted">Tài sản ${vnd(rc.assets)} − nợ ${vnd(rc.debts)}</div></div>
      <div class="stat"><div class="k">Thanh khoản</div><div class="v">${m(vnd(liq.have), "alloc.liquidity", {method: a.method_label})}</div>
        <div class="small muted">Cần ${vnd(liq.target)} (${esc(a.method_label.toLowerCase())}) · ${liq.short > 0 ? `thiếu ${vnd(liq.short)}` : "đủ"}</div></div>
    </div>
    <div class="row tight mt-xs small"><span class="chip">${icon("target", {size: 13})} ${done}/3 mục tiêu đủ</span>
      <span class="muted">${line.join(" · ")}</span></div>
    ${more("Xem hồ sơ khách hàng", profile)}`);
}

// ── 02 · the priorities: what to do now, with cause, deadline and action ───────────────────────────────

function priorities(a) {
  const liq = a.liquidity, cf = a.cashflow, ret = a.retirement, leg = a.legacy, gr = a.growth, dd = a.risk.drawdown_limit;
  const act = (b) => a.actions.find(x => x.bucket === b);
  const big = [...cf.dated].sort((x, y) => y.amount - x.amount)[0];
  const out = [];
  if (liq.short > 0) {
    const x = act("liquidity");
    out.push({kind: "urgent", tab: "liquidity", title: `Bổ sung ${vnd(liq.short)} dự phòng thanh khoản trước khi phân bổ thêm vốn dài hạn`,
      issue: `Thanh khoản có ${vnd(liq.have)}, cần ${vnd(liq.target)} cho ${cf.horizon_years} năm tới (${a.method_label.toLowerCase()})`,
      cause: big ? `Khoản chi lớn nhất: ${esc(big.label)} ${vnd(big.amount)} (${ym(big.month)}); đáy dòng tiền ${ym(cf.trough.month)}` : `Chi thường xuyên vượt thu nhập`,
      when: big ? `Trước ${ym(big.month)}` : `Trong 3 tháng`, action: x ? `${esc(x.what)}${x.amount ? ` · ${vnd(x.amount)}` : ""}` : "Xếp bậc thang tiền gửi"});
  }
  if (gr.worst_before.share > (dd || 1)) {
    out.push({kind: "urgent", tab: "growth", title: `Đưa rủi ro danh mục về dưới ngưỡng ${pct(dd, false, 0)}`,
      issue: `Khi thị trường xấu, danh mục có thể lỗ ${pct(gr.worst_before.share)}`, cause: "Tỷ trọng cổ phiếu và vàng cao hơn mô hình",
      when: "Trong quý này", action: gr.worst_after.share > dd
        ? `Tái cân bằng theo mô hình (lỗ khi thị trường xấu còn ${pct(gr.worst_after.share)}, vẫn trên ngưỡng): xem lại mức rủi ro với chuyên viên`
        : `Tái cân bằng theo mô hình: lỗ khi thị trường xấu còn ${pct(gr.worst_after.share)}`});
  }
  if (leg.gap > 0) {
    const ins = (leg.options || []).find(o => o.id === "insure");
    out.push({kind: "urgent", tab: "legacy", title: `Bảo vệ gia đình trước khoản hở ${range(leg.gap, leg.gap_high, "alloc.legacy")}`,
      issue: `Nếu rủi ro xảy ra, gia đình cần ${vnd(leg.target)} nhưng giỏ Di sản có ${range(leg.have_low, leg.have, "alloc.legacy")}`,
      cause: `Chi tiêu gia đình đến khi con nhỏ tự lập và học phí còn lại`, when: "Ngay: rủi ro không báo trước",
      action: ins ? `Bảo hiểm có người thụ hưởng, khoảng ${vnd(ins.monthly)}/tháng (so sánh 4 phương án ở giỏ Di sản)` : esc(leg.fill_with)});
  }
  if (ret.status === "short") {
    out.push({kind: "long", tab: "growth", title: `Quyết định lại mục tiêu nghỉ hưu năm ${ret.year}`,
      issue: `Dự kiến đạt ${vnd(ret.reach)}, cần ${vnd(ret.need)} (giá năm ${ret.year})`,
      cause: `Lợi suất cần ${ret.required != null ? pct(ret.required) : "trên 30%"}/năm, mô hình giả định ${pct(ret.expected)}/năm`,
      when: `Còn ${ret.years} năm`, action: `Thử ở phần 04: tiết kiệm thêm, giảm chi hoặc nghỉ muộn hơn`});
  }
  if (liq.excess > 0) out.push({kind: "improve", tab: "liquidity", title: `Đưa ${vnd(liq.excess)} tiền dư sang giỏ Tăng trưởng`,
    issue: `Thanh khoản dư so với nhu cầu ${cf.horizon_years} năm`, cause: "Tiền nằm chờ, lợi suất thấp", when: "Khi thuận tiện", action: "Chuyển sang tiền chờ đầu tư"});
  out.sort((x, y) => RANK[x.kind] - RANK[y.kind]);
  const sim = a.risk.source === "simulated";
  return section("02", "Ưu tiên tài chính", "Tôi cần làm gì ngay bây giờ?",
    out.length ? `${out.length} việc, việc cấp bách nhất trước${sim ? " · các đề xuất đúng khi giả định của mô hình được xác nhận (mức rủi ro đang giả lập)" : ""}` : "",
    out.length ? `<ol class="prio">${out.map((p, i) => `<li class="${i ? "" : "first"}" data-goto="${p.tab}" tabindex="0">
        <div class="row tight"><span class="pnum">${i + 1}</span><span class="pill ${KIND[p.kind][0]}">${KIND[p.kind][1]}</span><b>${p.title}</b></div>
        <dl class="pgrid small"><div><dt>Vấn đề</dt><dd data-explains>${p.issue}</dd></div><div><dt>Nguyên nhân</dt><dd data-explains>${p.cause}</dd></div>
          <div><dt>Thời hạn</dt><dd>${p.when}</dd></div><div><dt>Hành động đề xuất</dt><dd data-explains>${p.action}</dd></div></dl></li>`).join("")}</ol>`
      : `<p class="muted">Ba giỏ đều đủ: không có việc gấp.</p>`);
}

// ── 03 · the buckets ─────────────────────────────────────────────────────────────────────────────────────

// Liquidity: the two ways to count income side by side, the cash flow month by month, every line with its source
function liquidity(a) {
  const liq = a.liquidity, cf = a.cashflow, n = cf.months.length, have = liq.have;
  const loans = (a.existing_loans || []).map(l => l.name).filter(Boolean);
  const way = (k, title, sub, extra) => {
    const t = cf.targets[k], on = a.method === k || (extra && a.method === extra[0]);
    return `<div class="way${on ? " on" : ""}"><div class="row spread"><b>${esc(title)}</b>${on ? `<span class="pill ai">Đang dùng cho việc cần làm</span>` : ""}</div>
      <div class="small muted" data-explains>${sub}</div>
      <div class="kv mt-xs"><span>Giỏ Thanh khoản cần</span><b>${m(vnd(t), "alloc.liquidity", {method: a.methods[k]})}</b></div>
      ${extra ? `<div class="kv"><span>Chỉ tính thu nhập chắc chắn</span><b>${m(vnd(cf.targets[extra[0]]), "alloc.liquidity", {method: a.methods[extra[0]]})}</b></div>` : ""}
      <div class="kv"><span>Đang có ${m(vnd(have), "alloc.liquidity")}</span><b>${gap(Math.max(0, t - have), Math.max(0, have - t))}</b></div>
      <div class="row tight mt-xs">${(extra ? [[k, "Dùng: toàn bộ thu nhập"], [extra[0], "Dùng: chỉ chắc chắn"]] : [[k, "Dùng cách này"]]).map(([x, l]) =>
        `<button type="button" class="btn sm" data-method="${x}" aria-pressed="${a.method === x}" ${a.method === x ? "disabled" : ""}>${esc(l)}</button>`).join("")}</div></div>`;
  };
  const dated = (d, sign) => [esc(d.label), src(sign > 0 ? "Khoản thu theo lịch (không chắc chắn)" : d.label.startsWith("Trả gốc") ? "Hợp đồng vay: trả gốc cuối kỳ" : "Khoản chi đã lên lịch trong hồ sơ"), ym(d.month), sign * d.amount];
  const lines = [
    ["Thu nhập", src(`Thu nhập trong hồ sơ ${vnd(cf.income_monthly)}/tháng; chắc chắn ${vnd(cf.income_certain_monthly)}/tháng (lương, lương hưu, tiền thuê 12 tháng qua)`),
      `${n} tháng`, cf.income_monthly * n],
    ...(cf.dated_in || []).map(d => dated(d, 1)),
    ["Chi tiêu sinh hoạt", src(`Chi tiêu hằng tháng trong hồ sơ ${vnd(cf.living_monthly)}/tháng`), `${n} tháng`, -cf.living_monthly * n],
    ...(cf.debt_service_monthly ? [["Trả nợ vay", src(`${loans.length ? esc(loans.join(", ")) + " · " : ""}${vnd(cf.debt_service_monthly)}/tháng theo hợp đồng`),
      `${n} tháng`, -cf.debt_service_monthly * n]] : []),
    ...cf.dated.map(d => dated(d, -1)),
  ];
  const net = lines.reduce((t, l) => t + l[3], 0);
  const sum = `<p class="small muted">${[`Đáy dòng tiền ${ym(cf.trough.month)}: ${m(vnd(cf.trough.cum, true), "alloc.cashflow")}`,
    `Đệm ${cf.buffer_months} tháng chi: ${m(vnd(cf.buffer), "alloc.cashflow")}`,
    `Lãi vay +${m(pct(cf.rate_shock.pp, false, 0), "alloc.cashflow")}: thêm ${m(vnd(cf.rate_shock.monthly), "alloc.cashflow")}/tháng`].map(x => `<span>${x}</span>`).join(" · ")}</p>`;
  return `<h3>Cách tính</h3>
    <div class="ways">
      ${way("B", "Tính đủ thu nhập", `Lấy đáy dòng tiền ${cf.horizon_years} năm khi vẫn có thu nhập (cả thưởng), cộng đệm ${cf.buffer_months} tháng chi`, ["C"])}
      ${way("A", "Không tính thu nhập", `Mọi khoản chi ${cf.horizon_years} năm tới, như khi không còn thu nhập`)}
    </div>
    <h3 class="mt">Dòng tiền ${cf.horizon_years} năm tới <span class="hint">di chuột vào từng tháng để xem các khoản</span></h3>
    <div id="alloc-cash" class="mt-xs"></div>
    ${more(`Từng khoản dòng tiền (${lines.length})`, table(["Khoản", "Nguồn", "Khi nào", "Số tiền"], [...lines.map(([k, s, w, v]) => [k, s, esc(w), m(vnd(v, true), "alloc.cashflow")]),
      ["<b>Ròng</b>", src("Thu nhập trừ mọi khoản chi"), esc(`${ym(cf.months[0].month)}–${ym(cf.months[n - 1].month)}`), `<b>${m(vnd(net, true), "alloc.cashflow")}</b>`]]) + sum)}
    ${more("Bậc thang Thanh khoản", table(["Khoản", "Dùng cho", "Số tiền"], liq.ladder.map(r => [esc(r.what), esc(r.when), m(vnd(r.amount), "alloc.ladder")])))}
    ${more("Cách bù phần thiếu", table(["Cách bù", "Chi phí", "Được?", "Vì sao"], a.fill.options.map(o =>
      [esc(o.label), `<span data-explains>${esc(o.cost || "")}</span>`, o.id === a.fill.chosen ? `<span class="pill good">Đã chọn</span>` : o.ok ? "Có" : "Không", `<span data-explains>${esc(o.why)}</span>`])))}`;
}

// the months of the table as the chart's columns: income (and a bonus) above, every cost below, named in the tip
function months(cf) {
  return cf.months.map(x => {
    const dated = cf.dated.filter(d => d.month === x.month), bonus = (cf.dated_in || []).filter(d => d.month === x.month);
    const items = [{direction: "in", label: "Thu nhập", amount: cf.income_monthly}, ...bonus.map(d => ({direction: "in", label: d.label, amount: d.amount})),
      {direction: "out", label: "Chi tiêu sinh hoạt", amount: cf.living_monthly},
      ...(cf.debt_service_monthly ? [{direction: "out", label: "Trả nợ vay", amount: cf.debt_service_monthly}] : []),
      ...dated.map(d => ({direction: "out", label: d.label, amount: d.amount}))];
    const inn = cf.income_monthly + (x.dated_in || 0), out = cf.recurring_monthly + x.dated;
    return {month: x.month, in: inn, out, net: inn - out, items: items.filter(i => i.amount > 0)};
  });
}

// Growth: one source for every figure — today's bucket, what moves to Liquidity, what it grows to, what is needed —
// then the rebalance before and after, where its money comes from and why it suits a long-term goal
function growth(a) {
  const ret = a.retirement, gr = a.growth, s = a.assumptions, c = a.client || {}, dd = a.risk.drawdown_limit;
  const now = a.buckets.growth.value, g1 = gr.rebalance.total, moved = now - g1;
  const nominal = ret.year ? ` (năm ${ret.year}, giá danh nghĩa, lạm phát ${pct(s.inflation, false, 0)}/năm)` : "";
  const rows = ret.status === "retired" ? [["Nghỉ hưu", "Đã nghỉ", src(`Tuổi nghỉ hưu ${s.retirement_age} (giả định) · nay ${c.age} tuổi`)]] : [
    ["<b>Tài sản hiện tại</b>", m(vnd(now), "alloc.growth"), src("Giỏ Tăng trưởng hôm nay")],
    ...(Math.round(moved) ? [[moved > 0 ? "Chuyển sang Thanh khoản" : "Nhận tiền dư từ Thanh khoản", m(vnd(-moved, true), "alloc.growth"),
      src(moved > 0 ? "Bán để bù giỏ Thanh khoản (phần 02, việc số 1)" : "Thanh khoản dư so với nhu cầu, chuyển sang chờ đầu tư")],
      ["Vốn đầu tư dài hạn", m(vnd(g1), "alloc.growth"), src(`${vnd(now)} ${moved > 0 ? "−" : "+"} ${vnd(Math.abs(moved))}: con số dùng cho mọi phép tính dưới đây`)]] : []),
    ["Dòng tiền ròng mỗi năm (từ năm thứ " + (s.horizon_years + 1) + ")", `${m(vnd(ret.saving_yearly, true), "alloc.retirement")}/năm`,
      src(ret.saving_yearly < 0 ? "Thu nhập thấp hơn chi tiêu: mỗi năm rút bớt từ danh mục" : "Thu nhập trừ chi tiêu, cộng thêm vào danh mục mỗi năm")],
    ["Lợi suất giả định", `${m(pct(ret.expected), "alloc.growth")}/năm`, src(`Mô hình mức rủi ro ${a.risk.level} · ${esc(a.risk.name)}`)],
    ["<b>Giá trị dự kiến khi nghỉ hưu</b>", `<b>${m(vnd(ret.reach), "alloc.retirement")}</b>`, src(`Vốn đầu tư dài hạn và dòng tiền ròng, sau ${ret.years} năm ở lợi suất giả định`)],
    ["<b>Mục tiêu cần đạt</b>", `<b>${m(vnd(ret.need), "alloc.retirement")}</b>`, src(`Chi tiêu nay ${vnd(ret.spend_now)}/năm, tăng theo lạm phát đến ${ret.year}, × ${s.withdraw_multiple} năm chi`)],
    ["Lợi suất cần để đạt mục tiêu", ret.required != null ? `${m(pct(ret.required), "alloc.retirement")}/năm` : "Trên 30%/năm", src("Lợi suất mà giá trị dự kiến bằng mục tiêu")],
    ...(ret.status === "short" ? [
      ["<b>Thiếu</b>", `<b>${m(vnd(ret.short), "alloc.retirement")}</b>`, src("Mục tiêu cần đạt trừ giá trị dự kiến")],
      ["Khoản đóng góp bổ sung cần thêm", `${m(vnd(ret.extra_monthly), "alloc.retirement")}/tháng`, src(`Ngoài dòng tiền ròng ở trên, góp thêm mỗi tháng trong ${ret.saving_years} năm để bù phần thiếu`)],
      ["Hoặc nghỉ muộn", ret.delay.enough ? `${ret.delay.enough} năm` : "Lùi 10 năm vẫn chưa đủ", src("Giữ nguyên mọi thứ khác, lùi năm nghỉ")]] : []),
  ];
  const rr = gr.rebalance.rows, total = gr.rebalance.total || 1;
  const sells = rr.filter(r => r.trade < -1), buys = rr.filter(r => r.trade > 1);
  const sold = -sells.reduce((t, r) => t + r.trade, 0), bought = buys.reduce((t, r) => t + r.trade, 0);
  const before = table(["Loại", "Hiện tại", "Mục tiêu", "Giao dịch", "Sau điều chỉnh"], rr.map(r =>
    [esc(r.label) + (r.views && r.views.length ? `<div class="small muted">${esc(r.views.join(", "))}</div>` : ""),
      `${m(pct(r.now_pct), "alloc.rebalance")} <span class="small muted">${vnd(r.now)}</span>`,
      `${m(pct(r.target_pct), "alloc.rebalance")}${r.tilt ? ` <span class="small muted">(${m(pct(r.tilt, true, 0), "alloc.rebalance")})</span>` : ""}`,
      Math.abs(r.trade) > 1 ? `<b class="${r.trade > 0 ? "up" : "down"}">${r.trade > 0 ? "Mua" : "Bán"} ${m(vnd(Math.abs(r.trade)), "alloc.rebalance")}</b>` : `<span class="muted">Giữ</span>`,
      `${m(pct(r.after / total), "alloc.rebalance")} <span class="small muted">${vnd(r.after)}</span>`]), "cmp");
  return `<h3>Cách tính</h3>
    <p class="small muted">Một nguồn số liệu cho cả giỏ: mọi con số dưới đây đi từ <b>tài sản hiện tại</b> tới <b>giá trị dự kiến khi nghỉ hưu</b> và <b>mục tiêu cần đạt</b>${nominal}.</p>
    ${table(["Khoản", "Số tiền", "Nguồn"], rows)}
    <h3 class="mt">Tái cân bằng: trước và sau <span class="hint">mức rủi ro ${a.risk.level} · ${esc(a.risk.name)}</span></h3>
    ${before}
    <div class="notes mt-xs small">
      <p data-explains><b>Nguồn vốn.</b> ${sold ? `Bán ${vnd(sold)} (${sells.map(r => esc(r.label.toLowerCase())).join(", ")})` : "Không bán gì"}${bought ? ` để mua ${vnd(bought)} (${buys.map(r => esc(r.label.toLowerCase())).join(", ")})` : ""}${Math.abs(sold - bought) > 1e6 ? `; chênh ${vnd(Math.abs(sold - bought))} ${sold > bought ? "giữ ở tiền chờ đầu tư" : "lấy từ tiền chờ đầu tư"}` : ""}. Tổng giỏ không đổi: ${vnd(g1)}.</p>
      <p data-explains><b>Tác động.</b> Khi thị trường xấu, danh mục có thể lỗ ${m(pct(gr.worst_before.share), "alloc.worst")} trước điều chỉnh, ${m(pct(gr.worst_after.share), "alloc.worst")} sau${dd ? ` (ngưỡng chịu được ${pct(dd, false, 0)}${gr.worst_after.share > dd ? ": vẫn trên ngưỡng, nên xem lại mức rủi ro" : ""})` : ""}.</p>
      <p data-explains><b>Vì sao vẫn hợp với mục tiêu tăng trưởng dài hạn.</b> Bán bớt nhóm vượt tỷ trọng và mua nhóm còn thiếu đưa từng nhóm về tỷ trọng mục tiêu của mô hình mức rủi ro ${a.risk.level}: lợi suất giả định vẫn là ${pct(gr.expected)}/năm, còn rủi ro không dồn vào một nhóm tài sản.</p>
    </div>
    ${more("Theo 11 loại tài sản", table(["Loại", "Đang có", "Trong Tăng trưởng", "Mức mục tiêu"], a.eleven.rows.map(r =>
      [esc(r.label) + (r.loan ? ` <span class="chip">Khoản vay</span>` : ""), m(vnd(r.value), "alloc.eleven"), m(vnd(r.in_growth), "alloc.eleven"),
        r.target == null ? `<span class="muted">—</span>` : `${m(vnd(r.target), "alloc.eleven")} <span class="small muted">(${m(pct(r.target_pct), "alloc.eleven")})</span>`]))
      + `<p class="small muted">Ngoài 11 loại (tiền VND, tiền gửi, quỹ tiền tệ, bảo hiểm): ${m(vnd(a.eleven.outside), "alloc.eleven")}</p>`)}`;
}

// Legacy: the need, what is there (and how it reconciles with the bucket), the price drop spelled out, four ways to close it
function legacy(a) {
  const leg = a.legacy, loans = a.loans.items.map(l => l.name).filter(Boolean);
  const held = a.buckets.legacy.holdings.map(h => h.name).filter(Boolean), book = a.buckets.legacy.value;
  const adjust = leg.have - (book - leg.secured);  // insurance at its payout, not its cash value
  const drop = leg.drop ? leg.estate * leg.drop.drop : 0;
  const rows = [
    ...leg.floor_rows.map(r => [esc(r.label), src(r.how ? esc(r.how) : loans.length ? esc(loans.join(", ")) : "Các khoản vay đang có"), m(vnd(r.amount), "alloc.legacy")]),
    ["<b>Gia đình cần (sàn Di sản)</b>", src("Cộng ba khoản trên"), `<b>${m(vnd(leg.floor), "alloc.legacy")}</b>`],
    ...(leg.wish ? [["Mong muốn để lại", src("Khách hàng khai; mục tiêu là số lớn hơn"), m(vnd(leg.wish), "alloc.legacy")]] : []),
    ["Tài sản trong giỏ Di sản", src(held.length ? names(held) : "—"), m(vnd(book), "alloc.legacy")],
    ...(leg.secured ? [["Trừ nợ thế chấp trên các tài sản này", src(loans.length ? esc(loans[0]) : ""), m(vnd(-leg.secured, true), "alloc.legacy")]] : []),
    ...(Math.round(adjust) ? [[adjust > 0 ? "Bảo hiểm tính theo số tiền chi trả" : "Không tính bảo hiểm chưa có người thụ hưởng",
      src(adjust > 0 ? "Số tiền gia đình nhận thay cho giá trị hoàn lại" : "Chưa chỉ định người thụ hưởng: gia đình chưa chắc nhận được"), m(vnd(adjust, true), "alloc.legacy")]] : []),
    ["<b>Đang có (giá hôm nay)</b>", src("Phần gia đình nhận được"), `<b>${m(vnd(leg.have), "alloc.legacy")}</b>`],
    ["<b>Thiếu nếu giá giữ nguyên</b>", src(`Mục tiêu ${vnd(leg.target)} trừ phần đang có`), leg.gap > 0 ? `<b>${m(vnd(leg.gap), "alloc.legacy")}</b>` : `<span class="pill good">Đủ</span>`],
  ];
  const stress = leg.drop ? table(["Bước", "Giá trị", "Nguồn"], [
    ["Bất động sản trong giỏ Di sản (giá hôm nay)", m(vnd(leg.estate), "alloc.legacy"), src("Chỉ phần bất động sản chịu kịch bản; bảo hiểm và tài sản khác giữ nguyên")],
    [`Giảm ${pct(leg.drop.drop, false, 0)}`, m(vnd(-drop, true), "alloc.legacy"), src(`${vnd(leg.estate)} × ${pct(leg.drop.drop, false, 0)} · ${esc(leg.drop.note || "giả định")}${leg.drop.period ? `, như giai đoạn ${esc(leg.drop.period)}` : ""}`)],
    ["Đang có sau kịch bản", m(vnd(leg.have_low), "alloc.legacy"), src(`${vnd(leg.have)} − ${vnd(drop)}`)],
    ["<b>Thiếu nếu giá giảm</b>", `<b>${m(vnd(leg.gap_high), "alloc.legacy")}</b>`, src(`Mục tiêu ${vnd(leg.target)} − ${vnd(leg.have_low)}`)],
  ]) : "";
  const opts = leg.options || [], base = opts.length ? opts[0].left_now : 0, years = leg.years || 10;
  const options = opts.length ? `<h3 class="mt">Bốn cách khép khoản thiếu <span class="hint">tính trên phần thiếu khi giá giảm: ${vnd(base)}</span></h3>
    ${table(["Phương án", "Chi phí mỗi tháng", "Che được ngay", "Còn hở hôm nay", `Sau ${years} năm`, ""], opts.map(o =>
      [`<b>${esc(o.label)}</b><div class="small muted" data-explains>${esc(o.note)}</div>`, o.monthly ? vnd(o.monthly) : "0",
        o.covered_now ? `<span class="up">${vnd(o.covered_now)}</span>` : "0", o.left_now ? `<span class="down">${vnd(o.left_now)}</span>` : `<span class="pill good">Không</span>`,
        o.left_later ? `<span class="down">còn hở ${vnd(o.left_later)}</span>` : o.built ? `có sẵn ${vnd(o.built)}` : "đã che", ""]), "cmp")}` : "";
  return `<h3>Cách tính</h3>${table(["Khoản", "Nguồn / cách tính", "Số tiền"], rows)}
    ${stress ? `<h3 class="mt">Nếu giá bất động sản giảm</h3>${stress}` : ""}${options}`;
}

function actions(a, tab, staff, st) {
  const acts = a.actions.filter(x => TAB_ACTS[tab].includes(x.bucket)).map(x => ({...x, k: kindOf(x, a)})).sort((x, y) => RANK[x.k] - RANK[y.k]);
  return `<h3 class="mt">Cân nhắc thay đổi <span class="hint">theo bản chất: cần xử lý, cân nhắc, quyết định dài hạn</span></h3>
    ${acts.length ? `<ol class="alloc-acts">${acts.map(x => `
      <li><div class="row" style="gap:8px;flex-wrap:wrap;align-items:baseline">
        <span class="pill ${KIND[x.k][0]}">${KIND[x.k][1]}</span><strong>${esc(x.what)}</strong>${x.amount ? `<span>${range(x.amount, x.amount_high, "alloc.action")}</span>` : ""}
        <span class="small muted">Kiểm tra phù hợp:</span>${pill(x.check)}</div>
        <div class="small muted" data-explains>${esc(x.why)}</div>
        ${x.check.reasons.filter(r => r !== SIM).map(r => `<div class="small" data-explains>${esc(r)}</div>`).join("")}</li>`).join("")}
    </ol>` : `<p class="muted">Không có thay đổi nào cần cân nhắc ở giỏ này.</p>`}
    ${staff && !a.example ? `<div class="row mt" style="gap:12px;align-items:center">
      <button type="button" class="btn primary" data-send ${st.sent ? "disabled" : ""}>Gửi vào hàng duyệt</button>
      <span class="small muted">${st.sent ? `Đã gửi ${esc(st.sent)}` : `Gửi cả ${a.actions.length} thay đổi của ba giỏ`}</span></div>` : ""}`;
}

function buckets(a, st, staff) {
  const liq = a.liquidity, leg = a.legacy, ret = a.retirement, gr = a.growth, s = a.assumptions;
  const tiles = {
    liquidity: [liq.have, `Cần ${m(vnd(liq.target), "alloc.liquidity", {method: a.method_label})} · ${esc(a.method_label.toLowerCase())}`, gap(liq.short, liq.excess)],
    growth: [a.buckets.growth.value, `Lợi suất giả định ${m(pct(gr.expected), "alloc.growth")}/năm · cần ${m(pct(ret.required), "alloc.retirement")}/năm`,
      ret.status === "short" ? `<span class="pill warn">Thiếu ${m(vnd(ret.short), "alloc.retirement")} khi nghỉ hưu ${ret.year}</span><div class="small muted mt-xs">Giá danh nghĩa, lạm phát ${pct(s.inflation, false, 0)}/năm</div>`
        : `<span class="pill good">Đủ cho nghỉ hưu</span>`],
    legacy: [leg.have, `Cần ${m(vnd(leg.target), "alloc.legacy")} · sàn ${m(vnd(leg.floor), "alloc.legacy")}`,
      leg.gap > 0 ? `<span class="pill warn">Thiếu ${range(leg.gap, leg.gap_high, "alloc.legacy")}</span>` : `<span class="pill good">Đủ</span>`],
  };
  const tab = st.tab;
  return section("03", "Ba giỏ tài sản", "Mỗi giỏ một nhiệm vụ", "Chọn một giỏ để xem cách tính và các thay đổi nên cân nhắc", `
    <div class="btabs" role="tablist" aria-label="Ba giỏ">${Object.entries(TABS).map(([id, [ic, what]]) => {
      const [have, sub, tag] = tiles[id];
      return `<div class="kpi" role="tab" tabindex="0" data-tab="${id}" aria-selected="${id === tab}">
        <div class="bhead"><span class="ic-chip">${icon(ic, {size: 16})}</span><div><div class="bname">${esc(BUCKET[id])}</div><div class="small muted">${esc(what)}</div></div></div>
        <div class="v">${m(vnd(have), `alloc.${id}`, {method: a.method_label})}</div>
        <div class="small muted">${sub}</div><div class="mt-xs">${tag}</div></div>`;
    }).join("")}</div>
    <div role="tabpanel" class="mt">
      ${tab === "liquidity" ? liquidity(a) : tab === "growth" ? growth(a) : legacy(a)}
      ${actions(a, tab, staff, st)}
    </div>`, "alloc-buckets");
}

// ── 04 · the what-if: the same request with ``whatif``, now and the scenario side by side ──────────────────

function scenario(a, st) {
  const liq = a.liquidity, g = a.buckets.growth.value, sc = st.sc;
  const lo = -Math.floor(liq.have / STEP) * STEP, hi = Math.floor(g / STEP) * STEP;
  const b = st.scResult;
  const pick = (x) => ({liq: x.liquidity.have, short: x.liquidity.short, g1: x.growth.rebalance.total, reach: x.retirement.reach || 0,
    rshort: x.retirement.short || 0, req: x.retirement.required, leg: x.legacy.gap});
  let result = `<p class="small muted mt">Kéo các thanh trượt rồi bấm <b>Xem tác động</b>: hệ thống tính lại cả ba mục tiêu cùng lúc.</p>`;
  if (b) {
    const p = pick(a), q = pick(b);
    // a goal now and in the scenario, and the change coloured by whether it helps (``better``: which way is good)
    const row = (label, x, y, isPct, better) => {
      const d = (y ?? 0) - (x ?? 0), same = isPct ? Math.abs(d) < 5e-4 : Math.abs(d) < 5e5;
      const show = (v) => (isPct ? (v == null ? "—" : pct(v)) : vnd(v));
      return [label, show(x), show(y), same ? `<span class="muted">không đổi</span>`
        : `<b class="${(better === "up" ? d > 0 : d < 0) ? "up" : "down"}">${isPct ? pct(d, true) : vnd(d, true)}</b>`];
    };
    const why = [];
    const moved = (b.whatif || {}).move || 0, spend = (b.whatif || {}).spending_change || 0;
    if (moved > 0) why.push(p.short > 0 && moved <= p.short
      ? `Chuyển ${vnd(moved)} sang Thanh khoản thay cho một phần khoản bán đã đề xuất (giỏ đang thiếu ${vnd(p.short)}): tự nó không làm giảm vốn đầu tư dài hạn, chỉ là thực hiện sớm một phần việc số 1.`
      : `Dự phòng tiền mặt tăng ${vnd(moved)}${q.short <= 0 ? ", Thanh khoản đủ" : ""}; đổi lại vốn đầu tư dài hạn giảm ${vnd(p.g1 - q.g1)}, nên giá trị dự kiến khi nghỉ hưu giảm ${vnd(p.reach - q.reach)}.`);
    if (moved < 0) why.push(`Đưa ${vnd(-moved)} từ Thanh khoản sang Tăng trưởng${q.short > 0 ? `: Thanh khoản thiếu ${vnd(q.short)}, nên mô hình vẫn phải bán lại phần đó để bù` : `: vốn đầu tư dài hạn tăng ${vnd(q.g1 - p.g1)}`}.`);
    if (spend) why.push(`Chi tiêu ${spend < 0 ? "giảm" : "tăng"} ${vnd(Math.abs(spend))}/tháng: nhu cầu dòng tiền, mục tiêu nghỉ hưu và phần gia đình cần đều ${spend < 0 ? "nhỏ đi" : "lớn lên"}; thiếu khi nghỉ hưu ${q.rshort < p.rshort ? "giảm" : "tăng"} ${vnd(Math.abs(p.rshort - q.rshort))}.`);
    if (b.assumptions.retirement_age !== a.assumptions.retirement_age) why.push(`Nghỉ hưu ở ${b.assumptions.retirement_age} tuổi thay vì ${a.assumptions.retirement_age}: thêm ${b.assumptions.retirement_age - a.assumptions.retirement_age} năm tích lũy, lợi suất cần ${pct(q.req)} thay vì ${pct(p.req)}.`);
    result = `<h3 class="mt">${icon("flow", {size: 16})} Kịch bản hiện tại ↔ Kịch bản đề xuất</h3>
      ${table(["Mục tiêu", "Hiện tại", "Kịch bản", "Thay đổi"], [
        row("Thanh khoản đang có", p.liq, q.liq, false, "up"), row("Thanh khoản còn thiếu", p.short, q.short, false, "down"),
        row("Vốn đầu tư dài hạn", p.g1, q.g1, false, "up"), row("Giá trị dự kiến khi nghỉ hưu", p.reach, q.reach, false, "up"),
        row("Thiếu khi nghỉ hưu", p.rshort, q.rshort, false, "down"), row("Lợi suất cần", p.req, q.req, true, "down"),
        row("Di sản thiếu (giá giữ nguyên)", p.leg, q.leg, false, "down")], "cmp")}
      ${why.length ? more("Giải thích tác động", `<ul class="small">${why.map(w => `<li data-explains>${w}</li>`).join("")}</ul>`, true) : ""}`;
  }
  return section("04", "Kịch bản", "Nếu thay đổi, kết quả sẽ ra sao?",
    "Điều chỉnh tỷ trọng tài sản, khoản chi hoặc thời gian đầu tư và xem tác động lên ba mục tiêu. Lưu kịch bản để trao đổi với chuyên viên quản lý tài sản.", `
    <form data-whatif class="whatif">
      <label class="field"><span>Chuyển giữa Tăng trưởng và Thanh khoản <b data-out="move">${sc.move ? `${sc.move > 0 ? "→ Thanh khoản" : "→ Tăng trưởng"} ${vnd(Math.abs(sc.move))}` : "Không chuyển"}</b></span>
        <input type="range" name="move" min="${lo}" max="${hi}" step="${STEP}" value="${sc.move}"><span class="small muted range-ends"><span>← Tăng trưởng</span><span>Thanh khoản →</span></span></label>
      <label class="field"><span>Thay đổi chi tiêu mỗi tháng <b data-out="spend">${sc.spend ? vnd(sc.spend, true) : "Giữ nguyên"}</b></span>
        <input type="range" name="spend" min="-30000000" max="30000000" step="1000000" value="${sc.spend}"><span class="small muted range-ends"><span>Giảm</span><span>Tăng</span></span></label>
      <label class="field"><span>Tuổi nghỉ hưu <b data-out="age">${sc.age} tuổi</b></span>
        <input type="range" name="age" min="50" max="70" step="1" value="${sc.age}"><span class="small muted range-ends"><span>50</span><span>70</span></span></label>
      <div class="row tight"><button type="submit" class="btn primary">Xem tác động</button>
        <button type="button" class="btn" data-screset>Đặt lại</button></div>
    </form>
    <div id="sc-result">${result}</div>`, "alloc-whatif");
}

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope(), staff = ctx.role !== "client";
  const st = pages[client] ||= {method: "A", tab: "liquidity", example: false, assumptions: {}, sent: null, sc: null, scResult: null};
  const body = {method: st.method, assumptions: st.assumptions, role: ctx.role};
  let a;
  try {
    a = (st.example ? await post("/api/allocation/example", body)
      : await post("/api/allocation", {client_id: client, scope, ...body})).allocation;
  } catch (e) {
    if (!Object.keys(st.assumptions).length) throw e;
    st.assumptions = {};  // a changed assumption the engine refused: back to the file's
    toast(e.message);
    return render(box, ctx);
  }
  st.sc ||= {move: 0, spend: 0, age: a.assumptions.retirement_age};
  // every asset in the three buckets, the ones an RM moved first (P2: ghi đè giỏ, the CIO sees each)
  const held = Object.entries(a.buckets).flatMap(([b, x]) => x.holdings.filter(h => h.key).map(h => ({...h, bucket: b})))
    .sort((x, y) => !!y.moved - !!x.moved);
  const moved = held.filter(h => h.moved);
  const rc = a.reconcile, bsum = Object.entries(a.buckets).map(([b, x]) => `${BUCKET[b]} ${vnd(x.value)}`).join(" + ");
  box.innerHTML = `
    <div class="pagehead"><div>
      <div class="eyebrow">Wealth Planning Advisor${a.example ? ` · Ví dụ ${esc(a.example.id)}` : ""}</div>
      <h1 class="h1">Phân bổ tài sản</h1>
      <p class="lede">Ba giỏ: tiền cần dùng, phần để lại cho gia đình, phần đầu tư cho tương lai.</p>
    </div></div>
    ${staff ? `<div class="row mt"><label class="small"><input type="checkbox" data-example ${st.example ? "checked" : ""}> Ví dụ K-7F3A</label></div>` : ""}
    ${overview(a, ctx, staff)}
    ${priorities(a)}
    ${buckets(a, st, staff)}
    ${a.example ? "" : scenario(a, st)}
    <section class="panel mt">
      ${more("Giả định và đối chiếu", table(["Khoản", "Nguồn", "Số tiền"], [
        ["Tổng tài sản", src("Mọi tài sản đã hợp nhất"), m(vnd(rc.assets), "alloc.reconcile")],
        ["Nợ", src(a.loans.items.length ? names(a.loans.items.map(l => l.name).filter(Boolean)) : "Không có"), m(vnd(rc.debts), "alloc.reconcile")],
        ["Tài sản ròng", src("Tổng tài sản trừ nợ"), m(vnd(rc.net_worth), "alloc.reconcile")],
        ["Ba giỏ cộng lại", src(esc(bsum) + " (giá trị ghi sổ, trước khi trừ nợ thế chấp)"), m(vnd(rc.buckets), "alloc.reconcile")]])
        + `<h3 class="mt">Giả định</h3><form data-assume class="simform">${Object.entries(EDIT).map(([k, [unit, f]]) => `
        <label class="field"><span><span>${esc(a.assumption_labels[k] || k)}</span> <span class="muted">${esc(unit)}</span></span>
        <input type="number" step="any" name="${k}" value="${shown(a.assumptions[k], f)}"></label>`).join("")}
        <button type="submit" class="btn primary">Tính lại</button>
        ${Object.keys(st.assumptions).length ? `<button type="button" class="btn" data-reset>Về mặc định</button>` : ""}</form>`)}
      ${staff && !a.example ? more("Chuyển tài sản sang giỏ khác", `${moved.length ? table(["Tài sản", "Giỏ", "Lý do"], moved.map(h =>
        [esc(h.name), esc(BUCKET[h.moved.bucket]), `<span data-explains>${esc(h.moved.reason)}</span>`])) : ""}
        <form data-override class="simform">
          <label class="field"><span>Tài sản</span><select name="key">${held.map(h =>
            `<option value="${esc(h.key)}">${esc(h.name)} · ${esc(BUCKET[h.bucket])}</option>`).join("")}</select></label>
          <label class="field"><span>Sang giỏ</span><select name="bucket">${Object.entries(BUCKET).map(([k, v]) =>
            `<option value="${k}">${esc(v)}</option>`).join("")}<option value="">Về giỏ mặc định</option></select></label>
          <label class="field"><span>Lý do</span><input name="reason" placeholder="Ít nhất 10 ký tự"></label>
          <button type="submit" class="btn primary">Chuyển</button></form>
        <p class="small muted">CIO thấy mọi lần chuyển cùng lý do.</p>`) : ""}
    </section>`;

  const host = $("#alloc-cash", box);
  if (host && host.clientWidth) host.replaceChildren(cashflow(months(a.cashflow), a.cashflow.dated, host.clientWidth));
  const openTab = (t) => { if (st.tab !== t) { st.tab = t; render(box, ctx); } };
  box.querySelectorAll("[data-tab]").forEach(b => {
    b.onclick = (e) => { if (!e.target.closest(".how-n")) openTab(b.dataset.tab); };  // a figure opens its formula, not the tab
    b.onkeydown = (e) => { if ((e.key === "Enter" || e.key === " ") && e.target === b) { e.preventDefault(); openTab(b.dataset.tab); } };
  });
  box.querySelectorAll("[data-goto]").forEach(li => {  // a priority opens its bucket's tab and scrolls to it
    const go = (e) => {
      if (e.target.closest(".how-n, a")) return;
      st.tab = li.dataset.goto;
      render(box, ctx).then(() => $("#alloc-buckets", box)?.scrollIntoView({behavior: "smooth", block: "start"}));
    };
    li.onclick = go;
    li.onkeydown = (e) => { if (e.key === "Enter") go(e); };
  });
  box.querySelectorAll("[data-method]").forEach(b => b.onclick = () => { st.method = b.dataset.method; st.scResult = null; render(box, ctx); });
  const ex = $("[data-example]", box);
  if (ex) ex.onchange = () => { st.example = ex.checked; st.assumptions = {}; st.scResult = null; render(box, ctx); };
  const wf = $("[data-whatif]", box);
  if (wf) {
    const say = () => {
      const f = wf.elements, mv = +f.move.value, sp = +f.spend.value;
      $("[data-out=move]", wf).textContent = mv ? `${mv > 0 ? "→ Thanh khoản" : "→ Tăng trưởng"} ${vnd(Math.abs(mv))}` : "Không chuyển";
      $("[data-out=spend]", wf).textContent = sp ? vnd(sp, true) : "Giữ nguyên";
      $("[data-out=age]", wf).textContent = `${f.age.value} tuổi`;
    };
    wf.oninput = say;
    wf.onsubmit = async (e) => {
      e.preventDefault();
      const f = wf.elements;
      st.sc = {move: +f.move.value, spend: +f.spend.value, age: +f.age.value};
      const btn = wf.querySelector("[type=submit]");
      btn.disabled = true;
      try {
        const age = st.sc.age !== a.assumptions.retirement_age ? {retirement_age: st.sc.age} : {};
        st.scResult = (await post("/api/allocation", {client_id: client, scope, method: st.method, role: ctx.role,
          assumptions: {...st.assumptions, ...age}, whatif: {move: st.sc.move, spending_change: st.sc.spend}})).allocation;
        render(box, ctx).then(() => $("#sc-result", box)?.scrollIntoView({behavior: "smooth", block: "nearest"}));
      } catch (err) { btn.disabled = false; toast(err.message); }
    };
    $("[data-screset]", wf).onclick = () => { st.sc = null; st.scResult = null; render(box, ctx); };
  }
  $("[data-assume]", box).onsubmit = (e) => {
    e.preventDefault();
    const out = {};
    for (const [k, [, f]] of Object.entries(EDIT)) {
      const v = parseFloat(e.target.elements[k].value);
      if (!Number.isNaN(v) && v !== shown(a.assumptions[k], f)) out[k] = v * f;  // an untouched field is not a change
    }
    st.assumptions = {...st.assumptions, ...out};
    st.sc = null;
    st.scResult = null;
    render(box, ctx);
  };
  const reset = $("[data-reset]", box);
  if (reset) reset.onclick = () => { st.assumptions = {}; st.sc = null; st.scResult = null; render(box, ctx); };
  const over = $("[data-override]", box);
  if (over) over.onsubmit = async (e) => {
    e.preventDefault();
    const f = e.target.elements;
    try {
      await post("/api/allocation/override", {client_id: client, scope, key: f.key.value, bucket: f.bucket.value,
        reason: f.reason.value.trim(), by: ctx.user});
      e.target.reset();
      toast("Đã chuyển giỏ");
      st.scResult = null;
      render(box, ctx);
    } catch (err) { toast(err.message); }
  };
  const send = $("[data-send]", box);
  if (send) send.onclick = async () => {
    send.disabled = true;
    try {
      const r = await post("/api/allocation/send", {client_id: client, scope, method: st.method, assumptions: st.assumptions, by: ctx.user});
      st.sent = r.review_id;
      toast("Đã gửi vào hàng duyệt");
      render(box, ctx);
    } catch (e) { send.disabled = false; toast(e.message); }
  };
}
