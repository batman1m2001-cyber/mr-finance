/* Khẩu vị rủi ro (SCR-CL-04; UI redesign R3, was the pre-redesign “risk” tab). The risk test (POST /api/risk,
   FEAT-24): 8–12 situational questions, one at a time, each depending on the answers before it; then the result —
   tolerance (what the client wants) and capacity (what the data says they can carry) on the five levels, the
   profile taken from the lower of the two, the drawdown limit the overview then measures against, the persona,
   the warnings, why capacity sits where it does, the suggested mix and when the test asks again. The answers so
   far are kept for this page's life, per client. */
import {internal, esc, pct, post} from "../core/core.js";
import {icon} from "../core/icons.js?v=20261016r1";

const LEVELS = ["Bảo toàn", "Thận trọng", "Cân bằng", "Tăng trưởng", "Mạo hiểm"];
const runs = {};  // per client: {answers, order, reply}

// a score on 0–100 over the five levels, the level it falls in marked
function scale(label, hint, score, level, tone) {
  return `<div class="rscale">
    <div class="kv"><span>${label} <span class="muted small">${hint}</span></span><b>${LEVELS[level - 1]} · ${Math.round(score)}/100</b></div>
    <div class="rbands" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(score)}" aria-label="${label}">
      ${LEVELS.map((n, i) => `<span class="${i === level - 1 ? "on" : ""}" style="--tone:${tone}"></span>`).join("")}
      <i style="left:${Math.min(100, Math.max(0, score))}%;--tone:${tone}"></i></div>
    <div class="rlabels small muted">${LEVELS.map(n => `<span>${n}</span>`).join("")}</div></div>`;
}

export async function render(box, ctx) {
  const client = ctx.client(), staff = ctx.role !== "client";
  const run = runs[client] ||= {answers: {}, order: [], reply: null};
  const me = await fetch("/api/clients").then(r => r.json()).then(c => c.clients.find(x => x.id === client) || {}).catch(() => ({}));

  const step = async () => {
    box.querySelector(".rbody").classList.add("loading");
    try {
      run.reply = (await post("/api/risk", {client_id: client, answers: run.answers})).reply;
    } catch (e) {
      run.reply = {error: e.message};
    }
    if (box.isConnected) draw();
  };

  const draw = () => {
    const r = run.reply;
    let body;
    if (!r) {
      body = `<div class="panel rstart">
        <span class="ic-chip lg" style="--tone:var(--accent)">${icon("shield", {size: 22})}</span>
        <div><h3 class="h2">Bài test khẩu vị rủi ro</h3>
          <p>8–12 câu hỏi tình huống; câu sau phụ thuộc vào câu trả lời trước. Kết quả tách hai điều:
            <b>mức chấp nhận rủi ro</b> (anh/chị muốn chịu bao nhiêu) và <b>khả năng chịu rủi ro</b> (dữ liệu tài chính cho thấy anh/chị có thể chịu bao nhiêu).
            Hồ sơ lấy mức thấp hơn, và ngưỡng sụt giảm của hồ sơ là ngưỡng trang ${staff ? "Tổng quan" : "Wealth View"} dùng để đo rủi ro.</p>
          <button type="button" class="btn primary" id="risk-start">Bắt đầu cho ${esc(me.name || client)}</button></div></div>`;
    } else if (r.error) {
      body = `<div class="notice bad" role="alert">Không tải được bài test: ${esc(r.error)}</div>
        <button type="button" class="btn mt" id="risk-start">Thử lại</button>`;
    } else if (r.question) {
      const q = r.question;
      const of = Number(String(q.of).split("–").pop()) || 12;
      body = `<div class="panel qpanel">
        <div class="qtop"><span class="small muted">Câu ${q.number} / ${esc(q.of)}</span>
          <div class="bar-track" aria-hidden="true"><i style="width:${Math.round((q.number - 1) / of * 100)}%"></i></div></div>
        <h3 class="qtext">${esc(q.text)}</h3>
        <div class="opts">${q.options.map((o, i) => `<button type="button" class="opt" data-opt="${esc(o.id)}"><span class="optkey">${"ABCDEF"[i]}</span><span>${esc(o.text)}</span></button>`).join("")}</div>
        ${run.order.length ? `<button type="button" class="btn sm mt" id="risk-back">← Câu trước</button>` : ""}</div>`;
    } else {
      const res = r.result;
      body = `<div class="cols">
        <div class="panel c12 rhero">
          <div><div class="pc-head"><span class="ic-chip sm" style="--tone:var(--accent)">${icon("shield", {size: 14})}</span><span class="k">Hồ sơ rủi ro</span></div>
            <div class="hero-v">${esc(res.profile.name)}</div>
            <div>Ngưỡng sụt giảm tối đa <b>${pct(res.drawdown_limit, false, 0)}</b> <span class="muted">· ${res.questions} câu · ngày ${esc(res.taken)}</span></div>
            <div class="row tight mt"><span class="chip">Chân dung: <b>${esc(res.persona)}</b></span></div>
            <p class="small muted">${esc(res.persona_text)}</p></div>
          <div>${scale("Mức chấp nhận rủi ro", "(bạn muốn)", res.tolerance, res.tolerance_level, "var(--s2)")}
            ${scale("Khả năng chịu rủi ro", "(dữ liệu cho thấy)", res.capacity, res.capacity_level, "var(--s1)")}
            <p class="small muted">Hồ sơ lấy mức thấp hơn của hai chỉ số.</p></div>
        </div>
        ${res.warnings.length ? `<div class="notice warn c12">${res.warnings.map(w => `<div>${icon("alert", {size: 15})} ${esc(w)}</div>`).join("")}</div>` : ""}
        <div class="panel c6"><h3>Vì sao khả năng chịu rủi ro ở mức này</h3>
          <ul class="warns plain">${res.capacity_reasons.map(w => `<li>${icon("check", {size: 15})}<span>${esc(w)}</span></li>`).join("")}</ul></div>
        <div class="panel c6"><h3>Phân bổ gợi ý <span class="hint">hồ sơ ${esc(res.profile.name)}</span></h3>
          <table class="table"><tbody>${Object.entries(res.profile.mix).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="r">${esc(v)}</td></tr>`).join("")}</tbody></table>
          <p class="small muted">Gợi ý mang tính mô phỏng; khuyến nghị cụ thể phải qua RM duyệt.</p></div>
        <div class="panel c12"><h3>Tự cập nhật</h3><p>Hệ thống sẽ hỏi lại vào <b>${esc(res.retest.date)}</b>, hoặc sớm hơn:</p>
          <ul class="ul">${res.retest.when.map(w => `<li>${esc(w)}</li>`).join("")}</ul>
          <button type="button" class="btn" id="risk-redo">Làm lại bài test</button></div></div>`;
    }
    box.querySelector(".rbody").outerHTML = `<div class="rbody">${body}</div>`;
    const $ = (s) => box.querySelector(s);
    if ($("#risk-start")) $("#risk-start").onclick = step;
    for (const b of box.querySelectorAll("[data-opt]")) {
      b.onclick = () => { run.answers[r.question.id] = b.dataset.opt; run.order.push(r.question.id); step(); };
    }
    if ($("#risk-back")) $("#risk-back").onclick = () => { delete run.answers[run.order.pop()]; step(); };
    if ($("#risk-redo")) $("#risk-redo").onclick = () => { runs[client] = {answers: {}, order: [], reply: null}; render(box, ctx); };
    const first = $(".opt");
    if (first && run.order.length) first.focus({preventScroll: true});
  };

  box.innerHTML = `${staff ? internal() : ""}
    <div class="pagehead"><div><div class="eyebrow">${staff ? "Khách hàng" : "Wealth Planning"}</div><h1 class="h1">Risk profile test</h1>
      <p class="lede">Bạn muốn chịu bao nhiêu rủi ro, và dữ liệu cho thấy bạn chịu được bao nhiêu</p></div></div>
    <div class="rbody"></div>`;
  draw();
}
