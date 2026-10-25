/* Hiệu quả tư vấn over every client (SCR-RM-05; UI redesign R3, was the pre-redesign “perfall” tab; FEAT-28).
   Staff only. The same counts as performance.js summed over the clients, each AI's average score with its score
   per client, one row per client (a row opens that client's performance), the latest advice, the news missed
   grouped by item with the clients it touched, and the average reading. Data: GET /api/advisory/all. */
import {esc, get, n as how, pct, vnd} from "../core/core.js";
import {adviceTable, drawEngagement, drawSparks, engSeg, missedList, pipeline, tiles} from "./performance.js?v=20261025t2";

export async function render(box, ctx) {
  const a = await get("/api/advisory/all");
  const sm = a.summary;
  const rate = (c) => (c.right + c.wrong ? how(pct(c.right / (c.right + c.wrong), false, 0), "advisory.hit_rate", {right: String(c.right), wrong: String(c.wrong)}) : "—");

  box.innerHTML = `
    <div class="pagehead"><div><h1 class="h1" lang="en">Advisory performance</h1>
      <p class="lede">Hiệu quả tư vấn và AI trên tất cả khách hàng · ${a.clients.length} khách hàng · 12 tháng</p></div></div>
    ${tiles(sm, `lượt khách hàng · tác động ${how(vnd(sm.missed_news_value, true), "advisory.missed_news")}`)}
    ${pipeline(a.agents, "điểm trung bình trên mọi khách hàng · xu hướng độ chính xác 12 tháng",
      g => g.by_client.map(c => `<div class="kv"><span>${esc(c.client)}</span><b>${how(String(c.score), "advisory.agent_metric")}</b></div>`).join(""))}
    <div class="panel mt"><h3>Theo từng khách hàng <span class="hint">bấm một dòng để mở chi tiết khách hàng đó</span></h3>
      <div class="scrollx"><table class="table"><thead><tr><th>Khách hàng</th><th class="r">Khuyến nghị</th><th class="r">Đúng / sai</th><th class="r">Tỷ lệ đúng</th>
        <th class="r">Tiền mang lại</th><th class="r">Thiệt hại</th><th class="r">Bỏ lỡ</th><th class="r">Tin bị bỏ sót</th><th class="r">Mở cảnh báo</th></tr></thead><tbody>
        ${a.clients.map(c => `<tr class="rowlink" data-client="${esc(c.id)}" tabindex="0" role="link" aria-label="Mở hiệu quả tư vấn của ${esc(c.name)}">
          <td><b>${esc(c.name)}</b></td><td class="r">${c.advice}</td><td class="r">${c.right} / ${c.wrong}</td><td class="r">${rate(c)}</td>
          <td class="r up">${how(vnd(c.gained, true), "advisory.value", {count: String(c.right)})}</td><td class="r down">${c.lost ? how(vnd(c.lost, true), "advisory.value", {count: String(c.wrong)}) : "—"}</td>
          <td class="r">${c.missed} · ${how(vnd(c.missed_value), "advisory.value", {count: String(c.missed)})}</td><td class="r">${c.missed_news}</td><td class="r">${how(esc(c.alerts_opened), "advisory.alerts_opened")}</td></tr>`).join("")}
      </tbody></table></div></div>
    <div class="cols mt">
      <div class="panel c7"><h3>Nhật ký khuyến nghị <span class="hint">mới nhất · ${a.advice.length} khuyến nghị</span></h3>${adviceTable(a.advice.slice(0, 12), true)}</div>
      <div class="panel c5"><h3>Tin quan trọng bị bỏ lỡ <span class="hint">gộp theo tin · tổng tác động</span></h3>${missedList(a.missed_news)}</div>
    </div>
    <div class="panel mt"><h3>Mức độ theo dõi tin của khách hàng <span class="hint">trung bình mọi khách hàng</span></h3>
      ${engSeg()}<div id="eng-chart" class="mt"></div></div>
    <p class="small muted mt">${esc(a.note)}</p>`;
  drawSparks(box, a.agents, "độ chính xác trung bình 12 tháng");
  drawEngagement(box, a.engagement);
  for (const row of box.querySelectorAll("[data-client]")) {
    const open = () => { ctx.setClient(row.dataset.client); ctx.go("#/rm/khach-hang/hieu-qua"); };
    row.onclick = open;
    row.onkeydown = (ev) => { if (ev.key === "Enter") open(); };
  }
}
