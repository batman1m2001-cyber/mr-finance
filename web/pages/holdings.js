/* Tài sản (SCR-CL-02): every holding and debt, and adding more (UI redesign R3; was the pre-redesign “sources”
   tab). A statement upload (PDF, Excel, CSV, or a sample) read by POST /api/statement (FEAT-22), a declaration chat
   streamed by POST /api/declare/stream (FEAT-23; the agent may ask back with a form or a choice), and the book: every holding grouped by asset class, with source and trust, when
   it was bought, cost, value, profit against cost (deposits: interest accrued to the price date), and what is owed
   against it and paid on that each month (business feedback 2026-10-29; the purchase price column left).
   The last read and the chat are kept for this browser tab, per client; a turn that records something redraws the
   book only, not the page. */
import {$, esc, get, n as how, pct, post, stream, vnd} from "../core/core.js";
import {CLASS_ICON, icon} from "../core/icons.js?v=20261016r1";

const EXAMPLES = ["Tôi có 1 mảnh đất 500m2 ở Long Thành mua 2019 giá 3 tỷ", "Nhà tôi có 10 lượng vàng",
  "Tôi có 2 con, 14 tuổi và 10 tuổi", "Tôi có 20% cổ phần công ty Hoa Sen trị giá 5 tỷ"];
const TRUST = {verified: ["good", "Đã xác thực"], statement: ["ai", "Từ sao kê"], declared: ["warn", "Bạn tự khai"]};
const METHOD = {ai: "AI đọc", rules: "Đọc theo mẫu"};
// the groups by how soon each turns into cash, the quickest first (business feedback 2026-10-29), the debts last
const BOOK = [
  {id: "cash", label: "Tiền mặt & tài khoản thanh toán", color: "var(--s3)", classes: ["cash"]},
  {id: "deposit", label: "Tiền gửi tiết kiệm", color: "var(--s3)", classes: ["deposit"]},
  {id: "stock", label: "Cổ phiếu", color: "var(--s2)", classes: ["stock"]},
  {id: "fund", label: "Chứng chỉ quỹ", color: "var(--s5)", classes: ["fund"]},
  {id: "gold", label: "Vàng", color: "var(--s4)", classes: ["gold"]},
  {id: "bond", label: "Trái phiếu", color: "var(--s7)", classes: ["bond"]},
  {id: "crypto", label: "Tài sản số", color: "var(--s8)", classes: ["crypto"]},
  {id: "insurance", label: "Bảo hiểm", color: "var(--other)", classes: ["insurance"]},
  {id: "business", label: "Cổ phần doanh nghiệp", color: "var(--s6)", classes: ["business"]},
  {id: "real_estate", label: "Bất động sản", color: "var(--s1)", classes: ["real_estate"]},
  {id: "debt", label: "Khoản nợ", color: "var(--critical)", classes: ["loan", "card"], debt: true, icon: "loan"},
];
const UNIT = {stock: "cp", bond: "TP", fund: "CCQ", gold: "lượng"};
const num = (x) => vnd(x).replace(/ đ$/, "");
const day = (iso) => (iso ? iso.slice(8, 10) + "/" + iso.slice(5, 7) + "/" + iso.slice(0, 4) : "");
const keep = (k, v) => {
  try {
    if (v === undefined) return JSON.parse(sessionStorage.getItem(k) || "null");
    sessionStorage.setItem(k, JSON.stringify(v));
  } catch (_) { /* private mode */ }
  return null;
};

// what one row says: bought when, cost, profit (null where the source does not know); the note is HTML
function bookRow(h, asOf, srcName) {
  const d = h.detail || {};
  const r = {bought: "", cost: h.cost, pnl: null, ret: null, note: "", why: {}};
  const price = (text) => how(text, "holding.price", {price_date: day(asOf)});
  const terms = (text) => how(text, "holding.terms", {source: srcName});
  // the average price paid, on the row's line now that its column is gone (business feedback 2026-10-29)
  const paid = (text) => how(text, "holding.buy_price", {source: srcName});
  if (h.class === "stock" || h.class === "bond") {
    r.bought = day(d.bought);
    r.note = `${num(d.qty)} ${UNIT[h.class]}${d.avg_price ? ` · giá mua ${paid(`${num(d.avg_price)} đ`)}` : ""} · giá nay ${price(`${num(d.price)} đ`)}`;
    if (h.class === "bond") r.note += ` · coupon ${terms(pct(d.coupon))}/năm · đáo hạn ${day(d.maturity)}`;
    r.why = {qty: `${num(d.qty)} ${UNIT[h.class]}`, buy_price: d.avg_price ? `${num(d.avg_price)} đ` : null};
  } else if (h.class === "fund") {
    r.bought = day(d.bought);
    r.note = `${num(d.units)} CCQ${d.avg_nav ? ` · giá mua ${paid(`${num(d.avg_nav)} đ`)}` : ""} · NAV nay ${price(`${num(d.nav)} đ`)}`;
    r.why = {qty: `${num(d.units)} CCQ`, buy_price: d.avg_nav ? `${num(d.avg_nav)} đ` : null};
  } else if (h.class === "real_estate") {
    r.bought = d.purchase_year ? `Năm ${d.purchase_year}` : "";
    r.note = [d.sqm ? `${num(d.sqm)} m²` : "", esc(d.area_name || ""), d.rental_monthly ? `cho thuê ${terms(vnd(d.rental_monthly))}/tháng` : ""].filter(Boolean).join(" · ");
    r.why = {buy_price: h.cost ? vnd(h.cost) : null};
  } else if (h.class === "deposit") {
    r.bought = day(d.opened);
    r.cost = h.value;
    if (d.rate && d.opened) {
      const days = Math.max(0, (new Date(asOf) - new Date(d.opened)) / 864e5);
      r.pnl = Math.round(h.value * d.rate * days / 365);
      r.ret = r.pnl / h.value;
      r.accrued = true;
      r.why = {rate: pct(d.rate), days: String(Math.round(days))};
    }
    r.note = [d.rate ? `lãi suất ${terms(pct(d.rate))}/năm` : "", d.maturity ? `đáo hạn ${day(d.maturity)}` : ""].filter(Boolean).join(" · ");
  } else if (h.class === "gold") {
    r.note = `${num(d.qty)} lượng · giá nay ${price(vnd(d.price))}/lượng`;
  } else if (h.class === "insurance") {
    r.note = d.premium_annual ? `phí ${terms(vnd(d.premium_annual))}/năm` : "";
  } else if (h.class === "loan") {
    r.note = [d.rate ? `lãi suất ${terms(pct(d.rate))} ${d.rate_type === "floating" ? "thả nổi" : "cố định"}` : "",
      d.monthly_payment ? `trả ${terms(vnd(d.monthly_payment))}/tháng` : "", d.end ? `đến ${day(d.end).slice(3)}` : ""].filter(Boolean).join(" · ");
  } else if (h.class === "card") {
    r.note = d.limit ? `hạn mức ${terms(vnd(d.limit))}` : "";
  }
  if (r.pnl == null && r.cost != null && h.kind === "asset") {
    r.pnl = h.value - r.cost;
    r.ret = r.cost ? r.pnl / r.cost : null;
  }
  return r;
}
// what is owed against each asset (business feedback 2026-10-29): a loan on the asset it is secured on (its collateral),
// the broker's margin loan spread over the shares held there by value; with what is paid each month (a margin loan:
// its interest). asset key → {debt, pay, interest}
function debtsOf(holdings) {
  const out = new Map();
  const add = (k, debt, pay, interest) => {
    const o = out.get(k) || {debt: 0, pay: 0, interest: false};
    out.set(k, {debt: o.debt + debt, pay: o.pay + pay, interest: o.interest || interest});
  };
  for (const l of holdings.filter(h => h.kind === "liability")) {
    const dd = l.detail || {};
    if (dd.collateral) {
      const a = holdings.find(h => h.kind === "asset" && h.owner === l.owner && h.key.split(":").pop() === dd.collateral);
      if (a) add(a.key, l.value, dd.monthly_payment || 0, false);
    } else if (l.class === "loan" && l.source === "tcbs") {
      const held = holdings.filter(h => h.kind === "asset" && h.owner === l.owner && h.source === "tcbs" && h.class === "stock");
      const total = held.reduce((t, h) => t + h.value, 0);
      const pay = dd.monthly_payment || Math.round(l.value * (dd.rate || 0) / 12);
      for (const h of held) add(h.key, l.value * h.value / total, pay * h.value / total, !dd.monthly_payment);
    }
  }
  return out;
}
const debtCell = (v) => (v ? `<span class="down">−${how(vnd(v), "liabilities.total")}</span>` : `<span class="muted">—</span>`);
const payCell = (v, interest) => (v ? `${how(vnd(v), "holding.terms")}${interest ? `<div class="small muted">tiền lãi</div>` : ""}` : `<span class="muted">—</span>`);
const pnlCell = (pnl, ret, accrued, inputs = {}) => {
  if (pnl == null) return `<span class="muted">—</span>`;
  const tone = pnl >= 0 ? "up" : "down";
  return `<span class="${tone}">${how(vnd(pnl, true), "holding.pnl", inputs)}</span><div class="small ${tone}">${ret == null ? "" : how(pct(ret, true), "holding.pnl", inputs)}${accrued ? `<span class="muted"> lãi dồn tích</span>` : ""}</div>`;
};

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope(), staff = ctx.role !== "client";
  let [{dashboard: d}, {clients}] = await Promise.all([post("/api/dashboard", {client_id: client, scope}), get("/api/clients")]);
  const me = clients.find(c => c.id === client) || {};
  const closed = keep("mf.book.closed") || {};
  let chat = keep(`mf.chat.${client}`) || [], busy = false;
  const fresh = async () => {  // the book and the totals, after a write: only they are drawn again
    d = (await post("/api/dashboard", {client_id: client, scope})).dashboard;
    drawBook();
  };

  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">${staff ? "Tài sản" : "Wealth View"}</div><h1 class="h1">Dữ liệu chi tiết tài sản</h1>
      <p class="lede">Từng khoản tài sản và khoản nợ · thêm dữ liệu bằng sao kê hoặc chat</p></div></div>
    <div class="cols">
      <div class="panel c6" id="upload"></div>
      <div class="panel c6" id="chat"></div>
      <div class="panel c12" id="book"></div>
    </div>`;

  const drawUpload = () => {
    const read = keep(`mf.read.${client}`);
    $("#upload", box).innerHTML = `<h3><span class="ic-chip sm" style="--tone:var(--s7)">${icon("file", {size: 13})}</span> Tải sao kê <span class="hint">PDF · Excel · CSV</span></h3>
      <p class="small muted" style="margin-top:-6px">AI đọc sao kê của ngân hàng / công ty chứng khoán khác và tách từng khoản; bạn không phải nhập tay.</p>
      <div class="row"><label class="btn primary"><input type="file" id="stmt-file" accept=".pdf,.xlsx,.xlsm,.csv,.txt" hidden>Chọn tệp…</label>
        ${(me.samples || []).map(n => `<button type="button" class="btn" data-sample="${esc(n)}">Dùng sao kê mẫu: ${esc(n)}</button>`).join("")}</div>
      <div id="stmt-out" class="mt" aria-live="polite">${read ? `<div><b>Đã đọc ${read.count} khoản từ ${esc(read.institution)}</b> · ${how(vnd(read.total), "statement.total", {count: String(read.count), institution: read.institution})}
        <span class="pill ai">${METHOD[read.method] || esc(read.method)}</span></div>
        <table class="table"><tbody>${read.holdings.map(h => `<tr><td>${esc(h.name)}</td><td class="r">${how(vnd(h.value), "holding.value", {source: read.institution})}</td></tr>`).join("")}</tbody></table>` : ""}</div>`;
    const send = async (name, buf) => {
      const out = $("#stmt-out", box);
      out.innerHTML = `<span class="muted">Đang đọc ${esc(name)}…</span>`;
      try {
        const bytes = new Uint8Array(buf);
        let bin = "";
        for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
        const read = (await post("/api/statement", {client_id: client, filename: name, content: btoa(bin)})).read;
        keep(`mf.read.${client}`, read);
        drawUpload();
        await fresh();
      } catch (e) {
        out.innerHTML = `<span class="down">Không đọc được tệp: ${esc(e.message)}</span>`;
      }
    };
    const file = $("#stmt-file", box);
    file.onchange = async () => { const f = file.files[0]; if (f) send(f.name, await f.arrayBuffer()); };
    for (const b of box.querySelectorAll("[data-sample]")) b.onclick = async () => {
      const r = await fetch(`/samples/${encodeURIComponent(b.dataset.sample)}`);
      send(b.dataset.sample, await r.arrayBuffer());
    };
  };

  const formHtml = (f, i) => f.fields.length === 1 && f.fields[0].kind === "choice"
    ? `<div class="row tight mt">${f.fields[0].options.map(o => `<button type="button" class="chip" data-say="${esc(o)}">${esc(o)}</button>`).join("")}</div>`
    : `<form class="dform mt" data-form="${i}">${f.title ? `<div class="small"><b>${esc(f.title)}</b></div>` : ""}
        ${f.fields.map((x, k) => `<label class="dfield"><span class="small muted">${esc(x.label)}</span><span class="row tight" style="flex-wrap:nowrap">${x.kind === "choice"
          ? `<select name="f${k}"><option value=""></option>${x.options.map(o => `<option>${esc(o)}</option>`).join("")}</select>`
          : `<input name="f${k}" autocomplete="off" inputmode="${["number", "money", "year"].includes(x.kind) ? "decimal" : "text"}" style="flex:1;min-width:0">`}${x.unit ? `<span class="small muted">${esc(x.unit)}</span>` : ""}</span></label>`).join("")}
        <button type="submit" class="btn primary sm">Gửi</button></form>`;
  const botHtml = (m, i) => `${m.text ? esc(m.text).replace(/\n/g, "<br>") : m.live ? `<span class="muted">${esc(m.step || "Đang ghi nhận…")}</span>` : ""}
    ${m.form && !m.sent && !m.live && m.form.fields.length ? formHtml(m.form, i) : ""}
    ${m.method ? `<div class="small muted">${m.method === "ai" ? "Trợ lý AI" : "Đọc theo quy tắc"}${m.recorded ? ` · ghi ${m.recorded} mục` : ""}</div>` : ""}`;

  const drawChat = () => {
    const lines = chat.map((m, i) => (m.who === "me" ? `<div class="msg me" data-quote>${esc(m.text)}</div>`
      : `<div class="msg bot"${m.method ? " data-quote" : ""} data-m="${i}">${botHtml(m, i)}</div>`)).join("");
    $("#chat", box).innerHTML = `<h3><span class="ic-chip sm" style="--tone:var(--s4)">${icon("sparkles", {size: 13})}</span> Bổ sung tài sản <span class="hint">khai báo qua chat</span></h3>
      <div class="chatlog" id="chat-log" aria-live="polite">${lines || `<div class="msg bot">Chào anh/chị, hãy kể những tài sản ngân hàng chưa thấy: nhà đất, vàng, cổ phần, khoản nợ, người phụ thuộc…</div>`}</div>
      <div class="row tight mt" data-quote>${EXAMPLES.map(t => `<button type="button" class="chip" data-say="${esc(t)}">${esc(t)}</button>`).join("")}</div>
      <form id="chat-form" class="row mt" style="flex-wrap:nowrap"><input id="chat-in" autocomplete="off" style="flex:1;min-width:0" placeholder="Ví dụ: Tôi có 1 mảnh đất 500m2 ở Long Thành mua 2019 giá 3 tỷ" aria-label="Tin nhắn">
        <button type="submit" class="btn primary">Gửi</button></form>`;
    const log = $("#chat-log", box);
    const bubble = (i) => {  // one reply drawn again as its words arrive; the rest of the panel is left alone
      const el = log.querySelector(`[data-m="${i}"]`);
      if (el) el.innerHTML = botHtml(chat[i], i);
      log.scrollTop = log.scrollHeight;
    };
    const say = async (text) => {
      text = (text || "").trim();
      if (!text || busy) return;
      for (const m of chat) if (m.form) m.sent = true;  // a new message answers (or passes on) what was asked
      chat.push({who: "me", text});
      const i = chat.push({who: "bot", text: "", live: true}) - 1, m = chat[i];
      busy = true; drawChat();
      let wrote = 0;
      try {
        await stream("/api/declare/stream", {client_id: client, message: text, session_id: `${client}-web`}, (ev) => {
          if (ev.type === "text") m.text += ev.text;
          else if (ev.type === "step" && ev.phase === "start") m.step = ev.label;
          else if (ev.type === "form") m.form = ev.form;
          else if (ev.type === "answer") {
            Object.assign(m, {text: ev.turn.reply, method: ev.turn.method, recorded: ev.turn.recorded.length});
            wrote = ev.turn.recorded.length;
          } else if (ev.type === "error") m.text = "Xin lỗi, có lỗi khi ghi nhận: " + ev.text;
          else return;
          bubble(i);
        });
      } catch (e) {
        m.text = "Xin lỗi, có lỗi khi ghi nhận: " + e.message;
      }
      if (!m.text) m.text = "Xin lỗi, em chưa nhận được trả lời. Anh/chị thử lại giúp em nhé.";
      delete m.live; delete m.step;
      busy = false;
      keep(`mf.chat.${client}`, chat);
      drawChat();
      $("#chat-in", box)?.focus({preventScroll: true});
      if (wrote) await fresh();
    };
    for (const b of box.querySelectorAll("#chat [data-say]")) b.onclick = () => say(b.dataset.say);
    for (const f of box.querySelectorAll("#chat [data-form]")) f.onsubmit = (e) => {
      e.preventDefault();
      const form = chat[+f.dataset.form].form;
      const said = form.fields.map((x, k) => [x, (f.elements[`f${k}`].value || "").trim()]).filter(([, v]) => v)
        .map(([x, v]) => `${x.label}: ${v}${x.unit && x.kind !== "choice" ? " " + x.unit : ""}`).join("; ");
      if (said) say(form.title ? `${form.title} — ${said}` : said);
    };
    $("#chat-form", box).onsubmit = (e) => { e.preventDefault(); const i = $("#chat-in", box); const t = i.value; i.value = ""; say(t); };
    log.scrollTop = log.scrollHeight;
  };

  const drawBook = () => {
    const family = d.scope === "family";
    const srcRaw = (h) => (d.sources.find(s => s.source === h.source) || {}).label || h.source;
    const src = (h) => esc(srcRaw(h));
    const assets = d.net_worth.assets || 1;
    const known = new Set(BOOK.flatMap(g => g.classes));
    const groups = BOOK.map(g => ({...g, rows: d.holdings.filter(h => g.classes.includes(h.class))}))
      .concat([{id: "other", label: "Khác", color: "var(--other)", rows: d.holdings.filter(h => !known.has(h.class))}])
      .filter(g => g.rows.length);
    const cols = family ? 9 : 8;
    const owed = debtsOf(d.holdings);
    const body = groups.map(g => {
      const rows = g.rows.map(h => ({h, r: bookRow(h, d.as_of, srcRaw(h))}));
      const total = rows.reduce((a, x) => a + x.h.value, 0);
      const priced = rows.filter(x => x.r.pnl != null);
      const pnl = priced.length ? priced.reduce((a, x) => a + x.r.pnl, 0) : null;
      const cost = priced.reduce((a, x) => a + (x.r.cost || 0), 0);
      const open = !closed[g.id];
      const gdebt = rows.reduce((a, x) => a + ((owed.get(x.h.key) || {}).debt || 0), 0);
      const gpay = rows.reduce((a, x) => a + (g.debt ? (x.h.detail || {}).monthly_payment || 0 : (owed.get(x.h.key) || {}).pay || 0), 0);
      const head = `<tr class="grouprow" data-group="${g.id}" tabindex="0" aria-expanded="${open}">
        <td colspan="${cols - 5}"><span class="caret" aria-hidden="true">${icon("chevron", {size: 14})}</span>
          <span class="ic-chip sm" style="--tone:${g.color}">${icon(g.icon || CLASS_ICON[g.id] || "wallet", {size: 12})}</span>
          <b>${esc(g.label)}</b> <span class="muted small">${rows.length} khoản${g.debt ? "" : ` · ${how(pct(total / assets, false, total / assets < 0.1 ? 1 : 0), "class.share", {value: vnd(total), assets: vnd(d.net_worth.assets)})} tài sản`}</span></td>
        <td class="r">${cost && !g.debt ? how(vnd(cost), "holding.cost", {qty: `${priced.length} khoản`}) : ""}</td><td class="r"><b>${g.debt ? "−" : ""}${how(vnd(total), g.debt ? "liabilities.total" : "class.value", {count: String(rows.length)})}</b></td>
        <td class="r">${g.debt ? "" : pnlCell(pnl, pnl != null && cost ? pnl / cost : null, false, {value: vnd(priced.reduce((a, x) => a + x.h.value, 0)), cost: vnd(cost)})}</td>
        <td class="r">${gdebt ? debtCell(gdebt) : ""}</td><td class="r">${gpay ? payCell(gpay) : ""}</td></tr>`;
      const lines = open ? rows.map(({h, r}) => { const o = owed.get(h.key) || {}; return `<tr>
        ${family ? `<td class="wide">${esc(h.owner_name)}</td>` : ""}
        <td><div>${esc(h.name)}</div>${r.note ? `<div class="small muted">${r.note}</div>` : ""}<div class="small muted narrow-only">${family ? esc(h.owner_name) + " · " : ""}${src(h)}</div></td>
        <td class="wide"><div>${src(h)}</div><span class="pill ${(TRUST[h.trust] || [""])[0]}">${(TRUST[h.trust] || ["", h.trust])[1]}</span></td>
        <td class="nowrap">${r.bought || `<span class="muted">—</span>`}</td>
        <td class="r">${r.cost != null && h.kind === "asset" ? how(vnd(r.cost), "holding.cost", r.why) : `<span class="muted">—</span>`}</td>
        <td class="r">${h.kind === "liability" ? "−" : ""}${how(vnd(h.value), "holding.value", {source: srcRaw(h), price_date: day(d.as_of)})}</td>
        <td class="r">${h.kind === "liability" ? `<span class="muted">—</span>` : pnlCell(r.pnl, r.ret, r.accrued, {value: vnd(h.value), cost: r.cost != null ? vnd(r.cost) : null, ...r.why})}</td>
        <td class="r">${h.kind === "liability" ? `<span class="muted">—</span>` : debtCell(o.debt)}</td>
        <td class="r">${h.kind === "liability" ? payCell((h.detail || {}).monthly_payment) : payCell(o.pay, o.interest)}</td></tr>`; }).join("") : "";
      return `<tbody>${head}${lines}</tbody>`;
    }).join("");
    const nw = d.net_worth;
    const pays = d.holdings.filter(h => h.kind === "liability").reduce((a, h) => a + ((h.detail || {}).monthly_payment || 0), 0);
    const foot = (label, v, cls = "", pay = "") => `<tr class="${cls}"><td colspan="${cols - 4}">${label}</td><td class="r">${v}</td><td></td><td></td><td class="r">${pay}</td></tr>`;
    $("#book", box).innerHTML = `<h3>Tất cả tài sản và khoản nợ <span class="hint">${d.holdings.length} khoản · ${groups.length} nhóm · bấm tên nhóm để thu gọn</span></h3>
      <div class="scrollx"><table class="table book">
        <thead><tr>${family ? `<th class="wide">Chủ sở hữu</th>` : ""}<th>Khoản</th><th class="wide">Nguồn · độ tin cậy</th><th>Ngày mua</th>
          <th class="r">Giá vốn</th><th class="r">Giá trị hiện tại</th><th class="r">Lãi / lỗ</th><th class="r nar">Nợ vay trên tài sản</th><th class="r nar">Trả nợ / tháng</th></tr></thead>
        ${body}
        <tfoot>${foot("Tổng tài sản", how(vnd(nw.assets), "assets.total"))}${foot("Tổng nợ", "−" + how(vnd(nw.liabilities), "liabilities.total"), "", pays ? payCell(pays) : "")}${foot("<b>Tài sản ròng</b>", `<b>${how(vnd(nw.value), "net_worth", {assets: vnd(nw.assets), liabilities: vnd(nw.liabilities)})}</b>`, "total")}</tfoot>
      </table></div>
      <p class="footnote">Giá vốn: tổng số tiền đã bỏ ra · lãi/lỗ so với giá vốn, chưa trừ thuế phí · tiền gửi: lãi dồn tích đến ${esc(day(d.as_of))} · nợ vay trên tài sản: khoản vay thế chấp bằng tài sản đó, hoặc vay ký quỹ chia theo giá trị cổ phiếu · “—”: nguồn chưa cung cấp.</p>`;
    for (const row of box.querySelectorAll("[data-group]")) {
      const flip = () => { closed[row.dataset.group] = !closed[row.dataset.group]; keep("mf.book.closed", closed); drawBook(); };
      row.onclick = flip;
      row.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); flip(); } };
    }
  };

  drawUpload(); drawChat(); drawBook();
}
