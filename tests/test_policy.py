"""The policy agent and the policy radar (BRD-FR-306, RULE-AI-01, F-D8; BRD completion F9): a document from the
Official Gazette or an official page, verified by a second Compliance person; the agent reads only verified text,
each point's quote is checked word for word inside the article it names, a failing answer is retried at most
twice; the agent sees no client data; the radar keeps each document's status history and what changed."""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from operonx.app import Application
from starlette.testclient import TestClient
from test_views import FakeLLM

from control import alerts, config, db, roles
from control.errors import BadRequest, Conflict
from policy import agent, source, store, text
from views import prompts
from wealth import fixtures

TEXT = (Path(__file__).parent / "data" / "policy" / "113-2026-VBHN-TT-NHNN.txt").read_text()
PAGE_URL = "https://congbao.chinhphu.vn/van-ban/van-ban-hop-nhat-so-113-2026-vbhn-tt-nhnn-470806.htm"
PDF_URL = "https://congbaocdn.chinhphu.vn/180507251028987904/2026/10/15/470806-signed.pdf"
PAGE = f"""<html><head><title>Văn bản hợp nhất số 113/2026/VBHN-TT-NHNN hợp nhất Thông tư Quy định về hoạt động tư
vấn của tổ chức tín dụng, chi nhánh ngân hàng nước ngoài</title></head><body><span>Ban hành: 13/10/2026</span>
<a href="https://elsewhere.example/x.pdf">x</a><a href="{PDF_URL}">PDF</a></body></html>"""


@pytest.fixture
def gazette(monkeypatch):
    """The gazette page and its PDF, as the gazette serves them; the PDF's text layer is the real document's."""
    asked = []

    def get(url):
        asked.append(url)
        return PAGE.encode() if url == PAGE_URL else b"%PDF-signed"

    monkeypatch.setattr(source, "pdf_text", lambda data: TEXT)
    return SimpleNamespace(get=get, asked=asked)


def added(gazette, by="cio"):
    return store.add({"gazette_url": PAGE_URL}, by, get_url=gazette.get)


def verified(gazette):
    d = added(gazette)
    return store.verify(d["id"], "cio2", "Đối chiếu với tệp PDF đã ký trên Công báo")


def summarise(doc_id, by="cio", mode=""):
    return asyncio.run(agent.summarise(doc_id, by, mode))


# -- the source ----------------------------------------------------------------------------------


def test_a_gazette_document_is_fetched_from_the_gazettes_own_signed_pdf(gazette):
    d = added(gazette)
    assert gazette.asked == [PAGE_URL, PDF_URL]  # not the off-site link
    assert d["number"] == "113/2026/VBHN-TT-NHNN" and d["issuer"] == "Ngân hàng Nhà nước Việt Nam"
    assert d["issued"] == "13/10/2026" and d["status"] == "issued" and d["fetched"] and len(d["file_sha256"]) == 64
    assert [a["label"] for a in d["articles"]][:3] == ["Điều 1", "Điều 2", "Điều 3"]
    with pytest.raises(Conflict, match="đã có"):
        added(gazette)
    with pytest.raises(BadRequest, match="Công báo"):
        store.add({"gazette_url": "https://example.com/van-ban/x.htm"}, "cio")


def test_a_pasted_document_needs_an_official_address_and_only_a_cio_adds(gazette):
    item = {"source_url": "https://blog.example.vn/du-thao", "title": "Dự thảo Thông tư sửa đổi", "status": "draft"}
    with pytest.raises(BadRequest, match="tên miền chính thức"):
        store.add(item, "cio")
    with pytest.raises(roles.Forbidden):
        added(gazette, by="rm01")
    d = store.add({**item, "source_url": "https://www.sbv.gov.vn/du-thao-1", "number": "x/2026/TT-NHNN"}, "cio")
    assert d["status"] == "draft" and d["text"] == "" and d["issuer"] == "Ngân hàng Nhà nước Việt Nam"
    with pytest.raises(Conflict, match="Chưa có văn bản"):
        store.verify(d["id"], "cio2", "Đối chiếu với trang nguồn của NHNN")


def test_a_second_cio_verifies_the_source(gazette):
    d = added(gazette)
    with pytest.raises(roles.Forbidden, match="khác người thêm"):
        store.verify(d["id"], "cio", "Đối chiếu với tệp PDF đã ký trên Công báo")
    with pytest.raises(BadRequest, match="20 ký tự"):
        store.verify(d["id"], "cio2", "ok")
    v = store.verify(d["id"], "cio2", "Đối chiếu với tệp PDF đã ký trên Công báo")["verified"]
    assert v["by"] == "cio2" and v["text_sha256"] == text.sha(TEXT)


# -- the check -----------------------------------------------------------------------------------


QUOTE5 = "Tổ chức tín dụng cung ứng dịch vụ tư vấn phải đảm bảo thực hiện các nguyên tắc sau:"
QUOTE1 = (
    "Thông tư này quy định việc thực hiện tư vấn về hoạt động ngân hàng và hoạt động kinh doanh khác của tổ chức tín "
    "dụng, chi nhánh ngân hàng nước ngoài."
)


def answer(**over):
    out = {
        "summary": "Thông tư quy định hoạt động tư vấn của tổ chức tín dụng: phạm vi, nguyên tắc và quy định nội bộ.",
        "points": [
            {"point": "Phạm vi điều chỉnh", "article": "Điều 1", "quote": QUOTE1},
            {"point": "Nguyên tắc tư vấn", "article": "Điều 5", "quote": QUOTE5},
        ],
    }
    out.update(over)
    return out


def test_the_check_takes_the_documents_own_words_inside_the_named_article_only():
    out, findings = text.check(TEXT, answer())
    assert findings == [] and out["points"][1]["article"] == "Điều 5"
    paraphrase = answer(
        points=[answer()["points"][0], {**answer()["points"][1], "quote": QUOTE5.replace("phải", "cần")}]
    )
    assert "không có nguyên văn" in text.check(TEXT, paraphrase)[1][0]
    elsewhere = answer(points=[answer()["points"][0], {**answer()["points"][1], "article": "Điều 7"}])
    assert "không nằm trong Điều 7" in text.check(TEXT, elsewhere)[1][0]
    family = answer(summary="Gia đình quý khách nên rà lại danh mục theo thông tư này ngay trong quý.")
    assert any("Không kết luận cho khách hàng" in f for f in text.check(TEXT, family)[1])
    assert "points: 2–6" in text.check(TEXT, answer(points=answer()["points"][:1]))[1][0]
    one_line = TEXT.replace(QUOTE5[:30], QUOTE5[:30].replace(" ", "\n", 2))  # a PDF line break inside the quote
    assert text.check(one_line, answer())[1] == []


# -- the agent ------------------------------------------------------------------------------------


def test_the_agent_reads_only_verified_text_and_mock_quotes_pass_the_check(gazette):
    d = added(gazette)
    with pytest.raises(Conflict, match="chưa được xác nhận"):
        summarise(d["id"])
    store.verify(d["id"], "cio2", "Đối chiếu với tệp PDF đã ký trên Công báo")
    with pytest.raises(roles.Forbidden):
        summarise(d["id"], by="rm01")
    s = summarise(d["id"])["summary"]
    assert s["mode"] == "mock" and s["attempts"] == 1 and len(s["points"]) >= 2
    assert "gồm 12 điều" in s["summary"]  # Điều 4 quoted again inside the amendment (Điều 11) is not a 13th
    assert all(text.norm(p["quote"]) in text.norm(TEXT) for p in s["points"])
    with db.tx() as con:
        row = con.execute("select agent, subject_id, data from agent_runs where id = ?", (s["run_id"],)).fetchone()
    assert (row["agent"], row["subject_id"]) == ("policy", d["id"]) and json.loads(row["data"])["status"] == "ok"


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_CIO", "vendor/big-model")
    monkeypatch.setenv("LLM_MODEL_CHALLENGER", "vendor/small-model")
    sent, replies = [], []

    def reply(system, news_ids):
        return json.dumps(replies.pop(0), ensure_ascii=False)

    llms = {"llm:cio": FakeLLM("vendor/big-model", sent, answer=reply)}
    import operonx.providers.ops._utils as hub_utils

    monkeypatch.setattr(hub_utils, "resolve_hub", lambda: SimpleNamespace(get=lambda key: llms[key]))
    return SimpleNamespace(sent=sent, replies=replies)


def test_live_a_paraphrased_quote_goes_back_with_why_and_no_client_data_reaches_the_model(gazette, live):
    d = verified(gazette)
    bad = answer(points=[answer()["points"][0], {**answer()["points"][1], "quote": QUOTE5.replace("phải", "cần")}])
    live.replies[:] = [bad, answer()]
    s = summarise(d["id"])["summary"]
    assert (s["mode"], s["model"], s["attempts"]) == ("live", "vendor/big-model", 2)
    assert s["prompt_version"] == "CF-prompts-v1"
    second = live.sent[1][1]["content"]
    assert "Lần trước chưa đạt" in second and "không có nguyên văn" in second
    seen = json.dumps(live.sent, ensure_ascii=False)
    assert "DỮ_LIỆU" in seen and "nguyên văn" in live.sent[0][0]["content"]
    for cid in fixtures.client_ids(members=True):
        c = fixtures.client(cid)
        assert c["name"] not in seen and f'"{cid}"' not in seen


def test_live_three_failing_answers_end_the_run_in_error_with_an_alert(gazette, live):
    d = verified(gazette)
    bad = answer(summary="Quý khách nên mua thêm trái phiếu ngay.")
    live.replies[:] = [bad, bad, bad]
    with pytest.raises(Conflict, match="sau 3 lần"):
        summarise(d["id"])
    assert store.get(d["id"])["summary"] is None
    assert any(a["kind"] == "agent" and a["key"] == "policy" for a in alerts.for_role("cio"))


# -- the radar ------------------------------------------------------------------------------------


def test_the_radar_keeps_each_documents_status_history_and_what_changed(gazette):
    draft = store.add(
        {"source_url": "https://www.sbv.gov.vn/du-thao-2", "title": "Dự thảo Thông tư về tư vấn", "status": "draft"},
        "cio",
    )
    with pytest.raises(BadRequest, match="10 ký tự"):
        store.set_status(draft["id"], "consultation", "cio", "ok")
    with pytest.raises(Conflict, match="đang"):
        store.set_status(draft["id"], "draft", "cio", "Vẫn là dự thảo trên trang NHNN")
    look = store.radar()["documents"][0]["changed_at"] + 0.001
    d = store.set_status(draft["id"], "consultation", "cio", "NHNN đăng lấy ý kiến trên trang", "20/10/2026")
    assert [h["status"] for h in d["history"]] == ["draft", "consultation"] and d["history"][-1]["date"] == "20/10/2026"
    other = added(gazette)
    r = store.radar(since=look)
    by = {x["id"]: x for x in r["documents"]}
    assert by[draft["id"]]["changed"] and by[other["id"]]["new"] and r["changed"] == 2
    assert r["counts"]["consultation"] == 1 and r["counts"]["issued"] == 1
    assert "text" not in by[other["id"]]
    with db.tx() as con:
        acts = [x[0] for x in con.execute("select action from audit_log where object = ? order by seq", (draft["id"],))]
    assert acts == ["policy.add", "policy.status"]


def test_the_policy_prompt_is_versioned_configuration():
    p = prompts.default()
    assert "DỮ_LIỆU" in p["policy"] and "nguyên văn" in p["policy"]
    with pytest.raises(ValueError, match="policy"):
        prompts.check({**p, "policy": "Tóm tắt văn bản này cho khách hàng một cách ngắn gọn."})
    prompts.check({k: v for k, v in p.items() if k != "policy"})  # a version kept before F9 stays valid
    assert config.data("prompts").get("policy") is None or "nguyên văn" in config.data("prompts")["policy"]


def test_the_endpoints(gazette, monkeypatch):
    monkeypatch.setattr(source, "_get", gazette.get)
    with TestClient(Application.find(".").asgi()) as c:
        r = c.post("/api/policy", json={"item": {"gazette_url": PAGE_URL}, "by": "cio"})
        assert r.status_code == 200, r.text
        did = r.json()["document"]["id"]
        r = c.post("/api/policy/summarise", json={"document_id": did, "by": "cio"})
        assert r.status_code == 409 and "xác nhận" in r.json()["error"]
        r = c.post(
            "/api/policy/verify", json={"document_id": did, "by": "cio2", "note": "Đối chiếu tệp PDF đã ký"}
        )
        assert r.status_code == 200, r.text
        r = c.post("/api/policy/summarise", json={"document_id": did, "by": "cio"})
        assert r.status_code == 200 and r.json()["document"]["summary"]["points"]
        r = c.post(
            "/api/policy/status",
            json={"document_id": did, "status": "effective", "by": "cio", "note": "Có hiệu lực theo điều khoản"},
        )
        assert r.status_code == 200 and r.json()["document"]["status"] == "effective"
        radar = c.get("/api/policy").json()
        assert radar["documents"][0]["id"] == did and radar["statuses"]["effective"] == "Có hiệu lực"
        assert c.get(f"/api/policy/{did}").json()["document"]["text"]


def test_a_cut_off_answer_fails_the_run_and_the_attempt_is_recorded(gazette, live, monkeypatch):
    from test_views import FakeLLM

    d = verified(gazette)
    cut = FakeLLM("vendor/big-model", live.sent, answer=lambda *a: "{", finish="length")
    import operonx.providers.ops._utils as hub_utils

    monkeypatch.setattr(hub_utils, "resolve_hub", lambda: SimpleNamespace(get=lambda key: cut))
    with pytest.raises(Conflict, match="bị cắt"):
        summarise(d["id"])
    with db.tx() as con:
        data = json.loads(con.execute("select data from agent_runs where agent = 'policy'").fetchone()[0])
    assert data["status"] == "error" and "bị cắt" in data["nodes"][0]["error"] and agent.MAX_TOKENS >= 6000
