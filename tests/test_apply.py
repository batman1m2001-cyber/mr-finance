"""Application runs (src/apply) and the audit chain (src/control/audit): an approved view applied to
every family, reproducible to the dong, post-checked, ranked, traceable, withdrawable."""

import asyncio
import json
import sqlite3
from datetime import datetime, timezone
from email.utils import format_datetime

import pytest
from operonx import Operon
from starlette.testclient import TestClient

from apply import reads, trace
from apply import run as runs
from apply.graph import recompute_flow, run_decide_flow
from control import audit, db
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
RECOMPUTE = Operon(recompute_flow, params={"run_id": None, "by": None, "idem_key": None})
RUN_DECIDE = Operon(run_decide_flow, params={"run_id": None, "action": None, "by": None, "reason": None})


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


def test_a_run_recomputes_to_the_dong_and_tampering_is_found():
    _, run = approved(*MARKET)
    assert runs.verify(run["id"])["ok"]
    fid = next(iter(runs.family_results(run["id"])))
    with db.tx() as con:  # change one stored number
        row = con.execute(
            "select data from family_impacts where run_id = ? and family_id = ?", (run["id"], fid)
        ).fetchone()
        data = json.loads(row["data"])
        data["horizons"]["3m"]["expected"] += 1
        con.execute(
            "update family_impacts set data = ? where run_id = ? and family_id = ?", (json.dumps(data), run["id"], fid)
        )
    assert runs.verify(run["id"])["differences"] == [f"{fid} 3m expected"]
    with db.tx() as con:  # change the frozen snapshot
        row = con.execute("select data from run_snapshots where id = ?", (run["snapshot_id"],)).fetchone()
        snap = json.loads(row["data"])
        snap["branches"][0]["probability"] = 0.99
        con.execute("update run_snapshots set data = ? where id = ?", (json.dumps(snap), run["snapshot_id"]))
    assert runs.verify(run["id"])["differences"] == ["snapshot đã bị sửa"]


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
        asyncio.run(
            RUN_DECIDE.run(inputs={"run_id": run["id"], "action": "make_effective", "by": "cio", "reason": ""})
        )["$errors"]
    )
    ok(RUN_DECIDE, run_id=run["id"], action="make_effective", by="cio", reason="Đã kiểm tra, số hợp lý")
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
    out = ok(RECOMPUTE, run_id=run["id"], by="cio")
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
