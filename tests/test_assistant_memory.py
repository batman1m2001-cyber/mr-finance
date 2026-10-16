"""Long-term memory and the archive (A4, assistant.md §5, ADR-0028; OWN-AS-12…16): a few items per person, kept
only when asked and confirmed, never an amount, an account or someone outside the family; carried into the next
conversation; seen, corrected and forgotten on the Bộ nhớ page; isolated per person; the archive searchable;
deletion and retention real."""

import asyncio
import base64
import json
import os
import sqlite3
import time

import pytest
from operonx import Operon
from operonx_agents.testing import ScriptedLLM, asks, says, scripted

from assistant import conversations as conv
from assistant import memory
from assistant.graph import assistant_conversations_flow, assistant_flow, assistant_memory_flow
from control import audit, config, db

INPUTS = ("message", "role", "client_id", "scope", "route", "goals", "turn_id", "approvals", "conversation_id")
ASK = Operon(assistant_flow, params={k: None for k in INPUTS})
MEM = Operon(
    assistant_memory_flow,
    params={k: None for k in ("action", "item_id", "text", "kind", "query", "role", "client_id")},
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


def mem(action, role="client", client_id="C01", **kw):
    out = asyncio.run(MEM.run(inputs={"action": action, "role": role, "client_id": client_id, **kw}))
    if "$errors" in out:
        raise ValueError(next(iter(out["$errors"].values())).get("message"))
    return out["memory"]


def ctx(role="client", client_id="C01"):  # as the server builds it: the role's demo user when sign-in is off
    from assistant.ops import context, who

    return context({**who(role, client_id), "message": "", "route": "", "followed": None})


def keep(text, kind="preference", role="client", client_id="C01"):
    return asyncio.run(memory.remember(ctx(role, client_id), kind, text)).id


def test_what_is_never_kept():
    c = ctx()
    for text in ("Có 5 tỷ tiền gửi", "Lãi 7% là đủ", "Lương 120.000.000 mỗi tháng", "Tài khoản 190212345678",
                 "Thẻ 1902-CASA-01", "Hay nói chuyện với Lê Văn Phát", "x" * 201):  # fmt: skip
        assert memory.refused(text, c), text
    for text in (
        "Thích báo cáo ngắn, gọi buổi sáng",
        "Muốn mua nhà năm 2028",
        "Vợ là Trần Thu Hà, lo việc học của con",
    ):
        assert memory.refused(text, c) is None, text
    assert memory.refused("Vợ là Trần Thu Hà", ctx("rm", "C01"))  # staff keep no client's name


def test_kept_only_when_asked_and_confirmed_then_carried_into_the_next_conversation():
    llm = ScriptedLLM(asks(("ghi_nho", {"kind": "preference", "text": "Thích báo cáo ngắn"})), says("Tôi sẽ nhớ."))
    with scripted(copilot=llm):
        a = ask("Hãy nhớ là tôi thích báo cáo ngắn")
        assert a["status"] == "pending" and mem("list")["items"] == []  # nothing kept before the confirm
        assert a["waits"][0]["summary"] == "Ghi nhớ (Sở thích): “Thích báo cáo ngắn”?"
        done = ask(turn_id=a["turn_id"], approvals={a["waits"][0]["id"]: "approve"})
    assert done["status"] == "ok" and done["steps"][0]["status"] == "ok"
    (item,) = mem("list")["items"]
    assert item["text"] == "Thích báo cáo ngắn" and item["kind_label"] == "Sở thích"
    assert item["source"]["conversation"] == a["conversation_id"]
    nxt = ScriptedLLM(says("Ngắn gọn: ổn."))
    with scripted(copilot=nxt):
        ask("Tài sản thế nào?")  # a new conversation
    system = nxt.requests[0]["messages"][0]["content"]
    assert "Thích báo cáo ngắn" in system and "Điều người dùng đã nhờ ghi nhớ" in system


def test_template_mode_keeps_the_items_from_the_model():
    keep("Thích báo cáo ngắn")
    vid = config.propose("client_ai", {"mode": "off", "onprem_hosts": []}, "admin")["id"]
    config.decide(vid, "approve", "admin2")
    llm = ScriptedLLM(says("Xem bên dưới."))
    with scripted(copilot=llm):
        ask("Tài sản thế nào?")
    assert "Thích báo cáo ngắn" not in json.dumps(llm.requests, ensure_ascii=False)


def test_the_page_lists_corrects_and_forgets_audited_without_text():
    a, b = keep("Thích báo cáo ngắn"), keep("Muốn mua nhà năm 2028", "goal")
    fixed = mem("update", item_id=a, text="Thích báo cáo rất ngắn")["item"]
    assert fixed["text"] == "Thích báo cáo rất ngắn"
    with pytest.raises(ValueError, match="không lưu số tiền"):
        mem("update", item_id=a, text="Thích báo cáo 5 tỷ")
    assert mem("delete", item_id=b) == {"deleted": 1}
    assert [i["text"] for i in mem("list")["items"]] == ["Thích báo cáo rất ngắn"]
    assert mem("clear") == {"deleted": 1} and mem("list")["items"] == []
    with db.tx() as con:
        rows = [dict(r) for r in con.execute("select * from audit_log where action like 'assistant.memory.%'")]
        assert audit.verify(con)["ok"]
    assert [r["action"] for r in rows] == [
        "assistant.memory.update",
        "assistant.memory.delete",
        "assistant.memory.clear",
    ]
    assert "báo cáo" not in json.dumps(rows, ensure_ascii=False)


def test_one_persons_memory_is_never_anothers():
    mine = keep("Thích báo cáo ngắn")
    keep("Gọi buổi chiều", client_id="C02")
    keep("Ưu tiên khách có tin khẩn", role="rm", client_id=None)
    assert [i["text"] for i in mem("list")["items"]] == ["Thích báo cáo ngắn"]
    assert [i["text"] for i in mem("list", client_id="C02")["items"]] == ["Gọi buổi chiều"]
    assert [i["text"] for i in mem("list", role="rm", client_id="C01")["items"]] == ["Ưu tiên khách có tin khẩn"]
    for role, client in (("client", "C02"), ("rm", "C01")):  # an id is not a key to someone else's item
        with pytest.raises(ValueError, match="Không có mục này"):
            mem("update", role=role, client_id=client, item_id=mine, text="Đổi")
        assert mem("delete", role=role, client_id=client, item_id=mine) == {"deleted": 0}
    assert [i["text"] for i in mem("list")["items"]] == ["Thích báo cáo ngắn"]
    llm = ScriptedLLM(asks(("nho_lai", {"query": ""})), says("ok"))
    with scripted(copilot=llm):
        a = ask("Bạn nhớ gì về tôi?", client_id="C02")
    assert "Thích báo cáo ngắn" not in json.dumps(a, ensure_ascii=False) and "Gọi buổi chiều" in a["steps"][0]["text"]


def test_the_archive_is_searchable_by_its_owner_with_conversation_time_and_author():
    with scripted(copilot=ScriptedLLM(says("Học phí năm sau khoảng như năm nay."), says("Ổn."))):
        cid = ask("Học phí cho con năm sau thế nào?")["conversation_id"]
        ask("Học phí của tôi?", client_id="C02")
    hits = mem("search", query="hoc phi")["hits"]
    assert {h["conversation_id"] for h in hits} == {cid} and {h["author"] for h in hits} == {"bạn", "trợ lý"}
    assert all(h["at"] and h["title"] for h in hits)


def test_forgetting_leaves_nothing_readable_on_disk():
    """Without data keys too: the rows are gone and their pages overwritten (secure_delete), the log emptied."""
    keep("Thích nhạc trịnh vào buổi tối")
    with scripted(copilot=ScriptedLLM(says("Ổn."))):
        cid = ask("Câu hỏi về nhạc trịnh buổi tối")["conversation_id"]
    mem("clear")
    flow = Operon(
        assistant_conversations_flow, params={k: None for k in ("action", "conversation_id", "role", "client_id")}
    )
    out = asyncio.run(
        flow.run(inputs={"action": "delete", "conversation_id": cid, "role": "client", "client_id": "C01"})
    )
    assert out["conversations"]["deleted"] == cid
    raw = b"".join(f.read_bytes() for f in conv.db_path().parent.glob("assistant.db*"))
    assert "nhạc trịnh".encode() not in raw and "nhac trinh".encode() not in raw


def test_with_keys_the_items_are_sealed(monkeypatch):
    monkeypatch.setenv("MF_DATA_KEYS", f"k1={base64.b64encode(os.urandom(32)).decode()}")
    keep("Thích báo cáo ngắn")
    raw = b"".join(f.read_bytes() for f in conv.db_path().parent.glob("assistant.db*"))
    assert "báo cáo".encode() not in raw and mem("list")["items"][0]["text"] == "Thích báo cáo ngắn"


def test_retention_deletes_old_conversations_and_stale_facts():
    with scripted(copilot=ScriptedLLM(says("Một."), says("Hai."))):
        old = ask("Câu cũ")["conversation_id"]
        new = ask("Câu mới")["conversation_id"]
    with sqlite3.connect(conv.db_path()) as con:
        con.execute("update conversations set updated = ? where id = ?", (time.time() - 400 * 86400, old))
    stale = keep("Đang thuê nhà", "fact")
    asyncio.run(memory.store().update(conv.owner(ctx()), stale, expires=time.time() - 1))
    vid = config.propose("assistant_retention", {"archive_days": 200}, "compliance")["id"]
    config.decide(vid, "approve", "compliance2")
    from assistant.retention import sweep

    got = asyncio.run(sweep())
    assert got == {"conversations": 1, "turns": 1, "memory_items": 1}
    assert [c["id"] for c in conv.listing(ctx())] == [new]
    assert mem("list")["items"] == []


def test_the_archive_fold_equals_the_upstream_fold_on_vietnamese():
    from operonx_agents.memory import fold

    for text in [
        "Tài sản ròng ĐÃ tăng  2,3%\n nhờ bất động sản",
        "Quỹ trái phiếu, tiết kiệm 12 tháng; dự phòng ổn định",
        "Hãy nhớ: con đi du học năm 2030 — ưu tiên rủi ro thấp",
        "Nguyễn Minh Khoa, Đặng Thị Ứng",
    ]:
        assert memory.fast_fold(text) == fold(text)
