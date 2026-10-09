/* Mr. Finance — the page. It only calls the services (app/main.py) and draws what they return. */
(function () {
  "use strict";
  const {vnd, pct, months: monthsText, monthName, esc} = window.Fmt;
  const C = window.Charts;
  const $ = (s, root) => (root || document).querySelector(s);

  const state = {clients: [], client: null, scope: "personal", months: 12, tab: "overview", board: null, seq: 0,
                 reads: {}, chat: {}, busy: false};
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
      </div>`;
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
    if (!host || !state.board) return;
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
      const read = await api("/api/statement", {client_id: state.client, filename: name, content: b64(buf)});
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
      const turn = await api("/api/declare", {client_id: state.client, message: text, session_id: `${state.client}-web`});
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

  // ── loading ─────────────────────────────────────────────────────────
  async function load() {
    const seq = ++state.seq;
    const main = $("#main");
    main.classList.add("loading");
    try {
      const d = await api("/api/dashboard", {client_id: state.client, scope: state.scope, months: state.months});
      if (seq !== state.seq) return;
      state.board = d;
      renderOverview(d);
      renderSources(d);
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
    let tab = "overview";
    try { tab = localStorage.getItem("mf.tab") || tab; } catch (_) { /* */ }
    showTab(document.querySelector(`.tabs [data-tab="${tab}"]`) ? tab : "overview");
    load();
  }

  start();
})();
