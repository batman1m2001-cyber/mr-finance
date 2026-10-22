"""Regressions from the assistant stress test (docs/ASSISTANT_STRESS_PLAN.md; defects in
docs/brd/testing/assistant/defects.md): each test names the defect it holds fixed."""

import asyncio
import re

import pytest

from assistant import registry
from assistant.base import Ctx, ToolFailed
from assistant.graphtools import ASSUMED
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


def test_d08_each_allocation_group_carries_its_amount_not_only_a_rounded_share():
    """D08: “trái phiếu 3% × 45,97 tỷ ≈ 1,38 tỷ” — the share was rounded to a whole percent; the group held 1,50 tỷ."""
    from assistant.tools import _pct

    out = run(registry.REGISTRY["tong_quan"].run(ctx(), {}))
    from assistant.base import run_graph
    from dashboard.graph import dashboard_flow

    d = run(run_graph(dashboard_flow, client_id="C01", scope="personal"))["dashboard"]
    for a in d["allocation"]:
        assert f"{a['group']} {_vnd(a['value'])} ({_pct(a['share'], 0)})" in out["text"]


def test_d07_a_reply_has_room_for_the_models_reasoning_and_is_asked_to_be_short():
    """D07: max_tokens 1 200 cut general-knowledge answers mid-sentence (finish_reason "length", measured)."""
    from assistant import turn

    assert turn.ANSWER_TOKENS >= 2400 and turn.agent("client").settings.max_tokens == turn.ANSWER_TOKENS
    assert "dưới\n150 chữ" in turn.RULES


def test_d09_the_paid_web_search_is_not_for_general_knowledge():
    """D09: “Vàng có phải kênh trú ẩn an toàn?” spent US$0.023 on a web search the description invited."""
    d = registry.REGISTRY["tim_tren_web"].description
    assert "kiến thức chung" not in d and "tốn phí" in d and "phổ thông thì tự trả lời" in d


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


def test_d04_a_model_outage_is_not_blamed_on_the_wording():
    """D04: with the provider down, an unmatched question was answered “Tôi chưa hiểu câu hỏi này”."""
    from assistant import ops

    r = {"role": "client", "client_id": "C01", "scope": "personal", "message": "Viết giúp tôi một bài thơ về mùa thu",
         "route": "", "followed": None, "approvals": None}  # fmt: skip
    out = run(ops.fallback(r, "mô hình lỗi (ModelError)"))
    assert out["status"] == "unknown" and out["mode"] == "fallback"
    assert "Trợ lý AI hiện không trả lời được" in out["text"] and "chưa hiểu" not in out["text"]
    assert out["suggest"]  # what still works is listed


def test_d06_a_turns_steps_are_its_own_not_the_conversations(monkeypatch):
    """D06: each answer listed every tool call of the conversation so far as its own steps (the panel's “Các bước”,
    a conversation opened again)."""
    from operonx import Operon
    from operonx_agents.testing import ScriptedLLM, asks, says, scripted

    from assistant.graph import assistant_flow

    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")
    inputs = ("message", "role", "client_id", "scope", "route", "turn_id", "approvals", "conversation_id")
    engine = Operon(assistant_flow, params={k: None for k in inputs})

    def ask(message, cid=None):
        out = run(engine.run(inputs={"message": message, "role": "client", "client_id": "C01", "scope": "personal",
                                     "route": "#/client/tong-quan", "conversation_id": cid}))  # fmt: skip
        assert "$errors" not in out, out["$errors"]
        return out["assistant"]

    llm = ScriptedLLM(asks(("tong_quan", {})), says("Một."), asks(("dong_tien", {})), says("Hai."), says("Ba."))
    with scripted(copilot=llm):
        first = ask("Tài sản của tôi?")
        second = ask("Dòng tiền?", first["conversation_id"])
        third = ask("Cảm ơn.", first["conversation_id"])
    assert [s["tool"] for s in first["steps"]] == ["tong_quan"]
    assert [s["tool"] for s in second["steps"]] == ["dong_tien"]
    assert third["steps"] == [] and third["text"] == "Ba."


def test_d10_the_goals_tool_says_what_each_goal_needs_has_and_asks_a_month():
    """D10: “Mỗi tháng tôi cần để dành bao nhiêu?” — the goals tool told the model only each goal's status."""
    out = run(registry.REGISTRY["muc_tieu"].run(ctx(), {}))
    g = out["data"]["goals"]["tuition"]
    assert g["need"] and g["monthly"]
    assert (f"Học phí cho con (trong nước / du học): chậm tiến độ, cần {_vnd(g['need'])} ({g['by']}), có "
            f"{_vnd(g['have'])}") in out["text"]  # fmt: skip
    assert f"cần để dành {_vnd(g['monthly'])}/tháng" in out["text"] and "thiếu −" not in out["text"]


def test_d11_the_reserves_months_name_the_spending_they_are_counted_against():
    """D11: “đủ chi 3 năm” against a month that spent more: the basis (the profile's spending) was not said."""
    out = run(registry.REGISTRY["tong_quan"].run(ctx(), {}))
    assert "/tháng trong hồ sơ" in out["text"] and "(D11)" not in out["text"]
    # and the months themselves, to one decimal: without reasoning the model divided “3 năm” out itself (“32 tháng”)
    assert re.search(r"đủ chi \d+,\d tháng", out["text"]), out["text"]


def assume(**args):
    return run(registry.REGISTRY["gia_dinh"].run(ctx(), args))


def test_d12_a_what_if_said_in_words_runs_on_the_graphs_own_engine():
    """D12: “nhà đất giảm 20%” was answered with the 2022–2023 freeze scenario, “40%” by hand: the custom scenario
    (property, stocks, gold, rates, income) was reachable only from the graph."""
    from scenarios import _sim

    out = assume(nha_dat=-20)
    assert out["text"].startswith("Giả định của bạn: giá nhà đất −20%. Kịch bản của bạn: tài sản ròng ")
    assert out["data"]["assumed"]["real_estate"] == -0.2 and out["data"]["together"] < 0
    deeper = assume(nha_dat=-40)
    assert deeper["data"]["together"] < out["data"]["together"]  # a bigger fall costs more
    assert set(_sim.CUSTOM_LIMITS) == {k for k, _ in ASSUMED.values()}
    both = assume(co_phieu=-40, cung_luc=["lai_suat"])
    assert both["data"]["scenarios"] == ["custom", "rates_up"] and "Cùng lúc" in both["text"]
    assert "lãi vay thả nổi +3 điểm %/năm" in assume(lai_suat=3)["text"]


@pytest.mark.parametrize("bad", [{}, {"nha_dat": -60}, {"lai_suat": 9}, {"thu_nhap": 80}])
def test_d12_a_what_if_outside_its_bounds_is_refused_not_clipped(bad):
    with pytest.raises(ToolFailed):
        assume(**bad)


@pytest.fixture
def signed_in(monkeypatch):
    from operonx.app import Application
    from starlette.testclient import TestClient

    from people import auth

    monkeypatch.setenv("MF_AUTH", "on")
    monkeypatch.setenv("MF_DEMO_ACCOUNTS", "on")
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")
    with TestClient(Application.find(".").asgi()) as c:

        def post(who, path, payload, **kw):
            c.cookies.clear()
            c.cookies.set(auth.COOKIE, auth.issue(who))
            return c.post(path, json=payload, **kw)

        yield post


def c01_net_worth():
    out = run(registry.REGISTRY["tong_quan"].run(ctx(), {}))  # outside a request: unchecked, the reference figure
    return _vnd(out["data"]["net_worth"])


ASK = {"message": "Tài sản ròng của tôi bao nhiêu?", "role": "client", "scope": "personal",
       "route": "#/client/tong-quan", "conversation_id": None}  # fmt: skip


def test_d13_a_customer_naming_another_family_gets_nothing_of_it(signed_in):
    """D13 (S1): signed in as C02, a request naming client C01 was answered with C01's net worth, debts and
    holdings — the page API refused it (403); the assistant's tools ran their graphs nested, where no request was
    seen and nothing checked. Now a customer is always themselves (as their sessions already were)."""
    from operonx_agents.testing import ScriptedLLM, asks, says, scripted

    theirs = c01_net_worth()
    script = [x for _ in range(2) for x in (asks(("tong_quan", {})), says("Xong."))]
    with scripted(copilot=ScriptedLLM(*script)):
        r = signed_in("C02", "/api/assistant", {**ASK, "client_id": "C01"})
        s = signed_in(
            "C02", "/api/assistant/stream", {**ASK, "client_id": "C01"}, headers={"accept": "text/event-stream"}
        )
        cp = signed_in("C02", "/api/copilot", {"question": "Tài sản ròng?", "role": "client", "client_id": "C01"})
    for got in (r, s, cp):
        assert got.status_code == 200 and theirs not in got.text, got.text[:300]
    assert r.json()["assistant"]["steps"][0]["status"] == "ok"  # their own figures, read under their sign-in


def test_d13_staff_naming_a_family_not_theirs_are_refused(signed_in):
    from operonx_agents.testing import ScriptedLLM, asks, says, scripted

    theirs = c01_net_worth()
    with scripted(copilot=ScriptedLLM(asks(("tong_quan", {})), says("Xong."))):
        r = signed_in("rm02", "/api/assistant", {**ASK, "role": "rm", "client_id": "C01"})  # C01 is rm01's
        ok = signed_in("rm01", "/api/assistant", {**ASK, "role": "rm", "client_id": "C01"})
    assert r.status_code == 403 and "không được xem" in r.text and theirs not in r.text
    assert ok.status_code == 200 and ok.json()["assistant"]["steps"][0]["status"] == "ok"


def test_d13_a_tool_reading_another_family_inside_a_turn_is_refused(signed_in, monkeypatch):
    """D13, the second layer: a nested run is checked as the request around it, whatever family a tool reads."""
    from operonx_agents.testing import ScriptedLLM, asks, says, scripted

    from assistant import tools

    theirs = c01_net_worth()
    monkeypatch.setattr(tools, "_need_client", lambda ctx: "C01")  # a tool that names another family
    with scripted(copilot=ScriptedLLM(asks(("tong_quan", {})), says("Xong."))):
        r = signed_in("C02", "/api/assistant", {**ASK, "client_id": "C02"})
    a = r.json()["assistant"]
    assert r.status_code == 200 and a["steps"][0]["status"] == "failed"
    assert a["steps"][0]["text"] == "Không thực hiện được: Lê Văn Phát không được xem dữ liệu của khách hàng này"
    assert theirs not in r.text and "Traceback" not in r.text


def test_d13_a_customer_still_reads_their_own_family(signed_in):
    from operonx_agents.testing import ScriptedLLM, asks, says, scripted

    with scripted(copilot=ScriptedLLM(asks(("tong_quan", {})), says("Xong."))):
        r = signed_in("C02", "/api/assistant", {**ASK, "client_id": None})  # no client named: themselves
    a = r.json()["assistant"]
    assert a["status"] == "ok" and a["steps"][0]["status"] == "ok" and "Tài sản ròng" in a["steps"][0]["text"]


def flow(question, **args):
    c = ctx()
    c.question = question
    return run(registry.REGISTRY["dong_tien"].run(c, args))["data"]["month"]


def test_d14_a_month_merely_mentioned_is_not_the_month_shown():
    """D14: “Mình sắp sinh em bé vào tháng 3 năm sau” was answered with March of this year's cash flow: the tool
    took any “tháng N” in the question as the month to show."""
    latest = flow("Dòng tiền?", month="")
    assert flow("Mình sắp sinh em bé vào tháng 3 năm sau đó.", month="") == latest  # the model asked for none
    march = flow("Dòng tiền tháng 3?", month="2026-03")
    assert march == "2026-03" and flow("x", month="3/2026") == march and flow("x", month="03") == march
    # the keyword path (no model): the question's month, unless it is one still to come
    assert flow("Dòng tiền tháng 3?") == march
    assert flow("Mình sắp sinh em bé vào tháng 3 năm sau đó.") == latest
    assert flow("Chi tiêu tháng 3 năm nay?") == march


def test_d16_d17_the_overview_names_its_sources_and_what_the_stress_loss_is_made_of():
    """D16: “Những nguồn nào?” — only “21 khoản từ 7 nguồn”. D17: the stress loss (11,8%) against the −30% stocks
    scenario (4,2%): “hệ thống không giải thích được” — the largest contributors were not said."""
    out = run(registry.REGISTRY["tong_quan"].run(ctx(), {}))
    assert out["sources"][0].count(" khoản, ") >= 2  # each source by name, with its count and what it holds
    assert "Cách tính: mỗi khoản giảm theo mức sốc riêng của nó, tổng mất " in out["text"]
    assert "; lớn nhất: " in out["text"] and "(sốc " in out["text"]


def test_d19_d20_one_way_of_address_and_the_graph_is_a_page_to_open():
    """D19: “Em chưa tạo được… anh/chị cần…” — the assistant called itself and the person “em”. D20: asked to show a
    scenario on the graph, it opened the old impact graph: the workspace's lenses were no page it could open. Since
    ADR-0037 the client has no graph: the planning page is what it opens, by the bank's name."""
    from assistant import turn
    from assistant.tools import PAGES

    assert "gọi người dùng là “bạn”" in turn.RULES and "không dùng “anh/chị”" in turn.RULES  # D19 again in T2
    assert not [k for k, (_, r) in PAGES.items() if r.get("client", "").startswith("#/client/xem/")]
    out = run(registry.REGISTRY["mo_trang"].run(ctx(), {"page": "ke-hoach"}))
    assert out["navigate"] == "#/client/muc-tieu/ke-hoach" and out["text"] == "Mở trang Wealth Planning Advisor."


def test_d21_the_proposal_options_are_named_in_vietnamese_to_the_model():
    """D21: after a declined proposal the assistant offered “phương án nhẹ (light) hay nặng (heavy)”."""
    d = registry.REGISTRY["gui_de_xuat"].description
    assert "“phương án nhẹ”" in d and "“phương án mạnh”" in d and "tên tiếng Việt" in d


def test_d22_a_request_to_send_is_not_taken_for_an_approval_by_the_outage_fallback():
    """D22: provider down, a customer's “Gửi đề xuất … cho RM duyệt” matched the RM's approval tool by its word
    “duyệt”, and the customer was told “Vai trò Khách hàng không dùng được việc này; cần: RM”. A request to approve
    is still refused as one (tests/ui/test_copilot_ui.py)."""
    from assistant import ops

    r = {"role": "client", "client_id": "C01", "scope": "personal", "route": "", "followed": None, "approvals": None,
         "message": "Gửi đề xuất kịch bản cổ phiếu cho RM duyệt."}  # fmt: skip
    out = run(ops.fallback(r, "mô hình lỗi (ModelError)"))
    assert out["status"] == "unknown" and "Trợ lý AI hiện không trả lời được" in out["text"]
    assert "Vai trò" not in out["text"]
    rm = run(ops.fallback({**r, "role": "rm", "message": "Duyệt đề xuất này"}, "mô hình lỗi (ModelError)"))
    assert rm["steps"][0]["tool"] == "duyet_de_xuat" and "Vai trò" not in rm["text"]  # the RM's word, the RM's tool


class _Hub:
    def __init__(self, content, annotations):
        self.content, self.annotations = content, annotations

    def get(self, key):
        return self

    async def generate(self, **kw):
        from types import SimpleNamespace

        msg = SimpleNamespace(content=self.content, annotations=self.annotations)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage={"cost": 0.014})


@pytest.mark.parametrize(
    "content, annotations, sources",
    [
        ("Theo các nguồn tìm được, tỷ giá trung tâm là … Mức độ chắc chắn: trung bình.", [], []),
        (
            "Theo các nguồn tìm được, … (https://sbv.gov.vn/tygia). Mức độ chắc chắn: cao.",
            [],
            ["https://sbv.gov.vn/tygia"],
        ),
    ],
)
def test_d23_a_web_answer_without_links_says_it_is_unverified(monkeypatch, content, annotations, sources):
    """D23: “Tỷ giá USD/VND hôm nay?” came back “Theo các nguồn tìm được… mức chắc chắn trung bình” with no source at
    all: the provider sent no citations (oos-02 in T2; kn-04, kn-05 in T1)."""
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")
    monkeypatch.setattr("operonx.providers.ops._utils.resolve_hub", lambda: _Hub(content, annotations))
    out = run(registry.REGISTRY["tim_tren_web"].run(ctx(), {"q": "tỷ giá USD VND hôm nay"}))
    assert out["sources"] == sources
    assert ("không kèm đường dẫn nguồn" in out["text"]) == (not sources)


def test_d24_a_shock_at_a_planning_scenarios_level_runs_that_scenario():
    """D24: “Chứng khoán sập 30%” ran on the free what-if (flat −30 %: −1,66 tỷ; with rates +2 points −1,71 tỷ, loan
    interest only) where T1 had run the planning page's VN-Index −30 % (beta, funds, crypto: −1,82 tỷ; with rates
    +2 %: −3,87 tỷ). The model could not see that the levels matched: a description holds no digit."""
    k, g = registry.REGISTRY["kich_ban"].description, registry.REGISTRY["gia_dinh"].description
    for level in ("ba mươi phần trăm", "hai điểm phần trăm", "mười tám tháng", "năm phần trăm"):
        assert level in k
    assert "mức trùng thì dùng kich_ban" in g and "không định giá lại tài sản" in g
    # without reasoning the model did not look the levels up in kich_ban (latency report, 2026-10-18): they are said
    # here too, and a preset added to the one just run goes to the comparison
    s = registry.REGISTRY["so_sanh_kich_ban"].description
    assert "ba mươi phần trăm" in g and "so_sanh_kich_ban" in g and "co_phieu và lai_suat" in s


def test_d25_the_cash_flow_names_every_spending_group_and_income_source():
    """D25: “Vậy tôi nên cắt bớt khoản nào trước?” — “I don't have the data”: the cash-flow tool told the model only
    the largest group (the card showed five)."""
    out = run(registry.REGISTRY["dong_tien"].run(ctx(), {"month": None}))
    groups = out["text"].split("Các nhóm chi: ")[1].split(".")[0].split("; ")
    assert len(groups) == len(out["card"]["items"]) or len(groups) > len(out["card"]["items"]) >= 2
    assert "Nguồn tiền vào: " in out["text"]


def test_a_month_without_a_year_is_the_latest_one_with_data_and_the_model_knows_today():
    """“Dòng tiền tháng 9?” (progress list, 2026-10-18): the model asked for 2025-09 (it was not told the year) and the
    step failed; the data runs 2025-10…2026-09. It is told today's date, and to send the month alone."""
    from operonx_agents import RunContext

    from assistant.turn import instructions

    assert run(registry.REGISTRY["dong_tien"].run(ctx(), {"month": "09"}))["as_of"] == "2026-09"
    assert run(registry.REGISTRY["dong_tien"].run(ctx(), {"month": "11"}))["as_of"] == "2025-11"  # not the future
    assert "dạng MM;" in registry.REGISTRY["dong_tien"].params["month"].description
    today = __import__("datetime").date.today().strftime("%d/%m/%Y")
    assert f"Hôm nay: {today}." in instructions(RunContext(deps=ctx()))


def test_d26_a_role_is_offered_only_the_pages_it_can_open():
    """D26: a customer asking how fresh the data is was offered to open “Hệ thống”, an administrator's page."""
    import typing

    def pages(role):
        mo = next(x for x in registry.agent_tools(role) if x.name == "mo_trang")
        return set(typing.get_args(typing.get_args(mo.function.__annotations__["page"])[0]))

    assert "he-thong" not in pages("client") and "duyet" not in pages("client") and "toan-canh" in pages("client")
    assert "he-thong" in pages("admin")


def test_d27_the_policy_tool_names_every_factor_so_property_rules_are_found():
    """D27: “Mấy chính sách mới về bất động sản thì tôi mất bao nhiêu?” — “no line is a property policy”, while C02 has
    three (transfer tax, land price table, a second-home tax): the tool told the model only the largest of eighteen."""
    out = run(registry.REGISTRY["dong_luc"].run(ctx("client", "C02"), {}))
    listed = out["text"].split("Từng yếu tố: ")[1].split("; ")
    assert len(listed) == out["data"]["n"] and "bất động sản" in out["text"].split("Từng yếu tố: ")[1].lower()
    assert all("(" in x and ("chính sách" in x or "vĩ mô" in x or "dự án" in x or "yếu tố khác" in x) for x in listed)


def test_d28_a_compacted_conversation_keeps_the_order_of_questions_and_reads_back_rather_than_guess():
    """D28: after a compaction, “câu đầu tiên tôi hỏi là gì?” — “Chính sách nào tốn kém nhất?” (the twelfth; the first
    was “Tài sản ròng của tôi bao nhiêu?”): the summary kept the figures, not the questions, and the model guessed
    from the first message it still saw instead of reading the session back."""
    from assistant import turn

    assert "## Người dùng đã hỏi (theo thứ tự" in turn.SUMMARY and "tám mục" in turn.SUMMARY
    assert "gọi doc_lai_phien để đọc lại, không đoán" in turn.RULES


def test_d32_a_comparison_gives_each_scenarios_own_split_and_names_the_combinations():
    """D32: “VN-Index giảm 30 %: −1,82 tỷ, phần lớn từ cổ phiếu (khoảng 1,97 tỷ)” — a part larger than the whole: the
    comparison's only split by class was the two shocks together, under a plain ``by_class``."""
    out = run(registry.REGISTRY["so_sanh_kich_ban"].run(ctx(), {"scenarios": ["co_phieu", "lai_suat"]}))
    d = out["data"]
    assert "by_class" not in d and d["by_class_together"]
    assert set(d["by_class_alone"]) == set(d["alone"]) == {"vni_30", "rates_up"}
    for sid, split in d["by_class_alone"].items():  # no class loses more than its scenario's whole change
        assert all(abs(v) <= abs(d["alone"][sid]) + 1 for v in split.values() if v < 0), sid
