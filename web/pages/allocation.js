/* Phân bổ tài sản — the three buckets (ASSET_ALLOCATION_BRD, SCR-CL-13): Liquidity, Legacy and Growth, each with its
   target, what is there and the gap (POST /api/allocation). On top a short profile of the client (age, children, the
   large plans, income, retirement, the risk test's tolerance, capacity and drawdown limit). The three buckets are the
   page's tabs (feedback Chỉnh UI-UX); each tab shows how it is counted first — every figure with where it comes from,
   one table and, for Liquidity, the cash-flow chart with the two ways to count income side by side — then the changes
   to consider for that bucket with their suitability check (a blocked one only on staff screens). Shared below: the
   assumptions (edit and run again), the reconciliation, and for staff the bucket moves. The worked example K-7F3A
   (POST /api/allocation/example); an RM sends the actions to the review queue (POST /api/allocation/send). P2: the
   household by the 11 asset classes; an RM moves an asset to another bucket with a reason (POST
   /api/allocation/override), which the CIO reads on #/cio/phan-bo. */
import {$, esc, n as how, pct, post, toast, vnd} from "../core/core.js";
import {cashflow} from "../charts/money.js?v=20261016r4";

const CHECK = {PASS: ["good", "Phù hợp"], WARN: ["warn", "Cần lưu ý"], BLOCK: ["bad", "Bị chặn"]};
const BUCKET = {liquidity: "Thanh khoản", legacy: "Di sản", growth: "Tăng trưởng"};
const TABS = ["liquidity", "growth", "legacy"];
// which actions each tab lists: the loans sit with Liquidity (they cost cash each month), retirement with Growth
const TAB_ACTS = {liquidity: ["liquidity", "loans"], growth: ["growth", "retirement"], legacy: ["legacy"]};
// the assumptions a person may change: [unit shown, factor to the engine's number]
const EDIT = {horizon_years: ["năm", 1], buffer_months: ["tháng", 1], inflation: ["%", 0.01], retirement_age: ["tuổi", 1],
  legacy_wish: ["tỷ", 1e9], survivor_share: ["%", 0.01]};
const SIM = "Hồ sơ giả lập";  // every action's warning when the level is simulated: said once, in the notice
const pages = {};  // per client, for this page's life: the method, the tab, the example toggle, the assumptions changed

// an assumption as the form shows it: a share in percent to one decimal (⅔ → 66.7), any other number to two
const shown = (x, f) => +(x / f).toFixed(f < 1 ? 1 : 2);
const pill = (c) => `<span class="pill ${CHECK[c.status][0]}">${CHECK[c.status][1]}</span>`;
// every figure opens its formula (BRD-NFR-11): alloc.* in src/explain/metrics.py
const m = how;
const gap = (short, over) => (short > 0 ? `<span class="pill warn">Thiếu ${m(vnd(short), "alloc.liquidity")}</span>`
  : over > 0 ? `<span class="pill ai">Dư ${m(vnd(over), "alloc.liquidity")}</span>` : `<span class="pill good">Đủ</span>`);
const range = (a, b, metric) => m(b && Math.round(b) !== Math.round(a) ? `${vnd(a)}–${vnd(b)}` : vnd(a), metric);
const ym = (s) => (s ? `${s.slice(5, 7)}/${s.slice(0, 4)}` : "");
const more = (title, body) => `<details class="more mt"><summary>${esc(title)}</summary>${body}</details>`;
const table = (head, rows) => `<div class="scrollx"><table class="table"><thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead>
  <tbody>${rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
const src = (s) => `<span class="small muted" data-explains>${s}</span>`;  // where a figure comes from: a few words, no formula
const names = (xs, k = 3) => esc(xs.slice(0, k).join(", ")) + (xs.length > k ? ` +${xs.length - k}` : "");

// the client in a few lines: who, the children, the large plans, money a month, retirement, risk (feedback Chỉnh UI-UX)
function profile(a, ctx, staff) {
  const c = a.client || {}, r = a.risk, s = a.assumptions;
  const kids = (c.dependents || []).map(d => `${esc(d.name || d.relation || "Con")}${d.age != null ? ` (${d.age} tuổi)` : ""}`);
  const plans = (c.plans || []).map(p => `${esc(p.label)} · ${ym(p.date)} · ${vnd(p.amount)}`);
  const early = c.age && s.retirement_age < 60;
  const cells = [
    ["Khách hàng", `${esc(c.name || "")}${c.age ? ` · ${c.age} tuổi` : ""}`, esc([c.occupation, c.segment].filter(Boolean).join(" · "))],
    ["Con", kids.length ? kids.join(", ") : "Không khai", ""],
    ["Kế hoạch lớn", plans.length ? plans.slice(0, 2).join("<br>") : "Chưa có", plans.length > 2 ? `+${plans.length - 2} khoản khác` : ""],
    ["Thu nhập / chi tiêu", `${vnd(c.income_monthly)} / ${vnd(c.spending_monthly)} mỗi tháng`, `Chắc chắn ${vnd(c.income_certain_monthly)}/tháng`],
    ["Nghỉ hưu", `${s.retirement_age} tuổi${c.retirement_year ? ` · năm ${c.retirement_year}` : ""}`, early ? "Nghỉ hưu sớm" : ""],
    ["Khẩu vị rủi ro", esc(r.tolerance || r.name), `Mức ${r.level}/5 · hồ sơ ${esc(r.name)}`],
    ["Khả năng chịu rủi ro", esc(r.capacity || r.name), ""],
    ["Ngưỡng sụt giảm chịu được", r.drawdown_limit != null ? pct(r.drawdown_limit, false, 0) : "—", "của danh mục"],
  ];
  const test = ctx.role === "client" ? "#/client/muc-tieu/khau-vi" : ctx.href("khach-hang", "ke-hoach");
  return `<section class="panel mt"><h2 class="panel-title">Hồ sơ khách hàng</h2>
    <div class="who">${cells.map(([k, v, sub]) => `<div><div class="k">${esc(k)}</div><div class="v">${v}</div>${sub ? `<div class="small muted">${sub}</div>` : ""}</div>`).join("")}</div>
    <p class="small muted mt">${r.source === "simulated"
      ? `Mức rủi ro ${r.level} (${esc(r.name)}) là giả lập từ hồ sơ, nên mọi việc dưới đây đều cần lưu ý. <a href="${test}">${staff ? "Mời khách làm bài test" : "Làm bài test rủi ro"}</a>`
      : `Theo bài test rủi ro${r.at ? ` ngày ${esc(r.at)}` : ""}.`}</p></section>`;
}

// Liquidity: the two ways to count income side by side, the cash flow month by month, every line with its source
function liquidity(a, st) {
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
  const lines = [
    ["Thu nhập", src(`Thu nhập trong hồ sơ ${vnd(cf.income_monthly)}/tháng; chắc chắn ${vnd(cf.income_certain_monthly)}/tháng (lương, lương hưu, tiền thuê 12 tháng qua)`),
      `${n} tháng`, cf.income_monthly * n],
    ["Chi tiêu sinh hoạt", src(`Chi tiêu hằng tháng trong hồ sơ ${vnd(cf.living_monthly)}/tháng`), `${n} tháng`, -cf.living_monthly * n],
    ...(cf.debt_service_monthly ? [["Trả nợ vay", src(`${loans.length ? esc(loans.join(", ")) + " · " : ""}${vnd(cf.debt_service_monthly)}/tháng theo hợp đồng`),
      `${n} tháng`, -cf.debt_service_monthly * n]] : []),
    ...cf.dated.map(d => [esc(d.label), src(d.label.startsWith("Trả gốc") ? "Hợp đồng vay: trả gốc cuối kỳ" : "Khoản chi đã lên lịch trong hồ sơ"), ym(d.month), -d.amount]),
  ];
  const net = lines.reduce((t, l) => t + l[3], 0);
  const sum = `<p class="small muted">${[`Đáy dòng tiền ${ym(cf.trough.month)}: ${m(vnd(cf.trough.cum, true), "alloc.cashflow")}`,
    `Đệm ${cf.buffer_months} tháng chi: ${m(vnd(cf.buffer), "alloc.cashflow")}`,
    `Lãi vay +${m(pct(cf.rate_shock.pp, false, 0), "alloc.cashflow")}: thêm ${m(vnd(cf.rate_shock.monthly), "alloc.cashflow")}/tháng`].map(x => `<span>${x}</span>`).join(" · ")}</p>`;
  return `<section class="panel mt"><h2 class="panel-title">Cách tính</h2>
    <div class="ways">
      ${way("B", "Tính đủ thu nhập", `Lấy đáy dòng tiền ${cf.horizon_years} năm khi vẫn có thu nhập, cộng đệm ${cf.buffer_months} tháng chi`, ["C"])}
      ${way("A", "Không tính thu nhập", `Mọi khoản chi ${cf.horizon_years} năm tới, như khi không còn thu nhập`)}
    </div>
    <h3 class="mt">Dòng tiền ${cf.horizon_years} năm tới <span class="hint">di chuột vào từng tháng để xem các khoản</span></h3>
    <div id="alloc-cash" class="mt-xs"></div>
    ${table(["Khoản", "Nguồn", "Khi nào", "Số tiền"], [...lines.map(([k, s, w, v]) => [k, s, esc(w), m(vnd(v, true), "alloc.cashflow")]),
      ["<b>Ròng</b>", src("Thu nhập trừ mọi khoản chi"), esc(`${ym(cf.months[0].month)}–${ym(cf.months[n - 1].month)}`), `<b>${m(vnd(net, true), "alloc.cashflow")}</b>`]])}
    ${sum}
    ${more("Bậc thang Thanh khoản", table(["Khoản", "Dùng cho", "Số tiền"], liq.ladder.map(r => [esc(r.what), esc(r.when), m(vnd(r.amount), "alloc.ladder")])))}
    ${more("Cách bù phần thiếu", table(["Cách bù", "Chi phí", "Được?", "Vì sao"], a.fill.options.map(o =>
      [esc(o.label), `<span data-explains>${esc(o.cost || "")}</span>`, o.id === a.fill.chosen ? `<span class="pill good">Đã chọn</span>` : o.ok ? "Có" : "Không", `<span data-explains>${esc(o.why)}</span>`])))}
  </section>`;
}

// the months of the table as the chart's columns: income above, every cost below, the dated payments named in the tip
function months(cf) {
  return cf.months.map(x => {
    const dated = cf.dated.filter(d => d.month === x.month);
    const items = [{direction: "in", label: "Thu nhập", amount: cf.income_monthly}, {direction: "out", label: "Chi tiêu sinh hoạt", amount: cf.living_monthly},
      ...(cf.debt_service_monthly ? [{direction: "out", label: "Trả nợ vay", amount: cf.debt_service_monthly}] : []),
      ...dated.map(d => ({direction: "out", label: d.label, amount: d.amount}))];
    const out = cf.recurring_monthly + x.dated;
    return {month: x.month, in: cf.income_monthly, out, net: cf.income_monthly - out, items: items.filter(i => i.amount > 0)};
  });
}

// Growth: the retirement goal as one table with sources, the model's rebalance, the eleven classes
function growth(a) {
  const ret = a.retirement, gr = a.growth, s = a.assumptions, c = a.client || {};
  const rows = ret.status === "retired" ? [["Nghỉ hưu", "Đã nghỉ", src(`Tuổi nghỉ hưu ${s.retirement_age} (giả định) · nay ${c.age} tuổi`)]] : [
    ["Năm nghỉ", String(ret.year), src(`Tuổi nghỉ hưu ${s.retirement_age} (giả định) · nay ${c.age} tuổi · còn ${ret.years} năm`)],
    ["Cần khi nghỉ", m(vnd(ret.need), "alloc.retirement"), src(`Chi tiêu nay ${vnd(ret.spend_now)}/năm, tăng theo lạm phát ${pct(s.inflation, false, 0)}/năm, × ${s.withdraw_multiple} năm chi`)],
    ["Dự kiến đạt", m(vnd(ret.reach), "alloc.retirement"), src(`Giỏ Tăng trưởng ${vnd(gr.rebalance.total)} + tiết kiệm ${vnd(ret.saving_yearly)}/năm × ${ret.saving_years} năm, lợi nhuận mô hình ${pct(ret.expected)}`)],
    ["Lợi nhuận cần", ret.required != null ? `${m(pct(ret.required), "alloc.retirement")}/năm` : "Trên 30%/năm", src("Mức lợi nhuận để phần dự kiến đạt bằng phần cần")],
    ...(ret.status === "short" ? [
      ["Thiếu", `<b>${m(vnd(ret.short), "alloc.retirement")}</b>`, src("Cần khi nghỉ trừ dự kiến đạt")],
      ["Tiết kiệm thêm", `${m(vnd(ret.extra_monthly), "alloc.retirement")}/tháng`, src(`Để bù phần thiếu trong ${ret.saving_years} năm, cùng lợi nhuận mô hình`)],
      ["Hoặc nghỉ muộn", ret.delay.enough ? `${ret.delay.enough} năm` : "Lùi 10 năm vẫn chưa đủ", src("Giữ nguyên tiết kiệm, lùi năm nghỉ")]] : []),
  ];
  return `<section class="panel mt"><h2 class="panel-title">Cách tính</h2>
    <h3>Nghỉ hưu</h3>
    ${table(["Khoản", "Số tiền", "Nguồn"], rows)}
    <h3 class="mt">Mô hình Tăng trưởng <span class="hint">mức rủi ro ${a.risk.level} · ${esc(a.risk.name)}</span></h3>
    ${table(["Loại", "Hiện tại", "Tỷ trọng mục tiêu", "Mua / bán", "Nhận định"], gr.rebalance.rows.map(r =>
      [esc(r.label), m(pct(r.now_pct), "alloc.rebalance"), `${m(pct(r.target_pct), "alloc.rebalance")}${r.tilt ? ` <span class="small muted">(${m(pct(r.tilt, true, 0), "alloc.rebalance")})</span>` : ""}`, m(vnd(r.trade, true), "alloc.rebalance"), esc((r.views || []).join(", "))]))}
    <p class="small muted">Lỗ khi thị trường xấu: trước ${m(pct(gr.worst_before.share), "alloc.worst")} · sau ${m(pct(gr.worst_after.share), "alloc.worst")}</p>
    ${more("Theo 11 loại tài sản", table(["Loại", "Đang có", "Trong Tăng trưởng", "Mức mục tiêu"], a.eleven.rows.map(r =>
      [esc(r.label) + (r.loan ? ` <span class="chip">Khoản vay</span>` : ""), m(vnd(r.value), "alloc.eleven"), m(vnd(r.in_growth), "alloc.eleven"),
        r.target == null ? `<span class="muted">—</span>` : `${m(vnd(r.target), "alloc.eleven")} <span class="small muted">(${m(pct(r.target_pct), "alloc.eleven")})</span>`]))
      + `<p class="small muted">Ngoài 11 loại (tiền VND, tiền gửi, quỹ tiền tệ, bảo hiểm): ${m(vnd(a.eleven.outside), "alloc.eleven")}</p>`)}
  </section>`;
}

// Legacy: what the family would need, what is there, and how to fill the gap, as one table with sources
function legacy(a) {
  const leg = a.legacy, loans = a.loans.items.map(l => l.name).filter(Boolean);
  const held = a.buckets.legacy.holdings.map(h => h.name).filter(Boolean);
  const rows = [
    ...leg.floor_rows.map(r => [esc(r.label), src(r.how ? esc(r.how) : loans.length ? esc(loans.join(", ")) : "Các khoản vay đang có"), m(vnd(r.amount), "alloc.legacy")]),
    ["<b>Sàn Di sản</b>", src("Cộng ba khoản trên"), `<b>${m(vnd(leg.floor), "alloc.legacy")}</b>`],
    ...(leg.wish ? [["Mong muốn để lại", src("Khách hàng khai"), m(vnd(leg.wish), "alloc.legacy")]] : []),
    ["Đang có", src([held.length ? names(held) : "Tài sản giỏ Di sản", leg.secured ? `trừ nợ thế chấp ${vnd(leg.secured)}` : "",
      leg.insured ? `cộng bảo hiểm có người thụ hưởng ${vnd(leg.insured)}` : ""].filter(Boolean).join(" · ")), range(leg.have_low, leg.have, "alloc.legacy")],
    ...(leg.drop ? [["Nếu giá bất động sản giảm", src(esc(leg.drop.note || "giả định")), m(pct(leg.drop.drop, false, 0), "alloc.legacy")]] : []),
    [leg.gap > 0 ? "<b>Thiếu</b>" : "<b>Đủ</b>", src(`Mục tiêu ${vnd(leg.target)} trừ phần đang có`), leg.gap > 0 ? `<b>${range(leg.gap, leg.gap_high, "alloc.legacy")}</b>` : `<span class="pill good">Đủ</span>`],
  ];
  return `<section class="panel mt"><h2 class="panel-title">Cách tính</h2>
    ${table(["Khoản", "Nguồn / cách tính", "Số tiền"], rows)}
    <p class="small muted" data-explains>Cách bù: ${esc(leg.fill_with)}</p></section>`;
}

function actions(a, tab, staff, st) {
  const acts = a.actions.filter(x => TAB_ACTS[tab].includes(x.bucket));
  return `<section class="panel mt">
    <h2 class="panel-title">Cân nhắc thay đổi</h2>
    ${acts.length ? `<ol class="alloc-acts" style="margin:0;padding-left:20px;display:grid;gap:10px">${acts.map(x => `
      <li><div class="row" style="gap:8px;flex-wrap:wrap;align-items:baseline">
        <strong>${esc(x.what)}</strong>${x.amount ? `<span>${range(x.amount, x.amount_high, "alloc.action")}</span>` : ""}
        <span class="chip">${esc(x.bucket_label)}</span>${pill(x.check)}</div>
        <div class="small muted" data-explains>${esc(x.why)}</div>
        ${x.check.reasons.filter(r => r !== SIM).map(r => `<div class="small" data-explains>${esc(r)}</div>`).join("")}</li>`).join("")}
    </ol>` : `<p class="muted">Không có thay đổi nào cần cân nhắc ở giỏ này.</p>`}
    ${staff && !a.example ? `<div class="row mt" style="gap:12px;align-items:center">
      <button type="button" class="btn primary" data-send ${st.sent ? "disabled" : ""}>Gửi vào hàng duyệt</button>
      <span class="small muted">${st.sent ? `Đã gửi ${esc(st.sent)}` : `Gửi cả ${a.actions.length} thay đổi của ba giỏ`}</span></div>` : ""}
  </section>`;
}

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope(), staff = ctx.role !== "client";
  const st = pages[client] ||= {method: "A", tab: "liquidity", example: false, assumptions: {}, sent: null};
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
  const liq = a.liquidity, leg = a.legacy, ret = a.retirement, gr = a.growth;
  const tiles = {
    liquidity: [liq.have, liq.target, esc(a.method_label), gap(liq.short, liq.excess)],
    legacy: [leg.have, leg.target, `Sàn ${m(vnd(leg.floor), "alloc.legacy")}`, leg.gap > 0 ? `<span class="pill warn">Thiếu ${range(leg.gap, leg.gap_high, "alloc.legacy")}</span>` : `<span class="pill good">Đủ</span>`],
    growth: [a.buckets.growth.value, null, `Cần ${m(pct(ret.required), "alloc.retirement")}/năm · mô hình ${m(pct(gr.expected), "alloc.growth")}`,
      ret.status === "short" ? `<span class="pill warn">Thiếu ${m(vnd(ret.short), "alloc.retirement")} khi nghỉ hưu</span>` : `<span class="pill good">Đủ cho nghỉ hưu</span>`],
  };
  // every asset in the three buckets, the ones an RM moved first (P2: ghi đè giỏ, the CIO sees each)
  const held = Object.entries(a.buckets).flatMap(([b, x]) => x.holdings.filter(h => h.key).map(h => ({...h, bucket: b})))
    .sort((x, y) => !!y.moved - !!x.moved);
  const moved = held.filter(h => h.moved);
  const rc = a.reconcile, bsum = Object.entries(a.buckets).map(([b, x]) => `${BUCKET[b]} ${vnd(x.value)}`).join(" + ");
  const tab = st.tab;
  box.innerHTML = `
    <div class="pagehead"><div>
      <div class="eyebrow">Wealth Planning Advisor${a.example ? ` · Ví dụ ${esc(a.example.id)}` : ""}</div>
      <h1 class="h1">Phân bổ tài sản</h1>
      <p class="lede">Ba giỏ: tiền cần dùng, phần để lại cho gia đình, phần đầu tư cho tương lai.</p>
    </div></div>
    ${staff ? `<div class="row mt"><label class="small"><input type="checkbox" data-example ${st.example ? "checked" : ""}> Ví dụ K-7F3A</label></div>` : ""}
    ${profile(a, ctx, staff)}
    <div class="btabs mt" role="tablist" aria-label="Ba giỏ">${TABS.map(id => {
      const [have, target, sub, tag] = tiles[id];
      return `<div class="kpi" role="tab" tabindex="0" data-tab="${id}" aria-selected="${id === tab}">
        <div class="k">${esc(BUCKET[id])}</div>
        <div class="v">${m(vnd(have), `alloc.${id}`, {method: a.method_label})}</div>
        <div class="small muted">${target != null ? `Cần ${m(vnd(target), `alloc.${id}`, {method: a.method_label})} · ` : ""}${sub}</div>
        <div class="mt">${tag}</div></div>`;
    }).join("")}</div>
    <div role="tabpanel">
      ${tab === "liquidity" ? liquidity(a, st) : tab === "growth" ? growth(a) : legacy(a)}
      ${actions(a, tab, staff, st)}
    </div>
    <section class="panel mt">
      <h2 class="panel-title">Giả định và đối chiếu</h2>
      ${table(["Khoản", "Nguồn", "Số tiền"], [
        ["Tổng tài sản", src("Mọi tài sản đã hợp nhất"), m(vnd(rc.assets), "alloc.reconcile")],
        ["Nợ", src(a.loans.items.length ? names(a.loans.items.map(l => l.name).filter(Boolean)) : "Không có"), m(vnd(rc.debts), "alloc.reconcile")],
        ["Tài sản ròng", src("Tổng tài sản trừ nợ"), m(vnd(rc.net_worth), "alloc.reconcile")],
        ["Ba giỏ cộng lại", src(esc(bsum)), m(vnd(rc.buckets), "alloc.reconcile")]])}
      ${more("Giả định", `<form data-assume class="simform">${Object.entries(EDIT).map(([k, [unit, f]]) => `
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
  box.querySelectorAll("[data-tab]").forEach(b => {
    const open = () => { if (st.tab !== b.dataset.tab) { st.tab = b.dataset.tab; render(box, ctx); } };
    b.onclick = (e) => { if (!e.target.closest(".how-n")) open(); };  // a figure opens its formula, not the tab
    b.onkeydown = (e) => { if ((e.key === "Enter" || e.key === " ") && e.target === b) { e.preventDefault(); open(); } };
  });
  box.querySelectorAll("[data-method]").forEach(b => b.onclick = () => { st.method = b.dataset.method; render(box, ctx); });
  const ex = $("[data-example]", box);
  if (ex) ex.onchange = () => { st.example = ex.checked; st.assumptions = {}; render(box, ctx); };
  $("[data-assume]", box).onsubmit = (e) => {
    e.preventDefault();
    const out = {};
    for (const [k, [, f]] of Object.entries(EDIT)) {
      const v = parseFloat(e.target.elements[k].value);
      if (!Number.isNaN(v) && v !== shown(a.assumptions[k], f)) out[k] = v * f;  // an untouched field is not a change
    }
    st.assumptions = {...st.assumptions, ...out};
    render(box, ctx);
  };
  const reset = $("[data-reset]", box);
  if (reset) reset.onclick = () => { st.assumptions = {}; render(box, ctx); };
  const over = $("[data-override]", box);
  if (over) over.onsubmit = async (e) => {
    e.preventDefault();
    const f = e.target.elements;
    try {
      await post("/api/allocation/override", {client_id: client, scope, key: f.key.value, bucket: f.bucket.value,
        reason: f.reason.value.trim(), by: ctx.user});
      e.target.reset();
      toast("Đã chuyển giỏ");
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
