"""The product over HTTP, in process: what the web page calls."""

import base64
from pathlib import Path

from starlette.testclient import TestClient

from operonx.app import Application

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"


def test_upload_then_chat_then_the_dashboard_shows_both():
    app = Application.find(".")
    with TestClient(app.asgi()) as client:
        before = client.post("/api/dashboard", json={"client_id": "C01"}).json()["net_worth"]["value"]
        content = base64.b64encode((SAMPLES / "vps_C01.csv").read_bytes()).decode()
        read = client.post("/api/statement", json={"client_id": "C01", "filename": "vps_C01.csv", "content": content})
        assert read.status_code == 200, read.text
        assert (read.json()["institution"], read.json()["count"]) == ("VPS", 3)
        turn = client.post("/api/declare", json={"client_id": "C01", "message": "Nhà tôi có 10 lượng vàng"}).json()
        assert turn["recorded"][0]["data"]["qty"] == 10
        after = client.post("/api/dashboard", json={"client_id": "C01"}).json()
        assert after["net_worth"]["value"] == before + read.json()["total"] + 10 * 150_000_000
        assert {s["source"]: s["status"] for s in after["sources"]}["statement"] == "connected"
        assert client.get("/samples/vps_C01.csv").status_code == 200
        assert (
            client.post("/api/statement", json={"client_id": "C01", "filename": "x.exe", "content": ""}).status_code
            == 500
        )
        assert client.post("/api/reset").json() == {"reset": True}
