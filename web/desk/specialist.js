/* Chuyên gia · Bàn chuyên gia (SCR-SP-02, FEAT-41): the queue beside the evidence. Left, the recommendations an RM
   approved for the families assigned to this specialist, oldest first; right, the one picked — its actions, the RM's
   note — and its family's picture (net worth, allocation, risk against the limit, liquidity, goals), then the
   decision. Below: the certificate, the families, what the specialist decided.

   The queue is GET /api/desk's, which is what Duyệt khuyến nghị reads (GET /api/review, the same filter); the
   family's picture is POST /api/dashboard and /api/goals, the reads a specialist already makes for an assigned family
   (Q-26); the decision is Duyệt khuyến nghị's write (POST /api/review/specialist): a rejection says why in 10
   characters or more, and the server checks the certificate and the assignment again (BRD-RULE-ROLE-05, WF-08).
   data-node marks what the assistant reads. */
import {ago, esc, pct, post, toast, vnd, when} from "../core/core.js";

const KIND = {rm_note: "Khuyến nghị của RM", plan: "Phương án khách gửi"};
const RISK = {ok: ["good", "An toàn"], near: ["warn", "Gần ngưỡng"], over: ["bad", "Vượt ngưỡng"]};
const GOAL = {on_track: ["good", "Đúng tiến độ"], at_risk: ["warn", "Cần chú ý"], off_track: ["bad", "Chậm tiến độ"]};

// the months said as the overview tool says them: a long reserve also in years
const months = (m) => m == null ? "—" : `${String(Math.round(m * 10) / 10).replace(".", ",")} tháng chi tiêu${m >= 24 ? ` (khoảng ${Math.round(m / 12)} năm)` : ""}`;

export function hint(d) {
  return `<h3>Bàn chuyên gia</h3>
    <p class="small">Bên trái là khuyến nghị RM đã duyệt cho gia đình được giao bạn, cũ nhất trước. Chọn một khuyến nghị để
      xem bên cạnh các hành động, ghi chú của RM và bức tranh của gia đình, rồi duyệt hay từ chối.</p>
    <p class="small">${d.waiting.length ? `<b>${d.waiting.length}</b> khuyến nghị chờ bạn.` : "Không khuyến nghị nào chờ bạn."}
      Trợ lý bên cạnh đọc cùng bàn: hỏi “Khuyến nghị nào đang chờ tôi duyệt?” hay “Hồ sơ của gia đình này thế nào?”.</p>`;
}

export function render(box, d, api) {
  const cert = d.certificate;
  const row = (x) => `<button type="button" class="dk-row" data-i="${esc(x.id)}" data-node="item:${esc(x.id)}" aria-pressed="false">
      <span class="dk-row-t"><b>${esc(x.title)}</b><small>${esc(x.name)} · RM ${esc(x.rm || "—")} · chờ từ ${esc(ago(x.created))}</small></span>
      <span class="pill warn">Chờ bạn</span></button>`;
  box.innerHTML = `
    <header class="dk-head"><div><div class="eyebrow">Chuyên gia</div><h1 class="ws-title" id="dk-title">Bàn chuyên gia</h1>
      <p class="ws-sub small muted"><b>${d.waiting.length}</b> khuyến nghị chờ bạn · ${d.families.length} gia đình được giao · ${d.decided.length} đã xử lý gần đây</p></div>
      <span class="pill ${cert ? "good" : "bad"}" data-node="certificate">${cert ? `Chứng chỉ ${esc(cert.certificate)} · đến ${esc(cert.valid_until)}` : "Chưa có chứng chỉ còn hiệu lực"}</span></header>
    <div class="sp-bench">
      <div class="sp-side">
      <section class="panel" data-node="queue" aria-labelledby="sp-q"><div class="sechead"><h2 class="h3" id="sp-q">Chờ bạn duyệt</h2>
        <a class="small" href="#/specialist/duyet">Duyệt khuyến nghị →</a></div>
        <div class="dk-list">${d.waiting.map(row).join("") || `<p class="small muted">Không khuyến nghị nào chờ bạn. Chọn một gia đình để xem bức tranh của gia đình.</p>`}</div></section>
      <section class="panel" data-node="families" aria-labelledby="sp-f"><div class="sechead"><h2 class="h3" id="sp-f">Gia đình được giao</h2></div>
        <div class="dk-list">${d.families.map(f => `<button type="button" class="dk-row" data-f="${esc(f.id)}" data-node="family:${esc(f.id)}">
          <span class="dk-row-t"><b>${esc(f.name)}</b><small>${esc(f.id)}${f.segment ? ` · ${esc(f.segment)}` : ""}${f.approves ? "" : " · bạn chưa duyệt được (chứng chỉ)"}</small></span>
          ${f.waiting ? `<span class="badge warn">${f.waiting} chờ</span>` : ""}</button>`).join("") || `<p class="small muted">Chưa có gia đình nào được giao bạn.</p>`}</div></section>
      </div>
      <section class="panel sp-ev" data-node="evidence" aria-labelledby="sp-ev-t" aria-live="polite"><div id="sp-ev"></div></section>
    </div>
    <div class="dk-grid mt">
      <section class="panel dk-wide" data-node="decided" aria-labelledby="sp-d"><div class="sechead"><h2 class="h3" id="sp-d">Bạn đã xử lý</h2></div>
        <div class="dk-list">${d.decided.map(x => `<div class="dk-row"><span class="dk-row-t"><b>${esc(x.title)}</b>
          <small>${esc(x.name)} · ${esc(when(x.decided || x.created))}${x.note ? ` · ${esc(x.note)}` : ""}</small></span>
          <span class="badge ${x.status === "approved" ? "good" : "bad"}">${x.status === "approved" ? "Đã duyệt" : "Từ chối"}</span></div>`).join("")
          || `<p class="small muted">Bạn chưa duyệt khuyến nghị nào.</p>`}</div></section>
    </div>`;

  const ev = box.querySelector("#sp-ev");
  let token = 0;  // a later pick wins over a slower earlier read
  const mark = (sel) => {
    for (const b of box.querySelectorAll("[data-i], [data-f]")) {
      const on = b.matches(sel);
      b.classList.toggle("sel", on);
      if (b.dataset.i) b.setAttribute("aria-pressed", String(on));
    }
  };

  async function picture(family, mine) {
    const slot = ev.querySelector("#sp-pic");
    try {
      const [{dashboard: p}, {goals}] = await Promise.all([
        post("/api/dashboard", {client_id: family, scope: "family"}),
        post("/api/goals", {client_id: family, scope: "family"}).catch(() => ({goals: []})),
      ]);
      if (mine !== token || !slot.isConnected) return;
      const [rt, rw] = RISK[p.risk.status] || ["", p.risk.status];
      const top = Math.max(...p.allocation.map(a => a.share), 0.01);
      slot.innerHTML = `<dl class="dk-kv"><dt>Tài sản ròng</dt><dd class="num">${vnd(p.net_worth.value)}</dd>
          <dt>Khẩu vị rủi ro</dt><dd>${esc(p.profile.risk_profile || "—")}</dd>
          <dt>Rủi ro so với ngưỡng</dt><dd><span class="badge ${rt}">${esc(rw)}</span> <span class="num">${pct(p.risk.current, false, 1)} / ${pct(p.risk.limit, false, 1)}</span></dd>
          <dt>Thanh khoản</dt><dd class="num">${months(p.liquidity.months)}</dd></dl>
        <div class="dk-bars" aria-label="Phân bổ tài sản">${p.allocation.map(a => `<div class="dk-bar"><span class="dk-bar-l">${esc(a.group)}</span>
          <span class="dk-bar-t"><i class="pos" style="width:${Math.max(2, a.share / top * 100).toFixed(1)}%"></i></span><span class="num">${pct(a.share, false, 0)}</span></div>`).join("")}</div>
        ${goals.length ? `<div class="dk-list mt-xs">${goals.map(g => { const [gt, gw] = GOAL[g.goal.status] || ["", g.goal.status]; return `<div class="dk-row">
          <span class="dk-row-t"><b>${esc(g.title)}</b><small>cần ${vnd(g.goal.need)} · có ${vnd(g.goal.have)}</small></span><span class="badge ${gt}">${esc(gw)}</span></div>`; }).join("")}</div>` : ""}`;
    } catch (e) {
      if (mine === token && slot.isConnected) slot.innerHTML = `<p class="small muted">Không đọc được bức tranh của gia đình: ${esc(e.message)}</p>`;
    }
  }

  function pickItem(id, auto) {
    const x = d.waiting.find(w => w.id === id);
    const mine = ++token;
    mark(`[data-i="${CSS.escape(id)}"]`);
    ev.innerHTML = `<div class="sechead"><h2 class="h3" id="sp-ev-t">${esc(x.title)}</h2><span class="small muted">${esc(KIND[x.kind] || KIND.plan)}</span></div>
      <p class="small">${esc(x.name)} · gia đình ${esc(x.family_id)} · RM ${esc(x.rm || "—")} ${x.kind === "rm_note" ? "viết" : "đã duyệt"} ${esc(when(x.created))}</p>
      ${x.actions.length ? `<ul class="ul">${x.actions.map(a => `<li>${esc(a)}</li>`).join("")}</ul>` : ""}
      ${x.rm_note ? `<p class="small" data-quote><b>Ghi chú của RM:</b> ${esc(x.rm_note)}</p>` : ""}
      <h3 class="subhead mt">Bức tranh của gia đình</h3><div id="sp-pic"><p class="small muted">Đang đọc…</p></div>
      <div class="decide mt">${cert ? `<input id="sp-note" maxlength="1000" placeholder="Ghi chú (bắt buộc khi từ chối, từ 10 ký tự)" aria-label="Ghi chú cho ${esc(x.title)}">
        <button type="button" class="btn primary" data-ok>Duyệt</button><button type="button" class="btn danger" data-no>Từ chối</button>`
        : `<p class="small bad-text">Bạn chưa có chứng chỉ còn hiệu lực nên chưa duyệt được; Tuân thủ cập nhật “Chứng nhận chuyên gia” trong Cấu hình.</p>`}</div>`;
    if (!auto) api.inspect(`<h3>${esc(x.title)}</h3><dl class="dk-kv"><dt>Mã</dt><dd class="num">${esc(x.id)}</dd><dt>Khách hàng</dt><dd>${esc(x.name)}</dd>
        <dt>RM</dt><dd>${esc(x.rm || "—")}</dd><dt>Chờ từ</dt><dd>${esc(when(x.created))}</dd></dl>
      <p class="small mt">Khuyến nghị đến khách sau khi bạn duyệt. Từ chối cần lý do từ 10 ký tự; máy chủ kiểm tra lại chứng chỉ và việc phân công.</p>`);
    for (const [sel, decision] of [["[data-ok]", "approved"], ["[data-no]", "rejected"]]) {
      const b = ev.querySelector(sel);
      if (b) b.onclick = () => decide(x, decision, b);
    }
    picture(x.family_id, mine);
  }

  function pickFamily(fid) {
    const f = d.families.find(x => x.id === fid);
    const mine = ++token;
    mark(`[data-f="${CSS.escape(fid)}"]`);
    ev.innerHTML = `<div class="sechead"><h2 class="h3" id="sp-ev-t">${esc(f.name)}</h2><span class="small muted">${esc(f.id)}</span></div>
      <p class="small">${f.waiting ? `${f.waiting} khuyến nghị của gia đình này chờ bạn.` : "Không khuyến nghị nào của gia đình này chờ bạn."}</p>
      <h3 class="subhead mt">Bức tranh của gia đình</h3><div id="sp-pic"><p class="small muted">Đang đọc…</p></div>`;
    api.inspect(`<h3>${esc(f.name)}</h3><p class="small">Gia đình được giao bạn${f.approves ? "; bạn duyệt khuyến nghị của gia đình này." : ", nhưng bạn chưa duyệt được khi chưa có chứng chỉ còn hiệu lực."}</p>`);
    picture(fid, mine);
  }

  async function decide(x, decision, btn) {
    const note = ((ev.querySelector("#sp-note") || {}).value || "").trim();
    if (decision === "rejected" && note.length < 10) {
      toast("Từ chối cần lý do từ 10 ký tự");
      ev.querySelector("#sp-note").focus();
      return;
    }
    btn.disabled = true;
    try {
      await post("/api/review/specialist", {item_id: x.id, decision, note, by: api.user()});
      toast(decision === "approved" ? "Đã duyệt" : "Đã từ chối");
      api.reload();
    } catch (e) {
      toast("Không lưu được: " + e.message);
      btn.disabled = false;
    }
  }

  for (const b of box.querySelectorAll("[data-i]")) b.onclick = () => pickItem(b.dataset.i);
  for (const b of box.querySelectorAll("[data-f]")) b.onclick = () => pickFamily(b.dataset.f);
  if (d.waiting.length) pickItem(d.waiting[0].id, true);  // the oldest open beside the queue; Thông tin waits for a pick
  else ev.innerHTML = `<h2 class="h3" id="sp-ev-t">Bằng chứng</h2><p class="small muted">Chọn một khuyến nghị hay một gia đình để xem bức tranh của gia đình bên cạnh.</p>`;
}
