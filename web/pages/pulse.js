/* Toàn cảnh (redesign kit K2; board look, UI redesign R2): Financial Pulse, Money Flow, Wealth Map, what needs
   attention and the goals on one page. The numbers are the dashboard's (POST /api/dashboard), the month's
   transactions (POST /api/flows), the feed (POST /api/feed) and the goals (POST /api/goals); nothing is computed
   here that the server did not return, except sums and shares of what it returned (the month's change by asset
   class is the sum of each holding's value − its value last month). The full former overview stays one click
   away (“Chi tiết”). */
import {internal, n, nAttrs, ASSET_CLASS, CLASS_COLOR, $, esc, pct, post, signClass, vnd} from "../core/core.js";
import {CLASS_ICON, icon} from "../core/icons.js?v=20261016r1";
import {hover, sankey} from "../charts/charts.js";
import {donut, gauge, progress, ring} from "../charts/mini.js?v=20261016r2";

const STATUS = {
  ok: ["good", "An toàn"], near: ["warn", "Gần ngưỡng"], over: ["bad", "Vượt ngưỡng"],
  low: ["warn", "Thấp"], critical: ["bad", "Rất thấp"],
};
const GOAL = {on_track: ["good", "Đúng tiến độ", "var(--good)"], at_risk: ["warn", "Cần chú ý", "var(--warning)"],
  off_track: ["bad", "Chậm tiến độ", "var(--critical)"]};
const GROUP = {cash: "deposit"};  // cash and deposits are one group, as on the allocation table
const MONTH = (m) => `T${Number(m.slice(5))}/${m.slice(2, 4)}`;

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope();
  const staff = ctx.role !== "client";
  const [{dashboard: d}, first, fd, gd] = await Promise.all([
    post("/api/dashboard", {client_id: client, scope}),
    post("/api/flows", {client_id: client, scope}),
    post("/api/feed", {client_id: client, scope, role: staff ? "rm" : "client"}).catch((e) => ({error: e.message})),
    post("/api/goals", {client_id: client, scope}).catch((e) => ({error: e.message})),
  ]);
  let f = first.flows;
  const nw = d.net_worth, liq = d.liquidity, rk = d.risk;
  const pill = (s) => `<span class="pill ${(STATUS[s] || [""])[0]}">${esc((STATUS[s] || ["", s])[1])}</span>`;

  // Wealth Map: assets by class (cash folded into deposits), each opening to its holdings
  const groups = {};
  for (const h of d.holdings.filter(h => h.kind === "asset" && h.value > 0)) {
    const g = GROUP[h.class] || h.class;
    (groups[g] ||= {key: g, value: 0, items: []}).value += h.value;
    groups[g].items.push(h);
  }
  const map = Object.values(groups).sort((a, b) => b.value - a.value);
  const assets = map.reduce((a, g) => a + g.value, 0);
  const gname = (g) => (g === "deposit" ? "Tiền & tiền gửi" : ASSET_CLASS[g] || g);

  // the month's change of net worth by asset class: Σ (value − value last month); debts count against it
  const moved = {};
  for (const h of d.holdings) {
    if (h.prev_value == null) continue;
    const g = GROUP[h.class] || h.class, delta = (h.value - h.prev_value) * (h.kind === "liability" ? -1 : 1);
    if (delta) moved[g] = (moved[g] || 0) + delta;
  }
  const movers = Object.entries(moved).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));

  box.innerHTML = `${staff ? internal() : ""}
    <div class="cols pulse">
      <div class="c12 kpis" id="kpis"></div>
      <div class="panel c7" id="flow-panel">
        <h3>Dòng tiền của bạn <span class="hint" id="flow-of"></span>
          <select id="month" aria-label="Tháng" style="margin-left:auto"></select></h3>
        <div id="sankey"></div>
        <div class="ratios" id="ratios"></div>
        <div id="flow-rows" class="mt"></div>
        <div class="footnote">Chỉ từ giao dịch tài khoản; không suy diễn dòng tiền đầu tư. Bấm một dải để xem các giao dịch tạo nên nó.</div>
      </div>
      <div class="panel c5">
        <h3>Phân bổ tài sản <span class="hint">giá ngày ${esc(d.as_of)}</span></h3>
        <div class="wmap2"><div id="donut"></div><div class="wlegend" id="wlegend" role="list"></div></div>
        <div id="wmap-open"></div>
        <div class="footnote">Tổng ${n(vnd(assets), "assets.total")} tài sản. Nợ ${n(vnd(nw.liabilities), "liabilities.total")} không nằm trong biểu đồ; tài sản ròng = tài sản − nợ. Bấm một nhóm để xem từng khoản.</div>
      </div>
      <div class="panel c7" id="feed"></div>
      <div class="panel c5" id="goals"></div>
      <div class="c12 small"><a href="${ctx.href(ctx.role === "client" ? "tong-quan" : "khach-hang", ctx.role === "client" ? "chi-tiet" : "tong-quan")}">Xem đầy đủ: lãi/lỗ, rủi ro, thanh khoản, dòng tiền 12 tháng, tin nổi bật →</a></div>
    </div>`;

  // ── Financial Pulse: four cards, each with one small chart from the same numbers ─────────────────
  const hist = (d.cashflow && d.cashflow.history) || [];
  const card = (key, ic, tone, label, value, sub, viz = "", foot = "", cls = "") => `
    <div class="kpi pcard" ${key ? `data-focus="${key}"` : ""}>
      <div class="pc-head"><span class="ic-chip sm" style="--tone:${tone}">${icon(ic, {size: 14})}</span><span class="k">${label}</span></div>
      <div class="pc-body"><div class="pc-main"><div class="v ${cls}">${value}</div><div class="s">${sub}</div></div>${viz ? `<div class="pc-viz">${viz}</div>` : ""}</div>
      ${foot ? `<div class="pc-foot">${foot}</div>` : ""}</div>`;
  const drawKpis = () => {
    const top = movers.slice(0, 3);
    const max = Math.max(1, ...top.map(([, v]) => Math.abs(v)));
    const contrib = top.length ? `<div class="small muted">Thay đổi nhiều nhất trong tháng</div><div class="contrib" aria-label="Đóng góp trong tháng theo nhóm tài sản">${top.map(([g, v]) => `
      <div class="crow" data-g="${esc(g)}" data-delta="${v}"><span class="legend-dot" style="background:${CLASS_COLOR[g] || "var(--other)"}"></span><span>${esc(gname(g))}</span>
        <span class="cbar"><i style="width:${(Math.abs(v) / max) * 100}%;background:${v < 0 ? "var(--down)" : "var(--up)"}"></i></span>
        <b class="${signClass(v)}">${n(vnd(v, true), "class.month_change", {group: gname(g)})}</b></div>`).join("")}</div>` : "";
    const at = hist.findIndex(m => m.month === f.month);
    const end = at >= 0 ? at : hist.length - 1;
    const last = hist.slice(Math.max(0, end - 5), end + 1);
    const maxIO = Math.max(1, ...last.flatMap(m => [m.in, m.out]));
    const io = last.length ? `<svg class="mini" width="96" height="34" viewBox="0 0 96 34" role="img" aria-label="Tiền vào và ra ${last.length} tháng gần nhất">${last.map((m, i) => {
      const x = i * 16, hi = Math.max(1.5, (m.in / maxIO) * 32), ho = Math.max(1.5, (m.out / maxIO) * 32), on = m.month === f.month ? 1 : 0.4;
      return `<rect x="${x}" y="${34 - hi}" width="6" height="${hi}" rx="1.5" fill="var(--in)" opacity="${on}"/><rect x="${x + 7}" y="${34 - ho}" width="6" height="${ho}" rx="1.5" fill="var(--out)" opacity="${on}"/>`;
    }).join("")}</svg>` : "";
    const rate = f.total_in ? f.left / f.total_in : null;
    const fio = {total_in: vnd(f.total_in), total_out: vnd(f.total_out)};
    const months = liq.months >= 24 ? Math.floor(liq.months / 12) + " năm" : Math.round(liq.months) + " tháng";
    const share = assets ? liq.value / assets : 0;
    const chg = {now: vnd(nw.value), prev: vnd(nw.prev_value)};
    $("#kpis", box).innerHTML = [
      card("kpi:net_worth", "wallet", "var(--accent)", "Tài sản ròng", n(vnd(nw.value), "net_worth", {assets: vnd(nw.assets), liabilities: vnd(nw.liabilities)}),
        `<span class="${signClass(nw.month_change)}">${nw.month_change >= 0 ? "▲" : "▼"} ${n(vnd(nw.month_change, true), "net_worth.month_change", chg)} (${n(pct(nw.month_change_pct, true), "net_worth.month_change", chg)})</span> so với tháng trước`,
        "", contrib),
      card(`flow:${f.month}`, "flow", "var(--in)", `Dòng tiền ${MONTH(f.month)}`, n(`${f.left >= 0 ? "+" : "−"}${vnd(Math.abs(f.left))}`, "flow.left", fio),
        `<span class="nowrap">Vào <b>${n(vnd(f.total_in), "flow.in")}</b></span> · <span class="nowrap">Ra <b>${n(vnd(f.total_out), "flow.out")}</b></span>${rate != null ? `<br>${f.left >= 0 ? "Để dành" : "Thiếu"} ${n(pct(Math.abs(rate), false, 0), "flow.saving_rate", {left: vnd(f.left, true), total_in: vnd(f.total_in)})} tiền vào` : ""}`,
        io, `<span class="legend-dot" style="background:var(--in)"></span> vào <span class="legend-dot" style="background:var(--out);margin-left:8px"></span> ra · ${last.length} tháng`,
        f.left >= 0 ? "up" : "down"),
      card("kpi:liquidity", "bank", "var(--s3)", "Thanh khoản dự phòng", n(vnd(liq.value), "liquidity.value", {count: String(liq.items.length)}),
        `đủ chi ${n(months, "liquidity.months", {value: vnd(liq.value), spending: vnd(liq.spending_monthly)})} ${pill(liq.status)}`,
        ring(share, {size: 58, color: "var(--s3)", label: `${pct(share, false, 0)} tổng tài sản`, how: nAttrs("liquidity.share", {value: vnd(liq.value), assets: vnd(assets)})}),
        `${n(pct(share, false, 0), "liquidity.share", {value: vnd(liq.value), assets: vnd(assets)})} tổng tài sản · chi ${n(vnd(liq.spending_monthly), "spending.monthly")}/tháng`),
      card("kpi:risk", "shield", "var(--warning)", "Rủi ro khi thị trường xấu", n(pct(rk.current), "risk.current", {loss: vnd(rk.stress_loss), net_worth: vnd(nw.value)}),
        `ngưỡng ${n(pct(rk.limit, false, 0), "risk.limit")} ${pill(rk.status)}`,
        "", gauge(rk.current, rk.limit, {status: rk.status, label: `Sụt giảm ước tính ${pct(rk.current)} so với ngưỡng ${pct(rk.limit, false, 0)}`}) +
        `<div class="small muted mt-xs">Mất khoảng ${n(vnd(rk.stress_loss), "risk.loss")} trong kịch bản xấu</div>`),
    ].join("");
    for (const r of box.querySelectorAll(".crow[data-g]")) r.onclick = () => openGroup(r.dataset.g);
  };

  // ── Wealth Map: donut + legend; a group opens to its holdings ─────────────────────────────────────
  const openGroup = (key) => {
    const g = groups[key];
    if (!g) return;
    for (const b of box.querySelectorAll(".wrow[data-g]")) b.setAttribute("aria-pressed", String(b.dataset.g === key));
    const svg = $("#donut svg", box);
    if (svg) { svg.classList.add("picked"); for (const s of svg.querySelectorAll(".seg")) s.classList.toggle("on", s.dataset.key === key); }
    $("#wmap-open", box).innerHTML = `<table class="table mt"><caption class="small muted" style="text-align:left">${esc(gname(key))} · ${g.items.length} khoản</caption><tbody>${
      g.items.sort((a, b) => b.value - a.value).map(h => `<tr><td>${esc(h.name)}${scope === "family" && h.owner_name ? `<div class="small muted">${esc(h.owner_name)}</div>` : ""}</td><td class="r num">${n(vnd(h.value), "holding.value", {source: h.source_label || h.source || ""})}</td><td class="r num muted">${n(pct(h.value / assets), "holding.share", {value: vnd(h.value), assets: vnd(assets)})}</td></tr>`).join("")}</tbody></table>`;
  };
  const drawMap = () => {
    $("#donut", box).innerHTML = donut(map.map(g => ({key: g.key, value: g.value, color: CLASS_COLOR[g.key] || "var(--other)",
      label: `${gname(g.key)}: ${vnd(g.value)}, ${pct(g.value / assets)}`})), {size: 176, stroke: 24, center: vnd(assets), sub: "Tổng tài sản", how: nAttrs("assets.total"),
      label: "Phân bổ tài sản theo nhóm"});
    $("#wlegend", box).innerHTML = map.map(g => `<button type="button" class="wrow" role="listitem" data-g="${esc(g.key)}" aria-pressed="false">
      <span class="ic-chip sm" style="--tone:${CLASS_COLOR[g.key] || "var(--other)"}">${icon(CLASS_ICON[g.key] || "wallet", {size: 13})}</span>
      <span>${esc(gname(g.key))}</span><span class="num muted">${n(vnd(g.value), "class.value", {count: String(g.items.length)})}</span><b class="num">${n(pct(g.value / assets, false, 1), "class.share", {value: vnd(g.value), assets: vnd(assets)})}</b></button>`).join("");
    for (const b of box.querySelectorAll(".wrow[data-g]")) b.onclick = () => openGroup(b.dataset.g);
    for (const s of box.querySelectorAll("#donut .seg")) {
      const g = groups[s.dataset.key];
      s.addEventListener("click", () => openGroup(s.dataset.key));
      s.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openGroup(s.dataset.key); } });
      hover(s, `<b>${esc(gname(g.key))}</b><br>${vnd(g.value)} · ${pct(g.value / assets)}`);
    }
  };

  // ── Money Flow ──────────────────────────────────────────────────────────────────────────────────────
  const drawRows = (b, side) => {
    const el = $("#flow-rows", box);
    if (!b) {  // the table view of the chart: every band and its total
      const line = (x, sign) => `<tr class="click" data-cat="${esc(x.category)}" data-side="${sign}" data-focus="flow:${f.month}:${sign}:${esc(x.category)}"><td>${esc(x.label)}</td><td class="r num">${n(`${sign === "in" ? "+" : "−"}${vnd(x.amount)}`, "flow.band", {rows: String(x.rows.length)})}</td><td class="r small muted">${x.rows.length} giao dịch</td></tr>`;
      el.innerHTML = `<table class="table"><tbody>${f.inflow.map(x => line(x, "in")).join("")}${f.outflow.map(x => line(x, "out")).join("")}
        <tr><td><b>${f.left >= 0 ? "Còn lại" : "Thiếu hụt"}</b></td><td class="r num"><b class="${f.left >= 0 ? "up" : "down"}">${n(vnd(f.left, true), "flow.left", {total_in: vnd(f.total_in), total_out: vnd(f.total_out)})}</b></td><td></td></tr></tbody></table>`;
      for (const r of el.querySelectorAll("[data-cat]")) r.onclick = () => drawRows((r.dataset.side === "in" ? f.inflow : f.outflow).find(x => x.category === r.dataset.cat), r.dataset.side);
      return;
    }
    if (!b.rows) {  // Còn lại / Thiếu hụt: a difference, not rows
      el.innerHTML = `<p class="small">${esc(b.label)} = tiền vào ${n(vnd(f.total_in), "flow.in")} − tiền ra ${n(vnd(f.total_out), "flow.out")} = <b>${n(vnd(f.left, true), "flow.left", {total_in: vnd(f.total_in), total_out: vnd(f.total_out)})}</b>. <button type="button" class="linkbtn small" id="all-rows">Xem bảng tổng</button></p>`;
    } else {
      el.innerHTML = `<div class="row"><b>${esc(b.label)}</b><span class="muted small">${side === "in" ? "tiền vào" : "tiền ra"} · ${b.rows.length} giao dịch · ${n(vnd(b.amount), "flow.band", {rows: String(b.rows.length)})}</span><button type="button" class="linkbtn small" id="all-rows" style="margin-left:auto">← Bảng tổng</button></div>
        <table class="table"><tbody>${b.rows.map(r => `<tr><td class="num">${esc(r.date)}</td><td>${esc(r.desc)}${scope === "family" ? `<div class="small muted">${esc(r.owner_name)}</div>` : ""}</td><td class="r num">${n(vnd(r.amount), "transaction.amount", {date: r.date})}</td></tr>`).join("")}</tbody></table>`;
    }
    $("#all-rows", box).onclick = () => drawRows(null);
  };
  const drawRatios = () => {
    const rate = f.total_in ? f.left / f.total_in : null;
    const big = f.outflow[0];
    $("#ratios", box).innerHTML = [
      [f.left >= 0 ? "Tỷ lệ để dành" : "Chi vượt thu", rate == null ? "—" : n(pct(Math.abs(rate), false, 0), "flow.saving_rate", {left: vnd(f.left, true), total_in: vnd(f.total_in)}), f.left >= 0 ? "up" : "down"],
      ["Tiền ra / tiền vào", f.total_in ? n(pct(f.total_out / f.total_in, false, 0), "flow.out_in", {total_out: vnd(f.total_out), total_in: vnd(f.total_in)}) : "—", ""],
      ["Nhóm chi lớn nhất", big ? `${esc(big.label)} · ${n(vnd(big.amount), "flow.band", {rows: String(big.rows.length)})}` : "—", ""],
    ].map(([k, v, c]) => `<div class="ratio"><span class="k">${k}</span><b class="${c}">${v}</b></div>`).join("");
  };
  const drawFlow = () => {
    $("#flow-panel", box).dataset.focus = `flow:${f.month}`;
    $("#flow-of", box).textContent = `${MONTH(f.month)} · ${scope === "family" ? "gia đình" : "cá nhân"} · ${f.rows} giao dịch`;
    const sel = $("#month", box);
    sel.innerHTML = [...f.months].reverse().map(m => `<option value="${m}" ${m === f.month ? "selected" : ""}>${MONTH(m)}</option>`).join("");
    sel.onchange = async () => {
      try { f = (await post("/api/flows", {client_id: client, scope, month: sel.value})).flows; } catch (e) { $("#flow-rows", box).textContent = e.message; return; }
      drawKpis(); drawFlow();
    };
    sankey($("#sankey", box), f, {label: `Dòng tiền ${MONTH(f.month)}`, onPick: drawRows});
    drawRatios();
    drawRows(null);
  };

  // ── Intelligence Feed (kit K4) as impact cards ──────────────────────────────────────────────────
  const ROUTE = staff
    ? {impact: ctx.href("khach-hang", "tac-dong"), graph: ctx.href("khach-hang", "do-thi"), detail: ctx.href("khach-hang", "tong-quan")}
    : {impact: ctx.href("tin", "thi-truong"), graph: ctx.href("tin", "do-thi"), detail: ctx.href("tong-quan", "chi-tiet")};
  const SEV = {high: ["bad", "Cần xem"], medium: ["warn", "Đáng chú ý"], info: ["", "Thông tin"]};
  const TYPE = {impact: ["Tin tác động", "news", "var(--s1)"], goal: ["Mục tiêu", "target", "var(--s3)"], risk: ["Ngưỡng", "alert", "var(--warning)"],
    change: ["Thay đổi", "activity", "var(--s7)"]};
  const KIND = {run: "Lần áp dụng", regulation: "Ghi chú quy định", goal: "Mục tiêu", dashboard: "Tổng quan", transactions: "Giao dịch"};
  const PART = {risk: "rủi ro", liquidity: "thanh khoản", net_worth: "tài sản ròng"};
  const source = (ev) => `${KIND[ev.kind] || ev.kind} ${ev.kind === "dashboard" ? PART[ev.id] || ev.id : ev.kind === "transactions" ? `${ev.category} ${ev.month}` : ev.id}`;
  const drawFeed = () => {
    const el = $("#feed", box);
    if (fd.error) { el.innerHTML = `<h3>Điều đáng chú ý</h3><div class="small muted">Không tải được: ${esc(fd.error)}</div>`; return; }
    const its = fd.feed.items;
    el.innerHTML = `<h3>Điều đáng chú ý <span class="hint">${its.length ? `${its.length} mục · quan trọng trước` : ""}</span></h3>
      ${its.length ? `<div class="list">${its.map((i) => {
        const t = TYPE[i.type] || [i.type, "info", "var(--accent)"];
        return `<div class="item feed-item" data-focus="${esc(i.key)}">
        <span class="ic-chip" style="--tone:${t[2]}">${icon(t[1])}</span>
        <div><div class="t" data-explains>${esc(i.title)}</div>
          <div class="row tight mt-xs"><span class="pill ${SEV[i.severity][0]}">${SEV[i.severity][1]}</span><span class="pill">${esc(t[0])}</span>${i.value != null && i.type === "impact" ? `<span class="pill ${i.value < 0 ? "bad" : "good"}">${n(vnd(i.value, true), "impact.expected_3m", {event: i.title})} · 3 tháng</span>` : ""}</div>
          <div class="m mt-xs" data-explains>${esc(i.why)}</div>
          <div class="small muted">Nguồn: ${esc(source(i.evidence))}</div></div>
        ${i.link === "flow" ? `<button type="button" class="linkbtn small" data-month="${esc(i.evidence.month)}">Xem dòng tiền →</button>`
          : `<a class="small" href="${ROUTE[i.link]}">Xem bằng chứng →</a>`}</div>`;
      }).join("")}</div>`
        : `<div class="small muted">Không có điều gì cần chú ý lúc này.</div>`}
      <div class="footnote" data-explains>Vì sao một mục hiện ở đây: ${esc(fd.feed.rules)}</div>`;
    for (const b of el.querySelectorAll("[data-month]")) b.onclick = () => {
      const sel = $("#month", box);
      sel.value = b.dataset.month; sel.dispatchEvent(new Event("change"));
      sel.scrollIntoView({block: "center"});
    };
  };

  // ── Goals: what each followed goal needs, what the client has for it, how far along ───────────────
  const drawGoals = () => {
    const el = $("#goals", box);
    const plan = ctx.role === "client" ? ctx.href("muc-tieu", "ke-hoach") : ctx.href("khach-hang", "ke-hoach");
    if (gd.error) { el.innerHTML = `<h3>Mục tiêu tài chính</h3><div class="small muted">Không tải được: ${esc(gd.error)}</div>`; return; }
    const followed = gd.goals.filter(g => g.followed);
    el.innerHTML = `<h3>Mục tiêu tài chính <span class="hint">${followed.length} mục tiêu đang theo dõi</span></h3>
      ${followed.length ? `<div class="goals">${followed.map(g => {
        const x = g.goal, st = GOAL[x.status] || ["", x.status, "var(--accent)"];
        return `<div class="goal" data-focus="goal:${esc(g.id)}">
          <div class="row spread"><b>${esc(g.title)}</b><span class="pill ${st[0]}">${st[1]}</span></div>
          <div class="row spread small muted mt-xs"><span>Cần ${n(vnd(x.need), "goal.need")} · ${esc(x.by)}</span><b class="num" style="color:var(--ink)">${n(pct(Math.min(1, x.progress), false, 0), "goal.progress", {need: vnd(x.need), have: vnd(x.have)})}</b></div>
          ${progress(x.progress, {color: st[2], label: `${g.title}: ${pct(Math.min(1, x.progress), false, 0)}`})}
          <div class="small muted mt-xs">${x.gap > 0 ? `Còn thiếu ${n(vnd(x.gap), "goal.gap", {need: vnd(x.need), have: vnd(x.have)})}` : "Đã đủ nguồn"} · ${esc(x.have_label)} ${n(vnd(x.have), "goal.have")}</div></div>`;
      }).join("")}</div>` : `<div class="small muted">Chưa có mục tiêu đang theo dõi.</div>`}
      <div class="footnote">Theo giả định mặc định của trang Kế hoạch. <a href="${plan}">Mở Kế hoạch →</a></div>`;
  };

  drawKpis(); drawMap(); drawFlow(); drawFeed(); drawGoals();
}
