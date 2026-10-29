"""Admin's users and roles (Q-25; owner 2026-10-18, docs/OWNER_BACKLOG_1018_PLAN.md U): a change to a staff account
is a request one Admin files and another approves, audited; disabling takes effect on a live session at its next
request; a one-time code sets the password once and expires; the guards hold (one's own account, the last Admin, an
RM with families, the demo's personas while the demo accounts are on)."""

import time

import pytest
from starlette.testclient import TestClient

from control import audit, roles
from control import db as control_db
from control.errors import Conflict
from people import accounts, auth, store


@pytest.fixture
def on(state, monkeypatch):
    """Sign-in on, demo accounts off (a bank deployment): the seeded accounts may be changed."""
    monkeypatch.setenv("MF_AUTH", "on")
    monkeypatch.setenv("MF_DEMO_ACCOUNTS", "off")
    monkeypatch.setattr(auth, "checking", lambda: False)  # direct calls: no request around them
    return state


def add(name="Nguyễn Văn An", email="an.nguyen@onewealth.example", role="rm", by="admin"):
    return accounts.request("add", by, "Nhân viên mới", name=name, email=email, role=role)


def actions(target):
    with control_db.tx() as con:
        rows = con.execute("select action, actor from audit_log where object = ? order by seq", (target,)).fetchall()
        assert audit.verify(con)["ok"]
    return [(r["action"], r["actor"]) for r in rows]


def test_an_account_is_added_by_two_admins_and_its_code_sets_the_password_once(on):
    r = add()
    assert r["status"] == "pending" and r["label"] == "Thêm tài khoản" and r["role_label"] == "RM"
    with pytest.raises(roles.Forbidden, match="không tự duyệt"):
        accounts.decide(r["id"], "approve", "admin")
    done = accounts.decide(r["id"], "approve", "admin2")
    code, pid = done["code"], done["person_id"]
    assert done["status"] == "approved" and len(code) == 10 and pid.startswith("nv")
    assert "code" not in accounts.get(r["id"]) and code not in str(accounts.read())  # shown once, never kept
    assert roles.user(pid)["role"] == "rm" and auth.login("an.nguyen@onewealth.example", "x") is None
    assert accounts.redeem("an.nguyen@onewealth.example", "WRONGCODE1", "mat-khau-moi-1") is None
    assert accounts.redeem("AN.NGUYEN@onewealth.example", code.lower(), "mat-khau-moi-1") == pid
    assert auth.login("an.nguyen@onewealth.example", "mat-khau-moi-1")
    assert accounts.redeem("an.nguyen@onewealth.example", code, "mat-khau-khac-2") is None  # spent
    assert actions(r["id"]) == [("account.requested", "admin"), ("account.approved", "admin2")]
    assert actions(pid) == [("account.code_used", pid)]


def test_a_code_expires_and_a_short_password_is_refused(on):
    r = accounts.decide(add()["id"], "approve", "admin2")
    with pytest.raises(accounts.AccountError, match="8 ký tự"):
        accounts.redeem("an.nguyen@onewealth.example", r["code"], "ngan")
    with store._db(write=True) as con:
        con.execute("update account_flags set code_exp = ? where person_id = ?", (time.time() - 1, r["person_id"]))
    assert accounts.redeem("an.nguyen@onewealth.example", r["code"], "mat-khau-moi-1") is None


def test_disable_ends_a_live_session_at_its_next_request_and_enable_restores_it(on):
    r = accounts.request("disable", "admin2", "Nghỉ việc", person_id="cio2")
    accounts.decide(r["id"], "approve", "admin")
    assert accounts.disabled("cio2")
    with pytest.raises(roles.Forbidden, match="đang bị khoá"):
        roles.user("cio2")
    auth.set_password("cio2", "mat-khau-cio-1")
    assert auth.login("ha.le@tcbwealth.example", "mat-khau-cio-1") is None
    tok = auth.issue("cio2")
    assert auth.verify(tok) is None  # the open session ends at its next request
    r = accounts.request("enable", "admin", person_id="cio2")
    accounts.decide(r["id"], "approve", "admin2")
    assert auth.verify(tok)["id"] == "cio2" and auth.login("ha.le@tcbwealth.example", "mat-khau-cio-1")


def test_a_role_change_is_read_at_the_next_request(on):
    tok = auth.issue("cio2")
    r = accounts.request("role", "admin", person_id="cio2", role="admin")
    assert r["from_label"] == "CIO" and r["role_label"] == "Quản trị"
    accounts.decide(r["id"], "approve", "admin2")
    assert auth.verify(tok)["role"] == "admin" and roles.user("cio2")["role"] == "admin"


def test_a_reset_voids_the_old_password_and_hands_a_code(on):
    auth.set_password("cio2", "mat-khau-cu-1")
    r = accounts.decide(accounts.request("reset", "admin", person_id="cio2")["id"], "approve", "admin2")
    assert auth.login("ha.le@tcbwealth.example", "mat-khau-cu-1") is None
    assert accounts.redeem("ha.le@tcbwealth.example", r["code"], "mat-khau-moi-1") == "cio2"


def test_the_guards(on):
    with pytest.raises(accounts.AccountError, match="tài khoản của mình"):
        accounts.request("disable", "admin", person_id="admin")
    with pytest.raises(accounts.AccountError, match="phụ trách"):  # rm01 has families in the RM assignment
        accounts.request("role", "admin", person_id="rm01", role="cio")
    with pytest.raises(accounts.AccountError, match="khách hàng"):
        accounts.request("disable", "admin", person_id="C01")
    with pytest.raises(accounts.AccountError, match="đã là tên đăng nhập"):
        add(email="yen.hoang@tcbwealth.example")
    with pytest.raises(accounts.AccountError, match="Vai trò"):
        add(role="client")
    with pytest.raises(roles.Forbidden):
        accounts.request("disable", "cio", person_id="cio2")
    r = accounts.request("disable", "admin", person_id="cio2")
    with pytest.raises(Conflict, match="đang chờ"):
        accounts.request("reset", "admin2", person_id="cio2")
    with pytest.raises(accounts.AccountError, match="lý do"):
        accounts.decide(r["id"], "reject", "admin2")
    with pytest.raises(roles.Forbidden, match="người đề xuất"):
        accounts.decide(r["id"], "withdraw", "admin2")
    assert accounts.decide(r["id"], "withdraw", "admin")["status"] == "withdrawn"
    with pytest.raises(Conflict):
        accounts.decide(r["id"], "approve", "admin2")


def test_the_last_enabled_admin_stays(on):
    """Behind the other guards (a request needs an enabled Admin who is not its subject), still checked: the state
    may move between a request and its approval."""
    auth._seeded()
    with store._db(write=True) as con:
        accounts._set_flags(con, "admin2", disabled=1)
        with pytest.raises(accounts.AccountError, match="Quản trị cuối cùng"):
            accounts._check(con, "disable", {"person_id": "admin"}, "x")
        with pytest.raises(accounts.AccountError, match="Quản trị cuối cùng"):
            accounts._check(con, "role", {"person_id": "admin", "role": "cio"}, "x")


def test_a_second_admin_does_not_approve_a_request_about_themselves(on):
    r = accounts.request("reset", "admin", person_id="admin2")
    with pytest.raises(roles.Forbidden, match="chính mình"):
        accounts.decide(r["id"], "approve", "admin2")


def test_the_demo_personas_are_kept_while_the_demo_accounts_are_on(on, monkeypatch):
    monkeypatch.setenv("MF_DEMO_ACCOUNTS", "on")
    with pytest.raises(accounts.AccountError, match="tài khoản demo"):
        accounts.request("disable", "admin", person_id="rm02")
    pid = accounts.decide(add()["id"], "approve", "admin2")["person_id"]  # one added here may change
    assert accounts.request("disable", "admin", person_id=pid)["status"] == "pending"
    d = accounts.read()
    assert d["demo_protected"] and {p["id"]: p["protected"] for p in d["people"]}["rm02"]
    assert not {p["id"]: p["protected"] for p in d["people"]}[pid]


def test_the_services_and_the_reads(state, monkeypatch):
    from app.web import allowed_roles, app

    monkeypatch.setenv("MF_DEMO_ACCOUNTS", "off")
    c = TestClient(app)
    pid = accounts.decide(add()["id"], "approve", "admin2")
    r = c.post("/api/auth/redeem", json={"login": "an.nguyen@onewealth.example", "code": pid["code"],
                                         "password": "mat-khau-moi-1"})  # fmt: skip
    assert r.status_code == 200 and r.json()["user"]["id"] == pid["person_id"] and auth.COOKIE in r.cookies
    bad = c.post("/api/auth/redeem", json={"login": "an.nguyen@onewealth.example", "code": pid["code"],
                                           "password": "mat-khau-moi-1"})  # fmt: skip
    assert bad.status_code == 401
    assert allowed_roles("/api/accounts") == ("admin",)
    d = c.get("/api/accounts").json()
    assert {"people", "requests", "demo_protected", "kinds", "roles"} <= set(d)
    assert not any(p["role"] == "client" for p in d["people"])
