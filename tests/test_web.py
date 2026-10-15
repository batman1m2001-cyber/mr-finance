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
    client = TestClient(app)
    for page in pages:
        assert (WEB / "pages" / f"{page}.js").is_file(), page
        assert client.get(f"/pages/{page}.js").status_code == 200
    for asset in ("/", "/shell.js", "/core/core.js", "/core/tokens.css", "/charts/charts.js", "/pages/trace.js"):
        assert client.get(asset).status_code == 200, asset


def test_the_legacy_pages_keep_their_sections():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    shell = (WEB / "shell.js").read_text(encoding="utf-8")
    for tab in set(re.findall(r'legacy: "([a-z]+)"', shell)):
        assert f'id="tab-{tab}"' in html, tab
    assert "không phải cơ chế bảo mật" in html  # the role switcher says it is a demo
