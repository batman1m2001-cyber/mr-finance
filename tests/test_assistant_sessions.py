"""Sessions (OWN-SS-01…08, SESSIONS_PLAN.md, FEAT-37): a conversation is a session that can be renamed, archived and
brought back; a turn is kept from the moment it starts, so a refresh mid-answer finds the question and the tools that
ran; titles and goals are generated and refined, never over a name the person chose; compaction writes a structured
summary that the session keeps and the model can read past; and every session is its owner's alone."""

import asyncio
import json
import time
from types import SimpleNamespace

import pytest
from operonx import Operon
from operonx_agents.testing import ScriptedLLM, asks, says, scripted

from assistant import conversations as conv
from assistant import ops
from assistant.graph import assistant_conversations_flow, assistant_flow
from control import config

INPUTS = ("message", "role", "client_id", "scope", "route", "goals", "turn_id", "approvals", "conversation_id")
ASK = Operon(assistant_flow, params={k: None for k in INPUTS})
CONV_INPUTS = ("action", "conversation_id", "role", "client_id", "title")
CONVS = Operon(assistant_conversations_flow, params={k: None for k in CONV_INPUTS})


@pytest.fixture(autouse=True)
def model_on(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")


def ask(message=None, cid=None, role="client", client_id="C01", turn_id=None, approvals=None):
    inputs = {"message": message, "role": role, "client_id": client_id, "scope": "personal",
              "route": "#/client/tong-quan", "turn_id": turn_id, "approvals": approvals,
              "conversation_id": cid}  # fmt: skip
    out = asyncio.run(ASK.run(inputs=inputs))
    assert "$errors" not in out, out["$errors"]
    return out["assistant"]


def convs(action, cid=None, role="client", client_id="C01", title=None):
    out = asyncio.run(CONVS.run(inputs={"action": action, "conversation_id": cid, "role": role,
                                        "client_id": client_id, "title": title}))  # fmt: skip
    if "$errors" in out:
        raise ValueError(next(iter(out["$errors"].values())).get("message"))
    return out["conversations"]


def body(message, cid=None, client_id="C01"):
    return {"message": message, "role": "client", "client_id": client_id, "scope": "personal",
            "route": "#/client/tong-quan", "conversation_id": cid}  # fmt: skip


# -- S1: rename, archive, restore; owner only ----------------------------------------------------------------------


def test_a_session_is_renamed_archived_and_brought_back_by_its_owner_only():
    with scripted(copilot=ScriptedLLM(says("Một."), says("Hai."))):
        a = ask("Tài sản của tôi thế nào?")["conversation_id"]
        b = ask("Dòng tiền tháng này?")["conversation_id"]
    got = convs("rename", a, title="  Tài sản  tháng 10 ")
    assert got["conversation"]["title"] == "Tài sản tháng 10" and got["conversation"]["title_auto"] == 0
    with pytest.raises(ValueError, match="Tên"):
        convs("rename", a, title="   ")
    convs("archive", b)
    assert [c["id"] for c in convs("list")["items"]] == [a]  # archived: out of the list and the resume
    assert [c["id"] for c in convs("list_archived")["items"]] == [b]
    assert convs("open", b)["conversation"]["archived"]  # still opens, from Bộ nhớ or the archive view
    convs("restore", b)
    assert {c["id"] for c in convs("list")["items"]} == {a, b} and convs("list_archived")["items"] == []
    for role, client in (("client", "C02"), ("rm", "C01")):
        for action, extra in (("rename", {"title": "x"}), ("archive", {}), ("restore", {})):
            with pytest.raises(ValueError, match="Không có cuộc trò chuyện này"):
                convs(action, a, role=role, client_id=client, **extra)
    assert convs("open", a)["conversation"]["title"] == "Tài sản tháng 10"


# -- S1: a turn is kept from its start ------------------------------------------------------------------------------


async def _cut_after_first_step(payload):
    """The turn as the stream reads it, closed (the browser refreshed) once the first tool has ended."""
    gen = ops.turn_events(ops.request_of(**{k: payload.get(k) for k in ops.FIELDS}))
    seen = []
    async for e in gen:
        seen.append(e)
        if e.get("type") == "step" and e.get("phase") == "end":
            break
    await gen.aclose()
    return seen


def test_a_refresh_mid_answer_keeps_the_question_and_the_tools_that_ran():
    llm = ScriptedLLM(asks(("tong_quan", {})), asks(("dong_tien", {})), says("Ổn."))
    with scripted(copilot=llm):
        seen = asyncio.run(_cut_after_first_step(body("Tài sản và dòng tiền của tôi?")))
    assert [(e["type"], e["phase"]) for e in seen] == [("step", "start"), ("step", "end")]
    items = convs("list")["items"]
    assert len(items) == 1 and items[0]["turns"] == 1
    t = convs("open", items[0]["id"])["turns"][0]
    assert t["question"] == "Tài sản và dòng tiền của tôi?" and t["status"] == "interrupted"
    assert [(s["tool"], s["status"]) for s in t["answer"]["steps"]] == [("tong_quan", "ok")]
    assert "ngắt" in t["answer"]["text"]


def test_a_turn_left_running_by_a_dead_server_reads_as_interrupted():
    with scripted(copilot=ScriptedLLM(says("Ổn."))):
        cid = ask("Câu đầu")["conversation_id"]
    seq = conv.begin(cid, "Câu thứ hai")
    conv.progress(cid, seq, [{"tool": "tong_quan", "label": "Tổng quan", "status": "ok"}])
    assert convs("open", cid)["turns"][1]["status"] == "running"  # still within the run's wall clock
    with conv.db() as con:
        con.execute("update turns set at = ? where conversation_id = ? and seq = ?", (time.time() - 600, cid, seq))
    t = convs("open", cid)["turns"][1]
    assert t["status"] == "interrupted" and t["answer"]["steps"][0]["tool"] == "tong_quan"


def test_a_finished_turn_is_one_row_with_its_answer():
    with scripted(copilot=ScriptedLLM(asks(("tong_quan", {})), says("Tài sản ròng tăng."))):
        a = ask("Tài sản của tôi thế nào?")
    got = convs("open", a["conversation_id"])
    assert got["conversation"]["turns"] == 1 and len(got["turns"]) == 1
    t = got["turns"][0]
    assert t["status"] == "ok" and t["answer"]["text"] == "Tài sản ròng tăng." and "turn_seq" not in t["answer"]


# -- S1: two signed-in people, over HTTP ------------------------------------------------------------------------------


@pytest.fixture
def http(monkeypatch):
    from operonx.app import Application
    from starlette.testclient import TestClient

    monkeypatch.setenv("MF_AUTH", "on")
    monkeypatch.setenv("MF_DEMO_ACCOUNTS", "on")
    with TestClient(Application.find(".").asgi()) as c:
        yield c


def test_two_signed_in_customers_never_see_each_others_sessions(http):
    from people import auth

    def as_(who):
        http.cookies.clear()
        http.cookies.set(auth.COOKIE, auth.issue(who))
        return http

    def post(who, path, payload):
        r = as_(who).post(path, json=payload)
        return r.status_code, r.json()

    with scripted(copilot=ScriptedLLM(says("Ổn."), says("Cũng ổn."))):
        _, a = post("C01", "/api/assistant", body("Tài sản của tôi?"))
        _, b = post("C02", "/api/assistant", body("Tài sản của tôi?", client_id="C02"))
    ca, cb = a["assistant"]["conversation_id"], b["assistant"]["conversation_id"]
    lst = lambda who, cid=None: post(who, "/api/assistant/conversations", {"action": "list", "role": "client"})  # noqa: E731
    assert [c["id"] for c in lst("C01")[1]["conversations"]["items"]] == [ca]
    assert [c["id"] for c in lst("C02")[1]["conversations"]["items"]] == [cb]
    for action, extra in (("open", {}), ("rename", {"title": "x"}), ("archive", {}), ("delete", {})):
        code, out = post("C02", "/api/assistant/conversations", {"action": action, "conversation_id": ca,
                                                                  "role": "client", **extra})  # fmt: skip
        assert "Tài sản" not in json.dumps(out, ensure_ascii=False), (action, out)
    # naming another person's client id changes nothing: a customer is always themselves
    code, out = post("C02", "/api/assistant/conversations", {"action": "list", "role": "client", "client_id": "C01"})
    assert [c["id"] for c in out["conversations"]["items"]] == [cb]
    assert lst("C01")[1]["conversations"]["items"][0]["title"] != "x"


# -- S2: titles and goals ---------------------------------------------------------------------------------------------


class Hub:
    """The copilot model as the title request reaches it (``resolve_hub``): each call answers the next of
    ``answers`` (a dict as JSON, a string as is), and keeps what it was sent."""

    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    def get(self, key):
        assert key == "llm:copilot"
        return self

    async def generate(self, **kw):
        self.calls.append(kw)
        a = self.answers.pop(0)
        content = a if isinstance(a, str) else json.dumps(a, ensure_ascii=False)
        usage = SimpleNamespace(prompt_tokens=300, completion_tokens=40, cost=0.0002)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))], usage=usage)


@pytest.fixture
def hub(monkeypatch):
    def install(*answers):
        h = Hub(*answers)
        monkeypatch.setattr("operonx.providers.ops._utils.resolve_hub", lambda: h)
        return h

    return install


def test_the_title_and_goal_are_written_after_the_first_answer_and_once(hub):
    with scripted(copilot=ScriptedLLM(asks(("dong_tien", {})), says("Tháng 9 bạn dư 30 triệu."))):
        a = ask("Cho tôi xem dòng tiền tháng này, chi nhiều nhất vào đâu và còn dư bao nhiêu?")
    cid = a["conversation_id"]
    assert a["describe"] is True
    assert convs("list")["items"][0]["title"] == "Cho tôi xem dòng tiền tháng này, chi nhiều nhất…"  # until then
    h = hub({"title": "Dòng tiền tháng 9.", "goal": "Biết tháng này chi vào đâu và còn dư bao nhiêu"})
    got = convs("describe", cid)["conversation"]
    assert got["title"] == "Dòng tiền tháng 9" and got["goal"].startswith("Biết tháng này chi")
    assert got["cost_usd"] == 0.0002 and len(h.calls) == 1
    sent = json.dumps(h.calls[0]["messages"], ensure_ascii=False)
    assert "dòng tiền tháng này" in sent and "Tháng 9 bạn dư 30 triệu." in sent
    assert convs("describe", cid)["conversation"]["title"] == "Dòng tiền tháng 9" and len(h.calls) == 1  # once


def test_it_is_written_again_at_the_fourth_turn_but_never_over_a_name_the_person_chose(hub):
    llm = ScriptedLLM(*[says(f"Trả lời {i}.") for i in range(4)])
    with scripted(copilot=llm):
        cid = ask("Tài sản của tôi?")["conversation_id"]
        hub({"title": "Tài sản hiện tại", "goal": "Xem tài sản"})
        convs("describe", cid)
        convs("rename", cid, title="Của tôi")
        flags = [ask(q, cid=cid)["describe"] for q in ("Còn nợ?", "Và mục tiêu?", "Tóm lại nên chú ý gì?")]
    assert flags == [False, False, True]
    h = hub({"title": "Tài sản, nợ và mục tiêu", "goal": "Nắm toàn cảnh tài chính và điều cần chú ý"})
    got = convs("describe", cid)["conversation"]
    assert got["title"] == "Của tôi" and got["goal"] == "Nắm toàn cảnh tài chính và điều cần chú ý"
    assert len(h.calls) == 1


def test_template_mode_sends_nothing_for_a_title(hub):
    vid = config.propose("client_ai", {"mode": "off", "onprem_hosts": []}, "admin")["id"]
    config.decide(vid, "approve", "admin2")
    with scripted(copilot=ScriptedLLM(asks(("tong_quan", {})), says("Xem bên dưới."))):
        a = ask("Tài sản của Nguyễn Minh Khoa thế nào? Tôi muốn biết chi tiết")
    h = hub()
    got = convs("describe", a["conversation_id"])["conversation"]
    assert h.calls == [] and got["title"] == "Tài sản của Nguyễn Minh Khoa thế nào?" and got["goal"] is None


def test_a_broken_title_answer_changes_nothing(hub):
    with scripted(copilot=ScriptedLLM(says("Ổn."))):
        cid = ask("Tài sản của tôi?")["conversation_id"]
    hub("không phải JSON")
    assert convs("describe", cid)["conversation"]["title"] == "Tài sản của tôi?"


# -- S3: structured, recoverable compaction ---------------------------------------------------------------------------

SECTIONS = """## Mục tiêu
- Theo dõi dòng tiền và mục tiêu học phí
## Quyết định
- Giữ quỹ dự phòng 6 tháng
## Sở thích và giới hạn người dùng nêu
- Thích câu trả lời ngắn
## Việc còn dở
- Xem lại kịch bản lãi suất
## Thực thể (mã, tài sản, mục tiêu, tin, khách hàng)
- G1 học phí
## Kết quả công cụ (công cụ — điều chính — ngày số liệu)
- dong_tien — dư 30 triệu — 2026-09-30
## Tham chiếu (trang, mã để đọc lại)
- #/client/dong-tien"""


def _long(turns=12, at=10):
    script = []
    for i in range(turns):
        script.append(says(f"Trả lời {i}.", prompt_tokens=19_000 if i == at else 1_000))
        if i == at:
            script.append(says(SECTIONS))  # the summarizer
    llm = ScriptedLLM(*script)
    cid = None
    with scripted(copilot=llm):
        for i in range(turns):
            cid = ask(f"Câu hỏi {i} về dòng tiền", cid=cid)["conversation_id"]
    return llm, cid


def test_a_long_session_compacts_into_the_seven_sections_and_keeps_them():
    from assistant import turn

    llm, cid = _long()
    asked = [r for r in llm.requests if not r.get("tools")]
    assert len(asked) == 1
    prompt = asked[0]["messages"][-1]["content"]
    assert prompt.startswith(turn.SUMMARY) and "Câu hỏi 0 về dòng tiền" in prompt and "Write it as notes" not in prompt
    got = convs("open", cid)
    assert got["conversation"]["summary"] == SECTIONS and got["conversation"]["summary_at"]
    assert len(got["turns"]) == 12  # nothing deleted
    assert [t["answer"]["compacted"] for t in got["turns"]].index(True) == 10
    llm2 = ScriptedLLM(says("Theo tóm tắt, bạn giữ quỹ dự phòng 6 tháng."))
    with scripted(copilot=llm2):
        ask("Ta đã quyết định gì?", cid=cid)
    sent = json.dumps(llm2.requests[-1]["messages"], ensure_ascii=False)
    assert "[conversation summary]\\n## Mục tiêu" in sent and "Câu hỏi 0 về dòng tiền" not in sent  # continued


def test_what_the_summary_left_out_is_read_back_from_this_session_only():
    llm, cid = _long()
    with scripted(copilot=ScriptedLLM(says("Khác."))):
        other = ask("Câu hỏi 0 về dòng tiền ở phiên khác")["conversation_id"]
    reread = ScriptedLLM(asks(("doc_lai_phien", {"q": "câu hỏi 0", "n": 3})), says("Lượt đầu bạn hỏi về dòng tiền."))
    with scripted(copilot=reread):
        a = ask("Lúc đầu tôi hỏi gì?", cid=cid)
    step = a["steps"][0]
    assert step["tool"] == "doc_lai_phien" and step["status"] == "ok"
    assert "[lượt 1] Bạn: Câu hỏi 0 về dòng tiền" in step["text"] and "Trả lời 0." in step["text"]
    assert "phiên khác" not in step["text"] and other != cid


def test_the_upstream_summary_prompt_still_has_the_shape_we_replace():
    from operonx_agents.context import compaction

    from assistant import turn

    assert turn.UPSTREAM_PREAMBLE_END in compaction.summary_prompt([{"role": "user", "content": "x"}])
