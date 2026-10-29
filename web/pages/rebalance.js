/* CIO · Phân bổ (ASSET_ALLOCATION_BRD P2): the allocations an RM sent, each action approved or rejected on its own (Q-29:
   the client sees only the approved ones; POST /api/allocation/review); the model the tilts give, ±2-point tilts and
   Black–Litterman side by side, and the way in force (POST /api/allocation/method); every bucket an RM moved, with its
   reason (Compliance's log since OWN-FB-18). */
import {esc, n as how, pct, post, toast, when} from "../core/core.js";

const CHECK = {PASS: ["good", "Phù hợp"], WARN: ["warn", "Cần lưu ý"], BLOCK: ["bad", "Bị chặn"]};
const DONE = {approved: ["good", "Đã duyệt"], rejected: ["bad", "Đã từ chối"], pending: ["warn", "Chờ"]};
const LEVEL = 3;  // the model shown for one level, as on the tilt panel
// an action is sent as "what (amount)": the two drawn apart, so the words translate and the amount stays as it is
const said = (w) => {
  const m = /^(.*) \(([^()]*)\)$/s.exec(w);
  return m ? `<span>${esc(m[1])}</span> <span class="num" data-explains>(${m[2].split("–").map(x => `<span>${esc(x)}</span>`).join("–")})</span>`
    : `<span data-explains>${esc(w)}</span>`;
};

export async function render(box, ctx) {
  const [q, t] = await Promise.all([post("/api/allocation/queue", {}), post("/api/allocation/tilts", {})]);
  const p = (x) => pct(x, false, 1);
  const metric = {tilt: "alloc.model", bl: "alloc.bl"};
  const models = {tilt: t.model[LEVEL].classes, bl: t.model_bl[LEVEL].classes};
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO</div><div class="h1">Phân bổ</div>
      <div class="lede small">Việc RM gửi chờ CIO duyệt từng dòng; mô hình đang dùng; các lần RM chuyển giỏ.</div></div></div>
    <div class="row tight">${q.waiting.length ? `<span class="pill warn">${q.waiting.length} phân bổ chờ duyệt</span>` : `<span class="chip">Không có phân bổ chờ duyệt</span>`}
      ${q.overrides.length ? `<span class="chip">${q.overrides.length} lần chuyển giỏ</span>` : ""}</div>
    ${q.waiting.map(item).join("")}
    <section class="panel mt"><h3>Mô hình Tăng trưởng <span class="hint">mức rủi ro ${LEVEL}, theo nghiêng CIO đang có</span></h3>
      <div class="seg" role="group" aria-label="Cách tính mô hình">${t.methods.map(x =>
        `<button type="button" data-way="${x.id}" aria-pressed="${x.id === t.method}">${esc(x.label)}</button>`).join("")}</div>
      <div class="scrollx mt"><table class="table"><thead><tr><th>Loại</th><th class="r">Gốc</th>${t.methods.map(x =>
        `<th class="r"><span>${esc(x.label)}</span>${x.id === t.method ? " <span>✓</span>" : ""}</th>`).join("")}</tr></thead><tbody>${Object.entries(models.tilt).map(([c, m]) => `
        <tr><td>${esc(m.label)}</td><td class="r num">${how(p(m.base), "alloc.model", {level: LEVEL})}</td>
          ${t.methods.map(x => `<td class="r num">${how(p(models[x.id][c].target), metric[x.id], {level: LEVEL})}</td>`).join("")}</tr>`).join("")}
      </tbody></table></div>
      <p class="small muted" data-explains>Mọi khách dùng cách đang chọn (✓). Cả hai giữ mỗi loại trong ±5 điểm và trong khoảng cho phép.</p></section>
    <section class="panel mt"><h3>RM chuyển giỏ</h3>${q.overrides.length ? `<div class="scrollx"><table class="table"><thead><tr>
      <th>Khách</th><th>Tài sản</th><th>Từ → sang</th><th>Lý do</th><th>Lúc</th></tr></thead><tbody>${q.overrides.map(o => `
      <tr><td>${esc(o.client_name)}</td><td>${esc(o.name)}</td><td><span>${esc(o.from_label)}</span> → <span>${esc(o.to_label)}</span></td>
        <td data-explains>${esc(o.reason || "Về giỏ mặc định")}</td><td class="small muted">${esc(when(o.at))} · ${esc(o.by)}</td></tr>`).join("")}
      </tbody></table></div>` : `<p class="small muted">Chưa có lần chuyển nào.</p>`}</section>
    ${q.decided.length ? `<details class="more mt"><summary>Đã duyệt gần đây</summary>${q.decided.map(r => `
      <div class="mt"><strong>${esc(r.client_name)}</strong> <span class="pill ${DONE[r.status][0]}">${DONE[r.status][1]}</span>
        <ul class="small" style="margin:4px 0 0">${r.data.actions.map(a => `<li>${said(a.what)}
          <span class="pill ${DONE[a.status][0]}">${DONE[a.status][1]}</span></li>`).join("")}</ul></div>`).join("")}</details>` : ""}`;

  box.querySelectorAll("[data-way]").forEach(b => b.onclick = async () => {
    if (b.getAttribute("aria-pressed") === "true") return;
    try { await post("/api/allocation/method", {method: b.dataset.way, by: ctx.user}); toast("Đã đổi cách tính mô hình"); }
    catch (e) { toast(e.message); }
    render(box, ctx);
  });
  box.querySelectorAll("[data-item]").forEach(card => {
    card.querySelector("[data-save]").onclick = async (e) => {
      const decisions = {};
      card.querySelectorAll("[data-n]").forEach(row => {
        const on = row.querySelector("[aria-pressed=true]");
        if (on) decisions[row.dataset.n] = on.dataset.d;
      });
      if (!Object.keys(decisions).length) { toast("Chọn Duyệt hoặc Từ chối cho ít nhất một việc"); return; }
      e.target.disabled = true;
      try {
        await post("/api/allocation/review", {item_id: card.dataset.item, decisions, note: card.querySelector("[data-note]").value.trim(), by: ctx.user});
        toast("Đã ghi quyết định");
        render(box, ctx);
      } catch (err) { e.target.disabled = false; toast(err.message); }
    };
    card.querySelectorAll("[data-d]").forEach(b => b.onclick = () => {
      b.parentElement.querySelectorAll("[data-d]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
    });
  });
}

// one allocation waiting: each action with its check, decided one by one; an action already decided keeps its mark
function item(r) {
  return `<section class="panel mt" data-item="${esc(r.id)}"><h3>${esc(r.client_name)} <span class="hint">${esc(r.title)}</span></h3>
    <ol style="margin:0;padding-left:20px;display:grid;gap:8px">${r.data.actions.map(a => `
      <li data-n="${a.n}"><div class="row" style="gap:8px;flex-wrap:wrap;align-items:center;justify-content:space-between">
        <span>${said(a.what)} <span class="chip">${esc(a.bucket)}</span>
          <span class="pill ${CHECK[a.check][0]}">${CHECK[a.check][1]}</span></span>
        ${a.status === "pending" ? `<span class="seg" role="group" aria-label="Quyết định">
          <button type="button" data-d="approve" aria-pressed="false">Duyệt</button><button type="button" data-d="reject" aria-pressed="false">Từ chối</button></span>`
          : `<span class="pill ${DONE[a.status][0]}">${DONE[a.status][1]}</span>`}</div></li>`).join("")}</ol>
    <div class="row mt" style="gap:8px;align-items:center;flex-wrap:wrap"><input data-note class="input" placeholder="Ghi chú cho RM (không bắt buộc)" style="flex:1;min-width:180px">
      <button type="button" class="btn primary" data-save>Ghi quyết định</button></div>
    <p class="small muted">Khách chỉ thấy việc đã duyệt.</p></section>`;
}
