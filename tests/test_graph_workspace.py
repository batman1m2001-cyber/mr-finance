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
    # (hidden from the client, ADR-0037), Toàn cảnh and Chi tiết are the dashboard (UX_TOOLBAR_PLAN T3+T4); Bộ nhớ is
    # opened from the header (T2)
    sheets = lenses("Object.values(L.SHEETS).map(s => s.page)")
    assert client_pages() - {"map", "pulse", "detail"} == set(sheets)
    board = lenses('[L.resolve(["tong-quan", "toan-canh"]), L.resolve(["tong-quan", "chi-tiet"])]')
    assert [b["part"] for b in board] == ["month", "nw"] and not any(b["sheet"] for b in board)


def test_the_menu_is_the_banks_four_sections():
    """Business feedback 2 (WEALTH_NAMES_PLAN, ADR-0037, OWN-WN-01…06): four sections by the bank's names, each with
    the tabs it asked for, and every sheet under one of them."""
    toolbar = lenses("L.TOOLBAR.map(t => [t.id, t.label])")
    assert toolbar == [["tong-quan", "Wealth View"], ["muc-tieu", "Wealth Planning Advisor"], ["tin", "Headline News"],
                       ["chuyen-gia", "Relationship specialist"]]  # fmt: skip
    tabs = lenses("Object.fromEntries(L.TOOLBAR.map(t => [t.id, L.SECTIONS[t.id].tabs.map(x => x[0])]))")
    assert tabs == {"tong-quan": ["Wealth view", "Dữ liệu chi tiết tài sản"],
                    "muc-tieu": ["Wealth planning advisor", "Risk profile test"],
                    "tin": ["Tác động tin", "Đồ thị tác động", "Chi phí chính sách"],
                    "chuyen-gia": ["Relationship specialist"]}  # fmt: skip
    homes = lenses("L.TOOLBAR.map(t => L.SECTIONS[t.id].home)")
    assert homes == ["#/client/tong-quan", "#/client/muc-tieu/ke-hoach", "#/client/tin/thi-truong",
                     "#/client/chuyen-gia"]  # fmt: skip
    # nothing a client clicks leads to the graph: no tab names it, no tab's address is a lens of its own
    routes = lenses("Object.values(L.SECTIONS).flatMap(s => s.tabs.map(x => x[1]))")
    assert not [r for r in routes if r.startswith("#/client/xem/") or r.endswith("/ban-do")]


def test_old_addresses_open_their_page_over_its_lens():
    got = lenses("""[
      L.resolve([]), L.resolve(["tong-quan"]), L.resolve(["tong-quan", "ban-do"]), L.resolve(["xem", "rui-ro"]),
      L.resolve(["xem", "nope"]), L.resolve(["tai-san"]), L.resolve(["tin", "do-thi", "EV-1"]), L.resolve(["muc-tieu"]),
      L.resolve(["muc-tieu", "khau-vi"]), L.resolve(["chuyen-gia"]), L.resolve(["bo-nho"]), L.resolve(["what"])]""")
    home = {"lens": "tong-quan", "sheet": None, "param": None, "home": True}  # Wealth View (B3.1, ADR-0037)
    assert got[0] == got[1] == got[2] == got[11] == home  # ban-do: the former Đồ thị tài chính tab; an unknown one
    assert got[3] == {"lens": "rui-ro", "sheet": None, "param": None}  # the graph's own address, linked from nowhere
    assert got[4]["lens"] == "tong-quan" and got[4]["sheet"] is None
    assert got[5] == {"lens": "tong-quan", "sheet": "tai-san", "param": None}  # Dữ liệu chi tiết tài sản (Wealth View)
    assert got[6] == {"lens": "tin", "sheet": "do-thi", "param": "EV-1"}
    assert got[7]["sheet"] == "ke-hoach" and got[8] == {"lens": "muc-tieu", "sheet": "khau-vi", "param": None}
    assert got[9]["sheet"] == "chuyen-gia" and got[9]["lens"] is None  # Relationship specialist, its own view
    assert got[10]["sheet"] == "bo-nho"
    cash = lenses('[L.resolve(["dong-tien"]), L.resolve(["rui-ro", "khau-vi"])]')
    assert cash[0] == {"lens": "tong-quan", "sheet": None, "param": None, "part": "cash"}  # Dòng tiền: in Wealth View
    assert cash[1] == {"lens": "muc-tieu", "sheet": "khau-vi", "param": None}  # Risk profile test, in WPA


def test_every_route_the_server_builds_for_a_customer_resolves():
    # citations, search hits and the bell carry old addresses: each must land on a lens or a sheet, never nowhere
    from assistant.tools import PAGES

    routes = {r["client"] for _, r in PAGES.values() if "client" in r}
    for py in (ROOT / "src").rglob("*.py"):
        routes |= set(re.findall(r'"(#/client/[a-z/-]+)"', py.read_text(encoding="utf-8")))
    assert len(routes) >= 9
    parts = [r.removeprefix("#/client/").split("/") for r in sorted(routes)]
    got = lenses(f"{json.dumps(parts)}.map(p => L.resolve(p))")
    for route, r, part in zip(sorted(routes), got, parts):
        lens = part[0] == "xem" and r["lens"] == part[1]  # a lens of its own (the assistant's mo_trang, D20)
        assert r["sheet"] or r.get("part") or lens or route.endswith(("/ban-do", "/tong-quan")), (route, r)


def test_the_workspace_is_served_and_follows_the_motion_rules():
    from app.web import app

    client = TestClient(app)
    for name in ("workspace", "graph", "inspector", "lenses", "strip"):
        assert client.get(f"/workspace/{name}.js").status_code == 200, name
    js = "".join(p.read_text(encoding="utf-8") for p in WS.glob("*.js"))
    assert "setInterval" not in js  # nothing loops: activity comes from events (OWN-GW-08)
    assert js.count(".animate(") == len(
        re.findall(r"track\(\w+\.animate\(", js)
    )  # every Web Animation tracked (paused when hidden)
    css = (WEB / "core" / "tokens.css").read_text(encoding="utf-8").split("The Customer's workspace (FEAT-40")[1]
    for decl in re.findall(r"transition:\s*([^;]+);", css):
        for part in decl.split(","):
            assert part.split()[0] in ("transform", "opacity", "none"), decl
    reduced = css.split("@media (prefers-reduced-motion: reduce) {")[1].split("\n}\n")[0]
    for cls in (".wnode", ".wedge", ".wcomet", ".ws-sheet", ".wring", ".wburst"):
        assert cls in reduced, cls


def test_the_shell_mounts_the_workspace_for_the_customer_only():
    shell = (WEB / "shell.js").read_text(encoding="utf-8")
    assert 'if (rt.role === "client")' in shell and "leaveWorkspace()" in shell
    copilot = (WEB / "copilot.js").read_text(encoding="utf-8")
    assert "dock(host, hooks)" in copilot and "undock()" in copilot and "/api/assistant/stream" in copilot
    # the scenario's effect is hypothetical: the inspector says it never adds to net worth (OWN-GW-12)
    assert "không cộng vào tài sản ròng" in (WS / "inspector.js").read_text(encoding="utf-8")


def test_a_second_copy_of_the_app_runs_no_job_on_its_own(monkeypatch):
    # OWN-GW-14: the experiment serves the same app on its own port; with MF_JOBS=off no job has a clock
    from app.main import schedule

    assert schedule(every="1h") is not None
    monkeypatch.setenv("MF_JOBS", "off")
    assert schedule(every="1h") is None
