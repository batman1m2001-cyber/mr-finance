"""Dragging the dock's divider on the ×3 graph with the long conversation open: 120 pointer moves out 256 px and back,
3 rounds. Frame intervals and long tasks inside the drags only. Optional CSS (ablation) as the third argument."""

import json
import statistics
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests" / "ui"))
from test_graph_layout_ui import times

B, LABEL = sys.argv[1], sys.argv[2]
CSS = sys.argv[3] if len(sys.argv) > 3 else ""
EXE = next(iter(sorted(Path.home().glob(".cache/ms-playwright/chromium-*/chrome-linux/chrome"))))
REC = """() => { window.__f = []; window.__l = []; window.__on = false;
  new PerformanceObserver(l => { for (const e of l.getEntries()) if (window.__on) window.__l.push(e.duration); })
    .observe({type: 'longtask'});
  (function f(now) { if (window.__on) window.__f.push(now); requestAnimationFrame(f); })(performance.now()); }"""
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=str(EXE))
    c = b.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark")
    c.add_init_script(
        "try { localStorage.setItem('mf.theme', 'dark'); localStorage.removeItem('mf.ws.dockw'); } catch (_) {}"
    )
    c.request.post(B + "/api/auth/demo", data={"id": "C01"})

    def fulfil(route):
        r = route.fetch()
        body = r.json()
        body["overview"] = times(body["overview"], 3)
        route.fulfill(response=r, json=body)

    c.route("**/api/overview", fulfil)
    p = c.new_page()
    p.goto(f"{B}/?as=client#/client/xem/tong-quan")
    p.wait_for_selector(".wedge", state="attached")
    p.wait_for_function("document.querySelectorAll('#cp-msgs .cp-bot').length > 10", timeout=20000)
    p.wait_for_timeout(2000)
    if CSS:
        p.add_style_tag(content=CSS)
    p.evaluate(REC)
    for _ in range(3):
        sp = p.locator("#ws-split").bounding_box()
        x0, y = sp["x"] + sp["width"] / 2, sp["y"] + sp["height"] / 2
        p.mouse.move(x0, y)
        p.mouse.down()
        p.evaluate("window.__on = true")
        for i in range(1, 121):
            k = i / 60 if i <= 60 else (120 - i) / 60
            p.mouse.move(x0 - 256 * k, y)
        p.evaluate("window.__on = false")
        p.mouse.up()
        p.wait_for_timeout(800)
    f = p.evaluate("window.__f")
    lt = p.evaluate("window.__l")
    t = [b_ - a for a, b_ in zip(f, f[1:]) if b_ - a < 2000]
    print(
        json.dumps(
            {
                "label": LABEL,
                "frames": len(t),
                "mean": round(statistics.mean(t), 1),
                "p95": round(sorted(t)[int(len(t) * 0.95)], 1),
                "worst": round(max(t), 1),
                "long_tasks": len(lt),
                "long_ms": round(sum(lt)),
            }
        )
    )
    b.close()
