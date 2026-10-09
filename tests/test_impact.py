import asyncio

from operonx import Operon
from operonx.app.jobs import Job

from impact import _rules
from impact.graph import alerts_flow, sweep_flow
from impact.ops import every_client
from wealth import fixtures, store
from wealth.money import TY

ENGINE = Operon(alerts_flow, params={"client_id": None, "scope": None})


def h(cls, value, kind="asset", cost=None, **detail):
    return {
        "key": f"x:{cls}:{value}",
        "owner": "C01",
        "kind": kind,
        "class": cls,
        "name": detail.pop("name", cls),
        "value": value,
        "cost": cost,
        "detail": detail,
    }


def factor(fid):
    return next(f for f in fixtures.factors()["factors"] if f["id"] == fid)


def report(client_id, scope="personal"):
    out = asyncio.run(ENGINE.run(inputs={"client_id": client_id, "scope": scope}))
    assert "$errors" not in out, out["$errors"]
    return out["report"]


def test_a_second_property_is_taxed_and_the_home_lived_in_is_spared():
    homes = [h("real_estate", 14 * TY, use="Ở", name="Nhà ở"), h("real_estate", 8 * TY, use="Cho thuê", name="Căn Q7")]
    (hit,) = _rules.second_property(factor("P01"), homes, {}, fixtures.market())
    assert hit["exposure"] == 8 * TY and hit["raw"] == -8 * TY * 0.004 and hit["affected"] == ["Căn Q7"]
    assert _rules.second_property(factor("P01"), homes[:1], {}, fixtures.market()) == []


def test_the_transfer_tax_change_compares_both_ways_of_counting():
    rented = h("real_estate", 10 * TY, cost=4 * TY, use="Cho thuê", name="Căn cho thuê")
    (hit,) = _rules.transfer_tax(factor("P02"), [rented], {}, fixtures.market())
    old, new = 10 * TY * 0.02, 6 * TY * 0.2
    assert hit["raw"] == old - new and "tốn thêm" in hit["message"]


def test_a_rate_rise_costs_a_floating_loan_and_bonds_by_duration():
    rows = [
        h("loan", 2 * TY, kind="liability", rate_type="floating", name="Vay"),
        h("bond", 1 * TY, duration=2.0, name="TP"),
    ]
    loan, bond = _rules.rates(factor("M01"), rows, {}, fixtures.market())
    assert loan["raw"] == -2 * TY * 0.005 and bond["raw"] == -1 * TY * 2.0 * 0.005


def test_severity_follows_the_share_of_net_worth():
    assert [_rules.severity(x) for x in (0.02, -0.01, 0.005, -0.0029)] == ["high", "high", "medium", "low"]


def test_impact_is_exposure_times_sensitivity_times_probability():
    for a in report("C04")["alerts"]:
        f = factor(a["factor"])
        assert abs(a["impact"] - a["exposure"] * a["sensitivity"] * f["probability"]) <= 2 + abs(a["impact"]) * 1e-3
        assert a["source"] and a["status_label"]


def test_every_client_gets_alerts_largest_first_and_the_latest_is_kept():
    for cid in fixtures.client_ids():
        r = report(cid)
        impacts = [abs(a["impact"]) for a in r["alerts"]]
        assert impacts == sorted(impacts, reverse=True) and r["alerts"], cid
        assert store.result(cid, "alerts")["counts"] == r["counts"]


def test_the_family_view_finds_the_second_property():
    assert not any(a["factor"] == "P01" for a in report("C01")["alerts"])
    assert any(a["factor"] == "P01" for a in report("C01", "family")["alerts"])


def test_the_sweep_job_runs_every_client(tmp_path):
    run = asyncio.run(
        Job("sweep", graph=alerts_flow, items=every_client, key="client_id", record_dir=str(tmp_path / "jobs")).run()
    )
    assert run.status == "ok" and sorted(run.results) == fixtures.client_ids()


def test_the_morning_schedule_sweeps_through_invoke():
    from operonx.app.jobs import Job as _Job  # noqa: F401 - the schedule's graph has doors: run it as a job

    run = asyncio.run(_Job("morning", graph=sweep_flow, items=[{"tick": 1}], record_dir=None).run())
    assert run.status == "ok"
    (summary,) = run.results.values()
    assert [c["client_id"] for c in summary["clients"]] == fixtures.client_ids()
