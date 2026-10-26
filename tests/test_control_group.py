"""The control group (BRD-RULE-MEAS-06; BRD_REMAINING_PLAN G9, G-D8): drawn again from a seed within each stratum;
its RM gets no signal for it while the client loses nothing; the quarterly effect with a 90 % interval."""

import asyncio

import pytest
from operonx import Operon
from test_apply import MARKET, approved

from apply import reads
from contacts import store as contacts
from control import config
from control.errors import BadRequest
from feed.graph import feed_flow
from measure import control

FEED = Operon(feed_flow, params={"client_id": None, "scope": None, "role": None})
CFG = {"share": 0.5, "seed": "MEAS-06-2026", "strata": ["segment", "rm"]}


def items(client_id, role):
    out = asyncio.run(FEED.run(inputs={"client_id": client_id, "role": role}))
    assert "$errors" not in out, out["$errors"]
    return out["feed"]


def test_the_group_is_drawn_again_from_the_seed_within_each_stratum():
    assert control.strata(CFG) == {
        "segment=Priority|rm=rm01": ["C01", "C04", "C05"],
        "segment=Private|rm=rm02": ["C02"],
        "segment=Priority|rm=rm03": ["C03"],
    }
    assert control.members() == []  # 10 % of five families: the demo's group is empty
    assert control.members(CFG) == control.members(dict(CFG)) == ["C03", "C05"]  # the same seed, the same group
    # randomised rounding: each stratum takes ⌊share·n⌋ or one more, and on average exactly share·n
    sizes = []
    for i in range(400):
        got = control.members({**CFG, "share": 0.1, "seed": f"s{i}"})
        assert sum(1 for f in got if f in ("C01", "C04", "C05")) <= 1
        sizes.append(len(got))
    assert abs(sum(sizes) / len(sizes) - 0.5) < 0.1


def test_the_control_group_is_two_person_cio_configuration():
    with pytest.raises(ValueError, match="0,5"):
        config.propose("control_group", {**CFG, "share": 0.6}, "cio")
    with pytest.raises(ValueError, match="strata"):
        config.propose("control_group", {**CFG, "strata": ["age"]}, "cio")
    with pytest.raises(Exception, match="CIO"):
        config.propose("control_group", CFG, "admin")
    v = config.propose("control_group", CFG, "cio", "Thí điểm quý 4")
    with pytest.raises(Exception):
        config.decide(v["id"], "approve", "cio")  # not the proposer
    config.decide(v["id"], "approve", "cio2")
    assert control.members() == ["C03", "C05"]


def test_the_rm_gets_no_signal_for_a_control_family_and_the_client_loses_nothing(monkeypatch):
    _, run = approved(*MARKET)
    flagged = [r["family_id"] for r in run["ranking"] if r["pre_review"]]
    fid = flagged[0]
    assert run["families"] == 5  # every family is computed, the control group too
    before_rm, before_client = items(fid, "rm"), items(fid, "client")
    assert any(i["type"] == "impact" for i in before_rm["items"])
    monkeypatch.setattr(control, "members", lambda cfg=None: [fid])
    today = reads.rm_today()
    assert fid not in {c["family_id"] for c in today["cases"]} and today["control"] == [fid]
    assert today["control_withheld"] == [fid]
    rm = items(fid, "rm")
    assert not any(i["type"] in ("impact", "goal") for i in rm["items"]) and rm["withheld"] > 0
    assert items(fid, "client")["items"] == before_client["items"]  # the client sees everything
    with pytest.raises(BadRequest, match="nhóm đối chứng"):
        contacts.log(fid, "call", f"pre_review:{run['id']}", "", "rm01")
    assert not contacts.log(fid, "call", None, "Gọi định kỳ", "rm01")["from_signal"]  # service goes on


def test_the_effect_compares_the_groups_by_quarter_with_an_interval(monkeypatch):
    monkeypatch.setattr(control, "members", lambda cfg=None: ["C03", "C05"])
    for fid, n in (("C01", 3), ("C02", 2), ("C04", 4), ("C03", 1)):
        for _ in range(n):
            contacts.log(fid, "call", None, "", {"C02": "rm02", "C03": "rm03"}.get(fid, "rm01"))
    [q] = control.effect()["quarters"]
    c = q["contacts"]
    assert (c["n_tool"], c["n_control"]) == (3, 2)
    assert c["tool"] == pytest.approx(3 / q["months"], rel=1e-2) and c["control"] == pytest.approx(
        0.5 / q["months"], rel=1e-2
    )
    assert c["low"] < c["diff"] < c["high"]
    monkeypatch.setattr(control, "members", lambda cfg=None: ["C05"])
    [q] = control.effect()["quarters"]
    assert q["contacts"]["n_control"] == 1 and q["contacts"]["low"] is None  # too few for an interval
