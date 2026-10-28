/* Phân bổ tài sản — the three buckets (ASSET_ALLOCATION_BRD, SCR-CL-13): Liquidity, Legacy and Growth, each with its
   target, what is there and the gap (POST /api/allocation); the cash-flow method A/B/C; the numbered actions with their
   suitability check (a blocked one only on staff screens); the workings in collapsed zones; the assumptions (edit and
   run again); the worked example K-7F3A (POST /api/allocation/example); an RM sends the actions to the review queue
   (POST /api/allocation/send). */
import {$, esc, pct, post, toast, vnd} from "../core/core.js";

const CHECK = {PASS: ["good", "Phù hợp"], WARN: ["warn", "Cần lưu ý"], BLOCK: ["bad", "Bị chặn"]};
const BUCKET = {liquidity: "Thanh khoản", legacy: "Di sản", growth: "Tăng trưởng"};
// the assumptions a person may change: [unit shown, factor to the engine's number]
const EDIT = {horizon_years: ["năm", 1], buffer_months: ["tháng", 1], inflation: ["%", 0.01], retirement_age: ["tuổi", 1],
  legacy_wish: ["tỷ", 1e9], survivor_share: ["%", 0.01]};
const SIM = "Hồ sơ giả lập";  // every action's warning when the level is simulated: said once, in the notice
const pages = {};  // per client, for this page's life: the method, the example toggle, the assumptions changed

// an assumption as the form shows it: a share in percent to one decimal (⅔ → 66.7), any other number to two
const shown = (x, f) => +(x / f).toFixed(f < 1 ? 1 : 2);
const pill = (c) => `<span class="pill ${CHECK[c.status][0]}">${CHECK[c.status][1]}</span>`;
const gap = (short, over) => (short > 0 ? `<span class="pill warn">Thiếu ${vnd(short)}</span>`
  : over > 0 ? `<span class="pill ai">Dư ${vnd(over)}</span>` : `<span class="pill good">Đủ</span>`);
const range = (a, b) => (b && Math.round(b) !== Math.round(a) ? `${vnd(a)}–${vnd(b)}` : vnd(a));
const ym = (s) => (s ? `${s.slice(5, 7)}/${s.slice(0, 4)}` : "");
const more = (title, body) => `<details class="more mt"><summary>${esc(title)}</summary>${body}</details>`;
const kvs = (pairs) => pairs.map(([k, v]) => `<div class="kv"><span>${esc(k)}</span><b>${v}</b></div>`).join("");
const table = (head, rows) => `<div class="scrollx"><table class="table"><thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead>
  <tbody>${rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope(), staff = ctx.role !== "client";
  const st = pages[client] ||= {method: "A", example: false, assumptions: {}, sent: null};
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
  const liq = a.liquidity, leg = a.legacy, ret = a.retirement, gr = a.growth, cf = a.cashflow;
  const tiles = [
    ["liquidity", liq.have, liq.target, `${a.method_label}`, gap(liq.short, liq.excess)],
    ["legacy", leg.have, leg.target, `Sàn ${vnd(leg.floor)}`, leg.gap > 0 ? `<span class="pill warn">Thiếu ${range(leg.gap, leg.gap_high)}</span>` : `<span class="pill good">Đủ</span>`],
    ["growth", a.buckets.growth.value, null, `Cần ${pct(ret.required)}/năm · mô hình ${pct(gr.expected)}`,
      ret.status === "short" ? `<span class="pill warn">Thiếu ${vnd(ret.short)} khi nghỉ hưu</span>` : `<span class="pill good">Đủ cho nghỉ hưu</span>`],
  ];
  const acts = a.actions;
  box.innerHTML = `
    <div class="pagehead"><div>
      <div class="eyebrow">Wealth Planning Advisor${a.example ? ` · Ví dụ ${esc(a.example.id)}` : ""}</div>
      <h1 class="h1">Phân bổ tài sản</h1>
      <p class="lede">Ba giỏ: tiền cần dùng, phần để lại cho gia đình, phần đầu tư cho tương lai.</p>
    </div></div>
    <div class="row mt" style="gap:12px;flex-wrap:wrap;align-items:center">
      <div class="seg" role="group" aria-label="Cách tính">${Object.entries(a.methods).map(([k, v]) =>
        `<button type="button" data-method="${k}" aria-pressed="${k === a.method}" title="${esc(v)}">${esc(v)}</button>`).join("")}</div>
      ${staff ? `<label class="small"><input type="checkbox" data-example ${st.example ? "checked" : ""}> Ví dụ K-7F3A</label>` : ""}
    </div>
    ${a.risk.source === "simulated" ? `<p class="notice mt">Mức rủi ro ${a.risk.level} (${esc(a.risk.name)}) là giả lập, nên mọi việc dưới đây đều cần lưu ý.
      <a href="${ctx.role === "client" ? "#/client/muc-tieu/khau-vi" : ctx.href("khach-hang", "ke-hoach")}">${staff ? "Mời khách làm bài test" : "Làm bài test rủi ro"}</a></p>` : ""}
    <div class="kpis mt" style="grid-template-columns:repeat(auto-fit,minmax(220px,1fr))">${tiles.map(([id, have, target, sub, tag]) => `
      <div class="kpi"><div class="k">${esc(BUCKET[id])}</div>
        <div class="v">${vnd(have)}</div>
        <div class="small muted">${target != null ? `Cần ${vnd(target)} · ` : ""}${esc(sub)}</div>
        <div class="mt">${tag}</div></div>`).join("")}
    </div>
    <section class="panel mt">
      <h2 class="panel-title">Việc nên trao đổi</h2>
      <ol class="alloc-acts" style="margin:0;padding-left:20px;display:grid;gap:10px">${acts.map(x => `
        <li><div class="row" style="gap:8px;flex-wrap:wrap;align-items:baseline">
          <strong>${esc(x.what)}</strong>${x.amount ? `<span>${range(x.amount, x.amount_high)}</span>` : ""}
          <span class="chip">${esc(x.bucket_label)}</span>${pill(x.check)}</div>
          <div class="small muted">${esc(x.why)}</div>
          ${x.check.reasons.filter(r => r !== SIM).map(r => `<div class="small">${esc(r)}</div>`).join("")}</li>`).join("")}
      </ol>
      ${staff && !a.example ? `<div class="row mt" style="gap:12px;align-items:center">
        <button type="button" class="btn primary" data-send ${st.sent ? "disabled" : ""}>Gửi vào hàng duyệt</button>
        ${st.sent ? `<span class="small muted">Đã gửi ${esc(st.sent)}</span>` : ""}</div>` : ""}
    </section>
    <section class="panel mt">
      <h2 class="panel-title">Cách tính</h2>
      ${more("Dòng tiền " + cf.horizon_years + " năm", table(["Năm", "Thu", "Chi đều", "Khoản lớn", "Ròng"],
        cf.years.map(y => [`${ym(y.from)}–${ym(y.to)}`, vnd(y.income), vnd(y.recurring), vnd(y.dated), vnd(y.net, true)]))
        + `<p class="small muted">${[`Đáy dòng tiền ${ym(cf.trough.month)}: ${vnd(cf.trough.cum, true)}`, `Đệm ${cf.buffer_months} tháng: ${vnd(cf.buffer)}`,
          `Lãi vay +${pct(cf.rate_shock.pp, false, 0)}: thêm ${vnd(cf.rate_shock.monthly)}/tháng`].join(" · ")}</p>`
        + table(["Cách tính", "Giỏ Thanh khoản cần"], Object.entries(cf.targets).map(([k, v]) => [esc(a.methods[k]), vnd(v)])))}
      ${more("Bậc thang Thanh khoản", table(["Khoản", "Dùng cho", "Số tiền"], liq.ladder.map(r => [esc(r.what), esc(r.when), vnd(r.amount)])))}
      ${more("Cách bù phần thiếu", table(["Cách bù", "Chi phí", "Được?", "Vì sao"], a.fill.options.map(o =>
        [esc(o.label), esc(o.cost || ""), o.id === a.fill.chosen ? `<span class="pill good">Đã chọn</span>` : o.ok ? "Có" : "Không", esc(o.why)])))}
      ${more("Mô hình Tăng trưởng", table(["Loại", "Hiện tại", "Tỷ trọng mục tiêu", "Mua / bán", "Nhận định"], gr.rebalance.rows.map(r =>
        [esc(r.label), pct(r.now_pct), `${pct(r.target_pct)}${r.tilt ? ` <span class="small muted">(${pct(r.tilt, true, 0)})</span>` : ""}`, vnd(r.trade, true), esc((r.views || []).join(", "))]))
        + `<p class="small muted">Lỗ khi thị trường xấu: trước ${pct(gr.worst_before.share)} · sau ${pct(gr.worst_after.share)}</p>`)}
      ${more("Di sản", table(["Khoản", "Cách tính", "Số tiền"], leg.floor_rows.map(r => [esc(r.label), esc(r.how), vnd(r.amount)]))
        + kvs([["Đang có", range(leg.have_low, leg.have)], ["Nếu giá giảm", `${pct(leg.drop.drop, false, 0)} (${esc(leg.drop.note)})`],
          ["Cách bù", esc(leg.fill_with)]]))}
      ${more("Nghỉ hưu", kvs([["Năm nghỉ", ret.year], ["Cần khi nghỉ", vnd(ret.need)], ["Dự kiến đạt", vnd(ret.reach)],
        ["Lợi nhuận cần", `${pct(ret.required)}/năm`]].concat(ret.status === "short"
        ? [["Tiết kiệm thêm", `${vnd(ret.extra_monthly)}/tháng`], ["Hoặc nghỉ muộn", ret.delay.enough ? `${ret.delay.enough} năm` : "Lùi 10 năm vẫn chưa đủ"]] : [])))}
      ${more("Giả định", `<form data-assume class="simform">${Object.entries(EDIT).map(([k, [unit, f]]) => `
        <label class="field"><span><span>${esc(a.assumption_labels[k] || k)}</span> <span class="muted">${esc(unit)}</span></span>
        <input type="number" step="any" name="${k}" value="${shown(a.assumptions[k], f)}"></label>`).join("")}
        <button type="submit" class="btn primary">Tính lại</button>
        ${Object.keys(st.assumptions).length ? `<button type="button" class="btn" data-reset>Về mặc định</button>` : ""}</form>`)}
      ${more("Đối chiếu", kvs([["Tổng tài sản", vnd(a.reconcile.assets)], ["Nợ", vnd(a.reconcile.debts)],
        ["Tài sản ròng", vnd(a.reconcile.net_worth)], ["Ba giỏ cộng lại", vnd(a.reconcile.buckets)]]))}
    </section>`;

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
