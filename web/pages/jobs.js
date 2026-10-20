/* Việc nền (owner 2026-10-18, docs/OWNER_BACKLOG_1018_PLAN.md A): the agents and the background jobs on one page, for
   the CIO, Admin and Compliance (GET /api/jobs). Agent: the mode and today's budget, each agent's runs, the queue of
   “Chạy Agent CIO” requests; the CIO starts Agent CIO on an event with no view yet (POST /api/events/run-agent) and
   re-runs a failed challenger (POST /api/views/decide, action challenge). Lịch chạy: each job's clock and last run;
   Admin runs one now (POST /api/jobs/run). Lần chạy tay: who ran what. Compliance reads it without buttons. The
   assistant does the same writes on a Xác nhận. Rows are lists (.item), so a phone reads them as they are. */
import {ago, esc, get, post, toast} from "../core/core.js";
import {JOB} from "./system.js?v=20261020u1";

const MODE = {live: "Mô hình thật", mock: "Mô phỏng", inbox: "Hộp chờ (vùng AI)"};
const AGENT = {cio: "Agent CIO", challenger: "Agent Phản biện", policy: "Agent Chính sách", newsletter: "Bản tin"};
const QUEUE = {queued: ["warn", "Đang xếp hàng"], running: ["warn", "Đang chạy"], done: ["good", "Xong"], failed: ["bad", "Lỗi"]};
const RUN = {running: ["warn", "Đang chạy"], done: ["good", "Xong"], failed: ["bad", "Lỗi"]};

const badge = (map, s) => `<span class="badge ${map[s] ? map[s][0] : ""}">${esc(map[s] ? map[s][1] : s)}</span>`;
const every = (w) => (w.at ? `hằng ngày ${esc(w.at)}` : w.every ? `mỗi ${esc(w.every.replace("h", " giờ").replace("m", " phút").replace("s", " giây"))}` : "khi được yêu cầu");

const lastRun = (l) => (l ? `lần gần nhất ${esc(ago(l.at))}${l.manual ? ` (chạy tay ${esc(l.manual)})` : ""}` : "chưa ghi lần nào");
const state = (j) => (j.running ? badge(RUN, "running") : !j.last ? `<span class="badge">—</span>`
  : `<span class="badge ${j.last.ok ? "good" : "bad"}">${j.last.ok ? "ổn" : "lỗi"}</span>`);

export async function render(box, ctx) {
  const d = await get("/api/jobs");
  const cio = ctx.role === "cio", admin = ctx.role === "admin";
  const a = d.agents, st = a.status, b = st.budget || {};
  const failing = d.jobs.filter(j => j.last && !j.last.ok).length;
  const waiting = a.queue.filter(j => j.status === "queued" || j.status === "running").length;
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">${cio ? "CIO" : admin ? "Quản trị" : "Tuân thủ"}</div>
      <h1 class="h1">Việc nền</h1>
      <p class="lede">Agent ${esc(MODE[st.mode] || st.mode)} · ${waiting ? `${waiting} lần chạy đang chờ` : "không lần chạy nào chờ"}
        · ${d.jobs.length} việc theo lịch${failing ? ` · <span class="bad-text">${failing} đang lỗi</span>` : ""}.
        ${cio ? "Bạn chạy Agent CIO và Agent Phản biện; Quản trị chạy các việc theo lịch." : admin ? "Bạn chạy ngay các việc theo lịch; CIO chạy các agent." : "Chỉ xem: CIO chạy các agent, Quản trị chạy các việc theo lịch."}
        Trợ lý làm được các việc này sau khi bạn bấm Xác nhận.</p></div></div>

    <section class="panel" id="jobs-agents"><div class="h3">Agent</div>
      <p class="small muted">Chế độ ${esc(MODE[st.mode] || st.mode)}${st.models ? ` · ${esc([st.models.cio, st.models.challenger].filter(Boolean).join(" · "))}` : ""}
        · hôm nay ${Number(b.used_today || 0).toLocaleString("vi-VN")} / ${Number(b.daily || 0).toLocaleString("vi-VN")} token.
        Nhận định ra là bản nháp: qua Agent Phản biện, rồi CIO duyệt ở trang Sự kiện &amp; nhận định.</p>
      <div class="list">${a.health.map(h => `<div class="item"><span class="badge ${h.failed ? "bad" : "good"}">${h.failed ? `${h.failed} lỗi` : "ổn"}</span>
        <div><div class="t">${esc(AGENT[h.agent] || h.agent)}</div><div class="m">${h.runs} lần trong 7 ngày · gần nhất ${esc(ago(h.last))}${h.last_error ? ` · ${esc(h.last_error)}` : ""}</div></div><span></span></div>`).join("")
        || `<p class="small muted">Chưa agent nào chạy trong 7 ngày.</p>`}</div>
      ${cio ? `<div class="h3 mt">Chạy Agent CIO</div>
        <div class="list">${a.can_run.map(e => `<div class="item"><span class="badge ${e.urgent ? "bad" : ""}">${e.urgent ? "khẩn" : "sự kiện"}</span>
          <div><div class="t">${esc(e.title)}</div><div class="m mono">${esc(e.id)} · chưa có nhận định</div></div>
          <button type="button" class="btn sm" data-run="${esc(e.id)}">Chạy Agent CIO</button></div>`).join("")
          || `<p class="small muted">Sự kiện nào cũng đã có nhận định hoặc đang chạy.</p>`}</div>
        ${a.can_challenge.length ? `<div class="h3 mt">Phản biện lỗi, chạy lại</div><div class="list">${a.can_challenge.map(v => `<div class="item"><span class="badge bad">lỗi</span>
          <div><div class="t">${esc(v.title)}</div><div class="m"><span class="mono">${esc(v.id)}</span>${v.error ? ` · ${esc(v.error)}` : ""}</div></div>
          <button type="button" class="btn sm" data-challenge="${esc(v.id)}">Phản biện lại</button></div>`).join("")}</div>` : ""}` : ""}
      <div class="h3 mt">Các lần “Chạy Agent CIO”</div>
      <div class="list">${a.queue.map(j => `<div class="item">${badge(QUEUE, j.status)}
        <div><div class="t">${esc(j.title || j.event_id)}</div><div class="m"><span class="mono">${esc(j.id)}</span> · ${esc(j.by)} · ${esc(ago(j.created))} · ${esc(MODE[j.mode] || j.mode)}${j.view_id ? ` · nhận định <span class="mono">${esc(j.view_id)}</span>` : ""}${j.error ? ` · <span class="bad-text">${esc(j.error)}</span>` : ""}</div></div><span></span></div>`).join("")
        || `<p class="small muted">Chưa lần nào.</p>`}</div></section>

    <section class="panel mt" id="jobs-schedule"><div class="h3">Lịch chạy</div>
      <div class="list">${d.jobs.map(j => `<div class="item">${state(j)}
        <div><div class="t">${esc(j.label || JOB[j.id] || j.id)}</div><div class="m"><span class="mono">${esc(j.id)}</span> · ${every(j.when)} · ${lastRun(j.last)}</div>
          ${j.last && j.last.error ? `<div class="m ${j.last.ok ? "" : "bad-text"}">${esc(j.last.error)}</div>` : ""}</div>
        ${admin && j.runnable ? `<button type="button" class="btn sm" data-job="${esc(j.id)}" ${j.running ? "disabled" : ""}>${j.running ? "Đang chạy…" : "Chạy ngay"}</button>` : "<span></span>"}</div>`).join("")}</div>
      <p class="small muted">Nhịp máy chủ, hàng đợi agent, tổng hợp trí nhớ và lưu giữ chạy theo lịch, không chạy tay. Nạp lại lịch sử thị trường: trang Hệ thống.</p></section>

    <section class="panel mt" id="jobs-manual"><div class="h3">Lần chạy tay</div>
      <div class="list">${d.manual.map(r => `<div class="item">${badge(RUN, r.status)}
        <div><div class="t">${esc(r.label)}</div><div class="m"><span class="mono">${esc(r.id)}</span> · ${esc(r.by)} · ${esc(ago(r.created))}${r.seconds != null ? ` · ${r.seconds} giây` : ""}${r.summary && r.summary.items != null ? ` · ${r.summary.items} mục${r.summary.failed ? `, ${r.summary.failed} lỗi` : ""}` : ""}</div>
          ${r.error ? `<div class="m bad-text">${esc(r.error)}</div>` : ""}</div><span></span></div>`).join("")
        || `<p class="small muted">Chưa ai chạy tay việc nào.</p>`}</div></section>`;

  const again = () => setTimeout(() => { if (box.isConnected) render(box, ctx).catch(() => {}); }, 1500);
  box.querySelectorAll("[data-run]").forEach(btn => btn.onclick = async () => {
    btn.disabled = true; btn.textContent = "Đang xếp…";
    try { const r = await post("/api/events/run-agent", {event_id: btn.dataset.run, by: ctx.user}); toast(`Đã xếp Agent CIO (${r.job.id})`); again(); }
    catch (e) { toast(e.message); btn.disabled = false; btn.textContent = "Chạy Agent CIO"; }
  });
  box.querySelectorAll("[data-challenge]").forEach(btn => btn.onclick = async () => {
    btn.disabled = true; btn.textContent = "Đang phản biện…";
    try { await post("/api/views/decide", {view_id: btn.dataset.challenge, action: "challenge", by: ctx.user}); toast("Đã chạy lại Agent Phản biện"); again(); }
    catch (e) { toast(e.message); btn.disabled = false; btn.textContent = "Phản biện lại"; }
  });
  box.querySelectorAll("[data-job]").forEach(btn => btn.onclick = async () => {
    btn.disabled = true; btn.textContent = "Đang chạy…";
    try { const r = await post("/api/jobs/run", {job: btn.dataset.job, by: ctx.user}); toast(`Đã bắt đầu ${r.run.label} (${r.run.id})`); again(); }
    catch (e) { toast(e.message); btn.disabled = false; btn.textContent = "Chạy ngay"; }
  });
}
