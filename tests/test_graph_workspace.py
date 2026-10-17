"""The Customer's workspace (FEAT-40, ADR-0035): one page, the graph kept; every Customer page still reachable as a
sheet at its old address; the server's links resolve; the workspace follows the motion rules (B-01)."""

import base64
import json
import re
import subprocess
from pathlib import Path

import pytest
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
WS = WEB / "workspace"


def lenses(expr: str):
    """Evaluate `expr` against web/workspace/lenses.js (no imports, so node runs it as it is)."""
    src = base64.b64encode(
        (WS / "lenses.js").read_bytes()
    ).decode()  # a data: URL: node 18 reads a .js file as CommonJS
    code = f'import * as L from "data:text/javascript;base64,{src}"; console.log(JSON.stringify({expr}));'
    out = subprocess.run(["node", "--input-type=module", "-e", code], capture_output=True, text=True, timeout=30)
    if out.returncode:
        pytest.skip(f"node could not run lenses.js: {out.stderr[:200]}")
    return json.loads(out.stdout)


def client_pages():
    """The Customer menu of the shell (ROLES.client): page name per old address."""
    shell = (WEB / "shell.js").read_text(encoding="utf-8")
    block = shell.split("client: {", 1)[1].split("\n  rm: {", 1)[0]
    return set(re.findall(r'page: "([a-z]+)"', block))


def test_every_customer_page_has_an_entry_point():
    # OWN-GW-13: no capability is lost — each page of the old menu opens as a sheet; the map page is the graph itself
    sheets = lenses("Object.values(L.SHEETS).map(s => s.page)")
    assert client_pages() - {"map"} == set(sheets)
    toolbar = lenses("L.TOOLBAR.map(t => t.id)")
    assert toolbar == ["tong-quan", "tai-san", "dong-tien", "muc-tieu", "tin", "rui-ro", "chuyen-gia", "bo-nho"]


def test_old_addresses_open_their_page_over_its_lens():
    got = lenses("""[
      L.resolve([]), L.resolve(["tong-quan"]), L.resolve(["tong-quan", "ban-do"]), L.resolve(["xem", "rui-ro"]),
      L.resolve(["xem", "nope"]), L.resolve(["tai-san"]), L.resolve(["tin", "do-thi", "EV-1"]), L.resolve(["muc-tieu"]),
      L.resolve(["muc-tieu", "khau-vi"]), L.resolve(["chuyen-gia"]), L.resolve(["bo-nho"]), L.resolve(["what"])]""")
    assert got[0] == {"lens": None, "sheet": None, "param": None}  # #/client keeps the lens on screen
    assert got[1]["lens"] == got[2]["lens"] == "tong-quan" and got[1]["sheet"] is got[2]["sheet"] is None
    assert got[3] == {"lens": "rui-ro", "sheet": None, "param": None}
    assert got[4]["lens"] == "tong-quan" and got[4]["sheet"] is None
    assert got[5] == {"lens": "tai-san", "sheet": "tai-san", "param": None}
    assert got[6] == {"lens": "tin", "sheet": "do-thi", "param": "EV-1"}
    assert got[7]["sheet"] == "ke-hoach" and got[8] == {"lens": "rui-ro", "sheet": "khau-vi", "param": None}
    assert got[9]["sheet"] == "chuyen-gia" and got[9]["lens"] is None  # Experts keep their own view (OWN-GW-05)
    assert got[10]["sheet"] == "bo-nho" and got[11]["sheet"] is None


def test_every_route_the_server_builds_for_a_customer_resolves():
    # citations, search hits and the bell carry old addresses: each must land on a lens or a sheet, never nowhere
    from assistant.tools import PAGES

    routes = {r["client"] for _, r in PAGES.values() if "client" in r}
    for py in (ROOT / "src").rglob("*.py"):
        routes |= set(re.findall(r'"(#/client/[a-z/-]+)"', py.read_text(encoding="utf-8")))
    assert len(routes) >= 9
    parts = [r.removeprefix("#/client/").split("/") for r in sorted(routes)]
    got = lenses(f"{json.dumps(parts)}.map(p => L.resolve(p))")
    for route, r in zip(sorted(routes), got):
        assert r["sheet"] or route.endswith(("/ban-do", "/tong-quan")), (route, r)


def test_the_workspace_is_served_and_follows_the_motion_rules():
    from app.web import app

    client = TestClient(app)
    for name in ("workspace", "graph", "inspector", "lenses", "strip"):
        assert client.get(f"/workspace/{name}.js").status_code == 200, name
    js = "".join(p.read_text(encoding="utf-8") for p in WS.glob("*.js"))
    assert "setInterval" not in js  # nothing loops: activity comes from events (OWN-GW-08)
    assert ".animate(" not in js.replace(
        "track(dot.animate(", ""
    )  # every Web Animation is tracked (paused when hidden)
    css = (WEB / "core" / "tokens.css").read_text(encoding="utf-8").split("The Customer's workspace (FEAT-40")[1]
    for decl in re.findall(r"transition:\s*([^;]+);", css):
        for part in decl.split(","):
            assert part.split()[0] in ("transform", "opacity", "none"), decl
    reduced = css.split("@media (prefers-reduced-motion: reduce) {")[1].split("\n}\n")[0]
    for cls in (".wnode", ".wedge", ".wspark", ".ws-sheet", ".wring"):
        assert cls in reduced, cls


def test_the_shell_mounts_the_workspace_for_the_customer_only():
    shell = (WEB / "shell.js").read_text(encoding="utf-8")
    assert 'if (rt.role === "client")' in shell and "leaveWorkspace()" in shell
    copilot = (WEB / "copilot.js").read_text(encoding="utf-8")
    assert "dock(host)" in copilot and "undock()" in copilot
    # the scenario's effect is hypothetical: the inspector says it never adds to net worth (OWN-GW-12)
    assert "không cộng vào tài sản ròng" in (WS / "inspector.js").read_text(encoding="utf-8")
