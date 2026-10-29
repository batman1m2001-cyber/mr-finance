"""The data room (docs/ASSISTANT_DATA_PLAN.md D2, ADR-0040; OWN-DA-02, OWN-DA-03): ``truy_van`` reads only tables
built for the person asking, and only with one SELECT. Each adversarial case is refused and leaks nothing: a real
table, a CTE named like a room table, ATTACH, PRAGMA, a write, load_extension, a recursive CTE, two statements,
another family's row, held news, a slow query."""

import asyncio
import sqlite3
import time

import pytest

from assistant import dataroom
from assistant.base import Ctx
from assistant.dataroom import Refused, query
from news import store as news


def seed(n, held=(), title="Lãi suất điều hành"):
    now = time.time()
    rows = [
        {"source": "cafef_ck", "url_key": f"u{i}", "title_key": f"t{i}", "published": now - 86400 + i,
         "ingested": now, "kind": "domestic", "status": "new", "relevance": "high", "title": f"{title} {i}",
         "outlet": "CafeF", "label": "Trong nước", "summary": "", "restricted": ["VCB"] if i in held else []}
        for i in range(n)
    ]  # fmt: skip
    assert news.add(rows)[1] == 0


def ctx(role, client=None, scope="personal", user=None):
    return Ctx(role=role, client_id=client, scope=scope, question="", user=user)


def ask(role, sql, **kw):
    return asyncio.run(query(ctx(role, **kw), sql))


def refused(role, sql, **kw):
    with pytest.raises(Refused) as e:
        ask(role, sql, **kw)
    return str(e.value)


def test_each_role_has_the_tables_of_the_plan():
    names = {r: {t.name for t in dataroom.tables_for(r)} for r in dataroom.ROLES}
    assert names["cio"] == {"tin", "su_kien", "nhan_dinh", "de_xuat", "tac_dong_gia_dinh", "du_bao", "viec_nen",
                            "nguon_du_lieu", "nhat_ky", "tin_bi_giu", "canh_bao"}  # fmt: skip
    assert names["rm"] == {"tin", "su_kien", "gia_dinh", "tai_san", "lien_he", "duyet"}
    assert names["client"] == {"tin", "su_kien", "tai_san", "dong_tien", "muc_tieu"}
    assert names["admin"] == {"nhat_ky", "tin_bi_giu", "viec_nen", "canh_bao"}
    assert "compliance" not in dataroom.ROLES and "specialist" not in dataroom.ROLES
    assert refused("compliance", "select 1") == "Vai trò này không truy vấn dữ liệu"


def test_no_real_table_shares_a_room_tables_name():
    """The authorizer lets an unqualified, column-less read (``count(*)`` of a join) through by name: that is safe
    only while TEMP shadows every room name, which needs no real table of that name."""
    seed(1)
    ask("cio", "select count(*) from tin")  # every store's schema is in place
    from people import store

    store.client_ids()
    from wealth.paths import state_path

    con = sqlite3.connect(state_path())
    real = {r[0] for r in con.execute("select name from sqlite_master")}
    con.close()
    assert len(real) > 30 and not real & set(dataroom.TABLES)


@pytest.mark.parametrize(
    "sql",
    [
        "select * from people",
        "select email from people",
        "select * from accounts",
        "select * from news_items",
        "select * from main.people",
        "select * from main.news_items",
        "select count(*) from people",
        "select count(*) from tin, people",
        "select * from sqlite_master",
        "select * from temp.sqlite_master",
        "select * from sqlite_temp_master",
        "select * from tin where ma in (select id from main.news_items)",
        # a CTE named like a room table: SQLite names the CTE as the read's source (the reason the room copies)
        "with tin as (select email from main.people) select * from tin",
        "with tin as (select * from people) select count(*) from tin",
        "with su_kien as (select login, password from accounts) select * from su_kien",
    ],
)
def test_a_real_table_is_refused_and_reads_like_a_missing_one(sql):
    seed(3)
    said = refused("cio", sql)
    assert said.startswith("Bảng ") and "không có trong danh mục" in said
    assert "@" not in said and "password" not in said.split("không có")[1]
    missing = refused("cio", "select * from bang_khong_co")
    assert missing.split(" không có")[1] == said.split(" không có")[1]  # no oracle: real and missing read the same


@pytest.mark.parametrize(
    "sql",
    [
        "pragma table_info(people)",
        "select * from pragma_table_info('people')",
        "select name from pragma_table_list",
        "select * from pragma_database_list",
        "attach database ':memory:' as x",
        "select 1; attach database ':memory:' as x",
        "insert into tin (ma) values ('x')",
        "update tin set tieu_de = 'x'",
        "delete from tin",
        "drop table tin",
        "create table x (a)",
        "with a as (select 1) insert into tin (ma) select 1 from a",
        "with a as (select 1) delete from tin",
        "select load_extension('/tmp/x.so')",
        "select printf('%.*c', 1000000000, 'x')",
        "select randomblob(1000000000)",
        "select zeroblob(1000000000)",
        "select sqlite_version()",
        "select value from json_each('[1,2]')",
        "with recursive r(n) as (select 1 union all select n + 1 from r) select count(*) from r",
        "select 1; select 2",
        "select 1; drop table tin",
        "select 1 /* ; */ ; delete from tin",
        "begin",
        "vacuum",
        "explain select * from people",
    ],
)
def test_nothing_but_one_select_runs(sql):
    seed(3)
    said = refused("cio", sql)
    assert "people" not in said or said.startswith("Bảng people không có")
    assert ask("cio", "select count(*) from tin")["rows"] == [[3]]  # nothing changed


def test_a_recursive_cte_says_so():
    sql = "with recursive r(n) as (select 1 union all select n + 1 from r) select count(*) from r"
    assert refused("cio", sql) == "Không dùng CTE đệ quy (WITH RECURSIVE)"
    unsaid = "with r(n) as (select 1 union all select n + 1 from r) select count(*) from r"  # SQLite: word optional
    assert "không có trong danh mục" in refused("cio", unsaid)
    assert ask("cio", "with x as (select 1 as a) select a from x")["rows"] == [[1]]  # a plain CTE is a select


def test_a_semicolon_in_a_string_or_a_trailing_one_is_one_statement():
    seed(3)
    assert ask("cio", "select ';' as a, count(*) from tin;")["rows"] == [[";", 3]]
    assert ask("cio", "select count(*) from tin -- ; delete")["rows"] == [[3]]


def test_a_slow_query_is_stopped_near_two_seconds():
    seed(400)
    started = time.monotonic()
    said = refused("cio", "select count(*) from tin a, tin b, tin c, tin d")
    assert time.monotonic() - started < dataroom.SECONDS + 2
    assert said.startswith("Truy vấn chạy quá 2 giây")


def test_a_page_of_rows_and_always_the_total():
    seed(310)
    res = ask("cio", "select ma, tieu_de from tin order by luc_dang desc")
    assert res["shown"] == len(res["rows"]) == dataroom.ROWS and res["total"] == 310
    text = dataroom.text_of(res)
    assert text.startswith("Kết quả: 310 dòng, liệt kê 50 dòng đầu.")
    count = ask("cio", "select count(*) as so_tin from tin where ngay_lay = date('now', '+7 hours')")
    assert count["rows"] == [[310]] and dataroom.text_of(count) == "Kết quả: so_tin = 310 (1 dòng)."
    assert res["tables"] == ["tin"] and count["as_of"][:10] == time.strftime(
        "%Y-%m-%d", time.gmtime(time.time() + 7 * 3600)
    )


def test_khong_dau_matches_vietnamese_without_its_marks():
    seed(2, title="Lãi suất điều hành")
    seed_other = {"source": "cafef_ck", "url_key": "x", "title_key": "x", "published": 1.0, "ingested": 1.0,
                  "kind": "intl", "status": "new", "relevance": "low", "title": "Giá vàng", "outlet": "CafeF",
                  "label": "Quốc tế", "summary": ""}  # fmt: skip
    news.add([seed_other])
    res = ask("cio", "select count(*) from tin where khong_dau(tieu_de) like '%lai suat dieu hanh%'")
    assert res["rows"] == [[2]]


def test_held_news_is_not_in_tin_and_is_in_tin_bi_giu_for_the_cio():
    from events import store as events

    seed(5, held={2}, title="Tin")
    rows = ask("cio", "select tieu_de from tin")["rows"]
    assert len(rows) == 4 and ["Tin 2"] not in rows
    for role in ("rm", "client"):
        assert ["Tin 2"] not in ask(role, "select tieu_de from tin", client="C01" if role == "client" else None)["rows"]
    got = ask("cio", "select tieu_de, cong_ty_han_che from tin_bi_giu")["rows"]
    assert got == [["Tin 2", "VCB"]]
    assert refused("admin", "select * from tin").startswith("Bảng tin không có")
    assert refused("rm", "select * from tin_bi_giu").startswith("Bảng tin_bi_giu không có")
    # an event holding the held item: its title is that item's; the CIO sees it blocked, an RM or a client not at all
    held_id = next(i["id"] for i in news.inbox(held=True, limit=None))
    events.create([held_id], None, "cio")
    assert ask("cio", "select tieu_de, bi_giu from su_kien")["rows"] == [["Tin 2", 1]]
    assert ask("rm", "select count(*) from su_kien")["rows"] == [[0]]
    assert ask("client", "select count(*) from su_kien", client="C01")["rows"] == [[0]]


def test_the_audit_log_has_no_payloads_or_hashes_and_alerts_are_the_roles():
    from control import alerts

    seed(1)
    alerts.raise_("news_feed", "f1", "Nguồn lỗi")
    alerts.raise_("audit_chain", "c1", "Chuỗi gãy")
    cols = ask("cio", "select * from nhat_ky")["columns"]
    assert cols == ["so_thu_tu", "luc", "ngay", "gio", "nguoi", "hanh_dong", "doi_tuong"]
    assert sorted(r[0] for r in ask("cio", "select loai from canh_bao")["rows"]) == ["audit_chain", "news_feed"]
    assert sorted(r[0] for r in ask("admin", "select loai from canh_bao")["rows"]) == ["audit_chain", "news_feed"]
    for sql in ("select hash from nhat_ky", "select data from nhat_ky"):
        assert refused("cio", sql).startswith("Câu lệnh SQL lỗi: no such column")


@pytest.fixture
def as_signed_in(monkeypatch):
    """A served request signed in as ``who``: ``people.auth`` checks as it does behind the cookie."""
    from people import auth, store

    def sign(who):
        p = next(x for x in store.staff() if x["id"] == who) if not who.startswith("C") else {
            **store.client(who), "id": who, "role": "client"}  # fmt: skip
        viewer = auth._viewer({**p, "name": p.get("name") or who})
        monkeypatch.setattr(auth, "checking", lambda: True)
        monkeypatch.setattr(auth, "signed_in", lambda: viewer)
        return viewer

    return sign


def test_an_rm_reads_their_book_and_no_other_family(as_signed_in):
    from contacts import store as contacts
    from people import store
    from wealth import store as wealth_store

    book01, book02 = store.families_of("rm01"), store.families_of("rm02")
    assert "C01" in book01 and "C01" not in book02 and book02
    wealth_store.propose("C01", "tuition", "Học phí — Tích lũy đều", {"option": {"id": "light"}})
    contacts.log("C01", "call", None, "Gọi hỏi học phí", "rm01")
    c01 = store.client("C01")["name"]
    as_signed_in("rm02")
    for sql in ("select * from gia_dinh", "select * from tai_san", "select * from lien_he", "select * from duyet"):
        res = ask("rm", sql, user="rm02")
        assert "C01" not in str(res["rows"]) and c01 not in str(res["rows"]), sql
    fams = ask("rm", "select distinct ma_gia_dinh from tai_san", user="rm02")["rows"]
    assert sorted(r[0] for r in fams) == sorted(book02)
    as_signed_in("rm01")
    assert ask("rm", "select count(*) from duyet where ma_gia_dinh = 'C01'", user="rm01")["rows"] == [[1]]
    assert ask("rm", "select count(*) from lien_he", user="rm01")["rows"] == [[1]]


def test_a_client_reads_their_own_family_even_naming_another(as_signed_in):
    as_signed_in("C02")
    for sql in ("select distinct ma_gia_dinh from tai_san", "select 'C02' from dong_tien limit 1"):
        rows = ask("client", sql, client="C01", scope="family")["rows"]
        assert rows in ([["C02"]], []), (sql, rows)
    theirs = ask("client", "select count(*) from muc_tieu", client="C01")["rows"]
    own = ask("client", "select count(*) from muc_tieu", client="C02")["rows"]
    assert theirs == own
    owners = {r[0] for r in ask("client", "select chu_tai_khoan from dong_tien", client="C01")["rows"]}
    from people import store

    assert store.client("C01")["name"] not in owners


def test_the_tool_returns_rows_total_sql_and_as_of():
    seed(12)
    out = asyncio.run(dataroom.truy_van(ctx("cio"), {"sql": "select ma from tin"}))
    assert out["data"]["total"] == 12 and out["data"]["sql"] == "select ma from tin" and out["as_of"]
    assert out["text"].startswith("Kết quả: 12 dòng") and out["sources"][0].startswith("Truy vấn trên tin lúc ")
    with pytest.raises(Refused):
        asyncio.run(dataroom.truy_van(ctx("cio"), {}))


def test_a_long_cell_is_cut_and_the_live_file_is_never_written(tmp_path):
    seed(1, title="x" * 1000)
    from wealth.paths import state_path

    ask("cio", "select count(*) from tin")  # a new file: the stores' schemas are created once
    before = state_path().stat().st_mtime_ns
    cell = ask("cio", "select tieu_de from tin")["rows"][0][0]
    assert len(cell) == dataroom.CELL and cell.endswith("…")
    assert state_path().stat().st_mtime_ns == before  # the room's tables are TEMP: the file is not touched
