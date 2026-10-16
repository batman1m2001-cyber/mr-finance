"""Moving to the bank (BRD-RULE-DATA-10, BRD_REMAINING_PLAN G4): the audit log on write-once segments, and the
export to PostgreSQL with the JSON fields split into tables — lossless, sealed values still sealed. The last test
loads a real PostgreSQL in Docker (skipped when Docker or the image is not on the machine)."""

import asyncio
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import uuid

import pytest
from operonx import Operon

from control import audit, crypto, db, pgexport, secrets, worm
from wealth.paths import ROOT, state_path


def entries(n, start=0):
    with db.tx() as con:
        for i in range(start, start + n):
            audit.append(con, "admin", "test.entry", f"T-{i}", {"i": i, "x": 1.5})


def check():
    from control.graph import audit_check_flow

    return asyncio.run(Operon(audit_check_flow, params={"tick": None, "at": None}).run(inputs={}))


def con():
    c = sqlite3.connect(state_path())
    c.row_factory = sqlite3.Row
    return c


# -- write-once segments ---------------------------------------------------------------------


def test_the_check_writes_each_new_run_of_rows_once_read_only_and_chained():
    entries(3)
    got = check()
    assert got["chain"]["ok"] and got["worm"]["ok"] and got["segment"]["rows"] == 3
    assert check()["segment"] is None  # nothing new: no segment
    entries(2, start=3)
    got = check()
    assert got["segment"]["first"] == 4 and got["segment"]["last"] == 5
    files = worm.segments(worm.folder())
    assert [f.name for f in files] == ["audit-0000000001-0000000003.jsonl", "audit-0000000004-0000000005.jsonl"]
    assert all(oct(f.stat().st_mode)[-3:] == "444" for f in files)
    head = json.loads(files[1].open(encoding="utf-8").readline())
    assert head["prev_segment"] == hashlib.sha256(files[0].read_bytes()).hexdigest()
    assert worm.verify(con()) | {"ok": True} == worm.verify(con()) and worm.verify(con())["rows"] == 5


def test_a_segment_is_never_written_over(monkeypatch):
    entries(2)
    with con() as c:
        first = worm.write(c)
    entries(1, start=2)
    listed = worm.segments(worm.folder())
    monkeypatch.setattr(worm, "segments", lambda where: listed)  # another writer takes the name after we listed
    taken = worm.folder() / "audit-0000000003-0000000003.jsonl"
    taken.write_text("someone else's", encoding="utf-8")
    with con() as c, pytest.raises(FileExistsError):
        worm.write(c)
    assert taken.read_text(encoding="utf-8") == "someone else's" and first["rows"] == 2
    assert not list(worm.folder().glob(".*.part"))


def _rewrite_history(seq, action):
    """What someone who can write the database (and has no HMAC key) can do: change a row and recompute every hash
    after it, so the chain in the database checks again."""
    c = sqlite3.connect(state_path())
    c.row_factory = sqlite3.Row
    c.executescript("drop trigger audit_log_no_update;")
    c.execute("update audit_log set action = ? where seq = ?", (action, seq))
    prev = c.execute("select hash from audit_log where seq = ?", (seq - 1,)).fetchone()[0] if seq > 1 else audit.GENESIS
    for r in c.execute("select * from audit_log where seq >= ? order by seq", (seq,)).fetchall():
        body = {k: r[k] for k in ("seq", "ts", "actor", "action", "object")} | {"data": json.loads(r["data"])}
        h = audit._digest(r["alg"], prev, body, None)
        c.execute("update audit_log set prev_hash = ?, hash = ? where seq = ?", (prev, h, r["seq"]))
        prev = h
    c.commit()
    c.close()


def test_a_row_changed_after_it_was_segmented_is_caught_though_the_chain_was_recomputed(monkeypatch):
    monkeypatch.delenv("AUDIT_HMAC_KEY", raising=False)
    secrets.clear()
    entries(4)
    check()
    _rewrite_history(2, "test.forged")
    with con() as c:
        assert audit.verify(c)["ok"]  # the database's own chain cannot tell
        got = worm.verify(c)
    assert not got["ok"] and "Dòng 2" in got["reason"] and "sửa" in got["reason"]
    out = check()
    assert out["segment"] is None  # nothing is added on top of a broken record
    from control import alerts

    assert [a for a in alerts.recent() if a["kind"] == "audit_chain" and a["status"] == "open"]


@pytest.mark.parametrize("how", ["edited", "removed", "writable"])
def test_a_segment_edited_removed_or_left_writable_breaks_the_walk(how):
    entries(2)
    check()
    entries(2, start=2)
    check()
    first, second = worm.segments(worm.folder())
    if how == "edited":
        os.chmod(first, 0o644)
        first.write_text(first.read_text(encoding="utf-8").replace("T-1", "T-9"), encoding="utf-8")
        os.chmod(first, 0o444)
    elif how == "removed":
        first.unlink()
    else:
        os.chmod(second, 0o644)
    with con() as c:
        got = worm.verify(c)
    assert not got["ok"], how
    assert {"edited": "Dòng 2", "removed": "không nối", "writable": "ghi được"}[how] in got["reason"]


def test_segments_can_be_turned_off(monkeypatch):
    monkeypatch.setenv("MF_AUDIT_WORM", "off")
    entries(1)
    got = check()
    assert got["worm"]["on"] is False and got["segment"] is None


# -- the PostgreSQL export, without PostgreSQL -------------------------------------------------


def roundtrip():
    """Every row split as for PostgreSQL, then rebuilt: it must equal the SQLite row opened."""
    c = con()
    children = {}
    for t in pgexport.tables(c):
        for r in pgexport.rows(c, t):
            parent, kids = pgexport.split(t, r)
            for name, rs in kids.items():
                children[name] = children.get(name, 0) + len(rs)
            assert pgexport.rebuild(t, parent, kids) == pgexport.logical(t, r), (t.name, r)
    return children


@pytest.fixture
def filled(monkeypatch):
    from test_security import K1, fill_every_table

    monkeypatch.setenv("MF_DATA_KEYS", f"k1={K1}")
    secrets.clear()
    fill_every_table()
    yield
    secrets.clear()


def test_split_and_rebuilt_every_row_is_the_same_and_client_data_stays_sealed(filled):
    from test_security import names

    kids = roundtrip()
    for name in ("client_transactions", "family_impact_holdings", "run_snapshot_families", "application_run_ranking"):
        assert kids.get(name), name
    c = con()
    by = {t.name: t for t in pgexport.tables(c)}
    blob = "".join(pgexport.script(c))
    assert not [n for n in names() if n in blob]  # the load file carries no client name
    t = by["client_sources"]
    split = ((r, *pgexport.split(t, r)) for r in pgexport.rows(c, t))
    r, parent, kids = next(x for x in split if x[2]["client_transactions"])
    assert crypto.sealed(parent["data"]) and kids["client_transactions"]
    assert all(crypto.sealed(k["data"]) for k in kids["client_transactions"])
    k = kids["client_transactions"][0]
    with pytest.raises(crypto.CryptoError):  # sealed at the child's own place: moved, it does not open
        crypto.open_(k["data"], crypto.where("client_transactions", (r["client_id"], r["source"], 1), "data"))


def test_a_sealed_database_is_not_split_without_the_keys(filled, monkeypatch):
    c = con()
    t = next(t for t in pgexport.tables(c) if t.name == "client_sources")
    row = next(pgexport.rows(c, t))
    monkeypatch.delenv("MF_DATA_KEYS")
    secrets.clear()
    with pytest.raises(pgexport.ExportError, match="MF_DATA_KEYS"):
        pgexport.split(t, row)


def test_a_plain_database_splits_and_rebuilds_too(monkeypatch):
    from test_security import fill_every_table

    monkeypatch.delenv("MF_DATA_KEYS", raising=False)
    secrets.clear()
    fill_every_table()
    assert roundtrip().get("client_transactions")


def test_a_value_of_another_shape_stays_in_data():
    c = con()
    c.executescript(audit.SCHEMA)
    c.execute("create table if not exists events (id text primary key, created real, status text, data text)")
    odd = {"news_ids": [], "factors": ["A", 3], "title": "x"}
    c.execute("insert into events values ('EV-1', 1.0, 'open', ?)", (json.dumps(odd),))
    c.commit()
    t = next(t for t in pgexport.tables(c) if t.name == "events")
    parent, kids = pgexport.split(t, next(pgexport.rows(c, t)))
    assert kids == {"event_news": [], "event_factors": []} and json.loads(parent["data"]) == odd


# -- a real PostgreSQL -------------------------------------------------------------------------

IMAGE = os.environ.get("MF_PG_IMAGE", "postgres:16-alpine")


def _image_here():
    if not shutil.which("docker"):
        return False
    return subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True).returncode == 0


@pytest.mark.skipif(not _image_here(), reason=f"needs Docker and the {IMAGE} image on this machine")
def test_the_export_loads_into_postgresql_and_checks_row_for_row(filled, tmp_path):
    report = tmp_path / "report.json"
    name = f"mrf-test-pg-{uuid.uuid4().hex[:8]}"
    p = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "export_postgres.py"),
            "--docker",
            name,
            "--start",
            IMAGE,
            "--stop",
            "--report",
            str(report),
        ],
        capture_output=True,
        text=True,
        env=os.environ | {"MF_STATE": str(state_path())},
        timeout=300,
    )
    assert p.returncode == 0, p.stdout[-2000:] + p.stderr[-2000:]
    got = json.loads(report.read_text(encoding="utf-8"))
    assert got["ok"] and got["postgres"].startswith("16")
    assert got["tables"]["client_sources"]["children"]["client_transactions"]["postgres"] > 0
    assert got["tables"]["audit_log"]["postgres"] == got["tables"]["audit_log"]["sqlite"] > 0
