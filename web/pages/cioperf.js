/* CIO · Hiệu quả (OWN-FB-16): one plain page, how much news came in and what became of it, and how the
   approved views' forecasts are doing. Every figure from the reads the CIO's pages already use: the inbox
   (news), the events with their views, and the forecast scoring (/api/accuracy). Nothing technical. */
import {esc, get, n as how, pct, HORIZON} from "../core/core.js";

const DAY = 86400;
const kpi = (label, value, sub) => `<div class="kpi pcard"><div class="k">${label}</div><div class="v">${value}</div><div class="s muted">${sub}</div></div>`;

export async function render(box, ctx) {
  const now = Date.now() / 1000;
  const midnight = new Date(new Date().setHours(0, 0, 0, 0)).getTime() / 1000;
  const [news, {events}, acc] = await Promise.all([
    get(`/api/news/inbox?status=all&since=${Math.floor(now - 7 * DAY)}&limit=5000`),
    get("/api/events"),
    get("/api/accuracy"),
  ]);
  const items = news.items;
  const today = items.filter(i => i.ingested >= midnight).length;
  const relevant = items.filter(i => i.relevance === "high" || i.relevance === "medium").length;
  const grouped = items.filter(i => i.status === "grouped").length;
  const week = events.filter(e => e.created >= now - 7 * DAY);
  const views = events.flatMap(e => e.views || []);
  const count = (s) => views.filter(v => v.status === s).length;
  const approved = count("APPROVED"), waiting = count("PENDING_APPROVAL") + count("PENDING_CHALLENGE");
  const returned = count("REWORK_REQUESTED") + count("REJECTED");

  // the approved views' forecasts: scored right (the direction held), wrong, or still waiting for their date
  const fc = acc.recorded.flatMap(r => r.forecasts);
  const right = fc.filter(f => f.direction_hit === true).length, wrong = fc.filter(f => f.direction_hit === false).length;
  const open = fc.filter(f => f.result == null).length;
  const byH = Object.keys(HORIZON).map(h => {
    const xs = fc.filter(f => f.horizon === h);
    return {h, right: xs.filter(f => f.direction_hit === true).length, wrong: xs.filter(f => f.direction_hit === false).length,
      open: xs.filter(f => f.result == null).length, next: xs.filter(f => f.result == null).map(f => f.due).sort()[0]};
  });
  const hist = (acc.history && acc.history.kpi03) || {};  // a bank with no forecast scored yet has none

  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">CIO · 7 ngày qua</div><div class="h1">Hiệu quả</div>
      <div class="lede small">Bao nhiêu tin đến, bao nhiêu thành nhận định, và các dự báo đã duyệt đúng hay sai.</div></div></div>
    <div class="panel"><h3>Tin tức</h3>
      <div class="kpis">
        ${kpi("Tin thu thập hôm nay", today, `${items.length} tin trong 7 ngày`)}
        ${kpi("Tin liên quan", relevant, "mức liên quan cao hoặc vừa, 7 ngày")}
        ${kpi("Gom thành sự kiện", grouped, `${week.length} sự kiện mới trong 7 ngày`)}
        ${kpi("Nhận định đã duyệt", approved, `${waiting} chờ duyệt · ${returned} trả lại hoặc từ chối`)}
      </div></div>
    <div class="panel mt"><h3>Dự báo đã duyệt <span class="hint">chấm khi đến hạn</span></h3>
      <div class="kpis three">
        ${kpi("Đúng hướng", right, right + wrong ? `${how(pct(right / (right + wrong), false, 0), "accuracy.direction")} trên ${right + wrong} dự báo đã chấm` : "chưa có dự báo nào đến hạn")}
        ${kpi("Sai hướng", wrong, `${right + wrong} dự báo đã chấm`)}
        ${kpi("Đang chờ đến hạn", open, `của ${fc.length} dự báo từ ${acc.recorded.length} nhận định`)}
      </div>
      <table class="table mt"><thead><tr><th>Kỳ hạn</th><th class="num">Đúng</th><th class="num">Sai</th><th class="num">Đang chờ</th><th>Đến hạn gần nhất</th><th class="num">Qua lịch sử</th></tr></thead>
        <tbody>${byH.map(r => `<tr><td>${esc(HORIZON[r.h])}</td><td class="num">${r.right}</td><td class="num">${r.wrong}</td><td class="num">${r.open}</td>
          <td>${r.next ? esc(r.next) : "—"}</td>
          <td class="num">${hist[r.h] && hist[r.h].hit != null ? `${how(pct(hist[r.h].hit, false, 0), "accuracy.direction")} <span class="small muted">/ ${hist[r.h].n} lần</span>` : "—"}</td></tr>`).join("")}</tbody></table>
      <div class="footnote">Qua lịch sử: mô hình chạy lại trên dữ liệu ${esc(acc.history.from)} → ${esc(acc.history.to)}, tỷ lệ đúng hướng; mục tiêu ${pct(acc.history.target, false, 0)}. Dự báo chưa đến hạn không tính đúng hay sai.</div>
    </div>`;
}
