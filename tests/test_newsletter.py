"""The newsletter (BRD-FR-801, CONTENT-01 flow 1, CONTENT-02, CONTENT-03, SEC-04; BRD completion F8): drafted from
approved views only, general (no ticker, no portfolio), labelled, guarded against recommendation wording; Compliance
approves and is never the author; Private and retail at the same time unless a reason is recorded; a preview, never
sent. And the conflict-of-interest field on research, disclosed on the client's impact page."""

import asyncio
import json

import pytest
from operonx.app import Application
from starlette.testclient import TestClient
from test_views import GOLD, agent, decide, event

from apply import reads
from control import db, roles
from control.errors import BadRequest, Conflict
from news import store as news_store
from newsletter import compose, store
from research import conflict
from research import store as research

NOTE = "Đã kiểm tra nguồn công khai và xung đột lợi ích"


def approved_view(*titles):
    v = agent(event(*(titles or GOLD))["id"])["view"]
    decide(v["id"], "approve")
    return v["id"]


def draft(view_ids, **kw):
    return asyncio.run(store.draft(view_ids, kw.pop("by", "cio"), **kw))


def test_only_approved_views_make_a_letter_and_only_a_cio_drafts():
    pending = agent(event(*GOLD)["id"])["view"]["id"]
    with pytest.raises(Conflict, match="chưa được duyệt"):
        draft([pending])
    with pytest.raises(roles.Forbidden):
        draft([approved_view()], by="compliance")
    with pytest.raises(BadRequest, match="1–6"):
        draft([])


def test_a_cio_article_needs_a_body_goes_to_private_only_and_is_guarded():
    """OWN-FB-15: no views, the CIO's own words; a body under 40 characters or recommendation wording is refused."""
    with pytest.raises(BadRequest, match="40 đến 6000"):
        draft([], body="Ngắn quá")
    body = "Chính sách lãi suất tuần này giữ nguyên.\n\nNgân hàng Nhà nước tiếp tục bơm thanh khoản qua thị trường mở."
    n = draft([], title="Ghi chú chính sách", body=body)
    assert n["sections"] == [] and n["audience"] == "private" and n["mode"] == "article"
    assert n["body"].split("\n\n")[1].startswith("Ngân hàng") and n["guard"]["ok"]
    assert n["labels"]["ai"] == "Bài viết của CIO, không dùng AI"
    bad = store.act(n["id"], "edit", "cio", changes={"body": body + " Khuyến nghị mua ngay cổ phiếu ngân hàng."})
    assert not bad["guard"]["ok"]
    with pytest.raises(BadRequest, match="cần nội dung"):
        store.act(n["id"], "edit", "cio", changes={"body": ""})


def test_the_template_letter_names_no_ticker_and_carries_every_label():
    vid = approved_view()
    n = draft([vid])
    assert n["status"] == "DRAFT" and n["intro_by"] == "template" and n["guard"]["ok"], n["guard"]
    [s] = n["sections"]
    assert s["view_id"] == vid and s["impacts"] and s["branches"] and s["outlets"]
    text = compose.text_of(n)
    from views import schema

    assert not [t for t in schema.catalogue()["ticker"] if f" {t} " in f" {text} "]
    labels = n["labels"]
    assert set(labels) >= {"ai", "responsible", "time", "not_advice", "contact", "conflicts"}
    assert "không phải khuyến nghị" in labels["not_advice"] and "RM" in labels["contact"]
    assert labels["conflicts"] == [conflict.NONE]


def test_a_cio_edit_with_recommendation_wording_cannot_go_to_compliance():
    n = draft([approved_view()])
    bad = store.act(n["id"], "edit", "cio", changes={"intro": "Quý khách nên mua thêm cổ phiếu ngân hàng ngay."})
    assert not bad["guard"]["ok"] and any("khuyến nghị" in f for f in bad["guard"]["findings"])
    with pytest.raises(Conflict, match="Chưa gửi được"):
        store.act(n["id"], "submit", "cio")
    fixed = store.act(n["id"], "edit", "cio", changes={"intro": "Thị trường tuần qua có hai diễn biến đáng chú ý."})
    assert fixed["guard"]["ok"] and fixed["intro_by"] == "cio"


def test_private_and_retail_get_it_at_the_same_time_unless_a_reason_is_given():
    vid = approved_view()
    same = draft([vid], distribution={"send_at": "2026-10-20T08:00:00+07:00"})
    d = same["distribution"]
    assert d["private_at"] == d["retail_at"] and d["private_early_hours"] == 0
    with pytest.raises(BadRequest, match="căn cứ"):
        draft([vid], distribution={"send_at": "2026-10-20T08:00:00+07:00", "private_early_hours": 2})
    early = draft(
        [vid],
        distribution={
            "send_at": "2026-10-20T08:00:00+07:00",
            "private_early_hours": 2,
            "early_reason": "Khách Private đăng ký nhận bản tin trước giờ mở cửa",
        },
    )["distribution"]
    assert early["retail_at"] - early["private_at"] == 2 * 3600 and early["early_reason"]


def test_compliance_approves_never_the_author_and_a_return_goes_back_to_the_cio():
    n = draft([approved_view()])
    with pytest.raises(roles.Forbidden):
        store.act(n["id"], "approve", "cio")  # only Compliance
    with pytest.raises(roles.Forbidden):
        store.act(n["id"], "submit", "compliance")
    with pytest.raises(Conflict, match="không chờ duyệt"):
        store.act(n["id"], "approve", "compliance")
    store.act(n["id"], "submit", "cio")
    with pytest.raises(BadRequest, match="10 ký tự"):
        store.act(n["id"], "return", "compliance", note="sửa")
    back = store.act(n["id"], "return", "compliance", note="Phần mở đầu cần nói rõ nguồn tin")
    assert back["status"] == "RETURNED"
    store.act(n["id"], "edit", "cio", changes={"intro": "Bản tin tổng hợp nhận định đã duyệt, nguồn tin công khai."})
    store.act(n["id"], "submit", "cio")
    done = store.act(n["id"], "approve", "compliance", note="Đạt")
    assert done["status"] == "APPROVED" and done["approved_by"] == "compliance" and done["sent"] is False
    statuses = [h["status"] for h in done["history"]]
    assert statuses == ["DRAFT", "PENDING_COMPLIANCE", "RETURNED", "RETURNED", "PENDING_COMPLIANCE", "APPROVED"]
    with db.tx() as con:
        rows = con.execute("select action, data from audit_log where object = ? order by seq", (n["id"],)).fetchall()
    acts = [r[0] for r in rows]
    assert acts[0] == "newsletter.draft" and acts[-1] == "newsletter.approve"
    assert json.loads(rows[-1][1])["preview_only"] is True  # nothing is sent


def test_sec04_the_author_cannot_approve_even_with_both_roles(monkeypatch):
    n = draft([approved_view()])
    store.act(n["id"], "submit", "cio")
    real = roles.require
    monkeypatch.setattr(roles, "require", lambda who, *r: None if who == "cio" else real(who, *r))
    with pytest.raises(roles.Forbidden, match="khác người soạn"):
        store.act(n["id"], "approve", "cio")


def test_agent_mode_is_labelled_mock_without_models_and_a_failing_agent_falls_back(monkeypatch):
    vid = approved_view()
    n = draft([vid], mode="agent")
    assert n["intro_by"] == "mock" and "mô phỏng" in n["intro"] and n["guard"]["ok"]

    async def says_buy(sections):
        return "Quý khách nên mua vàng ngay hôm nay.", "live", []

    monkeypatch.setattr(compose, "agent_intro", says_buy)
    n = draft([vid], mode="agent")
    assert n["intro_by"] == "template" and n["guard"]["ok"]
    assert "không qua kiểm tra nội dung" in n["agent_findings"][0]


def test_the_endpoints():
    vid = approved_view()
    with TestClient(Application.find(".").asgi()) as c:
        r = c.post("/api/newsletters", json={"view_ids": [vid], "by": "cio"})
        assert r.status_code == 200, r.text
        nid = r.json()["newsletter"]["id"]
        d = c.get("/api/newsletters").json()
        assert d["newsletters"][0]["id"] == nid and vid in [v["id"] for v in d["approved_views"]]
        assert "sections" not in d["newsletters"][0]
        assert c.get(f"/api/newsletters/{nid}").json()["newsletter"]["sections"]
        r = c.post("/api/newsletters/act", json={"newsletter_id": nid, "action": "approve", "by": "compliance"})
        assert r.status_code == 409
        assert (
            c.post("/api/newsletters/act", json={"newsletter_id": nid, "action": "x", "by": "cio"}).status_code == 400
        )


# -- conflict of interest on research (CONTENT-03) ----------------------------------------------


def report(**kw):
    return {
        "kind": "research",
        "report_no": "RS-2026-201",
        "title": "Techcombank: tín dụng quý 3 tăng tốc",
        "summary": "Tăng trưởng tín dụng ngân hàng cao hơn kỳ vọng, nợ xấu ổn định.",
        "release_at": "2026-10-01T08:00:00+07:00",
        **kw,
    }


def test_research_naming_a_related_party_must_declare_it():
    with pytest.raises(research.ResearchError, match="xung đột lợi ích"):
        research.upload(report(), "cio")
    with pytest.raises(research.ResearchError, match="20 ký tự"):
        research.upload(report(conflict={"related": True, "parties": ["Techcombank"], "statement": "Có"}), "cio")
    ok = research.upload(
        report(conflict={"related": True, "statement": "Techcombank là công ty mẹ của đơn vị phát hành"}), "cio"
    )
    assert ok["conflict"]["parties"] == ["Techcombank"] and ok["conflict"]["mentions"] == ["Techcombank"]
    plain = research.upload(report(title="Ngân hàng: tín dụng quý 3", report_no="RS-2"), "cio")
    assert plain["conflict"]["related"] is False


def test_a_declared_conflict_shows_on_the_clients_impact_page_and_in_the_letter():
    statement = "Techcombank là công ty mẹ của đơn vị phát hành báo cáo"
    item = research.upload(report(conflict={"related": True, "statement": statement}), "cio")
    research.decide(item["id"], "release", "compliance", NOTE)
    [n] = [n for n in news_store.inbox() if n.get("research_id") == item["id"]]
    from test_views import EVENT, ok

    ev = ok(EVENT, news_ids=[n["id"]], by="cio")["event"]
    v = agent(ev["id"])["view"]
    decide(v["id"], "approve")
    page = reads.family_impact("C01", "client")
    assert any(statement in c for c in page["labels"]["conflicts"]), page["labels"]
    assert any(statement in c for i in page["items"] for c in i["conflicts"])
    letter = draft([v["id"]])  # the research's disclosure covers Techcombank: no second declaration
    assert any(statement in c for c in letter["labels"]["conflicts"])
    with pytest.raises(BadRequest, match="TCBS"):  # a party the CIO adds is theirs to declare
        store.act(letter["id"], "edit", "cio", changes={"intro": "Bản tin có nhận định của TCBS về tín dụng."})


def test_a_headline_with_banned_words_is_reworded_by_the_cio_before_it_goes(monkeypatch):
    vid = approved_view()
    real = compose.events.get
    monkeypatch.setattr(compose.events, "get", lambda eid: {**real(eid), "title": "Tiền trong nước bắt đáy"})
    n = draft([vid])
    assert not n["guard"]["ok"] and "bắt đáy" in n["guard"]["findings"][0]  # the event's headline
    n = store.act(
        n["id"],
        "edit",
        "cio",
        changes={
            "intro": "Bản tin tuần này có một diễn biến đáng chú ý.",
            "headings": {vid: "Dòng tiền trong nước khi chỉ số giảm sâu"},
        },
    )
    assert n["guard"]["ok"] and n["sections"][0]["heading"].startswith("Dòng tiền")
    assert store.act(n["id"], "submit", "cio")["status"] == "PENDING_COMPLIANCE"


def test_agent_mode_in_inbox_mode_uses_the_template_and_says_why(monkeypatch):
    from views import agents

    vid = approved_view()
    monkeypatch.setattr(agents, "configured_mode", lambda: "inbox")
    n = draft([vid], mode="agent")
    assert n["intro_by"] == "template" and "hộp chờ" in n["agent_findings"][0]
