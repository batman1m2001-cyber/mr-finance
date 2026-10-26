"""The data room (docs/ASSISTANT_DATA_PLAN.md §3.1–3.2, ADR-0040): the assistant's ``truy_van`` tool writes one SQL
``select`` over tables made for the person asking, and nothing else.

How the room is built, per call:

- one connection to ``state.db``, opened ``mode=ro``;
- for each room table the SQL names (and the role may have), a TEMP table holding exactly the rows and columns that
  role and person may see. Tables of family data (holdings, transactions, goals, families, contacts, reviews, family
  impacts) are filled from the same served reads the pages use, which open sealed columns and apply
  ``people.auth`` (``desk.reads.book_of``, ``auth.client_for``, ``auth.visible``). The others are copied from the real
  table with the role's filter (held news left out, the audit log without payloads or hashes);
- then ``PRAGMA query_only``, the limits, a progress handler and the authorizer, and only then the model's SQL.

Why copies and not TEMP views over the real tables (the plan's first design): SQLite tells the authorizer which view
a read comes from by *name*, and a CTE named like a view gets that name too. ``with tin as (select email from
main.people) select * from tin`` reached the authorizer as a read of ``people.email`` "inside" ``tin``
(2026-10-24, tests/test_dataroom.py). With copies the rule needs no name: the query may read the TEMP tables built
for it and no table of ``main`` at all. Building them takes about 30 ms for 1,481 news items.

The authorizer allows ``SELECT``, reads of those TEMP tables, and the functions in :data:`FUNCTIONS`; everything else
is denied (any real table, ``ATTACH``, ``PRAGMA`` and the ``pragma_*`` tables, writes, ``load_extension``,
recursive CTEs, ``sqlite_master``). A query stops after :data:`SECONDS`; it returns at most :data:`ROWS` rows and
always the total.
"""

from __future__ import annotations

import asyncio
import re
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Tuple

from assistant.base import Ctx, Param, Tool, ToolFailed

ROWS = 200  # rows returned; the total is counted past it
SECONDS = 2.0  # a query (and its count) stops after this
CELL = 300  # characters of one text cell returned
SQL_CHARS = 4000  # the longest SQL accepted
VN = timezone(timedelta(hours=7))
ROLES = ("cio", "rm", "client", "admin")

# the functions a query may call (SQLite's authorizer sees each by name); no printf/format (width), randomblob or
# zeroblob (memory), load_extension, sqlite_* (the build), and no table-valued function (json_each reads a "table")
FUNCTIONS = frozenset(
    """count sum total avg min max group_concat
    date time datetime julianday strftime unixepoch
    lower upper length substr substring instr trim ltrim rtrim replace like glob
    coalesce ifnull nullif iif abs round cast
    json_extract json_array_length
    row_number rank dense_rank lag lead first_value last_value ntile percent_rank cume_dist
    khong_dau""".split()
)


class Refused(ToolFailed):
    """The query was not run, or was stopped: said to the model as a failed step, never as an answer."""


@dataclass
class Who:
    """Whose room: the role and, for family data, the families (an RM's book, a client's own)."""

    ctx: Ctx
    role: str
    families: List[str] = field(default_factory=list)  # rm: the book; client: their family's head
    client_id: Optional[str] = None  # client: the person (their household by ctx.scope)


Loader = Callable[[Who], Awaitable[List[Sequence[Any]]]]


@dataclass
class Table:
    """One table of the room: its columns (name, SQLite type), the roles that have it, and how it is filled — a copy
    from the real tables (``copy``: SQL, or a function of the person giving SQL and its arguments) or rows from
    Python (``load``)."""

    name: str
    roles: Tuple[str, ...]
    columns: List[Tuple[str, str]]
    copy: Any = None
    load: Optional[Loader] = None

    def sql(self, who: Who) -> Tuple[str, Sequence[Any]]:
        got = self.copy(who) if callable(self.copy) else (self.copy, ())
        return got


def _vn_day(col: str) -> str:
    return f"date({col}, 'unixepoch', '+7 hours')"


def _vn_hour(col: str) -> str:
    return f"strftime('%H:%M', {col}, 'unixepoch', '+7 hours')"


def _j(path: str, col: str = "data") -> str:
    return f"json_extract({col}, '$.{path}')"


NEWS_COLUMNS = [
    ("ma", "TEXT"), ("tieu_de", "TEXT"), ("tom_tat", "TEXT"), ("nguon", "TEXT"), ("bao", "TEXT"),
    ("chuyen_muc", "TEXT"), ("loai", "TEXT"), ("trang_thai", "TEXT"), ("muc_lien_quan", "TEXT"),
    ("loai_su_kien", "TEXT"), ("diem", "REAL"), ("luc_dang", "REAL"), ("ngay_dang", "TEXT"), ("luc_lay", "REAL"),
    ("ngay_lay", "TEXT"), ("gio_lay", "TEXT"), ("url", "TEXT"),
]  # fmt: skip
NEWS_SELECT = (
    f"select id, {_j('title')}, {_j('summary')}, source, {_j('outlet')}, {_j('section')}, kind, status, relevance, "
    f"event_type, {_j('score')}, published, {_vn_day('published')}, ingested, {_vn_day('ingested')}, "
    f"{_vn_hour('ingested')}, {_j('url')}"
)
HELD_NEWS = (
    "exists (select 1 from main.news_items n, json_each(e.data, '$.news_ids') j where n.id = j.value and n.held = 1)"
)


def _events(who: Who) -> Tuple[str, Sequence[Any]]:
    # a held event's title is a held news title: no CIO has released it, so only the CIO (whose pages show it
    # blocked) has it; an RM or a client has the events that are not held
    keep = "" if who.role == "cio" else f" where not {HELD_NEWS}"
    return (
        f"select e.id, {_j('title', 'e.data')}, {_j('type', 'e.data')}, e.status, "
        f"coalesce({_j('urgent.flag', 'e.data')}, 0), {_j('created_by', 'e.data')}, e.created, {_vn_day('e.created')}, "
        f"coalesce(json_array_length(e.data, '$.news_ids'), 0), {HELD_NEWS} from main.events e{keep}",
        (),
    )


def _alerts(who: Who) -> Tuple[str, Sequence[Any]]:
    from control.alerts import KINDS

    kinds = sorted(k for k, v in KINDS.items() if who.role == "admin" or who.role in v["roles"])
    marks = ",".join("?" * len(kinds)) or "null"
    return (
        f"select id, kind, key, status, {_j('severity')}, {_j('title')}, {_j('detail')}, {_j('count')}, created, "
        f"{_vn_day('created')}, {_j('last_at')} from main.alerts where kind in ({marks})",
        kinds,
    )


# -- rows from the served reads (family data: sealed columns opened, people.auth applied) ------------------------


async def _consolidated(who: Who) -> List[Tuple[str, Dict[str, Any]]]:
    """(family, consolidate_flow's output) for each family of the room: a client's by their scope, an RM's whole
    households."""
    from assistant.base import run_graph
    from consolidate.graph import consolidate_flow

    if who.role == "client":
        pairs = [(who.families[0], who.client_id, who.ctx.scope)]
    else:
        pairs = [(f, f, "family") for f in who.families]
    outs = await asyncio.gather(*(run_graph(consolidate_flow, client_id=c, scope=s) for _, c, s in pairs))
    return [(f, o) for (f, _, _), o in zip(pairs, outs)]


async def _holdings(who: Who) -> List[Sequence[Any]]:
    rows = []
    for fam, out in await _consolidated(who):
        for h in out["holdings"]:
            rows.append((fam, h["key"], h.get("owner_name"), h["source"], h["kind"], h["class"], h["name"], h["value"],
                         h.get("prev_value"), h.get("cost"), int(bool(h.get("liquid"))), h.get("stress"),
                         h.get("trust")))  # fmt: skip
    return rows


async def _transactions(who: Who) -> List[Sequence[Any]]:
    from flows.ops import LABELS

    rows = []
    for _, out in await _consolidated(who):
        names = {m["id"]: m["name"] for m in out["members"]}
        for t in out["transactions"]:
            c = t.get("category") or "other"
            rows.append((t["date"], t["date"][:7], t["amount"], t["direction"], t["desc"], c, LABELS.get(c, c),
                         names.get(t.get("owner"), "")))  # fmt: skip
    return rows


async def _goals(who: Who) -> List[Sequence[Any]]:
    from assistant.base import run_graph
    from scenarios.graph import goals_flow

    out = (await run_graph(goals_flow, client_id=who.client_id, scope=who.ctx.scope))["goals"]
    followed = who.ctx.followed
    rows = []
    for g in out:
        x = g["goal"]
        on = g["id"] in followed if followed is not None else bool(g.get("followed"))
        rows.append((g["id"], g["title"], g.get("stage_label"), int(on), x.get("need"), x.get("have"), x.get("gap"),
                     x.get("monthly"), x.get("surplus"), x.get("by"), x.get("status"), x.get("progress")))  # fmt: skip
    return rows


async def _families(who: Who) -> List[Sequence[Any]]:
    from people import store

    rows = []
    for f in who.families:
        c = store.client(f)
        rows.append((f, c.get("name"), c.get("age"), c.get("occupation"), c.get("segment"), c.get("city"),
                     1 + len(c.get("household") or []), c.get("income_monthly"), c.get("spending_monthly"),
                     c.get("drawdown_limit")))  # fmt: skip
    return rows


async def _contacts(who: Who) -> List[Sequence[Any]]:
    from contacts import store as contacts

    out = contacts.recent(families=who.families, limit=1_000_000)
    return [
        (c["id"], c["family_id"], c["at"], _day(c["at"]), c["by"], c.get("channel_label"), int(c["from_signal"]),
         c.get("note"))
        for c in out
    ]  # fmt: skip


async def _reviews(who: Who) -> List[Sequence[Any]]:
    from people import store
    from wealth import store as wealth_store

    book = set(who.families)
    heads = {c: store.client(c).get("member_of") or c for c in store.client_ids(True)}
    return [
        (r["id"], r["client_id"], heads.get(r["client_id"], r["client_id"]), r["kind"], r["title"], r["status"],
         r.get("note"), r["created"], _day(r["created"]), r.get("decided"))
        for r in wealth_store.reviews()
        if heads.get(r["client_id"], r["client_id"]) in book
    ]  # fmt: skip


async def _impacts(who: Who) -> List[Sequence[Any]]:
    """One row per application run and family: the family's totals, never its holdings (§3.1 "aggregates only")."""
    from apply import run as apply_run
    from people import auth

    rows = []
    for r in apply_run.runs():
        results = apply_run.family_results(r["id"])
        for fam in auth.visible(sorted(results)):
            x = results[fam]
            h = x.get("horizons") or {}

            def exp(k, key="expected", h=h):
                return (h.get(k) or {}).get(key)

            rows.append((r["id"], r["event_id"], r["status"], fam, x.get("name"), x.get("assets"), x.get("net_worth"),
                         exp("1w"), exp("3m"), exp("12m"), ((x.get("pct") or {}).get("3m") or {}).get("expected"),
                         exp("3m", "p10"), int(bool(x.get("pre_review")))))  # fmt: skip
    return rows


def _day(epoch: Optional[float]) -> Optional[str]:
    return None if epoch is None else datetime.fromtimestamp(float(epoch), VN).strftime("%Y-%m-%d")


TABLES: Dict[str, Table] = {
    t.name: t
    for t in [
        Table("tin", ("cio", "rm", "client"), NEWS_COLUMNS,
              f"{NEWS_SELECT} from main.news_items where status != 'refused' and held = 0"),
        Table("tin_bi_giu", ("cio", "admin"), NEWS_COLUMNS + [("cong_ty_han_che", "TEXT")],
              f"{NEWS_SELECT}, (select group_concat(value, ', ') from json_each(data, '$.restricted')) "
              "from main.news_items where status != 'refused' and held = 1"),
        Table("su_kien", ("cio", "rm", "client"),
              [("ma", "TEXT"), ("tieu_de", "TEXT"), ("loai", "TEXT"), ("trang_thai", "TEXT"), ("khan", "INTEGER"),
               ("nguoi_lap", "TEXT"), ("luc_lap", "REAL"), ("ngay_lap", "TEXT"), ("so_tin", "INTEGER"),
               ("bi_giu", "INTEGER")], _events),
        Table("nhan_dinh", ("cio",),
              [("ma", "TEXT"), ("ma_su_kien", "TEXT"), ("phien_ban", "INTEGER"), ("trang_thai", "TEXT"),
               ("nguoi_lap", "TEXT"), ("che_do", "TEXT"), ("luc_lap", "REAL"), ("ngay_lap", "TEXT"),
               ("tom_tat", "TEXT"), ("so_tac_dong", "INTEGER")],
              f"select id, event_id, version, status, {_j('created_by')}, {_j('mode')}, created, {_vn_day('created')}, "
              f"{_j('current.summary')}, coalesce(json_array_length(data, '$.current.impacts'), 0) from main.views"),
        Table("de_xuat", ("cio",),
              [("ma", "TEXT"), ("ma_nhan_dinh", "TEXT"), ("ma_su_kien", "TEXT"), ("trang_thai", "TEXT"),
               ("nguoi_lap", "TEXT"), ("ma_quyet_dinh", "TEXT"), ("ngay_gia", "TEXT"), ("so_gia_dinh", "INTEGER"),
               ("ky_vong_3thang", "REAL"), ("so_cham_nguong", "INTEGER"), ("so_muc_tieu_doi", "INTEGER"),
               ("luc_lap", "REAL"), ("ngay_lap", "TEXT")],
              f"select id, view_id, event_id, status, {_j('by')}, {_j('decision_id')}, {_j('price_date')}, "
              f"{_j('families')}, {_j('totals.expected_3m')}, {_j('totals.pre_review')}, {_j('totals.goals_changed')}, "
              f"created, {_vn_day('created')} from main.application_runs"),
        Table("tac_dong_gia_dinh", ("cio",),
              [("ma_lan_ap_dung", "TEXT"), ("ma_su_kien", "TEXT"), ("trang_thai_lan", "TEXT"),
               ("ma_gia_dinh", "TEXT"), ("ten_gia_dinh", "TEXT"), ("tong_tai_san", "REAL"), ("tai_san_rong", "REAL"),
               ("ky_vong_1tuan", "REAL"), ("ky_vong_3thang", "REAL"), ("ky_vong_12thang", "REAL"),
               ("ty_le_3thang", "REAL"), ("p10_3thang", "REAL"), ("cham_nguong", "INTEGER")], load=_impacts),
        Table("du_bao", ("cio",),
              [("ma", "TEXT"), ("ma_nhan_dinh", "TEXT"), ("ma_su_kien", "TEXT"), ("yeu_to", "TEXT"),
               ("ky_han", "TEXT"), ("ngay_goc", "TEXT"), ("ngay_den_han", "TEXT"), ("ky_vong", "REAL"),
               ("p10", "REAL"), ("p50", "REAL"), ("p90", "REAL"), ("don_vi", "TEXT"), ("mo_hinh", "TEXT"),
               ("da_cham", "INTEGER"), ("ket_qua", "TEXT"), ("thuc_te", "REAL"), ("trong_khoang", "INTEGER"),
               ("dung_huong", "INTEGER")],
              f"select id, view_id, {_j('event_id')}, factor, horizon, origin, due, {_j('expected')}, {_j('p10')}, "
              f"{_j('p50')}, {_j('p90')}, {_j('unit')}, {_j('model')}, scored is not null, {_j('result')}, "
              f"{_j('realised')}, {_j('inside')}, {_j('direction_hit')} from main.forecasts"),
        Table("viec_nen", ("cio", "admin"),
              [("ma", "TEXT"), ("viec", "TEXT"), ("trang_thai", "TEXT"), ("nguoi_chay", "TEXT"),
               ("luc_bat_dau", "REAL"), ("ngay", "TEXT"), ("so_giay", "REAL"), ("loi", "TEXT")],
              f"select id, job, status, {_j('by')}, created, {_vn_day('created')}, {_j('seconds')}, {_j('error')} "
              "from main.job_runs"),
        Table("nguon_du_lieu", ("cio",),
              [("ma", "INTEGER"), ("viec", "TEXT"), ("chuoi", "TEXT"), ("nguon", "TEXT"), ("luc_bat_dau", "REAL"),
               ("ngay", "TEXT"), ("so_diem", "INTEGER"), ("loi", "TEXT")],
              f"select id, job, series, source, started, {_vn_day('started')}, points, error from main.source_runs"),
        Table("gia_dinh", ("rm",),
              [("ma_gia_dinh", "TEXT"), ("ten", "TEXT"), ("tuoi", "INTEGER"), ("nghe_nghiep", "TEXT"),
               ("phan_khuc", "TEXT"), ("thanh_pho", "TEXT"), ("so_thanh_vien", "INTEGER"),
               ("thu_nhap_thang", "REAL"), ("chi_tieu_thang", "REAL"), ("nguong_sut_giam", "REAL")],
              load=_families),
        Table("tai_san", ("rm", "client"),
              [("ma_gia_dinh", "TEXT"), ("ma_khoan", "TEXT"), ("chu_so_huu", "TEXT"), ("nguon", "TEXT"),
               ("loai", "TEXT"), ("lop", "TEXT"), ("ten", "TEXT"), ("gia_tri", "REAL"),
               ("gia_tri_thang_truoc", "REAL"), ("gia_von", "REAL"), ("thanh_khoan", "INTEGER"), ("muc_soc", "REAL"),
               ("do_tin_cay", "TEXT")], load=_holdings),
        Table("lien_he", ("rm",),
              [("ma", "TEXT"), ("ma_gia_dinh", "TEXT"), ("luc", "REAL"), ("ngay", "TEXT"), ("nguoi", "TEXT"),
               ("kenh", "TEXT"), ("tu_tin_hieu", "INTEGER"), ("ghi_chu", "TEXT")], load=_contacts),
        Table("duyet", ("rm",),
              [("ma", "TEXT"), ("ma_khach_hang", "TEXT"), ("ma_gia_dinh", "TEXT"), ("loai", "TEXT"),
               ("tieu_de", "TEXT"), ("trang_thai", "TEXT"), ("ghi_chu", "TEXT"), ("luc_lap", "REAL"),
               ("ngay_lap", "TEXT"), ("luc_quyet_dinh", "REAL")], load=_reviews),
        Table("dong_tien", ("client",),
              [("ngay", "TEXT"), ("thang", "TEXT"), ("so_tien", "REAL"), ("chieu", "TEXT"), ("mo_ta", "TEXT"),
               ("nhom", "TEXT"), ("ten_nhom", "TEXT"), ("chu_tai_khoan", "TEXT")], load=_transactions),
        Table("muc_tieu", ("client",),
              [("ma", "TEXT"), ("ten", "TEXT"), ("giai_doan", "TEXT"), ("dang_theo_doi", "INTEGER"), ("can", "REAL"),
               ("co", "REAL"), ("thieu", "REAL"), ("can_de_danh_thang", "REAL"), ("du_thang", "REAL"),
               ("han", "TEXT"), ("trang_thai", "TEXT"), ("tien_do", "REAL")], load=_goals),
        Table("nhat_ky", ("cio", "admin"),
              [("so_thu_tu", "INTEGER"), ("luc", "REAL"), ("ngay", "TEXT"), ("gio", "TEXT"), ("nguoi", "TEXT"),
               ("hanh_dong", "TEXT"), ("doi_tuong", "TEXT")],
              f"select seq, ts, {_vn_day('ts')}, {_vn_hour('ts')}, actor, action, object from main.audit_log"),
        Table("canh_bao", ("cio", "admin"),
              [("ma", "TEXT"), ("loai", "TEXT"), ("khoa", "TEXT"), ("trang_thai", "TEXT"), ("muc_do", "TEXT"),
               ("tieu_de", "TEXT"), ("chi_tiet", "TEXT"), ("so_lan", "INTEGER"), ("luc_tao", "REAL"),
               ("ngay_tao", "TEXT"), ("luc_gan_nhat", "REAL")], _alerts),
    ]
}  # fmt: skip


def tables_for(role: str) -> List[Table]:
    return [t for t in TABLES.values() if role in t.roles]


# -- who, and which tables a query names ---------------------------------------------------------------------------


def who_for(ctx: Ctx) -> Who:
    """The room's person: an RM's book (``desk.reads.book_of``), a client's own family (``auth.client_for``: a
    customer is always themselves); staff roles hold no family list (their family rows go through ``auth.visible``)."""
    if ctx.role not in ROLES:
        raise Refused("Vai trò này không truy vấn dữ liệu")
    if ctx.role == "rm":
        from desk.reads import book_of
        from people import auth

        return Who(ctx, "rm", families=book_of(auth.signed_in() or {"id": ctx.user, "role": "rm"}))  # as Hôm nay
    if ctx.role == "client":
        from people import auth
        from wealth import fixtures

        cid = auth.client_for(ctx.client_id)
        if not cid:
            raise Refused("Chưa chọn khách hàng")
        head = fixtures.client(cid).get("member_of") or cid
        return Who(ctx, "client", families=[head], client_id=cid)
    return Who(ctx, ctx.role)


WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
START = re.compile(r"^\s*(select|with)\b", re.I)
RECURSIVE = re.compile(r"\bwith\s+recursive\b", re.I)


def named(sql: str, role: str) -> List[Table]:
    words = {w.lower() for w in WORD.findall(sql)}
    return [t for t in tables_for(role) if t.name in words]


def _clean(sql: str) -> str:
    s = (sql or "").strip()
    while s.endswith(";"):
        s = s[:-1].rstrip()
    if not s:
        raise Refused("Thiếu câu lệnh SQL")
    if len(s) > SQL_CHARS:
        raise Refused(f"Câu lệnh dài quá {SQL_CHARS} ký tự")
    if not START.match(s):
        raise Refused("Chỉ được đọc: câu lệnh bắt đầu bằng SELECT hoặc WITH")
    if not sqlite3.complete_statement(s + "\n;") or _many(s):
        raise Refused("Mỗi lần chỉ một câu lệnh SELECT")
    if RECURSIVE.search(s):  # the reason; the authorizer refuses a recursive CTE with or without the word
        raise Refused("Không dùng CTE đệ quy (WITH RECURSIVE)")
    return s


def _many(s: str) -> bool:
    """A ``;`` outside quotes and comments: a second statement."""
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in "'\"`[":
            end = "]" if c == "[" else c
            j = s.find(end, i + 1)
            while j != -1 and end != "]" and j + 1 < n and s[j + 1] == end:  # '' inside a string
                j = s.find(end, j + 2)
            i = n if j == -1 else j + 1
            continue
        if s.startswith("--", i):
            j = s.find("\n", i)
            i = n if j == -1 else j + 1
            continue
        if s.startswith("/*", i):
            j = s.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        if c == ";":
            return True
        i += 1
    return False


# -- the room ------------------------------------------------------------------------------------------------------


def _fold(x: Any) -> Any:
    from copilot.scrub import fold

    return fold(x) if isinstance(x, str) else x


def _guard(names: frozenset, denied: List[str]):
    """SQLite's authorizer for the model's SQL: reads of the room's TEMP tables, SELECT, the allowed functions."""

    def auth(action, a1, a2, dbname, source):  # noqa: ARG001 - SQLite's signature
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ:
            # a column of a room table; or a read of no column (count(*) of a join), which SQLite reports without the
            # database when the name is unqualified: an unqualified name resolves to TEMP first, and no real table
            # shares a room table's name (tests/test_dataroom.py)
            if a1 in names and (dbname == "temp" or (dbname is None and a2 == "")):
                return sqlite3.SQLITE_OK
            denied.append(f"table:{a1}")
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION:
            if (a2 or "").lower() in FUNCTIONS:
                return sqlite3.SQLITE_OK
            denied.append(f"function:{a2}")
            return sqlite3.SQLITE_DENY
        denied.append(f"action:{action}")
        return sqlite3.SQLITE_DENY

    return auth


def _cell(v: Any) -> Any:
    if isinstance(v, str) and len(v) > CELL:
        return v[: CELL - 1] + "…"
    if isinstance(v, bytes):
        return f"<{len(v)} byte>"
    return v


def _said(exc: Exception, denied: List[str], role: str) -> str:
    """Why a query did not run, without naming anything outside the room: a real table and a missing one read the
    same, and the tables listed are the role's own."""
    have = ", ".join(t.name for t in tables_for(role))
    msg = str(exc)
    if f"action:{sqlite3.SQLITE_RECURSIVE}" in denied:
        return "Không dùng CTE đệ quy (WITH RECURSIVE)"
    if any(d.startswith("action:") for d in denied):
        return "Chỉ được đọc bằng một câu SELECT (không PRAGMA, ATTACH, ghi)"
    if any(d.startswith("table:") for d in denied) or msg.startswith("no such table"):
        name = next((d[6:] for d in denied if d.startswith("table:")), None) or msg.split(":", 1)[-1].strip()
        name = name.split(".")[-1]
        return f"Bảng {name} không có trong danh mục; chỉ đọc được: {have}"
    if any(d.startswith("function:") for d in denied):
        fn = next(d[9:] for d in denied if d.startswith("function:"))
        return f"Hàm {fn} không được dùng trong truy vấn"
    if msg == "interrupted":
        return f"Truy vấn chạy quá {SECONDS:.0f} giây nên đã dừng; hãy thu hẹp điều kiện hoặc bỏ phép nối chéo"
    if "one statement" in msg:
        return "Mỗi lần chỉ một câu lệnh SELECT"
    if "readonly" in msg or "query_only" in msg or "read-only" in msg:
        return "Chỉ được đọc: không ghi được dữ liệu"
    return f"Câu lệnh SQL lỗi: {msg}"  # syntax, a missing column: SQLite's own words, about the room's tables


def _build(con: sqlite3.Connection, who: Who, tables: List[Table], loaded: Dict[str, List[Sequence[Any]]]) -> None:
    for t in tables:
        cols = ", ".join(f"{c} {ty}" for c, ty in t.columns)
        con.execute(f"create temp table {t.name} ({cols})")
        marks = ", ".join("?" * len(t.columns))
        if t.load is not None:
            con.executemany(f"insert into temp.{t.name} values ({marks})", loaded[t.name])
        else:
            sql, args = t.sql(who)
            con.execute(f"insert into temp.{t.name} {sql}", tuple(args))


def _schemas() -> None:
    """The real tables exist before the room copies them (a new state file has only what its stores created)."""
    from control.audit import SCHEMA as AUDIT_SCHEMA
    from control.db import SCHEMA as CONTROL_SCHEMA
    from market.store import SCHEMA as MARKET_SCHEMA
    from news.store import SCHEMA as NEWS_SCHEMA
    from wealth.paths import ensure_schema, state_path

    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10)
    try:
        for name, script in (("control", CONTROL_SCHEMA + AUDIT_SCHEMA), ("news", NEWS_SCHEMA + AUDIT_SCHEMA),
                             ("market", MARKET_SCHEMA)):  # fmt: skip
            ensure_schema(con, path, name, script)
    finally:
        con.close()


def _run(who: Who, sql: str, tables: List[Table], loaded: Dict[str, List[Sequence[Any]]]) -> Dict[str, Any]:
    from wealth.paths import state_path

    _schemas()
    started = time.perf_counter()
    con = sqlite3.connect(f"file:{state_path()}?mode=ro", uri=True, timeout=5, check_same_thread=False)
    try:
        _build(con, who, tables, loaded)
        built = time.perf_counter()
        con.execute("pragma query_only = on")
        con.setlimit(sqlite3.SQLITE_LIMIT_ATTACHED, 0)
        con.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 1_000_000)
        con.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, SQL_CHARS + 100)
        con.create_function("khong_dau", 1, _fold, deterministic=True)
        denied: List[str] = []
        con.set_authorizer(_guard(frozenset(t.name for t in tables), denied))
        deadline = time.monotonic() + SECONDS
        con.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 2000)
        try:
            cur = con.execute(sql)
            columns = [d[0] for d in cur.description or []]
            rows = cur.fetchmany(ROWS + 1)
            total = len(rows)
            if total > ROWS:
                rows = rows[:ROWS]
                total = con.execute(f"select count(*) from ({sql})").fetchone()[0]
        except (sqlite3.DatabaseError, sqlite3.Warning, sqlite3.ProgrammingError) as exc:
            raise Refused(_said(exc, denied, who.role)) from None
        finally:
            con.set_progress_handler(None, 0)
            con.set_authorizer(None)
    finally:
        con.close()
    done = time.perf_counter()
    return {
        "sql": sql,
        "columns": columns,
        "rows": [[_cell(v) for v in r] for r in rows],
        "total": total,
        "shown": len(rows),
        "tables": [t.name for t in tables],
        "as_of": datetime.now(VN).strftime("%Y-%m-%d %H:%M"),
        "build_ms": round(1000 * (built - started), 1),
        "query_ms": round(1000 * (done - built), 1),
    }


async def query(ctx: Ctx, sql: str) -> Dict[str, Any]:
    """Run one ``select`` in the person's room: ``{"sql", "columns", "rows" (at most ROWS), "total", "shown",
    "tables", "as_of" (Vietnam time), "build_ms", "query_ms"}``. :class:`Refused` when it may not run or was
    stopped."""
    clean = _clean(sql)
    who = who_for(ctx)
    tables = named(clean, who.role)
    loaders = [t for t in tables if t.load is not None]
    loaded = dict(zip([t.name for t in loaders], await asyncio.gather(*(t.load(who) for t in loaders))))
    return await asyncio.to_thread(_run, who, clean, tables, loaded)


# -- the tool ------------------------------------------------------------------------------------------------------


def _num(v: Any) -> str:
    if isinstance(v, bool) or v is None:
        return "" if v is None else str(int(v))
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() and abs(v) < 1e15 else f"{v:.6g}"
    return str(v)


def text_of(res: Dict[str, Any], lines: int = 50) -> str:
    """What the model reads of a result: the total first (said as the total, with how many rows are listed), then the
    rows, one per line."""
    total, shown = res["total"], res["shown"]
    if total == 1 and len(res["columns"]) == 1:
        return f"Kết quả: {res['columns'][0]} = {_num(res['rows'][0][0])} (1 dòng)."
    head = f"Kết quả: {total} dòng" + (f", liệt kê {min(shown, lines)} dòng đầu" if total > min(shown, lines) else "")
    body = [" | ".join(res["columns"])] + [" | ".join(_num(v) for v in r) for r in res["rows"][:lines]]
    return head + ".\n" + "\n".join(body) if res["columns"] else head + "."


CALLS = 3  # truy_van calls a turn (ADR-0040): a fourth is refused, the model answers from what it has
# what one row of a table is called, for the template's sentence ("Có 1.415 tin.")
NOUNS = {"tin": "tin", "tin_bi_giu": "tin bị giữ", "su_kien": "sự kiện", "nhan_dinh": "nhận định",
         "de_xuat": "lần áp dụng", "tac_dong_gia_dinh": "dòng tác động", "du_bao": "dự báo", "viec_nen": "lần chạy",
         "nguon_du_lieu": "lần lấy số liệu", "gia_dinh": "gia đình", "tai_san": "khoản", "lien_he": "lần liên hệ",
         "duyet": "yêu cầu duyệt", "dong_tien": "giao dịch", "muc_tieu": "mục tiêu", "nhat_ky": "dòng nhật ký",
         "canh_bao": "cảnh báo"}  # fmt: skip
COUNT = re.compile(r"^\s*select\s+count\s*\(\s*(?:\*|distinct\s+\w+|\w+)\s*\)(?:\s+as\s+\w+)?\s+from\s+(\w+)\b", re.I)


def vn(v: Any) -> str:
    """A number as the person reads it: 1.415, 0,15."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return _num(v)
    if isinstance(v, float) and not v.is_integer():
        return f"{v:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    return f"{int(v):,}".replace(",", ".")


def template(res: Dict[str, Any]) -> str:
    """The answer said without the model (``client_ai`` off, ADR-0026): one count over one table as a sentence
    ("Có 1.415 tin."), one value as itself, otherwise the total and the first rows."""
    if res["total"] == 1 and len(res["columns"]) == 1:
        v = res["rows"][0][0]
        m = COUNT.match(res["sql"])
        if m and m.group(1).lower() in NOUNS and isinstance(v, int):
            return f"Có {vn(v)} {NOUNS[m.group(1).lower()]}."
        return f"{res['columns'][0]}: {vn(v)}."
    head = f"{vn(res['total'])} dòng" + (f", {min(res['shown'], 10)} dòng đầu" if res["total"] > 10 else "")
    body = [" | ".join(res["columns"])] + [" | ".join(vn(v) for v in r) for r in res["rows"][:10]]
    return head + ":\n" + "\n".join(body) if res["columns"] and res["rows"] else head + "."


def _audit(ctx: Ctx, sql: str, res: Optional[Dict[str, Any]], ms: float, refused: Optional[str] = None) -> None:
    """One audit row per query (ADR-0040): who, the role, the SQL, the rows and the time — or why it was refused."""
    from control import audit, db

    data: Dict[str, Any] = {"role": ctx.role, "client_id": ctx.client_id, "sql": sql[:SQL_CHARS], "ms": round(ms, 1)}
    if res is not None:
        data.update(rows=res["total"], shown=res["shown"])
    if refused is not None:
        data["refused"] = refused[:300]
    actor = ctx.user or f"client:{ctx.client_id or '-'}"
    with db.tx() as con:
        audit.append(con, actor, "assistant.query", ",".join(res["tables"]) if res and res["tables"] else "-", data)


# On a turn that disputes a number (``turn.disputes``), said next to the count, where the model writes from: in the
# system prompt alone, Haiku 5.5 counted again and then guessed why the person's number differed in 3 disputes of 3
# (“có thể bạn đang nhớ số khác”, D5 eval).
RECOUNTED = (
    "\nNgười dùng vừa nêu một con số khác: trả lời chỉ bằng bảng, điều kiện và con số vừa đếm ở trên. Không đoán "
    "và không kể vì sao con số của họ khác."
)


async def truy_van(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The ``truy_van`` tool's run: one SELECT in the room; the rows, the total, the SQL and when. Audited, refused
    after :data:`CALLS` a turn; with ``ctx.reads`` off the text is the template, which the person reads, not the
    model."""
    sql = str(args.get("sql") or "")
    ctx.queries += 1
    started = time.perf_counter()
    try:
        if ctx.queries > CALLS:
            raise Refused(f"Đã truy vấn {CALLS} lần trong lượt này: trả lời bằng các kết quả đã có")
        res = await query(ctx, sql)
    except Refused as exc:
        _audit(ctx, sql, None, 1000 * (time.perf_counter() - started), str(exc))
        raise
    _audit(ctx, sql, res, 1000 * (time.perf_counter() - started))
    how = {k: res[k] for k in ("sql", "total", "shown", "tables", "as_of")}
    said = text_of(res) + (RECOUNTED if ctx.recount else "") if ctx.reads else template(res)
    return {
        "text": said,
        "data": {"total": res["total"], "shown": res["shown"], "columns": res["columns"], "sql": res["sql"]},
        "as_of": res["as_of"],
        "sources": [f"Truy vấn trên {', '.join(res['tables']) or 'không bảng nào'} lúc {res['as_of']}"],
        "query": {**how, "ms": round(res["build_ms"] + res["query_ms"], 1)},  # “Cách tính” in the panel
    }


DESCRIPTION = (
    "đếm, lọc, liệt kê hay tổng hợp số liệu bằng một câu SELECT trên các bảng dưới đây (chỉ những gì vai trò này "
    "được xem): dùng khi không công cụ nào khác trả lời đúng câu hỏi, khi cần một tổng số, và khi người dùng nói một "
    "con số sai. Kết quả có tổng số dòng, câu SQL và thời điểm; người dùng xem được câu SQL"
)


def _catalog(role: str) -> str:
    from assistant import datacatalog

    return datacatalog.catalog(role)


CATALOGUE: Dict[str, Tool] = {
    "truy_van": Tool(
        "truy_van",
        DESCRIPTION,
        ROLES,
        truy_van,
        params={"sql": Param(str, "một câu SELECT (SQLite) trên các bảng dưới đây; đếm bằng count(*)")},
        reference=_catalog,
    )
}
