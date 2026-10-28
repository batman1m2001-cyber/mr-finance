"""NEWS_EVIDENCE_BRD: every frame passes the checks (§9), the statistics are computed with n and the base rate (§5),
the labels match the same way every time (§7), the CIO's review and the unsourced marks (§8.2), and Ví dụ 4 end to end
(a plan frame → a goal → an RM task → a client message once the RM declares the goal)."""

import asyncio
import re
from datetime import date, timedelta

import pytest
from operonx import Operon

from evidence import _check, _stats, agent, frames, labels
from evidence import catalogue as cat
from evidence.graph import evidence_decide_flow, evidence_draft_decide_flow, evidence_draft_flow, evidence_flow
from impact.graph import alerts_flow
from market import store as market
from procedural import goals
from research import ops as research_ops
from research.graph import goal_outflow_flow
from wealth import fixtures

READ = Operon(evidence_flow, params={"factor": None, "role": None})
DECIDE = Operon(evidence_decide_flow, params={"factor": None, "decision": None, "by": None, "note": None})
ALERTS = Operon(alerts_flow, params={"client_id": None, "scope": None})
DECLARE = Operon(
    goal_outflow_flow, params={"family_id": None, "goal_id": None, "purpose": None, "by": None, "country": None}
)
TODAY = date(2026, 10, 15)


def run(engine, **inputs):
    return asyncio.run(engine.run(inputs={k: inputs.get(k) for k in engine_params(engine)}))


def engine_params(engine):
    return {READ: ("factor", "role"), DECIDE: ("factor", "decision", "by", "note"),
            ALERTS: ("client_id", "scope"), DECLARE: ("family_id", "goal_id", "purpose", "by", "country")}[engine]  # fmt: skip


def error(out):
    (e,) = out["$errors"].values()
    return e["message"]


def alerts(client_id):
    out = run(ALERTS, client_id=client_id, scope="personal")
    assert "$errors" not in out, out["$errors"]
    return out["report"]["alerts"]


def series(events, fall=True):
    """A synthetic index: up 0.1% a day and down 0.5% a day the week after each event; ``fall=False`` the other way."""
    days = sorted(date.fromisoformat(e) for e in events)
    after = {d + timedelta(days=k) for d in days for k in range(1, 8)}
    out, v, d = [], 1000.0, days[0] - timedelta(days=60)
    while d <= days[-1] + timedelta(days=60):
        v *= (0.995 if d in after else 1.001) if fall else (1.005 if d in after else 0.999)
        out.append((d.isoformat(), round(v, 4)))
        d += timedelta(days=1)
    return out


def test_every_seed_frame_passes_the_checks():
    for fid, raw in frames.data()["frames"].items():
        why, _ = _check.check(raw)
        assert why == [], (fid, why)
        assert all(cat.valid_target(t) for t in raw["targets"]), fid


def test_the_checks_send_back_what_the_brd_forbids():
    raw = dict(frames.data()["frames"]["P09"])
    assert any("Loại sự kiện" in w for w in _check.check({**raw, "event_type": "đảo chính"})[0])
    assert any("Nhãn đối tượng" in w for w in _check.check({**raw, "targets": ["asset:tranh"]})[0])
    assert any("Kênh" in w for w in _check.check({**raw, "channels": ["tin đồn"]})[0])
    assert any("Thiếu trường" in w for w in _check.check({**raw, "watch": ""})[0])
    assert any("dự báo" in w for w in _check.check({**raw, "mechanism": "Giá vàng sẽ tăng 15% trong quý."})[0])
    assert any("cấm" in w for w in _check.check({**raw, "watch": "Theo dõi các vụ rửa tiền."})[0])
    bad = {**raw, "precedents": [{"event": "2013", "outcome": "", "difference": "x", "source": None}]}
    assert any("Tiền lệ 1 thiếu kết quả" in w for w in _check.check(bad)[0])
    # a model's answer of the wrong kind goes back instead of breaking the check (seen live: watch as a list)
    for wrong in ({"watch": ["Giá vàng thế giới", "Chênh lệch SJC"]}, {"targets": "asset:gold"}, {"precedents": ["2013"]}):
        assert any("Sai kiểu" in w for w in _check.check({**raw, **wrong})[0]), wrong


def test_the_statistics_say_n_and_the_base_rate():
    events = frames.data()["events"]["fed_hike"]
    s = _stats.measure(series(events), events, "1w")
    assert (s["n"], s["same"], s["way"], s["enough"]) == (len(events), len(events), "down", True)
    assert s["base_rate"] < 0.5 and s["edge"] >= cat.MIN_EDGE and s["direction"] == "negative"
    text = _stats.sentence(s, "Fed tăng lãi suất", "VN-Index")
    assert f"Trong {len(events)} lần" in text and "so với" in text and "Trung vị" in text
    few = _stats.measure(series(events), events[: cat.MIN_PRECEDENTS - 1], "1w")
    assert not few["enough"] and few["direction"] == "unclear"
    assert _stats.measure([], events, "1w")["direction"] == "unclear"


def test_the_statistics_branch_reads_the_market_and_falls_back_with_too_few():
    events = frames.data()["events"]["fed_hike"]
    assert frames.frame("M03")["branch"] == "qualitative"  # an empty market: no precedent measured
    market.put("VNINDEX", "test", "", series(events))
    f = frames.frame("M03")
    assert f["branch"] == "statistics" and f["stats"]["n"] == len(events) and f["direction"] == "negative"
    assert frames.label(f) == f"{len(events)}/{len(events)} lần"
    view = frames.view("M03")
    assert view["stats"]["base_rate"] is not None and view["stats"]["sentence"]


def test_the_computed_direction_wins_over_the_agents():
    """§9 rule 7: on the statistics branch the agent's direction gives way, with a note for the CIO."""
    raw = {**frames.data()["frames"]["M03"], "direction": "positive"}
    why, kept = _check.check(raw, "negative")
    assert why == [] and kept["direction"] == "negative"
    assert any("giữ chiều hướng của thống kê" in n for n in kept["notes"])
    market.put("VNINDEX", "test", "", series(frames.data()["events"]["fed_hike"], fall=False))
    assert frames.frame("M03")["direction"] == "positive"  # the index rose after each hike: the stats say so


def test_each_alert_names_the_labels_the_client_has_and_the_same_way_every_time():
    for cid in fixtures.client_ids():
        first = alerts(cid)
        for a in first:
            if a["evidence"]:
                targets = frames.data()["frames"][a["factor"]]["targets"]
                assert a["labels"] and set(a["labels"]) <= set(targets), (cid, a["id"], a["labels"])
                assert a["evidence"]["label"] and a["evidence"]["timeframe"] in cat.TIMEFRAMES, (cid, a["id"])
        assert [(a["id"], a["labels"]) for a in alerts(cid)] == [(a["id"], a["labels"]) for a in first]


def test_a_plan_label_read_from_a_goals_name_is_inferred():
    client = fixtures.client("C01")
    got = labels.of([], client, {}, TODAY)
    assert got["plan:study_abroad"]["inferred"]
    goal = goals.goals_of(client, TODAY)[0]
    dec = {goal["goal_id"]: {"purpose": "study_abroad", "country": "Úc"}}
    assert not labels.of([], client, dec, TODAY)["plan:study_abroad"]["inferred"]
    assert labels.match(["asset:gold", "plan:study_abroad"], got) == ["plan:study_abroad"]


def test_example_4_a_plan_frame_reaches_the_goal_and_the_client_only_once_declared():
    """Ví dụ 4: tighter transfers abroad → plan:study_abroad → C01's study in Úc → an RM task; the client reads a
    message (dated MM/YYYY, no AML wording) only after the RM declares the goal."""
    ev = [m for m in research_ops.matches("C01", TODAY) if m["note_id"] == "EV-P15"]
    assert [(m["level"], m["declared"], m["client_message"]) for m in ev] == [("confirm_goal", False, None)]
    run(DECLARE, family_id="C01", goal_id=ev[0]["goal_id"], purpose="study_abroad", country="Úc", by="rm01")
    (m,) = [m for m in research_ops.matches("C01", TODAY) if m["note_id"] == "EV-P15"]
    assert m["declared"] and m["level"] in ("remind", "contact_now") and m["rm_hint"]
    month = date.fromisoformat(m["milestone"]).strftime("%m/%Y")
    assert f"tháng {month}" in m["client_message"] and "{milestone}" not in m["client_message"]
    assert not goals.forbidden_words(m["client_message"]) and "rửa tiền" not in m["client_message"].lower()


def test_only_the_cio_sees_the_headline_the_review_and_the_unsourced_precedents():
    rm = run(READ, role="rm")["evidence"]
    p01 = next(f for f in rm["frames"] if f["factor"] == "P01")
    assert "unsourced" not in p01 and "headline" not in p01 and "review" not in p01 and "calendar" not in rm
    assert not any("unsourced" in p for f in rm["frames"] for p in f["precedents"])
    cio = run(READ, factor="P01", role="cio")["evidence"]
    (f,) = cio["frames"]
    assert f["unsourced"] == 1 and f["precedents"][0]["unsourced"] and f["review"]["status"] == "approved"
    assert cio["thresholds"] == {"min_precedents": cat.MIN_PRECEDENTS, "min_edge": cat.MIN_EDGE}


def test_a_returned_frame_leaves_the_chart_and_an_approved_one_comes_back():
    assert next(a for a in alerts("C01") if a["factor"] == "P09")["evidence"]
    out = run(DECIDE, factor="P09", decision="return", by="cio", note="Thiếu nguồn tiền lệ 2")
    assert out["review"]["status"] == "returned" and out["review"]["label"] == "Trả lại agent"
    assert next(a for a in alerts("C01") if a["factor"] == "P09")["evidence"] is None
    assert "P09" not in [f["factor"] for f in run(READ, role="rm")["evidence"]["frames"]]
    assert run(READ, factor="P09", role="cio")["evidence"]["frames"][0]["review"]["note"] == "Thiếu nguồn tiền lệ 2"
    run(DECIDE, factor="P09", decision="approve", by="cio")
    assert next(a for a in alerts("C01") if a["factor"] == "P09")["evidence"]


@pytest.mark.parametrize(
    "inputs, says",
    [
        ({"factor": "P09", "decision": "approve", "by": "rm01"}, "cần vai trò"),
        ({"factor": "X99", "decision": "approve", "by": "cio"}, "không có nhận định"),
        ({"factor": "P09", "decision": "maybe", "by": "cio"}, "decision là một trong"),
    ],
)
def test_only_the_cio_decides_and_only_on_a_known_frame(inputs, says):
    assert says in error(run(DECIDE, **inputs))


def test_reading_an_unknown_frame_is_refused():
    assert "không có nhận định" in error(run(READ, factor="X99", role="cio"))


# --- the evidence agent (§4, P1): mock mode here; the live loop with a fake model ---------------------------------
DRAFT = Operon(evidence_draft_flow, params={"news_id": None, "by": None, "mode": None})
DRAFT_DECIDE = Operon(evidence_draft_decide_flow, params={"news_id": None, "decision": None, "by": None, "note": None})


def news_item(title, kind="monetary", summary=""):
    import time

    from news import store as news

    key = re.sub(r"\W+", "-", title.lower())
    added, _ = news.add([{"source": "test", "url_key": key, "title_key": key, "published": "2026-10-27", "kind": kind,
                          "ingested": time.time(), "status": "new", "relevance": "high", "title": title,
                          "summary": summary, "outlet": "Test", "client_id": "C01"}])  # fmt: skip
    return added[0] if added else news.by_url_key(key)


def go(engine, **inputs):
    return asyncio.run(engine.run(inputs=inputs))


def test_the_agent_reads_the_event_type_from_the_words():
    assert agent.classify({"title": "Fed tăng lãi suất thêm 0,25 điểm"}) == "fed_hike"
    assert agent.classify({"title": "NHNN giảm lãi suất điều hành"}) == "sbv_rate_cut"
    assert agent.classify({"title": "Giá cà phê lập đỉnh mới"}) == "new"


def test_the_agent_sees_the_item_and_nothing_of_a_client():
    assert set(agent.seen({"title": "t", "client_id": "C01", "holdings": [1]})) == set(agent.NEWS_FIELDS)


def test_a_mock_draft_waits_for_the_cio_and_a_new_type_goes_qualitative():
    fed = news_item("Fed tăng lãi suất 0,25 điểm phần trăm")
    out = go(DRAFT, news_id=fed["id"], by="cio", mode="mock")
    assert "$errors" not in out, out.get("$errors")
    d = out["draft"]
    assert (d["event_type"], d["review"]["status"], d["mode"], d["failed"]) == ("fed_hike", "pending", "mock", [])
    other = news_item("Giá cà phê lập đỉnh mới", kind="commodity")
    d = go(DRAFT, news_id=other["id"], by="cio", mode="mock")["draft"]
    assert (d["event_label"], d["direction"], d["precedents"]) == ("Loại mới", "unclear", 0)
    cio = run(READ, role="cio")["evidence"]
    assert {fed["id"], other["id"]} <= {x["news_id"] for x in cio["drafts"]}
    assert fed["id"] not in {s["id"] for s in cio["suggested"]}
    assert "drafts" not in run(READ, role="rm")["evidence"]


def test_only_the_cio_drafts_and_a_failed_draft_is_never_approved():
    item = news_item("NHNN giảm lãi suất điều hành 0,5 điểm")
    assert "cần vai trò" in error(go(DRAFT, news_id=item["id"], by="rm01", mode="mock"))
    assert "không có tin" in error(go(DRAFT, news_id="NW-999999", by="cio", mode="mock"))
    d = agent.draft(item, agent.mock(item), ["chiều hướng không hợp lệ"], "live", 3, [])
    agent.keep(item["id"], d)
    assert "chưa qua kiểm tra" in error(go(DRAFT_DECIDE, news_id=item["id"], decision="approve", by="cio"))
    out = go(DRAFT_DECIDE, news_id=item["id"], decision="return", by="cio", note="Thiếu tiền lệ")
    assert out["draft"]["review"]["status"] == "returned"
    go(DRAFT, news_id=item["id"], by="cio", mode="mock")
    assert go(DRAFT_DECIDE, news_id=item["id"], decision="approve", by="cio")["draft"]["review"]["label"] == "Đã duyệt"


def test_the_live_agent_is_sent_back_with_the_reasons(monkeypatch):
    import json

    from views import agents

    good = {k: frames.data()["frames"]["P01"].get(k) for k in agent.FIELDS}
    asked = []

    async def model(role, system, user, max_tokens):
        asked.append(user)
        frame = {**good, "direction": "lên"} if len(asked) == 1 else good
        return json.dumps(frame, ensure_ascii=False), {"cost_usd": 0.001}

    monkeypatch.setattr(agents, "call_model", model)
    frame, why, attempts, calls = asyncio.run(agent.live({"title": "Fed tăng lãi suất", "client_id": "C01"}))
    assert (why, attempts, len(calls)) == ([], 2, 2)
    assert "bị trả lại" in asked[1] and "C01" not in asked[0]
