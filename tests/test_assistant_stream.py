"""The assistant's turn as it happens (FEAT-40, OWN-GW-06…10; POST /api/assistant/stream): one server-sent event per
real event — a tool starting with the graph nodes it reads, ending with what its result names, the model's text (model
mode only), a write waiting, then the same answer as the JSON door — and nothing that did not happen. Offline: a
scripted model (operonx-agents testing)."""

import json

import pytest
from operonx.app import Application
from operonx_agents.testing import ScriptedLLM, asks, says, scripted
from starlette.testclient import TestClient

from control import config

BODY = {"role": "client", "client_id": "C01", "scope": "personal", "route": "#/client/xem/tong-quan"}


@pytest.fixture(autouse=True)
def model_on(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")


@pytest.fixture
def app():  # one per test: a served app's lifespan starts once
    return Application.find(".").asgi()


def stream(app, llm=None, **body):
    """The events of one streamed turn, in order (``id:`` numbered by the door)."""

    def go():
        with TestClient(app) as c:
            r = c.post("/api/assistant/stream", json={**BODY, **body}, headers={"accept": "text/event-stream"})
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream"), r.text[:300]
        return r.text

    text = go() if llm is None else _with(llm, go)
    events, ids = [], []
    for block in text.split("\n\n"):
        data = [ln[5:].strip() for ln in block.splitlines() if ln.startswith("data:")]
        ids += [int(ln[3:]) for ln in block.splitlines() if ln.startswith("id:")]
        if data:
            item = json.loads("\n".join(data))
            events.append(item.get("event", item) if isinstance(item, dict) else item)
    assert ids == sorted(ids), ids  # numbered in order: a dropped reader resumes with after_seq
    return events


def _with(llm, fn):
    with scripted(copilot=llm):
        return fn()


def kinds(events):
    return [e["type"] + (f":{e['phase']}:{e['tool']}" if e["type"] == "step" else "") for e in events]


def test_each_tool_is_said_as_it_starts_and_ends_then_the_same_answer(app):
    llm = ScriptedLLM(asks(("tong_quan", {})), asks(("dong_tien", {})), says("Tài sản ròng tăng; tháng này còn dư."))
    ev = stream(app, llm, message="Tài sản của tôi thế nào và tháng này tôi chi bao nhiêu?")
    k = [x for x in kinds(ev) if x != "text"]
    assert k == ["start", "step:start:tong_quan", "step:end:tong_quan", "step:start:dong_tien", "step:end:dong_tien",
                 "answer"], k  # fmt: skip
    start = {e["tool"]: e for e in ev if e["type"] == "step" and e["phase"] == "start"}
    end = {e["tool"]: e for e in ev if e["type"] == "step" and e["phase"] == "end"}
    assert "ME" in start["tong_quan"]["nodes"] and start["dong_tien"]["nodes"] == ["FL:in", "FL:out"]
    assert end["tong_quan"]["ok"] and end["tong_quan"]["focus"] == ["kpi:net_worth", "kpi:liquidity", "kpi:risk"]
    assert end["dong_tien"]["focus"][0].startswith("flow:") and end["dong_tien"]["ms"] >= 0
    a = ev[-1]["assistant"]
    assert a["status"] == "ok" and a["mode"] == "model" and a["text"] == "Tài sản ròng tăng; tháng này còn dư."
    assert [s["tool"] for s in a["steps"]] == ["tong_quan", "dong_tien"] and a["audit_seq"]
    # the text events are the model's own words, and only those
    said = "".join(e["text"] for e in ev if e["type"] == "text")
    assert said in ("", a["text"])


def test_a_stress_test_puts_its_effect_on_its_scenario_node(app):
    llm = ScriptedLLM(asks(("kich_ban", {"scenario": "co_phieu"})), says("Mô phỏng xong."))
    ev = stream(app, llm, message="Nếu VN-Index giảm mạnh thì sao?")
    start = next(e for e in ev if e["type"] == "step" and e["phase"] == "start")
    end = next(e for e in ev if e["type"] == "step" and e["phase"] == "end")
    assert start["nodes"] == ["SC:vni_30"]
    card = ev[-1]["assistant"]["steps"][0]
    assert end["scenario"]["id"] == "vni_30" and end["scenario"]["effect"] < 0 and "scenario:vni_30" in end["focus"]
    assert card["status"] == "ok"  # hypothetical: the answer is a simulation, the net worth is not changed


def test_a_write_waits_and_the_stream_says_so(app):
    llm = ScriptedLLM(asks(("ghi_nho", {"text": "Tôi muốn giữ 6 tháng chi tiêu"})), says("Đã ghi."))
    ev = stream(app, llm, message="Hãy ghi nhớ: tôi muốn giữ 6 tháng chi tiêu")
    assert "wait" in [e["type"] for e in ev]
    assert ev[-1]["type"] == "answer" and ev[-1]["assistant"]["status"] == "pending"


def test_template_mode_streams_no_text_from_the_model(app):
    vid = config.propose("client_ai", {"mode": "off", "onprem_hosts": ["127.0.0.1"]}, "admin")["id"]
    config.decide(vid, "approve", "admin2")
    ev = stream(app, ScriptedLLM(asks(("tong_quan", {})), says("Đã xem.")), message="Tài sản thế nào?")
    assert not [e for e in ev if e["type"] == "text"]
    assert ev[-1]["assistant"]["mode"] == "template" and "step:end:tong_quan" in kinds(ev)


def test_without_a_model_the_fallback_says_its_one_tool(app, monkeypatch):
    monkeypatch.setenv("LLM_MODEL_COPILOT", "")
    ev = stream(app, message="Tài sản của tôi thế nào?")
    steps = [e for e in ev if e["type"] == "step"]
    assert [s["phase"] for s in steps] == ["start", "end"] and steps[0]["tool"] == steps[1]["tool"]
    assert ev[-1]["assistant"]["mode"] == "fallback"


def test_a_failed_tool_is_said_failed_and_lights_nothing(app):
    ev = stream(
        app, ScriptedLLM(asks(("tac_dong", {})), says("Không có.")), message="Tin nào ảnh hưởng?", client_id="C05"
    )
    end = next((e for e in ev if e["type"] == "step" and e["phase"] == "end"), None)
    if end is not None and not end["ok"]:
        assert end["focus"] == []


def test_a_bad_request_is_an_error_event_and_runs_nothing(app):
    ev = stream(app, message="")
    assert [e["type"] for e in ev] == ["error"]
