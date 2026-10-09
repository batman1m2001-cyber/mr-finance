"""The brief's five-minute demo (docs/DEMO.md), step by step, through the same HTTP calls the page
makes. If this passes, the demo runs."""

import base64
from pathlib import Path

import pytest
from operonx.app import Application
from starlette.testclient import TestClient

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"
BOLD = {
    "goal": "fast",
    "horizon": "gt10",
    "drop20": "buy",
    "drop35": "buy",
    "bet_bold": "c",
    "experience": "3to10",
    "leverage": "yes",
    "income": "volatile",
    "big_expense": "no",
    "new_assets": "small",
}


@pytest.fixture()
def client():
    with TestClient(Application.find(".").asgi()) as c:
        yield c


def test_the_five_minute_demo(client):

    # 1. Kết nối dữ liệu: tier 1 is there already; a VPS statement is read; the chat adds land and two children
    board = client.post("/api/dashboard", json={"client_id": "C01"}).json()
    tier1 = {s["source"] for s in board["sources"] if s["tier"] == 1 and s["status"] == "connected"}
    assert tier1 == {"techcombank", "tcbs", "techcom_capital", "onehousing"}
    content = base64.b64encode((SAMPLES / "vps_C01.csv").read_bytes()).decode()
    read = client.post(
        "/api/statement", json={"client_id": "C01", "filename": "vps_C01.csv", "content": content}
    ).json()
    assert (read["institution"], read["count"]) == ("VPS", 3)
    land = client.post(
        "/api/declare", json={"client_id": "C01", "message": "Tôi có 1 mảnh đất 500m2 ở Long Thành mua 2019 giá 3 tỷ"}
    ).json()
    kids = client.post("/api/declare", json={"client_id": "C01", "message": "Tôi có 2 con, 14 tuổi và 10 tuổi"}).json()
    assert len(land["recorded"]) == 1 and len(kids["recorded"]) == 2

    # 2. Bài test AI: wants high risk, can bear only a middle level — said out loud
    answers = {}
    while True:
        r = client.post("/api/risk", json={"client_id": "C01", "answers": answers}).json()
        if "result" in r:
            break
        q = r["question"]
        answers[q["id"]] = BOLD.get(q["id"], q["options"][-1]["id"])
    res = r["result"]
    assert res["tolerance_level"] > res["capacity_level"]
    assert res["warnings"][0].startswith("Anh/chị muốn rủi ro mức")

    # 3. Dashboard: personal ↔ family; the calendar shows the large tuition payment
    me = client.post("/api/dashboard", json={"client_id": "C01", "scope": "personal"}).json()
    family = client.post("/api/dashboard", json={"client_id": "C01", "scope": "family"}).json()
    assert family["net_worth"]["value"] > me["net_worth"]["value"]
    assert any("du học" in x["label"].lower() for x in family["cashflow"]["large"])

    # 4. Alerts: the second-property tax draft, and the metro near the Thảo Điền flat
    alerts = client.post("/api/alerts", json={"client_id": "C01", "scope": "family"}).json()["alerts"]
    by = {a["factor"]: a for a in alerts}
    assert by["P01"]["impact"] < 0 and "/năm" in by["P01"]["message"]
    assert by["I01"]["opportunity"] and "Thảo Điền" in by["I01"]["message"]

    # 5. Scenario: sell one property and see the cash change
    sim = client.post("/api/scenario", json={"client_id": "C01", "scenario": "sell_home", "scope": "family"}).json()
    assert sim["after"]["liquid"] > sim["before"]["liquid"] and len(sim["options"]) == 2

    # 6. RM approves
    item = client.post(
        "/api/review/propose",
        json={
            "client_id": "C01",
            "scenario": "sell_home",
            "title": sim["title"],
            "option": sim["options"][0],
            "summary": sim["summary"],
        },
    ).json()
    done = client.post(
        "/api/review/decide", json={"item_id": item["id"], "decision": "approved", "note": "Đồng ý"}
    ).json()
    assert done["status"] == "approved"
