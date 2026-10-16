"""The client-data barrier (BRD-NFR-08, BRD_REMAINING_PLAN G2), proven at the wire: every model resource points at a
recording OpenAI-compatible server on this machine — the outside providers by the host ``localhost``, the bank's
own model (``llm:onprem``) by ``127.0.0.1`` — and each test reads what reached it.

- ``off``: reading a statement and the declaring chat send nothing at all; a call carrying a client's name or
  account number is refused before it is sent, by every path (LLMOp, the agent, the CIO agent's ``call_model``
  with another model name than the resource's); a call without client data still goes out.
- ``onprem``: the two client steps reach only the on-premises host; take that host off the allow-list and the
  chat is refused and the rules answer, with nothing sent.
- ``demo`` (the public demo, ADR-0018): unchanged — the client steps reach the outside model.
"""

import asyncio
import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from operonx import Operon
from operonx.core.registry import ResourceHub

from control import barrier, config
from declare.graph import declare_flow
from statements.graph import statement_flow
from views import agents
from wealth.paths import DATA

REPLY = '{"holdings": [{"type": "cash", "name": "Tiền", "balance": 1000000}]}'


class Wire(BaseHTTPRequestHandler):
    seen: list = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Wire.seen.append({"host": self.headers["Host"].split(":")[0], "body": body})
        msg = {"role": "assistant", "content": REPLY}
        out = {
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": body["model"],
            "choices": [{"index": 0, "message": msg, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        if body.get("stream"):
            chunk = {**out, "object": "chat.completion.chunk"}
            chunk["choices"] = [{"index": 0, "delta": msg, "finish_reason": "stop"}]
            data = f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
        else:
            data = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture
def wire(tmp_path, monkeypatch):
    server = ThreadingHTTPServer(("127.0.0.1", 0), Wire)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    outside, inside = f"http://localhost:{port}/v1", f"http://127.0.0.1:{port}/v1"
    res = tmp_path / "resources.yaml"
    res.write_text(
        "".join(
            f"llm:{k}:\n  api_type: openai\n  api_key: test\n  base_url: {url}\n  model: {model}\n  max_retries: 0\n"
            for k, url, model in [
                ("assistant", outside, "assistant-m"),
                ("cio", outside, "cio-in-yaml"),  # the configured model differs: views/agents._llm builds a client
                ("challenger", outside, "challenger-m"),
                ("copilot", outside, "copilot-m"),
                ("onprem", inside, "onprem-m"),
            ]
        )
    )
    for k, v in {
        "MF_AI": "on",
        "LLM_API_KEY": "test",
        "LLM_ONPREM_MODEL": "onprem-m",
        "LLM_MODEL_CIO": "cio-m",
        "LLM_MODEL_CHALLENGER": "challenger-m",
    }.items():
        monkeypatch.setenv(k, v)
    previous = ResourceHub._instance
    ResourceHub.set_instance(ResourceHub.from_yaml(res))
    agents._LLMS.clear()
    installed = "remove" in barrier._INSTALLED  # app/main.py installed it in this process
    barrier.install()
    Wire.seen = []
    try:
        yield Wire.seen
    finally:
        if not installed:
            barrier.uninstall()
        agents._LLMS.clear()
        ResourceHub._instance = previous
        server.shutdown()


def client_ai(mode, hosts=("127.0.0.1",)):
    vid = config.propose("client_ai", {"mode": mode, "onprem_hosts": list(hosts)}, "admin")["id"]
    config.decide(vid, "approve", "admin2")


def statement():
    raw = (DATA / "samples" / "vps_C01.csv").read_bytes()
    out = asyncio.run(
        Operon(statement_flow, params={"client_id": None, "filename": None, "content": None}).run(
            inputs={"client_id": "C01", "filename": "vps_C01.csv", "content": base64.b64encode(raw).decode()}
        )
    )
    return out["saved"] if "saved" in out else out


def chat(message, session="t"):
    out = asyncio.run(
        Operon(declare_flow, params={"client_id": None, "message": None, "session_id": None}).run(
            inputs={"client_id": "C01", "message": message, "session_id": f"C01-{session}"}
        )
    )
    return out["turn"]


def cio(user):
    return asyncio.run(agents.call_model("cio", "Bạn là CIO.", user, 50))


def refused():
    """The CIO agent's call fails its run with the barrier's reason (views/agents.AgentError wraps it)."""
    return pytest.raises((barrier.ClientDataRefused, agents.AgentError), match="NFR-08")


NAMED = "Khách Nguyen Minh Khoa, tài khoản 1902-CASA-01, hỏi về lãi suất."


def test_the_shipped_setting_is_the_demo_and_a_bad_one_is_refused():
    assert config.data("client_ai") == {"mode": "demo", "onprem_hosts": ["localhost", "127.0.0.1"]}
    assert config.KINDS["client_ai"]["two_person"] and config.KINDS["client_ai"]["owner"] == "admin"
    for bad in (
        {"mode": "cloud", "onprem_hosts": []},
        {"mode": "onprem", "onprem_hosts": []},
        {"mode": "off", "onprem_hosts": ["http://x"]},
        {"mode": "off"},
    ):
        with pytest.raises(ValueError):
            config.propose("client_ai", bad, "admin")


def test_off_sends_nothing_from_the_client_steps_and_refuses_client_data_on_every_path(wire):
    client_ai("off")
    statement()
    turn = chat("Tôi có 10 lượng vàng")
    assert turn["method"] == "rules"
    assert wire == []  # the two client steps took their rule path
    with refused():
        cio(NAMED)  # the CIO agent's client (another model name than the resource's, built outside the hub)
    with refused():
        cio("Gia đình nguyễn minh an cần gì?")  # a dependent, accents and case as typed
    assert wire == []
    text, _ = cio("Lãi suất điều hành tháng này tăng 0,5 điểm.")
    assert text == REPLY and [w["host"] for w in wire] == ["localhost"]  # no client data: it goes out


def test_a_declared_dependent_becomes_an_identifier(wire):
    client_ai("off")
    from wealth import store

    store.add_profile("C01", "dependent", {"name": "Phạm Thị Lan", "relation": "Mẹ", "via": "chat"})
    with refused():
        cio("Bà Pham Thi Lan nên làm gì?")
    assert wire == []


def test_onprem_reaches_only_the_bank_host_and_without_it_on_the_list_nothing_leaves(wire):
    client_ai("onprem")
    got = statement()
    turn = chat("Tôi có 10 lượng vàng, tên tôi là Nguyễn Minh Khoa")
    assert turn["method"] == "ai"
    assert wire and {w["host"] for w in wire} == {"127.0.0.1"}
    assert {w["body"]["model"] for w in wire} == {"onprem-m"}
    assert "vps_C01.csv" in json.dumps(wire[0]["body"], ensure_ascii=False) and got
    wire.clear()
    client_ai("onprem", hosts=("bank-llm.internal",))  # 127.0.0.1 is no longer the bank's
    turn = chat("Tôi có 10 lượng vàng", session="u")  # no identifier in it, and still nothing leaves
    assert turn["method"] == "rules"
    with pytest.raises(barrier.ClientDataRefused, match="onprem_hosts"):
        asyncio.run(ResourceHub.instance().get("llm:onprem").generate(messages=[{"role": "user", "content": "hi"}]))
    assert wire == []


def test_demo_is_unchanged(wire):
    chat("Tôi có 10 lượng vàng, tên tôi là Nguyễn Minh Khoa")
    assert {w["host"] for w in wire} == {"localhost"} and {w["body"]["model"] for w in wire} == {"assistant-m"}
    wire.clear()
    cio(NAMED)
    assert [w["host"] for w in wire] == ["localhost"]


def test_a_refusal_is_audited_without_the_identifiers(wire):
    from control import db

    client_ai("off")
    with refused():
        cio(NAMED)
    with db.tx() as con:
        rows = [dict(r) for r in con.execute("select action, object, data from audit_log where action = 'ai.refused'")]
    assert rows and rows[-1]["object"] == "llm:cio"
    assert "1902" not in rows[-1]["data"] and "Khoa" not in rows[-1]["data"]


def test_the_app_installs_the_barrier_on_every_model():
    from operonx.core.registry.guards import guards_for

    import app.main  # noqa: F401

    assert all(barrier.check in guards_for(f"llm:{k}") for k in ("assistant", "cio", "challenger", "copilot", "onprem"))
