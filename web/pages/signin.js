/* Đăng nhập (BRD-RULE-SEC-01): every person signs in with their own account; the app then shows only their role's
   pages and only the families they may see. With MF_DEMO_ACCOUNTS on, the demo's accounts are listed below the
   form and open with one click; a bank deployment turns that off (and signs in through SSO). “Có mã một lần?” sets a
   password with the one-time code Admin hands over (Q-25, POST /api/auth/redeem). */
import {esc, get, post} from "../core/core.js";
import {icon} from "../core/icons.js";

// only the clients' accounts are listed (business feedback 2026-10-29); RM, CIO and Admin sign in with the form
const GROUPS = [
  ["client", "Khách hàng", "user"],
];

export async function render(box, ctx) {
  const {accounts} = ctx.demo ? await get("/api/auth/accounts") : {accounts: []};
  const names = Object.fromEntries(accounts.map(a => [a.id, a.name]));
  box.innerHTML = `
    <div class="signin">
      <form class="card signin-card" id="signin-form" autocomplete="on">
        <div class="h2">Đăng nhập</div>
        <div class="small muted">Mỗi người dùng tài khoản của mình: khách hàng thấy gia đình mình, RM thấy các gia đình được giao,
          CIO và Quản trị thấy phần việc của mình.</div>
        <label class="fld"><span>Email hoặc mã khách hàng</span>
          <input name="login" autocomplete="username" required maxlength="120" placeholder="vd. C01"></label>
        <label class="fld"><span>Mật khẩu</span>
          <input name="password" type="password" autocomplete="current-password" required maxlength="200"></label>
        <div class="row"><button type="submit" class="btn primary">Đăng nhập</button><span class="small bad-text" id="signin-err" role="alert"></span></div>
        <details class="signin-code" id="signin-code"><summary class="small">Có mã một lần?</summary><div class="stack mt">
          <div class="small muted">Quản trị trao mã khi tạo tài khoản hay đặt lại mật khẩu (dùng một lần, 24 giờ). Đặt mật khẩu mới bằng mã đó.</div>
          <label class="fld"><span>Mã một lần</span><input name="code" autocomplete="one-time-code" maxlength="20"></label>
          <label class="fld"><span>Mật khẩu mới (ít nhất 8 ký tự)</span><input name="new_password" type="password" autocomplete="new-password" maxlength="200"></label>
          <div class="row"><button type="button" class="btn" id="signin-redeem">Đặt mật khẩu và đăng nhập</button></div>
        </div></details>
      </form>
      ${accounts.length ? `
      <section class="card signin-demo" aria-labelledby="demo-h">
        <div class="row one"><span class="ic-chip">${icon("lock")}</span><div><div class="h3" id="demo-h">Tài khoản demo</div>
          <div class="small muted">Bấm để vào bằng tài khoản đó. Chỉ bật trên bản demo công khai; người và số liệu khách hàng đều là giả lập.</div></div></div>
        ${GROUPS.map(([role, label, ic]) => {
          const rows = accounts.filter(a => a.role === role);
          if (!rows.length) return "";
          return `<div class="demo-group"><div class="eyebrow">${icon(ic)} ${esc(label)}</div>
            <div class="demo-list">${rows.map(a => `
              <button type="button" class="demo-acc" data-acc="${esc(a.id)}">
                <b>${esc(a.name)}</b>
                <span class="small muted">${esc(a.member_of ? `Thành viên gia đình ${names[a.member_of] || a.member_of}` : a.title || "")}</span>
                <span class="small muted mono">${esc(a.login)}</span>
              </button>`).join("")}</div></div>`;
        }).join("")}
      </section>` : ""}
    </div>`;
  const err = box.querySelector("#signin-err");
  box.querySelector("#signin-form").onsubmit = async (e) => {
    e.preventDefault();
    err.textContent = "";
    const f = new FormData(e.target);
    try {
      await post("/api/auth/login", {login: f.get("login"), password: f.get("password")});
      ctx.signedIn();
    } catch (x) { err.textContent = x.message; }
  };
  box.querySelector("#signin-redeem").onclick = async () => {
    err.textContent = "";
    const f = new FormData(box.querySelector("#signin-form"));
    try {
      await post("/api/auth/redeem", {login: f.get("login"), code: f.get("code"), password: f.get("new_password")});
      ctx.signedIn();
    } catch (x) { err.textContent = x.message; }
  };
  for (const b of box.querySelectorAll("[data-acc]")) {
    b.onclick = async () => {
      b.disabled = true;
      try { await post("/api/auth/demo", {id: b.dataset.acc}); ctx.signedIn(); }
      catch (x) { err.textContent = x.message; b.disabled = false; }
    };
  }
}
