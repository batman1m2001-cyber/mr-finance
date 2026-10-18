/* Tài khoản và vai trò (Admin; Q-25, owner 2026-10-18, docs/OWNER_BACKLOG_1018_PLAN.md U): every staff account with
   its role and state; a request to add an account, change a role, disable, enable or reset a password, which a
   second Admin approves here (two people, audited). An approved add or reset shows its one-time code once, for the
   approver to hand over; the person sets their password with it on the sign-in page. GET /api/accounts; POST
   /api/accounts/request, /api/accounts/decide. Rows are lists (.item; a request's badge and buttons sit in its one column), so a phone reads them as they are. */
import {ago, esc, get, post, toast} from "../core/core.js";

const STATE = {pending: "warn", approved: "good", rejected: "bad", withdrawn: ""};

function person(a, d, me) {
  const tags = [a.disabled ? `<span class="badge bad">Đã khoá</span>` : `<span class="badge good">Đang mở</span>`];
  if (a.code_waiting) tags.push(`<span class="badge warn">Chờ đặt mật khẩu</span>`);
  else if (!a.has_password && !a.disabled) tags.push(`<span class="badge">Chưa có mật khẩu</span>`);
  if (a.demo) tags.push(`<span class="badge">demo</span>`);
  const fam = a.families ? ` · ${a.families.length ? `${a.families.length} gia đình` : "chưa có gia đình"}` : "";
  const busy = d.requests.some(r => r.status === "pending" && r.person_id === a.id);
  const can = a.id !== me && !a.protected && !busy;
  const acts = !can ? "" : `<div class="row tight mt">
      <select class="acc-ctl" data-role-for="${esc(a.id)}" aria-label="Vai trò mới cho ${esc(a.name)}">
        <option value="">Đổi vai trò…</option>${Object.entries(d.roles).filter(([r]) => r !== a.role).map(([r, l]) => `<option value="${r}">${esc(l)}</option>`).join("")}</select>
      ${a.disabled ? `<button type="button" class="btn sm" data-kind="enable" data-id="${esc(a.id)}">Mở lại</button>`
        : `<button type="button" class="btn sm" data-kind="disable" data-id="${esc(a.id)}">Khoá</button>
           <button type="button" class="btn sm" data-kind="reset" data-id="${esc(a.id)}">Đặt lại mật khẩu</button>`}</div>`;
  const why = a.id === me ? "Tài khoản của bạn: nhờ một Quản trị khác." : a.protected ? "Tài khoản demo: giữ nguyên khi bật tài khoản demo." : busy ? "Có yêu cầu đang chờ." : "";
  return `<div class="item" data-person="${esc(a.id)}"><span class="badge">${esc(d.roles[a.role] || a.role)}</span>
    <div><div class="t">${esc(a.name)}</div><div class="m"><span class="mono">${esc(a.login)}</span>${a.title ? ` · ${esc(a.title)}` : ""}${fam}${a.families && a.families.length ? ` · <a href="#/admin/cau-hinh">Phân công RM</a>` : ""}</div>
      <div class="row tight">${tags.join("")}</div>${why ? `<div class="m">${why}</div>` : ""}${acts}</div><span></span></div>`;
}

function request(r, me) {
  const what = r.kind === "add" ? `${esc(r.name)} · <span class="mono">${esc(r.email)}</span> · ${esc(r.role_label || r.role)}`
    : `${esc(r.name)}${r.kind === "role" ? ` · ${esc(r.from_label || r.from_role)} → ${esc(r.role_label || r.role)}` : ""}`;
  const mine = r.by === me;
  const acts = r.status !== "pending" ? "" : mine
    ? `<button type="button" class="btn sm" data-decide="withdraw" data-req="${esc(r.id)}">Rút</button>`
    : `<input class="acc-ctl acc-why" data-why="${esc(r.id)}" maxlength="300" placeholder="Lý do (khi từ chối)" aria-label="Lý do từ chối ${esc(r.id)}">
       <button type="button" class="btn sm primary" data-decide="approve" data-req="${esc(r.id)}">Duyệt</button>
       <button type="button" class="btn sm" data-decide="reject" data-req="${esc(r.id)}">Từ chối</button>`;
  return `<div class="item acc-req" data-req-row="${esc(r.id)}">
    <div><span class="badge ${STATE[r.status]}">${esc(r.status_label)}</span><div class="t mt-xs">${esc(r.label)}: ${what}</div>
      <div class="m"><span class="mono">${esc(r.id)}</span> · ${esc(r.by)} đề xuất ${esc(ago(r.created))}${r.note ? ` · “${esc(r.note)}”` : ""}${r.decided_by ? ` · ${esc(r.decided_by)} ${r.status === "withdrawn" ? "rút" : "quyết định"} ${esc(ago(r.decided_at))}${r.decision_note ? `: “${esc(r.decision_note)}”` : ""}` : ""}</div>
      ${r.status === "pending" && mine ? `<div class="m">Chờ một Quản trị khác duyệt.</div>` : ""}
      ${acts ? `<div class="row tight mt">${acts}</div>` : ""}</div></div>`;
}

export async function render(box, ctx) {
  const d = await get("/api/accounts");
  const me = ctx.user;
  const waiting = d.requests.filter(r => r.status === "pending");
  const byRole = Object.keys(d.roles).map(r => [r, d.people.filter(p => p.role === r)]).filter(([, l]) => l.length);
  box.innerHTML = `
    <div class="pagehead"><div><div class="eyebrow">Quản trị</div>
      <h1 class="h1">Tài khoản và vai trò</h1>
      <p class="lede">${d.people.length} tài khoản nhân viên · ${d.people.filter(p => p.disabled).length} đã khoá ·
        ${waiting.length ? `<span class="warn-text">${waiting.length} yêu cầu chờ duyệt</span>` : "không yêu cầu nào chờ"}.
        Mỗi thay đổi là một yêu cầu: một Quản trị đề xuất, một Quản trị khác duyệt; mọi bước ghi vào nhật ký. Tài khoản
        khách hàng đi cùng hồ sơ gia đình, không quản lý ở đây.</p></div></div>
    ${d.demo_protected ? `<div class="note small" role="note">Đang bật tài khoản demo: các tài khoản demo được giữ nguyên để người xem sau vẫn vào được. Tài khoản thêm ở trang này thì đổi được.</div>` : ""}

    <section class="panel mt" id="acc-requests"><div class="h3">Yêu cầu</div>
      <div class="list">${d.requests.map(r => request(r, me)).join("") || `<p class="small muted">Chưa có yêu cầu nào.</p>`}</div></section>

    <section class="panel mt" id="acc-add"><div class="h3">Thêm tài khoản nhân viên</div>
      <form class="stack" id="acc-add-form" autocomplete="off">
        <div class="row">
          <label class="fld"><span>Họ tên</span><input name="full_name" required maxlength="80"></label>
          <label class="fld"><span>Email (tên đăng nhập)</span><input name="email" type="email" required maxlength="120"></label>
          <label class="fld"><span>Vai trò</span><select name="role" required>${Object.entries(d.roles).map(([r, l]) => `<option value="${r}">${esc(l)}</option>`).join("")}</select></label>
          <label class="fld"><span>Chức danh</span><input name="title" maxlength="80" placeholder="không bắt buộc"></label>
        </div>
        <label class="fld"><span>Ghi chú cho người duyệt</span><input name="note" maxlength="300"></label>
        <div class="row"><button type="submit" class="btn primary">Gửi yêu cầu</button>
          <span class="small muted">Khi được duyệt, người duyệt nhận một mã dùng một lần (24 giờ) để trao cho nhân viên; RM mới nhận gia đình ở Cấu hình › Phân công RM.</span></div>
      </form></section>

    <section class="panel mt" id="acc-people"><div class="h3">Tài khoản</div>
      ${byRole.map(([r, list]) => `<div class="eyebrow mt">${esc(d.roles[r])}</div><div class="list">${list.map(a => person(a, d, me)).join("")}</div>`).join("")}</section>`;

  const again = () => { if (box.isConnected) render(box, ctx).catch(() => {}); };
  const ask = async (body) => {
    try { const r = await post("/api/accounts/request", {...body, by: me}); toast(`Đã gửi yêu cầu ${r.request.id}: chờ một Quản trị khác duyệt`); again(); }
    catch (e) { toast(e.message); }
  };
  box.querySelector("#acc-add-form").onsubmit = async (e) => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target));
    try { const r = await post("/api/accounts/request", {kind: "add", ...f, by: me}); toast(`Đã gửi yêu cầu ${r.request.id}: chờ một Quản trị khác duyệt`); again(); }
    catch (x) { toast(x.message); }
  };
  box.querySelectorAll("[data-kind]").forEach(b => b.onclick = () => ask({kind: b.dataset.kind, person_id: b.dataset.id}));
  box.querySelectorAll("[data-role-for]").forEach(s => s.onchange = () => { if (s.value) ask({kind: "role", person_id: s.dataset.roleFor, role: s.value}); });
  box.querySelectorAll("[data-decide]").forEach(b => b.onclick = async () => {
    const action = b.dataset.decide;
    const why = box.querySelector(`[data-why="${CSS.escape(b.dataset.req)}"]`);
    const note = why ? why.value.trim() : "";
    if (action === "reject" && note.length < 5) { toast("Từ chối cần lý do"); if (why) why.focus(); return; }
    b.disabled = true;
    try {
      const r = await post("/api/accounts/decide", {request_id: b.dataset.req, action, note, by: me});
      if (r.request.code) {
        await render(box, ctx);
        const row = box.querySelector(`[data-req-row="${CSS.escape(r.request.id)}"] > div`);  // the row's text
        row.insertAdjacentHTML("beforeend", `<div class="note mt" role="status" id="acc-code"><b>Mã dùng một lần: <span class="mono">${esc(r.request.code)}</span></b><div class="small">Chỉ hiện lần này. Trao cho ${esc(r.request.name)} (không qua email); hết hạn sau 24 giờ. Họ đặt mật khẩu ở trang đăng nhập › Có mã một lần?</div></div>`);
      } else { toast(action === "approve" ? "Đã duyệt" : action === "reject" ? "Đã từ chối" : "Đã rút"); again(); }
    } catch (e) { toast(e.message); b.disabled = false; }
  });
}
