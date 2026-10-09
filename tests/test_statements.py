import asyncio
import base64
import json
from pathlib import Path

import pytest
from operonx import Operon
from operonx.agents.testing import ScriptedLLM, says, scripted

from statements.graph import statement_flow
from wealth import store
from wealth.text import ascii_lower, number

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"
PARAMS = {"client_id": None, "filename": None, "content": None}


def read(client_id, name, raw=None):
    raw = raw if raw is not None else (SAMPLES / name).read_bytes()
    out = asyncio.run(
        Operon(statement_flow, params=PARAMS).run(
            inputs={
                "client_id": client_id,
                "filename": name,
                "content": base64.b64encode(raw).decode(),
            }
        )
    )
    return out


def test_numbers_come_in_every_vietnamese_spelling():
    assert number("2.000.000.000") == 2e9
    assert number("2,000,000,000") == 2e9
    assert number("5,0") == 5.0 and number("1.200") == 1200
    assert number("") is None and number(24000) == 24000.0
    assert ascii_lower("Mã CK  Số lượng") == "ma ck so luong"


@pytest.mark.parametrize(
    "client_id,name,institution,expect",
    [
        ("C01", "vps_C01.csv", "VPS", {"MWG": 6000, "SSI": 15000, "cash": 120_000_000}),
        ("C05", "ssi_C05.xlsx", "SSI", {"HPG": 5000, "MBB": 4000, "cash": 50_000_000}),
        ("C04", "vcb_C04.pdf", "Vietcombank", {"deposit": 2_000_000_000, "cash": 85_000_000}),
    ],
)
def test_the_rules_read_every_sample(monkeypatch, client_id, name, institution, expect):
    monkeypatch.setenv("MF_AI", "off")
    out = read(client_id, name)
    assert "$errors" not in out, out["$errors"]
    r = out["read"]
    assert (r["institution"], r["method"]) == (institution, "rules")
    got = {}
    for h in r["holdings"]:
        d = h["detail"]
        got[d.get("ticker") or h["class"]] = d.get("qty") or h["value"]
        assert h["trust"] == "statement" and h["source"] == "statement" and h["tier"] == 2
    assert got == expect
    # kept: the consolidation reads them back
    assert len(store.holdings(client_id, "statement")) == len(expect)


def test_a_deposit_keeps_its_rate_and_maturity(monkeypatch):
    monkeypatch.setenv("MF_AI", "off")
    deposit = next(h for h in read("C04", "vcb_C04.pdf")["read"]["holdings"] if h["class"] == "deposit")
    assert deposit["detail"]["rate"] == 0.05 and deposit["detail"]["maturity"] == "2027-03-15"
    assert deposit["name"] == "Tiền gửi có kỳ hạn 12 tháng (Vietcombank)"


def test_reading_the_same_file_twice_replaces_it(monkeypatch):
    monkeypatch.setenv("MF_AI", "off")
    read("C01", "vps_C01.csv")
    read("C01", "vps_C01.csv")
    assert len(store.holdings("C01", "statement")) == 3


def test_the_model_reads_what_the_rules_cannot(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    letter = "Thư xác nhận của HSC: quý khách đang nắm giữ 2.000 cổ phiếu FPT, giá vốn 100.000 đồng."
    reply = {
        "holdings": [
            {"type": "stock", "ticker": "fpt", "qty": 2000, "avg_price": 100000},
            {"type": "stock", "ticker": "??", "qty": 1},
        ]
    }
    model = ScriptedLLM(says(json.dumps(reply)))
    with scripted(assistant=model):
        out = read("C03", "hsc.txt", letter.encode())
    r = out["read"]
    assert (r["method"], r["institution"], model.calls) == ("ai", "HSC", 1)
    assert [(h["detail"]["ticker"], h["detail"]["qty"]) for h in r["holdings"]] == [("FPT", 2000)]
    assert "HSC" in model.requests[0]["messages"][-1]["content"]


def test_the_rules_step_in_when_the_model_gives_nothing_usable(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    with scripted(assistant=ScriptedLLM(says("Tôi không đọc được tệp này."))):
        r = read("C01", "vps_C01.csv")["read"]
    assert (r["method"], r["count"]) == ("rules", 3)


def test_the_rules_step_in_when_the_model_cannot_be_reached(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")

    def down(messages, params):
        raise ConnectionError("gateway unreachable")

    with scripted(assistant=ScriptedLLM(down)):
        out = read("C01", "vps_C01.csv")
    assert out["read"]["method"] == "rules" and out["read"]["count"] == 3
    (err,) = out["$errors"].values()
    assert err["handled"] is True
