"""Nguồn tin's test read (docs/NEWS_OPS_PLAN.md N1): https only, never a private, loopback or link-local address
(checked after the name resolves, and again on a redirect), the feed's own size cap; a good feed answers its count
and newest title, and nothing is kept."""

import io

from news import ops, rss, store


def test_the_test_read_refuses_http_and_every_inside_address():
    assert ops.probe("http://vnexpress.net/rss/kinh-doanh.rss")["error"].endswith("chỉ thử url https")
    for url in (
        "https://127.0.0.1/x",
        "https://localhost/x",
        "https://10.0.0.5/x",
        "https://169.254.169.254/",
        "https://[::1]/",
    ):
        r = ops.probe(url)
        assert not r["ok"] and "nội bộ" in r["error"], (url, r)


def test_a_redirect_inside_is_refused():
    try:
        ops._Checked().redirect_request(None, None, 302, "Found", {}, "https://192.168.1.12/feed")
    except ValueError as exc:
        assert "nội bộ" in str(exc)
    else:
        raise AssertionError("a redirect to a private address was followed")


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _serve(monkeypatch, body):
    monkeypatch.setattr(ops, "_public", lambda url: "example.org")
    opener = type("O", (), {"open": lambda self, req, timeout: _Resp(body)})()
    monkeypatch.setattr(ops.urllib.request, "build_opener", lambda *h: opener)


def test_a_good_feed_answers_its_count_and_newest_title_and_keeps_nothing(monkeypatch):
    _serve(
        monkeypatch,
        b"<rss><channel><item><title>Cu</title><link>https://e.org/1</link><pubDate>Mon, 12 Oct 2026 01:00:00 GMT"
        b"</pubDate></item><item><title>Moi</title><link>https://e.org/2</link><pubDate>Wed, 14 Oct 2026 01:00:00 GMT"
        b"</pubDate></item></channel></rss>",
    )
    before = store.last_run()
    r = ops.probe("https://example.org/feed.rss")
    assert r["ok"] and r["items"] == 2 and r["newest"]["title"] == "Moi"
    assert store.last_run() == before  # no run, no item recorded


def test_a_feed_over_the_size_cap_or_not_a_feed_says_why(monkeypatch):
    _serve(monkeypatch, b"x" * (rss.MAX_BYTES + 1))
    assert "larger than" in ops.probe("https://example.org/big")["error"]
    _serve(monkeypatch, b"<html>no</html>")
    assert "unknown feed root" in ops.probe("https://example.org/page")["error"]
