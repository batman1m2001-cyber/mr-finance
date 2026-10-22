/* The header (UI redesign R1, R-D5): one search box and a notifications bell, both over existing reads.
   Search: the role's pages (from the shell) and POST /api/search (holdings, goals, clients, events, news,
   research the role may open). The bell: the client's or RM's “Điều đáng chú ý” (POST /api/feed), the CIO's new
   news, Compliance's held news; first, for every role, a follow-up the person set that fired and they have not
   opened (A6, POST /api/assistant/memory follow_ups). Keyboard: “/” focuses search, arrows move, Enter opens, Esc closes. */
import {$, esc, get, post, read, vnd} from "./core/core.js";
import {icon} from "./core/icons.js?v=20261016r1";

const KIND = {page: ["Trang", "layers"], holding: ["Tài sản", "wallet"], goal: ["Mục tiêu", "target"], client: ["Khách hàng", "user"],
  event: ["Sự kiện", "news"], news: ["Tin", "news"], research: ["Nghiên cứu", "file"]};
const fold = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();

export function mount(shell) {
  const box = $("#search"), input = $("#q"), pop = $("#q-results");
  let hits = [], at = -1, seq = 0, timer = null;

  const close = () => { pop.hidden = true; input.setAttribute("aria-expanded", "false"); at = -1; };
  const draw = (q) => {
    if (!q) { close(); return; }
    pop.hidden = false; input.setAttribute("aria-expanded", "true");
    if (!hits.length) { pop.innerHTML = `<div class="pop-empty">Không thấy “${esc(q)}” trong những gì vai trò này mở được.</div>`; return; }
    let last = null;
    pop.innerHTML = hits.map((h, i) => {
      const head = h.kind !== last ? `<div class="pop-head">${KIND[h.kind][0]}</div>` : "";
      last = h.kind;
      return `${head}<a role="option" id="q-${i}" class="pop-item" href="${esc(h.route)}" data-i="${i}" aria-selected="${i === at}">
        <span class="ic-chip">${icon(KIND[h.kind][1])}</span><span class="pop-t"><b>${esc(h.label)}</b>${h.sub ? `<small>${esc(h.sub)}</small>` : ""}</span>
        ${h.value != null ? `<span class="num small muted">${vnd(h.value)}</span>` : ""}</a>`;
    }).join("");
    if (at >= 0) input.setAttribute("aria-activedescendant", `q-${at}`);
  };
  const open = (h) => {
    close(); input.value = ""; input.blur();
    if (h.client_id) shell.setClient(h.client_id);
    shell.go(h.route);
  };
  const run = async () => {
    const q = input.value.trim(), mine = ++seq;
    const role = shell.role();
    const pages = shell.pages(role).filter(p => fold(`${p.label} ${p.also || ""}`).includes(fold(q)))
      .map(p => ({kind: "page", label: p.label, sub: p.parent || "", route: p.route}));
    hits = pages; at = -1; draw(q);
    if (q.length < 2) return;
    try {
      const r = await post("/api/search", {q, role, client_id: shell.client(), scope: shell.scope()});
      if (mine !== seq) return;
      hits = pages.concat(r.search.hits); draw(q);
    } catch (_) { /* pages still shown */ }
  };
  input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(run, 180); });
  input.addEventListener("focus", () => { if (input.value.trim()) run(); });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!hits.length) return;
      at = (at + (e.key === "ArrowDown" ? 1 : -1) + hits.length) % hits.length;
      draw(input.value.trim());
      const el = $(`#q-${at}`, pop); if (el) el.scrollIntoView({block: "nearest"});
    } else if (e.key === "Enter") {
      e.preventDefault();
      const h = hits[at >= 0 ? at : 0]; if (h) open(h);
    } else if (e.key === "Escape") { close(); input.blur(); }
  });
  pop.addEventListener("click", (e) => {
    const a = e.target.closest("[data-i]"); if (!a) return;
    e.preventDefault(); open(hits[Number(a.dataset.i)]);
  });
  document.addEventListener("click", (e) => { if (!box.contains(e.target)) close(); });
  // a phone: the box is behind a search button (tokens.css .qopen); it opens focused, and closes when left empty
  const top = $(".shell-top"), qOpen = $("#q-open");
  const shown = (on) => { top.classList.toggle("q-shown", on); qOpen.setAttribute("aria-expanded", String(on)); };
  qOpen.onclick = () => { const on = !top.classList.contains("q-shown"); shown(on); if (on) input.focus(); };
  input.addEventListener("blur", () => setTimeout(() => { if (!input.value.trim() && pop.hidden) shown(false); }, 150));
  window.addEventListener("hashchange", () => shown(false));
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) { e.preventDefault(); input.focus(); }
  });

  // ── the bell ───────────────────────────────────────────────────────────
  const bell = $("#bell"), bpop = $("#bell-pop");
  let items = [], key = "";
  const SEV = {high: "bad", medium: "warn", info: ""};  // a feed item's severity, and an alert's
  const load = async () => {
    const role = shell.role(), client = shell.client(), scope = shell.scope();
    const k = `${role}|${client}|${scope}`;
    if (k === key) return;
    key = k;
    try {
      if ((role === "client" || role === "rm") && !client) items = [];  // a new RM, no family assigned yet (Q-25)
      else if (role === "client" || role === "rm") {
        const f = (await post("/api/feed", {client_id: client, scope, role})).feed;
        const where = role === "client" ? {impact: "#/client/tin/thi-truong", detail: "#/client/tong-quan/chi-tiet", flow: "#/client/tong-quan/toan-canh"}
          : {impact: "#/rm/khach-hang/tac-dong", detail: "#/rm/khach-hang/tong-quan", flow: "#/rm/khach-hang/toan-canh"};
        items = f.items.map(i => ({title: i.title, sub: i.why, tone: SEV[i.severity], route: where[i.link] || where.detail, focus: i.key, high: i.severity === "high"}));
      } else if (role === "specialist") {  // the action recommendations waiting for this specialist (G8)
        const q = (await get("/api/review?status=pending_specialist")).items;
        items = q.map(x => ({title: x.title, sub: x.client_name, tone: "warn", route: "#/specialist/duyet", focus: `review:${x.id}`}));
      } else {
        // staff: the alerts of the kinds the role looks after first (NFR-12), then the role's own queue
        const al = (await get("/api/system/alerts")).alerts.filter(a => a.status === "open");
        const alerts = al.map(a => ({title: a.title, sub: `${a.label}${a.count > 1 ? ` · ${a.count} lần` : ""}`, tone: SEV[a.severity],
          route: (WHERE[role] || {})[a.kind] || `#/${role}`, alert: a.id}));
        let rest = [], total = 0;
        if (role === "cio") {  // the high-relevance new news, as the desk counts them (“100 liên quan cao”), not all 800
          const n = (await get("/api/news/inbox?relevance=high&limit=1000")).items;
          rest = n.slice(0, 8).map(i => ({title: i.title, sub: i.outlet || "", tone: "", route: "#/cio/hop-tin"}));
          total = n.length;
        } else if (role === "compliance") {
          const n = (await get("/api/news/inbox?held=1")).items.filter(i => i.status !== "released");
          rest = n.slice(0, 8).map(i => ({title: i.title, sub: "Tin bị giữ", tone: "warn", route: "#/compliance/giu"}));
          total = n.length;
        }
        items = [...alerts, ...rest];
        items.total = alerts.length + total;
      }
    } catch (_) { items = []; }
    try {  // the person's own follow-ups that fired (A6): first, until opened
      const who = {role, client_id: role === "client" || role === "rm" ? client : null};
      const fired = (await read("/api/assistant/memory", {...who, action: "follow_ups"})).memory.unseen;
      const fu = fired.map(f => ({title: `Theo dõi: ${f.text}`, sub: f.fired_text,
        tone: "warn", route: `#/${role}/bo-nho`, followUp: f.id}));
      if (fu.length) { const total = items.total; items = [...fu, ...items]; if (total != null) items.total = total + fu.length; }
    } catch (_) { /* the bell without them */ }
    const count = items.total != null ? items.total : items.length;
    bell.dataset.count = count ? (count > 99 ? "99+" : String(count)) : "";
    bell.setAttribute("aria-label", count ? `Thông báo: ${count}` : "Thông báo: không có");
    if (!bpop.hidden) drawBell();
  };
  // where an alert's cause is seen, by role (Admin: Hệ thống lists them all)
  const WHERE = {
    admin: {news_feed: "#/admin/he-thong", market_job: "#/admin/du-lieu", agent: "#/admin/he-thong", audit_chain: "#/admin/nhat-ky", inbox: "#/admin/he-thong", zone_sync: "#/admin/he-thong"},
    cio: {news_feed: "#/cio/hop-tin", market_job: "#/cio/mo-hinh/du-lieu", agent: "#/cio/nhan-dinh", inbox: "#/cio/nhan-dinh"},
    compliance: {audit_chain: "#/compliance/nhat-ky"},
  };
  const TITLE = {client: "Điều đáng chú ý", rm: "Điều đáng chú ý · khách đang chọn", cio: "Cảnh báo và tin liên quan cao trong hộp tin",
    compliance: "Cảnh báo và tin đang bị giữ", admin: "Cảnh báo hệ thống", specialist: "Khuyến nghị chờ bạn duyệt"};
  const drawBell = () => {
    bpop.innerHTML = `<div class="pop-head">${TITLE[shell.role()]}</div>${items.length ? items.map((i, n) =>
      `<a class="pop-item" href="${esc(i.route)}" data-b="${n}"><span class="dot ${i.tone}"></span><span class="pop-t"><b>${esc(i.title)}</b><small>${esc(i.sub)}</small></span>${i.alert ? `<button type="button" class="btn sm" data-ack="${esc(i.alert)}" title="Đánh dấu đã xem (ghi vào nhật ký)">Đã xem</button>` : ""}</a>`).join("")
      : `<div class="pop-empty">Không có gì cần chú ý lúc này.</div>`}`;
  };
  bell.onclick = (e) => { e.stopPropagation(); bpop.hidden = !bpop.hidden; bell.setAttribute("aria-expanded", String(!bpop.hidden)); if (!bpop.hidden) drawBell(); };
  bpop.addEventListener("click", async (e) => {
    const ackBtn = e.target.closest("[data-ack]");
    if (ackBtn) {  // “Đã xem”: audited (alert.ack); the alert stays in Hệ thống until the thing works again
      e.preventDefault(); e.stopPropagation(); ackBtn.disabled = true;
      try { await post("/api/system/alerts/ack", {alert_id: ackBtn.dataset.ack, by: shell.user()}); } catch (_) { ackBtn.disabled = false; return; }
      key = ""; await load(); drawBell(); return;
    }
    const a = e.target.closest("[data-b]"); if (!a) return;
    e.preventDefault(); bpop.hidden = true;
    const it = items[Number(a.dataset.b)];
    // the client opened a high-level item (BRD-KPI-07): recorded, never in the way of opening it
    if (shell.role() === "client" && it.high) post("/api/feed/open", {client_id: shell.client(), key: it.focus}).catch(() => {});
    if (it.followUp) {  // opened: it leaves the bell (A6)
      const role = shell.role();
      post("/api/assistant/memory", {role, client_id: role === "client" || role === "rm" ? shell.client() : null, action: "follow_up_seen", key: it.followUp})
        .then(() => { key = ""; load(); }).catch(() => {});
    }
    shell.go(it.route, it.focus ? [it.focus] : null);
  });
  document.addEventListener("click", (e) => { if (!bpop.hidden && !bpop.contains(e.target)) { bpop.hidden = true; bell.setAttribute("aria-expanded", "false"); } });
  return {refresh: load};
}
