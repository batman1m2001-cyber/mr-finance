"""The data room eval's grader and cases (scripts/eval_assistant_data.py, data/assistant_data_eval.json) — free; the
eval itself costs money (docs/ASSISTANT_DATA_PLAN.md D5)."""

import asyncio
import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest

from assistant import dataroom, registry
from assistant.base import Ctx

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("eval_assistant_data", ROOT / "scripts/eval_assistant_data.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)
CASES = json.loads((ROOT / "data/assistant_data_eval.json").read_text())


def gold(rows, columns=("v",)):
    return {"gold": {"columns": list(columns), "rows": rows, "total": len(rows)}}


@pytest.mark.parametrize(
    "text, value",
    [
        ("Có 1.420 tin chờ xử lý.", 1420),
        ("Có 1420 tin.", 1420),
        ("Tổng tài sản khoảng 48,4 tỷ đồng.", 48_384_000_000.0),
        ("Tổng là 48.384.000.000 VND.", 48_384_000_000.0),
        ("Còn thiếu 3,53 tỷ.", 3_530_000_000.0),
        ("Bạn chi 90,4 triệu.", 90_393_000.0),
        ("Bất động sản chiếm 66,2%.", 66.2),
        ("Trung bình 115 triệu mỗi tháng.", 115_497_083.0),
    ],
)
def test_a_number_is_read_with_its_unit_and_separators(text, value):
    assert ev.correct({"want": "v", **gold([[value]])}, text)


def test_a_count_must_be_exact_and_a_near_number_is_wrong():
    assert not ev.correct({"want": "v", **gold([[1420]])}, "Có 1.415 tin chờ xử lý.")
    assert not ev.correct({"want": "v", **gold([[48_384_000_000.0]])}, "Khoảng 47 tỷ.")  # 3 % off


def test_none_is_zero_or_said_as_none():
    for text in ("Có 0 yêu cầu.", "Hiện không có yêu cầu nào đang chờ duyệt."):
        assert ev.correct({"want": "none", **gold([[0]])}, text)
        assert ev.correct({"want": "v", **gold([[0]])}, text)
    assert not ev.correct({"want": "none", **gold([[0]])}, "Có 2 yêu cầu.")


def test_names_match_without_diacritics_and_every_cell_of_a_row():
    goals = [["Học phí cho con (trong nước / du học)"], ["Mua thêm BĐS bằng vốn vay"]]
    t = {"want": "col:ten:all", **gold(goals, ["ten"])}
    assert ev.correct(t, "Hai mục tiêu: Học phí cho con và Mua thêm BĐS bằng vốn vay.")
    assert not ev.correct(t, "Chỉ có Học phí cho con.")
    row = {"want": "row", **gold([["Đỗ Thị Hạnh", 63]], ["ten", "tuoi"])}
    assert ev.correct(row, "Khách lớn tuổi nhất là Đỗ Thị Hạnh, 63 tuổi.") and not ev.correct(row, "Đỗ Thị Hạnh.")


def test_the_cases_are_thirty_a_role_with_todays_chat_and_a_dispute_each():
    turns = Counter(c["role"] for c in CASES["cases"] for _ in c["turns"])
    assert set(turns) == {"cio", "rm", "client"} and all(n >= 28 for n in turns.values()), turns
    assert CASES["cases"][0]["turns"][0]["q"] == "Hệ thống đã lấy về bao nhiêu tin?"  # the CIO's 2026-10-24 chat
    assert CASES["cases"][0]["turns"][1]["q"].startswith("Sao lại 200?")
    disputed = {c["role"] for c in CASES["cases"] for t in c["turns"] if t.get("dispute")}
    assert disputed == {"cio", "rm", "client"}
    assert len({c["id"] for c in CASES["cases"]}) == len(CASES["cases"])
    assert CASES["gate"]["accuracy"] >= 0.9 and CASES["gate"]["seconds_p95"] <= 6
    assert CASES["gate"]["cost_per_turn_usd"] <= 0.01


def test_every_gold_sql_runs_in_its_roles_room():
    for c in CASES["cases"]:
        ctx = Ctx(role=c["role"], client_id=c["client_id"], scope="personal", question="",
                  user=registry.DEMO_USER.get(c["role"]))  # fmt: skip
        for t in c["turns"]:
            r = asyncio.run(dataroom.query(ctx, t["sql"]))
            assert r["columns"], (c["id"], t["sql"])
            if t["want"].startswith("col:"):
                assert t["want"].split(":")[1] in r["columns"], (c["id"], t["want"])


def test_a_guess_why_is_flagged_and_where_to_add_is_not():
    for said in ("có thể bạn đang nhớ số khác", "có thể hai gia đình còn lại chưa nằm trong bảng",
                 "Bạn có thể kiểm tra lại sao kê", "Có lẽ do trang khác tính cả tin đã gom"):  # fmt: skip
        assert ev.GUESS.search(said), said
    for said in ("Nếu bạn có khoản tiền gửi nào khác, bạn có thể bổ sung trên trang Tài sản", "tôi có thể liệt kê"):
        assert not ev.GUESS.search(said), said
