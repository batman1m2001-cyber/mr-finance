"""Regressions from the assistant stress test (docs/ASSISTANT_STRESS_PLAN.md; defects in
docs/brd/testing/assistant/defects.md): each test names the defect it holds fixed."""

import asyncio

import pytest

from assistant import registry
from assistant.base import Ctx, ToolFailed
from assistant.tools import _vnd
from assistant.turn import FACTS_MODEL, graph_line


def run(coro):
    return asyncio.run(coro)


def ctx(role="client", client="C01", **kw):
    return Ctx(role=role, client_id=client, scope="personal", question="", user=registry.DEMO_USER[role], **kw)


def calc(expression, what=""):
    return run(registry.REGISTRY["tinh"].run(ctx(), {"expression": expression, "what": what}))


def test_d02_the_overview_names_total_assets_and_every_debt():
    """D02: asked for total assets and debt, the assistant had only net worth to read."""
    out = run(registry.REGISTRY["tong_quan"].run(ctx(), {}))
    d, text = out["data"], out["text"]
    assert d["assets"] - d["liabilities"] == d["net_worth"] and d["liabilities"] > 0
    assert f"= tổng tài sản {_vnd(d['assets'])} − nợ {_vnd(d['liabilities'])} (Vay mua nhà Thảo Điền " in text
    assert "Dư nợ thẻ Visa Signature" in text and "Phân bổ tài sản: Bất động sản " in text


def test_d03_a_calculation_is_a_tool_result_with_its_formula():
    """D03: the assistant refused to compute (no tool, a rule against arithmetic) and left a placeholder."""
    out = calc("1000000000/1.04**10", "sức mua sau 10 năm")
    assert out["text"] == "sức mua sau 10 năm: 1000000000/1.04**10 = 675.564.169"
    assert calc("2445/45971*100")["text"].endswith("= 5,32")
    assert calc("37 - 40")["text"].endswith("= -3")
    assert calc("1,5 * 2")["data"]["value"] == 3.0  # a Vietnamese decimal comma
    assert calc("3 × 4 ÷ 2")["data"]["value"] == 6.0
    assert "tinh" in FACTS_MODEL and "không tính nhẩm" in FACTS_MODEL


@pytest.mark.parametrize("bad", ["__import__('os').system('id')", "abs(-1)", "x + 1", "9 ** 9999", "1/0", "", "[1]"])
def test_d03_the_calculator_runs_arithmetic_only(bad):
    with pytest.raises(ToolFailed):
        calc(bad)


def test_d03_every_role_has_the_calculator():
    for role in ("client", "rm", "cio", "compliance", "specialist", "admin"):
        assert "tinh" in {t.name for t in registry.agent_tools(role)}


def test_d01_this_node_is_the_picked_one_not_a_button():
    """D01: “Nút này nói gì?” with a goal picked was read as a button of the interface."""
    g = {"lens": "muc-tieu", "selected": {"id": "GL:tuition", "kind": "goal", "label": "Học phí cho con"}}
    line = graph_line(ctx(graph=g))
    assert "“nút này”" in line and "không phải nút bấm" in line and "lien_ket" in line
