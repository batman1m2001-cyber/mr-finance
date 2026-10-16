/* Bộ nhớ (A4, FEAT-37; ADR-0028): what the assistant remembers about the person signed in — a few items they asked
   it to keep, each with its kind, when, from which conversation, and when it expires — to correct or forget, one or
   all; their past conversations with it, searchable, to open in the panel or delete; and the documents they add
   for it to read (A5: searched on the server only; a client's are readable by their RM); the follow-ups they set,
   to cancel (A6); items the consolidator drew from a conversation are marked as such. Everything is theirs
   only: the server keys every read and write by who is signed in (POST /api/assistant/memory, /conversations). */
import {esc, post, read, toast, when} from "../core/core.js";

const day = (t) => { const d = new Date(t * 1000); return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`; };

export async function render(box, ctx) {
  const who = {role: ctx.role, client_id: ctx.role === "client" || ctx.role === "rm" ? ctx.client() : null};
  const mem = (action, body = {}) => post("/api/assistant/memory", {...who, action, ...body}).then(r => r.memory);
  const convs = (action, body = {}) => post("/api/assistant/conversations", {...who, action, ...body}).then(r => r.conversations);
  const look = (path, action) => read(path, {...who, action}).then(r => r.memory || r.conversations);  // lists: forget nothing
  const [m, c, d, f] = await Promise.all([look("/api/assistant/memory", "list"), look("/api/assistant/conversations", "list"),
    look("/api/assistant/memory", "materials"), look("/api/assistant/memory", "follow_ups")]);
  if (!box.isConnected) return;

  const item = (i) => `<li class="mem-item" data-item="${esc(i.id)}">
      <div class="mem-top"><span class="pill">${esc(i.kind_label)}</span><b class="mem-text">${esc(i.text)}</b></div>
      <div class="small muted">Ghi ${esc(day(i.created))}${i.updated - i.created > 60 ? ` · sửa ${esc(day(i.updated))}` : ""}${i.expires ? ` · hết hạn ${esc(day(i.expires))}` : " · không hết hạn"}${i.source && i.source.conversation ? ` · <a href="#" data-conv="${esc(i.source.conversation)}">từ cuộc trò chuyện</a>` : ""}${i.source && i.source.by === "consolidator" ? " · trợ lý tự rút ra" : ""}</div>
      <div class="row mt-xs"><button type="button" class="btn sm ghostbtn" data-edit="${esc(i.id)}">Sửa</button><button type="button" class="btn sm ghostbtn" data-forget="${esc(i.id)}">Quên</button></div>
    </li>`;
  const conv = (x) => `<li class="mem-conv"><div><b>${esc(x.title || "Cuộc trò chuyện")}</b><div class="small muted">${esc(when(x.updated))} · ${x.turns} lượt</div></div>
      <div class="row"><button type="button" class="btn sm ghostbtn" data-open="${esc(x.id)}">Mở</button><button type="button" class="btn sm ghostbtn" data-delconv="${esc(x.id)}">Xoá</button></div></li>`;

  const doc = (x) => `<li class="mem-conv" data-doc="${esc(x.key)}"><div><b>${esc(x.name)}</b><div class="small muted">${x.added ? esc(when(x.added)) : ""}${x.own ? "" : " · của khách hàng"}</div></div>
      ${x.own ? `<div class="row"><button type="button" class="btn sm ghostbtn" data-deldoc="${esc(x.key)}">Xoá</button></div>` : ""}</li>`;

  const STATE = {open: ["Đang theo dõi", ""], fired: ["Đã báo", "good"]};
  const fu = (x) => `<li class="mem-conv" data-fu="${esc(x.id)}"><div><b>${esc(x.text)}</b><div class="small muted"><span class="pill ${STATE[x.status][1]}">${STATE[x.status][0]}</span>
      ${x.status === "fired" ? ` · ${esc(x.fired_text)}` : ` · đến ${esc(day(x.expires))}`}</div></div>
      ${x.status === "open" ? `<div class="row"><button type="button" class="btn sm ghostbtn" data-cancelfu="${esc(x.id)}">Huỷ</button></div>` : ""}</li>`;

  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Trợ lý OneWealth</div><h1 class="h1">Bộ nhớ</h1>
      <p class="lede">Những điều trợ lý ghi nhớ về bạn (bạn nhờ, hoặc trợ lý rút ra khi cuộc trò chuyện kết thúc), việc bạn nhờ theo dõi, các cuộc trò chuyện của bạn với trợ lý và tài liệu bạn thêm. Điều ghi nhớ và cuộc trò chuyện chỉ bạn thấy; bạn sửa hoặc xoá được mọi thứ ở đây. Trợ lý không ghi số tiền, số tài khoản hay thông tin của người ngoài gia đình.</p></div></div>
    <div class="cols">
      <section class="panel c6" aria-labelledby="mem-h">
        <div class="sechead"><h2 class="h2" id="mem-h">Điều trợ lý ghi nhớ</h2><span class="small muted"><b>${m.items.length}</b> mục</span></div>
        ${m.items.length ? `<ul class="mem-list">${m.items.map(item).join("")}</ul>
          <button type="button" class="btn sm danger mt" id="mem-clear">Quên tất cả</button>`
        : `<p class="muted">Chưa có gì. Trong khung trợ lý, nói “Hãy nhớ là…” để trợ lý ghi nhớ một điều; bạn xác nhận trước khi nó được lưu.</p>`}
      </section>
      <section class="panel c6" aria-labelledby="fu-h">
        <div class="sechead"><h2 class="h2" id="fu-h">Việc theo dõi</h2><span class="small muted"><b>${f.follow_ups.filter(x => x.status === "open").length}</b> đang mở</span></div>
        ${f.follow_ups.length ? `<ul class="mem-list">${f.follow_ups.map(fu).join("")}</ul>`
        : `<p class="muted">Chưa có. Trong khung trợ lý, nói “Báo tôi khi VN-Index dưới 1.200” hoặc “khi có tin về lãi suất”: chuông thông báo báo một lần khi điều đó xảy ra.</p>`}
      </section>
      <section class="panel c6" aria-labelledby="conv-h">
        <div class="sechead"><h2 class="h2" id="conv-h">Các cuộc trò chuyện</h2><span class="small muted"><b>${c.items.length}</b> cuộc</span></div>
        <form class="row" id="mem-search"><input id="mem-q" placeholder="Tìm trong các cuộc trò chuyện…" aria-label="Tìm trong các cuộc trò chuyện" style="flex:1;min-width:0">
          <button type="submit" class="btn sm">Tìm</button></form>
        <div id="mem-hits"></div>
        ${c.items.length ? `<ul class="mem-list mt">${c.items.map(conv).join("")}</ul>` : `<p class="muted mt">Chưa có cuộc trò chuyện nào.</p>`}
      </section>
      <section class="panel c6" aria-labelledby="doc-h">
        <div class="sechead"><h2 class="h2" id="doc-h">Tài liệu của bạn</h2><span class="small muted"><b>${d.materials.length}</b> tệp</span></div>
        <p class="small muted">Thêm tài liệu để hỏi trợ lý về nó (Word, PDF, Excel, PowerPoint, văn bản; tối đa 5 MB). ${ctx.role === "client" ? "Chỉ bạn và RM phụ trách bạn đọc được." : "Chỉ bạn đọc được."} Tệp được tìm ngay trên máy chủ OneWealth, không gửi sang dịch vụ khác để xử lý; trợ lý chỉ đọc đoạn khớp câu hỏi.</p>
        <form class="row mt-xs" id="doc-add"><input type="file" id="doc-file" accept=".txt,.md,.html,.htm,.docx,.pptx,.xlsx,.pdf" aria-label="Chọn tài liệu" style="flex:1;min-width:0">
          <button type="submit" class="btn sm">Thêm</button></form>
        ${d.materials.length ? `<ul class="mem-list mt">${d.materials.map(doc).join("")}</ul>` : `<p class="muted mt">Chưa có tài liệu nào.</p>`}
      </section>
    </div>`;

  const again = () => box.isConnected && render(box, ctx);
  const openInPanel = (id) => window.dispatchEvent(new CustomEvent("mf:open-conversation", {detail: {id}}));
  for (const a of box.querySelectorAll("[data-conv]")) a.onclick = (e) => { e.preventDefault(); openInPanel(a.dataset.conv); };
  for (const b of box.querySelectorAll("[data-open]")) b.onclick = () => openInPanel(b.dataset.open);
  for (const b of box.querySelectorAll("[data-forget]")) b.onclick = async () => {
    try { await mem("delete", {item_id: b.dataset.forget}); toast("Đã quên mục này"); } catch (e) { toast(e.message); }
    again();
  };
  for (const b of box.querySelectorAll("[data-edit]")) b.onclick = () => {
    const li = b.closest("[data-item]"), text = li.querySelector(".mem-text").textContent;
    li.querySelector(".mem-top").innerHTML = `<span class="pill">${esc(li.querySelector(".pill").textContent)}</span><input class="mem-input" maxlength="200" value="${esc(text)}" aria-label="Sửa mục ghi nhớ">`;
    b.textContent = "Lưu";
    b.onclick = async () => {
      try { await mem("update", {item_id: li.dataset.item, text: li.querySelector(".mem-input").value}); toast("Đã sửa"); again(); }
      catch (e) { toast(e.message); }
    };
  };
  const clear = box.querySelector("#mem-clear");
  if (clear) clear.onclick = async () => {
    if (!confirm("Quên tất cả những điều trợ lý ghi nhớ về bạn? Không lấy lại được.")) return;
    try { await mem("clear"); toast("Đã quên tất cả"); } catch (e) { toast(e.message); }
    again();
  };
  for (const b of box.querySelectorAll("[data-delconv]")) b.onclick = async () => {
    if (!confirm("Xoá cuộc trò chuyện này? Không lấy lại được.")) return;
    try { await convs("delete", {conversation_id: b.dataset.delconv}); toast("Đã xoá"); } catch (e) { toast(e.message); }
    again();
  };
  for (const b of box.querySelectorAll("[data-cancelfu]")) b.onclick = async () => {
    try { await mem("follow_up_cancel", {key: b.dataset.cancelfu}); toast("Đã huỷ theo dõi"); } catch (e) { toast(e.message); }
    again();
  };
  for (const b of box.querySelectorAll("[data-deldoc]")) b.onclick = async () => {
    if (!confirm("Xoá tài liệu này? Không lấy lại được.")) return;
    try { await mem("material_delete", {key: b.dataset.deldoc}); toast("Đã xoá"); } catch (e) { toast(e.message); }
    again();
  };
  box.querySelector("#doc-add").onsubmit = async (e) => {
    e.preventDefault();
    const f = box.querySelector("#doc-file").files[0];
    if (!f) { toast("Chọn một tệp"); return; }
    if (f.size > 5 * 1024 * 1024) { toast("Tệp quá 5 MB"); return; }
    const data = await new Promise((ok, no) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(",", 2)[1] || ""); r.onerror = no; r.readAsDataURL(f); });
    try { await mem("material_add", {file_name: f.name, data}); toast("Đã thêm " + f.name); } catch (err) { toast(err.message); }
    again();
  };
  box.querySelector("#mem-search").onsubmit = async (e) => {
    e.preventDefault();
    const q = box.querySelector("#mem-q").value.trim();
    const out = box.querySelector("#mem-hits");
    if (!q) { out.innerHTML = ""; return; }
    const {hits} = await mem("search", {query: q});
    out.innerHTML = hits.length ? `<p class="small muted mt"><b>${hits.length}</b> chỗ khớp “${esc(q)}”</p><ul class="mem-list mt-xs">${hits.map(h => `<li class="mem-hit"><div class="small muted">${esc(h.title)} · ${esc(h.author)} · ${esc(when(h.at))}</div>
        <div>…${esc(h.snippet)}…</div><button type="button" class="linkbtn small" data-open="${esc(h.conversation_id)}">Mở cuộc trò chuyện</button></li>`).join("")}</ul>`
      : `<p class="muted mt">Không thấy “${esc(q)}”.</p>`;
    for (const b of out.querySelectorAll("[data-open]")) b.onclick = () => openInPanel(b.dataset.open);
  };
}
