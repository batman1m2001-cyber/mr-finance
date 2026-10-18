"""Staff stress test U3 (docs/STAFF_STRESS_PLAN.md U-S6): each staff role's desk in a real browser on the served copy,
the real model — what HTTP cannot check: the docked assistant answering on the desk, the desk lighting what it read,
the panel's state, a write's Xác nhận button with nothing written before the click (RM), phone width without sideways
scroll, and (``--fail``) the fallback on a dead provider. Prints a JSON record; screenshots into OUT.

    .venv/bin/python -P scripts/stress_staff_browser.py <out dir>                                    (:8041)
    .venv/bin/python -P scripts/stress_staff_browser.py <out dir> --fail --base http://127.0.0.1:8042
"""

import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

exe = next(iter(sorted(Path.home().glob(".cache/ms-playwright/chromium-*/chrome-linux/chrome"))), None)
DESKS = [  # (person, role, the desk's question)
    ("rm01", "rm", "Sổ khách hàng hôm nay có gì cần làm?"),
    ("cio", "cio", "Có gì chờ tôi duyệt?"),
    ("sp_insurance", "specialist", "Khuyến nghị nào đang chờ tôi duyệt?"),
    ("compliance", "compliance", "Có gì đang chờ Tuân thủ?"),
    ("admin", "admin", "Hệ thống có gì bất thường?"),
]
# what the desk lights while the assistant works (web/desk/desk.js: a step's nodes take `act`, the answer keeps `lit`)
MARKS = """(() => { window.__marks = new Set();
  new MutationObserver(ms => { for (const m of ms) { const el = m.target;
    if (el.dataset && el.dataset.node && ['act', 'lit'].some(c => el.classList.contains(c)))
      window.__marks.add(el.dataset.node); } })
  .observe(document, {subtree: true, attributes: true, attributeFilter: ['class']});
})();"""
LAST = "() => { const b = [...document.querySelectorAll('#cp-msgs .cp-bot')].pop(); return b ? b.innerText : ''; }"
DONE = (
    "(() => { const b = [...document.querySelectorAll('#cp-msgs .cp-bot')].pop();"
    " return b && !b.hasAttribute('data-busy') && b.innerText.trim().length > 0; })()"
)


SPENT = {"cost": 0.0, "turns": 0}  # each answer frame's own usage (model and tools), as the harness counts it


def counted(req) -> None:
    if "/api/assistant/stream" not in req.url:
        return
    try:
        body = req.response().text()
    except Exception:  # noqa: BLE001 - a stream the page closed: its turn is counted by none
        return
    for line in body.splitlines():
        if line.startswith("data: ") and '"answer"' in line:
            u = (json.loads(line[6:]).get("assistant") or {}).get("usage") or {}
            SPENT["cost"] += float(u.get("cost_usd") or 0) + float(u.get("tools_cost_usd") or 0)
            SPENT["turns"] += 1


def context(b, base, vp, who):
    c = b.new_context(viewport={"width": vp[0], "height": vp[1]}, color_scheme="dark", bypass_csp=True)
    c.add_init_script("try { localStorage.setItem('mf.theme', 'dark'); } catch (_) {}")
    c.add_init_script(MARKS)
    c.on("requestfinished", counted)
    c.request.post(base + "/api/auth/demo", data={"id": who}).ok or sys.exit(f"sign-in failed for {who}")
    return c


def ask(p, q, timeout=120_000):
    if not p.locator("#cp-q:visible").count() and p.locator(".ws-ask:visible").count():
        p.click(".ws-ask")  # a phone: the dock is below the desk
    n = p.locator("#cp-msgs .cp-bot").count()
    p.evaluate("window.__marks && window.__marks.clear()")
    p.fill("#cp-q", q)
    p.press("#cp-q", "Enter")
    p.wait_for_function(f"document.querySelectorAll('#cp-msgs .cp-bot').length > {n}", timeout=timeout)
    p.wait_for_function(DONE, timeout=timeout)
    p.wait_for_timeout(500)
    return {
        "text": p.evaluate(LAST),
        "marks": sorted(p.evaluate("[...(window.__marks || [])]")),  # the nodes lit during the turn
        "lit": p.evaluate("document.querySelectorAll('.dk-center .lit').length"),  # kept after the answer
        "state": p.get_attribute(".cp-panel", "data-state"),
    }


def desk(b, base, out, who, role, q, vp, tag):
    c = context(b, base, vp, who)
    p = c.new_page()
    problems = []
    p.on("pageerror", lambda e: problems.append(str(e)))
    p.goto(f"{base}/#/{role}")
    p.wait_for_selector("#cp-q", state="attached", timeout=30_000)
    p.wait_for_timeout(1500)
    if tag != "desktop":  # its own conversation: the panel restores the person's last one, and a repeat is not a test
        if not p.locator("#cp-new:visible").count() and p.locator(".ws-ask:visible").count():
            p.click(".ws-ask")
        p.click("#cp-new")
    r = ask(p, q)
    r["sideways"] = p.evaluate("document.scrollingElement.scrollWidth > window.innerWidth")
    r["errors"] = problems
    p.screenshot(path=str(out / f"{role}_{tag}.jpg"), quality=80, full_page=tag == "phone")
    return c, p, r


def rm_write(c, base, p, out):
    """The RM's memory write: the button appears, nothing is written before the click, one item after it."""

    def items():
        return c.request.post(base + "/api/assistant/memory", data={"role": "rm", "action": "list"}).json()["memory"][
            "items"
        ]

    before = len(items())
    r = ask(p, "Nhớ giúp tôi: tôi chỉ gọi khách vào buổi sáng, trước 11 giờ.")
    btn = p.locator("button[data-ok]:visible")
    w = {"asked": r["text"], "button": btn.count(), "saved_before_click": len(items()) - before}
    p.screenshot(path=str(out / "rm_confirm_desktop.jpg"), quality=80)
    if btn.count():
        n = p.locator("#cp-msgs .cp-bot").count()
        btn.first.click()
        p.wait_for_function(f"document.querySelectorAll('#cp-msgs .cp-bot').length > {n}", timeout=120_000)
        p.wait_for_function(DONE, timeout=120_000)
        w["after"] = p.evaluate(LAST)
    w["saved_after_click"] = len(items()) - before
    return w


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out")
    ap.add_argument("--base", default="http://127.0.0.1:8041")
    ap.add_argument("--fail", action="store_true", help="the dead-provider copy: one desk per role, desktop only")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rec = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=str(exe))
        for who, role, q in DESKS:
            tags = [("fail", (1440, 900))] if a.fail else [("desktop", (1440, 900)), ("phone", (390, 844))]
            for tag, vp in tags:
                c, p, r = desk(b, a.base, out, who, role, q, vp, tag)
                if role == "rm" and tag == "desktop":
                    r["write"] = rm_write(c, a.base, p, out)
                rec[f"{role}_{tag}"] = r
                c.close()
        b.close()
    rec["spent"] = {"cost": round(SPENT["cost"], 5), "turns": SPENT["turns"]}
    sys.stdout.write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
