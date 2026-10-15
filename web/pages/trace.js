/* "Cách tính": one number of a family, back to the news it came from (FR-406). Staff only. */
import {internal, drawer, esc, failed, get, loading, pct, vnd, when, severity, runBadge} from "../core/core.js";

let factorNames = null;
export async function names() {
  if (!factorNames) {
    try {
      const m = await get("/api/model");
      factorNames = Object.fromEntries(m.factors.map(f => [f.id, f.name]));
    } catch (_) { factorNames = {}; }
  }
  return factorNames;
}

const DIR = {1: "tăng", "-1": "giảm"};

export async function openTrace(runId, familyId, key) {
  const body = drawer("Cách tính con số này", loading(4));
  try {
    const [t, nm] = await Promise.all([get(`/api/trace/${encodeURIComponent(runId)}/${encodeURIComponent(familyId)}${key ? `?key=${encodeURIComponent(key)}` : ""}`), names()]);
    const n = t.number;
    const holdings = [...t.holdings].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)).slice(0, 6);
    const resp = (t.challenge && t.challenge.responses) || {};
    const crit = t.challenge ? t.challenge.findings.filter(f => f.severity === "critical") : [];
    body.innerHTML = `${internal()}
      <div class="chain">
        <div class="link data"><div class="k">Con số · ${esc(t.family.name)}</div>
          <div class="hero sm ${n.value < 0 ? "down" : "up"}">${vnd(n.value, true)}</div>
          <div class="small muted">${esc(n.label)} · ${pct(n.pct, true, 2)} tài sản ròng · dải P10 ${vnd(n.band.p10, true)} đến P90 ${vnd(n.band.p90, true)}</div>
          <div class="small" style="margin-top:6px">${esc(t.formula)}</div></div>
        <div class="link data"><div class="k">Vị thế góp phần nhiều nhất</div>
          <table class="table"><tbody>${holdings.map(h => `<tr><td>${esc(h.name)}<div class="small muted">${esc(h.method)}${h.modelled ? ' · <span class="badge assumed">theo mô hình</span>' : ""}</div></td><td class="r ${h.contribution < 0 ? "down" : "up"}">${vnd(h.contribution, true)}</td></tr>`).join("")}</tbody></table></div>
        <div class="link ai"><div class="k">Kịch bản (Agent CIO soạn, CIO duyệt)</div>
          ${t.branches.map(b => `<div style="margin:6px 0"><b>${esc(b.name)}</b> · ${pct(b.probability, false, 0)}${b.regime === "stressed" ? ' · <span class="badge warn">căng thẳng</span>' : ""}
            <div class="small">Cú sốc lõi: ${b.core.map(s => `${esc(nm[s.factor] || s.factor)} ${DIR[s.direction]} cỡ ${s.size}`).join("; ")}</div>
            <div class="small muted">Gia đình trong nhánh này: ${vnd(b.family_expected, true)}</div></div>`).join("")}</div>
        <div class="link human"><div class="k">CIO duyệt</div>
          ${t.approval ? `<div>${esc(t.approval.by)} · ${when(t.approval.created)}</div><div class="small muted">“${esc(t.approval.reason)}”</div>` : "<div class='muted'>—</div>"}
          <div class="small" style="margin-top:4px">Lần áp dụng ${esc(t.run.id)} ${runBadge(t.run.status, t.run.status_label)}</div></div>
        <div class="link ai"><div class="k">Phản biện độc lập</div>
          ${t.challenge ? `<div class="small">${esc(t.challenge.model)} · ${t.challenge.findings.length} phát hiện · ${crit.length} nghiêm trọng (${crit.filter(f => resp[f.id]).length} đã trả lời)</div>
          ${crit.map(f => `<div class="small" style="margin-top:4px">${severity(f.severity)} ${esc(f.title)}${resp[f.id] ? `<div class="muted">CIO: ${esc(resp[f.id].reason)}</div>` : ""}</div>`).join("")}` : "<div class='muted'>—</div>"}</div>
        <div class="link"><div class="k">Sự kiện và tin nguồn</div>
          <div><b>${esc(t.event.title)}</b> <span class="small muted">${esc(t.event.id)}</span></div>
          ${t.news.map(x => `<div class="small" style="margin-top:4px"><a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${esc(x.title)}</a><div class="muted">${esc(x.outlet)} · ${esc(x.label)} · ${when(x.published)}</div></div>`).join("")}</div>
        <div class="link data"><div class="k">Ảnh chụp đã đông cứng</div>
          <div class="small">Giá ngày ${esc(t.snapshot.price_date)} · mô hình ${esc(t.snapshot.model.version)} ${t.snapshot.model.assumed ? '<span class="badge assumed">tham số giả định</span>' : ""} · ${esc(t.snapshot.engine_version)}</div>
          <div class="small muted num" style="word-break:break-all">SHA-256 ${esc(t.snapshot.hash)}</div></div>
      </div>`;
  } catch (e) {
    body.innerHTML = failed(e);
  }
}
