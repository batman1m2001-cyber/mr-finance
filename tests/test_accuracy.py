"""Accuracy over time (FEAT-18; BR-15, KPI-03/04, MEAS-01/02) and the measurement reports (MEAS-03, MEAS-05,
KPI-01, WF-09, NFR-02). History here is synthetic with a known volatility and correlation."""

import math
import random
from datetime import date, timedelta

import pytest
from starlette.testclient import TestClient
from test_apply import MARKET, approved

from control import config, db
from market import factors as mf
from measure import backtest, forecasts, realised, reports
from views import store as vstore


def daily(levels_from: str, days: int, seed: int = 1, vol: float = 6.0, rho: float = 0.6):
    """VNINDEX and GOLD as daily random walks (log moves) whose monthly sd is ``vol`` and 4, correlated ``rho``."""
    rnd = random.Random(seed)
    d0 = date.fromisoformat(levels_from)
    per_day = 1 / math.sqrt(365.25 / 12)
    vn, gold, a, b = [], [], 1000.0, 2000.0
    for i in range(days):
        z1, z2 = rnd.gauss(0, 1), rnd.gauss(0, 1)
        a *= math.exp(vol / 100 * per_day * z1)
        b *= math.exp(4 / 100 * per_day * (rho * z1 + math.sqrt(1 - rho**2) * z2))
        day = (d0 + timedelta(days=i)).isoformat()
        vn.append((day, a))
        gold.append((day, b))
    return {"VNINDEX": vn, "GOLD": gold}


def synthetic(days=365 * 7, seed=1):
    pts = daily("2019-01-01", days, seed)
    data = {k: realised.Series(k, "pct", v) for k, v in pts.items()}
    hist = {
        k: {"moves": {m["month"]: m["move"] for m in mf.moves("pct", v)}, "provenance": "thử"} for k, v in pts.items()
    }
    return data, hist


# -- the realised move ---------------------------------------------------------------------------


def test_a_move_is_measured_in_the_factors_unit_and_a_gap_is_no_data():
    pts = [("2026-01-02", 100.0), ("2026-01-05", 110.0), ("2026-01-30", 99.0)]
    assert realised.Series("X", "pct", pts).move("2026-01-02", "2026-01-06") == pytest.approx(10.0)  # holiday
    assert realised.Series("X", "bp", [("2026-01-02", 3.1), ("2026-01-09", 3.35)]).move(
        "2026-01-02", "2026-01-09"
    ) == pytest.approx(25.0)
    assert realised.Series("X", "pp", [("2026-01-02", 12.0), ("2026-01-09", 9.5)]).move(
        "2026-01-02", "2026-01-09"
    ) == pytest.approx(-2.5)
    assert realised.Series("X", "pct", pts).move("2026-01-05", "2026-01-20") is None  # 15 days without a point
    assert realised.Series("X", "pct", pts).move("2026-01-05", "2026-02-10") is None  # after the data
    flows = [(f"2026-{m:02d}-10", float(x)) for m, x in zip(range(1, 7), (10, -10, 20, -20, 0, 0))]
    s = realised.Series("FOREIGN_FLOW", "sd", flows)
    assert s.mean == 0 and s.move("2026-02-28", "2026-03-31") == pytest.approx(20 / s.sd)


# -- the model walked forward over history -------------------------------------------------------


def test_walking_forward_on_history_that_follows_the_model_covers_about_80_percent():
    data, hist = synthetic()
    out = backtest.run(hist=hist, data=data, base=config.data("factor_model"))
    h3 = {f["id"]: f for f in out["horizons"]["3m"]["factors"]}
    assert set(h3) == {"VNINDEX", "GOLD"} and out["from"] == "2021-01-31"  # the first moves 2019-02: 24 months
    for f in h3.values():
        assert f["n"] >= backtest.MIN_OBS and 0.65 <= f["coverage"] <= 0.95
    # the engine's band at one week is shrunk by the realisation (VN-Index 0.7): it covers less than at 3 months
    w = {f["id"]: f for f in out["horizons"]["1w"]["factors"]}
    assert w["VNINDEX"]["coverage"] < h3["VNINDEX"]["coverage"]
    # direction: VN-Index inferred from gold (ρ 0.6) has the right sign more often than a coin
    assert out["kpi03"]["3m"]["hit"] > 0.6 and out["kpi03"]["3m"]["n"] == h3["VNINDEX"]["direction_n"]


def test_fewer_than_24_observations_is_not_a_conclusion():
    assert backtest.verdict(23, 0.8) == "chưa đủ 24 quan sát"
    assert backtest.verdict(24, 0.8) == "đạt" and backtest.verdict(30, 0.5) == "dải hẹp"
    assert backtest.verdict(30, 0.95) == "dải rộng" and backtest._met(10, 0.9) is None


# -- the views' own forecasts --------------------------------------------------------------------


def test_an_approved_view_keeps_its_forecasts_and_they_are_scored_when_due():
    view, _ = approved(*MARKET)
    rows = forecasts.for_view(view["id"])
    assert len(rows) == 15 * 3  # every factor, every horizon
    today = date.today().isoformat()
    vn3 = next(r for r in rows if r["factor"] == "VNINDEX" and r["horizon"] == "3m")
    assert vn3["origin"] == today and vn3["due"] == (date.today() + timedelta(days=91)).isoformat()
    assert vn3["p10"] < vn3["p50"] < vn3["p90"] and vn3["expected"] < 0  # the mock view: VN-Index down
    assert forecasts.record(vstore.get(view["id"])) == 0  # once
    # the market fell 10 % over the week, and gold has no data at all
    data = {"VNINDEX": realised.Series("VNINDEX", "pct", [(today, 1000.0), (realised.add_days(today, 7), 900.0)])}
    later = realised.add_days(today, 8)
    got = forecasts.score(later, data)
    assert got["scored"] == 1 and got["no_data"] == 14  # the 1-week VN-Index; the rest have no series
    vn1 = next(r for r in forecasts.for_view(view["id"]) if r["factor"] == "VNINDEX" and r["horizon"] == "1w")
    assert vn1["realised"] == pytest.approx(-10.0) and vn1["direction_hit"] is True
    assert vn1["inside"] == (vn1["p10"] <= -10.0 <= vn1["p90"])
    s = forecasts.summary()
    vn = next(f for f in s["horizons"]["1w"]["factors"] if f["id"] == "VNINDEX")
    assert vn["n"] == 1 and vn["verdict"] == "chưa đủ 24 quan sát" and s["kpi03"]["1w"]["met"] is None
    assert s["horizons"]["3m"]["next_due"] == vn3["due"]


def test_views_approved_before_tracking_are_recorded_by_the_daily_job():
    view, _ = approved(*MARKET)
    with db.tx() as con:
        con.execute("delete from forecasts")
    assert forecasts.record_missing() == [view["id"]]
    assert forecasts.for_view(view["id"])[0]["late"] is True and forecasts.record_missing() == []


# -- the measurement reports ---------------------------------------------------------------------


def test_the_reports_read_approval_time_edits_and_news_to_rm_time():
    view, run = approved(*MARKET)
    r = reports.rubber_stamp()
    row = next(x for x in r["views"] if x["id"] == view["id"])
    assert row["edited"] is False and row["minutes"] is not None and row["minutes"] < reports.FAST_MIN
    assert r["by_month"][0]["no_edit_share"] == 1.0 and r["by_month"][0]["fast"] == 1
    sp = reports.speed()
    assert [x["run"] for x in sp["runs"]] == [run["id"]] and sp["urgent"] == "chưa có định nghĩa"
    t = reports.timing()
    assert t["agent"]["runs"] and t["agent"]["runs"][0]["minutes"] < reports.AGENT_TARGET_MIN


def test_an_event_without_an_approved_view_is_a_miss_after_a_day():
    from test_views import event

    ev = event("Giá vàng thế giới giảm mạnh, vàng miếng SJC giảm theo")
    assert reports.misses()["events"] == []  # under a day old
    got = reports.misses(now=ev["created"] + 2 * 86400)
    assert [(e["id"], e["cause"]) for e in got["events"]] == [(ev["id"], "Chưa có nhận định")]


def test_the_pages_api_is_for_staff(monkeypatch):
    from operonx.app import Application

    monkeypatch.setattr(backtest, "cached", lambda: {"horizons": {}, "kpi03": {}})
    with TestClient(Application.find(".").asgi()) as c:
        a = c.get("/api/accuracy").json()
        m = c.get("/api/measure").json()
    assert a["min_obs"] == 24 and a["accept"] == [0.7, 0.9] and "horizons" in a["views"]
    assert set(m) == {"misses", "rubber_stamp", "speed", "timing", "availability"}


def test_a_factors_own_band_is_its_shock_times_the_realisation_with_the_model_spread():
    from engine import default_model, factor_bands

    m = default_model()
    shock = {"factor": "VNINDEX", "direction": -1, "size": "M"}
    b = factor_bands([{"id": "a", "name": "a", "probability": 1.0, "shocks": [shock]}], m)
    vn = m.factor("VNINDEX")
    for h in ("1w", "3m", "12m"):
        assert b[h]["VNINDEX"]["expected"] == pytest.approx(-vn.sizes["M"] * vn.realisation[h])
        assert b[h]["VNINDEX"]["p10"] < b[h]["VNINDEX"]["p50"] < b[h]["VNINDEX"]["p90"]
    assert b["12m"]["GOLD"]["p90"] - b["12m"]["GOLD"]["p10"] > b["3m"]["GOLD"]["p90"] - b["3m"]["GOLD"]["p10"]
