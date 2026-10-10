/* Mr. Finance — the page. It only calls the services (app/main.py) and draws what they return. */
(function () {
  "use strict";
  const {vnd, pct, months: monthsText, monthName, esc} = window.Fmt;
  const C = window.Charts;
  const $ = (s, root) => (root || document).querySelector(s);

  const state = {clients: [], client: null, scope: "personal", months: 12, tab: "overview", board: null, seq: 0,
                 reads: {}, chat: {}, busy: false, risk: {}, alerts: null, alertFilter: "all",
                 catalog: [], sim: {}, simBusy: false, queue: []};
  const EXAMPLES = ["Tôi có 1 mảnh đất 500m2 ở Long Thành mua 2019 giá 3 tỷ", "Nhà tôi có 10 lượng vàng",
                    "Tôi có 2 con, 14 tuổi và 10 tuổi", "Tôi có 20% cổ phần công ty Hoa Sen trị giá 5 tỷ"];

  // colour follows the asset class, never its rank
  const GROUP_COLOR = {
    "Bất động sản": "var(--s1)", "Cổ phiếu": "var(--s2)", "Tiền & tiền gửi": "var(--s3)", "Vàng": "var(--s4)",
    "Chứng chỉ quỹ": "var(--s5)", "Cổ phần DN": "var(--s6)", "Trái phiếu": "var(--s7)", "Tài sản số": "var(--s8)",
  };
  const TRUST_COLOR = {verified: "var(--t1)", statement: "var(--t2)", declared: "var(--t3)"};
  const TRUST_LABEL = {verified: "Đã xác thực", statement: "Từ sao kê", declared: "KH tự khai"};
  const STATUS = {
    ok: {color: "var(--good)", icon: "●", text: "An toàn"},
    near: {color: "var(--warning)", icon: "▲", text: "Gần ngưỡng"},
    over: {color: "var(--critical)", icon: "■", text: "Vượt ngưỡng"},
    low: {color: "var(--warning)", icon: "▲", text: "Thấp"},
    critical: {color: "var(--critical)", icon: "■", text: "Rất thấp"},
  };
  const CLASS_LABEL = {
    cash: "Tiền mặt & thanh toán", deposit: "Tiền gửi", stock: "Cổ phiếu", bond: "Trái phiếu", fund: "Chứng chỉ quỹ",
    real_estate: "Bất động sản", gold: "Vàng", business: "Cổ phần DN", insurance: "Bảo hiểm", crypto: "Tài sản số",
    loan: "Khoản vay", card: "Dư nợ thẻ",
  };

  async function api(path, body) {
    const r = await fetch(path, body === undefined ? {} : {method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify(body)});
    if (!r.ok) throw new Error(`${path}: ${r.status}`);
    return r.json();
  }

  function status(key) {
    const s = STATUS[key] || STATUS.ok;
    return `<span class="status"><span class="dot" style="background:${s.color}" aria-hidden="true"></span>${s.text}</span>`;
  }

  // ── the overview ────────────────────────────────────────────────────
  function renderOverview(d) {
    const box = $("#tab-overview");
    const nw = d.net_worth, pf = d.performance, rk = d.risk, lq = d.liquidity, cf = d.cashflow;
    const up = nw.month_change >= 0;
    const who = d.members.map(m => `<span class="chip">${esc(m.name)} · ${esc(m.relation)}</span>`).join("")
      + d.waiting.map(m => `<span class="chip wait" title="Chưa đồng ý chia sẻ dữ liệu">${esc(m.name)} · chưa đồng ý chia sẻ</span>`).join("");
    box.innerHTML = `
      <div class="card hero">
        <div>
          <div class="label">Tài sản ròng ${d.scope === "family" ? "· gia đình" : "· cá nhân"}</div>
          <div class="figure">${vnd(nw.value)}</div>
          <div><span class="delta ${up ? "up" : "down"}">${up ? "▲" : "▼"} ${pct(nw.month_change_pct, true)}</span>
            <span class="muted">so với tháng trước (${vnd(nw.month_change, true)})</span></div>
          <div class="muted small" style="margin-top:6px">Tài sản ${vnd(nw.assets)} · Nợ ${vnd(nw.liabilities)} · cập nhật ${esc(d.as_of)}</div>
          <div class="who">${who}</div>
        </div>
        <div>
          <div class="label">Độ tin cậy dữ liệu · ${pct(nw.confidence, false, 0)}</div>
          <div id="trust" class="mt"></div>
        </div>
      </div>
      <div class="grid g3 mt">
        <div class="card"><h2>Phân bổ tài sản</h2><div id="alloc"></div></div>
        <div class="card"><h2>Lãi / lỗ danh mục <span class="hint">cổ phiếu, quỹ, trái phiếu</span></h2>
          <div class="stats">
            <div class="stat"><span class="k">Đã chốt (từ đầu năm)</span><span class="v">${vnd(pf.realized_ytd, true)}</span></div>
            <div class="stat"><span class="k">Chưa chốt</span><span class="v">${vnd(pf.unrealized, true)} <span class="muted">(${pct(pf.unrealized_pct, true)})</span></span></div>
            <div class="stat"><span class="k">Lợi nhuận từ đầu năm</span><span class="v">${pct(pf.ytd_return, true)}</span></div>
            <div class="stat"><span class="k">So với ${esc(pf.benchmark_name)} (${pct(pf.benchmark_ytd, true)})</span>
              <span class="v delta ${pf.vs_benchmark >= 0 ? "up" : "down"}">${pct(pf.vs_benchmark, true)}</span></div>
          </div>
          ${pf.by_class.length ? `<div class="tablewrap mt"><table><thead><tr><th>Loại</th><th class="num">Giá trị</th><th class="num">Lãi/lỗ</th></tr></thead><tbody>
            ${pf.by_class.map(c => `<tr><td>${esc(c.label)}</td><td class="num">${vnd(c.value)}</td><td class="num">${vnd(c.pnl, true)} <span class="muted">${pct(c.return, true)}</span></td></tr>`).join("")}
          </tbody></table></div>` : ""}
        </div>
        <div class="card"><h2>Rủi ro</h2>
          ${d.profile.risk_profile ? `<div class="stat"><span class="k">Hồ sơ rủi ro (bài test)</span><span class="v">${esc(d.profile.risk_profile)} · ${esc(d.profile.risk_persona)}</span></div>` : `<p class="muted small" style="margin:0 0 8px">Chưa làm bài test rủi ro: ngưỡng lấy theo hồ sơ.</p>`}
          <div class="stat"><span class="k">Ngưỡng sụt giảm chấp nhận</span><span class="v">${pct(rk.limit, false, 0)}</span></div>
          <div class="stat"><span class="k">Mức sụt giảm ước tính khi thị trường xấu</span><span class="v">${pct(rk.current)}</span></div>
          <div id="riskmeter"></div>
          <div>${status(rk.status)} <span class="muted small">· mất ${vnd(rk.stress_loss)} trong kịch bản xấu</span></div>
          ${d.concentration.warnings.length ? `<ul class="warn-list">${d.concentration.warnings.map(w => `<li><span class="ic" aria-hidden="true">⚠</span><span>Tập trung: ${esc(w)}</span></li>`).join("")}</ul>` : `<p class="muted small">Không có khoản nào tập trung quá ngưỡng.</p>`}
        </div>
      </div>
      <div class="card mt"><h2>Thanh khoản dự phòng</h2>
        <div class="stat"><span class="k">${vnd(lq.value)} tiền và tài sản rút được ngay</span>
          <span class="v">đủ chi ${monthsText(lq.months)} ${status(lq.status)}</span></div>
        <div id="liqmeter"></div>
        <div class="muted small">Chi tiêu ${vnd(lq.spending_monthly)}/tháng · mốc an toàn: 6 tháng</div>
      </div>
      <div class="card mt">
        <h2>Dòng tiền ${cf.months.length} tháng tới
          <span class="hint">vào ${vnd(cf.total_in)} · ra ${vnd(cf.total_out)}</span></h2>
        <div class="keys"><span><span class="sw" style="background:var(--in)"></span>Tiền vào</span>
          <span><span class="sw" style="background:var(--out)"></span>Tiền ra</span>
          <span><b style="color:var(--critical)">⚠</b> Khoản phải trả lớn</span>
          <span class="seg" role="group" aria-label="Số tháng" style="margin-left:auto">
            ${[12, 24, 36].map(n => `<button type="button" data-months="${n}" aria-pressed="${state.months === n}">${n} tháng</button>`).join("")}
          </span></div>
        <div id="cash" class="mt"></div>
        <div class="grid g2 mt">
          <div><h2>Khoản phải trả lớn</h2>${cf.large.length ? `<ul class="warn-list">${cf.large.map(l => `<li><span class="ic" aria-hidden="true">⚠</span><span><b>${monthName(l.month)}</b> · ${esc(l.label)} · ${vnd(l.amount)}</span></li>`).join("")}</ul>` : `<p class="muted small">Không có khoản lớn nào trong ${cf.months.length} tháng tới.</p>`}</div>
          <div><h2>Khoản định kỳ tìm thấy trong giao dịch</h2>
            <ul class="legend">${cf.recurring.map(r => `<li><span class="sw" style="background:${r.direction === "in" ? "var(--in)" : "var(--out)"}"></span><span>${esc(r.label)} <span class="muted small">· ${r.cadence === "monthly" ? "hằng tháng" : "theo kỳ"}</span></span><span class="v">${r.direction === "in" ? "+" : "−"}${vnd(r.amount)}</span><span></span></li>`).join("")}</ul></div>
        </div>
      </div>
      <div class="card mt" id="alerts-card"><h2>Cảnh báo tác động</h2><p class="muted small">Đang quét chính sách, vĩ mô và hạ tầng…</p></div>`;
    const trust = nw.trust_mix.map(t => ({label: TRUST_LABEL[t.trust] || t.label, value: t.value, share: t.share, trust: t.trust}));
    $("#trust", box).append(C.shareBar(trust, r => TRUST_COLOR[r.trust]));
    $("#alloc", box).append(C.shareBar(d.allocation.map(a => ({label: a.group, value: a.value, share: a.share})),
      r => GROUP_COLOR[r.label] || "var(--other)"));
    const rmax = Math.max(rk.limit * 1.6, rk.current * 1.1);
    $("#riskmeter", box).append(C.meter(rk.current, rmax, rk.limit, (STATUS[rk.status] || STATUS.ok).color,
      `Sụt giảm ước tính ${pct(rk.current)} so với ngưỡng ${pct(rk.limit, false, 0)}`));
    const lmax = Math.max(12, Math.min(lq.months, 36));
    $("#liqmeter", box).append(C.meter(Math.min(lq.months, lmax), lmax, 6, (STATUS[lq.status] || STATUS.ok).color,
      `Đủ chi ${monthsText(lq.months)}, mốc an toàn 6 tháng`));
    drawCash();
    for (const b of box.querySelectorAll("[data-months]")) b.onclick = () => { state.months = Number(b.dataset.months); load(); };
  }

  function drawCash() {
    const host = $("#cash");
    if (!host || !state.board || !host.clientWidth) return;   // hidden: drawn when its tab shows
    host.replaceChildren(C.cashflow(state.board.cashflow.months, state.board.cashflow.large, host.clientWidth));
  }
  let resizeTimer = null;
  addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(drawCash, 120); });

  // ── where the data comes from ───────────────────────────────────────
  function renderSources(d) {
    const box = $("#tab-sources");
    const tier = (n, title, sub) => {
      const rows = d.sources.filter(s => s.tier === n).map(s => `
        <div class="src"><span class="${s.status === "connected" ? "ok" : "no"}" aria-hidden="true">${s.status === "connected" ? "✓" : "○"}</span>
          <span><b>${esc(s.label)}</b></span>
          <span class="num">${s.count ? vnd(s.assets - s.liabilities) : "—"}</span>
          <span class="what">${esc(s.what)} · ${s.count ? `${s.count} khoản · ${s.trust.map(esc).join(", ")}` : "chưa có dữ liệu"}</span></div>`).join("");
      return `<div class="card"><h2>Tầng ${n} · ${title}</h2><p class="muted small" style="margin-top:-6px">${sub}</p>${rows}</div>`;
    };
    const family = d.scope === "family";
    box.innerHTML = `
      <div class="tiers">
        ${tier(1, "Hệ sinh thái Techcombank", "Tự động, khách hàng không cần thao tác.")}
        ${tier(2, "Ngoài hệ sinh thái", "Open API theo khung của NHNN, hoặc tải sao kê PDF / Excel để AI đọc.")}
        ${tier(3, "Khách hàng tự khai", "Form thông minh hoặc chat với AI.")}
      </div>
      <div class="grid g2 mt">${uploadCard()}${chatCard()}</div>
      <div class="card mt"><h2>Tất cả tài sản và khoản nợ <span class="hint">${d.holdings.length} khoản</span></h2>
        <div class="tablewrap"><table>
          <thead><tr>${family ? `<th class="wide">Chủ sở hữu</th>` : ""}<th>Khoản</th><th class="wide">Loại</th><th class="wide">Nguồn</th><th>Độ tin cậy</th><th class="num">Giá trị</th></tr></thead>
          <tbody>${d.holdings.map(h => { const src = esc((d.sources.find(s => s.source === h.source) || {}).label || h.source); return `<tr>${family ? `<td class="wide">${esc(h.owner_name)}</td>` : ""}<td>${esc(h.name)}<div class="sub">${family ? esc(h.owner_name) + " · " : ""}${src}</div></td>
            <td class="wide">${esc(CLASS_LABEL[h.class] || h.class)}</td><td class="wide">${src}</td>
            <td><span class="badge ${h.trust}">${TRUST_LABEL[h.trust]}</span></td>
            <td class="num">${h.kind === "liability" ? "−" : ""}${vnd(h.value)}</td></tr>`; }).join("")}</tbody>
        </table></div></div>`;
    wireSources();
  }

  // ── tier 2: a statement the client uploads ──────────────────────────
  const METHOD = {ai: "AI đọc", rules: "Đọc theo mẫu"};
  function uploadCard() {
    const me = state.clients.find(c => c.id === state.client) || {};
    const read = state.reads[state.client];
    const rows = read ? read.holdings.map(h => `<tr><td>${esc(h.name)}</td><td class="num">${vnd(h.value)}</td></tr>`).join("") : "";
    return `<div class="card"><h2>Tải sao kê <span class="hint">PDF · Excel · CSV</span></h2>
      <p class="muted small" style="margin-top:-6px">AI đọc sao kê của ngân hàng / công ty chứng khoán khác và tách từng khoản; khách hàng không phải nhập tay.</p>
      <div class="actions"><label class="btn"><input type="file" id="stmt-file" accept=".pdf,.xlsx,.xlsm,.csv,.txt" hidden>Chọn tệp…</label>
        ${(me.samples || []).map(n => `<button type="button" class="btn ghostbtn" data-sample="${esc(n)}">Dùng sao kê mẫu: ${esc(n)}</button>`).join("")}</div>
      <div id="stmt-out" class="mt" aria-live="polite">${read ? `<div><b>Đã đọc ${read.count} khoản từ ${esc(read.institution)}</b> · ${vnd(read.total)}
        <span class="badge statement">${METHOD[read.method] || read.method}</span></div>
        <div class="tablewrap"><table><tbody>${rows}</tbody></table></div>` : ""}</div></div>`;
  }

  function b64(buf) {
    const bytes = new Uint8Array(buf);
    let bin = "";
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(bin);
  }

  async function sendStatement(name, buf) {
    const out = $("#stmt-out");
    if (out) out.innerHTML = `<span class="muted">Đang đọc ${esc(name)}…</span>`;
    try {
      const read = (await api("/api/statement", {client_id: state.client, filename: name, content: b64(buf)})).read;
      state.reads[state.client] = read;
      await load();
    } catch (e) {
      if (out) out.innerHTML = `<span class="error">Không đọc được tệp: ${esc(e.message)}</span>`;
    }
  }

  // ── tier 3: the chat ────────────────────────────────────────────────
  function chatCard() {
    const log = state.chat[state.client] || [];
    const lines = log.map(m => m.who === "me"
      ? `<div class="msg me">${esc(m.text)}</div>`
      : `<div class="msg bot">${esc(m.text).replace(/\n/g, "<br>")}${m.method ? `<div class="muted small">${m.method === "ai" ? "Trợ lý AI" : "Đọc theo quy tắc"}${m.recorded ? ` · ghi ${m.recorded} mục` : ""}</div>` : ""}</div>`).join("");
    return `<div class="card"><h2>Khai báo qua chat</h2>
      <div class="chat" id="chat-log" aria-live="polite">${lines || `<div class="msg bot">Chào anh/chị, hãy kể những tài sản ngân hàng chưa thấy: nhà đất, vàng, cổ phần, khoản nợ, người phụ thuộc…</div>`}</div>
      <div class="chips">${EXAMPLES.map(t => `<button type="button" class="chipbtn" data-say="${esc(t)}">${esc(t)}</button>`).join("")}</div>
      <form id="chat-form" class="chatform"><input id="chat-in" autocomplete="off" placeholder="Ví dụ: Tôi có 1 mảnh đất 500m2 ở Long Thành mua 2019 giá 3 tỷ" aria-label="Tin nhắn">
        <button type="submit" class="btn">Gửi</button></form></div>`;
  }

  async function say(text) {
    text = (text || "").trim();
    if (!text || state.busy) return;
    const log = state.chat[state.client] = state.chat[state.client] || [];
    log.push({who: "me", text});
    state.busy = true;
    if (state.board) renderSources(state.board);
    try {
      const turn = (await api("/api/declare", {client_id: state.client, message: text, session_id: `${state.client}-web`})).turn;
      log.push({who: "bot", text: turn.reply, method: turn.method, recorded: turn.recorded.length});
    } catch (e) {
      log.push({who: "bot", text: "Xin lỗi, có lỗi khi ghi nhận: " + e.message});
    }
    state.busy = false;
    await load();
  }

  function wireSources() {
    const file = $("#stmt-file");
    if (file) file.onchange = async () => { const f = file.files[0]; if (f) sendStatement(f.name, await f.arrayBuffer()); };
    for (const b of document.querySelectorAll("[data-sample]")) {
      b.onclick = async () => {
        const r = await fetch(`/samples/${encodeURIComponent(b.dataset.sample)}`);
        sendStatement(b.dataset.sample, await r.arrayBuffer());
      };
    }
    for (const b of document.querySelectorAll("[data-say]")) b.onclick = () => say(b.dataset.say);
    const form = $("#chat-form");
    if (form) form.onsubmit = (ev) => { ev.preventDefault(); const i = $("#chat-in"); const t = i.value; i.value = ""; say(t); };
    const log = $("#chat-log");
    if (log) log.scrollTop = log.scrollHeight;
  }

  // ── alerts: what is moving the picture ──────────────────────────────
  const SEV = {
    high: {icon: "■", label: "Cao", color: "var(--critical)"},
    medium: {icon: "▲", label: "Trung bình", color: "var(--warning)"},
    low: {icon: "●", label: "Thấp", color: "var(--axis)"},
  };
  const KIND = {policy: "Chính sách", macro: "Vĩ mô", infrastructure: "Hạ tầng"};

  function sevTag(a) {
    if (a.opportunity) return `<span class="status"><span class="dot" style="background:var(--good)" aria-hidden="true"></span>Cơ hội · ${SEV[a.severity].label.toLowerCase()}</span>`;
    const v = SEV[a.severity];
    return `<span class="status"><span aria-hidden="true" style="color:${v.color}">${v.icon}</span>Rủi ro · ${v.label.toLowerCase()}</span>`;
  }

  function alertsCard(rep) {
    const box = $("#alerts-card");
    if (!box) return;
    const top = rep.alerts.slice(0, 3);
    box.innerHTML = `<h2>Cảnh báo tác động <span class="hint">${rep.risks} rủi ro · ${rep.opportunities} cơ hội</span></h2>
      <div class="alist">${top.map(a => `<div class="arow">${sevTag(a)}<b>${esc(a.title)}</b><span class="v ${a.impact >= 0 ? "delta up" : "delta down"}">${vnd(a.impact, true)}</span>
        <span class="muted small">${esc(a.message)}</span></div>`).join("")}</div>
      <button type="button" class="btn ghostbtn mt" id="to-alerts">Xem tất cả ${rep.alerts.length} cảnh báo →</button>`;
    $("#to-alerts").onclick = () => showTab("alerts");
  }

  function renderAlerts() {
    const box = $("#tab-alerts");
    const rep = state.alerts;
    if (!rep) { box.innerHTML = `<div class="card muted">Đang quét…</div>`; return; }
    const f = state.alertFilter;
    const list = rep.alerts.filter(a => f === "all" || (f === "opp" ? a.opportunity : !a.opportunity));
    const maxAbs = Math.max(1, ...rep.alerts.map(a => Math.abs(a.impact)));
    box.innerHTML = `
      <div class="card"><h2>Tác động lên tài sản ròng <span class="hint">${rep.scope === "family" ? "gia đình" : "cá nhân"} · tài sản ròng ${vnd(rep.net_worth)}</span></h2>
        <p class="muted small" style="margin-top:-4px">Tác động (VND) = Mức nắm giữ × Độ nhạy × Xác suất xảy ra · xác suất theo trạng thái: dự thảo thấp, đang lấy ý kiến trung bình, đã thông qua cao.</p>
        <div class="keys"><span><span class="sw" style="background:var(--out)"></span>Rủi ro (giảm tài sản)</span><span><span class="sw" style="background:var(--in)"></span>Cơ hội (tăng tài sản)</span>
          <span class="seg" role="group" aria-label="Lọc" style="margin-left:auto">${[["all", "Tất cả"], ["risk", "Rủi ro"], ["opp", "Cơ hội"]].map(([k, t]) => `<button type="button" data-af="${k}" aria-pressed="${f === k}">${t}</button>`).join("")}</span></div>
        <div class="dbars mt">${list.slice(0, 10).map(a => `<div class="dbar" tabindex="0" data-tip="${esc(a.id)}"><span class="dl">${esc(a.title)}</span>
          <span class="dt"><span class="dneg">${a.impact < 0 ? `<span style="width:${Math.abs(a.impact) / maxAbs * 100}%"></span>` : ""}</span><span class="dpos">${a.impact > 0 ? `<span style="width:${a.impact / maxAbs * 100}%"></span>` : ""}</span></span>
          <span class="dv">${vnd(a.impact, true)}</span></div>`).join("")}</div>
      </div>
      <p class="note mt">⚠ ${esc(rep.note)}</p>
      <div class="grid g2 mt">${list.map(a => `<div class="card acard">
          <div class="ahead2">${sevTag(a)}<span class="chip">${esc(KIND[a.kind] || a.kind)}</span><span class="chip">${esc(a.status_label)}</span></div>
          <h3>${esc(a.title)}</h3>
          <p>${esc(a.message)}</p>
          <div class="stats small">
            <div class="stat"><span class="k">Tác động ước tính (đã tính xác suất)</span><span class="v ${a.impact >= 0 ? "delta up" : "delta down"}">${vnd(a.impact, true)} · ${pct(a.impact_pct, true, 2)} tài sản ròng</span></div>
            <div class="stat"><span class="k">Mức nắm giữ × Độ nhạy × Xác suất</span><span class="v">${vnd(a.exposure)} × ${pct(a.sensitivity, true, 2)} × ${pct(a.probability, false, 0)}</span></div>
            <div class="stat"><span class="k">Khoản bị ảnh hưởng</span><span class="v">${a.affected.map(esc).join(", ")}</span></div>
          </div>
          <div class="muted small mt">Nguồn: ${esc(a.source)}</div></div>`).join("")}</div>`;
    for (const b of box.querySelectorAll("[data-af]")) b.onclick = () => { state.alertFilter = b.dataset.af; renderAlerts(); };
    for (const el of box.querySelectorAll("[data-tip]")) {
      const a = rep.alerts.find(x => x.id === el.dataset.tip);
      C.hover(el, `<b>${esc(a.title)}</b><div>${esc(a.message)}</div><div class="row"><span>Tác động</span><span>${vnd(a.impact, true)}</span></div>`);
    }
  }

  async function loadAlerts(seq) {
    try {
      const rep = (await api("/api/alerts", {client_id: state.client, scope: state.scope})).report;
      if (seq !== state.seq) return;
      state.alerts = rep;
      alertsCard(rep);
      renderAlerts();
    } catch (e) {
      const box = $("#alerts-card");
      if (box) box.innerHTML = `<h2>Cảnh báo tác động</h2><p class="error">Không tải được: ${esc(e.message)}</p>`;
    }
  }

  // ── scenarios ───────────────────────────────────────────────────────
  const PARAMS = {
    per_year: ["Học phí mỗi năm", "tỷ"], years: ["Số năm", ""], start_year: ["Năm bắt đầu", ""], fx_rise: ["Tỷ giá tăng", "%"],
    retire_age: ["Tuổi nghỉ hưu", ""], spending_after: ["Chi tiêu mỗi tháng sau nghỉ hưu", "triệu"], price: ["Giá BĐS", "tỷ"],
    loan_ratio: ["Tỷ lệ vay", "%"], rate: ["Lãi suất vay", "%"], rent_monthly: ["Tiền thuê kỳ vọng mỗi tháng", "triệu"],
    share: ["Phần chuyển cho con", "%"], need: ["Số tiền cần", "tỷ"], cost: ["Chi phí điều trị", "tỷ"], cover: ["Bảo hiểm chi trả", "%"],
    usd: ["Số USD cần", "USD"], amount: ["Khoản rút ra", "tỷ"],
  };
  const UNIT = {"tỷ": 1e9, "triệu": 1e6, "%": 0.01, "": 1, "USD": 1};
  const TONE = {good: "delta up", bad: "delta down", neutral: ""};

  function simState() { return state.sim[state.client] = state.sim[state.client] || {pick: null, result: null, sent: {}}; }

  async function runScenario(id, params) {
    const st = simState();
    st.pick = id;
    state.simBusy = true;
    renderScenarios();
    try {
      st.result = (await api("/api/scenario", {client_id: state.client, scenario: id, params: params || {}, scope: state.scope})).result;
    } catch (e) {
      st.result = {error: e.message};
    }
    state.simBusy = false;
    renderScenarios();
    // on a narrow screen the result sits above the list: bring it into view
    const panel = $("#tab-scenarios .simgrid > div:last-child");
    if (panel && innerWidth <= 980) panel.scrollIntoView({block: "start", behavior: "smooth"});
  }

  async function propose(option) {
    const st = simState(), r = st.result;
    try {
      const item = (await api("/api/review/propose", {client_id: state.client, scenario: r.scenario, title: r.title, option, summary: r.summary})).item;
      st.sent[`${r.scenario}:${option.id}`] = item.id;
      await loadQueue();
    } catch (e) { alert("Không gửi được: " + e.message); }
    renderScenarios();
  }

  function renderScenarios() {
    const box = $("#tab-scenarios");
    const st = simState();
    const me = state.clients.find(c => c.id === state.client) || {};
    const fit = (s) => s.personas.includes(me.persona_hint);
    const group = (kind, title, sub) => `<div class="card"><h2>${title}</h2><p class="muted small" style="margin-top:-6px">${sub}</p>
      <div class="slist">${state.catalog.filter(s => s.kind === kind).map(s => `<button type="button" class="sitem${st.pick === s.id ? " on" : ""}" data-sim="${s.id}">
        <b>${esc(s.title)}</b>${fit(s) ? `<span class="chip">hợp chân dung ${esc(me.persona_hint)}</span>` : ""}<span class="muted small">${esc(s.question)}</span></button>`).join("")}</div></div>`;
    const r = st.result;
    let panel = `<div class="card muted">Chọn một kịch bản để mô phỏng trên chính dữ liệu của ${esc(me.name || "khách hàng")}.</div>`;
    if (state.simBusy) panel = `<div class="card muted">Đang mô phỏng…</div>`;
    else if (r && r.error) panel = `<div class="card error">Không mô phỏng được: ${esc(r.error)}</div>`;
    else if (r) {
      const form = Object.entries(r.params || {}).filter(([k]) => PARAMS[k]).map(([k, v]) => {
        const [label, unit] = PARAMS[k];
        const shown = typeof v === "number" ? +(v / UNIT[unit]).toFixed(unit === "%" ? 1 : 2) : v;
        return `<label class="field"><span>${label}${unit ? ` (${unit})` : ""}</span><input type="number" step="any" name="${k}" value="${shown}"></label>`;
      }).join("");
      const cmp = (k, fmtf) => `<td class="num">${fmtf(r.before[k])}</td><td class="num">${fmtf(r.after[k])}</td>`;
      panel = `<div class="card">
          <div class="muted small">${r.kind === "stress" ? "Stress test thị trường · AI tự chạy" : "Kịch bản theo mốc đời"} · dữ liệu ngày ${esc(r.as_of)}</div>
          <h3 class="qtext" style="margin:4px 0 2px">${esc(r.title)}</h3><p class="muted">${esc(r.question)}</p>
          ${form ? `<form id="sim-form" class="simform">${form}<button type="submit" class="btn">Chạy lại</button></form>` : ""}
          <div class="stats mt">${r.summary.map(l => `<div class="stat"><span class="k">${esc(l.label)}</span><span class="v ${TONE[l.tone] || ""}">${esc(l.value)}</span></div>`).join("")}</div>
          <div class="tablewrap mt"><table><thead><tr><th></th><th class="num">Trước</th><th class="num">Sau</th></tr></thead><tbody>
            <tr><td>Tài sản ròng</td>${cmp("net_worth", vnd)}</tr>
            <tr><td>Thanh khoản</td>${cmp("liquid", vnd)}</tr>
            <tr><td>Đủ chi</td>${cmp("liquid_months", monthsText)}</tr></tbody></table></div>
        </div>
        <div class="grid g2 mt">${(r.options || []).map(o => {
          const sent = st.sent[`${r.scenario}:${o.id}`];
          const item = sent && state.queue.find(q => q.id === sent);
          const tag = item ? `<span class="badge ${item.status === "approved" ? "verified" : item.status === "rejected" ? "declared" : "statement"}">${item.status === "approved" ? "RM đã duyệt" : item.status === "rejected" ? "RM từ chối" : "Chờ RM duyệt"}</span>` : "";
          return `<div class="card"><div class="ahead2"><span class="chip">${o.id === "light" ? "Hướng nhẹ" : "Hướng mạnh"}</span>${tag}</div>
            <h3 style="margin:8px 0">${esc(o.title)}</h3>
            <div class="small muted">Làm gì</div><ul>${o.actions.map(a => `<li>${esc(a)}</li>`).join("")}</ul>
            <div class="small muted">Kết quả</div><ul>${o.effect.map(a => `<li>${esc(a)}</li>`).join("")}</ul>
            ${item ? (item.note ? `<p class="small"><b>Ghi chú RM:</b> ${esc(item.note)}</p>` : "") : `<button type="button" class="btn" data-propose="${o.id}">Gửi RM duyệt</button>`}</div>`;
        }).join("")}</div>
        <p class="note mt">${esc(r.note)}</p>`;
    }
    box.innerHTML = `<div class="simgrid"><div class="grid">${group("life", "Theo mốc trong đời", "Khách hàng chủ động thử.")}
      ${group("stress", "Stress test thị trường", "AI tự chạy, khách hàng xem kết quả.")}</div><div>${panel}</div></div>`;
    for (const b of box.querySelectorAll("[data-sim]")) b.onclick = () => runScenario(b.dataset.sim, {});
    for (const b of box.querySelectorAll("[data-propose]")) b.onclick = () => propose(r.options.find(o => o.id === b.dataset.propose));
    const form = $("#sim-form");
    if (form) form.onsubmit = (ev) => {
      ev.preventDefault();
      const prm = {...r.params};
      for (const i of form.querySelectorAll("input")) prm[i.name] = Number(i.value) * UNIT[PARAMS[i.name][1]];
      runScenario(r.scenario, prm);
    };
  }

  // ── the RM's queue ──────────────────────────────────────────────────
  async function loadQueue() {
    try { state.queue = (await api("/api/review")).items; } catch (_) { state.queue = []; }
    renderRM();
  }

  async function decideItem(id, decision) {
    const note = ($(`#note-${id}`) || {}).value || "";
    try {
      await api("/api/review/decide", {item_id: id, decision, note});
    } catch (e) { alert("Không lưu được: " + e.message); }
    await loadQueue();
    renderScenarios();
  }

  function renderRM() {
    const box = $("#tab-rm");
    const pending = state.queue.filter(q => q.status === "pending");
    const done = state.queue.filter(q => q.status !== "pending");
    const row = (q) => `<div class="card"><div class="ahead2"><b>${esc(q.client_name)}</b><span class="muted small">${new Date(q.created * 1000).toLocaleString("vi-VN")}</span>
        ${q.status !== "pending" ? `<span class="badge ${q.status === "approved" ? "verified" : "declared"}">${q.status === "approved" ? "Đã duyệt" : "Từ chối"}</span>` : ""}</div>
      <h3 style="margin:8px 0">${esc(q.title)}</h3>
      <ul>${((q.data.option || {}).actions || []).map(a => `<li>${esc(a)}</li>`).join("")}</ul>
      <div class="stats small">${(q.data.summary || []).slice(0, 4).map(l => `<div class="stat"><span class="k">${esc(l.label)}</span><span class="v">${esc(l.value)}</span></div>`).join("")}</div>
      ${q.status === "pending" ? `<div class="chatform mt"><input id="note-${q.id}" placeholder="Ghi chú cho khách hàng (không bắt buộc)" aria-label="Ghi chú">
        <button type="button" class="btn" data-ok="${q.id}">Duyệt</button><button type="button" class="btn ghostbtn" data-no="${q.id}">Từ chối</button></div>`
        : (q.note ? `<p class="small"><b>Ghi chú:</b> ${esc(q.note)}</p>` : "")}</div>`;
    box.innerHTML = `<div class="card"><h2>Hàng chờ RM duyệt <span class="hint">${pending.length} đang chờ</span></h2>
        <p class="muted small" style="margin-top:-6px">Mọi khuyến nghị từ kịch bản đều là mô phỏng cho đến khi RM duyệt (tuân thủ đề bài).</p></div>
      <div class="grid g2 mt">${pending.map(row).join("") || `<div class="card muted">Không có đề xuất nào đang chờ.</div>`}</div>
      ${done.length ? `<h2 class="mt" style="font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-2)">Đã xử lý</h2><div class="grid g2">${done.map(row).join("")}</div>` : ""}`;
    for (const b of box.querySelectorAll("[data-ok]")) b.onclick = () => decideItem(b.dataset.ok, "approved");
    for (const b of box.querySelectorAll("[data-no]")) b.onclick = () => decideItem(b.dataset.no, "rejected");
  }

  // ── the risk test ───────────────────────────────────────────────────
  const LEVEL_NAMES = ["Bảo toàn", "Thận trọng", "Cân bằng", "Tăng trưởng", "Mạo hiểm"];
  function riskState() {
    return state.risk[state.client] = state.risk[state.client] || {answers: {}, order: [], reply: null};
  }

  async function riskStep() {
    const r = riskState();
    const box = $("#tab-risk");
    box.classList.add("loading");
    try {
      r.reply = (await api("/api/risk", {client_id: state.client, answers: r.answers})).reply;
    } catch (e) {
      r.reply = {error: e.message};
    }
    box.classList.remove("loading");
    renderRisk();
    if (r.reply && r.reply.result) load();   // the dashboard measures risk against it now
  }

  function scoreBar(label, score, level) {
    return `<div class="stat"><span class="k">${label}</span><span class="v">${LEVEL_NAMES[level - 1]} · ${Math.round(score)}/100</span></div>
      <div class="meter" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${score}" aria-label="${label}">
        <span class="fill" style="width:${score}%;background:var(--s1)"></span>
        ${[20, 40, 60, 80].map(x => `<span class="mark" style="left:calc(${x}% - 1px);height:10px;top:0;background:var(--surface)"></span>`).join("")}</div>`;
  }

  function renderRisk() {
    const box = $("#tab-risk");
    const r = riskState();
    const me = state.clients.find(c => c.id === state.client) || {};
    if (!r.reply) {
      box.innerHTML = `<div class="card"><h2>Bài test khẩu vị rủi ro</h2>
        <p>8–12 câu hỏi tình huống; câu sau phụ thuộc vào câu trả lời trước. Kết quả tách hai điều:
        <b>mức chấp nhận rủi ro</b> (anh/chị muốn chịu bao nhiêu) và <b>khả năng chịu rủi ro</b> (dữ liệu tài chính cho thấy anh/chị có thể chịu bao nhiêu).</p>
        <button type="button" class="btn" id="risk-start">Bắt đầu cho ${esc(me.name || "")}</button></div>`;
      $("#risk-start").onclick = riskStep;
      return;
    }
    if (r.reply.error) {
      box.innerHTML = `<div class="card error">Không tải được bài test: ${esc(r.reply.error)}</div>`;
      return;
    }
    if (r.reply.question) {
      const q = r.reply.question;
      box.innerHTML = `<div class="card qcard"><div class="muted small">Câu ${q.number} / ${q.of}</div>
        <h3 class="qtext">${esc(q.text)}</h3>
        <div class="opts">${q.options.map(o => `<button type="button" class="opt" data-opt="${esc(o.id)}">${esc(o.text)}</button>`).join("")}</div>
        <div class="actions mt">${r.order.length ? `<button type="button" class="btn ghostbtn" id="risk-back">← Câu trước</button>` : ""}</div></div>`;
      for (const b of box.querySelectorAll("[data-opt]")) {
        b.onclick = () => { r.answers[q.id] = b.dataset.opt; r.order.push(q.id); riskStep(); };
      }
      const back = $("#risk-back");
      if (back) back.onclick = () => { delete r.answers[r.order.pop()]; riskStep(); };
      return;
    }
    const res = r.reply.result;
    box.innerHTML = `
      <div class="card hero">
        <div><div class="label">Hồ sơ rủi ro</div>
          <div class="figure" style="font-size:40px">${esc(res.profile.name)}</div>
          <div>Ngưỡng sụt giảm tối đa <b>${pct(res.drawdown_limit, false, 0)}</b> · ${res.questions} câu · ngày ${esc(res.taken)}</div>
          <div class="who"><span class="chip">Chân dung: <b>${esc(res.persona)}</b></span></div>
          <p class="muted small">${esc(res.persona_text)}</p></div>
        <div>${scoreBar("Mức chấp nhận rủi ro (KH muốn)", res.tolerance, res.tolerance_level)}
          ${scoreBar("Khả năng chịu rủi ro (dữ liệu cho thấy)", res.capacity, res.capacity_level)}
          <div class="muted small">Hồ sơ lấy mức thấp hơn của hai chỉ số.</div></div>
      </div>
      ${res.warnings.length ? `<div class="card mt"><h2>Cần lưu ý</h2><ul class="warn-list">${res.warnings.map(w => `<li><span class="ic" aria-hidden="true">⚠</span><span>${esc(w)}</span></li>`).join("")}</ul></div>` : ""}
      <div class="grid g2 mt">
        <div class="card"><h2>Vì sao khả năng chịu rủi ro ở mức này</h2><ul class="legend">${res.capacity_reasons.map(w => `<li><span class="sw" style="background:var(--axis)"></span><span>${esc(w)}</span><span></span><span></span></li>`).join("")}</ul></div>
        <div class="card"><h2>Phân bổ gợi ý cho hồ sơ ${esc(res.profile.name)}</h2>
          <table><tbody>${Object.entries(res.profile.mix).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${esc(v)}</td></tr>`).join("")}</tbody></table>
          <p class="muted small">Gợi ý mang tính mô phỏng; khuyến nghị cụ thể phải qua RM duyệt.</p></div>
      </div>
      <div class="card mt"><h2>Tự cập nhật</h2><p>Hệ thống sẽ hỏi lại vào <b>${esc(res.retest.date)}</b>, hoặc sớm hơn:</p>
        <ul>${res.retest.when.map(w => `<li>${esc(w)}</li>`).join("")}</ul>
        <button type="button" class="btn ghostbtn" id="risk-redo">Làm lại bài test</button></div>`;
    $("#risk-redo").onclick = () => { state.risk[state.client] = null; renderRisk(); };
  }

  // ── loading ─────────────────────────────────────────────────────────
  async function load() {
    const seq = ++state.seq;
    const main = $("#main");
    main.classList.add("loading");
    try {
      const d = (await api("/api/dashboard", {client_id: state.client, scope: state.scope, months: state.months})).dashboard;
      if (seq !== state.seq) return;
      state.board = d;
      renderOverview(d);
      renderSources(d);
      if (state.alerts && state.alerts.client_id === state.client && state.alerts.scope === state.scope) alertsCard(state.alerts);
      loadAlerts(seq);
      renderScenarios();
      if (!$("#tab-risk").dataset.client || $("#tab-risk").dataset.client !== state.client) {
        $("#tab-risk").dataset.client = state.client;
        renderRisk();
      }
    } catch (e) {
      $("#tab-overview").innerHTML = `<div class="card error">Không tải được dữ liệu: ${esc(e.message)}</div>`;
    } finally {
      if (seq === state.seq) main.classList.remove("loading");
    }
  }

  function showTab(tab) {
    state.tab = tab;
    for (const b of document.querySelectorAll(".tabs button")) {
      if (b.dataset.tab === tab) b.setAttribute("aria-current", "page");
      else b.removeAttribute("aria-current");
    }
    for (const s of document.querySelectorAll(".tab")) s.hidden = s.id !== `tab-${tab}`;
    // a chart drawn while its tab was hidden measured no width: draw it again now it shows
    if (tab === "overview") drawCash();
    try { localStorage.setItem("mf.tab", tab); } catch (_) { /* private mode */ }
  }

  function theme() {
    const root = document.documentElement;
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("mf.theme", root.dataset.theme); } catch (_) { /* private mode */ }
  }

  async function start() {
    try { const t = localStorage.getItem("mf.theme"); if (t) document.documentElement.dataset.theme = t; } catch (_) { /* */ }
    const {clients} = await api("/api/clients");
    try { state.catalog = (await api("/api/scenarios")).scenarios; } catch (_) { state.catalog = []; }
    loadQueue();
    state.clients = clients;
    const sel = $("#client");
    sel.innerHTML = clients.map(c => `<option value="${esc(c.id)}">${esc(c.name)} · ${esc(c.persona_hint)}</option>`).join("");
    let saved = null;
    try { saved = localStorage.getItem("mf.client"); } catch (_) { /* */ }
    state.client = clients.some(c => c.id === saved) ? saved : clients[0].id;
    sel.value = state.client;
    sel.onchange = () => { state.client = sel.value; try { localStorage.setItem("mf.client", sel.value); } catch (_) { /* */ } load(); };
    for (const b of document.querySelectorAll("[data-scope]")) {
      b.onclick = () => {
        state.scope = b.dataset.scope;
        for (const o of document.querySelectorAll("[data-scope]")) o.setAttribute("aria-pressed", String(o === b));
        load();
      };
    }
    for (const b of document.querySelectorAll(".tabs button")) b.onclick = () => showTab(b.dataset.tab);
    $("#theme").onclick = theme;
    $("#reset").onclick = async () => {
      if (!confirm("Xóa mọi dữ liệu đã tải lên, đã khai, bài test và hàng chờ RM để làm lại demo?")) return;
      await api("/api/reset", {});
      Object.assign(state, {reads: {}, chat: {}, risk: {}, sim: {}, alerts: null, queue: []});
      $("#tab-risk").dataset.client = "";
      await loadQueue();
      load();
    };
    let tab = "overview";
    try { tab = localStorage.getItem("mf.tab") || tab; } catch (_) { /* */ }
    showTab(document.querySelector(`.tabs [data-tab="${tab}"]`) ? tab : "overview");
    load();
  }

  start();
})();
