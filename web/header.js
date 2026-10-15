/* The header (UI redesign R1, R-D5): one search box and a notifications bell, both over existing reads.
   Search: the role's pages (from the shell) and POST /api/search (holdings, goals, clients, events, news,
   research the role may open). The bell: the client's or RM's “Điều đáng chú ý” (POST /api/feed), the CIO's new
   news, Compliance's held news. Keyboard: “/” focuses search, arrows move, Enter opens, Esc closes. */
import {$, esc, get, post, vnd} from "./core/core.js";
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
    const pages = shell.pages(role).filter(p => fold(p.label).includes(fold(q)))
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
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) { e.preventDefault(); input.focus(); }
  });

  // ── the bell ───────────────────────────────────────────────────────────
  const bell = $("#bell"), bpop = $("#bell-pop");
  let items = [], key = "";
  const SEV = {high: "bad", medium: "warn", info: ""};
  const load = async () => {
    const role = shell.role(), client = shell.client(), scope = shell.scope();
    const k = `${role}|${client}|${scope}`;
    if (k === key) return;
    key = k;
    try {
      if (role === "client" || role === "rm") {
        const f = (await post("/api/feed", {client_id: client, scope, role})).feed;
        const where = role === "client" ? {impact: "#/client/tin/thi-truong", detail: "#/client/tong-quan/chi-tiet", flow: "#/client/tong-quan/toan-canh"}
          : {impact: "#/rm/khach-hang/tac-dong", detail: "#/rm/khach-hang/tong-quan", flow: "#/rm/khach-hang/toan-canh"};
        items = f.items.map(i => ({title: i.title, sub: i.why, tone: SEV[i.severity], route: where[i.link] || where.detail, focus: i.key}));
      } else if (role === "cio") {
        const n = (await get("/api/news/inbox?limit=200")).items;
        items = n.slice(0, 8).map(i => ({title: i.title, sub: i.outlet || "", tone: "", route: "#/cio/hop-tin"}));
        items.total = n.length;
      } else {
        const n = (await get("/api/news/inbox?held=1")).items.filter(i => i.status !== "released");
        items = n.slice(0, 8).map(i => ({title: i.title, sub: "Tin bị giữ", tone: "warn", route: "#/compliance/giu"}));
        items.total = n.length;
      }
    } catch (_) { items = []; }
    const count = items.total != null ? items.total : items.length;
    bell.dataset.count = count ? String(Math.min(count, 99)) : "";
    bell.setAttribute("aria-label", count ? `Thông báo: ${count}` : "Thông báo: không có");
    if (!bpop.hidden) drawBell();
  };
  const TITLE = {client: "Điều đáng chú ý", rm: "Điều đáng chú ý · khách đang chọn", cio: "Tin mới trong hộp tin", compliance: "Tin đang bị giữ"};
  const drawBell = () => {
    bpop.innerHTML = `<div class="pop-head">${TITLE[shell.role()]}</div>${items.length ? items.map((i, n) =>
      `<a class="pop-item" href="${esc(i.route)}" data-b="${n}"><span class="dot ${i.tone}"></span><span class="pop-t"><b>${esc(i.title)}</b><small>${esc(i.sub)}</small></span></a>`).join("")
      : `<div class="pop-empty">Không có gì cần chú ý lúc này.</div>`}`;
  };
  bell.onclick = (e) => { e.stopPropagation(); bpop.hidden = !bpop.hidden; bell.setAttribute("aria-expanded", String(!bpop.hidden)); if (!bpop.hidden) drawBell(); };
  bpop.addEventListener("click", (e) => {
    const a = e.target.closest("[data-b]"); if (!a) return;
    e.preventDefault(); bpop.hidden = true;
    const it = items[Number(a.dataset.b)];
    shell.go(it.route, it.focus ? [it.focus] : null);
  });
  document.addEventListener("click", (e) => { if (!bpop.hidden && !bpop.contains(e.target)) { bpop.hidden = true; bell.setAttribute("aria-expanded", "false"); } });
  return {refresh: load};
}
