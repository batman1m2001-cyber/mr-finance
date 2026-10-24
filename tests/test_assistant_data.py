"""The data room wired into the assistant (docs/ASSISTANT_DATA_PLAN.md D4, ADR-0040): ``truy_van`` in the registry
with the role's catalog, three queries a turn, an audit row per query, “Cách tính” in the answer's steps, the
template with ``client_ai`` off, and the re-count rule — with the CIO's conversation of 2026-10-24 replayed on a
scripted model. Offline: no model is called."""

import asyncio
import json
import time

import pytest
from operonx import Operon
from operonx_agents.testing import ScriptedLLM, asks, says, scripted

from assistant import base, conversations, datacatalog, dataroom, registry, turn
from assistant.base import Ctx
from assistant.dataroom import Refused, truy_van
from assistant.graph import assistant_flow
from control import audit, config, db
from news import store as news

INPUTS = ("message", "role", "client_id", "scope", "route", "goals", "turn_id", "approvals", "conversation_id")
ASK = Operon(assistant_flow, params={k: None for k in INPUTS})


def seed(n, status="new"):
    now = time.time()
    rows = [
        {"source": "cafef_ck", "url_key": f"u{status}{i}", "title_key": f"t{status}{i}", "published": now - 3600,
         "ingested": now, "kind": "domestic", "status": status, "relevance": "high",
         "title": f"Lãi suất điều hành {status} {i}", "outlet": "CafeF", "label": "Trong nước", "summary": "",
         "restricted": []}
        for i in range(n)
    ]  # fmt: skip
    assert news.add(rows)[1] == 0


def ctx(role, reads=True, user=None):
    return Ctx(role=role, client_id=None, scope="personal", question="", reads=reads, user=user)


def run(coro):
    return asyncio.run(coro)


def queries():
    with db.tx() as con:
        rows = [dict(r) for r in con.execute("select * from audit_log where action = 'assistant.query' order by seq")]
        assert audit.verify(con)["ok"]
    return [{**r, "data": json.loads(r["data"])} for r in rows]


@pytest.fixture
def model_on(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")


def ask(message, role="cio", cid=None, route="#/cio/hop-tin"):
    inputs = {"message": message, "role": role, "client_id": None, "scope": "personal", "route": route}
    inputs.update({"turn_id": None, "approvals": None, "conversation_id": cid})
    out = run(ASK.run(inputs=inputs))
    assert "$errors" not in out, out["$errors"]
    return out["assistant"]


# -- the registry ---------------------------------------------------------------------------------------------------


def test_truy_van_is_offered_to_its_roles_with_their_catalog():
    assert registry.REGISTRY["truy_van"] is dataroom.CATALOGUE["truy_van"]
    assert registry.LABELS["truy_van"] == "Truy vấn dữ liệu"
    described = {}
    for role in dataroom.ROLES:
        t = {x.name: x for x in registry.agent_tools(role)}["truy_van"]
        assert t.spec.description == dataroom.DESCRIPTION + "\n\n" + datacatalog.catalog(role)  # lines kept
        assert t.spec.readonly and t.spec.approval == "never" and t.spec.params_schema["required"] == ["sql"]
        described[role] = t.spec.description
    assert "## nhan_dinh" in described["cio"] and "## nhan_dinh" not in described["rm"]
    assert "## tin_bi_giu" in described["compliance"] and "## tin\n" not in described["compliance"]
    assert "truy_van" not in {x.name for x in registry.agent_tools("specialist")}  # no room for the specialist
    assert "ADR-0040" in base.Param.__doc__ and "truy_van" in base.Param.__doc__  # the one exception, said so


# -- three a turn, each one audited ---------------------------------------------------------------------------------


def test_three_queries_a_turn_then_refused_and_each_one_audited():
    seed(5)
    c = ctx("cio", user="cio")
    for _ in range(dataroom.CALLS):
        assert run(truy_van(c, {"sql": "select count(*) from tin"}))["data"]["total"] == 1
    with pytest.raises(Refused, match="3 lần trong lượt này"):
        run(truy_van(c, {"sql": "select count(*) from tin"}))
    with pytest.raises(Refused):  # a new turn, a real table: refused, and audited as refused
        run(truy_van(ctx("cio", user="cio"), {"sql": "select email from people"}))
    rows = queries()
    assert len(rows) == 5 and all(r["actor"] == "cio" for r in rows)
    first = rows[0]
    assert first["object"] == "tin" and first["data"]["sql"] == "select count(*) from tin"
    assert first["data"]["role"] == "cio" and first["data"]["rows"] == 1 and first["data"]["ms"] >= 0
    assert "refused" not in first["data"]
    assert "3 lần" in rows[3]["data"]["refused"] and rows[4]["object"] == "-" and rows[4]["data"]["refused"]
    assert "rows" not in rows[4]["data"]


# -- the template, with client_ai off -------------------------------------------------------------------------------


def test_the_template_says_a_count_as_a_sentence_and_rows_as_rows():
    seed(1415)
    seed(3, status="grouped")
    say = lambda sql, reads=False: run(truy_van(ctx("cio", reads=reads), {"sql": sql}))["text"]  # noqa: E731
    assert say("select count(*) from tin where trang_thai = 'new'") == "Có 1.415 tin."
    assert say("SELECT count(*) AS so_tin FROM tin") == "Có 1.418 tin."
    assert say("select count(*) from su_kien") == "Có 0 sự kiện."
    assert say("select max(diem) as cao_nhat from tin").startswith("cao_nhat: ")
    many = say("select trang_thai, count(*) as so_tin from tin group by trang_thai order by so_tin desc")
    assert many == "2 dòng:\ntrang_thai | so_tin\nnew | 1.415\ngrouped | 3"
    assert say("select ma from tin").startswith("1.418 dòng, 10 dòng đầu:\nma\n")
    # the model's own reading (client_ai allows it) is the total and the rows, not the sentence
    assert say("select count(*) from tin", reads=True) == "Kết quả: count(*) = 1418 (1 dòng)."


def test_with_client_ai_off_the_model_writes_the_sql_and_never_reads_the_rows(model_on):
    seed(1415)
    vid = config.propose("client_ai", {"mode": "off", "onprem_hosts": ["127.0.0.1"]}, "admin")["id"]
    config.decide(vid, "approve", "admin2")
    llm = ScriptedLLM(asks(("truy_van", {"sql": "select count(*) from tin"})), says("Đây là kết quả."))
    with scripted(copilot=llm):
        a = ask("Hệ thống đã lấy về bao nhiêu tin?")
    assert a["mode"] == "template" and a["text"] == "Có 1.415 tin."
    sent = json.dumps([r["messages"] for r in llm.requests], ensure_ascii=False)
    assert "1415" not in sent and "1.415" not in sent  # the model saw the step's status, never the count
    q = a["steps"][0]["query"]
    assert q["sql"] == "select count(*) from tin" and (q["total"], q["shown"]) == (1, 1) and q["tables"] == ["tin"]


# -- “Cách tính” and the re-count rule: the conversation of 2026-10-24 -------------------------------------------


def test_the_rule_to_count_again_is_in_the_prompt_of_the_roles_with_a_room():
    for role in ("cio", "rm", "client", "compliance", "admin", "specialist"):
        text = turn.instructions(type("R", (), {"deps": ctx(role)})())
        assert (turn.DATA_RULE in text) == (role in dataroom.ROLES), role
    assert "đếm lại ngay" in turn.DATA_RULE and "không cãi" in turn.DATA_RULE and "count(*)" in turn.DATA_RULE


def test_the_cio_conversation_of_2026_10_24_counts_and_counts_again_showing_how(model_on):
    """The CIO asked how many news items were fetched; the assistant said 200 (a list's cap) and argued when told
    1,415. Now: it counts with truy_van, the answer carries its SQL, and the contradiction is counted again."""
    seed(1415)
    seed(64, status="grouped")
    by_status = "select trang_thai, count(*) as so_tin from tin group by trang_thai order by so_tin desc"
    llm = ScriptedLLM(
        asks(("truy_van", {"sql": by_status})),
        says("Hệ thống có 1.479 tin: 1.415 chờ xử lý, 64 đã gom thành sự kiện."),
        asks(("truy_van", {"sql": "select count(*) from tin where trang_thai = 'new'"})),
        says("Tôi đã đếm lại các tin chờ xử lý trong bảng tin: 1.415 tin."),
    )
    with scripted(copilot=llm):
        first = ask("Hệ thống đã lấy về bao nhiêu tin?")
        second = ask("Sao lại 200? Tôi thấy 1.415 tin chờ xử lý mà.", cid=first["conversation_id"])
    # the model read the counted total, not a page of the list
    read = json.dumps(llm.requests[1]["messages"], ensure_ascii=False)
    assert "Kết quả: 2 dòng" in read and "new | 1415" in read and "grouped | 64" in read
    # each answer carries how it counted, for “Cách tính”
    q1, q2 = first["steps"][0]["query"], second["steps"][0]["query"]
    assert q1["sql"] == by_status and q1["total"] == 2 and q1["as_of"] and first["as_of"] == q1["as_of"]
    assert q2["sql"].endswith("trang_thai = 'new'") and second["steps"][0]["label"] == "Truy vấn dữ liệu"
    assert second["sources"][0].startswith("Truy vấn trên tin lúc ")
    # the second turn disputes a number: its prompt says so and its first request must call a tool (on the real model
    # the rule alone got “Tôi đã đếm lại” with no tool called); the first turn and the answer's request are free
    system = llm.requests[2]["messages"][0]["content"]
    assert (
        turn.DATA_RULE in system
        and turn.RECOUNT in system
        and turn.RECOUNT not in llm.requests[0]["messages"][0]["content"]
    )
    assert [r.get("tool_choice") for r in llm.requests] == [None, None, "required", None]
    # the recount's result says, next to the count, not to guess why (in the prompt alone Haiku guessed 3 of 3, D5)
    assert dataroom.RECOUNTED.strip() in json.dumps(llm.requests[3]["messages"], ensure_ascii=False)
    assert dataroom.RECOUNTED.strip() not in read
    assert [r["data"]["sql"] for r in queries()] == [q1["sql"], q2["sql"]]


def test_a_dispute_is_a_number_the_last_answer_did_not_say():
    c = Ctx(role="cio", client_id=None, scope="personal", question="")
    cid = conversations.start(c, "Hệ thống đã lấy về bao nhiêu tin?")
    assert not turn.disputes("Sao lại 200?", cid)  # no answer yet: nothing to dispute
    conversations.record(cid, "Hệ thống đã lấy về bao nhiêu tin?", {"status": "ok", "text": "Có 200 tin, 64 đã gom."})
    assert turn.disputes("Sao lại 200? Tôi thấy 1.415 tin chờ xử lý mà.", cid)
    assert turn.disputes("Tôi thấy 1415 tin", cid) and turn.disputes("Không phải 1,415 à?", cid)
    assert not turn.disputes("Vậy 64 tin đã gom là những tin nào?", cid)  # its own number, asked about
    assert not turn.disputes("Còn tin hôm nay thì sao?", cid)  # no number
    assert turn.numbers("1.415 tin, 1,415 hay 1415; 64") == {"1415", "64"}


def test_the_panel_shows_how_it_counted_collapsed():
    js = open("web/copilot.js", encoding="utf-8").read()
    assert '<details class="cp-how small muted mt"><summary>Cách tính</summary>' in js  # collapsed: no `open`
    assert "s.query && s.query.sql" in js and "meta(m) + how(m)" in js and "số liệu lúc" in js
    shell = open("web/shell.js", encoding="utf-8").read()
    assert "./copilot.js?v=20261024d2" in shell  # the browser fetches the new panel
