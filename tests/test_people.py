"""The people table (src/people, owner's data layer 2026-10-16): every person in SQLite, seeded from the JSON files,
and read back exactly as those files read; the RM users are the families' RMs."""

import importlib.util
import json

from control import roles
from people import store
from wealth import fixtures
from wealth.paths import DATA, ROOT


def _make_advisory():
    spec = importlib.util.spec_from_file_location("make_advisory", ROOT / "scripts" / "make_advisory.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_client_reads_back_exactly_as_its_seed_file():
    seeds = sorted((DATA / "clients").glob("*.json"))
    assert [p.stem for p in seeds] == fixtures.client_ids(members=True)
    for p in seeds:
        assert fixtures.client(p.stem) == json.loads(p.read_text(encoding="utf-8")), p.stem
    assert fixtures.client_ids() == [p.stem for p in seeds if not json.loads(p.read_text()).get("member_of")]


def test_every_kind_of_person_is_a_row():
    kinds = {}
    for p in store.everyone():
        kinds.setdefault((p["kind"], p["role"]), []).append(p["id"])
    assert set(kinds) == {
        ("staff", "cio"),
        ("staff", "rm"),
        ("staff", "admin"),
        ("client", "client"),
        ("dependent", "dependent"),
    }
    deps = sum(len(json.loads(p.read_text())["dependents"]) for p in (DATA / "clients").glob("*.json"))
    assert len(kinds[("dependent", "dependent")]) == deps
    assert {p["id"] for p in store.everyone() if p["kind"] == "client"} == set(fixtures.client_ids(members=True))


def test_a_familys_team_is_the_one_the_advisory_record_had_and_its_rm_is_an_rm_user():
    adv = _make_advisory()
    for cid in adv.CLIENTS:
        team = store.team(cid)
        old = adv.team(cid)
        assert {k: v for k, v in team["rm"].items() if k != "id"} == old["rm"]
        rm = roles.require(team["rm"]["id"], "rm")
        assert rm["name"] == team["rm"]["name"]
        assert store.assigned_rm(cid) == team["rm"]["id"]
        assert cid in store.families_of(team["rm"]["id"])


def test_a_household_member_has_their_familys_rm():
    for cid in fixtures.client_ids(members=True):
        head = fixtures.client(cid).get("member_of")
        if head:
            assert store.assigned_rm(cid) == store.assigned_rm(head)


def test_no_retired_role_acts_in_the_app():
    """Compliance and the specialists are retired (OWN-FB-18): every user is a seeded CIO, RM or Admin."""
    assert not store.staff("specialist") and not store.staff("compliance")
    assert set(roles.users()) == {p["id"] for p in store.staff()}


def test_reset_brings_the_people_back_to_their_seeds():
    before = store.everyone()
    with store._db(write=True) as con:
        con.execute("delete from people where kind = 'dependent'")
        con.execute("update people set name = 'x' where id = 'C01'")
    assert store.everyone() != before
    store.reset()
    assert store.everyone() == before


def test_a_staff_member_added_to_the_seed_joins_a_database_seeded_before():
    from people import auth

    auth.accounts()  # seeded with accounts
    with store._db(write=True) as con:
        con.execute("delete from accounts where person_id = 'admin2'")
        con.execute("delete from people where id = 'admin2'")
    store._TOPPED.clear()  # a new process opens the older database
    assert [a["id"] for a in auth.accounts() if a["role"] == "admin"] == ["admin", "admin2"]
    assert roles.users()["admin2"]["role"] == "admin"
