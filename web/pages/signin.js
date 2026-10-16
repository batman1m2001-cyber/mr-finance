/* Đăng nhập (BRD-RULE-SEC-01): every person signs in with their own account; the app then shows only their role's
   pages and only the families they may see. With MF_DEMO_ACCOUNTS on, the demo's accounts are listed below the
   form and open with one click; a bank deployment turns that off (and signs in through SSO). */
import {esc, get, post} from "../core/core.js";
import {icon} from "../core/icons.js";

const GROUPS = [
  ["client", "Khách hàng", "user"],
  ["rm", "Chuyên viên quan hệ khách hàng (RM)", "users"],
  ["cio", "Giám đốc đầu tư (CIO)", "activity"],
  ["compliance", "Tuân thủ", "shield"],
  ["admin", "Quản trị", "settings"],
  ["specialist", "Chuyên gia (duyệt khuyến nghị)", "check"],
];

export async function render(box, ctx) {
  const {accounts} = ctx.demo ? await get("/api/auth/accounts") : {accounts: []};
  const names = Object.fromEntries(accounts.map(a => [a.id, a.name]));
  box.innerHTML = `
    <div class="signin">
      <form class="card signin-card" id="signin-form" autocomplete="on">
        <div class="h2">Đăng nhập</div>
        <div class="small muted">Mỗi người dùng tài khoản của mình: khách hàng thấy gia đình mình, RM thấy các gia đình được giao,
          CIO, Tuân thủ và Quản trị thấy phần việc của mình.</div>
        <label class="fld"><span>Email hoặc mã khách hàng</span>
          <input name="login" autocomplete="username" required maxlength="120" placeholder="vd. yen.hoang@tcbwealth.example hoặc C01"></label>
        <label class="fld"><span>Mật khẩu</span>
          <input name="password" type="password" autocomplete="current-password" required maxlength="200"></label>
        <div class="row"><button type="submit" class="btn primary">Đăng nhập</button><span class="small bad-text" id="signin-err" role="alert"></span></div>
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
  for (const b of box.querySelectorAll("[data-acc]")) {
    b.onclick = async () => {
      b.disabled = true;
      try { await post("/api/auth/demo", {id: b.dataset.acc}); ctx.signedIn(); }
      catch (x) { err.textContent = x.message; b.disabled = false; }
    };
  }
}
