"""Application runs (src/apply) and the audit chain (src/control/audit): an approved view applied to
every family, reproducible to the dong, post-checked, ranked, traceable, withdrawable."""

import asyncio
import json
import sqlite3
from datetime import datetime, timezone
from email.utils import format_datetime

import pytest
from operonx import Operon
from operonx.app import Application
from starlette.testclient import TestClient

from apply import reads, trace
from apply import run as runs
from apply.graph import recompute_flow, run_decide_flow
from control import audit, crypto, db
from events.graph import event_flow
from news.graph import ingest_flow
from views.graph import cio_agent_flow, decide_flow
from wealth import fixtures

NOW = 1_792_000_000.0
LINKS = iter(range(10**6))
INGEST = Operon(ingest_flow, params={"feeds": None, "now": None, "tick": None, "at": None})
EVENT = Operon(event_flow, params={"news_ids": None, "title": None, "by": None})
AGENT = Operon(cio_agent_flow, params={"event_id": None, "by": None, "mode": None})
DECIDE = Operon(
    decide_flow,
    params={
        "view_id": None,
        "action": None,
        "by": None,
        "reason": None,
        "idem_key": None,
        "edits": None,
        "responses": None,
    },
)
RECOMPUTE = Operon(recompute_flow, params={"run": None, "by": None, "idem_key": None})
RUN_DECIDE = Operon(run_decide_flow, params={"run": None, "action": None, "by": None, "reason": None})


def ok(engine, **inputs):
    out = asyncio.run(engine.run(inputs=inputs))
    assert "$errors" not in out, out["$errors"]
    return out


def approved(*titles):
    """News → event → mock agent → approved: returns (view, run)."""
    when = format_datetime(datetime.fromtimestamp(NOW - 600, timezone.utc))
    body = "".join(
        f"<item><title>{t} ({n})</title><link>https://vneconomy.vn/a{n}.htm</link><description>{t}</description>"
        f"<pubDate>{when}</pubDate></item>"
        for t, n in zip(titles, LINKS)
    )
    ids = ok(INGEST, feeds={"vneconomy_ck": f"<rss><channel>{body}</channel></rss>"}, now=NOW)["ingest"]["ids"]
    ev = ok(EVENT, news_ids=ids, by="cio")["event"]
    view = ok(AGENT, event_id=ev["id"], by="cio")["result"]["view"]
    dec = ok(
        DECIDE, view_id=view["id"], action="approve", by="cio", reason="Đồng ý kịch bản", idem_key=f"ap-{view['id']}"
    )["decision"]
    return view, runs.get(dec["run"]["id"])


MARKET = ("VN-Index giảm mạnh, khối ngoại bán ròng", "Cổ phiếu ngân hàng giảm theo thị trường chứng khoán")


def test_approval_applies_the_view_to_every_family():
    view, run = approved(*MARKET)
    assert run["status"] == "EFFECTIVE" and run["families"] == len(fixtures.client_ids())
    assert run["snapshot_id"].startswith("SN-") and run["model"]["assumed"]
    ranks = [r["expected_3m"] for r in run["ranking"]]
    assert ranks == sorted(ranks)
    fams = runs.family_results(run["id"])
    for fid, r in fams.items():  # BR-09: the flag is exactly the 3-month P10 at −5 % of net worth
        assert r["pre_review"] == (r["net_worth"] > 0 and r["horizons"]["3m"]["p10"] <= -0.05 * r["net_worth"])
        assert sum(r["horizons"]["3m"]["by_class"].values()) == r["horizons"]["3m"]["expected"]
    ex = run["exposure"]
    assert sum(ex["total"].values()) == run["totals"]["expected_3m"]
    assert ex["rows"][0]["vnd"].keys() == set(ex["factors"])


def _edit_impact(run_id, family_id, change):
    """Change one stored family result as someone holding the key would (sealed when MF_DATA_KEYS is set)."""
    with db.tx() as con:
        row = con.execute(
            "select id, data from family_impacts where run_id = ? and family_id = ?", (run_id, family_id)
        ).fetchone()
        at = crypto.where("family_impacts", row["id"], "data")
        d = json.loads(crypto.open_(row["data"], at))
        change(d)
        con.execute("update family_impacts set data = ? where id = ?", (crypto.seal(db.dumps(d), at), row["id"]))


def test_a_run_recomputes_to_the_dong_and_tampering_is_found():
    _, run = approved(*MARKET)
    assert runs.verify(run["id"])["ok"]
    fid = next(iter(runs.family_results(run["id"])))
    _edit_impact(run["id"], fid, lambda d: d["horizons"]["3m"].update(expected=d["horizons"]["3m"]["expected"] + 1))
    assert runs.verify(run["id"])["differences"] == [f"{fid} 3m expected"]

    def goal_level(d):  # change one goal's level instead (FR-404)
        d["horizons"]["3m"]["expected"] -= 1
        d["goal_impact"]["pool"]["after"] += 1

    _edit_impact(run["id"], fid, goal_level)
    assert runs.verify(run["id"])["differences"] == [f"{fid} goal_impact"]
    with db.tx() as con:  # change the frozen snapshot
        row = con.execute("select data from run_snapshots where id = ?", (run["snapshot_id"],)).fetchone()
        snap = json.loads(row["data"])
        snap["branches"][0]["probability"] = 0.99
        con.execute("update run_snapshots set data = ? where id = ?", (json.dumps(snap), run["snapshot_id"]))
    assert runs.verify(run["id"])["differences"] == ["snapshot đã bị sửa"]


def test_a_run_gives_each_goal_its_funding_before_and_after_with_a_level():
    # FR-404: every family's dated goals, funded in date order from its financial assets
    _, run = approved(*MARKET)
    fams = runs.family_results(run["id"])
    c01 = fams["C01"]["goal_impact"]
    assert [g["goal_id"] for g in c01["goals"]] == ["GL-C01-01", "GL-C01-02"]
    pool = c01["pool"]
    assert pool["after"] == pool["before"] + pool["change"] and pool["change"] < 0  # a market fall
    for r in fams.values():
        for g in r["goal_impact"]["goals"]:
            for side in ("before", "after"):
                assert g[side]["level"] in ("Đạt", "Theo dõi", "Thiếu") and 0 <= g[side]["ratio"] <= 1
            assert g["changed"] == (g["before"]["level"] != g["after"]["level"])
    assert run["totals"]["goals_changed"] == sum(g["changed"] for r in fams.values() for g in r["goal_impact"]["goals"])


def test_goal_levels_follow_the_funding_and_the_surplus():
    from apply.goals import goal_impacts

    fam = {
        "holdings": [
            {"key": "s", "kind": "asset", "class": "stock", "value": 1_000.0},
            {"key": "h", "kind": "asset", "class": "real_estate", "value": 9_000.0},  # not in the pool
        ],
        "goals": [
            {"goal_id": "G1", "label": "a", "date": "2027-01-15", "amount": 800.0},
            {"goal_id": "G2", "label": "b", "date": "2027-01-20", "amount": 200.0},
        ],
        "surplus_monthly": 30.0,
    }
    out = goal_impacts(fam, {"s": -100.0, "h": -5_000.0}, "2026-10-09")
    assert out["pool"] == {"before": 1_000.0, "after": 900.0, "change": -100.0}
    g1, g2 = out["goals"]
    assert g1["before"]["level"] == g1["after"]["level"] == "Đạt"  # the earlier goal is funded first
    # G2: 100 short over 3 months = 33.3/month against a surplus of 30 → above 1 → Thiếu
    assert (g2["before"]["ratio"], g2["after"]["ratio"]) == (1.0, 0.5)
    assert (g2["before"]["level"], g2["after"]["level"], g2["changed"]) == ("Đạt", "Thiếu", True)
    fam["surplus_monthly"] = 60.0  # 33.3 / 60 = 0.56 → Đạt; 40 / 60 → Theo dõi
    assert goal_impacts(fam, {"s": -100.0}, "2026-10-09")["goals"][1]["after"]["level"] == "Đạt"
    assert goal_impacts(fam, {"s": -120.0}, "2026-10-09")["goals"][1]["after"]["level"] == "Theo dõi"


def test_the_same_approval_applied_twice_is_one_run():
    view, run = approved(*MARKET)
    again = asyncio.run(
        runs.apply_view(
            view | {"status": "APPROVED"}, "cio", run["decision_id"], idem_key=f"apply:{run['decision_id']}"
        )
    )
    assert again["id"] == run["id"] and len(runs.runs(view_id=view["id"])) == 1


def test_a_held_run_is_hidden_from_rms_until_the_cio_makes_it_effective(monkeypatch):
    real = runs.postcheck

    def critical(*a, **kw):
        out = real(*a, **kw)
        out["findings"].append({"id": "PX", "severity": "critical", "family_id": None, "title": "t", "detail": "d"})
        out["counts"]["critical"] += 1
        return out

    monkeypatch.setattr(runs, "postcheck", critical)
    _, run = approved(*MARKET)
    assert run["status"] == "NEEDS_CIO_REVIEW"
    assert reads.family_impact("C01", "rm")["items"] == []
    assert reads.family_impact("C01", "cio")["items"][0]["status"] == "NEEDS_CIO_REVIEW"
    assert "Cần lý do" in str(
        asyncio.run(RUN_DECIDE.run(inputs={"run": run["id"], "action": "make_effective", "by": "cio", "reason": ""}))[
            "$errors"
        ]
    )
    ok(RUN_DECIDE, run=run["id"], action="make_effective", by="cio", reason="Đã kiểm tra, số hợp lý")
    assert reads.family_impact("C01", "rm")["items"][0]["status_label"] == "Hiệu lực"


def test_withdrawing_the_view_withdraws_its_runs_and_rms_see_the_label():
    view, run = approved(*MARKET)
    out = ok(DECIDE, view_id=view["id"], action="withdraw", by="cio", reason="Tin nguồn đã được đính chính")
    assert out["decision"]["withdrawn_runs"] == [run["id"]]
    rm = reads.family_impact("C01", "rm")
    assert rm["items"][0]["status_label"] == "Đã thu hồi" and rm["effective_count"] == 0
    assert reads.family_impact("C01", "client")["items"] == []


def test_recompute_makes_a_new_run_and_supersedes_the_old():
    _, run = approved(*MARKET)
    out = ok(RECOMPUTE, run=run["id"], by="cio")
    assert out["run"]["status"] == "EFFECTIVE" and out["run"]["id"].endswith("-2")
    assert all(c["delta"] == 0 for c in out["compare"])  # same data, same numbers
    assert runs.get(run["id"])["status"] == "SUPERSEDED"
    labels = [i["status_label"] for i in reads.family_impact("C01", "rm")["items"]]
    assert sorted(labels) == ["Hiệu lực", "Đã thay thế"]


def test_the_trace_goes_from_a_number_back_to_the_news():
    view, run = approved(*MARKET)
    t = trace.trace(run["id"], "C01")
    fam = runs.family_result(run["id"], "C01")
    assert t["number"]["value"] == fam["horizons"]["3m"]["expected"]
    assert sum(h["contribution"] for h in t["holdings"]) == t["number"]["value"]
    weighted = sum(b["probability"] * b["family_expected"] for b in t["branches"])
    assert weighted == pytest.approx(t["number"]["value"], abs=len(t["branches"]))
    assert t["approval"]["by"] == "cio" and t["approval"]["reason"] == "Đồng ý kịch bản"
    assert t["view"]["id"] == view["id"] and all(n["url"].startswith("https://vneconomy.vn/") for n in t["news"])
    assert t["snapshot"]["price_date"] == fixtures.market()["as_of"]
    one = trace.trace(run["id"], "C01", key="VNINDEX")
    assert one["number"]["value"] == fam["horizons"]["3m"]["by_factor"]["VNINDEX"]
    assert all("VNINDEX" in h["loads"] for h in one["holdings"])


def test_the_client_reads_asset_classes_only_with_the_labels():
    approved(*MARKET)
    c = reads.family_impact("C01", "client")
    item = c["items"][0]
    for staff_only in ("holdings", "by_factor", "summary", "pre_review", "postcheck"):
        assert staff_only not in item
    assert item["event"]["title"] in ("Thị trường cổ phiếu", "Sự kiện thị trường")  # not the headline
    assert "không phải khuyến nghị" in c["labels"]["note"] and c["labels"]["ai"] == "AI hỗ trợ"
    with pytest.raises(Exception, match="không có"):
        reads.family_impact("C01", "hacker")


def test_the_rm_today_list_holds_the_flagged_families_worst_first():
    _, run = approved(*MARKET)
    flagged = [r["family_id"] for r in run["ranking"] if r["pre_review"]]
    cases = reads.rm_today()["cases"]
    assert sorted(c["family_id"] for c in cases) == sorted(flagged)
    assert [c["p10_3m_pct"] for c in cases] == sorted(c["p10_3m_pct"] for c in cases)


# -- the audit chain ---------------------------------------------------------------------------


def test_every_step_is_in_the_audit_chain_and_it_verifies():
    view, run = approved(*MARKET)
    with db.tx() as con:
        v = audit.verify(con)
        actions = [r["action"] for r in con.execute("select action from audit_log order by seq")]
    assert v["ok"] and v["count"] == len(actions)
    for needed in (
        "news.add",
        "event.create",
        "view.create",
        "agent.start",
        "agent.finish",
        "challenge.add",
        "decision.approve",
        "run.create",
        "run.computed",
        "run.status",
    ):
        assert needed in actions, needed


def test_the_database_refuses_to_edit_the_log_and_a_forced_edit_is_found():
    approved(*MARKET)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        with db.tx() as con:
            con.execute("update audit_log set actor = 'mallory' where seq = 2")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        with db.tx() as con:
            con.execute("delete from audit_log where seq = 2")
    with db.tx() as con:  # someone with write access drops the trigger and edits a row
        con.execute("drop trigger audit_log_no_update")
        con.execute("update audit_log set actor = 'mallory' where seq = 2")
    with db.tx() as con:
        v = audit.verify(con)
    assert (v["ok"], v["broken_at"]) == (False, 2)


def test_hmac_chain_and_no_downgrade(monkeypatch):
    monkeypatch.setenv("AUDIT_HMAC_KEY", "test-key")
    approved(*MARKET)
    with db.tx() as con:
        v = audit.verify(con)
    assert v["ok"] and v["algorithms"] == ["hmac-sha256"]
    monkeypatch.delenv("AUDIT_HMAC_KEY")
    with pytest.raises(audit.AuditError, match="không được hạ về SHA-256"):
        with db.tx() as con:
            audit.append(con, "x", "y", "z")
    with db.tx() as con:
        assert not audit.verify(con)["ok"]  # without the key the chain cannot be checked


# -- the reads ---------------------------------------------------------------------------------


def test_the_endpoints():
    from app.web import app

    _, run = approved(*MARKET)
    client = TestClient(app)
    assert client.get("/api/runs").json()["runs"][0]["id"] == run["id"]
    assert client.get(f"/api/runs/{run['id']}/verify").json()["ok"]
    assert client.get("/api/families/C01/impact?role=client").json()["items"]
    assert client.get("/api/families/C01/impact?role=x").status_code == 403
    assert client.get(f"/api/trace/{run['id']}/C01").json()["number"]["value"] is not None
    assert client.get("/api/trace/AR-0000-v1-1/C01").status_code == 404
    assert client.get("/api/audit/verify").json()["ok"]
    assert client.get("/api/audit?limit=5").json()["rows"][0]["seq"] > 1
    assert "cases" in client.get("/api/rm/today").json()


def test_br08_each_goal_gets_its_vnd_share_of_the_pools_impact_at_every_horizon():
    from apply.goals import goal_impacts

    fam = {
        "holdings": [{"key": "s", "kind": "asset", "class": "stock", "value": 1_000.0}],
        "goals": [
            {"goal_id": "G1", "label": "a", "date": "2027-01-15", "amount": 600.0},
            {"goal_id": "G2", "label": "b", "date": "2027-01-20", "amount": 300.0},
        ],
        "surplus_monthly": 30.0,
    }
    bands = {"3m": {"expected": -100.0, "p5": -300.0, "p10": -250.0, "p50": -90.0, "p90": 40.0}}
    out = goal_impacts(fam, {"s": -100.0}, "2026-10-09", bands)
    g1, g2 = out["goals"]
    assert (g1["share"], g2["share"], out["unallocated"]["share"]) == (0.6, 0.3, pytest.approx(0.1))
    assert g1["impact"]["3m"] == {"expected": -60, "p5": -180, "p10": -150, "p50": -54, "p90": 24}
    for x in ("expected", "p5", "p10", "p50", "p90"):  # the goals and the rest add up to the pool
        total = g1["impact"]["3m"][x] + g2["impact"]["3m"][x] + out["unallocated"]["impact"]["3m"][x]
        assert abs(total - bands["3m"][x]) <= 2


def test_br08_a_run_sums_the_vnd_impact_by_goal_from_the_same_engine_and_old_runs_still_verify():
    _, run = approved(*MARKET)
    fams = runs.family_results(run["id"])
    gi = fams["C01"]["goal_impact"]
    pool3 = gi["pool"]["bands"]["3m"]
    assert set(gi["pool"]["bands"]) == {"1w", "3m", "12m"}
    assert abs(pool3["expected"] - gi["pool"]["change"]) <= len(fams["C01"]["holdings"])  # one engine, two cuts
    for g in gi["goals"]:
        assert set(g["impact"]) == {"1w", "3m", "12m"} and set(g["impact"]["3m"]) == {
            "expected",
            "p5",
            "p10",
            "p50",
            "p90",
        }
        assert g["impact"]["3m"]["p5"] <= g["impact"]["3m"]["p50"] <= g["impact"]["3m"]["p90"]
    assert runs.verify(run["id"])["ok"]

    def before_f10(d):  # a run stored before F10: no per-goal impact; it still verifies on what it holds
        for g in (d.get("goal_impact") or {}).get("goals", []):
            g.pop("impact", None), g.pop("share", None)

    for fid in runs.family_results(run["id"]):
        _edit_impact(run["id"], fid, before_f10)
    assert runs.verify(run["id"])["ok"]
    _edit_impact(run["id"], "C01", lambda d: d["goal_impact"]["goals"][0]["after"].update(ratio=0.0))
    assert "C01 goal_impact" in runs.verify(run["id"])["differences"]


def test_fd9_the_client_reads_how_its_number_is_made_by_asset_class_with_no_holding_named():
    _, run = approved(*MARKET)
    how = trace.client_how(run["id"], "C01")
    fam = runs.family_result(run["id"], "C01")
    assert how["number"]["value"] == fam["horizons"]["3m"]["expected"] and how["formula"].startswith("Tác động kỳ vọng")
    assert sum(c["contribution"] for c in how["classes"]) == pytest.approx(
        how["number"]["value"], abs=len(how["classes"])
    )
    assert sum(b["probability"] for b in how["branches"]) == pytest.approx(1.0)
    assert all(b["moves"] and b["family_expected"] is not None for b in how["branches"])
    text = json.dumps(how, ensure_ascii=False)
    for h in fam["holdings"]:  # no holding, ticker or account by name
        assert f'"{h["key"]}"' not in text and (not h.get("name") or h["name"] not in text)
    from events import store as events
    from views import store as vstore

    ev = events.get(vstore.get(run["view_id"])["event_id"])
    assert ev["title"] not in text and not any(n["title"] in text for n in ev["news"])  # outlets, not headlines
    with TestClient(Application.find(".").asgi()) as c:
        r = c.get(f"/api/families/C01/how?run={run['id']}")
        assert r.status_code == 200 and r.json()["classes"]
        assert c.get("/api/families/C01/how?run=AR-9999").status_code == 404


def test_nfr01_one_familys_page_reads_its_row_and_the_snapshot_head_only():
    _, run = approved(*MARKET)
    full = runs.snapshot(run["snapshot_id"])
    head = runs.snapshot_head(run["snapshot_id"])
    assert "families" not in head and head == {k: v for k, v in full.items() if k != "families"}
    every = runs.family_results(run["id"])
    for fid in every:
        assert runs.family_result(run["id"], fid) == every[fid]
    with pytest.raises(KeyError):
        runs.family_result(run["id"], "C99")


def test_nfr01_one_read_reads_each_client_from_the_database_once_and_still_hands_out_copies(monkeypatch):
    from people import store as people_store

    a = people_store.client("C01")
    with people_store.one_read():
        b, c = people_store.client("C01"), people_store.client("C01")
        b["name"] = "đổi"
        assert c["name"] == a["name"] and people_store.client("C01") == a
        with monkeypatch.context() as m:  # inside one_read a second read never reaches the database
            m.setattr(people_store, "_client_rows", None)
            assert people_store.client("C01") == a
    with monkeypatch.context() as m:  # outside it every read does
        m.setattr(people_store, "_client_rows", None)
        with pytest.raises(TypeError):
            people_store.client("C01")
