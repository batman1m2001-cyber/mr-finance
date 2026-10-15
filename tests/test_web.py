"""The web shell (web/): every page the shell routes to exists and is served, and the new assets load."""

import re
from pathlib import Path

from starlette.testclient import TestClient

WEB = Path(__file__).resolve().parents[1] / "web"


def test_every_routed_page_module_exists_and_is_served():
    from app.web import app

    shell = (WEB / "shell.js").read_text(encoding="utf-8")
    pages = set(re.findall(r'page: "([a-z]+)"', shell))
    assert {"impact", "today", "inbox", "events", "exposure", "runs", "model", "held", "audit"} <= pages
    assert {"detail", "holdings", "plan", "risktest", "policy", "advisor", "performance", "perfall"} <= pages  # R3
    client = TestClient(app)
    for page in pages:
        assert (WEB / "pages" / f"{page}.js").is_file(), page
        assert client.get(f"/pages/{page}.js").status_code == 200
    for asset in ("/", "/shell.js", "/core/core.js", "/core/tokens.css", "/charts/charts.js", "/pages/trace.js"):
        r = client.get(asset)
        assert r.status_code == 200, asset
        # a module from before a deploy must not run beside one from after it: the browser checks every load
        assert r.headers["cache-control"] == "no-cache", asset


def test_every_page_is_a_module_page():
    # ADR-0019: the pre-redesign pages (app.js, app.css, charts.js, fmt.js) are gone; the shell routes modules only
    html = (WEB / "index.html").read_text(encoding="utf-8")
    shell = (WEB / "shell.js").read_text(encoding="utf-8")
    assert "legacy" not in shell and 'class="tab"' not in html
    for gone in ("app.js", "app.css", "charts.js", "fmt.js"):
        assert not (WEB / gone).exists() and gone not in html, gone
    assert "không phải cơ chế bảo mật" in html  # the role switcher says it is a demo
