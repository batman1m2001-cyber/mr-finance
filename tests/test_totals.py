"""A total is a count, never the length of a page (docs/ASSISTANT_DATA_PLAN.md §2, D1). Each test seeds more rows
than the cap a page or tool used to stop at, and checks that the number shown or said is the database's count."""

import asyncio
import time

from starlette.testclient import TestClient

from assistant.base import Ctx
from news import store as news


def seed(n, held=(), relevance="high", title="Lãi suất điều hành", status="new"):
    """n news items, newest last; the indices in ``held`` name a restricted company (held for Compliance)."""
    now = time.time()
    rows = [
        {"source": "cafef_ck", "url_key": f"u{i}", "title_key": f"t{i}", "published": now - 86400 + i,
         "ingested": now, "kind": "domestic", "status": status, "relevance": relevance, "title": f"{title} {i}",
         "outlet": "CafeF", "label": "Trong nước", "summary": "", "restricted": ["VCB"] if i in held else []}
        for i in range(n)
    ]  # fmt: skip
    assert news.add(rows)[1] == 0
    return rows


def ctx(role):
    return Ctx(role=role, client_id=None, scope="personal", question="")


def test_the_inbox_page_gets_a_page_of_rows_and_the_counted_total():
    """The inbox page said "300 tin chờ xử lý" for 1,415: its header was the length of a 300-row page."""
    from app.web import app

    seed(310)
    http = TestClient(app)
    d = http.get("/api/news/inbox?limit=40").json()
    assert len(d["items"]) == 40 and d["total"] == 310
    d = http.get("/api/news/inbox?limit=40&q=" + "điều hành 30").json()  # words: matched as the list matches them
    assert d["total"] == len(news.inbox(query="điều hành 30", limit=None)) == 11  # 30, 300…309
    held = http.get("/api/news/inbox?held=1").json()
    assert held["items"] == [] and held["total"] == 0
    page = open("web/pages/inbox.js", encoding="utf-8").read()
    assert "${num(total)} tin chờ xử lý" in page and "items.length} tin chờ" not in page


def test_count_matches_the_list_for_every_filter():
    seed(30, held={3, 4})
    for f in ({}, {"status": "all"}, {"held": True}, {"held": False}, {"relevance": "high"}, {"query": "hành 2"}):
        assert news.count(**f) == len(news.inbox(**f, limit=None)), f
    assert news.count(held=True) == 2 and len(news.inbox(limit=10)) == 10


def test_the_cio_desk_counts_the_news_stage_past_its_old_cap_of_5000():
    from desk import reads as desk_reads

    seed(5003)
    d = desk_reads.desk("cio", {"id": "cio", "role": "cio"})
    stage = next(s for s in d["pipeline"] if s["id"] == "news")
    assert stage["count"] == 5003 and stage["waits"] == 5003
    assert len(d["items"]["news"]) == 5


def test_search_finds_and_counts_past_5000_and_says_six_of_how_many():
    from assistant.actions import search
    from search.ops import LIMIT, find

    seed(5001)
    oldest = {"source": "cafef_ck", "url_key": "old", "title_key": "old", "published": 1.0, "ingested": 1.0}
    oldest.update(kind="domestic", status="new", relevance="low", title="Trái phiếu xanh", summary="")
    news.add([oldest])
    old = find("trai phieu xanh", "cio", [], [])
    assert [h["label"] for h in old["hits"]] == ["Trái phiếu xanh"]  # the oldest of 5,002: past the old 5,000
    many = find("lai suat", "cio", [], [])
    assert len(many["hits"]) == LIMIT and many["total"] == 5001 and many["found"]["news"] == 5001
    out = asyncio.run(search(ctx("cio"), {"q": "lai suat"}))
    assert out["text"].startswith(f"{LIMIT} / 5001 kết quả") and out["data"]["total"] == 5001


def test_the_alerts_tool_and_the_bell_count_past_the_page_of_50():
    from app.web import app
    from assistant.actions import system_alerts
    from control import alerts

    for i in range(53):
        alerts.raise_("news_feed", f"feed{i}", f"Nguồn {i} lỗi")
    first = alerts.for_role("cio")[-1]
    alerts.ack(first["id"], "cio")
    assert len(alerts.for_role("cio")) == 50
    assert alerts.counts("cio") == {"total": 53, "open": 52} and alerts.counts("compliance") == {"total": 0, "open": 0}
    out = asyncio.run(system_alerts(ctx("cio"), {}))
    assert out["text"].startswith("53 cảnh báo hệ thống, 52 chưa ai xem")
    assert (out["data"]["total"], out["data"]["open"]) == (53, 52)
    http = TestClient(app)
    bell = http.get("/api/system/alerts?role=cio").json()
    assert len(bell["alerts"]) == 50 and (bell["total"], bell["open"]) == (53, 52)
    assert http.get("/api/system").json()["alerts_open"] == 52
    header = open("web/header.js", encoding="utf-8").read()
    assert "sys.open" in header and "limit=1000" not in header


def test_the_held_news_tool_says_every_held_item_not_those_on_the_first_200():
    from assistant.tools import held

    seed(260, held=set(range(0, 260, 20)))  # 13 held, most of them older than the newest 200
    out = asyncio.run(held(ctx("compliance"), {}))
    assert out["data"]["items"] == 13 and out["text"].startswith("13 tin đang bị giữ")
