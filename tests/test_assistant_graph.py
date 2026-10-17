"""The assistant sees the graph (UNIFIED_FLOWS_PLAN F10, OWN-GW-47/48): the panel's request carries the workspace —
the lens, what is picked, the active scenarios — checked on the server (unknown ids dropped, the person's what-if
only inside its bounds); the instructions say it, the picked item's name only in model mode; ``lien_ket`` answers
with the overview's own links and ``so_sanh_kich_ban`` with the combine engine's own numbers, each alone and all
together; the stream lights what each read. Offline: a scripted model."""

import asyncio

import pytest
from operonx import Operon
from operonx_agents.testing import ScriptedLLM, asks, says
from test_assistant_stream import BODY, app, model_on, stream  # noqa: F401 - the stream test's fixtures

from assistant import graphtools
from assistant import stream as st
from assistant.base import Ctx, ToolFailed
from assistant.ops import graph_of, request_of
from assistant.turn import graph_line
from overview.graph import overview_flow
from scenarios.graph import combine_flow

PICK = {"id": "GL:tuition", "kind": "goal", "label": "Học phí cho con"}


def ctx(graph=None, reads=True):
    return Ctx(role="client", client_id="C01", scope="personal", question="", reads=reads, graph=graph or {})


def run(coro):
    return asyncio.run(coro)


def combined(ids, params=None):
    eng = Operon(combine_flow, params={"client_id": None, "scenarios": None, "params": None, "scope": None,
                                       "goals": None})  # fmt: skip
    out = run(eng.run(inputs={"client_id": "C01", "scenarios": ids, "params": params or {}, "scope": "personal",
                              "goals": None}))  # fmt: skip
    return out["result"]


def test_the_request_carries_the_workspace_checked():
    g = graph_of({"lens": "muc-tieu", "selected": PICK, "active": ["vni_30", "nope", "vni_30", "tuition"]})
    assert g == {"lens": "muc-tieu", "selected": PICK, "active": ["vni_30"]}  # unknown and life events dropped
    assert graph_of({"lens": "../x", "selected": {"id": ""}, "active": "vni_30"}) == {}
    assert graph_of("anything") == {}
    ok = graph_of({"active": ["custom"], "params": {"custom": {"stock": -0.2}}})
    assert ok["active"] == ["custom"] and ok["params"]["custom"]["stock"] == -0.2
    assert "active" not in graph_of({"active": ["custom"], "params": {"custom": {"stock": -0.9}}})  # out of bounds
    many = graph_of({"active": ["vni_30", "rates_up", "usd_up", "re_freeze", "bond_crisis", "custom", "vni_30"]})
    assert len(many["active"]) == 6 and many["params"]["custom"]["stock"] == 0  # no inputs: a what-if of nothing
    r = request_of(message="Mục này liên quan gì?", role="client", client_id="C01", graph={"lens": "tin"})
    assert r["graph"] == {"lens": "tin"}


def test_the_instructions_say_it_and_the_name_only_in_model_mode():
    g = {"lens": "muc-tieu", "selected": PICK, "active": ["vni_30", "rates_up"]}
    model = graph_line(ctx(g, reads=True))
    assert "Mục tiêu & kịch bản" in model and "“Học phí cho con” (GL:tuition)" in model
    assert "VN-Index giảm 30%" in model and "Lãi suất tăng 2%" in model and "lien_ket" in model
    template = graph_line(ctx(g, reads=False))
    assert "Học phí" not in template and "GL:tuition" not in template and "đang chọn một mục tiêu" in template
    assert graph_line(ctx({})) == ""


def test_links_are_the_overviews_own():
    o = run(Operon(overview_flow, params={"client_id": None, "scope": None, "role": None, "goals": None}).run(
        inputs={"client_id": "C01", "role": "client"}))["overview"]  # fmt: skip
    mine = [e for e in o["edges"] if "GL:tuition" in (e["from"], e["to"])]
    got = run(graphtools.links(ctx({"selected": PICK}), {}))
    assert got["data"]["node"] == "GL:tuition" and len(got["data"]["links"]) == len(mine)
    for row in got["data"]["links"]:
        e = next(x for x in mine if row["id"] in (x["from"], x["to"]))
        assert (row["value"], row["monthly"], row["certainty"]) == (e["value"], e.get("monthly"), e["certainty"])
    assert "goal:tuition" in got["focus"] and "kpi:net_worth" in got["focus"]  # the node and its neighbours
    edge = run(graphtools.links(ctx(), {"node": "ME>GL:tuition"}))
    assert edge["text"].startswith("Liên kết") and edge["data"]["node"] == "GL:tuition"
    with pytest.raises(ToolFailed):
        run(graphtools.links(ctx(), {}))  # nothing picked, nothing named
    with pytest.raises(ToolFailed):
        run(graphtools.links(ctx(), {"node": "HD:someone-else"}))


def test_the_comparison_is_the_engines_own_alone_and_together():
    got = run(graphtools.compare(ctx({"active": ["vni_30", "rates_up"]}), {}))
    both = combined(["vni_30", "rates_up"])
    assert got["data"]["together"] == pytest.approx(both["change"])
    assert got["data"]["alone"]["vni_30"] == pytest.approx(combined(["vni_30"])["change"])
    assert got["data"]["alone"]["rates_up"] == pytest.approx(combined(["rates_up"])["change"])
    assert "Cùng lúc" in got["text"] and "không cộng vào tài sản ròng" in got["text"]
    assert {"scenario:vni_30", "scenario:rates_up", "class:stock"} <= set(got["focus"])
    assert got["data"]["goals"] == {g["id"]: [g["before"]["status"], g["after"]["status"]] for g in both["goals"]}
    picked = run(graphtools.compare(ctx({"active": ["vni_30", "rates_up"], "selected": PICK}), {}))
    assert picked["text"].split("Mục tiêu: ")[1].startswith("Học phí cho con")  # what is picked is said first
    named = run(graphtools.compare(ctx(), {"scenarios": ["ty_gia"]}))  # named: the active set is not needed
    assert named["data"]["scenarios"] == ["usd_up"]
    mine = run(graphtools.compare(ctx({"active": ["custom"], "params": {"custom": {"income": -0.2}}}), {}))
    assert mine["data"]["scenarios"] == ["custom"]
    with pytest.raises(ToolFailed):
        run(graphtools.compare(ctx({"active": ["custom"]}), {}))  # the what-if without its inputs: nothing to run


def test_the_stream_lights_what_each_read():
    sel = {"selected": {"id": "EV:x>CL:stock", "kind": "edge", "label": "x"}}
    assert st.nodes_for("lien_ket", {}, sel) == ["EV:x", "CL:stock"]
    assert st.nodes_for("lien_ket", {"node": "GL:tuition"}, {}) == ["GL:tuition"]
    assert st.nodes_for("so_sanh_kich_ban", {}, {"active": ["vni_30", "rates_up"]}) == ["SC:vni_30", "SC:rates_up"]
    assert st.nodes_for("so_sanh_kich_ban", {"scenarios": ["lai_suat"]}, {}) == ["SC:rates_up"]


def test_a_turn_with_the_workspace_through_the_stream(app):  # noqa: F811
    g = {"lens": "muc-tieu", "selected": PICK, "active": ["vni_30", "rates_up"]}
    llm = ScriptedLLM(asks(("lien_ket", {})), asks(("so_sanh_kich_ban", {})), says("Đã xem."))
    ev = stream(app, llm, message="Mục này liên quan gì, và các kịch bản đang bật cùng lúc thì sao?", graph=g)
    start = {e["tool"]: e for e in ev if e["type"] == "step" and e["phase"] == "start"}
    end = {e["tool"]: e for e in ev if e["type"] == "step" and e["phase"] == "end"}
    assert start["lien_ket"]["nodes"] == ["GL:tuition"]
    assert start["so_sanh_kich_ban"]["nodes"] == ["SC:vni_30", "SC:rates_up"]
    assert end["lien_ket"]["ok"] and "goal:tuition" in end["lien_ket"]["focus"]
    assert end["so_sanh_kich_ban"]["ok"] and "scenario:rates_up" in end["so_sanh_kich_ban"]["focus"]
    a = ev[-1]["assistant"]
    assert a["status"] == "ok" and [s["tool"] for s in a["steps"]] == ["lien_ket", "so_sanh_kich_ban"]
    assert BODY["route"]  # the stream test's body, unchanged
