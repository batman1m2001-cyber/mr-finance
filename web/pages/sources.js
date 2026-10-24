/* Nguồn tin (Admin, docs/NEWS_OPS_PLAN.md N1): the white list the daily collection reads, one row per source with
   its last 7 days, and the changes made here (add, edit, off/on, delete) kept on the page until Gửi đề xuất proposes
   the whole list as a new version of `news_sources`; an Admin approves it here or on Cấu hình, and the next run uses
   it. Thử reads a feed now and keeps nothing. GET /api/news/sources, /api/news/sources/test; POST
   /api/config/propose, /api/config/decide. */
import {ago, esc, get, num, post, toast} from "../core/core.js";

const KIND = {domestic: "Trong nước", intl: "Quốc tế"};
let draft = null;  // {base: hash of the list it started from, list}: the changes not yet proposed
const tried = {};  // url → the last Thử answer
const open = new Set();  // the rows whose edit fields are open

const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const slug = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/gi, "d").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");

function changes(from, to) {
  const was = Object.fromEntries(from.map(s => [s.id, s]));
  const now = new Set(to.map(s => s.id));
  return {
    added: to.filter(s => !was[s.id]).length,
    removed: from.filter(s => !now.has(s.id)).length,
    changed: to.filter(s => was[s.id] && !same(was[s.id], s)).length,
  };
}

function health(h) {
  if (!h) return `<span class="muted">7 ngày: chưa lấy lần nào</span>`;
  const bad = h.failed ? ` · <span class="warn-text" title="${esc(h.last_error ? h.last_error.error : "")}">${h.failed} lỗi${h.last_error ? `, gần nhất ${esc(ago(h.last_error.at))}` : ""}</span>` : "";
  return `7 ngày: ${num(h.attempted)} lần · ${num(h.fetched)} tin đọc được${bad}`;
}

function test(url) {
  const t = tried[url];
  if (!t) return "";
  if (t === "busy") return `<div class="m" role="status">Đang thử…</div>`;
  return t.ok
    ? `<div class="m good-text" role="status">Đọc được ${t.items} tin (${t.ms} ms)${t.newest ? ` · mới nhất: “${esc(t.newest.title)}”` : ""}</div>`
    : `<div class="m bad-text" role="status">Không đọc được: ${esc(t.error)}</div>`;
}

function row(s, d, was) {
  const tag = !was ? `<span class="badge">Mới</span>` : !same(was, s) ? `<span class="badge warn">Đã sửa</span>` : "";
  return `<div class="item" data-src="${esc(s.id)}">
    <span class="badge ${s.approved ? "good" : ""}">${s.approved ? "Bật" : "Tắt"}</span>
    <div><div class="t">${esc(s.outlet)} · ${esc(s.section)} <span class="small muted">${KIND[s.kind] || esc(s.kind)}</span> ${tag}</div>
      <div class="m mono" style="word-break:break-all">${esc(s.url)}</div>
      <div class="m">${health(d.health[s.id])}</div>${test(s.url)}
      <div class="row tight mt-xs">
        <button type="button" class="btn sm" data-act="test">Thử</button>
        <button type="button" class="btn sm" data-act="flip">${s.approved ? "Tắt" : "Bật"}</button>
        <button type="button" class="btn sm" data-act="edit" aria-expanded="${open.has(s.id)}">Sửa</button>
        <button type="button" class="btn sm ghostbtn" data-act="drop">Xoá</button></div>
      ${!open.has(s.id) ? "" : `<div class="row mt-xs" data-edit>
        <label class="fld"><span>Báo</span><input data-f="outlet" value="${esc(s.outlet)}" maxlength="60"></label>
        <label class="fld"><span>Chuyên mục</span><input data-f="section" value="${esc(s.section)}" maxlength="60"></label>
        <label class="fld" style="flex:2"><span>URL (https)</span><input data-f="url" value="${esc(s.url)}" maxlength="300"></label>
        <label class="fld"><span>Loại</span><select data-f="kind">${Object.entries(KIND).map(([k, l]) => `<option value="${k}" ${k === s.kind ? "selected" : ""}>${l}</option>`).join("")}</select></label>
      </div>`}</div><span></span></div>`;
}

export async function render(box, ctx) {
  const d = await get("/api/news/sources");
  const me = ctx.user;
  const base = JSON.stringify(d.sources);
  if (!draft || draft.base !== base) draft = {base, list: structuredClone(d.sources)};
  const list = draft.list;
  const was = Object.fromEntries(d.sources.map(s => [s.id, s]));
  const c = changes(d.sources, list);
  const dirty = c.added + c.removed + c.changed;
  const p = d.pending;
  const pc = p && changes(d.sources, p.data);
  const say = (x) => [x.added && `${x.added} thêm`, x.changed && `${x.changed} sửa`, x.removed && `${x.removed} xoá`].filter(Boolean).join(", ") || "không đổi gì";
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Quản trị</div>
      <h1 class="h1">Nguồn tin</h1>
      <p class="lede">${d.sources.length} nguồn · ${d.sources.filter(s => s.approved).length} đang bật · bản v${d.active.version}.
        Sửa ở đây rồi Gửi đề xuất; bản được duyệt dùng từ lần lấy tin sau.</p></div></div>
    ${p ? `<div class="note mt" role="note" id="src-pending"><b>Đề xuất v${p.version} chờ duyệt</b> · ${esc(say(pc))} · ${esc(p.proposed_by)} ${esc(ago(p.created))}${p.note ? ` · “${esc(p.note)}”` : ""}
      <div class="row tight mt"><button type="button" class="btn sm primary" data-decide="approve">Duyệt</button>
        <button type="button" class="btn sm" data-decide="reject">Từ chối</button></div></div>` : ""}

    <section class="panel mt" id="src-list"><div class="h3">Danh sách</div>
      <div class="list">${list.map(s => row(s, d, was[s.id])).join("")}</div>
      ${c.removed ? `<p class="small muted">Sẽ xoá: ${d.sources.filter(s => !list.some(x => x.id === s.id)).map(s => esc(`${s.outlet} · ${s.section}`)).join(", ")}</p>` : ""}</section>

    <section class="panel mt" id="src-add"><div class="h3">Thêm nguồn</div>
      <form class="row" id="src-add-form" autocomplete="off">
        <label class="fld"><span>Báo</span><input name="outlet" required maxlength="60"></label>
        <label class="fld"><span>Chuyên mục</span><input name="section" required maxlength="60"></label>
        <label class="fld" style="flex:2"><span>URL RSS (https)</span><input name="url" type="url" required pattern="https://.*" maxlength="300"></label>
        <label class="fld"><span>Loại</span><select name="kind">${Object.entries(KIND).map(([k, l]) => `<option value="${k}">${l}</option>`).join("")}</select></label>
        <button type="submit" class="btn">Thêm</button></form></section>

    <div class="panel mt row" id="src-send" style="position:sticky;bottom:0">
      <span class="small ${dirty ? "warn-text" : "muted"}" id="src-dirty">${dirty ? `Chưa gửi: ${esc(say(c))}` : "Không có thay đổi"}</span>
      <input id="src-note" maxlength="300" placeholder="Ghi chú cho người duyệt" style="flex:1" aria-label="Ghi chú cho người duyệt">
      <button type="button" class="btn sm ghostbtn" id="src-undo" ${dirty ? "" : "disabled"}>Bỏ thay đổi</button>
      <button type="button" class="btn sm primary" id="src-propose" ${dirty && !p ? "" : "disabled"} title="${p ? "Đã có một đề xuất chờ duyệt" : ""}">Gửi đề xuất</button></div>`;

  const again = () => { if (box.isConnected) render(box, ctx).catch(e => toast(e.message)); };
  const find = (el) => list.find(s => s.id === el.closest("[data-src]").dataset.src);
  box.querySelectorAll("[data-act]").forEach(b => b.onclick = async () => {
    const s = find(b);
    if (b.dataset.act === "edit") { open.has(s.id) ? open.delete(s.id) : open.add(s.id); }
    if (b.dataset.act === "flip") s.approved = !s.approved;
    if (b.dataset.act === "drop") list.splice(list.indexOf(s), 1);
    if (b.dataset.act === "test") {
      tried[s.url] = "busy"; again();
      try { tried[s.url] = await get(`/api/news/sources/test?url=${encodeURIComponent(s.url)}`); }
      catch (e) { tried[s.url] = {ok: false, error: e.message}; }
    }
    again();
  });
  box.querySelectorAll("[data-f]").forEach(i => i.onchange = () => {
    const v = i.value.trim();
    if (i.dataset.f === "url" && !v.startsWith("https://")) { toast("URL cần bắt đầu bằng https://"); i.value = find(i).url; return; }
    if (!v) { i.value = find(i)[i.dataset.f]; return; }
    find(i)[i.dataset.f] = v;
    again();
  });
  box.querySelector("#src-add-form").onsubmit = (e) => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target));
    let id = slug(`${f.outlet}_${f.section}`) || "nguon";
    for (let k = 2; list.some(s => s.id === id); k++) id = `${slug(`${f.outlet}_${f.section}`)}_${k}`;
    list.push({id, outlet: f.outlet.trim(), section: f.section.trim(), url: f.url.trim(), kind: f.kind, approved: true});
    again();
  };
  box.querySelector("#src-undo").onclick = () => { draft = null; again(); };
  box.querySelector("#src-propose").onclick = async (e) => {
    e.target.disabled = true;
    try {
      const r = await post("/api/config/propose", {kind: "news_sources", data: list, by: me, note: box.querySelector("#src-note").value.trim()});
      toast(`Đã gửi đề xuất v${(r.version || {}).version || ""}: chờ duyệt`); again();
    } catch (x) { toast(x.message); e.target.disabled = false; }
  };
  box.querySelectorAll("[data-decide]").forEach(b => b.onclick = async () => {
    b.disabled = true;
    try {
      await post("/api/config/decide", {version_id: p.id, action: b.dataset.decide, by: me});
      if (b.dataset.decide === "approve") draft = null;
      toast(b.dataset.decide === "approve" ? `Đã duyệt v${p.version}: dùng từ lần lấy tin sau` : "Đã từ chối"); again();
    } catch (x) { toast(x.message); b.disabled = false; }
  });
}
