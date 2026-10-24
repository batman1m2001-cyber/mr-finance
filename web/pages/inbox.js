/* CIO · Hộp tin (FR-103): the news that passed the gates, newest first. Filter, pick several, group
   them into an event, or drop them. The strip on top is feed health: each source's last fetch and
   its items per hour over a day. */
import {EVENT_TYPE, ago, empty, esc, get, num, post, toast, when} from "../core/core.js";
import {spark} from "../charts/charts.js";

const REL = {high: ["bad", "Liên quan cao"], medium: ["warn", "Vừa"], low: ["", "Thấp"]};
const state = {source: "", kind: "", relevance: "", q: "", picked: new Set(), shown: 40};

export async function render(box, ctx) {
  // a page of rows; the total is counted by the server (it said 300 for 1,415 when it was the page's length)
  const params = new URLSearchParams({limit: String(state.shown)});
  for (const k of ["source", "kind", "relevance", "q"]) if (state[k]) params.set(k, state[k]);
  const d = await get(`/api/news/inbox?${params}`);
  const items = d.items;
  const total = d.total == null ? items.length : d.total;
  const last = d.last_run;
  const errors = d.sources.filter(s => s.last && s.last.error);
  box.innerHTML = `
    <div class="pagehead">
      <div><div class="eyebrow">CIO · Hộp tin</div><div class="h1">${num(total)} tin chờ xử lý</div>
        <div class="lede small">Lấy tin tự động mỗi 10 phút từ ${d.sources.length} nguồn công khai trong danh sách trắng. Lần gần nhất: ${last ? ago(last.at) : "chưa có"}${errors.length ? ` · <span class="down">${errors.length} nguồn lỗi</span>` : ""}.</div></div>
      <div class="row"><button type="button" class="btn" id="fetch">Lấy tin ngay</button></div>
    </div>
    <div class="panel flat" style="margin-bottom:16px">
      <details class="more"><summary>Tình trạng nguồn tin (24 giờ)</summary>
      <div class="scrollx"><table class="table"><thead><tr><th>Nguồn</th><th>Loại</th><th>Tin/giờ</th><th class="r">Lần trước</th></tr></thead><tbody>
      ${d.sources.map(s => `<tr><td>${esc(s.outlet)} <span class="muted small">${esc(s.section)}</span></td><td>${s.kind === "intl" ? "Quốc tế" : "Trong nước"}</td>
        <td>${spark(s.hourly)}</td><td class="r small">${s.last ? (s.last.error ? `<span class="down">lỗi</span>` : `${s.last.accepted} nhận · ${s.last.refused} từ chối`) : "—"}</td></tr>`).join("")}
      </tbody></table></div></details>
    </div>
    <div class="row" style="margin-bottom:12px">
      <select id="f-source" aria-label="Nguồn"><option value="">Mọi nguồn</option>${d.sources.map(s => `<option value="${esc(s.id)}" ${state.source === s.id ? "selected" : ""}>${esc(s.outlet)} · ${esc(s.section)}</option>`).join("")}</select>
      <select id="f-kind" aria-label="Loại"><option value="">Quốc tế + trong nước</option><option value="intl" ${state.kind === "intl" ? "selected" : ""}>Quốc tế</option><option value="domestic" ${state.kind === "domestic" ? "selected" : ""}>Trong nước</option></select>
      <select id="f-rel" aria-label="Mức liên quan"><option value="">Mọi mức liên quan</option><option value="high" ${state.relevance === "high" ? "selected" : ""}>Cao</option><option value="medium" ${state.relevance === "medium" ? "selected" : ""}>Vừa</option><option value="low" ${state.relevance === "low" ? "selected" : ""}>Thấp</option></select>
      <input id="f-q" type="search" placeholder="Tìm trong tiêu đề" value="${esc(state.q)}" aria-label="Tìm" style="padding:7px 10px;border:1px solid var(--axis);border-radius:9px;background:var(--surface);color:var(--ink)">
    </div>
    <div class="panel" style="padding:8px 8px">
      <div class="row spread" style="padding:6px 10px 10px">
        <span class="small muted"><span id="picked">Chọn tin để gom thành một sự kiện</span> · <span id="page-count">${num(items.length)} / ${num(total)}</span></span>
        <div class="row"><button type="button" class="btn sm" id="dismiss" disabled>Bỏ tin</button>
        <button type="button" class="btn sm primary" id="group" disabled>Gom thành sự kiện</button></div>
      </div>
      <div class="list">${items.length ? items.map(i => `
        <label class="item" style="cursor:pointer">
          <input type="checkbox" data-id="${esc(i.id)}" ${state.picked.has(i.id) ? "checked" : ""} aria-label="Chọn ${esc(i.title)}">
          <div><div class="t" data-quote>${esc(i.title)}</div>
            <div class="m">${esc(i.outlet)} · ${esc(i.label)} · ${when(i.published)}${i.event_type ? ` · ${esc(EVENT_TYPE[i.event_type] || i.event_type)}` : ""}${i.held ? ' · <span class="badge bad">bị giữ: danh sách hạn chế</span>' : ""}</div></div>
          <span class="badge ${REL[i.relevance][0]}">${REL[i.relevance][1]}</span>
        </label>`).join("") : empty("Không có tin nào khớp bộ lọc")}</div>
      ${total > items.length ? `<div class="row" style="justify-content:center;padding:10px"><button type="button" class="btn sm" id="more">Xem thêm (còn ${num(total - items.length)} tin)</button></div>` : ""}
    </div>`;

  const pickedText = () => {
    const n = state.picked.size;
    box.querySelector("#picked").textContent = n ? `Đã chọn ${n} tin` : "Chọn tin để gom thành một sự kiện";
    box.querySelector("#group").disabled = !n;
    box.querySelector("#dismiss").disabled = !n;
  };
  pickedText();
  box.querySelectorAll("[data-id]").forEach(c => {
    c.onchange = () => { c.checked ? state.picked.add(c.dataset.id) : state.picked.delete(c.dataset.id); pickedText(); };
  });
  const more = box.querySelector("#more");
  if (more) more.onclick = () => { state.shown += 40; render(box, ctx); };
  const refilter = () => {
    state.shown = 40;
    state.source = box.querySelector("#f-source").value; state.kind = box.querySelector("#f-kind").value;
    state.relevance = box.querySelector("#f-rel").value; state.q = box.querySelector("#f-q").value.trim();
    render(box, ctx);
  };
  for (const id of ["#f-source", "#f-kind", "#f-rel"]) box.querySelector(id).onchange = refilter;
  box.querySelector("#f-q").onkeydown = (e) => { if (e.key === "Enter") refilter(); };
  box.querySelector("#fetch").onclick = async (e) => {
    e.target.disabled = true; e.target.textContent = "Đang lấy…";
    try { const r = await post("/api/news/ingest", {}); toast(`Thêm ${r.ingest.added} tin mới`); } catch (err) { toast(err.message); }
    render(box, ctx);
  };
  box.querySelector("#dismiss").onclick = async () => {
    try { await post("/api/news/dismiss", {ids: [...state.picked], by: ctx.user}); toast(`Đã bỏ ${state.picked.size} tin`); state.picked.clear(); }
    catch (err) { toast(err.message); }
    render(box, ctx);
  };
  box.querySelector("#group").onclick = async () => {
    try {
      const r = await post("/api/events", {news_ids: [...state.picked], by: ctx.user});
      state.picked.clear();
      toast(`Đã lập ${r.event.id}${r.event.blocked ? " (đang bị giữ chờ Tuân thủ)" : ""}`);
      ctx.go(ctx.href("nhan-dinh", r.event.id));
    } catch (err) { toast(err.message); }
  };
}
