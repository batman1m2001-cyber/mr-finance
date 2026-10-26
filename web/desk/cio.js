/* CIO · Decision board (SCR-CIO-15, FEAT-41, OWN-FB-07…13): where the news-to-family pipeline stands and what waits
   for the CIO. The flow is Tin → Nhận định → Lần áp dụng, then Gia đình → RM in their own frame (đến khách hàng); a
   stage picked lists its items in Thông tin. Below: the decisions waiting, each with its impact level, news group,
   outlets and scope, filtered as the inbox is and shown 20 at a time; the inbox itself (pages/inbox.js, drawn here);
   and Tổng quan tác động tới tài sản: one scenario in force in plain words, its factors and the families ranked.

   Every figure is GET /api/desk's, composed from the stores the CIO's pages read; every item opens its page as a
   sheet. data-node marks what the CIO's assistant reads (its step lights it). */
import {EVENT_TYPE, ago, esc, n as how, pct, signClass, vnd} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";
import {render as inbox} from "../pages/inbox.js?v=20261024g1";

const STAGE_ICON = {news: "inbox", views: "sparkles", runs: "zap", families: "users", rm: "user"};
const STAGE_PAGE = {news: "Hộp tin", views: "Sự kiện & nhận định", runs: "Lần áp dụng", families: "Tác động danh mục",
  rm: "Đồ thị lần áp dụng"};  // the page a stage's button opens
const TO_CLIENT = new Set(["families", "rm"]);  // OWN-FB-08: their own frame
const KIND = {view: ["sparkles", "Nhận định"], run: ["zap", "Lần áp dụng"], config: ["sliders", "Cấu hình"],
  letter: ["mail", "Bài viết"], event: ["news", "Sự kiện"], held: ["shield", "Tin bị giữ"], research: ["file", "Nghiên cứu"],
  policy: ["scale", "Chính sách"]};  // the last three were Compliance's (OWN-FB-18)
const LEVEL = {high: ["bad", "Tác động cao"], medium: ["warn", "Tác động vừa"], low: ["", "Tác động thấp"]};
const SCOPE = {domestic: "Trong nước", intl: "Quốc tế", both: "Trong nước + quốc tế"};
const PAGE = 20;
const state = {source: "", scope: "", level: "", q: "", shown: PAGE, scenario: null};

const row = (x) => {
  const lv = LEVEL[x.level];
  const meta = [EVENT_TYPE[x.group] || x.group, (x.outlets || []).join(", "), SCOPE[x.scope]].filter(Boolean).join(" · ");
  return `<a class="dk-row" href="${esc(x.route)}">
  <span class="ic-chip">${icon((KIND[x.kind] || ["file"])[0])}</span>
  <span class="dk-row-t"><b>${esc(x.title)}</b><small>${esc((KIND[x.kind] || ["", ""])[1])} · ${esc(ago(x.at))}${meta ? ` · ${esc(meta)}` : ""}</small></span>
  ${lv ? `<span class="badge ${lv[0]}">${lv[1]}</span>` : ""}
  <span class="pill ${x.kind === "event" ? "" : "warn"}">${esc(x.status)}</span></a>`;
};

const item = (x) => `<a class="dk-row" href="${esc(x.route || "#")}"${x.route ? "" : ' aria-disabled="true"'}>
  <span class="dk-row-t"><b>${esc(x.title)}</b>${x.sub ? `<small>${esc(x.sub)}</small>` : ""}</span>
  ${x.value != null ? `<span class="num small ${signClass(x.value)}">${vnd(x.value, true)}</span>` : ""}</a>`;

const stage = (s, i) => `<li${TO_CLIENT.has(s.id) ? ' class="to-client"' : ""}>
  <button type="button" class="dk-stage${s.waits ? " waits" : ""}" data-stage="${esc(s.id)}" data-node="stage:${esc(s.id)}" aria-describedby="dk-st-${i}">
    <span class="dk-stage-i">${icon(STAGE_ICON[s.id] || "layers", {size: 18})}</span>
    <span class="dk-stage-n num">${s.count}</span><span class="dk-stage-l">${esc(s.label)}</span>
    <span class="dk-stage-u small muted" id="dk-st-${i}">${esc(s.unit)}${s.note ? ` · ${esc(s.note)}` : ""}</span>
    ${s.waits ? `<span class="dk-badge" aria-label="${s.waits} việc chờ">${s.waits}</span>` : ""}</button></li>`;

export function hint(d) {
  const waits = d.decide.length;
  return `<h3>Decision board</h3>
    <p class="small">Mỗi nút trên dòng chảy là một chặng từ tin tức đến gia đình. Chọn một chặng để xem các mục của nó ở đây;
      mỗi mục mở trang của nó.</p>
    <p class="small">${waits ? `<b>${waits}</b> việc đang chờ bạn quyết định.` : "Không có việc nào chờ bạn quyết định."}
      Trợ lý bên cạnh đọc cùng các con số này: hỏi “Có gì chờ tôi duyệt?” hay “Tác động lớn nhất ở đâu?”.</p>`;
}

// the scenario in plain words (OWN-FB-12): no run id, the news names it
function impact(sc) {
  if (!sc) return `<p class="small muted">Chưa có kịch bản nào đang hiệu lực: duyệt một nhận định để máy tính cho mọi gia đình.</p>`;
  const max = Math.max(1, ...sc.factors.map(f => Math.abs(f.value)));
  const word = sc.expected_3m < 0 ? "dự kiến giảm" : "dự kiến tăng";
  return `<p class="dk-plain">Nếu kịch bản “${esc(sc.event)}” xảy ra, <b>${sc.families} gia đình</b> ${word}
      <b class="${signClass(sc.expected_3m)}">${how(vnd(Math.abs(sc.expected_3m), false), "run.expected_3m", {families: String(sc.families)})}</b> trong 3 tháng${sc.pre_review ? `; <b>${sc.pre_review} gia đình</b> cần RM xem trước` : ""}.</p>
    <div class="dk-impact">
      <div><h3 class="dk-sub">Theo yếu tố <span class="hint">tổng mọi gia đình</span></h3>
        <div class="dk-bars" role="list" aria-label="Theo yếu tố, tổng mọi gia đình">${sc.factors.map(f => `<div class="dk-bar" role="listitem">
          <span class="dk-bar-l">${esc(f.name)}</span><span class="dk-bar-t"><i class="${f.value < 0 ? "neg" : "pos"}" style="width:${(Math.abs(f.value) / max * 100).toFixed(1)}%"></i></span>
          <span class="num small ${signClass(f.value)}">${how(vnd(f.value, true), "impact.by_factor", {part: f.name})}</span></div>`).join("")}</div></div>
      <div><h3 class="dk-sub">Xếp hạng gia đình <span class="hint">xấu nhất trước</span></h3>
        <div class="scrollx"><table class="table dk-rank"><thead><tr><th>Gia đình</th><th class="r">Kỳ vọng</th><th class="r">% tài sản ròng</th>
          <th class="r">P10 ${how("?", "impact.p10_3m")}</th></tr></thead><tbody>
        ${sc.ranking.map(r => `<tr><td>${esc(r.name)} ${r.pre_review ? '<span class="badge bad">RM xem trước</span>' : ""}</td>
          <td class="r ${signClass(r.expected_3m)}">${how(vnd(r.expected_3m, true), "impact.expected_3m")}</td>
          <td class="r">${how(pct(r.expected_3m_pct, true, 2), "impact.expected_3m")}</td>
          <td class="r down">${how(pct(r.p10_3m_pct, true, 1), "impact.p10_3m")}</td></tr>`).join("")}</tbody></table></div>
        <p class="small muted">P10: 1 trong 10 khả năng kết quả 3 tháng xấu hơn mức này.</p></div>
    </div>`;
}

export function render(box, d, api) {
  const stages = d.pipeline;
  const head = stages.filter(s => !TO_CLIENT.has(s.id)), tail = stages.filter(s => TO_CLIENT.has(s.id));
  const scenarios = d.scenarios || [];
  const sc = scenarios.find(x => x.run_id === state.scenario) || scenarios[0];
  const outlets = [...new Set(d.decide.flatMap(x => x.outlets || []))].sort();
  box.innerHTML = `
    <header class="dk-head"><div><div class="eyebrow">CIO</div><h1 class="ws-title" id="dk-title" lang="en">Decision board</h1>
      <p class="ws-sub small muted">${d.decide.length ? `<b>${d.decide.length}</b> việc chờ bạn` : "Không có việc chờ bạn"} ·
        ${stages[0].count} tin mới · ${scenarios.length} kịch bản đang hiệu lực</p></div></header>
    <ol class="dk-flow cio" aria-label="Dòng chảy từ tin tức đến gia đình">${head.map((s, i) => stage(s, i)).join("")}
      <li class="dk-flow-client"><span class="dk-flow-cap small">Đến khách hàng</span>
        <ol class="dk-flow">${tail.map((s, i) => stage(s, head.length + i)).join("")}</ol></li></ol>
    <div class="dk-grid">
      <section class="panel dk-wide" data-node="decide" aria-labelledby="dk-decide"><div class="sechead"><h2 class="h3" id="dk-decide">Cần bạn quyết định</h2>
        <span class="small muted" id="dk-dec-n"></span></div>
        <div class="row dk-filters">
          <select id="dk-f-source" aria-label="Nguồn"><option value="">Mọi nguồn</option>${outlets.map(o => `<option ${state.source === o ? "selected" : ""}>${esc(o)}</option>`).join("")}</select>
          <select id="dk-f-scope" aria-label="Trong nước hay quốc tế"><option value="">Quốc tế + trong nước</option>${Object.entries({domestic: "Trong nước", intl: "Quốc tế"}).map(([k, v]) => `<option value="${k}" ${state.scope === k ? "selected" : ""}>${v}</option>`).join("")}</select>
          <select id="dk-f-level" aria-label="Mức tác động"><option value="">Mọi mức tác động</option>${Object.entries({high: "Cao", medium: "Vừa", low: "Thấp"}).map(([k, v]) => `<option value="${k}" ${state.level === k ? "selected" : ""}>${v}</option>`).join("")}</select>
          <input id="dk-f-q" type="search" placeholder="Tìm trong tiêu đề" value="${esc(state.q)}" aria-label="Tìm">
        </div>
        <div class="dk-list" id="dk-dec"></div></section>
      <section class="panel dk-wide" data-node="exposure" aria-labelledby="dk-exp"><div class="sechead"><h2 class="h3" id="dk-exp">Tổng quan tác động tới tài sản</h2>
        <div class="row">${scenarios.length > 1 ? `<select id="dk-sc" aria-label="Kịch bản">${scenarios.map(x => `<option value="${esc(x.run_id)}" ${x === sc ? "selected" : ""}>${esc(x.event.length > 60 ? `${x.event.slice(0, 58)}…` : x.event)} · ${esc(x.date || "")}</option>`).join("")}</select>` : ""}
          ${sc ? `<a class="small" href="${esc(sc.route)}">Mở Tác động danh mục →</a>` : ""}</div></div>
        <div id="dk-impact">${impact(sc)}</div></section>
      <section class="panel dk-wide" data-node="inbox" aria-labelledby="dk-inbox"><div id="dk-inbox-b"><p class="small muted">Đang tải hộp tin…</p></div></section>
    </div>`;

  // the decisions: the inbox's filters, 20 rows, then Xem thêm (OWN-FB-10)
  const decisions = () => {
    const q = state.q.toLowerCase();
    const rows = d.decide.filter(x => (!state.source || (x.outlets || []).includes(state.source))
      && (!state.scope || x.scope === state.scope || x.scope === "both")
      && (!state.level || x.level === state.level) && (!q || x.title.toLowerCase().includes(q)));
    const shown = rows.slice(0, state.shown);
    box.querySelector("#dk-dec-n").textContent = rows.length === d.decide.length ? `${d.decide.length} việc` : `${rows.length} / ${d.decide.length} việc`;
    box.querySelector("#dk-dec").innerHTML = shown.map(row).join("")
      + (rows.length > shown.length ? `<button type="button" class="btn sm dk-more" id="dk-more">Xem thêm (còn ${rows.length - shown.length})</button>` : "")
      || `<p class="small muted">${d.decide.length ? "Không có việc nào khớp bộ lọc." : "Không có việc nào chờ bạn: nhận định, lần áp dụng, cấu hình, bài viết, tin bị giữ, nghiên cứu và chính sách đều đã xử lý."}</p>`;
    const more = box.querySelector("#dk-more");
    if (more) more.onclick = () => { state.shown += PAGE; decisions(); };
  };
  const refilter = () => {
    state.source = box.querySelector("#dk-f-source").value; state.scope = box.querySelector("#dk-f-scope").value;
    state.level = box.querySelector("#dk-f-level").value; state.q = box.querySelector("#dk-f-q").value.trim();
    state.shown = PAGE;
    decisions();
  };
  for (const id of ["#dk-f-source", "#dk-f-scope", "#dk-f-level"]) box.querySelector(id).onchange = refilter;
  box.querySelector("#dk-f-q").oninput = refilter;
  decisions();

  const pickSc = box.querySelector("#dk-sc");
  if (pickSc) pickSc.onchange = () => {
    state.scenario = pickSc.value;
    const x = scenarios.find(s => s.run_id === pickSc.value);
    box.querySelector("#dk-impact").innerHTML = impact(x);
    box.querySelector("#dk-exp").nextElementSibling.querySelector("a").href = x.route;
  };

  // the inbox, drawn into the board (OWN-FB-11): its own read, its own buttons
  const inboxBox = box.querySelector("#dk-inbox-b");
  const ctx = {user: (api.user && api.user()) || "cio", go: api.go, href: (id, p) => `#/cio/${id}${p ? `/${p}` : ""}`, embedded: true};
  inbox(inboxBox, ctx).catch(e => { inboxBox.innerHTML = `<p class="small bad-text">Không tải được hộp tin: ${esc(e.message)}</p>`; });

  for (const b of box.querySelectorAll("[data-stage]")) b.onclick = () => pick(b.dataset.stage);
  function pick(id) {
    for (const b of box.querySelectorAll("[data-stage]")) b.classList.toggle("sel", b.dataset.stage === id);
    const s = stages.find(x => x.id === id);
    const list = {news: d.items.news, views: d.items.views, runs: d.items.runs, families: d.items.families, rm: d.items.rm}[id] || [];
    api.inspect(`<h3>${esc(s.label)} <span class="small muted">${s.count} ${esc(s.unit)}</span></h3>
      ${s.note ? `<p class="small">${esc(s.note)}</p>` : ""}
      <div class="dk-list">${list.map(item).join("") || `<p class="small muted">Không có mục nào.</p>`}</div>
      <p class="mt">${id === "news" ? `<button type="button" class="btn" id="dk-to-inbox">Đến Hộp tin</button>` : `<a class="btn" href="${esc(s.route)}">Mở ${esc(STAGE_PAGE[s.id] || s.label)}</a>`}</p>`,
    (el) => { const b = el.querySelector("#dk-to-inbox"); if (b) b.onclick = () => box.querySelector("#dk-inbox-b").scrollIntoView({block: "start"}); });
  }
}
