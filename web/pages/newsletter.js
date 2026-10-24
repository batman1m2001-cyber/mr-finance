/* Bài viết (BRD-FR-801, CONTENT-01 flow 1, CONTENT-02, SEC-04; F8; OWN-FB-15): the CIO writes an article of their own
   (title and body: their news or a policy note, for Private clients only), or drafts a general market letter from
   approved views (by template, or with the CIO agent writing the opening under the content guard), Compliance approves
   or returns it, and it is a preview: nothing is sent. Private and retail clients receive it at the same time unless
   the CIO records why Private should have it earlier. GET /api/newsletters[/{id}], POST /api/newsletters[/act]. */
import {empty, esc, get, post, toast, when} from "../core/core.js";

const STATUS = {DRAFT: ["", "Nháp"], RETURNED: ["warn", "Bị trả lại"], PENDING_COMPLIANCE: ["warn", "Chờ Tuân thủ duyệt"],
  APPROVED: ["good", "Đã duyệt · xem trước"], WITHDRAWN: ["", "Đã rút"]};
const badge = (s) => `<span class="badge ${(STATUS[s] || [""])[0]}">${esc((STATUS[s] || [, s])[1])}</span>`;
const INTRO_BY = {template: "theo mẫu", live: "AI viết (CIO agent)", mock: "theo mẫu (AI mô phỏng)"};

export async function render(box, ctx) {
  const p = ctx.param || "";
  return p.startsWith("NL-") ? renderOne(box, ctx, p) : renderList(box, ctx);
}

function tomorrow8() {
  const d = new Date(Date.now() + 86400000);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T08:00`;
}

async function renderList(box, ctx) {
  const d = await get("/api/newsletters");
  const cio = ctx.role === "cio";
  const waiting = d.newsletters.filter(n => n.status === "PENDING_COMPLIANCE").length;
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">${cio ? "CIO" : "Tuân thủ"} · Bài viết</div>
      <div class="h1">${d.newsletters.length} bài viết · ${waiting} chờ duyệt</div>
      <div class="lede small">Bài của CIO, hoặc bản tin từ nhận định đã duyệt. Người duyệt khác người viết. Bản demo chỉ xem trước, không gửi thật.</div></div></div>
    ${cio ? `<div class="panel" style="margin-bottom:16px"><details class="more" ${d.newsletters.length ? "" : "open"}><summary>Viết bài mới</summary>
      <form id="nl" class="cols" style="margin-top:8px">
        <label class="field c12">Tiêu đề<input name="title" placeholder="Để trống: theo ngày"></label>
        <label class="field c12">Nội dung <span class="muted">(tin của bạn hoặc chính sách; dòng trống để xuống đoạn)</span><textarea name="body" rows="7" maxlength="6000"></textarea></label>
        <details class="more c12"><summary>Hoặc dựng từ nhận định đã duyệt (1–6)</summary>
          ${d.approved_views.length ? `<div class="list" style="margin-top:6px">${d.approved_views.map(v => `<label class="item" style="grid-template-columns:auto 1fr;cursor:pointer">
          <input type="checkbox" name="views" value="${esc(v.id)}"><div><div class="t mono">${esc(v.id)}</div><div class="m" data-quote>${esc(v.summary)}</div></div></label>`).join("")}</div>` : `<p class="small muted">Chưa có nhận định nào đã duyệt.</p>`}</details>
        <div class="c12 small muted aud">Bài không kèm nhận định chỉ gửi khách Private.</div>
        <label class="field c3 fromviews" hidden>Phần mở đầu<select name="mode"><option value="template">Theo mẫu</option><option value="agent">CIO agent viết (qua kiểm tra nội dung)</option></select></label>
        <label class="field c3">Gửi lúc<input name="send_at" type="datetime-local" value="${tomorrow8()}" required></label>
        <label class="field c3 fromviews" hidden>Private nhận sớm hơn (giờ)<input name="early" type="number" min="0" max="72" value="0"></label>
        <label class="field c9 early" hidden>Căn cứ cho Private nhận sớm (từ 20 ký tự; Tuân thủ xem)<input name="early_reason"></label>
        <label class="field c3">Xung đột lợi ích<select name="related"><option value="">Không liên quan bên liên quan</option><option value="1">Có</option></select></label>
        <label class="field c3 coi" hidden>Bên liên quan<input name="parties" placeholder="TCBS"></label>
        <label class="field c6 coi" hidden>Lời công bố (từ 20 ký tự)<input name="statement"></label>
        <div class="c12 row"><button class="btn primary" type="submit">Lưu bản nháp</button></div>
      </form></details></div>` : ""}
    <div class="panel" style="padding:8px">${d.newsletters.length ? `<div class="list">${d.newsletters.map(n => `
      <a class="item" href="${ctx.href("ban-tin", n.id)}" style="text-decoration:none;color:inherit;grid-template-columns:auto 1fr auto">
        <span class="badge mono">${esc(n.id)}</span>
        <div><div class="t">${esc(n.title)}</div><div class="m">${n.view_ids.length ? `${n.view_ids.length} nhận định` : "Bài viết · chỉ khách Private"} · soạn bởi ${esc(n.author)} · ${when(n.created)}${n.distribution.private_early_hours ? ` · <span class="warn-text">Private sớm ${n.distribution.private_early_hours} giờ</span>` : ""}</div></div>
        ${badge(n.status)}</a>`).join("")}</div>` : empty("Chưa có bài viết", cio ? "Mở “Viết bài mới”." : "Bài CIO gửi duyệt sẽ chờ ở đây.")}</div>`;

  const form = box.querySelector("#nl");
  if (!form) return;
  const early = form.querySelector("[name=early]"), rel = form.querySelector("[name=related]");
  early.oninput = () => { form.querySelector(".early").hidden = !(Number(early.value) > 0); };
  const picked = () => {  // views chosen: a letter to everyone, with its opening and the Private-early option
    const on = form.querySelectorAll("[name=views]:checked").length > 0;
    form.querySelectorAll(".fromviews").forEach(x => { x.hidden = !on; });
    form.querySelector(".aud").textContent = on ? "Bản tin từ nhận định: khách Private và đại chúng nhận cùng lúc, trừ khi ghi căn cứ cho Private nhận sớm."
      : "Bài không kèm nhận định chỉ gửi khách Private.";
    if (!on) { early.value = 0; early.oninput(); }
  };
  form.querySelectorAll("[name=views]").forEach(x => { x.onchange = picked; });
  rel.onchange = () => form.querySelectorAll(".coi").forEach(x => { x.hidden = !rel.value; });
  form.onsubmit = async (e) => {
    e.preventDefault();
    const f = new FormData(form);
    const body = {view_ids: f.getAll("views"), body: f.get("body") || "", by: ctx.user, title: f.get("title") || "", mode: f.get("mode"),
      distribution: {send_at: `${f.get("send_at")}:00+07:00`, private_early_hours: Number(f.get("early") || 0), early_reason: f.get("early_reason") || ""},
      conflict: {related: !!f.get("related"), parties: String(f.get("parties") || "").split(",").map(s => s.trim()).filter(Boolean), statement: f.get("statement") || ""}};
    const btn = form.querySelector("[type=submit]"); btn.disabled = true;
    try { const r = await post("/api/newsletters", body); ctx.go(ctx.href("ban-tin", r.newsletter.id)); }
    catch (err) { toast(err.message); btn.disabled = false; }
  };
}

function preview(n) {
  const l = n.labels;
  return `<article class="panel c8 letter" aria-label="Bản xem trước" style="align-self:start">
    <div class="notice small">Bản xem trước — không gửi thật trong demo.</div>
    <h2 class="h2" style="margin-top:12px">${esc(n.title)}</h2>
    <div class="small muted">${esc(l.time)} · ${esc(l.responsible)} · <span class="badge ai">${esc(l.ai)}</span></div>
    ${n.intro ? `<p style="margin-top:10px">${esc(n.intro)}</p>` : ""}
    ${(n.body || "").split("\n\n").filter(Boolean).map(p => `<p style="margin-top:10px">${esc(p)}</p>`).join("")}
    ${n.sections.map(s => `<section style="margin-top:14px"><h3>${esc(s.heading || s.event)}</h3>
      <div class="small muted">Nhận định CIO duyệt ngày ${when(s.approved)} · nguồn: ${s.outlets.map(esc).join(", ")}</div>
      <ul>${s.impacts.map(i => `<li>${esc(i)}</li>`).join("")}${s.tickers_not_named ? `<li class="muted">và ${s.tickers_not_named} tác động tới cổ phiếu cụ thể (không nêu tên trong bản tin chung)</li>` : ""}</ul>
      <div class="small">Kịch bản: ${s.branches.map(b => `<b>${esc(b.name)}</b> ${Math.round(b.probability * 100)}% (${b.shocks.map(esc).join(", ")})`).join(" · ")}</div></section>`).join("")}
    <footer class="small" style="margin-top:16px;border-top:1px solid var(--axis);padding-top:10px">
      <div>${esc(l.not_advice)}</div><div>${l.conflicts.map(esc).join("<br>")}</div><div class="muted">${esc(l.contact)}</div></footer>
  </article>`;
}

async function renderOne(box, ctx, id) {
  const {newsletter: n} = await get(`/api/newsletters/${encodeURIComponent(id)}`);
  const cio = ctx.role === "cio", edit = cio && ["DRAFT", "RETURNED"].includes(n.status);
  const dist = n.distribution;
  box.innerHTML = `
    <div class="pagehead"><div><a class="small" href="${ctx.href("ban-tin")}">← Bài viết</a>
      <div class="eyebrow" style="margin-top:6px">${esc(n.id)} · ${n.sections.length ? `phần mở đầu ${esc(INTRO_BY[n.intro_by] || `sửa bởi ${n.intro_by}`)}` : "bài viết của CIO"}</div>
      <div class="h1">${esc(n.title)}</div></div>${badge(n.status)}</div>
    <div class="cols">
      ${preview(n)}
      <div class="c4" style="display:grid;gap:16px;align-content:start">
        <div class="panel"><h3>Kiểm tra nội dung</h3>
          ${n.guard.ok ? `<div class="small"><span class="badge good">Đạt</span> không có từ ngữ khuyến nghị, mã cổ phiếu hay tên trong danh sách hạn chế; đủ nhãn.</div>`
            : n.guard.findings.map(f => `<div class="small bad-text">• ${esc(f)}</div>`).join("")}
          ${n.agent_findings.map(f => `<div class="small warn-text" style="margin-top:6px">${esc(f)}</div>`).join("")}</div>
        <div class="panel"><h3>Phân phối</h3>
          ${n.audience === "private" ? `<div class="small">Chỉ khách Private: ${when(dist.retail_at)}</div>` : dist.private_early_hours ? `<div class="small"><span class="badge warn">Private nhận sớm ${dist.private_early_hours} giờ</span></div>
            <div class="small" style="margin-top:6px">Private: ${when(dist.private_at)} · đại chúng: ${when(dist.retail_at)}</div>
            <div class="small" style="margin-top:6px"><b>Căn cứ:</b> ${esc(dist.early_reason)}</div>`
            : `<div class="small">Khách Private và đại chúng nhận cùng lúc: ${when(dist.retail_at)}</div>`}</div>
        ${edit ? `<div class="panel"><h3>Sửa</h3>
          <label class="field">Tiêu đề<input id="t" value="${esc(n.title)}"></label>
          ${n.sections.length ? `<label class="field">Phần mở đầu<textarea id="i" rows="5">${esc(n.intro)}</textarea></label>` : ""}
          <label class="field">Nội dung<textarea id="b" rows="8">${esc(n.body || "")}</textarea></label>
          ${n.sections.map((s, k) => `<label class="field">Tiêu đề phần ${k + 1}<input data-heading="${esc(s.view_id)}" value="${esc(s.heading || s.event)}"></label>`).join("")}
          <div class="row mt"><button type="button" class="btn sm" id="save">Lưu</button>
            <button type="button" class="btn sm primary" id="submit" ${n.guard.ok ? "" : "disabled"}>Gửi Tuân thủ duyệt</button></div></div>` : ""}
        ${!cio && n.status === "PENDING_COMPLIANCE" ? `<div class="panel"><h3>Tuân thủ duyệt</h3>
          <label class="field">Ghi chú (trả lại: từ 10 ký tự)<textarea id="note" rows="3"></textarea></label>
          <div class="row mt"><button type="button" class="btn sm primary" data-act="approve">Duyệt</button><button type="button" class="btn sm danger" data-act="return">Trả lại</button></div></div>` : ""}
        ${cio && ["PENDING_COMPLIANCE", "APPROVED", "DRAFT", "RETURNED"].includes(n.status) ? `<div class="row"><button type="button" class="btn sm" data-act="withdraw">Rút bản tin</button></div>` : ""}
        <div class="panel"><h3>Lịch sử</h3>${n.history.map(h => `<div class="small" style="margin:4px 0">${when(h.at)} · ${esc(h.by)} · ${badge(h.status)}${h.note ? ` · ${esc(h.note)}` : ""}</div>`).join("")}</div>
      </div>
    </div>`;
  const act = async (action, extra = {}) => {
    try { await post("/api/newsletters/act", {newsletter_id: n.id, action, by: ctx.user, ...extra}); toast("Đã ghi"); }
    catch (e) { toast(e.message); }
    renderOne(box, ctx, id);
  };
  const save = box.querySelector("#save");
  if (save) save.onclick = () => act("edit", {changes: {title: box.querySelector("#t").value, body: box.querySelector("#b").value,
    ...(box.querySelector("#i") ? {intro: box.querySelector("#i").value} : {}),
    headings: Object.fromEntries([...box.querySelectorAll("[data-heading]")].map(x => [x.dataset.heading, x.value]))}});
  const submit = box.querySelector("#submit");
  if (submit) submit.onclick = () => act("submit");
  box.querySelectorAll("[data-act]").forEach(b => b.onclick = () => act(b.dataset.act, {note: (box.querySelector("#note") || {}).value || ""}));
}
