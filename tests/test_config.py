"""Versioned, owned configuration (BRD FR-701, §13.1 with F14, ADR-0016): propose, then approve."""

import pytest
from operonx.app import Application
from starlette.testclient import TestClient
from test_apply import MARKET, approved
from test_news import NOW, feed, ingest, rfc

from apply import run as runs
from control import audit, config, db, roles
from engine import default_model
from news import store


def test_a_proposal_changes_nothing_until_a_second_owner_approves_it():
    new = {**config.THRESHOLDS, "pre_review_pct": -0.01}
    v = config.propose("thresholds", new, "cio", "Hạ ngưỡng xem trước")
    assert v["status"] == "PROPOSED" and v["version"] == 2
    assert config.data("thresholds") == config.THRESHOLDS  # still the version in force
    with pytest.raises(roles.Forbidden, match="người thứ hai"):
        config.decide(v["id"], "approve", "cio")  # §13.1 / F14: not by the proposer
    with pytest.raises(roles.Forbidden):
        config.decide(v["id"], "approve", "rm01")  # not the owner's role
    done = config.decide(v["id"], "approve", "cio2")
    assert done["status"] == "ACTIVE" and done["decided_by"] == "cio2"
    assert config.data("thresholds")["pre_review_pct"] == -0.01
    assert [x["status"] for x in config.versions("thresholds")] == ["ACTIVE", "SUPERSEDED"]
    with db.tx() as con:
        actions = [r["action"] for r in con.execute("select action from audit_log order by seq")]
        assert actions[-2:] == ["config.propose", "config.approve"] and audit.verify(con)["ok"]


def test_wrong_owner_wrong_content_and_a_second_pending_are_refused():
    with pytest.raises(roles.Forbidden):
        config.propose("restricted", [{"name": "X", "ticker": "X", "aliases": []}], "cio")  # Compliance owns it
    with pytest.raises(ValueError):
        config.propose("thresholds", {"pre_review_pct": 0.3}, "cio")
    with pytest.raises(ValueError, match="giống"):
        config.propose("thresholds", dict(config.THRESHOLDS), "cio")
    config.propose("thresholds", {**config.THRESHOLDS, "modelled_share": 0.6}, "cio")
    with pytest.raises(ValueError, match="đang chờ"):
        config.propose("thresholds", {**config.THRESHOLDS, "modelled_share": 0.7}, "cio2")


def test_one_person_kinds_and_rejection():
    sources = config.data("news_sources")
    v = config.propose("news_sources", sources[:-1], "admin", "Bỏ một nguồn")
    assert config.decide(v["id"], "approve", "admin")["status"] == "ACTIVE"  # Admin, two-person: no
    assert len(config.data("news_sources")) == len(sources) - 1
    r = config.propose("restricted", config.data("restricted")[:1], "compliance")
    assert config.decide(r["id"], "reject", "compliance2", "Chưa đủ căn cứ")["status"] == "REJECTED"
    assert len(config.data("restricted")) == 3


def test_the_restricted_list_in_force_holds_the_news():
    rows = config.data("restricted") + [
        {"name": "Hưng Thịnh Phát (mock)", "ticker": "HTP", "aliases": ["hưng thịnh phát"]}
    ]
    v = config.propose("restricted", rows, "compliance", "Thêm HTP")
    config.decide(v["id"], "approve", "compliance2")
    out = ingest(
        {"vneconomy_tc": feed(("Hưng Thịnh Phát chậm trả nợ", "https://vneconomy.vn/htp.htm", "", rfc(NOW - 60)))}
    )
    assert out["held"] == 1 and store.inbox()[0]["restricted"] == ["Hưng Thịnh Phát (mock)"]


def test_a_run_freezes_the_thresholds_and_the_model_in_force():
    _, before = approved(*MARKET)
    snap = runs.snapshot(before["snapshot_id"])
    assert snap["thresholds"] == config.THRESHOLDS
    v = config.propose("thresholds", {**config.THRESHOLDS, "pre_review_pct": -0.001}, "cio")
    config.decide(v["id"], "approve", "cio2")
    assert runs.verify(before["id"])["ok"]  # the old run recomputes with its own thresholds
    _, after = approved("Lãi suất điều hành tăng mạnh", "Ngân hàng nhà nước tăng lãi suất")
    fams = runs.family_results(after["id"])
    assert runs.snapshot(after["snapshot_id"])["thresholds"]["pre_review_pct"] == -0.001
    assert all(
        r["pre_review"] == (r["net_worth"] > 0 and r["horizons"]["3m"]["p10"] <= -0.001 * r["net_worth"])
        for r in fams.values()
    )
    m0 = default_model()
    data = config.data("factor_model")
    data["version"] = data.get("version", "") + "-cio"
    fm = config.propose("factor_model", data, "cio", "Đổi nhãn phiên bản")
    config.decide(fm["id"], "approve", "cio2")
    assert default_model() is not m0 and default_model().hash != m0.hash


def test_the_demo_reset_returns_to_the_shipped_files():
    v = config.propose("thresholds", {**config.THRESHOLDS, "modelled_share": 0.9}, "cio")
    config.decide(v["id"], "approve", "cio2")
    db.reset()
    assert config.data("thresholds") == config.THRESHOLDS and config.active("thresholds")["version"] == 1


def test_the_endpoints():
    with TestClient(Application.find(".").asgi()) as c:
        kinds = c.get("/api/config").json()["kinds"]
        assert [k["kind"] for k in kinds] == [
            "factor_model",
            "thresholds",
            "return_assumptions",
            "restricted",
            "forbidden_phrases",
            "consent",
            "related_parties",
            "news_sources",
            "price_sources",
            "ticker_map",
            "rm_assignment",
            "certifications",
            "control_group",
            "assistant_retention",
            "ai_mode",
            "client_ai",
            "prompts",
            "models",
        ]
        r = c.post(
            "/api/config/propose",
            json={"kind": "thresholds", "data": {**config.THRESHOLDS, "concentration_share": 0.5}, "by": "cio"},
        )
        vid = r.json()["version"]["id"]
        assert (
            c.post("/api/config/decide", json={"version_id": vid, "action": "approve", "by": "cio"}).status_code != 200
        )
        ok = c.post("/api/config/decide", json={"version_id": vid, "action": "approve", "by": "cio2"})
        assert ok.status_code == 200 and ok.json()["version"]["status"] == "ACTIVE"
        assert c.get(f"/api/config/{vid}").json()["data"]["concentration_share"] == 0.5
