"""The assistant's tool registry (A1, ADR-0032): every tool is refused to the roles it is not for, every write asks
the person first and changes nothing until they confirm, and is read back after — a write that answered but did
not land is said as such, never as done. Through operonx-agents too: a write parks the run, Approve runs and
verifies it, Deny runs nothing."""

import asyncio
import hashlib
import inspect
import sqlite3
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from urllib.parse import urlparse

import pytest
from operonx_agents import Agent, Approve, Deny, Model, RunContext, Runner, SQLiteStateStore
from operonx_agents.testing import ScriptedLLM, asks, says, scripted

from assistant import base, registry
from assistant.base import KINDS, Ctx, NotConfirmed, ToolFailed, execute
from assistant.tools import PAGES
from control import roles
from wealth import store as wealth_store

ROLES = roles.ROLES
WRITES = sorted(n for n, t in registry.REGISTRY.items() if t.write)
READS = sorted(n for n, t in registry.REGISTRY.items() if not t.write)


def ctx(role, client="C01"):
    return Ctx(
        role=role,
        client_id=client if role in ("client", "rm") else None,
        scope="personal",
        question="",
        user=registry.DEMO_USER[role],
    )


def run(coro):
    return asyncio.run(coro)


def rss(url, *titles):
    """A feed as the source at ``url`` would serve it: its own links (the gate refuses a link off the source)."""
    when = format_datetime(datetime.now(timezone.utc) - timedelta(minutes=10))
    host = urlparse(url).netloc
    items = "".join(
        f"<item><title>{t}</title><link>https://{host}/a{k}.htm</link>"
        f"<description>{t}</description><pubDate>{when}</pubDate></item>"
        for k, t in enumerate(titles)
    )
    return f"<rss><channel>{items}</channel></rss>".encode()


# -- what each write needs before it can be asked for, and the arguments the model would give --


def _review_pending(mp):
    wealth_store.propose("C01", "tuition", "Học phí — Tích lũy đều", {"option": {"id": "light"}})
    return {"decision": "approved"}


def _feeds(mp):
    mp.setattr("news.ops._get", lambda url, timeout: rss(url, "VN-Index giảm mạnh, khối ngoại bán ròng"))
    return {}


def _an_event(mp):
    from events.graph import event_flow
    from news.graph import ingest_flow

    _feeds(mp)
    ids = run(base.run_graph(ingest_flow, feeds=None, now=None, tick=None, at=None))["ingest"]["ids"]
    ev = run(base.run_graph(event_flow, news_ids=ids, title=None, by="cio"))["event"]
    return {"event_id": ev["id"], "urgent": True, "reason": "Tác động lớn tới danh mục trái phiếu"}


def _an_alert(mp):
    from control import alerts

    return {"alert_id": alerts.raise_("news_feed", "vneconomy_ck", "Nguồn tin không lấy được")["id"]}


def _an_item(mp):
    from assistant import memory

    return {"item_id": run(memory.remember(ctx("client"), "goal", "Mua nhà năm sau")).id}


def _a_follow_up(mp):
    from assistant import followups

    return {"follow_up_id": followups.create(ctx("client"), "topic", topic="lãi suất")["id"]}


def _a_failed_challenge(mp):
    from views import agents
    from views.graph import cio_agent_flow

    ev = _an_event(mp)["event_id"]

    async def down(*a, **k):
        raise agents.AgentError("Agent Phản biện không trả lời")

    with mp.context() as m:
        m.setattr(agents, "challenge", down)
        v = run(base.run_graph(cio_agent_flow, event_id=ev, by="cio", mode=None))["result"]["view"]
    assert v["status"] == "PENDING_CHALLENGE"
    return {"view_id": v["id"]}


class FakeRun:
    run_id, items, failed, timed_out, errors = "R-1", [object()], [], [], {}


class FakeJob:
    def __init__(self, name):
        self.name = name

    async def run(self, **kw):
        return FakeRun()


def _a_job(mp):
    from control import jobs

    mp.setitem(jobs._JOBS, "audit_check", FakeJob("audit_check"))
    return {"job": "audit_check"}


SETUP = {  # write → (who asks, what must exist first → the model's arguments)
    "duyet_de_xuat": ("rm", _review_pending),
    "lay_tin": ("cio", _feeds),
    "gui_de_xuat": ("client", lambda mp: {"scenario": "co_phieu", "option": "light"}),
    "ghi_lien_he": ("rm", lambda mp: {"channel": "call", "note": "Hỏi thăm sau tin lãi suất"}),
    "khuyen_nghi": ("rm", lambda mp: {"title": "Tăng dự phòng", "actions": ["Gửi thêm 200 triệu kỳ hạn 12 tháng"]}),
    "danh_dau_khan": ("cio", _an_event),
    "chay_agent_cio": ("cio", lambda mp: {"event_id": _an_event(mp)["event_id"], "mode": ""}),
    "phan_bien_lai": ("cio", _a_failed_challenge),
    "chay_viec_nen": ("admin", _a_job),
    "yeu_cau_tai_khoan": ("admin", lambda mp: {"kind": "disable", "person": "cio2"}),
    "da_xem_canh_bao": ("cio", _an_alert),
    "ghi_nho": ("client", lambda mp: {"kind": "preference", "text": "Thích báo cáo ngắn"}),
    "quen": ("client", _an_item),
    "theo_doi": ("client", lambda mp: {"series": "VNINDEX", "op": "below", "level": 1200}),
    "huy_theo_doi": ("client", _a_follow_up),
}
DELETES = ("quen",)  # writes whose effect is an absence
BUSINESS = (
    "reviews",
    "rm_contacts",
    "events",
    "alerts",
    "news_items",
    "audit_log",
    "agent_jobs",
    "challenges",
    "job_runs",
    "account_requests",
)


def fingerprint(path):
    """The rows of the tables a write changes (the business records and the audit chain; the memory items and
    the follow-ups)."""
    h = hashlib.sha256(_rows(path, BUSINESS).encode())
    h.update(_rows(path.with_name("assistant.db"), ("operonx_agents_memory", "follow_ups")).encode())
    return h.hexdigest()


def _rows(path, tables):
    if not path.exists():
        return ""
    con = sqlite3.connect(path)
    have = {r[0] for r in con.execute("select name from sqlite_master where type = 'table'")}
    out = []
    for t in tables:
        if t in have:
            out += [repr(row) for row in con.execute(f"select * from {t} order by rowid")]  # noqa: S608 - fixed
    con.close()
    return "\n".join(out)


# -- the catalogue ------------------------------------------------------------------------------


def test_the_catalogue_is_whole():
    assert set(SETUP) == set(WRITES)  # a new write is tested here, or this fails
    assert set(registry.LABELS) == set(registry.REGISTRY)  # every step has a name in the panel
    for name, t in registry.REGISTRY.items():
        assert t.kind in KINDS and set(t.roles) <= set(ROLES), name
        assert not any(c.isdigit() for c in t.description), name  # the model reads no data
        assert t.page is None or t.page in PAGES, name
        assert t.timeout > 0, name
        if t.write:
            assert t.plan and t.verify, name
    for role in ROLES:
        tools = registry.agent_tools(role)
        assert {x.name for x in tools} == {t.name for t in registry.for_role(role)}
        for x in tools:
            t = registry.REGISTRY[x.name]
            assert (x.spec.approval == "always") == t.write and (x.spec.verify is not None) == t.write
            assert x.spec.readonly != t.write and x.spec.timeout == t.timeout


def test_the_copilot_keeps_its_thirteen_and_each_desks_reads():
    from copilot.tools import TOOLS

    # the thirteen, plus the staff desks' reads so the fallback answers each role (staff stress D13); Compliance's
    # and the specialists' desks left with their roles (OWN-FB-18)
    assert len(TOOLS) == 24 and all(TOOLS[n] is registry.REGISTRY[n] for n in TOOLS)
    assert not any(TOOLS[n].write for n in TOOLS if n not in ("lay_tin", "duyet_de_xuat"))


# -- role refusal: never offered, and refused when called anyway --------------------------------

REFUSED = [(n, r) for n, t in sorted(registry.REGISTRY.items()) for r in ROLES if r not in t.roles]


@pytest.mark.parametrize("name, role", REFUSED)
def test_a_tool_is_refused_to_a_role_it_is_not_for(name, role):
    t = registry.REGISTRY[name]
    assert name not in {x.name for x in registry.agent_tools(role)}  # not offered: the model cannot call it
    with pytest.raises(roles.Forbidden):
        run(registry.plan(t, ctx(role), {})) if t.write else base.allowed(t, role)
    # the agent tool built for a role that may use it, handed this person: refused before anything runs
    agent = next(x for x in registry.agent_tools(t.roles[0]) if x.name == name)
    with pytest.raises(roles.Forbidden):
        run(agent.function(RunContext(deps=ctx(role)), **{k: v for k, v in _defaults(t).items()}))


def _defaults(t):
    return {k: (p.default if p.default is not ... else "x") for k, p in t.params.items()}


# -- reads answer for their roles ---------------------------------------------------------------


@pytest.mark.parametrize("name", READS)
def test_a_read_answers_or_says_why_not(name):
    t = registry.REGISTRY[name]
    for role in t.roles:
        args = {"q": "học phí"} if name == "tim_kiem" else {"page": "toan-canh"} if name == "mo_trang" else {}
        try:
            out = run(execute(t, ctx(role), args))
        except ToolFailed as exc:  # an honest "cannot", e.g. no approved news for this family yet
            assert str(exc), (name, role)
            continue
        assert out["text"].strip(), (name, role)


# -- writes: asked first, nothing changed before the confirm, read back after -------------------


@pytest.mark.parametrize("name", WRITES)
def test_a_write_asks_first_changes_nothing_then_is_read_back(name, monkeypatch, state):
    t = registry.REGISTRY[name]
    role, setup = SETUP[name]
    asked = setup(monkeypatch)
    before = fingerprint(state)
    plan = run(registry.plan(t, ctx(role), asked))
    assert plan["summary"].endswith("?") and fingerprint(state) == before  # planning wrote nothing
    out = run(execute(t, ctx(role), plan["args"]))  # confirmed: runs, then its verifier reads it back
    assert out["text"].startswith("Đã") and fingerprint(state) != before
    verdict = t.verify(ctx(role), out)
    assert (run(verdict) if inspect.isawaitable(verdict) else verdict) is True


@pytest.mark.parametrize("name", WRITES)
def test_a_write_that_did_not_land_is_not_said_done(name, monkeypatch, state, tmp_path):
    t = registry.REGISTRY[name]
    role, setup = SETUP[name]
    plan = run(registry.plan(t, ctx(role), setup(monkeypatch)))
    if name in DELETES:  # a deletion that did not land: the same answer, the item still there
        out = {"text": "Đã quên mục này.", "data": {"id": plan["args"]["item_id"]}}
    else:
        out = run(execute(t, ctx(role), plan["args"]))
        # the same answer, from a write whose effect is not there (an empty state, in a folder of its own: the
        # row, the status, the memory item never written)
        (tmp_path / "elsewhere").mkdir()
        monkeypatch.setenv("MF_STATE", str(tmp_path / "elsewhere" / "state.db"))

    async def answered(c, a):
        return out

    monkeypatch.setattr(t, "run", answered)
    with pytest.raises(NotConfirmed, match="chưa xác nhận được"):
        run(execute(t, ctx(role), plan["args"]))


def test_the_copilot_says_an_unconfirmed_write_failed(monkeypatch):
    from copilot.ops import run_tool

    item = wealth_store.propose("C01", "tuition", "Học phí — Tích lũy đều", {"option": {"id": "light"}})
    t = registry.REGISTRY["duyet_de_xuat"]

    async def answered(c, a):  # says it decided, writes nothing
        return {"text": "Đã ghi: duyệt.", "data": {"id": item, "decision": "approved"}}

    monkeypatch.setattr(t, "run", answered)
    got = run(run_tool("duyet_de_xuat", {"item_id": item, "decision": "approved"}, True, "rm", "C01", "personal", ""))
    assert got["status"] == "failed" and "chưa xác nhận được" in got["text"]
    assert wealth_store.review(item)["status"] == "pending"


# -- through operonx-agents: the run parks on a write; Approve runs and verifies it; Deny runs nothing


def _agent(role):
    return Agent(
        name="assistant", model=Model("copilot"), instructions="Trợ lý.", tools=list(registry.agent_tools(role))
    )


@pytest.mark.parametrize("answer", ["approve", "deny"])
def test_an_agent_write_waits_for_the_person(answer, tmp_path, state):
    item = wealth_store.propose("C01", "tuition", "Học phí — Tích lũy đều", {"option": {"id": "light"}})
    store = SQLiteStateStore(str(tmp_path / "runs.db"))
    me = ctx("rm")
    llm = ScriptedLLM(asks(("duyet_de_xuat", {"decision": "approved"})), says("Xong."))

    async def go():
        with scripted(copilot=llm):
            res = await Runner.run(_agent("rm"), "Duyệt đề xuất đang chờ", deps=me, store=store)
            assert res.status == "interrupted" and wealth_store.review(item)["status"] == "pending"
            (wait,) = res.interruptions
            assert wait.tool == "duyet_de_xuat"
            plan = await registry.plan(registry.REGISTRY[wait.tool], me, wait.args)
            assert plan["summary"] == "Duyệt đề xuất “Học phí — Tích lũy đều”?"  # what the panel shows
            said = Approve() if answer == "approve" else Deny("Chưa")
            done = await Runner.resume(_agent("rm"), res.run_id, store=store, approvals={wait.id: said}, deps=me)
            return done, llm

    done, llm = run(go())
    assert done.status == "completed"
    tool_msg = next(m for m in llm.requests[-1]["messages"] if m.get("role") == "tool")
    if answer == "approve":
        assert wealth_store.review(item)["status"] == "approved"  # the RM's approval is final (OWN-FB-18)
        assert tool_msg["content"].rstrip().endswith("checked after it ran.")  # verified, and the model is told
    else:
        assert wealth_store.review(item)["status"] == "pending"
        assert "declined" in tool_msg["content"]


def test_the_barrier_off_shows_the_model_only_statuses():
    t = registry.REGISTRY["tong_quan"]
    agent = next(x for x in registry.agent_tools("client") if x.name == "tong_quan")
    shown = run(agent.function(RunContext(deps=Ctx("client", "C01", "personal", "", reads=False))))
    assert shown.model_dump_json() == '{"status":"ok","tool":"tong_quan","page":"#/client/tong-quan/toan-canh"}'
    full = run(agent.function(RunContext(deps=ctx("client"))))
    assert "Tài sản ròng" in full.text and t.name == full.tool
