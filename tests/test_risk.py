import asyncio
import random

from operonx import Operon

from dashboard.graph import dashboard_flow
from risk import _bank
from risk.graph import risk_flow
from wealth import fixtures, store

ENGINE = Operon(risk_flow, params={"client_id": None, "answers": None})


def step(client_id, answers):
    out = asyncio.run(ENGINE.run(inputs={"client_id": client_id, "answers": answers}))
    assert "$errors" not in out, out["$errors"]
    return out["reply"]


def take(client_id, choose):
    answers, asked = {}, []
    while True:
        r = step(client_id, answers)
        if "result" in r:
            return r["result"], asked
        q = r["question"]
        asked.append(q["id"])
        answers[q["id"]] = choose(q)


def test_a_fearful_answer_asks_about_a_smaller_fall_a_calm_one_about_a_crash():
    ctx = {"age": 45}
    assert _bank.next_id({"goal": "grow", "horizon": "5to10", "drop20": "sell_all"}, ctx) == "drop5"
    assert _bank.next_id({"goal": "grow", "horizon": "5to10", "drop20": "buy"}, ctx) == "drop35"
    assert _bank.next_id({"goal": "nonsense"}, ctx) == "goal", "a wrong option is asked again"


def test_only_a_business_owner_is_asked_about_the_business():
    base = {
        "goal": "grow",
        "horizon": "5to10",
        "drop20": "hold",
        "drop35": "hold",
        "bet_bold": "b",
        "experience": "lt3",
        "leverage": "never",
        "income": "stable",
    }
    assert _bank.next_id(base, {"owns_business": True, "age": 55}) == "business"
    assert _bank.next_id(base, {"owns_business": False, "dependents": 2, "age": 45}) == "big_expense"
    assert _bank.next_id(base, {"owns_business": False, "dependents": 0, "age": 50}) is None


def test_every_path_asks_8_to_12_questions():
    rng = random.Random(7)
    for cid in fixtures.client_ids():
        for _ in range(6):
            res, asked = take(cid, lambda q: rng.choice(q["options"])["id"])
            assert 8 <= len(asked) <= 12, (cid, asked)
            assert res["questions"] == len(asked)


def test_the_drop_question_uses_the_client_s_own_portfolio():
    r = step("C01", {"goal": "grow", "horizon": "5to10"})
    assert r["question"]["id"] == "drop20" and "tỷ" in r["question"]["text"]


def test_a_cautious_retiree_gets_a_cautious_profile():
    res, _ = take("C04", lambda q: q["options"][0]["id"])
    assert res["persona"] == "Nghỉ hưu"
    assert res["profile"]["level"] == 1 and res["drawdown_limit"] == 0.05


def test_who_says_bold_but_sold_in_the_dip_is_stepped_down():
    res, _ = take("C03", lambda q: q["options"][-1]["id"])
    assert res["persona"] == "F2" and res["tolerance_level"] == 5
    assert any("nói và làm chưa khớp" in w for w in res["warnings"])
    assert res["profile"]["level"] == min(4, res["capacity_level"])


def test_wanting_more_than_one_can_bear_is_said_out_loud():
    res, _ = take("C05", lambda q: q["options"][-1]["id"])
    assert res["capacity_level"] < res["tolerance_level"]
    assert res["warnings"][0].startswith("Anh/chị muốn rủi ro mức")


def test_the_result_sets_the_dashboard_s_drawdown_limit():
    res, _ = take("C04", lambda q: q["options"][0]["id"])
    assert store.result("C04", "risk")["drawdown_limit"] == 0.05
    board = asyncio.run(
        Operon(dashboard_flow, params={"client_id": None, "scope": None, "months": None}).run(
            inputs={"client_id": "C04", "scope": "personal", "months": 12}
        )
    )["dashboard"]
    assert board["risk"]["limit"] == 0.05 and board["profile"]["risk_persona"] == "Nghỉ hưu"
