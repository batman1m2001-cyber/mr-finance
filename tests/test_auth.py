"""Sign-in (src/people/auth.py, BRD-RULE-SEC-01): every person has their own account; only a verified session is
trusted; a customer sees only their family, an RM only the families assigned to them; nobody acts in someone
else's name. Sign-in is ON in this file (the rest of the suite runs with MF_AUTH=off)."""

import pytest
from operonx.app import Application
from starlette.testclient import TestClient

from people import auth, store

PASSWORD = "mat-khau-demo"


@pytest.fixture(autouse=True)
def sign_in_on(monkeypatch):
    monkeypatch.setenv("MF_AUTH", "on")
    monkeypatch.setenv("MF_DEMO_PASSWORD", PASSWORD)
    monkeypatch.setenv("MF_DEMO_ACCOUNTS", "on")


@pytest.fixture
def http():
    with TestClient(Application.find(".").asgi()) as c:
        yield c


def as_(c, person_id):
    c.cookies.clear()
    c.cookies.set(auth.COOKIE, auth.issue(person_id))
    return c


# -- accounts and sessions ---------------------------------------------------------------------


def test_every_client_and_every_acting_staff_member_has_an_account_and_specialists_do_not():
    have = {a["id"] for a in auth.accounts()}
    people = store.everyone()
    assert have == {p["id"] for p in people if p["role"] in auth.ACCOUNT_ROLES}
    assert {"C01", "C01S", "rm01", "rm03", "cio2", "compliance", "admin"} <= have
    assert not have & {p["id"] for p in people if p["role"] in ("specialist", "dependent")}


def test_a_password_is_kept_as_a_salted_hash():
    a, b = auth.hash_password("x" * 8), auth.hash_password("x" * 8)
    assert a != b and "x" * 8 not in a
    assert auth.check_password("x" * 8, a) and not auth.check_password("y" * 8, a)


def test_a_session_is_signed_and_expires():
    t = auth.issue("rm01", now=1_000)
    assert auth.verify(t, now=1_001)["id"] == "rm01"
    assert auth.verify(t, now=1_000 + auth.TTL) is None
    body, sig = t.split(".")
    forged = auth.issue("cio", now=1_000).split(".")[0] + "." + sig
    assert auth.verify(forged, now=1_001) is None
    assert auth.verify("garbage") is None


def test_login_by_email_or_id_and_one_answer_for_any_failure(http):
    r = http.post("/api/auth/login", json={"login": "YEN.HOANG@tcbwealth.example", "password": PASSWORD})
    assert r.status_code == 200 and r.json()["user"]["id"] == "rm01"
    assert "httponly" in r.headers["set-cookie"].lower() and "samesite=lax" in r.headers["set-cookie"].lower()
    assert http.get("/api/auth/me").json()["user"]["families"] == ["C01", "C04", "C05"]
    assert http.post("/api/auth/login", json={"login": "c01", "password": PASSWORD}).json()["user"]["family"] == "C01"
    wrong = http.post("/api/auth/login", json={"login": "c01", "password": "x"})
    nobody = http.post("/api/auth/login", json={"login": "nobody", "password": PASSWORD})
    assert wrong.status_code == nobody.status_code == 401 and wrong.json() == nobody.json()
    assert http.post("/api/auth/logout").status_code == 200
    assert http.get("/api/auth/me").json()["user"] is None


def test_without_a_demo_password_nobody_signs_in_with_one(http, monkeypatch):
    monkeypatch.delenv("MF_DEMO_PASSWORD")
    auth.reset()
    assert http.post("/api/auth/login", json={"login": "c01", "password": PASSWORD}).status_code == 401
    auth.set_password("C01", "mot-mat-khau-rieng")
    assert http.post("/api/auth/login", json={"login": "c01", "password": "mot-mat-khau-rieng"}).status_code == 200


def test_the_demo_account_list_opens_only_when_switched_on(http, monkeypatch):
    listed = http.get("/api/auth/accounts").json()["accounts"]
    assert {a["role"] for a in listed} == set(auth.ACCOUNT_ROLES)
    assert http.post("/api/auth/demo", json={"id": "compliance2"}).json()["user"]["role"] == "compliance"
    monkeypatch.setenv("MF_DEMO_ACCOUNTS", "off")
    assert http.get("/api/auth/accounts").json()["accounts"] == []
    assert http.post("/api/auth/demo", json={"id": "cio"}).status_code == 403
    assert http.post("/api/auth/demo", json={"id": "sp_global"}).status_code == 403


def test_a_sign_in_is_in_the_audit_chain(http):
    http.post("/api/auth/demo", json={"id": "cio"})
    as_(http, "compliance")
    rows = http.get("/api/audit").json()["rows"]
    assert any(r["action"] == "auth.sign_in" and r["actor"] == "cio" for r in rows)


# -- what each person may open ---------------------------------------------------------------


def test_nothing_under_api_opens_without_a_session(http):
    from app.web import STAFF_ONLY

    for path in ("/api/clients", "/api/events", "/api/families/C01/impact", "/api/advisory?client_id=C01") + tuple(
        p.rstrip("/") for p in STAFF_ONLY
    ):
        assert http.get(path).status_code == 401, path
    assert http.get("/healthz").status_code == 200
    assert http.post("/api/dashboard", json={"client_id": "C01"}).status_code != 200


def test_a_customer_sees_only_their_own_family(http):
    as_(http, "C02")
    assert [c["id"] for c in http.get("/api/clients").json()["clients"]] == ["C02"]
    assert http.get("/api/families/C02/impact").status_code == 200
    assert http.get("/api/families/C01/impact").status_code == 403
    assert http.get("/api/advisory", params={"client_id": "C01"}).status_code == 403
    assert http.get("/api/events").status_code == 403
    assert http.post("/api/dashboard", json={"client_id": "C02"}).status_code == 200
    assert http.post("/api/dashboard", json={"client_id": "C01"}).status_code != 200
    as_(http, "C02S")  # a household member sees their family
    assert http.post("/api/dashboard", json={"client_id": "C02", "scope": "family"}).status_code == 200


def test_a_customer_cannot_ask_for_the_staff_view(http):
    as_(http, "C01")
    staff = http.get("/api/families/C01/impact", params={"role": "rm"})
    assert staff.status_code == 200 and staff.json()["role"] == "client"


def test_an_rm_sees_only_the_families_assigned_to_them(http):
    as_(http, "rm03")
    assert [c["id"] for c in http.get("/api/clients").json()["clients"]] == ["C03"]
    assert http.get("/api/families/C03/impact", params={"role": "rm"}).status_code == 200
    assert http.get("/api/families/C01/impact", params={"role": "rm"}).status_code == 403
    assert http.post("/api/dashboard", json={"client_id": "C01"}).status_code != 200
    assert http.get("/api/rm/today").status_code == 200
    as_(http, "cio")
    assert http.get("/api/rm/today").status_code == 403
    assert len(http.get("/api/clients").json()["clients"]) == len(store.client_ids())


def test_nobody_acts_in_someone_elses_name(http):
    from control import config

    body = {"kind": "thresholds", "data": {**config.THRESHOLDS, "concentration_share": 0.5}}
    as_(http, "cio")
    assert http.post("/api/config/propose", json={**body, "by": "cio2"}).status_code != 200
    vid = http.post("/api/config/propose", json={**body, "by": "cio"}).json()["version"]["id"]
    assert (
        http.post("/api/config/decide", json={"version_id": vid, "action": "approve", "by": "cio2"}).status_code != 200
    )
    as_(http, "cio2")
    ok = http.post("/api/config/decide", json={"version_id": vid, "action": "approve", "by": "cio2"})
    assert ok.status_code == 200 and ok.json()["version"]["status"] == "ACTIVE"


def test_runs_no_request_started_are_not_checked():
    """The engine over every family, a scheduled job, a direct run: no session, nothing to check."""
    from wealth import fixtures

    assert [fixtures.client(c)["id"] for c in fixtures.client_ids()] == fixtures.client_ids()


def test_lists_over_every_family_show_only_the_families_the_person_may_see(http):
    """Search, the review queue and the advisory record read every family for the CIO, and only an RM's own
    families for that RM (a run over every family no longer fails for them)."""
    as_(http, "rm03")

    def clients_found(q, cid="C03"):
        hits = http.post("/api/search", json={"q": q, "role": "rm", "client_id": cid}).json()["search"]["hits"]
        return [h["client_id"] for h in hits if h["kind"] == "client"]

    assert clients_found("Phạm Gia Huy") == ["C03"]
    assert clients_found("Nguyễn Minh Khoa") == []
    assert [c["id"] for c in http.get("/api/advisory/all").json()["clients"]] == ["C03"]
    assert {r["client_id"] for r in http.get("/api/review").json()["items"]} <= {"C03", "C03S"}
    as_(http, "rm01")
    assert clients_found("Nguyễn Minh Khoa", "C01") == ["C01"]
    assert http.post("/api/search", json={"q": "x", "role": "rm", "client_id": "C03"}).status_code != 200
    as_(http, "cio")
    assert len(http.get("/api/advisory/all").json()["clients"]) == len(store.client_ids())
