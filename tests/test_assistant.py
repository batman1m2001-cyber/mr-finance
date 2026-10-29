"""The assistant's turn (A2, assistant.md §3): several tools in one turn, answers that cite what they rest on, writes
that wait for the person who asked, the barrier's template mode, and the Copilot's path when the model is missing
or fails (NFR-03). Offline: a scripted model (operonx-agents testing)."""

import asyncio
import json
import re

import pytest
from operonx import Operon
from operonx.app import Application
from operonx_agents.testing import ScriptedLLM, asks, says, scripted
from starlette.testclient import TestClient

from assistant.graph import assistant_flow
from control import audit, config, db
from wealth import fixtures
from wealth import store as wealth_store

INPUTS = ("message", "role", "client_id", "scope", "route", "goals", "turn_id", "approvals", "conversation_id")
ASK = Operon(assistant_flow, params={k: None for k in INPUTS})


@pytest.fixture(autouse=True)
def model_on(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")


def ask(
    message=None, role="client", client_id="C01", turn_id=None, approvals=None, route="#/client/tong-quan", cid=None
):
    inputs = {"message": message, "role": role, "client_id": client_id, "scope": "personal", "route": route}
    inputs.update({"turn_id": turn_id, "approvals": approvals, "conversation_id": cid})
    out = asyncio.run(ASK.run(inputs=inputs))
    assert "$errors" not in out, out["$errors"]
    return out["assistant"]


def client_ai(mode):
    vid = config.propose("client_ai", {"mode": mode, "onprem_hosts": ["127.0.0.1"]}, "admin")["id"]
    config.decide(vid, "approve", "admin2")


def test_one_question_two_tools_and_an_answer_that_cites_them():
    llm = ScriptedLLM(asks(("tong_quan", {})), asks(("dong_tien", {})), says("Tài sản ròng tăng; tháng này còn dư."))
    with scripted(copilot=llm):
        a = ask("Tài sản của tôi thế nào và tháng này tôi chi bao nhiêu?")
    assert a["status"] == "ok" and a["mode"] == "model" and a["text"] == "Tài sản ròng tăng; tháng này còn dư."
    assert [s["tool"] for s in a["steps"]] == ["tong_quan", "dong_tien"] and all(
        s["status"] == "ok" for s in a["steps"]
    )
    assert a["citations"] == [{"label": "Wealth View", "route": "#/client/tong-quan/toan-canh"}]  # ADR-0037
    assert a["as_of"] and a["sources"] and a["steps"][0]["card"]["kind"] == "figures"
    # the model read the tools' results (demo mode) and was told the page, not the client
    seen = json.dumps(llm.requests[-1]["messages"], ensure_ascii=False)
    assert "Tài sản ròng" in seen and "tong-quan" in seen


def test_the_turn_is_audited_without_its_text():
    with scripted(copilot=ScriptedLLM(asks(("tong_quan", {})), says("Ổn."))):
        a = ask("Tài sản của tôi thế nào?")
    with db.tx() as con:
        row = dict(con.execute("select * from audit_log where seq = ?", (a["audit_seq"],)).fetchone())
        assert audit.verify(con)["ok"]
    data = json.loads(row["data"])
    assert row["action"] == "assistant.turn" and row["object"] == "tong_quan"
    assert data["steps"] == [["tong_quan", "ok"]] and data["mode"] == "model"
    assert "Tài sản" not in json.dumps(row, ensure_ascii=False)


def test_the_turn_is_timed_without_its_words_and_the_model_does_not_reason_first():
    """The latency report (2026-10-18): a tool turn's two model calls each waited 0.3–0.45 s on hidden reasoning, and
    nothing recorded where a turn's time went (the assistant's traces are off: they would hold people's words)."""
    llm = ScriptedLLM(asks(("tong_quan", {})), says("Ổn."))
    with scripted(copilot=llm):
        a = ask("Tài sản của tôi thế nào?")
    assert all(q.get("reasoning") == {"enabled": False} for q in llm.requests), llm.requests[0].keys()
    t = a["timing"]
    assert len(t["calls"]) == 2 and t["start"] is not None and t["first_text"] is not None, t  # tool call, answer
    assert all(first is not None and 0 <= first <= end for first, end in t["calls"]), t
    assert t["start"] <= t["first_text"] <= t["total"] and t["tools"] >= 0, t
    assert t["start"] + t["calls"][0][1] <= t["first_text"], t  # this model wrote nothing before its tool call
    with db.tx() as con:
        row = con.execute("select data from audit_log where seq = ?", (a["audit_seq"],)).fetchone()
    assert json.loads(row["data"])["timing"] == t  # the audit keeps it: a slow turn can be read back


def test_a_write_waits_for_the_person_who_asked_then_runs_once_and_is_checked():
    before = len(wealth_store.reviews("C01"))
    llm = ScriptedLLM(asks(("gui_de_xuat", {"scenario": "co_phieu", "option": "light"})), says("Đã gửi, chờ RM."))
    with scripted(copilot=llm):
        a = ask("Gửi phương án nhẹ của kịch bản cổ phiếu giảm cho RM")
        assert a["status"] == "pending" and len(wealth_store.reviews("C01")) == before  # nothing written yet
        (w,) = a["waits"]
        assert w["tool"] == "gui_de_xuat" and w["summary"].startswith("Gửi “Giảm điểm nóng”")
        other = ask(role="rm", turn_id=a["turn_id"], approvals={w["id"]: "approve"})  # not theirs to answer
        assert other["status"] == "failed" and len(wealth_store.reviews("C01")) == before
        done = ask(turn_id=a["turn_id"], approvals={w["id"]: "approve"})
        again = ask(turn_id=a["turn_id"], approvals={w["id"]: "approve"})
    assert done["status"] == "ok" and [s["status"] for s in done["steps"]] == ["ok"]
    assert done["steps"][0]["text"].startswith("Đã gửi") and len(wealth_store.reviews("C01")) == before + 1
    assert again["status"] == "failed" and len(wealth_store.reviews("C01")) == before + 1  # once


def test_a_declined_write_runs_nothing():
    llm = ScriptedLLM(asks(("ghi_lien_he", {"channel": "call"})), says("Không ghi."))
    with scripted(copilot=llm):
        a = ask("Ghi lại cuộc gọi với khách này", role="rm", route="#/rm")
        done = ask(role="rm", turn_id=a["turn_id"], approvals={a["waits"][0]["id"]: "deny"})
    from contacts import store as contacts

    assert done["steps"][0]["status"] == "declined" and contacts.recent() == []


def test_with_the_barrier_off_the_model_sees_no_client_data_and_the_tools_write_the_answer():
    client_ai("off")
    llm = ScriptedLLM(asks(("tong_quan", {})), asks(("dong_tien", {})), says("Xem số liệu bên dưới."))
    with scripted(copilot=llm):
        a = ask("Tài sản của Nguyễn Minh Khoa thế nào, tháng 9 chi bao nhiêu?")
    assert a["mode"] == "template" and a["text"].startswith("Tài sản ròng") and "Tháng" in a["text"]
    sent = json.dumps([r["messages"] for r in llm.requests], ensure_ascii=False)
    c = fixtures.client("C01")
    assert c["name"] not in sent and "Tài sản ròng" not in sent and not re.search(r"tháng 9", sent)
    assert "<người>" in a["seen"]


def test_without_a_model_the_copilot_path_answers(monkeypatch):
    monkeypatch.delenv("LLM_MODEL_COPILOT")
    a = ask("Tài sản của tôi thế nào?")
    assert a["mode"] == "fallback" and a["status"] == "ok" and a["steps"][0]["tool"] == "tong_quan"


def test_a_model_that_fails_before_any_tool_falls_back_said_so():
    with scripted(copilot=ScriptedLLM(RuntimeError("provider down"))):
        a = ask("Tài sản của tôi thế nào?")
    assert a["mode"] == "fallback" and "mô hình lỗi" in a["why"] and a["steps"][0]["tool"] == "tong_quan"


def test_a_tool_the_role_does_not_have_is_not_there_to_call():
    llm = ScriptedLLM(asks(("lay_tin", {})), says("Tôi không làm được việc này."))
    with scripted(copilot=llm):
        a = ask("Lấy tin mới đi")
    assert a["steps"][0]["status"] == "failed" and "lay_tin" not in json.dumps(llm.requests[0].get("tools"))


def test_the_endpoint():
    with scripted(copilot=ScriptedLLM(asks(("tong_quan", {})), says("Ổn."))):
        with TestClient(Application.find(".").asgi()) as c:
            r = c.post("/api/assistant", json={"message": "Tài sản thế nào?", "role": "client", "client_id": "C01"})
    assert r.status_code == 200 and r.json()["assistant"]["status"] == "ok"


def test_a_long_message_is_refused():
    out = asyncio.run(ASK.run(inputs={"message": "x" * 2001, "role": "client", "client_id": "C01"}))
    assert "$errors" in out


def test_a_turn_costs_what_the_provider_charged_its_model_and_its_tools(monkeypatch):
    """operonx-agents 0.3.1 takes OpenRouter's reported cost; the web search adds its own call's (A8)."""
    from assistant import web

    async def search(ctx, question):
        return {"text": "Lãi suất điều hành giữ nguyên.", "query": question, "sources": [{"url": "https://sbv.gov.vn"}],
                "cost_usd": 0.012}  # fmt: skip

    monkeypatch.setattr(web, "search", search)
    llm = ScriptedLLM(asks(("tim_tren_web", {"q": "lãi suất điều hành"}), cost=0.001), says("Giữ nguyên.", cost=0.002))
    with scripted(copilot=llm):
        a = ask("Lãi suất điều hành hiện nay là bao nhiêu?")
    assert a["usage"]["cost_usd"] == pytest.approx(0.015) and a["usage"]["tools_cost_usd"] == 0.012
    with db.tx() as con:
        row = con.execute("select data from audit_log where action = 'assistant.turn' order by seq desc").fetchone()
    assert json.loads(row["data"])["cost_usd"] == pytest.approx(0.015)  # the audit records it, as the map shows
