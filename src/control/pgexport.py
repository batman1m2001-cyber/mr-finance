"""Moving to the bank's database (BRD-RULE-DATA-10, BRD_REMAINING_PLAN G4, ADR-0025): the SQLite state mapped to
PostgreSQL, with the JSON fields the product reads by field split out of ``data`` into columns and child tables.

- **Every table** keeps its columns, primary key, unique constraints and indexes: ``text`` → ``text``, ``real`` →
  ``double precision``, ``integer`` → ``bigint`` (an AUTOINCREMENT key → an identity column).
- **JSON** ``data`` columns become ``jsonb``, except where a client value may be sealed whole (``crypto.COLUMNS``):
  those stay ``text``, as sealed values are strings. ``external_outputs.body`` stays the text that was signed.
- **Split fields** (``FIELD_COLUMNS``): a scalar a query filters on becomes a column of its table
  (``agent_runs.status``, ``agent_jobs.started``, ``policy_documents.source_url`` …).
- **Child tables** (``CHILDREN``): a list or map inside ``data`` becomes rows of its own — status histories, the
  news an event groups, a run's families and ranking, a family's holdings, a source's transactions.
- **Lossless:** a value is split only when it has the expected shape (a non-empty list of dicts, a string …);
  anything else stays in ``data`` as it was. ``rebuild()`` puts a PostgreSQL row back together, and the export is
  checked by rebuilding every row read back from PostgreSQL and comparing it with SQLite.
- **Encryption carries over:** the associated data of a sealed value is its table, primary key and column
  (``crypto.where``), so a sealed value that is not split is copied as it is and opens in PostgreSQL. A sealed value
  that is split is opened with the keys and each child's data sealed again at the child's own place. Without the
  keys a sealed database cannot be split: the export says so and stops.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

from control import crypto

TYPES = {"text": "text", "real": "double precision", "integer": "bigint"}
SIGNED_TEXT = {("external_outputs", "body")}  # hashed as stored: kept byte for byte


@dataclass(frozen=True)
class FieldColumn:
    table: str
    field: str
    type: str  # "text" | "double precision"


@dataclass(frozen=True)
class Child:
    """``table.data[field]`` moved to the table ``name``: ``parent`` names the columns holding the parent's key;
    ``shape`` is ``list`` (dicts, by ``pos``), ``values`` (strings, by ``pos``, in ``column``) or ``map`` (key in
    ``column``); ``columns`` are fields of each item made columns, the rest of the item stays in ``data``."""

    table: str
    field: str
    name: str
    parent: Tuple[str, ...]
    shape: str
    column: str = ""
    columns: Tuple[Tuple[str, str], ...] = ()


FIELD_COLUMNS = [
    FieldColumn("agent_runs", "status", "text"),  # views/store.py: the agents' last runs, by status
    FieldColumn("agent_runs", "error", "text"),
    FieldColumn("agent_runs", "finished", "double precision"),
    FieldColumn("agent_jobs", "started", "double precision"),  # views/queue.py: jobs running too long
    FieldColumn("policy_documents", "source_url", "text"),  # policy/store.py: one document per source
]

HISTORY = (("at", "double precision"), ("by", "text"), ("status", "text"), ("note", "text"))
CHILDREN = [
    Child("views", "history", "view_history", ("view_id",), "list", columns=HISTORY),
    Child("config_versions", "history", "config_version_history", ("version_id",), "list", columns=HISTORY),
    Child("policy_documents", "history", "policy_document_history", ("document_id",), "list", columns=HISTORY),
    Child("newsletters", "history", "newsletter_history", ("newsletter_id",), "list", columns=HISTORY),
    Child("alerts", "history", "alert_history", ("alert_id",), "list", columns=HISTORY),
    Child("application_runs", "history", "application_run_history", ("run_id",), "list", columns=HISTORY),
    Child("news_items", "history", "news_item_history", ("news_id",), "list", columns=HISTORY),
    Child("news_items", "factors", "news_item_factors", ("news_id",), "values", column="factor"),
    Child("events", "news_ids", "event_news", ("event_id",), "values", column="news_id"),
    Child("events", "factors", "event_factors", ("event_id",), "values", column="factor"),
    Child("newsletters", "view_ids", "newsletter_views", ("newsletter_id",), "values", column="view_id"),
    Child("run_snapshots", "families", "run_snapshot_families", ("snapshot_id",), "map", column="family_id"),
    Child(
        "application_runs", "ranking", "application_run_ranking", ("run_id",), "list", columns=(("family_id", "text"),)
    ),
    Child("family_impacts", "holdings", "family_impact_holdings", ("impact_id",), "list"),
    Child("client_sources", "transactions", "client_transactions", ("client_id", "source"), "list"),
]

WHOLE = {t: set(cols) for t, _, cols, _ in crypto.COLUMNS}  # columns a client value is sealed in whole
FIELDS = {t: set(fs) for t, _, fs in crypto.FIELDS}  # fields of data sealed one by one


class ExportError(RuntimeError):
    pass


def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


# -- the source schema -------------------------------------------------------------------------


@dataclass
class Table:
    name: str
    columns: List[Tuple[str, str, bool, Optional[str]]]  # name, declared type, not null, default
    pk: Tuple[str, ...]
    identity: bool
    uniques: List[Tuple[str, ...]]
    indexes: List[str]

    def pg_type(self, col: str, declared: str) -> str:
        if col == "data" and (self.name, col) not in SIGNED_TEXT:
            return "text" if col in WHOLE.get(self.name, ()) else "jsonb"
        return TYPES.get(declared.lower(), "text")

    def json_column(self) -> bool:
        return any(c[0] == "data" for c in self.columns)


def tables(con: sqlite3.Connection) -> List[Table]:
    out = []
    for name, sql in con.execute(
        "select name, sql from sqlite_master where type = 'table' and name not like 'sqlite_%' order by name"
    ).fetchall():
        info = con.execute(f"pragma table_info({q(name)})").fetchall()
        cols = [(r[1], r[2] or "", bool(r[3]), r[4]) for r in info]
        pk = tuple(r[1] for r in sorted((r for r in info if r[5]), key=lambda r: r[5]))
        uniques, indexes = [], []
        for il in con.execute(f"pragma index_list({q(name)})").fetchall():
            idx, unique, origin = il[1], il[2], il[3]
            if origin == "u" and unique:
                uniques.append(tuple(r[2] for r in con.execute(f"pragma index_info({q(idx)})")))
            elif origin == "c":
                cols_i = [r[2] for r in con.execute(f"pragma index_info({q(idx)})")]
                indexes.append(
                    f"create {'unique ' if unique else ''}index {q(idx)} on {q(name)} ({', '.join(map(q, cols_i))})"
                )
        out.append(Table(name, cols, pk, "autoincrement" in (sql or "").lower(), uniques, indexes))
    return out


def ddl(con: sqlite3.Connection) -> List[str]:
    """The PostgreSQL schema: every table, the split columns, the child tables and their indexes."""
    have = {t.name: t for t in tables(con)}
    out = []
    for t in have.values():
        lines = []
        for col, declared, notnull, default in t.columns:
            typ = t.pg_type(col, declared)
            if t.identity and t.pk == (col,):
                lines.append(f"{q(col)} bigint generated by default as identity")
                continue
            line = f"{q(col)} {typ}" + (" not null" if notnull else "")
            if default is not None:
                line += f" default {default}"
            lines.append(line)
        for f in FIELD_COLUMNS:
            if f.table == t.name:
                lines.append(f"{q(f.field)} {f.type}")
        lines.append(f"primary key ({', '.join(map(q, t.pk))})")
        lines += [f"unique ({', '.join(map(q, u))})" for u in t.uniques]
        out.append(f"create table {q(t.name)} (\n  " + ",\n  ".join(lines) + "\n)")
        out += t.indexes
    for f in FIELD_COLUMNS:
        if f.table in have:
            out.append(f"create index {q(f.table + '_' + f.field)} on {q(f.table)} ({q(f.field)})")
    for c in CHILDREN:
        if c.table not in have:
            continue
        parent = have[c.table]
        ptypes = {col: parent.pg_type(col, d) for col, d, _, _ in parent.columns}
        lines = [f"{q(n)} {ptypes[p]} not null" for n, p in zip(c.parent, parent.pk)]
        key = "pos" if c.shape in ("list", "values") else c.column
        lines.append(f"{q('pos')} integer not null" if key == "pos" else f"{q(key)} text not null")
        if c.shape == "values":
            lines.append(f"{q(c.column)} text not null")
        lines += [f"{q(n)} {typ}" for n, typ in c.columns]
        if c.shape != "values":
            lines.append(f"{q('data')} {'text' if sealed_child(c) else 'jsonb'} not null")
        lines.append(f"primary key ({', '.join(map(q, (*c.parent, key)))})")
        lines.append(
            f"foreign key ({', '.join(map(q, c.parent))}) references {q(c.table)} ({', '.join(map(q, parent.pk))})"
            " on delete cascade"
        )
        out.append(f"create table {q(c.name)} (\n  " + ",\n  ".join(lines) + "\n)")
        for n, _ in c.columns:
            out.append(f"create index {q(c.name + '_' + n)} on {q(c.name)} ({q(n)})")
        if c.shape == "values":
            out.append(f"create index {q(c.name + '_' + c.column)} on {q(c.name)} ({q(c.column)})")
    return out


def sealed_child(c: Child) -> bool:
    """A child whose source may be sealed: its data is sealed too (so stored as text)."""
    return "data" in WHOLE.get(c.table, ()) or c.field in FIELDS.get(c.table, ())


# -- rows ------------------------------------------------------------------------------------


def _fits(value: Any, typ: str) -> bool:
    if typ == "double precision":
        return isinstance(value, float)
    if typ == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, str)


def _rid(pk_values: Tuple[Any, ...]) -> Any:
    return pk_values if len(pk_values) > 1 else pk_values[0]


def _dumps(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, allow_nan=False)


def split(t: Table, row: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
    """One SQLite row as its PostgreSQL row and child rows. Values not split are copied as stored."""
    children = [c for c in CHILDREN if c.table == t.name]
    fields = [f for f in FIELD_COLUMNS if f.table == t.name]
    out = dict(row)
    kids: Dict[str, List[Dict[str, Any]]] = {c.name: [] for c in children}
    if "data" not in row or (not children and not fields) or row["data"] is None:
        return out, kids
    pk = tuple(row[c] for c in t.pk)
    raw = row["data"]
    whole = crypto.sealed(raw)
    if whole and not crypto.on():
        raise ExportError(f"{t.name}: dữ liệu đã mã hóa, cần MF_DATA_KEYS để tách bảng")
    data = json.loads(crypto.open_(raw, crypto.where(t.name, _rid(pk), "data")) if whole else raw)
    changed = False
    if isinstance(data, dict):
        for f in fields:
            if f.field in data and _fits(data[f.field], f.type):
                out[f.field] = data.pop(f.field)
                changed = True
        for c in children:
            v = data.get(c.field)
            field_sealed = crypto.sealed(v)
            if field_sealed:
                if not crypto.on():
                    raise ExportError(f"{t.name}.{c.field}: dữ liệu đã mã hóa, cần MF_DATA_KEYS để tách bảng")
                v = crypto.open_json(v, crypto.where(t.name, _rid(pk), c.field))
            rows = _items(c, pk, v, whole or field_sealed)
            if rows:
                del data[c.field]
                kids[c.name] = rows
                changed = True
    if changed:
        text = _dumps(data)
        out["data"] = crypto.seal(text, crypto.where(t.name, _rid(pk), "data")) if whole else text
    return out, kids


def _items(c: Child, pk: Tuple[Any, ...], v: Any, sealed: bool) -> List[Dict[str, Any]]:
    base = dict(zip(c.parent, pk))
    rows = []
    if c.shape == "values":
        if not (isinstance(v, list) and v and all(isinstance(x, str) for x in v)):
            return []
        return [{**base, "pos": i, c.column: x} for i, x in enumerate(v)]
    if c.shape == "map":
        if not (isinstance(v, dict) and v):
            return []
        pairs = list(v.items())
    else:
        if not (isinstance(v, list) and v and all(isinstance(x, dict) for x in v)):
            return []
        pairs = list(enumerate(v))
    for k, item in pairs:
        r = {**base, ("pos" if c.shape == "list" else c.column): k}
        rest = dict(item) if c.shape == "list" else item
        for n, typ in c.columns:
            if n in rest and _fits(rest[n], typ):
                r[n] = rest.pop(n)
        text = _dumps(rest)
        r["data"] = crypto.seal(text, crypto.where(c.name, (*pk, k), "data")) if sealed else text
        rows.append(r)
    return rows


def rebuild(t: Table, row: Dict[str, Any], kids: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """A PostgreSQL row and its child rows put back as the SQLite row, every sealed value opened (``logical``)."""
    out = {c[0]: row.get(c[0]) for c in t.columns}
    pk = tuple(row[c] for c in t.pk)
    data = out.get("data")
    if "data" in out and data is not None:
        if isinstance(data, str):
            data = json.loads(crypto.open_(data, crypto.where(t.name, _rid(pk), "data")))
        if isinstance(data, dict):
            for f in FIELD_COLUMNS:
                if f.table == t.name and row.get(f.field) is not None:
                    data[f.field] = row[f.field]
            for c in CHILDREN:
                if c.table == t.name and kids.get(c.name):
                    data[c.field] = _unsplit(c, pk, kids[c.name])
        out["data"] = data
    return logical(t, out)


def _unsplit(c: Child, pk: Tuple[Any, ...], rows: List[Dict[str, Any]]) -> Any:
    if c.shape == "values":
        return [r[c.column] for r in sorted(rows, key=lambda r: r["pos"])]
    key = "pos" if c.shape == "list" else c.column
    items = {}
    for r in rows:
        d = r["data"]
        if isinstance(d, str):
            d = json.loads(crypto.open_(d, crypto.where(c.name, (*pk, r[key]), "data")))
        if c.shape == "list":
            d = {**d, **{n: r[n] for n, _ in c.columns if r.get(n) is not None}}
        items[r[key]] = d
    if c.shape == "map":
        return items
    return [items[k] for k in sorted(items)]


def logical(t: Table, row: Dict[str, Any]) -> Dict[str, Any]:
    """A row with every sealed value opened and ``data`` parsed: what SQLite and PostgreSQL must agree on."""
    out = dict(row)
    pk = tuple(row[c] for c in t.pk)
    for col in WHOLE.get(t.name, ()):
        if col != "data" and isinstance(out.get(col), str):
            out[col] = crypto.open_(out[col], crypto.where(t.name, _rid(pk), col))
    if "data" in out and (t.name, "data") not in SIGNED_TEXT and out["data"] is not None:
        d = out["data"]
        if isinstance(d, str):
            d = json.loads(crypto.open_(d, crypto.where(t.name, _rid(pk), "data")))
        if isinstance(d, dict):
            for f in FIELDS.get(t.name, ()):
                if f in d:
                    d = {**d, f: crypto.open_json(d[f], crypto.where(t.name, _rid(pk), f))}
        out["data"] = d
    return out


def rows(con: sqlite3.Connection, t: Table) -> Iterator[Dict[str, Any]]:
    cols = [c[0] for c in t.columns]
    for r in con.execute(f"select {', '.join(map(q, cols))} from {q(t.name)} order by {', '.join(map(q, t.pk))}"):
        yield dict(zip(cols, r))


# -- the load file ---------------------------------------------------------------------------


def _copy_value(v: Any) -> str:
    if v is None:
        return "\\N"
    if isinstance(v, bool):
        v = int(v)
    if isinstance(v, float):
        v = repr(v)
    s = str(v)
    if "\x00" in s:
        raise ExportError("PostgreSQL text cannot hold a NUL character")
    return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def _copy(name: str, cols: List[str], values: Iterable[Tuple[Any, ...]]) -> Iterator[str]:
    yield f"copy {q(name)} ({', '.join(map(q, cols))}) from stdin;\n"
    for v in values:
        yield "\t".join(_copy_value(x) for x in v) + "\n"
    yield "\\.\n"


def script(con: sqlite3.Connection) -> Iterator[str]:
    """The whole load as one psql script: the schema, then every table by ``COPY``, then the identity counters."""
    yield "\\set ON_ERROR_STOP on\nbegin;\n"
    for stmt in ddl(con):
        yield stmt + ";\n"
    for t in tables(con):
        extra = [f.field for f in FIELD_COLUMNS if f.table == t.name]
        cols = [c[0] for c in t.columns] + extra
        children = [c for c in CHILDREN if c.table == t.name]
        kid_rows: Dict[str, List[Dict[str, Any]]] = {c.name: [] for c in children}
        parents = []
        for r in rows(con, t):
            p, kids = split(t, r)
            parents.append(tuple(p.get(c) for c in cols))
            for name, rs in kids.items():
                kid_rows[name] += rs
        yield from _copy(t.name, cols, parents)
        for c in children:
            kcols = child_columns(c)
            yield from _copy(c.name, kcols, (tuple(r.get(k) for k in kcols) for r in kid_rows[c.name]))
        if t.identity:
            (pk,) = t.pk
            yield (
                f"select setval(pg_get_serial_sequence('{q(t.name)}', '{pk}'), "
                f"coalesce((select max({q(pk)}) from {q(t.name)}), 0) + 1, false);\n"
            )
    yield "commit;\n"


def child_columns(c: Child) -> List[str]:
    key = ["pos"] if c.shape in ("list", "values") else [c.column]
    body = [c.column] if c.shape == "values" else [n for n, _ in c.columns] + ["data"]
    return [*c.parent, *key, *body]


# -- the check -------------------------------------------------------------------------------


def expected(con: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    """What PostgreSQL must hold, from SQLite: rows per table (children included), sums of the number columns, and
    every row opened (``logical``) by primary key."""
    out: Dict[str, Dict[str, Any]] = {}
    for t in tables(con):
        nums = [c[0] for c in t.columns if TYPES.get(c[1].lower()) in ("bigint", "double precision")]
        entry = {"rows": 0, "sums": {n: 0 for n in nums}, "logical": {}}
        kids = {c.name: 0 for c in CHILDREN if c.table == t.name}
        for r in rows(con, t):
            entry["rows"] += 1
            for n in nums:
                entry["sums"][n] += r[n] or 0
            entry["logical"][tuple(r[c] for c in t.pk)] = logical(t, r)
            for name, rs in split(t, r)[1].items():
                kids[name] += len(rs)
        out[t.name] = entry
        for name, n in kids.items():
            out[name] = {"rows": n}
    return out


def compare(con: sqlite3.Connection, read) -> Dict[str, Any]:
    """Check PostgreSQL against SQLite. ``read(sql)`` runs one query on PostgreSQL and returns the rows as dicts.
    Counts and sums by SQL there, then every row read back, rebuilt and compared with SQLite."""
    want = expected(con)
    report: Dict[str, Any] = {"tables": {}, "ok": True}
    for t in tables(con):
        w = want[t.name]
        sums = ", ".join(f"coalesce(sum({q(n)}), 0) as {q(n)}" for n in w["sums"])
        got = read(f"select count(*) as n{', ' + sums if sums else ''} from {q(t.name)}")[0]
        sums_ok = all(abs((got[n] or 0) - v) <= 1e-9 * max(1.0, abs(v)) for n, v in w["sums"].items())
        kids_by: Dict[str, Dict[Tuple, List[Dict[str, Any]]]] = {}
        entry = {"sqlite": w["rows"], "postgres": got["n"], "sums": sums_ok, "children": {}}
        for c in CHILDREN:
            if c.table != t.name:
                continue
            krows = read(f"select row_to_json(x) as r from {q(c.name)} x")
            entry["children"][c.name] = {"expected": want[c.name]["rows"], "postgres": len(krows)}
            grouped: Dict[Tuple, List[Dict[str, Any]]] = {}
            for k in krows:
                k = k["r"]
                grouped.setdefault(tuple(k[p] for p in c.parent), []).append(k)
            kids_by[c.name] = grouped
        mismatched = []
        back = read(f"select row_to_json(x) as r from {q(t.name)} x")
        seen = set()
        for b in back:
            b = b["r"]
            pk = tuple(b[c] for c in t.pk)
            seen.add(pk)
            kids = {name: g.get(pk, []) for name, g in kids_by.items()}
            if rebuild(t, b, kids) != w["logical"].get(pk):
                mismatched.append(pk)
        missing = [pk for pk in w["logical"] if pk not in seen]
        entry["mismatched"] = [list(m) for m in mismatched[:5]]
        entry["missing"] = len(missing)
        entry["ok"] = (
            w["rows"] == got["n"]
            and sums_ok
            and not mismatched
            and not missing
            and all(v["expected"] == v["postgres"] for v in entry["children"].values())
        )
        report["ok"] &= entry["ok"]
        report["tables"][t.name] = entry
    return report
