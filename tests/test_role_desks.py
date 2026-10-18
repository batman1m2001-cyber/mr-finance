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


def test_the_rm_keeps_every_page_it_had():
    # the RM's menu before the desk, page for page; the ten client pages stay under Khách hàng
    assert menu("rm") == ["ban", "hom-nay", "khach-hang", "hieu-qua", "bo-nho"]
    shell = (WEB / "shell.js").read_text(encoding="utf-8")
    block = shell.split('{id: "khach-hang", label: "Khách hàng", clientPick: true, sub: [', 1)[1].split("]}", 1)[0]
    pages = ["tac-dong", "do-thi", "toan-canh", "ban-do", "tong-quan", "tai-san", "ke-hoach", "chinh-sach", "hieu-qua"]
    assert re.findall(r'id: "([a-z-]+)"', block) == pages + ["duyet"]


def test_the_specialist_keeps_every_page_it_had():
    assert menu("specialist") == ["ban", "duyet", "bo-nho"]


def test_admin_keeps_every_page_it_had():
    assert menu("admin") == ["ban", "he-thong", "du-lieu", "cau-hinh", "agent", "nhat-ky", "bo-nho"]


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
    rm = client.get("/api/desk?role=cio", headers=as_("rm01")).json()
    assert rm["role"] == "rm" and sorted(f["id"] for f in rm["families"]) == ["C01", "C04", "C05"]
    assert [f["id"] for f in client.get("/api/desk", headers=as_("rm03")).json()["families"]] == ["C03"]
    assert client.get("/api/desk?role=cio", headers=as_("admin")).json()["role"] == "admin"
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


def test_the_rm_desk_is_hom_nay_the_queue_and_the_contacts_of_the_rms_own_families():
    from wealth import store as reviews

    _, run = approved(*MARKET)
    flagged = {x["family_id"] for x in run["ranking"] if x["pre_review"]}
    waiting = reviews.propose("C01", "plan", "Kế hoạch học phí", {})
    reviews.propose("C03", "plan", "Không phải của rm01", {})
    note = reviews.propose("C01", "rm_note", "Ghi chú của RM", {})  # the RM's own note: not theirs to approve
    for who in ("rm01", "rm03"):
        book = sorted(desk_reads._book({"id": who, "role": "rm"}))
        d = desk_reads.desk("rm", {"id": who, "role": "rm", "families": book})
        today = apply_reads.rm_today(book)
        assert sorted(f["id"] for f in d["families"]) == book
        assert {c["family_id"] for c in d["calls"]} == {c["family_id"] for c in today["cases"]} == flagged & set(book)
        assert [c["p10_3m_pct"] for c in d["calls"]] == sorted(c["p10_3m_pct"] for c in d["calls"])  # worst first
        for f in d["families"]:
            assert f["level"] == max([w["level"] for w in f["why"]], default=0)
            assert (f["level"] == 3) == (f["id"] in flagged)  # no goal task here: only the threshold calls now
            row = next(x for x in run["ranking"] if x["family_id"] == f["id"])
            assert f["net_worth"] == row["net_worth"] and f["net_worth_run"] == run["id"]
        ids = {x["id"] for x in d["proposals"]}
        assert (waiting in ids) == (who == "rm01") and note not in ids
        assert all(x["family_id"] in book for x in d["proposals"])
    d = desk_reads.desk("rm", {"id": "rm01", "role": "rm", "families": ["C01", "C04", "C05"]})
    c01 = next(f for f in d["families"] if f["id"] == "C01")
    assert c01["proposals"] == 1 and c01["level"] >= 2 and "1 đề xuất chờ bạn duyệt" in [w["text"] for w in c01["why"]]


def test_without_sign_in_the_rm_desk_is_every_family_as_hom_nay_is():
    d = desk_reads.desk("rm", None)
    from wealth import fixtures

    assert [f["id"] for f in sorted(d["families"], key=lambda f: f["id"])] == fixtures.client_ids()


# -- the role's assistant reads the desk ---------------------------------------------------------------------------


def test_the_cio_assistant_says_the_desks_numbers():
    _, run = approved(*MARKET)
    pending_view("Lãi suất liên ngân hàng tăng")
    d = desk_reads.desk("cio", {"id": "cio", "role": "cio"})
    said = asyncio.run(execute(registry.REGISTRY["ban_quyet_dinh"], ctx("cio"), {}))
    assert said["data"]["waiting"] == len(d["decide"]) and said["data"]["stages"]["runs"] == 1
    exp = asyncio.run(execute(registry.REGISTRY["phoi_nhiem"], ctx("cio"), {}))
    assert exp["data"]["expected_3m"] == run["totals"]["expected_3m"] and run["id"] in exp["text"]


DESK_TOOLS = {"ban_quyet_dinh": ("cio",), "phoi_nhiem": ("cio",), "lan_ap_dung": ("cio",), "do_chinh_xac": ("cio",),
              "so_khach_hang": ("rm",), "van_hanh": ("admin",), "chuoi_nhat_ky": ("admin", "compliance"),
              "cau_hinh_cho_duyet": ("admin", "compliance"), "ban_chuyen_gia": ("specialist",),
              "ho_so_khach": ("specialist",)}  # fmt: skip


@pytest.mark.parametrize("name", sorted(DESK_TOOLS))
def test_a_desk_tool_is_its_roles_alone_and_opens_its_desk(name):
    from assistant.stream import NODES
    from assistant.tools import PAGES

    t = registry.REGISTRY[name]
    assert t.roles == DESK_TOOLS[name] and not t.write
    assert all(PAGES[t.page][1][r].startswith(f"#/{r}") for r in t.roles) and NODES[name]


def test_the_rm_assistant_says_the_books_numbers():
    from wealth import store as reviews

    approved(*MARKET)
    reviews.propose("C01", "plan", "Kế hoạch học phí", {})
    d = desk_reads.desk("rm", {"id": "rm01", "role": "rm"})
    said = asyncio.run(execute(registry.REGISTRY["so_khach_hang"], ctx("rm"), {}))
    soon = [f for f in d["families"] if f["level"] >= 2]
    assert said["data"] == {"families": len(d["families"]), "soon": len(soon), "proposals": len(d["proposals"]),
                            "tasks": len(d["tasks"])}  # fmt: skip
    assert {f"family:{f['id']}" for f in soon} <= set(said["focus"]) and "C03" not in said["text"]


def test_the_agents_beneath_the_desk_are_untouched():
    # the CIO's own agent and its challenger (FEAT-04, 05) are still the flows they were; the desk only reads them
    from views import graph

    assert graph.cio_agent_flow and graph.decide_flow
    d = desk_reads.desk("cio", {"id": "cio", "role": "cio"})
    assert {"mode", "models"} <= set(d["agents"])


# -- Admin · Vận hành (M3) -------------------------------------------------------------------------------------------


def test_the_admin_desk_is_he_thongs_own_read():
    from app.web import system_read
    from control import config

    config.propose("thresholds", {**config.data("thresholds"), "pre_review_pct": -0.07}, "cio2", "thử")
    s, d = system_read(), desk_reads.desk("admin", {"id": "admin", "role": "admin"})
    node = {n["id"]: n for n in d["nodes"]}
    lanes = ["sources", "store", "ai", "people"]  # left to right: where data comes from to who works on it
    assert [n["lane"] for n in d["nodes"]] == sorted((n["lane"] for n in d["nodes"]), key=lanes.index)
    assert (
        node["chain"]["value"] == f"{s['chain']['count']} dòng" and node["chain"]["state"] == "ok" and d["chain"]["ok"]
    )
    assert [c["id"] for c in d["config"]] == [c["id"] for c in s["config_waiting"]] and len(d["config"]) == 1
    assert d["config"][0]["by"] == "cio2" and node["config"]["state"] == "warn"
    assert sum(d["roles"].values()) == len(s["people"]) and d["clients"] == s["clients"]
    assert d["failing"] == [] and all(n["state"] in ("ok", "warn", "idle", "bad") for n in d["nodes"])
    assert all(n["route"].startswith("#/admin/") for n in d["nodes"])


def test_a_failing_feed_and_a_broken_chain_turn_their_nodes_red(monkeypatch):
    from app import web

    real = web.system_read

    def broken():
        s = real()
        s["feeds"] = [{"id": "vnexpress_kd", "error": "HTTP 503", "accepted": 0}, {"id": "fed", "error": None}]
        s["chain"] = {**s["chain"], "ok": False, "broken_at": 7, "reason": "băm không khớp"}
        return s

    monkeypatch.setattr(web, "system_read", broken)
    node = {n["id"]: n for n in desk_reads.desk("admin", None)["nodes"]}
    assert (
        node["feeds"]["state"] == "bad"
        and "HTTP 503" in node["feeds"]["error"]
        and node["feeds"]["value"] == "1/2 nguồn"
    )
    assert node["chain"]["state"] == "bad" and node["chain"]["error"] == "băm không khớp"
    said = asyncio.run(execute(registry.REGISTRY["van_hanh"], ctx("admin"), {}))
    assert said["data"]["off"] >= 2 and "node:feeds" in said["focus"] and "HTTP 503" in said["text"]


def test_the_chain_and_the_configuration_tools_read_what_their_pages_read():
    from control import audit, config, db

    with db.tx() as con:
        count = audit.verify(con)["count"]
    for role in ("admin", "compliance"):
        got = asyncio.run(execute(registry.REGISTRY["chuoi_nhat_ky"], ctx(role), {}))
        assert got["data"]["ok"] and got["data"]["count"] >= count
    assert asyncio.run(execute(registry.REGISTRY["cau_hinh_cho_duyet"], ctx("admin"), {}))["data"]["waiting"] == 0
    config.propose("thresholds", {**config.data("thresholds"), "pre_review_pct": -0.07}, "cio2", "thử")
    got = asyncio.run(execute(registry.REGISTRY["cau_hinh_cho_duyet"], ctx("compliance"), {}))
    assert got["data"]["waiting"] == 1 and "cio2" in got["text"]


# -- Expert · Bàn chuyên gia (M4) --------------------------------------------------------------------------------------


def recommendation(cid, title, by="rm01"):
    """An RM's recommendation for ``cid``, stored as the RM's write stores it: it waits for a certified specialist."""
    from review import specialist
    from wealth import store as reviews

    item = reviews.propose(
        cid, "rm_note", title, {"option": {"title": title, "actions": ["Bán bớt cổ phiếu"]}, "author": by}
    )
    return reviews.decide(item, "pending_specialist" if specialist.approvers(cid) else "approved", "Khách đồng ý.", by)


def page_waiting(client, who):
    """What Duyệt khuyến nghị lists as waiting for ``who`` (web/pages/specialist.js over GET /api/review)."""
    q = client.get("/api/review", headers=who).json()
    me = q["certificate"] and next(
        a["id"] for a in sum(q["approvers"].values(), []) if a["certificate"] == q["certificate"]["certificate"]
    )
    mine = {c for c, a in q["approvers"].items() if any(x["id"] == me for x in a)}
    return sorted(x["id"] for x in q["items"] if x["status"] == "pending_specialist" and x["family_id"] in mine)


def test_the_expert_desk_is_what_duyet_khuyen_nghi_lists_for_each_specialist(monkeypatch):
    from app.web import app
    from people import auth
    from people import store as people

    c01, c04 = recommendation("C01", "Giảm cổ phiếu ngân hàng"), recommendation("C04", "Mua bảo hiểm sức khoẻ")
    assert c01["status"] == c04["status"] == "pending_specialist"
    monkeypatch.setenv("MF_AUTH", "on")
    client = TestClient(app)
    for who in ("sp_global", "sp_real_estate", "sp_insurance", "sp_banking", "sp_private"):
        h = {"cookie": f"{auth.COOKIE}={auth.issue(who)}"}
        d = client.get("/api/desk?role=cio", headers=h).json()
        assert d["role"] == "specialist" and d["me"] == who
        assert [f["id"] for f in d["families"]] == people.families_of_specialist(who), who  # their families alone
        assert sorted(x["id"] for x in d["waiting"]) == (page_waiting(client, h) if d["certificate"] else []), who
    h = lambda who: {"cookie": f"{auth.COOKIE}={auth.issue(who)}"}  # noqa: E731
    ins = client.get("/api/desk", headers=h("sp_insurance")).json()
    assert [x["id"] for x in ins["waiting"]] == [c01["id"], c04["id"]]  # oldest first
    assert ins["waiting"][0]["rm"] == "rm01" and ins["waiting"][0]["rm_note"] == "Khách đồng ý."
    assert [x["id"] for x in client.get("/api/desk", headers=h("sp_private")).json()["waiting"]] == [c04["id"]]
    # assigned to C01 but no certificate in force: the family is theirs to read, not to decide (BRD-RULE-ROLE-05)
    re_ = client.get("/api/desk", headers=h("sp_real_estate")).json()
    assert re_["certificate"] is None and re_["waiting"] == [] and not any(f["approves"] for f in re_["families"])


def test_without_sign_in_the_expert_desk_is_the_page_users(monkeypatch):
    from app.web import app

    recommendation("C01", "Giảm cổ phiếu ngân hàng")
    client = TestClient(app)
    d = client.get("/api/desk?role=specialist&user=sp_global").json()
    assert d["me"] == "sp_global" and d["certificate"] and len(d["waiting"]) == 1
    anyone = client.get("/api/desk?role=specialist").json()
    assert anyone["me"] is None and anyone["certificate"] is None and anyone["waiting"] == []


def test_a_decision_on_the_desk_is_the_existing_write_and_moves_the_item(monkeypatch):
    from operonx.app import Application

    from people import auth

    item = recommendation("C01", "Giảm cổ phiếu ngân hàng")
    monkeypatch.setenv("MF_AUTH", "on")
    h = {"cookie": f"{auth.COOKIE}={auth.issue('sp_global')}"}
    say = lambda decision, note: {"item_id": item["id"], "decision": decision, "note": note, "by": "sp_global"}  # noqa: E731
    with TestClient(Application.find(str(ROOT)).asgi()) as client:  # the served app: the write is a served flow
        short = client.post("/api/review/specialist", json=say("rejected", "ngắn"), headers=h)
        assert short.status_code >= 400 and "10" in short.text  # the note rule, unchanged
        assert (
            client.post("/api/review/specialist", json=say("approved", ""), headers=h).json()["item"]["status"]
            == "approved"
        )
        d = client.get("/api/desk", headers=h).json()
    assert d["waiting"] == [] and [(x["id"], x["status"]) for x in d["decided"]] == [(item["id"], "approved")]


def test_the_expert_assistant_says_the_queue_and_reads_only_an_assigned_family():
    from assistant.base import ToolFailed

    item = recommendation("C01", "Giảm cổ phiếu ngân hàng")
    d = desk_reads.desk("specialist", {"id": "sp_global", "role": "specialist"})
    said = asyncio.run(execute(registry.REGISTRY["ban_chuyen_gia"], ctx("specialist"), {}))
    assert said["data"] == {"waiting": len(d["waiting"]), "certified": True, "families": ["C01", "C03"]}
    assert item["id"] in said["text"] and d["certificate"]["certificate"] in said["text"]
    one = asyncio.run(execute(registry.REGISTRY["ho_so_khach"], ctx("specialist"), {}))  # one family waits: C01
    assert one["data"] == {"family": "C01"} and "C01" in one["text"]
    with pytest.raises(ToolFailed):  # C02 is not sp_global's
        asyncio.run(execute(registry.REGISTRY["ho_so_khach"], ctx("specialist"), {"gia_dinh": "C02"}))
