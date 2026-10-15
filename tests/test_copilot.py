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
    assert done["status"] == "ok" and wealth_store.review(item)["status"] == "approved"
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
