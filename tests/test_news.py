"""The news (src/news): reading feeds, the gates, sorting, the restricted hold, the inbox. The feeds
here are written for the tests (no network, no copied articles)."""

import asyncio
import time
from datetime import datetime, timezone
from email.utils import format_datetime

import pytest
from operonx import Operon
from starlette.testclient import TestClient

from news import rss, rules, store
from news.graph import dismiss_flow, ingest_flow, release_flow
from news.ops import config

NOW = 1_792_000_000.0  # 2026-10-14
INGEST = Operon(ingest_flow, params={"feeds": None, "now": None, "tick": None, "at": None})


def rfc(ts):
    return format_datetime(datetime.fromtimestamp(ts, timezone.utc))


def feed(*items, bom=False):
    body = "".join(
        f"<item><title><![CDATA[{t}]]></title><link>{link}</link><description><![CDATA[{d}]]></description>"
        + (f"<pubDate>{p}</pubDate>" if p else "")
        + "</item>"
        for t, link, d, p in items
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>x</title>{body}</channel></rss>'
    return ("﻿" if bom else "") + xml


def ingest(feeds, now=NOW):
    out = asyncio.run(INGEST.run(inputs={"feeds": feeds, "now": now}))
    assert "$errors" not in out, out["$errors"]
    return out["ingest"]


# -- reading feeds -----------------------------------------------------------------------------


def test_rss_with_a_bom_cdata_and_html_reads_as_plain_text():
    xml = feed(
        (
            "Lãi suất &amp; tỷ giá",
            "https://vnexpress.net/a.html",
            '<a href="x"><img src="y"></a></br>Tóm tắt <b>ngắn</b>.',
            rfc(NOW),
        ),
        bom=True,
    )
    [it] = rss.parse(xml)
    assert it.title == "Lãi suất & tỷ giá"
    assert it.summary == "Tóm tắt ngắn ."
    assert it.published == NOW


def test_dates_with_two_digit_years_and_atom_feeds_read():
    assert (
        rss.parse_time("Thu, 15 Oct 26 13:46:00 +0700")
        == datetime(2026, 10, 15, 6, 46, tzinfo=timezone.utc).timestamp()
    )
    atom = (
        '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>A</title><id>u1</id>'
        '<link rel="alternate" href="https://www.ecb.europa.eu/p.html"/><updated>2026-10-14T08:00:00Z</updated>'
        "<summary>S</summary></entry></feed>"
    )
    [it] = rss.parse(atom)
    assert (it.link, it.published) == (
        "https://www.ecb.europa.eu/p.html",
        datetime(2026, 10, 14, 8, tzinfo=timezone.utc).timestamp(),
    )


def test_a_page_that_is_not_a_feed_is_an_error():
    with pytest.raises(rss.FeedError):
        rss.parse("<html><body>not a feed</body></html>")


# -- the gates ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source, link, published, outcome, why",
    [
        ("vnexpress_kd", "https://vnexpress.net/a.html", NOW - 60, rules.ACCEPT, ""),
        ("unknown", "https://vnexpress.net/a.html", NOW - 60, rules.REFUSE, "danh sách trắng"),
        ("vnexpress_kd", "https://evil.example/a.html", NOW - 60, rules.REFUSE, "trang của nguồn"),
        ("vnexpress_kd", "https://vnexpress.net/a.html", None, rules.REFUSE, "giờ công bố"),
        ("vnexpress_kd", "https://vnexpress.net/a.html", NOW + 11 * 60, rules.REFUSE, "muộn hơn lúc nạp"),
        ("vnexpress_kd", "https://vnexpress.net/a.html", NOW + 9 * 60, rules.ACCEPT, ""),
        ("vnexpress_kd", "https://vnexpress.net/a.html", NOW - 8 * 86400, rules.SKIP, "cũ hơn"),
        ("fed", "https://www.federalreserve.gov/newsevents/x.htm", NOW - 60, rules.ACCEPT, ""),
    ],
)
def test_the_gates(source, link, published, outcome, why):
    v = rules.gate(config(), source, link, published, NOW)
    assert v.outcome == outcome
    assert why in v.reason


def test_the_same_article_is_kept_once():
    assert rules.url_key("http://www.vnexpress.net/a.html/?utm_source=x") == rules.url_key(
        "https://vnexpress.net/a.html"
    )
    first = ingest({"vnexpress_kd": feed(("Tin A", "https://vnexpress.net/a.html", "", rfc(NOW - 60)))})
    again = ingest(
        {
            "vnexpress_kd": feed(
                ("Tin A", "http://vnexpress.net/a.html/", "", rfc(NOW - 60)),  # same link
                ("tin a!", "https://vnexpress.net/other.html", "", rfc(NOW - 60)),  # same title, same source
            )
        }
    )
    assert (first["added"], again["added"], again["duplicates"]) == (1, 0, 2)


# -- sorting -----------------------------------------------------------------------------------


def test_classification_by_source_then_words():
    cfg = config()
    fed = rules.classify(cfg, "vnexpress_kd", "Fed giữ nguyên lãi suất, phố Wall tăng", "")
    assert fed.kind == "intl" and fed.event_type == "monetary"
    assert {"US10Y", "GLOBAL_EQ", "VN_RATE"} <= set(fed.factors)
    vn = rules.classify(cfg, "vneconomy_ck", "VN-Index giảm, khối ngoại bán ròng", "")
    assert vn.kind == "domestic" and vn.event_type == "equity" and {"VNINDEX", "FOREIGN_FLOW"} <= set(vn.factors)
    assert vn.relevance in ("medium", "high")
    calm = rules.classify(cfg, "vietstock_vm", "Niềm tin kinh doanh vững vàng", "")
    assert calm.event_type is None and calm.factors == [] and calm.relevance == "low"  # "vững vàng" is not gold


def test_an_item_naming_the_restricted_list_is_held_until_the_cio_releases_it():
    out = ingest(
        {
            "vneconomy_tc": feed(
                ("Sao Mai Land chậm trả lãi trái phiếu", "https://vneconomy.vn/sml.htm", "", rfc(NOW - 60))
            )
        }
    )
    assert out["held"] == 1
    [it] = store.inbox()
    assert it["held"] and it["restricted"] == ["Sao Mai Land (mock)"]
    engine = Operon(release_flow, params={"item_id": None, "by": None, "note": None})
    for who in ("admin", "rm01", "nobody"):  # only the CIO may release (BR-04, OWN-FB-18)
        denied = asyncio.run(engine.run(inputs={"item_id": it["id"], "by": who, "note": "Cho qua"}))
        assert "$errors" in denied and store.inbox()[0]["held"]
    bad = asyncio.run(engine.run(inputs={"item_id": it["id"], "by": "cio", "note": " "}))
    assert "$errors" in bad  # a release needs a reason
    ok = asyncio.run(
        engine.run(inputs={"item_id": it["id"], "by": "cio", "note": "Tin công khai, không liên quan giao dịch"})
    )
    assert ok["released"] == it["id"]
    [it] = store.inbox()
    assert not it["held"] and it["cleared"]["by"] == "cio"


# -- the run and the inbox ---------------------------------------------------------------------


def test_one_run_counts_each_source_keeps_refusals_aside_and_survives_a_broken_feed():
    out = ingest(
        {
            "vnexpress_kd": feed(
                ("Giá vàng thế giới giảm mạnh", "https://vnexpress.net/g.html", "", rfc(NOW - 120)),
                ("Tin từ tương lai", "https://vnexpress.net/f.html", "", rfc(NOW + 3600)),
                ("Tin không giờ", "https://vnexpress.net/n.html", "", None),
            ),
            "cafef_ck": "<html>maintenance</html>",
            "rogue": feed(("Tin lạ", "https://rogue.example/x", "", rfc(NOW - 60))),
        }
    )
    s = out["sources"]
    assert (s["vnexpress_kd"]["accepted"], s["vnexpress_kd"]["refused"]) == (1, 2)
    assert s["cafef_ck"]["error"].startswith("FeedError")
    assert s["rogue"]["refused"] == 1
    assert [i["title"] for i in store.inbox()] == ["Giá vàng thế giới giảm mạnh"]
    reasons = sorted(i["refused_reason"] for i in store.inbox(status="refused"))
    assert reasons == [
        "Giờ công bố muộn hơn lúc nạp quá 10 phút",
        "Nguồn không thuộc danh sách trắng",
        "Tin không có giờ công bố",
    ]
    assert store.last_run()["added"] == 1


def test_the_inbox_filters_and_dismiss():
    ingest(
        {
            "vnexpress_kd": feed(("VN-Index tăng mạnh", "https://vnexpress.net/1.html", "", rfc(NOW - 300))),
            "fed": feed(("Fed statement", "https://www.federalreserve.gov/2.htm", "", rfc(NOW - 200))),
        }
    )
    assert [i["source"] for i in store.inbox()] == ["fed", "vnexpress_kd"]  # newest first
    assert [i["source"] for i in store.inbox(kind="intl")] == ["fed"]
    assert [i["source"] for i in store.inbox(query="vn-index")] == ["vnexpress_kd"]
    fed_id = store.inbox(source="fed")[0]["id"]
    out = asyncio.run(
        Operon(dismiss_flow, params={"ids": None, "by": None, "note": None}).run(inputs={"ids": [fed_id]})
    )
    assert out["changed"] == 1
    assert [i["source"] for i in store.inbox()] == ["vnexpress_kd"]
    assert store.inbox(status="dismissed")[0]["history"][0]["by"] == "cio"
    vne_id = store.inbox(source="vnexpress_kd")[0]["id"]
    for who in ("admin", "rm01"):  # only the CIO drops items (FR-103)
        denied = asyncio.run(
            Operon(dismiss_flow, params={"ids": None, "by": None, "note": None}).run(
                inputs={"ids": [vne_id], "by": who}
            )
        )
        assert "$errors" in denied
    assert [i["source"] for i in store.inbox()] == ["vnexpress_kd"]
    store.reset()
    assert len(store.inbox()) == 2  # the demo starts over: items back to new


def test_the_inbox_endpoint_returns_items_and_feed_health():
    from app.web import app

    now = time.time()
    ingest(
        {"vnexpress_kd": feed(("Tỷ giá USD/VND tăng", "https://vnexpress.net/fx.html", "", rfc(now - 600)))}, now=now
    )
    body = TestClient(app).get("/api/news/inbox").json()
    assert [i["title"] for i in body["items"]] == ["Tỷ giá USD/VND tăng"]
    vne = next(s for s in body["sources"] if s["id"] == "vnexpress_kd")
    assert vne["last"]["accepted"] == 1 and sum(vne["hourly"]) == 1 and len(vne["hourly"]) == 24
    assert TestClient(app).get("/api/news/inbox?since=abc").status_code == 400


def test_the_assistant_counts_the_inbox_in_the_database_not_a_capped_list():
    """CIO chat 2026-10-24: the inbox held 1,415 new items and the assistant said 200, the length of ``inbox()``'s
    default page. 250 new and 3 grouped, 4 of them fetched today: every figure counted, today's by source."""
    from assistant.base import Ctx
    from assistant.tools import inbox

    now, old = time.time(), time.time() - 3 * 86400
    rows = [
        {"source": "vnexpress_kd" if i % 2 else "cafef_ck", "url_key": f"u{i}", "title_key": f"t{i}", "published": old,
         "ingested": now if i < 4 else old, "kind": "domestic", "status": "grouped" if i >= 250 else "new"}
        for i in range(253)
    ]  # fmt: skip
    assert store.add(rows)[1] == 0 and len(store.inbox()) == 200  # the page the old count read
    out = asyncio.run(inbox(Ctx(role="cio", client_id=None, scope="own", question=""), {}))
    assert out["data"] == {
        "new": 250,
        "grouped": 3,
        "fetched_today": 4,
        "by_source": {"cafef_ck": 2, "vnexpress_kd": 2},
    }
    assert "250 tin mới" in out["text"] and "3 tin đã gom" in out["text"] and "lấy về 4 tin" in out["text"]
