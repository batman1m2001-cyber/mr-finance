"""The Copilot (src/copilot, kit K5, ADR-0012): the router never sees client data; roles and confirm hold."""

import asyncio
import json
import re
from types import SimpleNamespace

from operonx import Operon
from operonx.app import Application
from starlette.testclient import TestClient

from copilot import router
from copilot.graph import copilot_flow
from copilot.scrub import fold, names, scrub
from wealth import fixtures
from wealth import store as wealth_store

ASK = Operon(copilot_flow, params={k: None for k in ("question", "role", "client_id", "scope", "route", "confirm")})
CODES = set(json.load(open("data/market.json"))["stocks"]) | {"TCBF", "TCEF", "TCB12401", "SMR12501"}


def ask(question=None, role="client", client_id="C01", route="#/client/tong-quan/toan-canh", confirm=None):
    out = asyncio.run(
        ASK.run(
            inputs={
                "question": question,
                "role": role,
                "client_id": client_id,
                "scope": "personal",
                "route": route,
                "confirm": confirm,
            }
        )
    )
    assert "$errors" not in out, out["$errors"]
    return out["copilot"]


def hostile_questions():
    for cid in fixtures.client_ids(members=True):
        c = fixtures.client(cid)
        for person in [c["name"]] + [d["name"] for d in c.get("dependents") or []]:
            low = person.lower()
            yield f"{person} có 1,8 tỷ ở tài khoản 1902-TD-01, cổ phiếu FPT, TCBF; {low} chi 34.800.000đ tháng 9/2026?"


def leaks(text):
    f = fold(text)
    found = [n for n in names() if fold(n) in f]
    found += re.findall(r"\d", text)
    found += [c for c in CODES if re.search(rf"\b{c}\b", text)]
    return found


def test_the_router_prompt_carries_no_name_number_or_code():
    for q in hostile_questions():
        for role in ("client", "rm"):
            system, user = router.prompt(scrub(q), "#/rm/khach-hang/tac-dong/AR-0003-v1-2", role)
            assert leaks(system + user) == [], (q, leaks(system + user))


def test_the_live_router_receives_only_the_scrubbed_question(monkeypatch):
    seen = []

    class FakeLLM:
        async def generate(self, messages, **kw):
            seen.append(messages)
            msg = SimpleNamespace(content='{"tool": "dong_tien", "args": {}}')
            return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason="stop")], model="fake-router")

    monkeypatch.setattr(router, "live", lambda: True)
    monkeypatch.setattr("operonx.providers.ops._utils.resolve_hub", lambda: SimpleNamespace(get=lambda key: FakeLLM()))
    q = next(hostile_questions())
    got = ask(q)
    assert got["status"] == "ok" and got["tool"] == "dong_tien"
    assert got["router"] == {"kind": "llm", "model": "fake-router"}
    assert seen and leaks(json.dumps(seen, ensure_ascii=False)) == []
    assert "<người>" in got["seen"] and not re.search(r"\d", got["seen"])


def test_an_answer_outside_the_catalogue_falls_back_to_keywords_said_so(monkeypatch):
    class Liar:
        async def generate(self, messages, **kw):
            msg = SimpleNamespace(content='{"tool": "chuyen_tien", "args": {"so_tien": 1}}')
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)], model="fake-router")

    monkeypatch.setattr(router, "live", lambda: True)
    monkeypatch.setattr("operonx.providers.ops._utils.resolve_hub", lambda: SimpleNamespace(get=lambda key: Liar()))
    got = ask("Có gì cần chú ý?")
    assert got["tool"] == "chu_y" and got["router"]["kind"] == "keyword" and got["router"]["fallback"]


def test_a_client_cannot_run_a_cio_tool_even_by_confirm():
    assert ask("Lấy tin mới")["status"] == "forbidden"
    assert ask(confirm={"tool": "lay_tin", "args": {}})["status"] == "forbidden"


def test_no_write_without_confirm_and_the_result_is_the_real_one():
    item = wealth_store.propose("C01", "tuition", "Học phí — Tích lũy đều", {"option": {"id": "light"}})
    first = ask("Duyệt đề xuất đang chờ", role="rm", route="#/rm/khach-hang/duyet")
    assert first["status"] == "pending" and first["confirm"] == {
        "tool": "duyet_de_xuat",
        "args": {"item_id": item, "decision": "approved"},
    }
    assert wealth_store.review(item)["status"] == "pending"  # nothing written yet
    assert ask(confirm=first["confirm"], role="client")["status"] == "forbidden"  # the client cannot confirm it
    assert wealth_store.review(item)["status"] == "pending"
    done = ask(confirm=first["confirm"], role="rm")
    # the RM's approval is the last (OWN-FB-18)
    assert done["status"] == "ok" and wealth_store.review(item)["status"] == "approved"
    assert "Đã ghi: duyệt" in done["text"]
    again = ask(confirm=first["confirm"], role="rm")  # the server refuses a second decision: said as a failure
    assert again["status"] == "failed" and again["text"].startswith("Không thực hiện được")


def test_a_failing_tool_is_reported_as_failed_and_unknown_questions_get_help():
    got = ask("Dòng tiền tháng 3/2020?")
    assert got["status"] == "failed" and "Không có giao dịch" in got["text"]
    assert ask("xin chào")["status"] == "unknown" and ask("xin chào")["suggest"]
    nav = ask("mở đồ thị tác động")
    assert nav["navigate"] == "#/client/tin/do-thi"


def test_the_endpoint():
    with TestClient(Application.find(".").asgi()) as c:
        r = c.post("/api/copilot", json={"question": "Tài sản của tôi thế nào?", "role": "client", "client_id": "C01"})
        body = r.json()["copilot"]
        assert r.status_code == 200 and body["status"] == "ok" and body["router"]["kind"] == "keyword"


# -- Copilot 2.0 (UI redesign R5) ------------------------------------------------------------------


def test_an_answer_says_when_its_data_is_from_what_it_read_and_carries_its_card():
    from dashboard.graph import dashboard_flow

    a = ask("Tài sản của tôi thế nào?")
    d = asyncio.run(
        Operon(dashboard_flow, params={"client_id": None, "scope": None, "months": None}).run(
            inputs={"client_id": "C01"}
        )
    )["dashboard"]
    assert a["status"] == "ok" and a["answered_at"] > 0
    assert a["as_of"] == d["as_of"] and a["sources"]
    assert a["card"]["kind"] == "figures" and a["card"]["items"][0]["label"] == "Tài sản ròng"
    f = ask("Dòng tiền tháng này?")
    assert f["card"]["kind"] == "bars" and f["as_of"] == f["focus"][0].split(":")[1]


def test_investigate_reads_the_events_path_from_the_impact_graph():
    from test_apply import MARKET, approved

    from apply.impact_graph import family_graph

    _, run = approved(*MARKET)
    a = ask("Vì sao tin này ảnh hưởng tới tôi?")
    assert a["tool"] == "dieu_tra" and a["status"] == "ok"
    g = family_graph("C01", "client")
    ev = next(n for n in g["nodes"] if n["kind"] == "event")
    assert a["focus"] == [f"event:{ev['ref']}"] and f"Lần áp dụng {run['id']}" in a["sources"]
    steps = {s["label"]: s["items"] for s in a["card"]["steps"]}
    assert steps["Sự kiện"] == [ev["label"]]  # the client's event type, never the headline
    branches = [n["label"] for n in g["nodes"] if n["kind"] == "branch"]
    assert set(steps["Kịch bản"]) <= set(branches) and steps["Kịch bản"][0] in a["text"]
    assert ask("Vì sao?", role="rm")["card"]["steps"][1]["items"] != steps["Sự kiện"]  # staff read the headline


def test_a_stress_scenario_is_the_planning_pages_and_picked_by_words():
    from scenarios.graph import scenario_flow

    a = ask("Nếu lãi suất tăng mạnh thì sao?")
    assert a["tool"] == "kich_ban" and a["status"] == "ok"
    r = asyncio.run(
        Operon(scenario_flow, params={"client_id": None, "scenario": None, "params": None, "scope": None}).run(
            inputs={"client_id": "C01", "scenario": "rates_up"}
        )
    )["result"]
    assert r["title"] in a["text"]
    figs = {x["label"]: x["value"] for x in a["card"]["items"]}
    from copilot.tools import _vnd

    assert figs["Trước"] == _vnd(r["before"]["net_worth"]) and figs["Sau cú sốc"] == _vnd(r["after"]["net_worth"])
    assert "VN-Index giảm 30%" in ask("Tạo kịch bản chứng khoán giảm mạnh")["text"]
    assert ask("Kịch bản bất động sản đóng băng")["card"]["title"] == "BĐS đóng băng như 2022–2023"


def test_every_call_is_in_the_audit_chain_with_the_question_as_the_router_saw_it():
    from control import audit, db

    with db.tx() as con:
        before = con.execute("select count(*) from audit_log").fetchone()[0]
    q = "Nguyễn Minh Khoa có 1,8 tỷ, kịch bản lãi suất tăng?"
    a = ask(q)
    ask("Câu gì đó không hiểu")
    with db.tx() as con:
        rows = con.execute("select actor, action, object, data from audit_log order by seq").fetchall()[before:]
        assert audit.verify(con)["ok"]
    assert [r[1] for r in rows] == ["copilot.ask", "copilot.ask"]
    first = json.loads(rows[0][3])
    assert rows[0][0] == "client:C01" and rows[0][2] == "kich_ban" and first["status"] == "ok"
    assert first["seen"] == a["seen"] and not leaks(first["seen"]) and a["audit_seq"] > 0
    assert rows[1][2] == "-" and json.loads(rows[1][3])["status"] == "unknown"


def test_goals_are_the_ones_the_browser_follows():
    out = asyncio.run(
        Operon(
            copilot_flow,
            params={k: None for k in ("question", "role", "client_id", "scope", "route", "confirm", "goals")},
        ).run(
            inputs={"question": "Mục tiêu của tôi thế nào?", "role": "client", "client_id": "C01", "goals": ["medical"]}
        )
    )
    a = out["copilot"]
    assert a["text"].startswith("1 mục tiêu") and [x["title"] for x in a["card"]["items"]] == ["Chi phí y tế lớn"]
