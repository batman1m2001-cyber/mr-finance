import asyncio

from operonx import Operon

from consolidate.graph import consolidate_flow
from consolidate.ops import household, merge_holdings
from wealth import fixtures, store

ENGINE = Operon(consolidate_flow, params={"client_id": None, "scope": None})


def run(client_id, scope="personal"):
    out = asyncio.run(ENGINE.run(inputs={"client_id": client_id, "scope": scope}))
    assert "$errors" not in out, out["$errors"]
    return out


def test_the_family_view_holds_only_members_who_consented():
    assert [m["id"] for m in household(client_id="C01", scope="family")()["members"]] == [
        "C01",
        "C01S",
    ]
    c02 = household(client_id="C02", scope="family")()
    assert [m["id"] for m in c02["members"]] == ["C02"] and c02["waiting"][0]["id"] == "C02S"
    # an op that raises is recorded, not raised: the run says which op and why
    bad = asyncio.run(ENGINE.run(inputs={"client_id": "C01", "scope": "everyone"}))
    assert "holdings" not in bad
    (err,) = [e for k, e in bad["$errors"].items() if k.endswith(".who")]
    assert err["type"] == "ValueError"


def test_the_merge_keeps_one_copy_of_each_holding_and_counts_every_source():
    h = {
        "key": "C01:declared:g",
        "owner": "C01",
        "source": "declared",
        "trust": "declared",
        "kind": "asset",
        "value": 5,
    }
    out = merge_holdings(
        members=[{"id": "C01", "name": "A"}],
        waiting=[],
        bank=[],
        broker=[],
        funds=[],
        homes=[],
        other=[],
        read=[],
        said=[h, {**h, "value": 7}],
        transactions=[],
    )()
    assert [x["value"] for x in out["holdings"]] == [7]
    declared = next(s for s in out["sources"] if s["source"] == "declared")
    assert (declared["count"], declared["assets"], declared["status"]) == (1, 7, "connected")
    assert next(s for s in out["sources"] if s["source"] == "statement")["status"] == "empty"


def test_every_client_consolidates_from_every_tier():
    for cid in fixtures.client_ids():
        out = run(cid)
        tiers = {h["tier"] for h in out["holdings"]}
        assert 1 in tiers, cid
        assert all(h["owner"] == cid for h in out["holdings"])
    assert {h["tier"] for h in run("C01")["holdings"]} == {1, 2, 3}


def test_the_family_view_adds_the_spouse_and_their_transactions():
    me, family = run("C01"), run("C01", "family")
    assert {h["owner"] for h in family["holdings"]} == {"C01", "C01S"}
    assert len(family["transactions"]) > len(me["transactions"])
    assert family["holdings"][0]["owner_name"]


def test_what_a_client_added_joins_the_picture():
    store.put_holdings(
        "C05",
        "statement",
        [
            {
                "key": "C05:statement:vps:stock:SSI",
                "owner": "C05",
                "source": "statement",
                "tier": 2,
                "trust": "statement",
                "kind": "asset",
                "class": "stock",
                "name": "Cổ phiếu SSI (VPS)",
                "value": 33_000_000,
                "prev_value": 31_500_000,
                "ytd_value": None,
                "cost": None,
                "liquid": True,
                "stress": 0.375,
                "detail": {},
            }
        ],
    )
    store.add_profile("C05", "asset", {"class": "gold", "name": "Vàng", "qty": 1})
    out = run("C05")
    trusts = {h["trust"] for h in out["holdings"]}
    assert {"verified", "statement", "declared"} <= trusts
