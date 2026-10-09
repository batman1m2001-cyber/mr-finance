from wealth import fixtures, store, valuation
from wealth.money import TR, TY, months_text, pct, vnd


def test_money_reads_like_a_vietnamese_reader_says_it():
    assert vnd(45_200_000_000) == "45,2 tỷ"
    assert vnd(2_440_000_000) == "2,44 tỷ"
    assert vnd(850 * TR) == "850 triệu"
    assert vnd(-1_500 * TR, signed=True) == "-1,5 tỷ"
    assert pct(0.031, signed=True) == "+3,1%"
    assert months_text(14) == "14 tháng" and months_text(360) == "30 năm"


def test_every_client_fixture_values_without_a_gap():
    mk = fixtures.market()
    for cid in fixtures.client_ids(members=True):
        c = fixtures.client(cid)
        rows = (
            valuation.techcombank(cid, c["sources"]["techcombank"], mk)
            + valuation.tcbs(cid, c["sources"]["tcbs"], mk)
            + valuation.techcom_capital(cid, c["sources"]["techcom_capital"], mk)
            + valuation.onehousing(cid, c["sources"]["onehousing"], mk)
            + valuation.open_api(cid, c["sources"].get("open_api"), mk)
            + valuation.declared(cid, c.get("declared"), mk)
        )
        assert rows, cid
        for h in rows:
            assert h["value"] > 0 or h["class"] == "insurance", h
            assert h["kind"] in ("asset", "liability") and h["trust"] in ("verified", "declared")
            assert h["key"].startswith(f"{cid}:")


def test_a_stock_is_valued_at_market_with_its_cost_and_stress():
    mk = fixtures.market()
    h = valuation.stock(
        "C01", "tcbs", {"ticker": "FPT", "qty": 1_000, "avg_price": 95_000}, mk, "verified"
    )
    assert h["value"] == 128 * TR and h["cost"] == 95 * TR and h["prev_value"] == 122 * TR
    assert h["stress"] == round(0.25 * 1.05, 4) and h["detail"]["sector"] == "Công nghệ"


def test_open_api_reads_only_what_the_client_consented_to():
    mk = fixtures.market()
    raw = [
        {
            "institution": "VPBank",
            "consent": False,
            "accounts": [{"id": "x", "type": "CASA", "name": "a", "balance": 1}],
        }
    ]
    assert valuation.open_api("C01", raw, mk) == []


def test_declared_gold_is_valued_at_today_s_price_and_a_house_at_its_word():
    mk = fixtures.market()
    gold, house = valuation.declared(
        "C04",
        [
            {"class": "gold", "name": "Vàng", "qty": 2},
            {"class": "real_estate", "name": "Nhà", "value": 18 * TY},
        ],
        mk,
    )
    assert gold["value"] == 300 * TR and gold["trust"] == "declared"
    assert house["value"] == 18 * TY and house["kind"] == "asset"


def test_the_store_keeps_what_clients_add_and_resets():
    store.put_holdings("C01", "statement", [{"key": "C01:statement:x", "value": 1}])
    store.put_holdings(
        "C01", "statement", [{"key": "C01:statement:x", "value": 2}]
    )  # replaced, not doubled
    assert [h["value"] for h in store.holdings("C01", "statement")] == [2]
    item = store.add_profile("C01", "dependent", {"name": "An"})
    assert store.profile("C01", "dependent")[0]["id"] == item
    rid = store.propose("C01", "scenario", "Bán căn hộ", {"x": 1})
    assert store.decide(rid, "approved", "ok")["status"] == "approved"
    assert store.decide(rid, "rejected") is None, "decided once"
    store.reset()
    assert store.holdings("C01") == [] and store.reviews() == []
