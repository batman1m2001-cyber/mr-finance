"""The web shell (web/): every page the shell routes to exists and is served, and the new assets load."""

import re
from pathlib import Path

from starlette.testclient import TestClient

WEB = Path(__file__).resolve().parents[1] / "web"


def test_every_routed_page_module_exists_and_is_served():
    from app.web import app

    shell = (WEB / "shell.js").read_text(encoding="utf-8")
    pages = set(re.findall(r'page: "([a-z]+)"', shell))
    assert {"impact", "events", "exposure", "runs", "model", "held", "audit"} <= pages
    assert (WEB / "pages" / "inbox.js").is_file()  # no route of its own: the CIO's board draws it (OWN-FB-11)
    assert {"detail", "holdings", "plan", "risktest", "policy", "advisor", "performance", "perfall", "allocation"} <= pages  # R3; allocation: SCR-CL-13
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
    assert "Mỗi người đăng nhập bằng tài khoản của mình" in html  # sign-in replaced the role switcher (ADR-0020)


def test_the_pages_reach_the_backend_only_through_lib_api():
    # D8: one BASE in web/lib/api.js; to serve web/ from elsewhere, only that line changes
    from app.web import app

    found = [
        f"{p.relative_to(WEB)}:{n}"
        for p in WEB.rglob("*.js")
        if p != WEB / "lib" / "api.js"
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"\bfetch\(|new WebSocket\((?!socket\()|new EventSource\(", line)  # a WebSocket takes its address from socket()
    ]
    assert not found, found
    assert 'export const BASE = ""' in (WEB / "lib" / "api.js").read_text(encoding="utf-8")
    assert TestClient(app).get("/lib/api.js").status_code == 200
