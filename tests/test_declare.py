import asyncio

from operonx import Operon
from operonx.agents.testing import ScriptedLLM, asks, says, scripted

from consolidate.graph import consolidate_flow
from declare import _rules
from declare.graph import declare_flow
from wealth import store
from wealth.money import TR, TY

PARAMS = {"client_id": None, "message": None, "session_id": None}


def say(message, client_id="C05"):
    out = asyncio.run(
        Operon(declare_flow, params=PARAMS).run(
            inputs={"client_id": client_id, "message": message, "session_id": f"{client_id}-t"}
        )
    )
    assert "$errors" not in out or all(e.get("handled") for e in out["$errors"].values()), out.get("$errors")
    return out["turn"]


def test_the_rules_read_the_sentences_the_demo_needs():
    (home,) = _rules.parse("Tôi có 1 căn ở Thảo Điền mua 2019 giá 8 tỷ")
    want = {"class": "real_estate", "area": "thao_dien", "purchase_year": 2019, "value": 8 * TY}
    assert {k: home["data"][k] for k in want} == want
    assert _rules.parse("Nhà tôi có 10 lượng vàng") == [
        {"kind": "asset", "data": {"class": "gold", "name": "Vàng (tự khai)", "qty": 10.0}}
    ]
    kids = _rules.parse("Tôi có 2 con, 14 tuổi và 10 tuổi")
    assert [k["data"]["birth_year"] for k in kids] == [2012, 2016]
    (loan,) = _rules.parse("Tôi đang nợ 500 triệu, trả 12 triệu mỗi tháng")
    assert (loan["data"]["value"], loan["data"]["monthly_payment"]) == (500 * TR, 12 * TR)
    assert _rules.money("1,5 tỷ và 850 triệu") == [1.5 * TY, 850 * TR]
    assert _rules.parse("Thời tiết hôm nay đẹp") == []


def test_a_turn_records_what_was_said_and_the_picture_grows():
    before = _net("C05")
    turn = say("Tôi có 1 căn ở Thảo Điền mua 2019 giá 8 tỷ")
    assert turn["method"] == "rules" and [r["kind"] for r in turn["recorded"]] == ["asset"]
    assert "Thảo Điền" in turn["reply"]
    assert _net("C05") == before + 8 * TY


def test_nothing_recognised_records_nothing_and_says_how_to_put_it():
    turn = say("Thời tiết hôm nay đẹp")
    assert turn["recorded"] == [] and "Thảo Điền" in turn["reply"]


def test_the_agent_records_through_its_tools(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    model = ScriptedLLM(
        asks(
            ("declare_gold", {"luong": 5}),
            ("declare_dependent", {"name": "Bảo", "relation": "Con", "birth_year": 2021}),
        ),
        says("Đã ghi 5 lượng vàng và con Bảo."),
    )
    with scripted(assistant=model):
        turn = say("Tôi có 5 lượng vàng, con tôi tên Bảo sinh 2021")
    assert (turn["method"], turn["reply"]) == ("ai", "Đã ghi 5 lượng vàng và con Bảo.")
    assert sorted(r["kind"] for r in turn["recorded"]) == ["asset", "dependent"]
    assert store.profile("C05", "asset")[0]["qty"] == 5
    # the client is the run's deps: the tool wrote for C05, not anyone else
    assert store.profile("C01") == []


def test_when_the_agent_cannot_answer_the_rules_still_record(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")

    def down(messages, params):
        raise ConnectionError("gateway unreachable")

    with scripted(assistant=ScriptedLLM(down)):
        turn = say("Nhà tôi có 10 lượng vàng")
    assert turn["method"] == "rules" and turn["recorded"][0]["data"]["qty"] == 10


def _net(client_id):
    out = asyncio.run(
        Operon(consolidate_flow, params={"client_id": None, "scope": None}).run(
            inputs={"client_id": client_id, "scope": "personal"}
        )
    )
    hs = out["holdings"]
    return sum(h["value"] for h in hs if h["kind"] == "asset") - sum(h["value"] for h in hs if h["kind"] == "liability")


def test_land_with_its_size_is_valued_by_its_area():
    (land,) = _rules.parse("Tôi có 1 mảnh đất 500m2 ở Long Thành mua 2019 giá 3 tỷ")
    assert {k: land["data"][k] for k in ("area", "sqm", "purchase_price", "value")} == {
        "area": "long_thanh",
        "sqm": 500.0,
        "purchase_price": 3 * TY,
        "value": None,
    }
    say("Tôi có 1 mảnh đất 500m2 ở Long Thành mua 2019 giá 3 tỷ")
    held = asyncio.run(
        Operon(consolidate_flow, params={"client_id": None, "scope": None}).run(
            inputs={"client_id": "C05", "scope": "personal"}
        )
    )["holdings"]
    (row,) = [h for h in held if h["source"] == "declared" and h["class"] == "real_estate"]
    assert row["value"] == 500 * 18 * TR and row["cost"] == 3 * TY
