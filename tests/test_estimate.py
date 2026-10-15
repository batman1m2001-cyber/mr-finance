"""Estimating the factor model from history and validating it out of sample (F2; BRD §9.2, ENG-11, MEAS-08, AI-05).
The history here is synthetic with known volatilities and correlation, so the estimates can be checked."""

import json
import math
import random

import pytest

from control import config, roles
from engine import FactorModel
from market import estimate


def months(n, first=(2020, 1)):
    y, m = first
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y, m + 1) if m < 12 else (y + 1, 1)
    return out


def synthetic(n=80, rho=0.6, seed=7):
    """VNINDEX (vol 6) and GOLD (vol 4) correlated ``rho``; US10Y (vol 25) with too few months; the rest absent."""
    rnd = random.Random(seed)
    ms = months(n)
    vn, gold = {}, {}
    for m in ms:
        a, b = rnd.gauss(0, 1), rnd.gauss(0, 1)
        vn[m] = 6 * a
        gold[m] = 4 * (rho * a + math.sqrt(1 - rho**2) * b)
    us = {m: rnd.gauss(0, 25) for m in ms[:20]}
    return {
        "VNINDEX": {"moves": vn, "provenance": "Dữ liệu thị trường (vndirect)"},
        "GOLD": {"moves": gold, "provenance": "Dữ liệu thị trường (msn)"},
        "US10Y": {"moves": us, "provenance": "Dữ liệu thị trường (msn)"},
    }


def test_volatility_and_shrunk_correlation_come_from_55_months_and_the_rest_stays_assumed():
    base = config.data("factor_model")
    hist = synthetic()
    end = months(80)[-1]
    out = estimate.estimate(base, end=end, hist=hist)
    model, rep = out["model"], out["report"]
    f = {x["id"]: x for x in model["factors"]}
    win = sorted(hist["VNINDEX"]["moves"])[-55:]
    sd = estimate._sd([hist["VNINDEX"]["moves"][m] for m in win])
    assert f["VNINDEX"]["vol_month"] == pytest.approx(sd, rel=1e-3) and not f["VNINDEX"]["assumed"]
    assert f["VNINDEX"]["estimated"]["months"] == 55 and f["VNINDEX"]["brd_parameter"] == "Ước lượng"
    assert f["US10Y"]["assumed"] and f["US10Y"]["vol_month"] == 25  # 20 months < 24
    assert f["RE_SPREAD"]["assumed"] and f["RE_SPREAD"]["brd_parameter"] == "Giả định"
    pair = next(r for a, b, r in model["correlations"] if {a, b} == {"VNINDEX", "GOLD"})
    sample, _ = estimate._corr(
        {m: hist["VNINDEX"]["moves"][m] for m in win}, {m: hist["GOLD"]["moves"][m] for m in win}
    )
    assert pair == pytest.approx(0.8 * sample, abs=0.001)  # 20 % shrinkage toward zero (BRD §9.2)
    assert rep["estimated"] == 2 and rep["window"] == 55 and model["status"] == "estimated"
    same = {(a, b): r for a, b, r in base["correlations"] if "VNINDEX" not in (a, b) or "GOLD" in (a, b)}
    for a, b, r in model["correlations"]:
        if (a, b) in same and {a, b} != {"VNINDEX", "GOLD"} and not ({a, b} & {"VNINDEX", "GOLD"}):
            assert r == pytest.approx(same[(a, b)], abs=0.001)  # assumed pairs untouched
    FactorModel.from_dict(model)  # a model the engine accepts
    assert {x["id"]: x["sizes"] for x in model["factors"]} == {x["id"]: x["sizes"] for x in base["factors"]}


def test_out_of_sample_coverage_is_near_80_percent_when_the_history_is_what_the_model_says():
    base = config.data("factor_model")
    hist = synthetic(n=120, seed=3)
    v = estimate.validate(base, split=months(120)[59], test_to=months(120)[-1], hist=hist)
    assert {r["id"] for r in v["factors"]} == {"VNINDEX", "GOLD"}
    assert 0.7 <= v["pooled_coverage_1m"] <= 0.9 and v["pass"]
    assert v["factors"][0]["months"] == 60 and v["correlation_pairs"] == 1


def test_a_band_too_narrow_is_said_to_be():
    base = config.data("factor_model")
    hist = synthetic(n=120, seed=5)
    calm = sorted(hist["VNINDEX"]["moves"])
    for m in calm[60:]:
        hist["VNINDEX"]["moves"][m] *= 3  # the market got three times as volatile after the split
    v = estimate.validate(base, split=calm[59], test_to=calm[-1], hist=hist)
    vn = next(r for r in v["factors"] if r["id"] == "VNINDEX")
    assert vn["verdict"] == "dải hẹp" and vn["coverage_1m"] < 0.7


def test_the_estimate_is_proposed_by_one_cio_and_approved_by_another(monkeypatch):
    from operonx.app import Application
    from starlette.testclient import TestClient

    monkeypatch.setattr(estimate, "history", lambda: synthetic())
    end = months(80)[-1]
    with TestClient(Application.find(".").asgi()) as c:
        assert c.post("/api/model/estimate", json={"by": "rm01", "end": end}).status_code != 200
        r = c.post("/api/model/estimate", json={"by": "cio", "end": end})
    assert r.status_code == 200, r.text
    vid = r.json()["version"]["id"]
    assert config.data("factor_model")["status"] == "assumed"  # nothing changes before the second CIO
    with pytest.raises(roles.Forbidden):
        config.decide(vid, "approve", by="cio")  # not by the one who proposed it
    config.decide(vid, "approve", by="cio2")
    assert config.data("factor_model")["version"] == f"FM-EST-{end}"
    from engine import default_model

    assert not next(f for f in default_model().factors if f.id == "VNINDEX").assumed


def test_the_page_api_shows_the_estimate_and_its_check(monkeypatch):
    from operonx.app import Application
    from starlette.testclient import TestClient

    monkeypatch.setattr(estimate, "history", lambda: synthetic(n=120, seed=3))
    with TestClient(Application.find(".").asgi()) as c:
        d = c.get("/api/model/estimate").json()
    assert d["report"]["estimated"] == 2 and d["validation"]["factors"]


# -- BRD-RULE-AI-05: a stressed branch carries VN-Index and real-estate credit --------------------


def test_a_stressed_branch_without_vnindex_and_re_spread_is_refused():
    from views import schema

    view = json.loads(json.dumps(_view()))
    assert schema.check(view, ["NW-1"]) == []
    view["scenarios"]["branches"][1]["core_shocks"] = [{"factor": "VNINDEX", "direction": "down", "size": "L"}]
    errs = schema.check(view, ["NW-1"])
    assert any("RE_SPREAD" in e and "căng thẳng" in e for e in errs)
    assert schema.check(view, ["NW-1"], agent=False) == []  # a CIO edit: the challenger's R2 finding instead


def _view():
    shock = lambda f, d, s: {"factor": f, "direction": d, "size": s}  # noqa: E731
    return {
        "summary": "Lãi suất điều hành giữ nguyên, thị trường đã phản ánh phần lớn thông tin.",
        "impacts": [
            {
                "target_type": "asset_class",
                "target": "stock",
                "level": -1,
                "horizon": "3m",
                "confidence": "medium",
                "rationale": "Thanh khoản thắt lại khi lãi suất cao.",
                "source_ids": ["NW-1"],
            }
        ],
        "scenarios": {
            "priced_in": "partial",
            "branches": [
                {
                    "id": "base",
                    "name": "Cơ sở",
                    "probability": 0.7,
                    "regime": "normal",
                    "core_shocks": [shock("VN_RATE", "up", "S")],
                    "rationale": "Ngân hàng nhà nước giữ lãi suất trong quý tới.",
                    "source_ids": ["NW-1"],
                },
                {
                    "id": "stress",
                    "name": "Căng thẳng",
                    "probability": 0.3,
                    "regime": "stressed",
                    "core_shocks": [shock("VNINDEX", "down", "L"), shock("RE_SPREAD", "up", "M")],
                    "rationale": "Tín dụng bất động sản căng lại như năm 2022.",
                    "source_ids": ["NW-1"],
                },
            ],
        },
    }
