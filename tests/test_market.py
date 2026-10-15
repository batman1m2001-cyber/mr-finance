"""Market data (F1): each source's adapter on a response recorded from it (2026-10-16), the fallback order, the
jobs keeping points in SQLite and recording every run, the factors made from the series, the configuration that
names the sources, and the read API. The suite never touches the network."""

import json
import urllib.error
from datetime import date

import pytest

from market import factors, fetch, sources, store
from market.sources import Request
from wealth.paths import ROOT

REC = ROOT / "tests" / "data" / "market"


def rec(name: str) -> bytes:
    return (REC / name).read_bytes()


class Net:
    """The network, answered from the recordings by host; counts the requests."""

    def __init__(self, fail=()):
        self.fail, self.asked = set(fail), []

    def __call__(self, req: Request) -> bytes:
        self.asked.append(req)
        u = req.url
        for host in self.fail:
            if host in u:
                raise urllib.error.URLError(f"{host} down")
        if "vndirect" in u:
            return rec("vnd_vnindex.json" if "VNINDEX" in u else "vnd_fpt.json")
        if "vietcap" in u:
            return rec("vietcap_fpt.json")
        if "resolver/api/resolve" in u:
            return rec("msn_config.json")
        if "Charts/TimeRange" in u:
            return rec("msn.json")
        if "binance" in u:
            return rec("binance_btc.json")
        if "vietcombank" in u:
            return rec("vcb.json")
        if "pnj.io" in u:
            return rec("pnj.json")
        if "hnx.vn" in u:
            return rec("hnx.html")
        if "worldgovernmentbonds" in u:
            return rec("wgb.json")
        if "cafef" in u:
            return rec("cafef.json")
        raise AssertionError(f"unexpected request {u}")


SEP = (date(2026, 9, 1), date(2026, 9, 10))


@pytest.fixture(autouse=True)
def fresh_msn_key():
    sources._msn_key.clear()


# -- adapters ------------------------------------------------------------------------------------


def test_vndirect_gives_daily_closes_and_stocks_in_dong():
    fpt = sources.vndirect("FPT", *SEP, Net(), scale=1000)
    assert fpt.points[0] == ("2026-09-03", pytest.approx(65637.0)) and len(fpt.points) == 6
    idx = sources.vndirect("VNINDEX", *SEP, Net())
    assert idx.points[-1] == ("2026-09-10", pytest.approx(1829.23))


def test_vietcap_gives_the_same_closes_in_dong():
    got = sources.vietcap("FPT", *SEP, Net())
    assert got.points[0] == ("2026-09-03", pytest.approx(65637.02))  # VNDirect: 65.637 thousand


def test_msn_gives_every_instrument_of_one_request_with_its_scale():
    net = Net()
    got, _ = sources.msn_many(["ck48ur", "a33knm"], date(2026, 10, 5), date(2026, 10, 10), net)
    assert got["ck48ur"][0] == ("2026-10-05", pytest.approx(4139.49))
    us10 = sources.msn("a33knm", date(2026, 10, 5), date(2026, 10, 10), net, scale=0.1)
    assert us10.points[0][1] == pytest.approx(5.311)  # MSN's TNX is the yield ×10
    assert "RECORDED-KEY" not in us10.url  # the key is not kept with the points


def test_binance_vcb_pnj_hnx_wgb_cafef():
    btc = sources.binance("BTCUSDT", date(2026, 8, 31), date(2026, 9, 10), Net())
    assert btc.points[0] == ("2026-09-01", pytest.approx(77439.0))
    usd = sources.vcb("USD", date(2026, 9, 8), date(2026, 9, 8), Net())
    assert usd.points == [("2026-09-08", 25780.0)]
    sjc = sources.pnj("SJC", date(2026, 9, 8), date(2026, 9, 8), Net())
    assert sjc.points[0][1] >= 100_000_000  # VND per lượng: "146.500" is 146,500,000
    curve = sources.hnx_curve(rec("hnx.html").decode())
    assert curve["3M"] == pytest.approx(3.89209748625565) and curve["10Y"] == pytest.approx(4.49731894912047)
    wgb = sources.wgb("58", date(2026, 10, 8), date(2026, 10, 15), Net())
    assert wgb.points[0] == ("2026-10-08", 4.559)
    flow = sources.cafef("VNINDEX", *SEP, Net())
    assert ("2026-09-10", 367012110000.0) in flow.points


def test_a_day_that_fails_is_skipped_and_only_all_failing_is_an_error():
    def get(req):
        if "20260909" in req.url:
            raise urllib.error.HTTPError(req.url, 422, "not yet", None, None)  # PNJ, a day not over
        return rec("pnj.json")

    got = sources.pnj("SJC", date(2026, 9, 8), date(2026, 9, 9), get)
    assert [d for d, _ in got.points] == ["2026-09-08"]
    with pytest.raises(urllib.error.HTTPError):
        sources.pnj("SJC", date(2026, 9, 9), date(2026, 9, 9), get)


# -- jobs -----------------------------------------------------------------------------------------


def test_a_job_keeps_its_series_and_records_each_fetch():
    out = fetch.run_job("market_equity", Net(), today=date(2026, 9, 10), since=date(2026, 9, 1))
    assert out["errors"] == 0 and {s["series"] for s in out["series"]} >= {"VNINDEX", "FPT", "VCB"}
    assert store.points("FPT")[0] == ("2026-09-03", pytest.approx(65637.0))
    runs = store.runs("market_equity")
    assert len(runs) == len(out["series"]) and all(r["source"] == "vndirect" for r in runs)
    again = fetch.run_job("market_equity", Net(), today=date(2026, 9, 10), since=date(2026, 9, 1))
    assert again["points"] == out["points"] and len(store.points("FPT")) == 6  # a day's point is replaced, not added


def test_a_source_that_fails_hands_over_to_its_fallback_and_says_so():
    fetch.run_job(
        "market_equity", Net(fail={"vndirect"}), today=date(2026, 9, 10), since=date(2026, 9, 1), only=["FPT"]
    )
    run = store.runs("market_equity")[0]
    assert run["source"] == "vietcap" and run["error"] is None
    assert run["tried"][0]["source"] == "vndirect" and "down" in run["tried"][0]["error"]
    assert store.coverage()["FPT"]["source"] == "vietcap"


def test_when_every_source_fails_the_run_records_the_error():
    out = fetch.run_job("market_fx", Net(fail={"vietcombank", "msn"}), today=date(2026, 9, 10), since=date(2026, 9, 1))
    assert out["errors"] == 1
    h = store.job_health()["market_fx"]
    assert h["last_ok"] is None and "vcb" in h["last_error"] and "msn" in h["last_error"]


def test_the_world_job_asks_msn_once_for_all_its_series():
    net = Net()
    out = fetch.run_job("market_world", net, today=date(2026, 10, 10), since=date(2026, 10, 5))
    assert out["errors"] == 0 and len(out["series"]) == 11
    assert sum("Charts/TimeRange" in r.url for r in net.asked) == 1


def test_the_hnx_curve_is_asked_once_a_day_for_all_tenors():
    net = Net()
    fetch.run_job("market_yields", net, today=date(2026, 9, 8), since=date(2026, 9, 8))
    assert sum("hnx.vn" in r.url for r in net.asked) == 1
    assert store.points("VN_GOV_10Y") == [("2026-09-08", pytest.approx(4.49731894912047))]


def test_every_job_is_scheduled_in_the_app():
    from app.main import APP

    names = {j.name for j in APP.jobs}
    assert set(fetch.jobs()) | {"market_backfill", "news_ingest"} <= names


# -- factors ---------------------------------------------------------------------------------------


def test_the_dxy_follows_the_ice_formula():
    one = {k: [("2026-10-05", v)] for k, v in
           {"EURUSD": 1.1221, "USDJPY": 157.9, "GBPUSD": 1.3219, "USDCAD": 1.4257, "USDSEK": 10.0316,
            "USDCHF": 0.8305}.items()}  # fmt: skip
    ((d, v),) = factors.dxy(one)
    assert d == "2026-10-05" and 95 < v < 105


def test_the_sjc_gap_is_sjc_against_world_gold_in_dong_per_luong():
    gap = factors.sjc_gap({"SJC": [("2026-10-06", 143_300_000.0)], "XAUUSD": [("2026-10-05", 4139.49)],
                           "USDVND": [("2026-10-06", 25_700.0)]})  # fmt: skip
    world = 4139.49 * 25_700 * 37.5 / 31.1035
    assert gap == [("2026-10-06", pytest.approx((143_300_000 / world - 1) * 100))]


def test_moves_are_in_each_factors_unit():
    pts = [("2026-01-30", 100.0), ("2026-02-27", 110.0), ("2026-03-31", 99.0)]
    assert [round(m["move"], 6) for m in factors.moves("pct", pts)] == [10.0, -10.0]
    ys = [("2026-01-30", 4.0), ("2026-02-27", 4.25)]
    assert factors.moves("bp", ys) == [{"month": "2026-02", "move": pytest.approx(25.0)}]
    flows = [("2026-01-05", 1.0), ("2026-02-05", 2.0), ("2026-03-05", 3.0)]
    assert [round(m["move"], 6) for m in factors.moves("sd", flows)] == [-1.0, 0.0, 1.0]


def test_each_factor_says_where_it_comes_from():
    fetch.run_job("market_equity", Net(), today=date(2026, 9, 10), since=date(2026, 9, 1), only=["VNINDEX"])
    rows = {f["id"]: f for f in factors.factor_series()}
    assert len(rows) == 15
    assert rows["VNINDEX"]["provenance"] == "Dữ liệu thị trường (vndirect)"
    for f in ("RE_SPREAD", "FIN_SPREAD", "VN_HOUSE"):
        assert rows[f]["provenance"] == "Giả định"
    assert rows["GOLD"]["provenance"].startswith("Giả định")  # nothing stored yet
    assert "thay thế" not in rows["VNINDEX"]["provenance"]


# -- configuration and API --------------------------------------------------------------------------


def test_the_sources_are_configuration_owned_by_admin():
    from control import config, roles

    base = config.data("price_sources")
    bad = json.loads(json.dumps(base))
    bad["series"][0]["sources"] = [{"source": "yahoo", "symbol": "^VNINDEX"}]
    with pytest.raises(ValueError, match="yahoo"):
        config.propose("price_sources", bad, by="admin")
    with pytest.raises(roles.Forbidden):
        config.propose("price_sources", base, by="cio")
    new = json.loads(json.dumps(base))
    new["series"][1]["sources"].reverse()  # FPT: Vietcap first
    vid = config.propose("price_sources", new, by="admin")["id"]
    config.decide(vid, "approve", by="admin")
    fetch.run_job("market_equity", Net(), today=date(2026, 9, 10), since=date(2026, 9, 1), only=["FPT"])
    assert store.runs("market_equity")[0]["source"] == "vietcap"


def test_the_ticker_map_turns_a_demo_ticker_into_the_exchange_symbol():
    from control import config

    vid = config.propose("ticker_map", {**config.data("ticker_map"), "FPT": "FPTX"}, by="admin")["id"]
    config.decide(vid, "approve", by="admin")
    net = Net()
    fetch.run_job("market_equity", net, today=date(2026, 9, 10), since=date(2026, 9, 1), only=["FPT"])
    assert "symbol=FPTX" in net.asked[0].url


def test_the_market_page_reads_sqlite_only():
    from operonx.app import Application
    from starlette.testclient import TestClient

    fetch.run_job("market_equity", Net(), today=date(2026, 9, 10), since=date(2026, 9, 1), only=["VNINDEX"])
    with TestClient(Application.find(".").asgi()) as c:
        d = c.get("/api/market").json()
        assert {j["id"] for j in d["jobs"]} == set(fetch.jobs())
        vn = next(s for s in d["series"] if s["id"] == "VNINDEX")
        assert vn["n"] == 6 and vn["source"] == "vndirect" and len(vn["tail"]) <= 6
        assert c.get("/api/market/series", params={"id": "VNINDEX"}).json()["points"][0][0] == "2026-09-03"
        assert c.get("/api/market/series", params={"id": "DXY"}).status_code == 200
        assert c.get("/api/market/series", params={"id": "nope"}).status_code == 404
