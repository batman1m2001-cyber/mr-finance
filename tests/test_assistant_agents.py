"""The assistant's background agents (A6, FEAT-39, ADR-0031; OWN-AS-12, 18, 19): the memory consolidator distils an
idle conversation into a few long-term items — only where the model may read it, within its budget, merging repeats,
never keeping what a person could not, retried a bounded number of times, its cost per day recorded; follow-ups fire
once, from rules, when a market series crosses a level or an event on a topic is approved."""

import asyncio
import json
import time
from types import SimpleNamespace

import pytest
from operonx import Operon

from assistant import consolidate, followups, memory, registry
from assistant import conversations as conv
from assistant.base import ToolFailed
from assistant.graph import assistant_memory_flow

MEM = Operon(
    assistant_memory_flow,
    params={k: None for k in ("action", "item_id", "text", "kind", "query", "role", "client_id", "file_name", "data",
                              "key")},
)  # fmt: skip


def run(coro):
    return asyncio.run(coro)


def ctx(role="client", client_id="C01"):  # as the server builds it: the role's demo user when sign-in is off
    from assistant.ops import context, who

    return context({**who(role, client_id), "message": "", "route": "", "followed": None})


def mem(action, role="client", client_id="C01", **kw):
    out = asyncio.run(MEM.run(inputs={"action": action, "role": role, "client_id": client_id, **kw}))
    if "$errors" in out:
        raise ValueError(next(iter(out["$errors"].values())).get("message"))
    return out["memory"]


@pytest.fixture(autouse=True)
def model_on(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")


class Model:
    """The copilot model, scripted: each call answers the next of ``answers`` (a dict is sent as JSON, an exception
    raised), and keeps what it was sent."""

    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    def get(self, key):
        assert key == "llm:copilot"
        return self

    async def generate(self, **kw):
        self.calls.append(kw)
        a = self.answers.pop(0) if self.answers else {"items": []}
        if isinstance(a, Exception):
            raise a
        usage = SimpleNamespace(prompt_tokens=900, completion_tokens=120, cost=0.0011)
        msg = SimpleNamespace(content=json.dumps(a, ensure_ascii=False))
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=usage)


@pytest.fixture
def model(monkeypatch):
    def install(*answers):
        m = Model(*answers)
        monkeypatch.setattr("operonx.providers.ops._utils.resolve_hub", lambda: m)
        return m

    return install


def talk(*turns, role="client", client_id="C01", idle=True):
    """A conversation with these (question, answer) turns, left idle for 20 minutes unless ``idle`` is False."""
    c = ctx(role, client_id)
    cid = conv.start(c, turns[0][0])
    for q, a in turns:
        conv.record(cid, q, {"text": a})
    if idle:
        with conv.db() as con:
            con.execute("update conversations set updated = ? where id = ?", (time.time() - 20 * 60, cid))
    return cid


TALK = [("Tôi thích báo cáo thật ngắn, đừng dài dòng", "Vâng, tôi sẽ trả lời ngắn gọn."),
        ("Năm tới tôi muốn mua nhà cho con gái", "Mục tiêu mua nhà: xem trang Kế hoạch.")]  # fmt: skip


# -- the consolidator ---------------------------------------------------------------------------------------------


def test_an_idle_conversation_is_distilled_once_and_again_only_when_it_changes(model):
    m = model({"items": [{"kind": "preference", "text": "Thích báo cáo ngắn", "same_as": None},
                         {"kind": "goal", "text": "Mua nhà cho con gái", "same_as": None}]})  # fmt: skip
    fresh = talk(*TALK, idle=False)
    cid = talk(*TALK)
    assert [c["id"] for c in consolidate.due()] == [cid]  # the fresh one is not idle yet
    out = run(consolidate.run_due())
    assert out["done"] == 1 and out["added"] == 2 and out["tokens"] == 1020 and out["cost"] == 0.0011
    items = run(memory.items(ctx()))
    assert {i["text"] for i in items} == {"Thích báo cáo ngắn", "Mua nhà cho con gái"}
    assert all(i["confidence"] == 0.7 and i["source"] == {"conversation": cid, "by": "consolidator"} for i in items)
    sent = m.calls[0]["messages"][-1]["content"]
    assert "Tôi thích báo cáo thật ngắn" in sent and "mua nhà cho con gái" in sent
    assert m.calls[0]["max_tokens"] == consolidate.ANSWER_TOKENS
    assert consolidate.due() == [] and run(consolidate.run_due())["conversations"] == 0  # the same content: not again
    conv.record(cid, "Thêm: tôi không muốn đầu tư tiền số", {"text": "Đã hiểu."})
    with conv.db() as con:
        con.execute("update conversations set updated = ? where id in (?, ?)", (time.time() - 20 * 60, cid, fresh))
    assert {c["id"] for c in consolidate.due()} == {cid, fresh}  # changed, and the other now idle


def test_what_a_person_could_not_keep_is_not_kept_and_repeats_are_merged(model):
    mine = run(memory.remember(ctx(), "preference", "Thích báo cáo ngắn"))  # confirmed by the person: confidence 1
    model({"items": [
        {"kind": "preference", "text": "Muốn báo cáo thật ngắn gọn", "same_as": "m1"},  # the model says: the same
        {"kind": "fact", "text": "Tài khoản 190212345678 ở ngân hàng", "same_as": None},  # an account
        {"kind": "goal", "text": "Mua nhà cho con gái", "same_as": None},
        {"kind": "goal", "text": "Mua nhà cho con gái năm tới", "same_as": None},  # its words: the one before's
        {"kind": "constraint", "text": "Không đầu tư tiền số", "same_as": None},
        {"kind": "goal", "text": "Có năm tỷ để mua nhà", "same_as": None},  # a sixth: past the five, never read
    ]})  # fmt: skip
    talk(*TALK)
    out = run(consolidate.run_due())
    assert (out["added"], out["merged"], out["refused"]) == (2, 2, 1), out
    texts = {i["text"]: i for i in run(memory.items(ctx()))}
    assert texts["Thích báo cáo ngắn"]["confidence"] == 1 and mine.id == texts["Thích báo cáo ngắn"]["id"]
    # the person's own wording stands; the consolidator's own item takes the newer wording
    assert set(texts) == {"Thích báo cáo ngắn", "Mua nhà cho con gái năm tới", "Không đầu tư tiền số"}
    with conv.db() as con:
        row = dict(con.execute("select * from consolidations").fetchone())
    assert "nhà" not in json.dumps(row, ensure_ascii=False)  # the run keeps counts, never the text


def test_a_consolidated_item_is_reworded_by_the_next_conversation_but_a_confirmed_one_is_not(model):
    model({"items": [{"kind": "goal", "text": "Mua nhà", "same_as": None}]},
          {"items": [{"kind": "goal", "text": "Mua nhà ở Đà Nẵng", "same_as": "m1"}]})  # fmt: skip
    talk(*TALK)
    run(consolidate.run_due())
    talk(("Nhà ở Đà Nẵng nhé", "Đã ghi nhận."))
    run(consolidate.run_due())
    assert [i["text"] for i in run(memory.items(ctx()))] == ["Mua nhà ở Đà Nẵng"]


def test_where_the_model_may_not_read_nothing_is_sent(model, monkeypatch):
    from assistant import turn

    m = model()
    monkeypatch.setattr(turn, "model_reads", lambda: False)
    talk(*TALK)
    out = run(consolidate.run_due())
    assert out["skipped"] == 1 and m.calls == [] and run(memory.items(ctx())) == []
    assert consolidate.due() == []  # recorded: not asked again for the same content


def test_a_failure_is_retried_twice_then_left(model):
    m = model(RuntimeError("provider down"), ValueError("bad"), RuntimeError("again"), {"items": []})
    cid = talk(*TALK)
    for _ in range(4):
        run(consolidate.run_due())
    assert len(m.calls) == 3  # one try and two retries, then no more for this content
    with conv.db() as con:
        rows = [dict(r) for r in con.execute("select status, attempts, error from consolidations")]
    assert rows == [{"status": "failed", "attempts": 3, "error": "RuntimeError: again"}]
    conv.record(cid, "Một câu nữa", {"text": "Vâng."})
    with conv.db() as con:
        con.execute("update conversations set updated = ? where id = ?", (time.time() - 20 * 60, cid))
    run(consolidate.run_due())
    assert len(m.calls) == 4  # changed content: tried again


def test_a_long_conversation_keeps_to_the_budget_newest_first(model):
    m = model()
    long = [(f"Câu hỏi số {k}: " + "chi tiêu gia đình tháng này " * 30, "Trả lời " + "x" * 600) for k in range(40)]
    talk(*long)
    run(consolidate.run_due())
    sent = "".join(x["content"] for x in m.calls[0]["messages"])
    assert consolidate.tokens(sent) + consolidate.ANSWER_TOKENS <= consolidate.BUDGET
    assert "Câu hỏi số 39" in sent and "Câu hỏi số 0:" not in sent
    with conv.db() as con:
        assert "lượt cũ không đọc" in con.execute("select error from consolidations").fetchone()[0]


def test_the_cost_per_day_adds_up(model):
    model({"items": []}, {"items": []})
    talk(*TALK)
    talk(("Một cuộc khác", "Vâng."), role="rm", client_id="C01")
    run(consolidate.run_due())
    day = consolidate.costs()[0]
    assert (day["runs"], day["done"], day["tokens"], round(day["cost"], 4)) == (2, 2, 2040, 0.0022)


def test_the_job_is_scheduled_every_five_minutes():
    from app.main import APP
    from assistant.graph import assistant_consolidate_flow

    job = next(j for j in APP.jobs if j.name == "assistant_consolidate")
    assert job.graph is assistant_consolidate_flow


# -- follow-ups ---------------------------------------------------------------------------------------------------


def close(series, value, day="2026-10-16"):
    from market import store

    store.put(series, "test", "https://example.test", [(day, value)])


def test_a_market_follow_up_fires_once_for_its_owner_only():
    mine = followups.create(ctx(), "market", series_id="VNINDEX", op="below", level=1200)
    theirs = followups.create(ctx("client", "C02"), "market", series_id="VNINDEX", op="above", level=1300)
    close("VNINDEX", 1250)
    assert followups.check_market(["VNINDEX"])["fired"] == 0
    close("VNINDEX", 1180, "2026-10-17")
    assert followups.check_market(["VNINDEX"]) == {"checked": 2, "fired": 1, "expired": 0}
    assert followups.check_market(["VNINDEX"])["fired"] == 0  # once
    got = followups.get(ctx(), mine["id"])
    assert got["status"] == "fired" and got["fired"] == {"value": 1180.0, "date": "2026-10-17", "series": "VNINDEX"}
    assert followups.get(ctx(), theirs["id"]) is None  # another person's is not mine to read
    assert followups.get(ctx("client", "C02"), theirs["id"])["status"] == "open"
    assert [f["id"] for f in followups.unseen(ctx())] == [mine["id"]]
    assert followups.unseen(ctx("client", "C02")) == []


def test_the_market_job_checks_its_own_series():
    f = followups.create(ctx(), "market", series_id="SJC", op="above", level=80_000_000)
    close("SJC", 90_000_000)
    assert "VNINDEX" in followups.job_series("market_equity") and followups.job_series("market_gold") == ["SJC"]
    assert followups.check_market(followups.job_series("market_equity"))["checked"] == 0  # not its series
    assert followups.check_market(followups.job_series("market_gold"))["fired"] == 1
    assert followups.get(ctx(), f["id"])["status"] == "fired"


def test_a_topic_follow_up_fires_on_an_event_approved_after_it(monkeypatch):
    from apply import run as runs
    from events import store as events

    f = followups.create(ctx(), "topic", topic="lãi suất")
    later = time.time() + 1
    titles = {"EV-1": "NHNN giữ nguyên lai suat điều hành", "EV-2": "Giá dầu tăng mạnh"}
    effective = [
        {"id": "AR-1", "event_id": "EV-2", "history": [{"at": later, "status": "EFFECTIVE"}]},
        {"id": "AR-0", "event_id": "EV-1", "history": [{"at": f["created"] - 60, "status": "EFFECTIVE"}]},  # before
    ]
    monkeypatch.setattr(runs, "runs", lambda statuses=None: effective)
    monkeypatch.setattr(events, "get", lambda eid: {"title": titles[eid]})
    assert followups.check_topics()["fired"] == 0  # an older approval, and a run on another topic
    effective.append({"id": "AR-2", "event_id": "EV-1", "history": [{"at": later, "status": "EFFECTIVE"}]})
    assert followups.check_topics()["fired"] == 1
    got = followups.get(ctx(), f["id"])
    assert got["fired"] == {"event_id": "EV-1", "run_id": "AR-2", "title": "NHNN giữ nguyên lai suat điều hành"}
    from control import crypto

    with conv.db() as con:  # the person's words go through the data keys like the rest of assistant.db
        stored = con.execute("select topic from follow_ups").fetchone()[0]
    assert crypto.open_(stored, followups._place(f["id"])) == "lãi suất"


def test_open_follow_ups_are_capped_and_expire():
    for k in range(followups.OPEN_MAX):
        followups.create(ctx(), "topic", topic=f"chủ đề {k}")
    with pytest.raises(ValueError, match="đã có 20"):
        followups.create(ctx(), "topic", topic="một nữa")
    old = followups.create(ctx("client", "C02"), "market", series_id="USDVND", op="above", level=30000, days=1)
    assert followups.check_market(now=old["expires"] + 1)["expired"] >= 1
    assert followups.get(ctx("client", "C02"), old["id"])["status"] == "expired"


def test_what_cannot_be_followed_is_refused_before_anything_is_written():
    t = registry.REGISTRY["theo_doi"]
    with pytest.raises(ToolFailed, match="chuỗi"):
        run(registry.plan(t, ctx(), {"series": "", "topic": ""}))
    with pytest.raises(ToolFailed, match="Cần so sánh"):
        run(registry.plan(t, ctx(), {"series": "VNINDEX"}))
    plan = run(registry.plan(t, ctx(), {"series": "VNINDEX", "op": "below", "level": 1200}))
    assert plan["summary"] == "Báo cho bạn một lần khi VN-Index dưới 1.200 điểm (theo dõi 30 ngày)?"
    assert followups.listing(ctx()) == []


def test_the_page_lists_cancels_and_marks_seen():
    open_ = followups.create(ctx(), "topic", topic="lãi suất")
    fired = followups.create(ctx(), "market", series_id="VNINDEX", op="below", level=1200)
    close("VNINDEX", 1100)
    followups.check_market()
    got = mem("follow_ups")
    assert {f["id"] for f in got["follow_ups"]} == {open_["id"], fired["id"]}
    assert [f["id"] for f in got["unseen"]] == [fired["id"]]
    assert mem("follow_up_cancel", role="client", client_id="C02", key=open_["id"])["cancelled"] == 0
    assert mem("follow_up_cancel", key=open_["id"])["cancelled"] == 1
    assert mem("follow_up_seen", key=fired["id"])["seen"] == 1
    got = mem("follow_ups")
    assert got["unseen"] == [] and [f["id"] for f in got["follow_ups"]] == [fired["id"]]
