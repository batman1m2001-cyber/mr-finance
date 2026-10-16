/* Radar chính sách (BRD-FR-306, F-D8; F9): the policy documents Compliance tracks, where each stands and what changed
   since the reader last looked, and the policy agent's summary of a verified document with each quote marked in the
   document's own text. Compliance adds (from the Official Gazette, or an official page with pasted text), a second
   Compliance person verifies the source, Compliance updates the status and runs the agent; the CIO reads.
   GET /api/policy[?since], /api/policy/{id}; POST /api/policy, /verify, /status, /summarise. */
import {empty, esc, get, post, toast, when} from "../core/core.js";

const TONE = {draft: "", consultation: "warn", issued: "ai", effective: "good", dropped: ""};
const badge = (s, label) => `<span class="badge ${TONE[s] || ""}">${esc(label)}</span>`;
const SEEN = "mf.radar.seen";

function seen(v) {
  try { if (v === undefined) return Number(localStorage.getItem(SEEN) || 0); localStorage.setItem(SEEN, String(v)); }
  catch (e) { /* private window: every visit is a first look */ }
  return 0;
}

export async function render(box, ctx) {
  const p = ctx.param || "";
  return p.startsWith("PD-") ? renderOne(box, ctx, p) : renderList(box, ctx);
}

async function renderList(box, ctx) {
  const since = seen();
  const d = await get(`/api/policy?since=${since}`);
  seen(Date.now() / 1000);
  const cmp = ctx.role === "compliance";
  const counts = Object.entries(d.statuses).map(([k, label]) => `${badge(k, label)} ${d.counts[k]}`).join(" ");
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">${cmp ? "Tuân thủ" : "CIO"} · Radar chính sách <span class="badge warn">Đề xuất</span></div>
      <div class="h1">${d.documents.length} văn bản theo dõi${since ? ` · ${d.changed} thay đổi từ lần xem trước` : ""}</div>
      <div class="lede small">Cách hiểu của chúng tôi về “radar chính sách” (BRD chưa mô tả, Q-09): văn bản chính sách đang theo dõi, trạng thái và lịch sử
        của từng văn bản, những gì đổi từ lần bạn xem trước, và bản tóm tắt của Agent Chính sách — mỗi ý kèm câu trích nguyên văn đã đối chiếu với văn bản.
        Agent chỉ đọc văn bản đã được người thứ hai xác nhận nguồn, không đọc danh mục hay dữ liệu khách hàng.</div>
      <div class="row" style="margin-top:8px;flex-wrap:wrap;gap:6px">${counts}</div></div></div>
    ${cmp ? `<div class="panel" style="margin-bottom:16px"><details class="more" ${d.documents.length ? "" : "open"}><summary>Thêm văn bản</summary>
      <form id="add" class="cols" style="margin-top:8px">
        <label class="field c12">Từ Công báo (congbao.chinhphu.vn/van-ban/…): máy chủ tải tệp PDF đã ký và lấy chữ
          <input name="gazette_url" placeholder="https://congbao.chinhphu.vn/van-ban/…"></label>
        <details class="c12 more"><summary>Hoặc trang chính thức khác (dự thảo, lấy ý kiến): dán văn bản</summary>
          <div class="cols" style="margin-top:8px">
            <label class="field c6">Địa chỉ nguồn (https, tên miền chính thức)<input name="source_url"></label>
            <label class="field c6">Tên văn bản<input name="title"></label>
            <label class="field c3">Số hiệu<input name="number"></label>
            <label class="field c3">Cơ quan ban hành<input name="issuer"></label>
            <label class="field c3">Ngày<input name="issued" placeholder="dd/mm/yyyy"></label>
            <label class="field c3">Trạng thái<select name="status">${Object.entries(d.statuses).map(([k, l]) => `<option value="${k}">${esc(l)}</option>`).join("")}</select></label>
            <label class="field c12">Văn bản (có thể để trống khi chưa có)<textarea name="text" rows="5"></textarea></label>
          </div></details>
        <label class="field c12">Ghi chú<input name="note" placeholder="Vì sao theo dõi văn bản này"></label>
        <div class="c12 row"><button class="btn primary" type="submit">Thêm vào radar</button></div>
      </form></details></div>` : ""}
    <div class="panel" style="padding:8px">${d.documents.length ? `<div class="list">${d.documents.map(x => `
      <a class="item" href="${ctx.href("chinh-sach", x.id)}" style="text-decoration:none;color:inherit;grid-template-columns:auto 1fr auto">
        <span class="badge mono">${esc(x.id)}</span>
        <div><div class="t">${esc(x.title)}${x.new ? ` <span class="badge ai">Mới</span>` : x.changed ? ` <span class="badge warn">Thay đổi</span>` : ""}</div>
          <div class="m">${esc([x.number, x.issuer, x.issued].filter(Boolean).join(" · "))} · ${x.verified ? `nguồn đã xác nhận (${esc(x.verified.by)})` : `<span class="warn-text">chưa xác nhận nguồn</span>`}
            · ${x.summary ? `có tóm tắt (${x.summary.mode === "live" ? "AI" : "mô phỏng"})` : "chưa tóm tắt"} · đổi ${when(x.changed_at)}</div>
          <div class="m">${x.history.map(h => esc(d.statuses[h.status])).join(" → ")}</div></div>
        ${badge(x.status, x.status_label)}</a>`).join("")}</div>` : empty("Chưa có văn bản", cmp ? "Mở “Thêm văn bản”." : "Tuân thủ thêm văn bản vào radar.")}</div>`;

  const form = box.querySelector("#add");
  if (!form) return;
  form.onsubmit = async (e) => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(form));
    const item = f.gazette_url.trim() ? {gazette_url: f.gazette_url.trim(), note: f.note}
      : {source_url: f.source_url, title: f.title, number: f.number, issuer: f.issuer, issued: f.issued, status: f.status, text: f.text, note: f.note};
    const btn = form.querySelector("[type=submit]"); btn.disabled = true; btn.textContent = "Đang tải…";
    try { const r = await post("/api/policy", {item, by: ctx.user}); ctx.go(ctx.href("chinh-sach", r.document.id)); }
    catch (err) { toast(err.message); btn.disabled = false; btn.textContent = "Thêm vào radar"; }
  };
}

/* the document's text with each quote marked and each article heading an anchor */
function marked(textNorm, quotes) {
  let html = esc(textNorm);
  quotes.forEach((q, k) => {
    const e = esc(q);
    html = html.replace(e, `<mark id="q${k + 1}" title="Trích dẫn ${k + 1}">${e}</mark>`);
  });
  return html.replace(/(Điều \d+\.)/g, "<br><br><b>$1</b>");
}

async function renderOne(box, ctx, id) {
  const {document: d} = await get(`/api/policy/${encodeURIComponent(id)}`);
  const cmp = ctx.role === "compliance", s = d.summary;
  const textNorm = (d.text || "").split(/\s+/).join(" ").trim();
  const STATUSES = {draft: "Dự thảo", consultation: "Lấy ý kiến", issued: "Đã ban hành", effective: "Có hiệu lực", dropped: "Dừng / bãi bỏ"};
  box.innerHTML = `
    <div class="pagehead"><div><a class="small" href="${ctx.href("chinh-sach")}">← Radar chính sách</a>
      <div class="eyebrow" style="margin-top:6px">${esc(d.id)} · ${esc([d.number, d.issuer, d.issued].filter(Boolean).join(" · "))}</div>
      <div class="h1">${esc(d.title)}</div></div>${badge(d.status, d.status_label)}</div>
    <div class="cols">
      <div class="c8" style="display:grid;gap:16px;align-content:start">
        <div class="panel"><h3>Tóm tắt của Agent Chính sách</h3>
          ${s ? `<div class="small muted">${s.mode === "live" ? `<span class="badge ai">AI · ${esc(s.model)}</span>` : `<span class="badge">Mô phỏng — không gọi mô hình</span>`}
              · ${esc(s.run_id)} · ${when(s.at)} · ${s.attempts} lần · mọi trích dẫn đã đối chiếu nguyên văn trong điều được nêu</div>
            <p style="margin-top:8px">${esc(s.summary)}</p>
            <ol>${s.points.map((p, k) => `<li style="margin:8px 0"><b>${esc(p.point)}</b> <span class="small muted">(${esc(p.article)})</span>
              <div class="small"><button type="button" class="linkish" data-q="${k + 1}" title="Xem trong văn bản">“${esc(p.quote)}”</button></div></li>`).join("")}</ol>
            <div class="small muted">Nội bộ — không gửi khách hàng; không kết luận cho khách hàng hay danh mục nào.</div>`
            : `<p class="small muted">${d.verified ? "Chưa có tóm tắt." : "Agent chỉ tóm tắt văn bản đã xác nhận nguồn."}</p>`}
          ${cmp && d.verified ? `<div class="row mt"><button type="button" class="btn sm primary" id="run">${s ? "Tóm tắt lại" : "Chạy Agent Chính sách"}</button></div>` : ""}</div>
        <div class="panel"><h3>Văn bản</h3>${textNorm ? `<div class="small muted">${new Set(d.articles.map(a => a.label)).size} điều · ${d.fetched ? `chữ lấy từ <a href="${esc(d.file_url)}" target="_blank" rel="noopener">tệp PDF đã ký trên Công báo</a> (SHA-256 ${esc(d.file_sha256.slice(0, 12))}…)` : "văn bản dán, đối chiếu với nguồn khi xác nhận"}</div>
          <div class="small" style="margin-top:8px;max-height:520px;overflow:auto;line-height:1.6">${marked(textNorm, s ? s.points.map(p => p.quote) : [])}</div>`
          : `<p class="small muted">Chưa có văn bản.</p>`}</div>
      </div>
      <div class="c4" style="display:grid;gap:16px;align-content:start">
        <div class="panel"><h3>Nguồn</h3>
          <div class="small"><a href="${esc(d.source_url)}" target="_blank" rel="noopener">${esc(d.source_url)}</a></div>
          <div class="small" style="margin-top:6px">Thêm bởi ${esc(d.added_by)} · ${when(d.created)}</div>
          ${d.verified ? `<div class="small" style="margin-top:6px"><span class="badge good">Đã xác nhận nguồn</span> ${esc(d.verified.by)} · ${when(d.verified.at)}<br>${esc(d.verified.note)}</div>`
            : cmp ? `<label class="field mt">Xác nhận nguồn (người khác người thêm; từ 20 ký tự)<textarea id="vnote" rows="2"></textarea></label>
              <div class="row mt"><button type="button" class="btn sm primary" id="verify">Xác nhận nguồn</button></div>`
            : `<div class="small warn-text" style="margin-top:6px">Chưa xác nhận nguồn</div>`}</div>
        ${cmp ? `<div class="panel"><h3>Cập nhật trạng thái</h3>
          <label class="field">Trạng thái<select id="st">${Object.entries(STATUSES).filter(([k]) => k !== d.status).map(([k, l]) => `<option value="${k}">${esc(l)}</option>`).join("")}</select></label>
          <label class="field">Ngày<input id="sdate" placeholder="dd/mm/yyyy"></label>
          <label class="field">Ghi chú (nguồn của thông tin, từ 10 ký tự)<input id="snote"></label>
          <div class="row mt"><button type="button" class="btn sm" id="status">Ghi</button></div></div>` : ""}
        <div class="panel"><h3>Lịch sử</h3>${d.history.map(h => `<div class="small" style="margin:4px 0">${when(h.at)} · ${esc(h.by)} · ${badge(h.status, STATUSES[h.status])}${h.date ? ` (${esc(h.date)})` : ""}${h.note ? ` · ${esc(h.note)}` : ""}</div>`).join("")}</div>
      </div>
    </div>`;
  const act = async (path, body, btn) => {
    if (btn) { btn.disabled = true; }
    try { await post(path, {document_id: d.id, by: ctx.user, ...body}); toast("Đã ghi"); }
    catch (e) { toast(e.message); }
    renderOne(box, ctx, id);
  };
  box.querySelectorAll("[data-q]").forEach(b => b.onclick = () => {
    const m = box.querySelector(`#q${b.dataset.q}`);
    if (m) { m.scrollIntoView({block: "center", behavior: "smooth"}); m.classList.add("flash"); setTimeout(() => m.classList.remove("flash"), 1200); }
  });
  const run = box.querySelector("#run");
  if (run) run.onclick = () => { run.textContent = "Agent đang đọc…"; act("/api/policy/summarise", {}, run); };
  const verify = box.querySelector("#verify");
  if (verify) verify.onclick = () => act("/api/policy/verify", {note: box.querySelector("#vnote").value}, verify);
  const status = box.querySelector("#status");
  if (status) status.onclick = () => act("/api/policy/status", {status: box.querySelector("#st").value, date: box.querySelector("#sdate").value, note: box.querySelector("#snote").value}, status);
}
