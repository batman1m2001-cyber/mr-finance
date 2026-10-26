"""The declaring chat as it happens (POST /api/declare/stream, FEAT-23): a tool starting and ending, the agent's words,
a form when it asks back, then the same turn as the JSON door — and the rules when no model answers. Offline: a
scripted model (operonx-agents testing)."""

import json

import pytest
from operonx.app import Application
from operonx_agents.testing import ScriptedLLM, asks, says, scripted
from starlette.testclient import TestClient

from wealth import store

BODY = {"client_id": "C05", "session_id": "C05-web"}


@pytest.fixture
def app():  # one per test: a served app's lifespan starts once
    return Application.find(".").asgi()


def stream(app, llm=None, **body):
    def go():
        with TestClient(app) as c:
            r = c.post("/api/declare/stream", json={**BODY, **body}, headers={"accept": "text/event-stream"})
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream"), r.text[:300]
        return r.text

    if llm is None:
        text = go()
    else:
        with scripted(assistant=llm):
            text = go()
    events = []
    for block in text.split("\n\n"):
        data = [ln[5:].strip() for ln in block.splitlines() if ln.startswith("data:")]
        if data:
            item = json.loads("\n".join(data))
            events.append(item.get("event", item) if isinstance(item, dict) else item)
    return events


def test_a_turn_streams_its_step_and_words_then_the_turn_and_writes_once(app, monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    llm = ScriptedLLM(asks(("declare_gold", {"luong": 5})), says("Dạ, em đã ghi 5 lượng vàng."))
    ev = stream(app, llm, message="Nhà tôi có 5 lượng vàng")
    assert ev[0]["type"] == "start"
    steps = [(e["phase"], e["tool"]) for e in ev if e["type"] == "step"]
    assert steps == [("start", "declare_gold"), ("end", "declare_gold")]
    assert "".join(e["text"] for e in ev if e["type"] == "text") == "Dạ, em đã ghi 5 lượng vàng."
    (answer,) = [e for e in ev if e["type"] == "answer"]
    turn = answer["turn"]
    assert (turn["method"], turn["reply"], [r["kind"] for r in turn["recorded"]]) == (
        "ai", "Dạ, em đã ghi 5 lượng vàng.", ["asset"]
    )
    assert [a["qty"] for a in store.profile("C05", "asset")] == [5]


def test_several_missing_details_come_back_as_a_form_and_nothing_is_written(app, monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    ask = {
        "title": "Căn nhà ở Quận 7",
        "fields": [
            {"label": "Giá trị hiện tại", "kind": "money", "unit": "tỷ"},
            {"label": "Diện tích", "kind": "number", "unit": "m²"},
            {"label": "Đang cho thuê?", "kind": "choice", "options": ["Có", "Không"]},
            {"label": "", "kind": "text"},  # no label: dropped
            {"label": "Năm mua", "kind": "date"},  # an unknown kind: a text blank
        ],
    }
    llm = ScriptedLLM(asks(("hoi_them", ask)), says("Anh/chị điền giúp em mấy thông tin này nhé."))
    ev = stream(app, llm, message="Tôi có một căn nhà ở Quận 7")
    (form,) = [e["form"] for e in ev if e["type"] == "form"]
    assert form["title"] == "Căn nhà ở Quận 7"
    assert [(f["label"], f["kind"]) for f in form["fields"]] == [
        ("Giá trị hiện tại", "money"), ("Diện tích", "number"), ("Đang cho thuê?", "choice"), ("Năm mua", "text")
    ]
    assert form["fields"][2]["options"] == ["Có", "Không"]
    turn = ev[-1]["turn"]
    assert turn["recorded"] == [] and turn["method"] == "ai" and store.profile("C05", "asset") == []


def test_without_a_model_the_rules_answer_on_the_stream(app):
    ev = stream(app, message="Nhà tôi có 10 lượng vàng")
    assert [e["type"] for e in ev] == ["start", "answer"]
    turn = ev[-1]["turn"]
    assert turn["method"] == "rules" and turn["recorded"][0]["data"]["qty"] == 10


def test_when_the_model_fails_before_writing_the_rules_record(app, monkeypatch):
    monkeypatch.setenv("MF_AI", "on")

    def down(messages, params):
        raise ConnectionError("gateway unreachable")

    ev = stream(app, ScriptedLLM(down), message="Nhà tôi có 10 lượng vàng")
    turn = ev[-1]["turn"]
    assert turn["method"] == "rules" and [a["qty"] for a in store.profile("C05", "asset")] == [10]


def test_a_bad_request_is_an_error_event_and_runs_nothing(app):
    assert stream(app, message="  ") == [{"type": "error", "text": "an empty message"}]


def test_details_given_later_fill_in_the_item_instead_of_adding_a_second(app, monkeypatch):
    """On 2026-10-26 "Khoảng 12 tỷ, 95 m2", said after "một căn nhà ở Quận 7", became a second house."""
    monkeypatch.setenv("MF_AI", "on")
    home = {"name": "Căn nhà ở Quận 7", "location": "Quận 7"}
    stream(app, ScriptedLLM(asks(("declare_property", home)), says("Dạ.")), message="Tôi có một căn nhà ở Quận 7")
    ev = stream(
        Application.find(".").asgi(),  # a second turn: a second app (a served app's lifespan starts once)
        ScriptedLLM(asks(("declare_property", {**home, "value_ty": 12, "sqm": 95})), says("Dạ, em đã cập nhật.")),
        message="Khoảng 12 tỷ, 95 m2",
    )
    (house,) = store.profile("C05", "asset")
    assert (house["value"], house["sqm"], house["location"]) == (12e9, 95, "Quận 7")
    assert [r["data"]["id"] for r in ev[-1]["turn"]["recorded"]] == [house["id"]]  # this turn's write: the book redraws


def test_a_house_with_its_size_in_a_priced_area_tells_the_agent_the_books_value(app, monkeypatch):
    """On 2026-10-26 the reply said 12 tỷ while the book showed 9,025,000,000 (95 m² at the area's price)."""
    monkeypatch.setenv("MF_AI", "on")
    home = {"name": "Căn nhà Phú Mỹ Hưng", "location": "Phú Mỹ Hưng, Quận 7", "value_ty": 12, "sqm": 95}
    llm = ScriptedLLM(asks(("declare_property", home)), says("Dạ."))
    stream(app, llm, message="Nhà Phú Mỹ Hưng 95 m2, 12 tỷ")
    (house,) = store.profile("C05", "asset")
    assert (house["value"], house["sqm"], house["area"]) == (12e9, 95, "phu_my_hung")
    told = str(llm.requests[-1]["messages"][-1])
    assert "Sổ tài sản định giá theo giá khu vực" in told and "12 tỷ. Sổ tài sản" in told and "9,03 tỷ" in told, told
