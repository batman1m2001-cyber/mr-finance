"""Everyone the demo knows, in the state file (owner's data layer, 2026-10-16).

``people`` holds one row per person:
- **staff**: CIO, RM, Compliance, Admin, and the specialists of the families' teams;
- **clients**: each customer, and a household member (``member_of`` the family's main client);
- **dependents**: a client's children or parents (``member_of`` that client).

A client's personal record is the row's ``data``. ``client_sources`` holds what each mock source system (bank,
broker, fund manager, housing platform, Open API) has for them. ``teams`` links a family to its RM and
specialists.

Seeds: ``data/clients/*.json`` and ``data/people/staff.json`` (scripts/make_people.py). They are loaded into an
empty database, and again on demo reset (:func:`reset`), and are never read at request time. A staff member added
to the seed after a database was made joins it, with an account, the first time a process opens it
(:func:`_top_up`). :func:`client`
puts a client back together exactly as their seed file reads.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from wealth.paths import DATA, state_path

KINDS = ("staff", "client", "dependent")
STAFF_ROLES = ("cio", "rm", "compliance", "admin", "specialist")

SCHEMA = """
create table if not exists people (
  id text primary key, seq integer not null, kind text not null, role text not null, name text not null,
  email text, member_of text, rm_id text, data text not null);  -- rm_id: the seed's; rm_assignment decides
create index if not exists people_kind on people (kind, role);
create index if not exists people_member on people (member_of);
create table if not exists client_sources (
  client_id text not null, source text not null, pos integer not null, data text not null,
  primary key (client_id, source));
create table if not exists teams (
  client_id text not null, person_id text not null, role text not null, lead integer not null, pos integer not null,
  primary key (client_id, person_id));
create table if not exists accounts (
  person_id text primary key, login text not null unique, password text, created real not null,
  last_login real);
create table if not exists settings (key text primary key, value text not null);
"""


def _seed_staff() -> Dict[str, Any]:
    return json.loads((DATA / "people" / "staff.json").read_text(encoding="utf-8"))


def _seed_clients() -> List[Dict[str, Any]]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((DATA / "clients").glob("*.json"))]


def _seed(con: sqlite3.Connection) -> None:
    seed = _seed_staff()
    seq = 0
    for s in seed["staff"]:
        seq += 1
        con.execute(
            "insert into people values (?, ?, 'staff', ?, ?, ?, null, null, ?)",
            (s["id"], seq, s["role"], s["name"], s.get("email"), json.dumps(s, ensure_ascii=False)),
        )
    teams = seed["teams"]
    specialists = [s["id"] for s in seed["staff"] if s["role"] == "specialist"]
    clients = _seed_clients()
    head = {c["id"]: c.get("member_of") or c["id"] for c in clients}
    for c in clients:
        seq += 1
        rec = {k: v for k, v in c.items() if k not in ("sources", "dependents")}
        rm = (teams.get(head[c["id"]]) or {}).get("rm")
        con.execute(
            "insert into people values (?, ?, 'client', 'client', ?, ?, ?, ?, ?)",
            (c["id"], seq, c["name"], c.get("email"), c.get("member_of"), rm, json.dumps(rec, ensure_ascii=False)),
        )
        for i, d in enumerate(c.get("dependents", []), 1):
            seq += 1
            con.execute(
                "insert into people values (?, ?, 'dependent', 'dependent', ?, null, ?, null, ?)",
                (f"{c['id']}-D{i}", seq, d["name"], c["id"], json.dumps(d, ensure_ascii=False)),
            )
        for pos, (src, data) in enumerate((c.get("sources") or {}).items()):
            con.execute(
                "insert into client_sources values (?, ?, ?, ?)",
                (c["id"], src, pos, json.dumps(data, ensure_ascii=False)),
            )
    for cid, t in teams.items():
        con.execute("insert into teams values (?, ?, 'rm', 0, 0)", (cid, t["rm"]))
        for pos, sid in enumerate(specialists, 1):
            con.execute("insert into teams values (?, ?, 'specialist', ?, ?)", (cid, sid, int(sid in t["lead"]), pos))


_TOPPED: set = set()


def _top_up(con: sqlite3.Connection) -> None:
    """Staff in the seed but not in a database seeded earlier (the second Admin, F4) are added, with an account
    when their role has one. Nothing else in the database changes."""
    have = {r[0] for r in con.execute("select id from people where kind = 'staff'")}
    if not have:
        return  # an empty database is seeded whole
    missing = [s for s in _seed_staff()["staff"] if s["id"] not in have]
    if not missing:
        return
    from people import auth

    con.execute("begin immediate")
    seq = con.execute("select coalesce(max(seq), 0) from people").fetchone()[0]
    accounts = con.execute("select 1 from accounts limit 1").fetchone() is not None
    demo = os.environ.get("MF_DEMO_PASSWORD") or ""
    for s in missing:
        seq += 1
        con.execute(
            "insert or ignore into people values (?, ?, 'staff', ?, ?, ?, null, null, ?)",
            (s["id"], seq, s["role"], s["name"], s.get("email"), json.dumps(s, ensure_ascii=False)),
        )
        if accounts and s["role"] in auth.ACCOUNT_ROLES:  # with no accounts yet, auth seeds them all
            con.execute(
                "insert or ignore into accounts values (?, ?, ?, ?, null)",
                (s["id"], (s.get("email") or s["id"]).lower(), auth.hash_password(demo) if demo else None, time.time()),
            )
    con.execute("commit")


@contextmanager
def _db(write: bool = False) -> Iterator[sqlite3.Connection]:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10, isolation_level=None)
    con.row_factory = sqlite3.Row
    try:
        con.executescript(SCHEMA)
        if str(path) not in _TOPPED:
            _top_up(con)
            _TOPPED.add(str(path))
        if write or not con.execute("select 1 from people limit 1").fetchone():
            con.execute("begin immediate")
            if not con.execute("select 1 from people limit 1").fetchone():
                _seed(con)
            yield con
            con.execute("commit")
        else:
            yield con
    except BaseException:
        if con.in_transaction:
            con.execute("rollback")
        raise
    finally:
        con.close()


def reset() -> None:
    """The demo starts over: the people go back to their seeds."""
    with _db(write=True) as con:
        for t in ("people", "client_sources", "teams"):
            con.execute(f"delete from {t}")
        _seed(con)


def _person(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        **json.loads(row["data"]),
        "id": row["id"],
        "kind": row["kind"],
        "role": row["role"],
        "name": row["name"],
        **({"email": row["email"]} if row["email"] else {}),
    }


# -- clients -----------------------------------------------------------------------------------


def client(client_id: str) -> Dict[str, Any]:
    """One client's record with their dependents and source-system data, as their seed file reads. KeyError when
    there is no such client."""
    cid = str(client_id or "")
    with _db() as con:
        row = con.execute("select data from people where id = ? and kind = 'client'", (cid,)).fetchone()
        if row is None:
            raise KeyError(f"no client {cid!r}")
        rec = json.loads(row["data"])
        deps = con.execute(
            "select data from people where member_of = ? and kind = 'dependent' order by seq", (cid,)
        ).fetchall()
        srcs = con.execute(
            "select source, data from client_sources where client_id = ? order by pos", (cid,)
        ).fetchall()
    rec["dependents"] = [json.loads(d["data"]) for d in deps]
    rec["sources"] = {s["source"]: json.loads(s["data"]) for s in srcs}
    return rec


def client_ids(members: bool = False) -> List[str]:
    """Every client id, sorted; household members only with ``members=True``."""
    q = "select id from people where kind = 'client'" + ("" if members else " and member_of is null")
    with _db() as con:
        return [r["id"] for r in con.execute(q + " order by id")]


def assigned_rm(client_id: str) -> Optional[str]:
    """The RM a family is assigned to (a household member: their family's), from the ``rm_assignment``
    configuration in force (Admin, FEAT-14; BRD-RULE-ROLE-02)."""
    with _db() as con:
        row = con.execute("select member_of from people where id = ? and kind = 'client'", (str(client_id),)).fetchone()
    if row is None:
        return None
    return _assignment().get(row["member_of"] or str(client_id))


def families_of(rm_id: str) -> List[str]:
    """The main clients an RM is assigned to."""
    return sorted(f for f, rm in _assignment().items() if rm == rm_id)


def _assignment() -> Dict[str, str]:
    from control import config

    return config.data("rm_assignment")


# -- staff -------------------------------------------------------------------------------------


def staff(role: Optional[str] = None) -> List[Dict[str, Any]]:
    """The staff in seed order, of one role if given."""
    q, args = "select * from people where kind = 'staff'", ()
    if role:
        q, args = q + " and role = ?", (role,)
    with _db() as con:
        return [_person(r) for r in con.execute(q + " order by seq", args)]


def person(person_id: str) -> Optional[Dict[str, Any]]:
    with _db() as con:
        row = con.execute("select * from people where id = ?", (str(person_id or ""),)).fetchone()
    return _person(row) if row else None


def team(client_id: str) -> Optional[Dict[str, Any]]:
    """A family's RM and specialists, the way the Chuyên gia page shows them: the specialists sit in their RM's
    office; ``lead`` marks the ones who matter most to this family."""
    with _db() as con:
        rows = con.execute(
            "select t.role as link, t.lead, p.* from teams t join people p on p.id = t.person_id "
            "where t.client_id = ? order by t.pos",
            (str(client_id),),
        ).fetchall()
    if not rows:
        return None
    rm = person(assigned_rm(client_id) or "") or next(_person(r) for r in rows if r["link"] == "rm")
    office = rm.get("office")
    out_rm = {
        "id": rm["id"],
        "role": rm.get("title_en", "Relationship manager"),
        "role_vi": rm["title"],
        "name": rm["name"],
        "email": rm.get("email"),
        "phone": rm.get("phone"),
        "office": office,
        "hours": rm.get("hours"),
    }
    specialists = []
    for r in rows:
        if r["link"] != "specialist":
            continue
        p = _person(r)
        specialists.append(
            {
                "id": p["specialty"],
                "person_id": p["id"],
                "role": p["title_en"],
                "role_vi": p["title"],
                "name": p["name"],
                "email": p.get("email"),
                "phone": p.get("phone"),
                "covers": p.get("covers", []),
                "office": office,
                "lead": bool(r["lead"]),
            }
        )
    return {"rm": out_rm, "specialists": specialists}


def everyone() -> List[Dict[str, Any]]:
    """Every person, in seed order, without the clients' records (the admin screen's list)."""
    with _db() as con:
        rows = con.execute("select id, kind, role, name, email, member_of from people order by seq").fetchall()
    rm = _assignment()
    return [{**dict(r), "rm_id": rm.get(r["member_of"] or r["id"]) if r["kind"] == "client" else None} for r in rows]
