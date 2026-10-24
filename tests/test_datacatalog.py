"""The data catalog (docs/ASSISTANT_DATA_PLAN.md D3, OWN-DA-04): every table and column of the room is documented,
every example SQL runs in its role's room, and a role's catalog names only its own tables."""

import asyncio
import re
import time

import pytest

from assistant import datacatalog, dataroom
from assistant.base import Ctx
from assistant.dataroom import Table, query
from news import store as news


def test_every_column_of_the_room_is_documented():
    assert datacatalog.undocumented() == []
    for name, t in dataroom.TABLES.items():
        about, cols = datacatalog.docs()[name]
        assert about and all(cols.values()), name


def test_an_undocumented_column_fails(monkeypatch):
    t = dataroom.TABLES["tin"]
    grown = Table(t.name, t.roles, t.columns + [("cot_moi", "TEXT")], t.copy, t.load)
    monkeypatch.setitem(dataroom.TABLES, "tin", grown)
    assert datacatalog.undocumented() == ["tin.cot_moi"]
    monkeypatch.setitem(dataroom.TABLES, "tin", Table(t.name, t.roles, t.columns[1:], t.copy, t.load))
    assert datacatalog.undocumented() == ["tin.ma"]


def test_the_codes_the_stores_use_are_the_ones_documented():
    from apply.run import STATUS_LABEL
    from contacts.store import CHANNELS
    from control.alerts import KINDS
    from flows.ops import LABELS
    from views.store import LIFECYCLE

    cols = {t: c for t, (_, c) in datacatalog.docs().items()}

    def says(table, col, values):
        missing = [v for v in values if not re.search(rf"(^|[\s,(:]){re.escape(v)}($|[\s,);])", cols[table][col])]
        assert not missing, (table, col, missing)

    says("tin", "trang_thai", [s for s in news.STATUSES if s != "refused"])
    says("nhan_dinh", "trang_thai", LIFECYCLE)
    says("de_xuat", "trang_thai", STATUS_LABEL)
    says("tac_dong_gia_dinh", "trang_thai_lan", STATUS_LABEL)
    says("canh_bao", "loai", KINDS)
    says("dong_tien", "nhom", list(LABELS) + ["other"])
    says("dong_tien", "ten_nhom", LABELS.values())
    says("lien_he", "kenh", CHANNELS.values())


def test_each_role_has_a_catalog_naming_only_its_own_tables():
    for role in dataroom.ROLES:
        text = datacatalog.catalog(role)
        mine = {t.name for t in dataroom.tables_for(role)}
        headed = set(re.findall(r"^## (\w+):", text, re.M))
        assert headed == mine, role
        quoted = {w for w in re.findall(r"`(\w+)", text) if w in dataroom.TABLES}
        assert quoted <= mine, (role, quoted - mine)
        n = len(datacatalog.examples(role))
        assert 10 <= n <= 20, (role, n)
        for _, sql in datacatalog.examples(role):
            words = set(re.findall(r"\w+", sql)) & set(dataroom.TABLES)
            assert words and words <= mine, (role, sql)
    assert datacatalog.catalog("specialist") == ""


def test_the_cio_catalog_has_the_question_of_2026_10_24_and_the_definitions():
    text = datacatalog.catalog("cio")
    asked = dict(datacatalog.examples("cio"))
    assert "Hệ thống đã lấy về bao nhiêu tin?" in asked and "Hôm nay lấy về bao nhiêu tin?" in asked
    assert "ngay_lay = date('now', '+7 hours')" in text and "trang_thai = 'REJECTED'" in text


def seed_news():
    now = time.time()
    rows = [
        {"source": "cafef_ck", "url_key": f"u{i}", "title_key": f"t{i}", "published": now - 3600, "ingested": now,
         "kind": "domestic", "status": "new", "relevance": "high", "title": f"Lãi suất điều hành {i}",
         "outlet": "CafeF", "label": "Trong nước", "summary": "", "restricted": ["VCB"] if i < 2 else []}
        for i in range(12)
    ]  # fmt: skip
    news.add(rows)


@pytest.fixture
def as_signed_in(monkeypatch):
    from people import auth, store

    def sign(who):
        p = next(x for x in store.staff() if x["id"] == who) if not who.startswith("C") else {
            **store.client(who), "id": who, "role": "client"}  # fmt: skip
        viewer = auth._viewer({**p, "name": p.get("name") or who})
        monkeypatch.setattr(auth, "checking", lambda: True)
        monkeypatch.setattr(auth, "signed_in", lambda: viewer)

    return sign


WHO = {"cio": (None, "cio"), "rm": (None, "rm01"), "client": ("C01", "C01"), "compliance": (None, "compliance"),
       "admin": (None, "admin")}  # fmt: skip


@pytest.mark.parametrize("role", dataroom.ROLES)
def test_every_example_runs_in_its_room(role, as_signed_in):
    seed_news()
    client, user = WHO[role]
    if role in ("rm", "client"):
        as_signed_in(user)
    ctx = Ctx(role=role, client_id=client, scope="family", question="", user=user)
    for q, sql in datacatalog.examples(role):
        res = asyncio.run(query(ctx, sql))  # Refused fails the test
        assert res["columns"], q
    if role == "cio":
        got = dict(
            asyncio.run(query(ctx, dict(datacatalog.examples("cio"))["Hệ thống đã lấy về bao nhiêu tin?"]))["rows"]
        )
        assert got == {"new": 10}  # 12 fetched, 2 held for Compliance
    if role == "compliance":
        assert asyncio.run(query(ctx, "select count(*) from tin_bi_giu"))["rows"] == [[2]]
    if role in ("rm", "client"):
        assert asyncio.run(query(ctx, "select count(*) from tai_san"))["rows"][0][0] > 0
