"""Conversations on the server (A3, assistant.md §5, OWN-AS-10/11): a conversation carries on from turn to turn and
from device to device, is listed, opened and deleted by its owner only, compacts when it grows instead of dropping
what was said, is sealed at rest, and keeps what a model allowed to read was sent apart from template mode."""

import asyncio
import base64
import json
import os
import sqlite3

import pytest
from operonx import Operon
from operonx_agents.testing import ScriptedLLM, asks, says, scripted

from assistant import conversations as conv
from assistant.graph import assistant_conversations_flow, assistant_flow
from control import audit, config, db
from wealth import fixtures

INPUTS = ("message", "role", "client_id", "scope", "route", "goals", "turn_id", "approvals", "conversation_id")
ASK = Operon(assistant_flow, params={k: None for k in INPUTS})
CONVS = Operon(
    assistant_conversations_flow, params={k: None for k in ("action", "conversation_id", "role", "client_id")}
)


@pytest.fixture(autouse=True)
def model_on(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")


def ask(message=None, cid=None, role="client", client_id="C01", turn_id=None, approvals=None):
    inputs = {
        "message": message,
        "role": role,
        "client_id": client_id,
        "scope": "personal",
        "route": "#/client/tong-quan",
    }
    inputs.update({"turn_id": turn_id, "approvals": approvals, "conversation_id": cid})
    out = asyncio.run(ASK.run(inputs=inputs))
    assert "$errors" not in out, out["$errors"]
    return out["assistant"]


def convs(action, cid=None, role="client", client_id="C01"):
    out = asyncio.run(
        CONVS.run(inputs={"action": action, "conversation_id": cid, "role": role, "client_id": client_id})
    )
    if "$errors" in out:
        raise ValueError(next(iter(out["$errors"].values())).get("message"))
    return out["conversations"]


def sent(llm, i=-1):
    return json.dumps(llm.requests[i]["messages"], ensure_ascii=False)


def test_a_conversation_carries_on_and_opens_again_as_it_was_shown():
    llm = ScriptedLLM(asks(("tong_quan", {})), says("Tài sản ròng tăng."), says("Vì cổ phiếu lên."))
    with scripted(copilot=llm):
        first = ask("Tài sản của tôi thế nào?")
        cid = first["conversation_id"]
        second = ask("Vì sao vậy?", cid=cid)
    assert cid and second["conversation_id"] == cid
    # the model saw the first question, the tool's result and its own answer before the second question
    assert "Tài sản của tôi thế nào?" in sent(llm) and "Tài sản ròng tăng." in sent(llm) and "Vì sao vậy?" in sent(llm)
    got = convs("open", cid)  # another device: the same turns, as the panel showed them
    assert [t["question"] for t in got["turns"]] == ["Tài sản của tôi thế nào?", "Vì sao vậy?"]
    assert got["turns"][0]["answer"]["steps"][0]["card"]["kind"] == "figures"
    assert got["turns"][1]["answer"]["text"] == "Vì cổ phiếu lên." and got["waiting"] == []
    assert got["conversation"]["title"] == "Tài sản của tôi thế nào?" and got["conversation"]["turns"] == 2


def test_the_list_is_the_owners_newest_first():
    with scripted(copilot=ScriptedLLM(says("Một."), says("Hai."), says("Ba."))):
        a = ask("Câu một")["conversation_id"]
        b = ask("Câu hai")["conversation_id"]
        ask("Câu ba", client_id="C02")  # another client's
    items = convs("list")["items"]
    assert [c["id"] for c in items] == [b, a] and "owner" not in items[0]
    assert [c["title"] for c in convs("list", client_id="C02")["items"]] == ["Câu ba"]


def test_nobody_else_opens_continues_or_deletes_it():
    with scripted(copilot=ScriptedLLM(says("Ổn."))):
        cid = ask("Tài sản của tôi thế nào?")["conversation_id"]
    for role, client in (("client", "C02"), ("rm", "C01")):
        with pytest.raises(ValueError, match="Không có cuộc trò chuyện này"):
            convs("open", cid, role=role, client_id=client)
        with pytest.raises(ValueError, match="Không có cuộc trò chuyện này"):
            convs("delete", cid, role=role, client_id=client)
        with scripted(copilot=ScriptedLLM(says("x"))):
            other = ask("Tiếp tục", cid=cid, role=role, client_id=client)
        assert other["status"] == "failed" and other["text"] == "Không có cuộc trò chuyện này"
    assert convs("open", cid)["conversation"]["turns"] == 1  # untouched


def test_delete_removes_the_turns_and_the_models_side_audited_without_text():
    with scripted(copilot=ScriptedLLM(asks(("tong_quan", {})), says("Ổn."))):
        cid = ask("Tài sản của tôi thế nào?")["conversation_id"]
    assert convs("delete", cid) == {"deleted": cid, "turns": 1}
    with sqlite3.connect(conv.db_path()) as con:
        left = [
            con.execute(f"select count(*) from {t}").fetchone()[0]
            for t in ("conversations", "turns", "operonx_agents_items")
        ]  # noqa: E501
    assert left == [0, 0, 0] and convs("list")["items"] == []
    with db.tx() as con:
        row = dict(con.execute("select * from audit_log where action = 'assistant.conversation.delete'").fetchone())
    assert row["object"] == cid and "Tài sản" not in json.dumps(row, ensure_ascii=False)


def test_a_write_waits_inside_its_conversation_and_its_answer_joins_it():
    llm = ScriptedLLM(asks(("gui_de_xuat", {"scenario": "co_phieu", "option": "light"})), says("Đã gửi, chờ RM."))
    with scripted(copilot=llm):
        a = ask("Gửi phương án nhẹ của kịch bản cổ phiếu giảm cho RM")
        cid = a["conversation_id"]
        assert convs("open", cid)["waiting"] == [a["turn_id"]]  # another device can answer it
        done = ask(turn_id=a["turn_id"], approvals={a["waits"][0]["id"]: "approve"})
    assert done["conversation_id"] == cid and done["status"] == "ok"
    got = convs("open", cid)
    assert [t["question"] for t in got["turns"]] == ["Gửi phương án nhẹ của kịch bản cổ phiếu giảm cho RM", None]
    assert got["turns"][0]["answer"]["status"] == "pending" and got["waiting"] == []


def test_a_long_conversation_compacts_instead_of_dropping_and_the_transcript_keeps_every_turn():
    """30 turns; once a prompt passes 75 % of the 24k budget, the older exchanges become one summary written by
    the model, the last ones stay as said, and the next prompts start from it."""
    script = []
    for i in range(30):
        script.append(says(f"Trả lời {i}.", prompt_tokens=19_000 if i in (12, 24) else 1_000 + 500 * (i % 12)))
        if i in (12, 24):
            script.append(says(f"Tóm tắt đến lượt {i}."))  # the summarizer, the same model
    llm = ScriptedLLM(*script)
    with scripted(copilot=llm):
        cid, said = None, []
        for i in range(30):
            a = ask(f"Câu hỏi {i}", cid=cid)
            cid = a["conversation_id"]
            said.append(a["compacted"])
    assert [i for i, x in enumerate(said) if x] == [12, 24]  # the answer whose prompt passed the budget says so
    last = sent(llm)
    assert "[conversation summary]\\nTóm tắt đến lượt 24." in last and "Tóm tắt đến lượt 12." not in last
    assert "Câu hỏi 0" not in last and "Câu hỏi 29" in last and "Trả lời 28." in last
    assert len(llm.requests[-1]["messages"]) < 20 < 61  # the summary, the kept exchanges, not 30 turns' messages
    summaries = [r for r in llm.requests if not r.get("tools")]
    assert len(llm.requests) == 32 and len(summaries) == 2  # 30 answers + 2 summaries: nothing asked twice
    assert convs("open", cid)["conversation"]["turns"] == 30
    with sqlite3.connect(conv.db_path()) as con:
        items = [json.loads(r[0]) for r in con.execute("select item from operonx_agents_items order by seq")]
    assert sum(i["role"] == "summary" for i in items) == 2 and sum(i["role"] == "user" for i in items) == 30


def test_with_keys_set_nothing_said_is_stored_in_clear(monkeypatch):
    key = base64.b64encode(os.urandom(32)).decode()
    monkeypatch.setenv("MF_DATA_KEYS", f"k1={key}")
    with scripted(copilot=ScriptedLLM(asks(("tong_quan", {})), says("Tài sản ròng tăng."))):
        cid = ask("Tài sản của Nguyễn Minh Khoa thế nào?")["conversation_id"]
    raw = b""
    for f in conv.db_path().parent.glob("assistant.db*"):
        raw += f.read_bytes()
    assert b"Nguy" not in raw and "Tài sản".encode() not in raw and b"enc:1:k1:" in raw
    got = convs("open", cid)  # and it opens
    assert got["conversation"]["title"].startswith("Tài sản của Nguyễn") and got["turns"][0]["answer"]["text"]


def test_closing_the_barrier_mid_conversation_sends_none_of_what_was_read_before():
    with scripted(copilot=ScriptedLLM(asks(("tong_quan", {})), says("Tài sản ròng 43 tỷ."))):
        cid = ask("Tài sản của tôi thế nào?")["conversation_id"]
    vid = config.propose("client_ai", {"mode": "off", "onprem_hosts": []}, "admin")["id"]
    config.decide(vid, "approve", "admin2")
    llm = ScriptedLLM(asks(("dong_tien", {})), says("Xem bên dưới."))
    with scripted(copilot=llm):
        a = ask("Tháng này tôi chi bao nhiêu?", cid=cid)
    out = json.dumps([r["messages"] for r in llm.requests], ensure_ascii=False)
    assert a["mode"] == "template" and a["conversation_id"] == cid
    assert "Tài sản ròng" not in out and "43 tỷ" not in out and fixtures.client("C01")["name"] not in out
    assert convs("open", cid)["conversation"]["turns"] == 2


def test_the_audit_chain_holds():
    with scripted(copilot=ScriptedLLM(says("Ổn."))):
        cid = ask("Xin chào")["conversation_id"]
    convs("delete", cid)
    with db.tx() as con:
        assert audit.verify(con)["ok"]


def test_a_rotation_reseals_the_conversations_and_the_old_key_goes(monkeypatch):
    k1, k2 = (base64.b64encode(os.urandom(32)).decode() for _ in range(2))
    with scripted(copilot=ScriptedLLM(asks(("tong_quan", {})), says("Ổn."))):
        cid = ask("Tài sản của tôi thế nào?")["conversation_id"]  # stored plain: no key yet
    with sqlite3.connect(conv.db_path(), isolation_level=None) as con:
        assert set(conv.census(con)) == {"plain"}
        monkeypatch.setenv("MF_DATA_KEYS", f"k1={k1}")
        conv.rotate(con)
        assert set(conv.census(con)) == {"k1"}
        monkeypatch.setenv("MF_DATA_KEYS", f"k2={k2},k1={k1}")
        conv.rotate(con)
        assert set(conv.census(con)) == {"k2"}
    monkeypatch.setenv("MF_DATA_KEYS", f"k2={k2}")  # k1 dropped: everything still opens, the model's side too
    assert convs("open", cid)["turns"][0]["question"] == "Tài sản của tôi thế nào?"
    llm = ScriptedLLM(says("Vẫn ổn."))
    with scripted(copilot=llm):
        ask("Còn bây giờ?", cid=cid)
    assert "Tài sản của tôi thế nào?" in sent(llm)
