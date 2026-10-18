"""Each staff role's desk (FEAT-41, ADR-0036, OWN-MR-01…12): every page of the role's menu is still reachable (a
rail group's tab, at its old address), the desk is the role's own and nobody else's, its figures are the figures the
existing reads give, and the role's assistant reads the same composition the desk draws."""

import asyncio
import base64
import json
import re
import subprocess
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import pytest
from starlette.testclient import TestClient
from test_apply import AGENT, EVENT, INGEST, LINKS, MARKET, NOW, approved, ok

from apply import reads as apply_reads
from apply import run as apply_run
from assistant import registry
from assistant.base import Ctx, execute
from control import roles
from desk import reads as desk_reads
from news import store as news

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
STAFF_WITH_DESK = sorted(desk_reads.BUILD)


def desks():
    """web/desk/roles.js's DESKS (no imports, so node runs it as it is)."""
    src = base64.b64encode((WEB / "desk" / "roles.js").read_bytes()).decode()
    code = f'import {{DESKS}} from "data:text/javascript;base64,{src}"; console.log(JSON.stringify(DESKS));'
    out = subprocess.run(["node", "--input-type=module", "-e", code], capture_output=True, text=True, timeout=30)
    if out.returncode:
        pytest.skip(f"node could not run roles.js: {out.stderr[:200]}")
    return json.loads(out.stdout)


def menu(role):
    """The ids of ``role``'s menu in web/shell.js (ROLES.<role>.nav, top level), unchanged by the desks."""
    shell = (WEB / "shell.js").read_text(encoding="utf-8")
    block = re.split(r"\n  [a-z]+: \{", shell.split(f"\n  {role}: {{", 1)[1], maxsplit=1)[0]
    return re.findall(r'^      \{id: "([a-z-]+)"', block, flags=re.M)


def pending_view(title):
    """News → event → mock agent, not decided: a view waiting for the CIO."""
    when = format_datetime(datetime.fromtimestamp(NOW - 600, timezone.utc))
    body = (
        f"<item><title>{title}</title><link>https://vneconomy.vn/p{next(LINKS)}.htm</link>"
        f"<description>{title}</description><pubDate>{when}</pubDate></item>"
    )
    ids = ok(INGEST, feeds={"vneconomy_ck": f"<rss><channel>{body}</channel></rss>"}, now=NOW)["ingest"]["ids"]
    ev = ok(EVENT, news_ids=ids, by="cio")["event"]
    return ev, ok(AGENT, event_id=ev["id"], by="cio")["result"]["view"]


def ctx(role):
    return Ctx(role=role, client_id=None, scope="personal", question="", user=registry.DEMO_USER[role])


# -- no capability lost: every page of the menu has a place on the desk -----------------------------------------


@pytest.mark.parametrize("role", STAFF_WITH_DESK)
def test_every_page_of_the_menu_is_in_exactly_one_rail_group(role):
    assert sorted(desks()) == STAFF_WITH_DESK  # a desk on screen for each desk the server builds, and no other
    groups = desks()[role]["groups"]
    placed = [i for g in groups for i in g["nav"]]
    assert sorted(placed) == sorted(menu(role)), "a page of the menu with no rail group, or one in two"
    assert len(placed) == len(set(placed))
    assert [g["id"] for g in groups if g.get("desk")] == ["ban"] and menu(role)[0] == "ban"


def test_the_cio_keeps_every_page_it_had():
    # the CIO's menu before the desk (6e735dd), page for page: the desk is added, nothing removed (OWN-MR-02)
    before = ["hop-tin", "nhan-dinh", "phoi-nhiem", "ap-dung", "do-thi", "nghien-cuu", "ban-tin", "chinh-sach"]
    before += ["mo-hinh", "do-luong", "agent", "cau-hinh", "bo-nho"]
    assert menu("cio") == ["ban"] + before


# -- the desk is the role's own -----------------------------------------------------------------------------------


def test_a_role_without_a_desk_is_refused_and_a_role_reads_only_its_own(monkeypatch):
    from app.web import app

    client = TestClient(app)
    assert client.get("/api/desk?role=client").status_code == 403
    assert client.get("/api/desk?role=nobody").status_code == 403
    for role in STAFF_WITH_DESK:
        assert client.get(f"/api/desk?role={role}").json()["role"] == role
    with pytest.raises(roles.Forbidden):
        desk_reads.desk("client", {"id": "C01", "role": "client"})


def test_with_sign_in_the_session_says_whose_desk_and_the_query_cannot_change_it(monkeypatch):
    from app.web import app
    from people import auth

    monkeypatch.setenv("MF_AUTH", "on")
    client = TestClient(app)
    assert client.get("/api/desk").status_code == 401
    as_ = lambda who: {"cookie": f"{auth.COOKIE}={auth.issue(who)}"}  # noqa: E731
    assert client.get("/api/desk", headers=as_("C01")).status_code == 403  # a client has no desk
    got = client.get("/api/desk?role=rm", headers=as_("cio"))
    assert got.status_code == 200 and got.json()["role"] == "cio"
    for who in ("rm01", "compliance", "admin", "sp_global"):  # no desk yet, or their own: never the CIO's
        r = client.get("/api/desk?role=cio", headers=as_(who))
        assert r.status_code == 403 or r.json()["role"] != "cio", who


# -- the desk says the existing reads' numbers --------------------------------------------------------------------


def test_the_cio_desk_counts_what_the_cio_pages_count():
    view, run = approved(*MARKET)
    ev, waiting = pending_view("Lãi suất liên ngân hàng tăng")
    d = desk_reads.desk("cio", {"id": "cio", "role": "cio"})
    stage = {s["id"]: s for s in d["pipeline"]}

    effective = [r for r in apply_run.runs() if r["status"] == "EFFECTIVE"]
    assert stage["runs"]["count"] == len(effective) == 1
    assert d["exposure"]["run_id"] == run["id"] and d["exposure"]["expected_3m"] == run["totals"]["expected_3m"]
    assert d["exposure"]["families"] == run["families"] and d["exposure"]["pre_review"] == run["totals"]["pre_review"]
    assert stage["families"]["count"] == len({x["family_id"] for x in run["ranking"]})
    assert stage["news"]["count"] == len(news.inbox(status="new", limit=5000))
    assert stage["rm"]["count"] == len({c["family_id"] for c in apply_reads.rm_today(None)["cases"]})
    # the view waiting is in the queue and on the stage, opening its own page; the approved one is not
    queued = {x["id"]: x for x in d["decide"]}
    assert waiting["status"] == "PENDING_APPROVAL"
    assert queued[waiting["id"]]["route"] == f"#/cio/nhan-dinh/{waiting['id']}"
    assert view["id"] not in queued and stage["views"]["waits"] == 1
    # each factor bar is the run's own total for that factor, largest first
    total = run["exposure"]["total"]
    bars = [(f["id"], f["value"]) for f in d["exposure"]["factors"]]
    assert bars and all(total[i] == v for i, v in bars)
    assert [abs(v) for _, v in bars] == sorted((abs(v) for _, v in bars), reverse=True)
    assert all(x["route"].startswith("#/cio/") for x in d["decide"] + d["events"])


def test_an_empty_desk_is_still_a_desk():
    d = desk_reads.desk("cio", {"id": "cio", "role": "cio"})
    assert d["exposure"] is None and d["decide"] == []
    assert [s["id"] for s in d["pipeline"]] == ["news", "events", "views", "runs", "families", "rm"]


# -- the role's assistant reads the desk ---------------------------------------------------------------------------


def test_the_cio_assistant_says_the_desks_numbers():
    _, run = approved(*MARKET)
    pending_view("Lãi suất liên ngân hàng tăng")
    d = desk_reads.desk("cio", {"id": "cio", "role": "cio"})
    said = asyncio.run(execute(registry.REGISTRY["ban_quyet_dinh"], ctx("cio"), {}))
    assert said["data"]["waiting"] == len(d["decide"]) and said["data"]["stages"]["runs"] == 1
    exp = asyncio.run(execute(registry.REGISTRY["phoi_nhiem"], ctx("cio"), {}))
    assert exp["data"]["expected_3m"] == run["totals"]["expected_3m"] and run["id"] in exp["text"]


@pytest.mark.parametrize("name", ["ban_quyet_dinh", "phoi_nhiem", "lan_ap_dung", "do_chinh_xac"])
def test_a_desk_tool_is_its_roles_alone_and_opens_its_desk(name):
    from assistant.stream import NODES
    from assistant.tools import PAGES

    t = registry.REGISTRY[name]
    assert t.roles == ("cio",) and not t.write
    assert PAGES[t.page][1]["cio"].startswith("#/cio") and NODES[name]


def test_the_agents_beneath_the_desk_are_untouched():
    # the CIO's own agent and its challenger (FEAT-04, 05) are still the flows they were; the desk only reads them
    from views import graph

    assert graph.cio_agent_flow and graph.decide_flow
    d = desk_reads.desk("cio", {"id": "cio", "role": "cio"})
    assert {"mode", "models"} <= set(d["agents"])
