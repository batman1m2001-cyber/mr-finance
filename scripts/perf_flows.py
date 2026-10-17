"""The graph's idle cost while money flows: Chrome's CPU time over a fixed window (all its processes, from /proc:
browser, renderer, GPU/compositor, raster), and rAF frame intervals. C01, dark theme, 1440×900, headless software
raster (no GPU: every repaint is CPU, so this is the worst case, not a phone's GPU).
Usage: python -P flows_perf.py BASE LABEL LENS[:x] ... [--secs 6] [--runs 3] [--reduce] -> one JSON line per lens."""

import json
import os
import statistics
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests" / "ui"))
from test_graph_layout_ui import times  # noqa: E402  (the dense graph of the layout audit)

args = sys.argv[1:]
BASE, LABEL = args[0], args[1]
SECS = float(args[args.index("--secs") + 1]) if "--secs" in args else 6
RUNS = int(args[args.index("--runs") + 1]) if "--runs" in args else 3
REDUCE = "--reduce" in args
CSS = args[args.index("--css") + 1] if "--css" in args else ""
JS = Path(args[args.index("--js") + 1]).read_text() if "--js" in args else ""
LENSES = [
    a
    for i, a in enumerate(args[2:], 2)
    if not a.startswith("--") and not a.replace(".", "").isdigit() and args[i - 1] not in ("--css", "--js")
]
EXE = next(iter(sorted(Path.home().glob(".cache/ms-playwright/chromium-*/chrome-linux/chrome"))), None)
TICK = os.sysconf("SC_CLK_TCK")
FRAMES = """(ms) => new Promise(done => { const t = []; let last = performance.now();
  const end = last + ms;
  const f = (now) => { t.push(now - last); last = now; if (now < end) requestAnimationFrame(f); else done(t); };
  requestAnimationFrame(f); })"""


def chrome_cpu():
    """CPU seconds used so far by every Playwright Chromium process."""
    total = 0.0
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            if "ms-playwright/chromium" not in Path(f"/proc/{pid}/cmdline").read_text(errors="ignore"):
                continue
            f = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            total += (int(f[11]) + int(f[12])) / TICK
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return total


def many(o, n):
    """``o`` with n more spending categories under FL:out, from 0.3% to 30% of the month: low and high volumes."""
    o = {**o, "nodes": list(o["nodes"]), "edges": list(o["edges"])}
    proto = next(nd for nd in o["nodes"] if nd["id"].startswith("FC:out:"))
    big = max(abs(e.get("monthly") or 0) for e in o["edges"] if e["from"] == "FL:out")
    for k in range(n):
        v = round(big * (0.003 + 0.3 * (k / max(1, n - 1)) ** 2))
        nid = f"FC:out:x{k}"
        o["nodes"].append({**proto, "id": nid, "label": f"Chi {k + 1}", "value": v})
        o["edges"].append(
            {
                "from": "FL:out",
                "to": nid,
                "dir": "fwd",
                "value": v,
                "monthly": v,
                "label": f"Chi {k + 1}",
                "certainty": "actual",
            }
        )
    return o


def one(b, lens, x):
    c = b.new_context(
        viewport={"width": 1440, "height": 900},
        color_scheme="dark",
        bypass_csp=True,
        reduced_motion="reduce" if REDUCE else "no-preference",
    )
    c.add_init_script("try { localStorage.setItem('mf.theme', 'dark'); } catch (_) {}")
    c.request.post(BASE + "/api/auth/demo", data={"id": "C01"})
    if x > 1 or lens.endswith("+"):

        def fulfil(route):
            r = route.fetch()
            body = r.json()
            body["overview"] = many(body["overview"], 30) if lens.endswith("+") else times(body["overview"], x)
            route.fulfill(response=r, json=body)

        c.route("**/api/overview", fulfil)
    p = c.new_page()
    p.goto(f"{BASE}/?as=client#/client/xem/{lens.rstrip('+')}")
    p.wait_for_selector(".wedge", state="attached", timeout=30000)
    if lens.endswith("+"):  # open the spending flow: its categories show
        p.wait_for_timeout(1200)
        p.click('.wnode[data-n="FL:out"] .wcore')
        p.wait_for_timeout(600)
        if p.locator(".wnode.k-category").count() < 10:
            p.dblclick('.wnode[data-n="FL:out"] .wcore')
    if CSS:
        p.add_style_tag(content=CSS)
    if JS:
        p.wait_for_timeout(1500)
        p.evaluate(JS)
    p.wait_for_timeout(2500)  # the layout settles, the lens's slide ends
    count = p.evaluate(
        "({sparks: document.querySelectorAll('.wspark').length,"
        " edges: document.querySelectorAll('.wedge:not(.faint)').length,"
        " shown: [...document.querySelectorAll('.wspark')].filter(s => getComputedStyle(s).display !== 'none').length})"
    )
    cpu0, t0 = chrome_cpu(), time.monotonic()
    frames = p.evaluate(FRAMES, int(SECS * 1000))
    cpu = (chrome_cpu() - cpu0) / (time.monotonic() - t0)
    c.close()
    frames = frames[2:]
    return {**count, "cpu": cpu, "mean": statistics.mean(frames), "p95": sorted(frames)[int(len(frames) * 0.95)]}


with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=str(EXE)) if EXE else pw.chromium.launch()
    for spec in LENSES:
        lens, _, x = spec.partition(":")
        x = int(x or 1)
        rs = [one(b, lens, x) for _ in range(RUNS)]
        med = {k: round(statistics.median(r[k] for r in rs), 3) for k in ("cpu", "mean", "p95")}
        print(
            json.dumps(
                {
                    "label": LABEL,
                    "lens": lens,
                    "x": x,
                    "reduce": REDUCE,
                    **{k: rs[0][k] for k in ("sparks", "shown", "edges")},
                    **med,
                    "cpu_runs": [round(r["cpu"], 3) for r in rs],
                }
            ),
            flush=True,
        )
    b.close()
