/* Tài sản (SCR-CL-02): every holding and debt, and adding more (UI redesign R3; was the pre-redesign “sources”
   tab). A statement upload (PDF, Excel, CSV, or a sample) read by POST /api/statement (FEAT-22), a declaration chat
   by POST /api/declare (FEAT-23), and the book: every holding grouped by asset class, with source and trust, when
   and at what it was bought, cost, value, and profit against cost (deposits: interest accrued to the price date).
   The last read and the chat are kept for this browser tab, per client. */
import {internal, $, esc, get, pct, post, vnd} from "../core/core.js";
import {CLASS_ICON, icon} from "../core/icons.js?v=20261016r1";

const EXAMPLES = ["Tôi có 1 mảnh đất 500m2 ở Long Thành mua 2019 giá 3 tỷ", "Nhà tôi có 10 lượng vàng",
  "Tôi có 2 con, 14 tuổi và 10 tuổi", "Tôi có 20% cổ phần công ty Hoa Sen trị giá 5 tỷ"];
const TRUST = {verified: ["good", "Đã xác thực"], statement: ["ai", "Từ sao kê"], declared: ["warn", "Bạn tự khai"]};
const METHOD = {ai: "AI đọc", rules: "Đọc theo mẫu"};
const BOOK = [
  {id: "real_estate", label: "Bất động sản", color: "var(--s1)", classes: ["real_estate"]},
  {id: "stock", label: "Cổ phiếu", color: "var(--s2)", classes: ["stock"]},
  {id: "fund", label: "Chứng chỉ quỹ", color: "var(--s5)", classes: ["fund"]},
  {id: "bond", label: "Trái phiếu", color: "var(--s7)", classes: ["bond"]},
  {id: "deposit", label: "Tiền gửi tiết kiệm", color: "var(--s3)", classes: ["deposit"]},
  {id: "cash", label: "Tiền mặt & tài khoản thanh toán", color: "var(--s3)", classes: ["cash"]},
  {id: "gold", label: "Vàng", color: "var(--s4)", classes: ["gold"]},
  {id: "business", label: "Cổ phần doanh nghiệp", color: "var(--s6)", classes: ["business"]},
  {id: "insurance", label: "Bảo hiểm", color: "var(--other)", classes: ["insurance"]},
  {id: "crypto", label: "Tài sản số", color: "var(--s8)", classes: ["crypto"]},
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

// what one row says: bought when, at what, cost, profit (null where the source does not know)
function bookRow(h, asOf) {
  const d = h.detail || {};
  const r = {bought: "", price: "", cost: h.cost, pnl: null, ret: null, note: ""};
  if (h.class === "stock" || h.class === "bond") {
    r.bought = day(d.bought);
    if (d.avg_price) r.price = `${num(d.avg_price)} đ/${UNIT[h.class]}`;
    r.note = `${num(d.qty)} ${UNIT[h.class]} · giá nay ${num(d.price)} đ`;
    if (h.class === "bond") r.note += ` · coupon ${pct(d.coupon)}/năm · đáo hạn ${day(d.maturity)}`;
  } else if (h.class === "fund") {
    r.bought = day(d.bought);
    if (d.avg_nav) r.price = `${num(d.avg_nav)} đ/CCQ`;
    r.note = `${num(d.units)} CCQ · NAV nay ${num(d.nav)} đ`;
  } else if (h.class === "real_estate") {
    r.bought = d.purchase_year ? `Năm ${d.purchase_year}` : "";
    if (h.cost) r.price = vnd(h.cost);
    r.note = [d.sqm ? `${num(d.sqm)} m²` : "", d.area_name || "", d.rental_monthly ? `cho thuê ${vnd(d.rental_monthly)}/tháng` : ""].filter(Boolean).join(" · ");
  } else if (h.class === "deposit") {
    r.bought = day(d.opened);
    r.cost = h.value;
    if (d.rate && d.opened) {
      const days = Math.max(0, (new Date(asOf) - new Date(d.opened)) / 864e5);
      r.pnl = Math.round(h.value * d.rate * days / 365);
      r.ret = r.pnl / h.value;
      r.accrued = true;
    }
    r.note = [d.rate ? `lãi suất ${pct(d.rate)}/năm` : "", d.maturity ? `đáo hạn ${day(d.maturity)}` : ""].filter(Boolean).join(" · ");
  } else if (h.class === "gold") {
    r.note = `${num(d.qty)} lượng · giá nay ${vnd(d.price)}/lượng`;
  } else if (h.class === "insurance") {
    r.note = d.premium_annual ? `phí ${vnd(d.premium_annual)}/năm` : "";
  } else if (h.class === "loan") {
    r.note = [d.rate ? `lãi suất ${pct(d.rate)} ${d.rate_type === "floating" ? "thả nổi" : "cố định"}` : "",
      d.monthly_payment ? `trả ${vnd(d.monthly_payment)}/tháng` : "", d.end ? `đến ${day(d.end).slice(3)}` : ""].filter(Boolean).join(" · ");
  } else if (h.class === "card") {
    r.note = d.limit ? `hạn mức ${vnd(d.limit)}` : "";
  }
  if (r.pnl == null && r.cost != null && h.kind === "asset") {
    r.pnl = h.value - r.cost;
    r.ret = r.cost ? r.pnl / r.cost : null;
  }
  return r;
}
const pnlCell = (pnl, ret, accrued) => (pnl == null ? `<span class="muted">—</span>`
  : `<span class="${pnl >= 0 ? "up" : "down"}">${vnd(pnl, true)}</span><div class="small ${pnl >= 0 ? "up" : "down"}">${ret == null ? "" : pct(ret, true)}${accrued ? `<span class="muted"> lãi dồn tích</span>` : ""}</div>`);

export async function render(box, ctx) {
  const client = ctx.client(), scope = ctx.scope(), staff = ctx.role !== "client";
  const [{dashboard: d}, {clients}] = await Promise.all([post("/api/dashboard", {client_id: client, scope}), get("/api/clients")]);
  const me = clients.find(c => c.id === client) || {};
  const closed = keep("mf.book.closed") || {};
  let chat = keep(`mf.chat.${client}`) || [], busy = false;

  box.innerHTML = `${staff ? internal() : ""}
    <div class="pagehead"><div><div class="eyebrow">Tài sản</div><h1 class="h1">Dữ liệu chi tiết tài sản</h1>
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
      <div id="stmt-out" class="mt" aria-live="polite">${read ? `<div><b>Đã đọc ${read.count} khoản từ ${esc(read.institution)}</b> · ${vnd(read.total)}
        <span class="pill ai">${METHOD[read.method] || esc(read.method)}</span></div>
        <table class="table"><tbody>${read.holdings.map(h => `<tr><td>${esc(h.name)}</td><td class="r">${vnd(h.value)}</td></tr>`).join("")}</tbody></table>` : ""}</div>`;
    const send = async (name, buf) => {
      const out = $("#stmt-out", box);
      out.innerHTML = `<span class="muted">Đang đọc ${esc(name)}…</span>`;
      try {
        const bytes = new Uint8Array(buf);
        let bin = "";
        for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
        const read = (await post("/api/statement", {client_id: client, filename: name, content: btoa(bin)})).read;
        keep(`mf.read.${client}`, read);
        ctx.go(location.hash);  // the book and the totals change: draw the page again
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

  const drawChat = () => {
    const lines = chat.map(m => (m.who === "me" ? `<div class="msg me">${esc(m.text)}</div>`
      : `<div class="msg bot">${esc(m.text).replace(/\n/g, "<br>")}${m.method ? `<div class="small muted">${m.method === "ai" ? "Trợ lý AI" : "Đọc theo quy tắc"}${m.recorded ? ` · ghi ${m.recorded} mục` : ""}</div>` : ""}</div>`)).join("");
    $("#chat", box).innerHTML = `<h3><span class="ic-chip sm" style="--tone:var(--s4)">${icon("sparkles", {size: 13})}</span> Bổ sung tài sản <span class="hint">khai báo qua chat</span></h3>
      <div class="chatlog" id="chat-log" aria-live="polite">${lines || `<div class="msg bot">Chào anh/chị, hãy kể những tài sản ngân hàng chưa thấy: nhà đất, vàng, cổ phần, khoản nợ, người phụ thuộc…</div>`}
        ${busy ? `<div class="msg bot muted">Đang ghi nhận…</div>` : ""}</div>
      <div class="row tight mt">${EXAMPLES.map(t => `<button type="button" class="chip" data-say="${esc(t)}">${esc(t)}</button>`).join("")}</div>
      <form id="chat-form" class="row mt" style="flex-wrap:nowrap"><input id="chat-in" autocomplete="off" style="flex:1;min-width:0" placeholder="Ví dụ: Tôi có 1 mảnh đất 500m2 ở Long Thành mua 2019 giá 3 tỷ" aria-label="Tin nhắn">
        <button type="submit" class="btn primary">Gửi</button></form>`;
    const say = async (text) => {
      text = (text || "").trim();
      if (!text || busy) return;
      chat.push({who: "me", text});
      busy = true; drawChat();
      try {
        const turn = (await post("/api/declare", {client_id: client, message: text, session_id: `${client}-web`})).turn;
        chat.push({who: "bot", text: turn.reply, method: turn.method, recorded: turn.recorded.length});
      } catch (e) {
        chat.push({who: "bot", text: "Xin lỗi, có lỗi khi ghi nhận: " + e.message});
      }
      busy = false;
      keep(`mf.chat.${client}`, chat);
      ctx.go(location.hash);  // a declaration adds holdings: draw the page again
    };
    for (const b of box.querySelectorAll("[data-say]")) b.onclick = () => say(b.dataset.say);
    $("#chat-form", box).onsubmit = (e) => { e.preventDefault(); const i = $("#chat-in", box); const t = i.value; i.value = ""; say(t); };
    const log = $("#chat-log", box); log.scrollTop = log.scrollHeight;
  };

  const drawBook = () => {
    const family = d.scope === "family";
    const src = (h) => esc((d.sources.find(s => s.source === h.source) || {}).label || h.source);
    const assets = d.net_worth.assets || 1;
    const known = new Set(BOOK.flatMap(g => g.classes));
    const groups = BOOK.map(g => ({...g, rows: d.holdings.filter(h => g.classes.includes(h.class))}))
      .concat([{id: "other", label: "Khác", color: "var(--other)", rows: d.holdings.filter(h => !known.has(h.class))}])
      .filter(g => g.rows.length);
    const cols = family ? 8 : 7;
    const body = groups.map(g => {
      const rows = g.rows.map(h => ({h, r: bookRow(h, d.as_of)}));
      const total = rows.reduce((a, x) => a + x.h.value, 0);
      const priced = rows.filter(x => x.r.pnl != null);
      const pnl = priced.length ? priced.reduce((a, x) => a + x.r.pnl, 0) : null;
      const cost = priced.reduce((a, x) => a + (x.r.cost || 0), 0);
      const open = !closed[g.id];
      const head = `<tr class="grouprow" data-group="${g.id}" tabindex="0" aria-expanded="${open}">
        <td colspan="${cols - 3}"><span class="caret" aria-hidden="true">${icon("chevron", {size: 14})}</span>
          <span class="ic-chip sm" style="--tone:${g.color}">${icon(g.icon || CLASS_ICON[g.id] || "wallet", {size: 12})}</span>
          <b>${esc(g.label)}</b> <span class="muted small">${rows.length} khoản${g.debt ? "" : ` · ${pct(total / assets, false, total / assets < 0.1 ? 1 : 0)} tài sản`}</span></td>
        <td class="r">${cost && !g.debt ? vnd(cost) : ""}</td><td class="r"><b>${g.debt ? "−" : ""}${vnd(total)}</b></td>
        <td class="r">${g.debt ? "" : pnlCell(pnl, pnl != null && cost ? pnl / cost : null)}</td></tr>`;
      const lines = open ? rows.map(({h, r}) => `<tr>
        ${family ? `<td class="wide">${esc(h.owner_name)}</td>` : ""}
        <td><div>${esc(h.name)}</div>${r.note ? `<div class="small muted">${esc(r.note)}</div>` : ""}<div class="small muted narrow-only">${family ? esc(h.owner_name) + " · " : ""}${src(h)}</div></td>
        <td class="wide"><div>${src(h)}</div><span class="pill ${(TRUST[h.trust] || [""])[0]}">${(TRUST[h.trust] || ["", h.trust])[1]}</span></td>
        <td class="nowrap">${r.bought || `<span class="muted">—</span>`}</td>
        <td class="r wide">${r.price || `<span class="muted">—</span>`}</td>
        <td class="r">${r.cost != null && h.kind === "asset" ? vnd(r.cost) : `<span class="muted">—</span>`}</td>
        <td class="r">${h.kind === "liability" ? "−" : ""}${vnd(h.value)}</td>
        <td class="r">${h.kind === "liability" ? `<span class="muted">—</span>` : pnlCell(r.pnl, r.ret, r.accrued)}</td></tr>`).join("") : "";
      return `<tbody>${head}${lines}</tbody>`;
    }).join("");
    const nw = d.net_worth;
    const foot = (label, v, cls = "") => `<tr class="${cls}"><td colspan="${cols - 2}">${label}</td><td class="r">${v}</td><td></td></tr>`;
    $("#book", box).innerHTML = `<h3>Tất cả tài sản và khoản nợ <span class="hint">${d.holdings.length} khoản · ${groups.length} nhóm · bấm tên nhóm để thu gọn</span></h3>
      <div class="scrollx"><table class="table book">
        <thead><tr>${family ? `<th class="wide">Chủ sở hữu</th>` : ""}<th>Khoản</th><th class="wide">Nguồn · độ tin cậy</th><th>Ngày mua</th>
          <th class="r wide">Giá mua</th><th class="r">Giá vốn</th><th class="r">Giá trị hiện tại</th><th class="r">Lãi / lỗ</th></tr></thead>
        ${body}
        <tfoot>${foot("Tổng tài sản", vnd(nw.assets))}${foot("Tổng nợ", "−" + vnd(nw.liabilities))}${foot("<b>Tài sản ròng</b>", `<b>${vnd(nw.value)}</b>`, "total")}</tfoot>
      </table></div>
      <p class="footnote">Giá vốn: tổng số tiền đã bỏ ra · lãi/lỗ so với giá vốn, chưa trừ thuế phí · tiền gửi: lãi dồn tích đến ${esc(day(d.as_of))} · “—”: nguồn chưa cung cấp.</p>`;
    for (const row of box.querySelectorAll("[data-group]")) {
      const flip = () => { closed[row.dataset.group] = !closed[row.dataset.group]; keep("mf.book.closed", closed); drawBook(); };
      row.onclick = flip;
      row.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); flip(); } };
    }
  };

  drawUpload(); drawChat(); drawBook();
}
