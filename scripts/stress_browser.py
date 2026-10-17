"""Stress test T3/S7 (docs/ASSISTANT_STRESS_PLAN.md): the real panel on the served copy (:8041), the real model —
what HTTP cannot check: the graph pick reaching the answer, the nodes lighting, the Xác nhận button and the state
after it, the title and history after a reload, phone width. Prints a JSON record; screenshots into OUT."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

exe = next(iter(sorted(Path.home().glob(".cache/ms-playwright/chromium-*/chrome-linux/chrome"))), None)
B = "http://127.0.0.1:8041"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
# the nodes the panel marks while it reads: act, then ok / lit / kept
LIT = """(() => { window.__lit = new Set();
  new MutationObserver(ms => { for (const m of ms) { const el = m.target;
    if (el.classList && ['act', 'ok', 'lit', 'kept'].some(c => el.classList.contains(c)) && el.dataset && el.dataset.n)
      window.__lit.add(el.dataset.n); } })
  .observe(document, {subtree: true, attributes: true, attributeFilter: ['class']});
})();"""
LAST = "() => { const b = [...document.querySelectorAll('#cp-msgs .cp-bot')].pop(); return b ? b.innerText : ''; }"
rec = {}


def context(b, vp, who="C01"):
    c = b.new_context(viewport={"width": vp[0], "height": vp[1]}, color_scheme="dark", bypass_csp=True)
    c.add_init_script("try { localStorage.setItem('mf.theme', 'dark'); } catch (_) {}")
    c.add_init_script(LIT)
    c.request.post(B + "/api/auth/demo", data={"id": who})
    return c


def ask(p, q, timeout=120_000):
    n = p.locator("#cp-msgs .cp-bot").count()
    p.evaluate("window.__lit && window.__lit.clear()")
    p.fill("#cp-q", q)
    p.press("#cp-q", "Enter")
    p.wait_for_function(f"document.querySelectorAll('#cp-msgs .cp-bot').length > {n}", timeout=timeout)
    p.wait_for_function("(() => { const b = [...document.querySelectorAll('#cp-msgs .cp-bot')].pop();"
                        " return b && !b.hasAttribute('data-busy') && b.innerText.trim().length > 0; })()",
                        timeout=timeout)  # fmt: skip
    p.wait_for_timeout(600)
    return p.evaluate(LAST), sorted(p.evaluate("[...(window.__lit || [])]"))


with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=str(exe))
    # desktop: a pick, a question about “this”, a write confirmed, the state, a reload
    c = context(b, (1440, 900))
    p = c.new_page()
    p.goto(f"{B}/?as=client#/client/xem/muc-tieu")
    p.wait_for_selector(".wnode.k-family")
    p.wait_for_timeout(1500)
    p.click('.wnode[data-n="GL:tuition"] .wcore')
    p.click("#ws-tab-a")
    text, lit = ask(p, "Nút này nói gì vậy?")
    rec["pick"] = {"text": text, "lit": lit, "mentions_goal": "học phí" in text.lower()}
    p.screenshot(path=str(OUT / "pick_desktop.jpg"), quality=80)
    before = c.request.post(
        B + "/api/assistant/memory", data={"role": "client", "client_id": "C01", "action": "list"}
    ).json()
    n_before = len(before["memory"]["items"])
    text, _ = ask(p, "Ghi nhớ giúp tôi: tôi muốn ưu tiên quỹ học phí cho con trước các khoản đầu tư khác.")
    btn = p.locator("button[data-ok]:visible")
    rec["write"] = {"asked": text, "button": btn.count()}
    p.screenshot(path=str(OUT / "confirm_desktop.jpg"), quality=80)
    mid = c.request.post(
        B + "/api/assistant/memory", data={"role": "client", "client_id": "C01", "action": "list"}
    ).json()
    rec["write"]["saved_before_click"] = len(mid["memory"]["items"]) - n_before
    if btn.count():
        n = p.locator("#cp-msgs .cp-bot").count()
        btn.first.click()
        p.wait_for_function(f"document.querySelectorAll('#cp-msgs .cp-bot').length > {n}", timeout=120_000)
        p.wait_for_function("(() => { const b = [...document.querySelectorAll('#cp-msgs .cp-bot')].pop();"
                            " return b && !b.hasAttribute('data-busy') && b.innerText.trim().length > 0; })()",
                            timeout=120_000)  # fmt: skip
        rec["write"]["after"] = p.evaluate(LAST)
    after = c.request.post(
        B + "/api/assistant/memory", data={"role": "client", "client_id": "C01", "action": "list"}
    ).json()
    rec["write"]["saved_after_click"] = len(after["memory"]["items"]) - n_before
    items = after["memory"]["items"]
    rec["write"]["item"] = next((i.get("text") for i in items if "học phí" in json.dumps(i, ensure_ascii=False)), None)
    p.wait_for_timeout(6000)  # the title (describe) after the answer
    msgs_before = p.locator("#cp-msgs .cp-bot").count()
    title_before = p.locator("#cp-title").inner_text() if p.locator("#cp-title").count() else None
    p.reload()
    p.wait_for_selector(".wnode.k-family")
    p.wait_for_timeout(2500)
    if not p.locator("#cp-q:visible").count() and p.locator("#ws-tab-a").count():
        p.click("#ws-tab-a")
    rec["reload"] = {
        "title_before": title_before,
        "msgs_before": msgs_before,
        "msgs_after": p.locator("#cp-msgs .cp-bot").count(),
        "title_after": p.locator("#cp-title").inner_text() if p.locator("#cp-title").count() else None,
    }
    p.click("#cp-hist")
    p.wait_for_timeout(1500)
    rec["reload"]["history"] = p.locator("#cp-hl").inner_text()[:600] if p.locator("#cp-hl").count() else None
    p.screenshot(path=str(OUT / "history_desktop.jpg"), quality=80)
    c.close()
    # phone: the same pick, one question, no sideways scroll
    c = context(b, (390, 844))
    p = c.new_page()
    p.goto(f"{B}/?as=client#/client/xem/muc-tieu")
    p.wait_for_selector(".wnode.k-family")
    p.wait_for_timeout(1500)
    p.click('.wnode[data-n="GL:tuition"] .wcore')
    if p.locator("#ws-tab-a").count():
        p.click("#ws-tab-a")
    text, lit = ask(p, "Mục tiêu này mỗi tháng cần để dành bao nhiêu?")
    rec["phone"] = {
        "text": text,
        "lit": lit,
        "sideways": p.evaluate("document.scrollingElement.scrollWidth > window.innerWidth"),
    }
    p.screenshot(path=str(OUT / "pick_phone.jpg"), quality=80, full_page=True)
    b.close()
print(json.dumps(rec, ensure_ascii=False, indent=1))
