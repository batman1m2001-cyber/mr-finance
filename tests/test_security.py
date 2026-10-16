"""BRD-NFR-07 (BRD_REMAINING_PLAN G3): client data encrypted at rest, keys from a secret store, and the attacks a
web app meets — each one tried here against the served application, not described.

- **At rest:** with a key, no client's or dependent's name and no account number is in the database files, after
  every kind of write (seed, statement, chat, risk result, RM proposal, application run, chat history); a sealed
  value moved to another row, or changed, does not open; a rotation re-seals in place and the old key can go.
- **Secrets:** the store, then a file, then the environment; a configured store that does not answer is an error.
- **Headers:** every kind of response carries them — the graph services, the web app, its files, ``/healthz``.
- **Attacks:** a cross-site write, a forged or tampered session, another family's data, SQL in the inputs, paths
  out of the web folder, an oversized upload. (Prompt injection: tests/test_views.py; stored script in the page:
  tests/ui/test_attacks.py.)
"""

import asyncio
import base64
import json
import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from operonx import Operon
from operonx.app import Application
from starlette.testclient import TestClient

from control import crypto, secrets
from people import auth, store
from wealth import store as wealth
from wealth.paths import DATA, state_path

K1, K2 = (base64.b64encode(os.urandom(32)).decode() for _ in range(2))
ACCOUNTS = ["1902-CASA-01", "VPB-001", "LN-HOME-01", "OH-TD-01", "VISA-SIG-01", "SSI-001"]


@pytest.fixture
def keyed(monkeypatch):
    monkeypatch.setenv("MF_DATA_KEYS", f"k1={K1}")
    yield
    secrets.clear()


def names():
    out = []
    for p in sorted((DATA / "clients").glob("*.json")):
        c = json.loads(p.read_text(encoding="utf-8"))
        out += [c["name"]] + [d["name"] for d in c.get("dependents", [])]
    return out


def found_in_files(needles):
    blobs = b"".join(p.read_bytes() for p in state_path().parent.glob("*.db*"))
    return [n for n in needles if n.encode("utf-8") in blobs]


def fill_every_table():
    """One of every write that holds client data."""
    from test_apply import MARKET, approved

    from declare.graph import declare_flow
    from statements.graph import statement_flow

    store.client("C01")  # seeds
    raw = (DATA / "samples" / "vps_C01.csv").read_bytes()
    asyncio.run(
        Operon(statement_flow, params={"client_id": None, "filename": None, "content": None}).run(
            inputs={"client_id": "C01", "filename": "vps_C01.csv", "content": base64.b64encode(raw).decode()}
        )
    )
    asyncio.run(
        Operon(declare_flow, params={"client_id": None, "message": None, "session_id": None}).run(
            inputs={"client_id": "C01", "message": "Tôi có 10 lượng vàng", "session_id": "C01-s"}
        )
    )
    wealth.add_profile("C01", "dependent", {"name": "Nguyễn Minh Khang", "relation": "Con", "via": "chat"})
    wealth.put_result("C01", "risk", {"for": "Nguyễn Minh Khoa", "level": 3})
    rid = wealth.propose("C01", "goal", "Đề xuất cho Nguyễn Minh Khoa", {"account": "1902-CASA-01"})
    wealth.decide(rid, "approved", "Đã gọi Nguyễn Minh Khoa")
    approved(*MARKET)  # an application run: snapshot, ranking, exposure, every family's result
    session = crypto.SealedSession(_Memory(), "C01-s")
    asyncio.run(session.add_items([{"role": "user", "content": "Tôi là Nguyễn Minh Khoa, tài khoản 1902-CASA-01"}]))
    return session


class _Memory:
    def __init__(self):
        self.items = []

    async def get_items(self, limit=None):
        return list(self.items)

    async def add_items(self, items):
        self.items += items

    async def pop_item(self):
        return self.items.pop() if self.items else None

    async def clear(self):
        self.items.clear()


# -- at rest -----------------------------------------------------------------------------------


def test_without_a_key_the_names_are_there_to_find(monkeypatch):  # the control: the check below can see a name
    monkeypatch.delenv("MF_DATA_KEYS", raising=False)
    fill_every_table()
    assert found_in_files(["Nguyễn Minh Khoa", "1902-CASA-01"])


def test_with_a_key_no_client_name_or_account_number_is_in_the_database(keyed):
    session = fill_every_table()
    assert not found_in_files(names() + ["Nguyễn Minh Khang"] + ACCOUNTS)
    assert "Nguyễn Minh Khoa" not in json.dumps(session.inner.items, ensure_ascii=False)
    # and the product reads it back as it was written
    assert store.client("C01")["name"] == "Nguyễn Minh Khoa"
    assert [d["name"] for d in wealth.profile("C01", "dependent")] == ["Nguyễn Minh Khang"]
    assert wealth.result("C01", "risk")["for"] == "Nguyễn Minh Khoa"
    assert asyncio.run(session.get_items())[0]["content"].startswith("Tôi là Nguyễn Minh Khoa")
    with sqlite3.connect(state_path()) as con:
        assert set(crypto.census(con)) == {"k1"}  # nothing plain


def test_a_sealed_value_moved_or_changed_does_not_open(keyed):
    a, b = crypto.where("people", "C01", "name"), crypto.where("people", "C02", "name")
    sealed = crypto.seal("Nguyễn Minh Khoa", a)
    assert crypto.open_(sealed, a) == "Nguyễn Minh Khoa"
    with pytest.raises(crypto.CryptoError, match="chuyển chỗ"):
        crypto.open_(sealed, b)  # copied to another row
    raw = bytearray(base64.b64decode(sealed.rsplit(":", 1)[1]))
    raw[20] ^= 1
    with pytest.raises(crypto.CryptoError):
        crypto.open_(sealed.rsplit(":", 1)[0] + ":" + base64.b64encode(bytes(raw)).decode(), a)
    with pytest.raises(crypto.CryptoError, match="k9"):
        crypto.open_(sealed.replace(":k1:", ":k9:"), a)  # a key nobody has


def test_a_plain_database_is_sealed_and_a_rotation_lets_the_old_key_go(monkeypatch):
    monkeypatch.delenv("MF_DATA_KEYS", raising=False)
    store.client("C01")  # seeded plain
    with sqlite3.connect(state_path()) as con:
        assert set(crypto.census(con)) == {"plain"}
    monkeypatch.setenv("MF_DATA_KEYS", f"k1={K1}")
    with sqlite3.connect(state_path(), isolation_level=None) as con:
        assert crypto.rotate(con)["people"] > 0
        assert set(crypto.census(con)) == {"k1"}
    monkeypatch.setenv("MF_DATA_KEYS", f"k2={K2},k1={K1}")  # the new key first
    with sqlite3.connect(state_path(), isolation_level=None) as con:
        crypto.rotate(con)
        assert set(crypto.census(con)) == {"k2"}
    monkeypatch.setenv("MF_DATA_KEYS", f"k2={K2}")  # k1 dropped
    assert store.client("C01")["sources"]["techcombank"]["accounts"][0]["id"] == "1902-CASA-01"
    monkeypatch.setenv("MF_DATA_KEYS", f"k1={K1}")  # only the old key: the data does not open
    with pytest.raises(crypto.CryptoError):
        store.client("C01")


def test_a_bad_key_setting_is_refused(monkeypatch):
    for bad in ("k1=not-base64!", f"k1={base64.b64encode(b'short').decode()}", f"1x={K1}"):
        monkeypatch.setenv("MF_DATA_KEYS", bad)
        with pytest.raises(crypto.CryptoError):
            crypto.keys()


# -- secrets -----------------------------------------------------------------------------------


class Vault(BaseHTTPRequestHandler):
    values: dict = {}

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.headers.get("X-Vault-Token") != "t0ken" or self.path != "/v1/secret/data/mr-finance":
            self.send_response(403)
            self.end_headers()
            return
        body = json.dumps({"data": {"data": Vault.values, "metadata": {"version": 3}}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def test_secrets_come_from_the_store_then_a_file_then_the_environment(tmp_path, monkeypatch):
    server = ThreadingHTTPServer(("127.0.0.1", 0), Vault)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        Vault.values = {"MF_DATA_KEYS": f"k1={K1}"}
        (tmp_path / "AUDIT_HMAC_KEY").write_text("from-a-file\n")
        monkeypatch.setenv("MF_SECRETS_DIR", str(tmp_path))
        monkeypatch.setenv("MF_ZONE_KEY", "from-env")
        monkeypatch.setenv("MF_DATA_KEYS", "k1=stale-copy-in-env")
        monkeypatch.setenv("VAULT_ADDR", f"http://127.0.0.1:{server.server_address[1]}")
        monkeypatch.setenv("VAULT_TOKEN", "t0ken")
        secrets.clear()
        assert secrets.lookup("MF_DATA_KEYS") == (f"k1={K1}", "vault")  # the store wins over the stale env copy
        assert crypto.current() == "k1"
        assert secrets.lookup("AUDIT_HMAC_KEY") == ("from-a-file", "file")
        assert secrets.lookup("MF_ZONE_KEY") == ("from-env", "env")
        assert secrets.lookup("MF_INBOX_KEY") == (None, "none")
        monkeypatch.setenv("VAULT_TOKEN", "wrong")
        secrets.clear()
        with pytest.raises(secrets.SecretStoreError):  # never a quiet fall back to the environment
            secrets.get("MF_DATA_KEYS")
        assert secrets.source("MF_DATA_KEYS") == "error"
    finally:
        server.shutdown()
        secrets.clear()


# -- the served application --------------------------------------------------------------------


@pytest.fixture
def http(monkeypatch):
    monkeypatch.setenv("MF_AUTH", "on")
    with TestClient(Application.find(".").asgi(), base_url="http://testserver") as c:
        yield c


def as_(c, person_id):
    c.cookies.clear()
    c.cookies.set(auth.COOKIE, auth.issue(person_id))
    return c


def test_every_kind_of_response_carries_the_security_headers(http):
    as_(http, "C01")
    answers = {
        "page": http.get("/"),
        "file": http.get("/shell.js"),
        "web read": http.get("/api/how"),
        "graph service": http.post("/api/dashboard", json={"client_id": "C01"}),
        "health": http.get("/healthz"),
        "refusal": http.get("/api/audit"),
    }
    for what, r in answers.items():
        h = r.headers
        assert (
            "frame-ancestors 'none'" in h["content-security-policy"]
            and "script-src 'self' 'sha256-" in (h["content-security-policy"])
        ), what
        assert (h["x-content-type-options"], h["x-frame-options"], h["referrer-policy"]) == (
            "nosniff",
            "DENY",
            "no-referrer",
        ), what
        assert "strict-transport-security" not in h, what  # plain http: the host's TLS is not there
    assert answers["graph service"].status_code == 200 and answers["refusal"].status_code == 403
    assert answers["graph service"].headers["cache-control"] == "no-store"
    assert answers["web read"].headers["cache-control"] == "no-store"
    assert (
        "max-age" in http.get("/healthz", headers={"x-forwarded-proto": "https"}).headers["strict-transport-security"]
    )


def test_the_page_runs_no_script_but_its_own(http):
    import hashlib
    import re

    html = http.get("/").text
    csp = http.get("/").headers["content-security-policy"]
    for body in re.findall(r"<script>(.*?)</script>", html, re.S):  # each inline script is allowed by its hash only
        assert base64.b64encode(hashlib.sha256(body.encode()).digest()).decode() in csp
    assert "unsafe-inline" not in csp.split("script-src", 1)[1].split(";")[0]
    assert "unsafe-eval" not in csp


def test_a_session_cookie_is_http_only_same_site_and_secure_over_https(http, monkeypatch):
    monkeypatch.setenv("MF_DEMO_ACCOUNTS", "on")
    plain = http.post("/api/auth/demo", json={"id": "C01"}).headers["set-cookie"].lower()
    assert "httponly" in plain and "samesite=lax" in plain and "secure" not in plain
    https = http.post("/api/auth/demo", json={"id": "C01"}, headers={"x-forwarded-proto": "https"})
    assert "secure" in https.headers["set-cookie"].lower()


def test_a_write_from_another_site_is_refused_before_the_app(http):
    as_(http, "C01")
    before = len(wealth.profile("C01"))
    evil = http.post(
        "/api/declare",
        json={"client_id": "C01", "message": "Tôi có 10 lượng vàng", "session_id": "x"},
        headers={"Origin": "https://evil.example"},
    )
    assert evil.status_code == 403 and "trang khác" in evil.json()["error"]
    assert len(wealth.profile("C01")) == before  # nothing recorded
    for origin in ("null", "http://testserver.evil.example"):
        assert http.post("/api/reset", headers={"Origin": origin}).status_code == 403
    same = http.post(
        "/api/declare",
        json={"client_id": "C01", "message": "Tôi có 10 lượng vàng", "session_id": "x"},
        headers={"Origin": "http://testserver"},
    )
    assert same.status_code == 200 and len(wealth.profile("C01")) == before + 1


def test_a_tampered_or_forged_session_opens_nothing(http):
    good = auth.issue("C01")
    body, sig = good.split(".")
    claims = json.loads(base64.urlsafe_b64decode(body + "=="))
    for token in (
        base64.urlsafe_b64encode(json.dumps({**claims, "sub": "admin"}).encode()).rstrip(b"=").decode() + "." + sig,
        auth.issue("C01", now=0),  # expired
        good[:-2] + ("AA" if good[-2:] != "AA" else "BB"),
        "",
    ):
        http.cookies.clear()
        http.cookies.set(auth.COOKIE, token)
        assert http.get("/api/how").status_code == 401
        assert http.post("/api/dashboard", json={"client_id": "C01"}).status_code in (401, 403)


def test_one_family_cannot_read_another(http):
    as_(http, "C01")
    assert http.post("/api/dashboard", json={"client_id": "C02"}).status_code == 403
    assert http.get("/api/families/C02/impact").status_code == 403


def test_sql_in_the_inputs_is_data(http):
    as_(http, "cio")
    with sqlite3.connect(state_path()) as con:
        people = con.execute("select count(*) from people").fetchone()[0]
    for evil in ("C01' OR '1'='1", "C01; drop table people; --", "' union select data from people --"):
        r = http.post("/api/dashboard", json={"client_id": evil})
        assert r.status_code == 400 and "no client" in r.json()["error"] and "Nguyễn" not in r.text
        r = http.post("/api/search", json={"q": evil, "role": "cio"})
        assert r.status_code < 500 and "Nguyễn Minh Khoa" not in r.text
    with sqlite3.connect(state_path()) as con:
        assert con.execute("select count(*) from people").fetchone()[0] == people
    assert as_(http, "admin").get("/api/audit/verify").json()["ok"]


def test_no_path_leads_out_of_the_web_folder(http):
    as_(http, "admin")
    for path in (
        "/../data/state.db",
        "/%2e%2e/resources.yaml",
        "/samples/../../.env",
        "/samples/%2e%2e/%2e%2e/resources.yaml",
        "/..%2fapp/main.py",
        "/web/../app/main.py",
    ):
        r = http.get(path)
        assert r.status_code in (400, 404) or "llm:assistant" not in r.text and "APP = Application" not in r.text, path
    from statements.ops import load_sample

    out = load_sample(filename="../../.env")()  # the eval's sample loader: an op reports its error, sends nothing
    assert "content" not in (out or {})


def test_an_oversized_upload_is_refused(http):
    as_(http, "C01")
    big = base64.b64encode(b"x" * (5 * 1024 * 1024 + 1)).decode()
    r = http.post("/api/statement", json={"client_id": "C01", "filename": "a.csv", "content": big})
    assert r.status_code >= 400 and "5 MB" in r.text
