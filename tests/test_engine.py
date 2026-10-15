"""The scenario engine (src/engine): the factor model's checks, propagation, the bands, the
loadings that matter most, and that a family's numbers add up and repeat to the dong."""

import copy
import json
import math

import pytest

from engine import (
    Branch,
    FactorModel,
    FactorModelError,
    ScenarioError,
    Shock,
    default_model,
    evaluate,
    linalg,
    propagate,
)
from wealth.paths import DATA
from wealth.valuation import holding

RAW = json.loads((DATA / "factor_model.json").read_text(encoding="utf-8"))
HORIZONS = ("1w", "3m", "12m")


def model_with(**changes):
    raw = copy.deepcopy(RAW)
    raw.update(changes)
    return FactorModel.from_dict(raw)


def asset(cls, value, **detail):
    return holding(
        "C99", "declared", f"{cls}:{len(detail)}:{value}", trust="declared", cls=cls, name=cls, value=value, **detail
    )


def loan(value, **detail):
    return holding(
        "C99",
        "techcombank",
        f"loan:{value}",
        trust="verified",
        cls="loan",
        kind="liability",
        name="loan",
        value=value,
        **detail,
    )


def one(factor, direction=1, size="M", priced_in="none", regime="normal"):
    return [
        {
            "id": "b",
            "probability": 1.0,
            "regime": regime,
            "shocks": [{"factor": factor, "direction": direction, "size": size, "priced_in": priced_in}],
        }
    ]


# -- the model ---------------------------------------------------------------------------------


def test_the_model_has_the_brds_fifteen_factors_and_both_regimes_are_valid_covariances():
    m = default_model()
    assert len(m.ids) == 15
    assert m.factor("GOLD").sizes == {"S": 2, "M": 5, "L": 10}
    assert m.factor("VN_HOUSE").realisation == {"1w": 0.0, "3m": 0.3, "12m": 1.0}
    for regime in ("normal", "stressed"):
        cov = m.cov[regime]
        assert linalg.is_symmetric(cov)
        linalg.cholesky(cov)  # positive definite, or it raises
        w, _ = linalg.eigh(m.corr[regime])
        assert min(w) > 0
    # stressed: every volatility at least 1.2 × normal, and the overridden pair as the file says
    assert all(s >= 1.2 * n - 1e-12 for s, n in zip(m.vol("stressed"), m.vol("normal")))
    # the overridden pairs keep their sign and are stronger than in the normal regime; the repair
    # that made the matrix positive definite is measured and kept with the model
    for a, b, _ in RAW["stressed"]["overrides"]:
        i, j = m.index(a), m.index(b)
        assert abs(m.corr["stressed"][i][j]) > abs(m.corr["normal"][i][j])
        assert m.corr["stressed"][i][j] * m.corr["normal"][i][j] > 0
    assert m.stressed_repair["max_change"] < 0.15
    assert m.status == "assumed"


@pytest.mark.parametrize(
    "correlations, why",
    [
        ([["GOLD", "DXY", 1.2]], "outside"),
        ([["GOLD", "GOLD", 0.5]], "itself"),
        ([["GOLD", "NOPE", 0.1]], "unknown factor"),
        ([["GOLD", "DXY", 0.9], ["DXY", "BTC", 0.9], ["GOLD", "BTC", -0.9]], "positive definite"),
    ],
)
def test_a_wrong_factor_model_is_refused(correlations, why):
    with pytest.raises(FactorModelError, match=why):
        model_with(correlations=correlations)


def test_a_realisation_outside_zero_to_one_is_refused():
    raw = copy.deepcopy(RAW)
    raw["factors"][0]["realisation"]["1w"] = 1.5
    with pytest.raises(FactorModelError, match="realisation"):
        FactorModel.from_dict(raw)


def test_the_model_hash_changes_with_any_parameter():
    raw = copy.deepcopy(RAW)
    raw["factors"][0]["vol_month"] += 1
    assert FactorModel.from_dict(raw).hash != default_model().hash


# -- propagation -------------------------------------------------------------------------------


def test_the_core_moves_as_given_and_the_rest_by_conditional_expectation():
    m = default_model()
    p = propagate(Branch("b", "b", 1.0, (Shock("GOLD", -1, "M"),)), m)
    g = m.index("GOLD")
    assert p.moves[g] == -5.0
    cov = m.cov["normal"]
    for i in range(15):  # one core factor: Δn_i = Σ_ig / Σ_gg × Δc
        assert p.moves[i] == pytest.approx(cov[i][g] / cov[g][g] * -5.0, abs=1e-12)
    assert p.moves[m.index("DXY")] > 0  # gold down, dollar up (negative correlation)


def test_two_core_shocks_follow_the_solved_system():
    m = default_model()
    b = Branch("b", "b", 1.0, (Shock("VNINDEX", -1, "L"), Shock("RE_SPREAD", 1, "M")), "stressed")
    p = propagate(b, m)
    cov = m.cov["stressed"]
    core = [m.index("VNINDEX"), m.index("RE_SPREAD")]
    dc = [-15.0, 150.0]
    x = linalg.solve_spd(linalg.sub(cov, core, core), [[v] for v in dc])
    for i in range(15):
        if i not in core:
            assert p.moves[i] == pytest.approx(sum(cov[i][c] * x[k][0] for k, c in enumerate(core)), rel=1e-9)
    # the conditional covariance is a covariance: symmetric, non-negative diagonal
    assert linalg.is_symmetric(p.residual, tol=1e-9)
    assert all(p.residual[i][i] >= -1e-9 for i in range(15))


def test_priced_in_multipliers_scale_the_move_and_its_uncertainty():
    m = default_model()
    full = propagate(Branch("b", "b", 1.0, (Shock("VNINDEX", -1, "M", "none"),)), m)
    half = propagate(Branch("b", "b", 1.0, (Shock("VNINDEX", -1, "M", "partial"),)), m)
    gone = propagate(Branch("b", "b", 1.0, (Shock("VNINDEX", -1, "M", "full"),)), m)
    for a, b, c in zip(full.moves, half.moves, gone.moves):
        assert b == pytest.approx(a * 0.5)
        assert c == 0.0
    assert gone.core_cov == [[0.0]]
    stock = [asset("stock", 1_000_000_000, beta=1.0, ticker="AAA")]
    assert evaluate(stock, one("VNINDEX", -1, "M", "full"))["horizons"]["3m"]["expected"] == 0


# -- the bands ---------------------------------------------------------------------------------


def family():
    return [
        asset("stock", 2_000_000_000, beta=1.1, ticker="AAA"),
        asset("gold", 2_000_000_000),
        asset("bond", 1_000_000_000, duration=3.0, coupon=0.08, bond_kind="corporate", sector="Bất động sản"),
        asset("real_estate", 10_000_000_000),
        loan(3_000_000_000, rate_type="floating"),
    ]


BRANCHES = [
    {"id": "base", "name": "Cơ sở", "probability": 0.6, "shocks": [{"factor": "GOLD", "direction": -1, "size": "M"}]},
    {
        "id": "bad",
        "name": "Xấu",
        "probability": 0.4,
        "regime": "stressed",
        "shocks": [
            {"factor": "VNINDEX", "direction": -1, "size": "L"},
            {"factor": "RE_SPREAD", "direction": 1, "size": "M"},
        ],
    },
]


def test_the_same_inputs_give_the_same_numbers_to_the_dong():
    a = evaluate(family(), BRANCHES)
    b = evaluate(family(), copy.deepcopy(BRANCHES))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_bands_are_ordered_and_widen_with_the_horizon():
    out = evaluate(family(), BRANCHES)["horizons"]
    widths = []
    for h in HORIZONS:
        r = out[h]
        assert r["p5"] <= r["p10"] <= r["p50"] <= r["p90"]
        assert r["p10"] < r["expected"] < r["p90"]
        widths.append(r["p90"] - r["p10"])
    assert widths[0] < widths[1] < widths[2]


def test_the_contributions_add_up_to_the_expected_change():
    out = evaluate(family(), BRANCHES)["horizons"]
    for h in HORIZONS:
        r = out[h]
        assert sum(r["by_holding"].values()) == r["expected"]
        assert sum(r["by_class"].values()) == r["expected"]
        assert sum(r["by_factor"].values()) == r["expected"]


def test_the_expected_change_is_the_probability_weighted_branch_mean():
    out = evaluate(family(), BRANCHES)["horizons"]["3m"]
    means = {b["id"]: b["expected"] for b in out["branches"]}
    assert out["expected"] == pytest.approx(0.6 * means["base"] + 0.4 * means["bad"], abs=1)


def test_a_branch_with_no_shock_is_centred_on_zero():
    out = evaluate(family(), [{"id": "calm", "probability": 1.0, "shocks": []}])["horizons"]["3m"]
    assert out["expected"] == 0
    assert out["p10"] == pytest.approx(-out["p90"], abs=2)


def test_the_band_has_the_three_parts():
    out = evaluate(family(), BRANCHES)["horizons"]["3m"]
    parts = out["branches"][0]["sd_parts"]
    assert parts["residual"] > 0 and parts["core"] > 0 and parts["idiosyncratic"] > 0
    # a stock VN-Index explains entirely has no own risk
    whole = evaluate([asset("stock", 1e9, beta=1.0, ticker="AAA", r2=1.0)], one("GOLD"))["horizons"]["3m"]
    assert whole["branches"][0]["sd_parts"]["idiosyncratic"] == 0


# -- loadings ----------------------------------------------------------------------------------


def test_the_brd_gold_example_has_its_structure():
    """BRD 9.4: world gold −5 % in the base case; the engine infers USD/VND and the SJC gap;
    SJC ≈ gold + USD/VND + 0.9 × gap; 2 tỷ of SJC gold moves by that share."""
    m = default_model()
    p = propagate(Branch("base", "Cơ sở", 1.0, (Shock("GOLD", -1, "M"),)), m)
    fx, gap = p.moves[m.index("USDVND")], p.moves[m.index("SJC_GAP")]
    real = {f: m.factor(f).realisation["3m"] for f in ("GOLD", "USDVND", "SJC_GAP")}
    sjc = -5.0 * real["GOLD"] + fx * real["USDVND"] + 0.9 * gap * real["SJC_GAP"]
    out = evaluate([asset("gold", 2_000_000_000)], one("GOLD", -1, "M"), m)["horizons"]["3m"]
    assert out["expected"] == round(2_000_000_000 * sjc / 100)
    assert out["by_factor"]["GOLD"] == -100_000_000


def test_loans_move_net_worth_the_right_way():
    usd = [loan(1_000_000_000, currency="USD")]
    up = evaluate(usd, one("USDVND", 1, "M"))["horizons"]["3m"]
    assert up["expected"] < 0  # the dollar up, the debt up
    floating = [loan(1_000_000_000, rate_type="floating")]
    out = evaluate(floating, one("VN_RATE", 1, "M"))["horizons"]
    real = default_model().factor("VN_RATE").realisation
    for h, months in (("3m", 3), ("12m", 12)):  # extra interest over the horizon
        assert out[h]["expected"] == round(-1_000_000_000 * 50 / 10_000 * real[h] * months / 12)
    fixed = [loan(1_000_000_000, rate_type="fixed")]
    assert evaluate(fixed, one("VN_RATE", 1, "M"))["horizons"]["3m"]["expected"] == 0


def test_bonds_lose_when_yields_and_their_sector_spread_rise():
    re_bond = asset("bond", 1e9, duration=3.0, coupon=0.1, bond_kind="corporate", sector="Bất động sản")
    out = evaluate([re_bond], one("RE_SPREAD", 1, "M"))
    loads = out["holdings"][0]["loads"]
    assert loads["RE_SPREAD"] == pytest.approx(-3.0 / 1.1 / 10_000)
    assert out["horizons"]["3m"]["by_factor"]["RE_SPREAD"] < 0


def test_fpt_also_moves_with_the_dollar():
    fpt = evaluate([asset("stock", 1e9, beta=1.05, ticker="FPT")], one("USDVND"))["holdings"][0]["loads"]
    assert fpt["USDVND"] == pytest.approx(0.005)
    assert fpt["VNINDEX"] == pytest.approx(0.0105)


def test_proxies_are_labelled_and_cash_has_no_load():
    out = evaluate([asset("real_estate", 1e9), asset("business", 1e9), asset("cash", 1e9)], one("VNINDEX"))
    by = {h["class"]: h for h in out["holdings"]}
    assert by["real_estate"]["modelled"] and "theo mô hình" in by["real_estate"]["method"]
    assert by["business"]["loads"] == {"VNINDEX": pytest.approx(0.005)}
    assert by["cash"]["loads"] == {} and not by["cash"]["modelled"]


# -- refused inputs ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "branches, why",
    [
        ([{"id": "a", "probability": 0.5, "shocks": []}], "cộng bằng 1"),
        ([{"id": "a", "probability": 1.0, "shocks": [{"factor": "NOPE", "direction": 1, "size": "M"}]}], "danh mục"),
        ([{"id": "a", "probability": 1.0, "shocks": [{"factor": "GOLD", "direction": 1, "size": "XL"}]}], "S, M"),
        ([{"id": "a", "probability": 1.0, "shocks": [{"factor": "GOLD", "direction": 2, "size": "M"}]}], "chiều"),
        (
            [
                {
                    "id": "a",
                    "probability": 1.0,
                    "shocks": [
                        {"factor": "GOLD", "direction": 1, "size": "M"},
                        {"factor": "GOLD", "direction": -1, "size": "S"},
                    ],
                }
            ],
            "hai cú sốc",
        ),
        ([{"id": str(i), "probability": 0.2, "shocks": []} for i in range(5)], "1–4"),
        ([{"id": "a", "probability": 1.0, "regime": "panic", "shocks": []}], "chế độ"),
    ],
)
def test_wrong_branches_are_refused(branches, why):
    with pytest.raises(ScenarioError, match=why):
        evaluate(family(), branches)


# -- the sample clients ------------------------------------------------------------------------


def test_every_sample_client_gets_consistent_numbers():
    import asyncio

    from operonx import Operon

    from consolidate.graph import consolidate_flow
    from wealth import fixtures

    engine = Operon(consolidate_flow, params={"client_id": None, "scope": None})
    for cid in fixtures.client_ids():
        holdings = asyncio.run(engine.run(inputs={"client_id": cid, "scope": "family"}))["holdings"]
        out = evaluate(holdings, BRANCHES)
        for h in HORIZONS:
            r = out["horizons"][h]
            assert r["p5"] <= r["p10"] <= r["p50"] <= r["p90"]
            assert sum(r["by_holding"].values()) == r["expected"]
            assert all(math.isfinite(v) for v in (r["p5"], r["p90"]))
        assert out == evaluate(holdings, BRANCHES)
