/* CIO · Bàn quyết định (SCR-CIO-15, FEAT-41): where the news-to-family pipeline stands and what waits for the CIO.
   The pipeline is a flow of six stages — Tin → Sự kiện → Nhận định → Lần áp dụng → Gia đình → RM — each with its
   count and what waits; a stage picked lists its items in Thông tin. Below: the decisions waiting (views, runs held
   for review, configuration, returned letters, events with no view yet), the exposure of the newest effective run,
   the latest events, the model's data, and the agents beneath the desk (Agent CIO, challenger: FEAT-04, 05).

   Every figure is GET /api/desk's, composed from the stores the CIO's pages read; every item opens its page as a
   sheet. data-node marks what the CIO's assistant reads (its step lights it). */
import {EVENT_TYPE, ago, esc, n as how, pct, signClass, viewBadge, vnd} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";

const STAGE_ICON = {news: "inbox", events: "news", views: "sparkles", runs: "zap", families: "users", rm: "user"};
const STAGE_PAGE = {news: "Hộp tin", events: "Sự kiện & nhận định", views: "Sự kiện & nhận định", runs: "Lần áp dụng",
  families: "Phơi nhiễm", rm: "Đồ thị lần áp dụng"};  // the page a stage's button opens
const KIND = {view: ["sparkles", "Nhận định"], run: ["zap", "Lần áp dụng"], config: ["sliders", "Cấu hình"],
  letter: ["mail", "Bản tin"], event: ["news", "Sự kiện"]};
const MODE = {live: ["good", "Trực tiếp"], mock: ["warn", "Mô phỏng"], rules: ["", "Luật"]};

const row = (x) => `<a class="dk-row" href="${esc(x.route)}">
  <span class="ic-chip">${icon((KIND[x.kind] || ["file"])[0])}</span>
  <span class="dk-row-t"><b>${esc(x.title)}</b><small>${esc((KIND[x.kind] || ["", ""])[1])} ${esc(x.id)} · ${esc(ago(x.at))}</small></span>
  <span class="pill ${x.kind === "event" ? "" : "warn"}">${esc(x.status)}</span></a>`;

const item = (x) => `<a class="dk-row" href="${esc(x.route || "#")}"${x.route ? "" : ' aria-disabled="true"'}>
  <span class="dk-row-t"><b>${esc(x.title)}</b>${x.sub ? `<small>${esc(x.sub)}</small>` : ""}</span>
  ${x.value != null ? `<span class="num small ${signClass(x.value)}">${vnd(x.value, true)}</span>` : ""}</a>`;

export function hint(d) {
  const waits = d.decide.length;
  return `<h3>Bàn quyết định</h3>
    <p class="small">Mỗi nút trên dòng chảy là một chặng từ tin tức đến gia đình. Chọn một chặng để xem các mục của nó ở đây;
      mỗi mục mở trang của nó.</p>
    <p class="small">${waits ? `<b>${waits}</b> việc đang chờ bạn quyết định.` : "Không có việc nào chờ bạn quyết định."}
      Trợ lý bên cạnh đọc cùng các con số này: hỏi “Có gì chờ tôi duyệt?” hay “Phơi nhiễm lớn nhất ở đâu?”.</p>`;
}

export function render(box, d, api) {
  const stages = d.pipeline;
  const e = d.exposure, m = d.model, a = d.agents || {};
  const mode = MODE[a.mode] || ["", a.mode || "—"];
  const max = e ? Math.max(1, ...e.factors.map(f => Math.abs(f.value))) : 1;
  box.innerHTML = `
    <header class="dk-head"><div><div class="eyebrow">CIO</div><h1 class="ws-title" id="dk-title">Bàn quyết định</h1>
      <p class="ws-sub small muted">${d.decide.length ? `<b>${d.decide.length}</b> việc chờ bạn` : "Không có việc chờ bạn"} ·
        ${stages[0].count} tin mới · ${stages[3].count} lần áp dụng đang hiệu lực</p></div>
      <span class="pill ${mode[0]}" title="Chế độ của Agent CIO khi chạy bây giờ">Agent CIO: ${esc(mode[1])}</span></header>
    <ol class="dk-flow" aria-label="Dòng chảy từ tin tức đến gia đình">${stages.map((s, i) => `<li>
      <button type="button" class="dk-stage${s.waits ? " waits" : ""}" data-stage="${esc(s.id)}" data-node="stage:${esc(s.id)}" aria-describedby="dk-st-${i}">
        <span class="dk-stage-i">${icon(STAGE_ICON[s.id] || "layers", {size: 18})}</span>
        <span class="dk-stage-n num">${s.count}</span><span class="dk-stage-l">${esc(s.label)}</span>
        <span class="dk-stage-u small muted" id="dk-st-${i}">${esc(s.unit)}${s.note ? ` · ${esc(s.note)}` : ""}</span>
        ${s.waits ? `<span class="dk-badge" aria-label="${s.waits} việc chờ">${s.waits}</span>` : ""}</button></li>`).join("")}</ol>
    <div class="dk-grid">
      <section class="panel dk-wide" data-node="decide" aria-labelledby="dk-decide"><div class="sechead"><h2 class="h3" id="dk-decide">Cần bạn quyết định</h2>
        <span class="small muted">${d.decide.length} việc</span></div>
        <div class="dk-list">${d.decide.map(row).join("") || `<p class="small muted">Không có việc nào chờ bạn: nhận định, lần áp dụng, cấu hình và bản tin đều đã xử lý.</p>`}</div></section>
      <section class="panel" data-node="exposure" aria-labelledby="dk-exp"><div class="sechead"><h2 class="h3" id="dk-exp">Phơi nhiễm</h2>
        ${e ? `<a class="small" href="${esc(e.route)}">Mở Phơi nhiễm →</a>` : ""}</div>
        ${e ? `<p class="dk-big ${signClass(e.expected_3m)}">${how(vnd(e.expected_3m, true), "run.expected_3m", {families: String(e.families)})}</p>
          <p class="small muted">kỳ vọng 3 tháng trên ${e.families} gia đình · ${e.pre_review} chạm ngưỡng · ${esc(e.run_id)}: ${esc(e.event)}</p>
          <div class="dk-bars" role="list" aria-label="Theo yếu tố, tổng mọi gia đình">${e.factors.map(f => `<div class="dk-bar" role="listitem">
            <span class="dk-bar-l">${esc(f.name)}</span><span class="dk-bar-t"><i class="${f.value < 0 ? "neg" : "pos"}" style="width:${(Math.abs(f.value) / max * 100).toFixed(1)}%"></i></span>
            <span class="num small ${signClass(f.value)}">${how(vnd(f.value, true), "impact.by_factor", {part: f.name})}</span></div>`).join("")}</div>
          <p class="small mt">Xấu nhất: ${e.worst.map(w => `${esc(w.name)} <span class="${signClass(w.expected_3m_pct)}">${pct(w.expected_3m_pct, true, 2)}</span>${w.pre_review ? ' <span class="badge bad">xem trước</span>' : ""}`).join(" · ")}</p>`
        : `<p class="small muted">Chưa có lần áp dụng nào đang hiệu lực: duyệt một nhận định để máy tính cho mọi gia đình.</p>`}</section>
      <section class="panel" data-node="events" aria-labelledby="dk-ev"><div class="sechead"><h2 class="h3" id="dk-ev">Sự kiện gần đây</h2>
        <a class="small" href="#/cio/nhan-dinh">Tất cả →</a></div>
        <div class="dk-list">${d.events.map(x => `<a class="dk-row" href="${esc(x.route)}"><span class="dk-row-t"><b>${esc(x.title)}</b>
          <small>${esc(EVENT_TYPE[x.type] || x.type || "")} · ${esc(x.id)} · ${esc(ago(x.created))}</small></span>
          ${x.blocked ? '<span class="badge bad">bị giữ</span>' : x.status ? viewBadge(x.status) : '<span class="pill">chưa có nhận định</span>'}</a>`).join("") || `<p class="small muted">Chưa có sự kiện. Gom tin trong Hộp tin thành một sự kiện.</p>`}</div></section>
      <section class="panel" data-node="model" aria-labelledby="dk-model"><div class="sechead"><h2 class="h3" id="dk-model">Mô hình và dữ liệu</h2></div>
        <dl class="dk-kv">
          <dt>Yếu tố có dữ liệu thật</dt><dd class="num"><a href="#/cio/mo-hinh/du-lieu">${m.factors_real}/${m.factors}</a></dd>
          <dt>Nguồn dữ liệu đang lỗi</dt><dd class="num ${m.late_jobs.length ? "bad-text" : ""}">${m.late_jobs.length}</dd>
          <dt>Dự báo chờ đến hạn chấm</dt><dd class="num"><a href="#/cio/mo-hinh/do-chinh-xac">${m.forecasts_waiting}/${m.forecasts}</a></dd>
          <dt>Hạn chấm gần nhất</dt><dd class="num">${esc(m.next_due || "—")}</dd></dl>
        ${m.late_jobs.length ? `<p class="small bad-text">${m.late_jobs.map(j => esc(j.job)).join(", ")}</p>` : ""}</section>
      <section class="panel" data-node="agents" aria-labelledby="dk-ag"><div class="sechead"><h2 class="h3" id="dk-ag">Agent dưới bàn</h2>
        <a class="small" href="#/cio/agent">Bản đồ agent →</a></div>
        <dl class="dk-kv">
          <dt>Agent CIO</dt><dd><span class="pill ${mode[0]}">${esc(mode[1])}</span> ${esc((a.models || {}).cio || "")}</dd>
          <dt>Phản biện</dt><dd>${esc((a.models || {}).challenger || "—")}</dd>
          <dt>Phiên bản prompt</dt><dd>${esc(a.prompt_version || "—")}</dd>
          <dt>Token hôm nay</dt><dd class="num">${((a.budget || {}).used_today || 0).toLocaleString("vi-VN")} / ${((a.budget || {}).daily || 0).toLocaleString("vi-VN")}</dd></dl>
        <p class="small muted">Chạy Agent CIO ở trang của mỗi sự kiện; phản biện chạy sau mỗi bản soạn.</p></section>
    </div>`;

  for (const b of box.querySelectorAll("[data-stage]")) b.onclick = () => pick(b.dataset.stage);
  function pick(id) {
    for (const b of box.querySelectorAll("[data-stage]")) b.classList.toggle("sel", b.dataset.stage === id);
    const s = stages.find(x => x.id === id);
    const list = {
      news: d.items.news, events: d.events.map(x => ({title: x.title, sub: `${x.id}${x.blocked ? " · bị giữ" : ""}`, route: x.route})),
      views: d.decide.filter(x => x.kind === "view").map(x => ({title: x.title, sub: `${x.id} · ${x.status}`, route: x.route})),
      runs: d.items.runs, families: d.items.families, rm: d.items.rm,
    }[id] || [];
    api.inspect(`<h3>${esc(s.label)} <span class="small muted">${s.count} ${esc(s.unit)}</span></h3>
      ${s.note ? `<p class="small">${esc(s.note)}</p>` : ""}
      <div class="dk-list">${list.map(item).join("") || `<p class="small muted">Không có mục nào.</p>`}</div>
      <p class="mt"><a class="btn" href="${esc(s.route)}">Mở ${esc(STAGE_PAGE[s.id] || s.label)}</a></p>`);
  }
}
