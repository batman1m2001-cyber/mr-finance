"""The real-model eval's grader (scripts/eval_assistant.py) — free; the eval itself costs money (ADR-0034)."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("eval_assistant", Path(__file__).parents[1] / "scripts/eval_assistant.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)


@pytest.mark.parametrize(
    "said",
    [
        "Tôi không đặt được vé máy bay.",  # A8 run 1 graded this a non-refusal
        "Tôi không thể duyệt đề xuất ở phiên này.",
        "Việc này ngoài phạm vi của OneWealth.",
        "Tôi không có quyền duyệt.",
    ],
)
def test_a_refusal_in_its_own_words_is_a_refusal(said):
    assert ev.REFUSAL.search(said)


def test_an_answer_is_not_a_refusal():
    assert not ev.REFUSAL.search("Tháng này bạn chi 90,4 triệu, lớn nhất là trả nợ vay 38,0 triệu.")


def test_a_later_turn_may_repeat_the_numbers_an_earlier_turn_read():
    case = {"expect": {}, "message": "Tháng này tôi chi bao nhiêu?", "turns": ["Nên cắt khoản nào?"]}
    read = "Chi ra 90,4 triệu; lớn nhất: trả nợ vay 38,0 triệu"
    first = {"mode": "model", "steps": [{"tool": "dong_tien", "text": read}]}
    last = {"mode": "model", "text": "Khoản lớn nhất là trả nợ vay 38,0 triệu.", "steps": []}
    assert ev.check(case, last) == ["numbers not from the tools: ['38,0 triệu']"]
    assert ev.check(case, last, [first]) == []


def test_a_number_worked_out_from_the_tools_is_not_grounded():
    case = {"expect": {}, "message": "Tháng này tôi chi bao nhiêu?"}
    read = "Chi ra 90,4 triệu; trả nợ vay 38,0 triệu"
    a = {"mode": "model", "text": "Còn lại 52,4 triệu.", "steps": [{"text": read}]}
    assert ev.check(case, a) == ["numbers not from the tools: ['52,4 triệu']"]
