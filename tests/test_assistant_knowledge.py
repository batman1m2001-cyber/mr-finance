"""Knowledge and the web (A5, assistant.md §6, ADR-0029/0030; OWN-AS-02, 07, 16, 17): the product guide answers how
to use the app with the page to open; a person's documents are read by them (and a client's RM) only, and deleted for
good; web search sends only the scrubbed question, cites its sources, states its certainty and is capped."""

import asyncio
import base64
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from operonx import Operon

from assistant import knowledge, registry, web
from assistant.base import ToolFailed
from assistant.graph import assistant_memory_flow
from control import db

ROOT = Path(__file__).resolve().parents[1]
MEM = Operon(
    assistant_memory_flow,
    params={
        k: None for k in ("action", "item_id", "text", "kind", "query", "role", "client_id", "file_name", "data", "key")
    },
)


def run(coro):
    return asyncio.run(coro)


def ctx(role="client", client_id="C01"):  # as the server builds it: the role's demo user when sign-in is off
    from assistant.ops import context, who

    return context({**who(role, client_id), "message": "", "route": "", "followed": None})


def tool(name, c, **args):
    return run(registry.REGISTRY[name].run(c, args))


def mem(action, role="client", client_id="C01", **kw):
    out = asyncio.run(MEM.run(inputs={"action": action, "role": role, "client_id": client_id, **kw}))
    if "$errors" in out:
        raise ValueError(next(iter(out["$errors"].values())).get("message"))
    return out["memory"]


# -- the product guide --------------------------------------------------------------------------------------------


def test_the_guide_answers_from_the_role_pages_with_the_page_to_open():
    out = tool("huong_dan", ctx("client"), q="quỹ khẩn cấp của tôi đủ dùng bao lâu")
    assert "Toàn cảnh" in out["text"] and "6 tháng" in out["text"]
    assert out["evidence"] == {"label": "Toàn cảnh", "route": "#/client/tong-quan/toan-canh"}
    assert out["sources"][0] == "Hướng dẫn sử dụng · Toàn cảnh"
    cio = tool("huong_dan", ctx("cio"), q="gộp tin thành sự kiện")
    routes = [p["route"] for p in cio["data"]["passages"] if p["route"]]
    assert routes and all(r.startswith("#/cio/") for r in routes)  # the CIO's pages, never a client's
    mine = tool("huong_dan", ctx("compliance"), q="làm sao để trợ lý quên điều nó nhớ")
    assert mine["evidence"]["route"] == "#/compliance/bo-nho"  # the shared page, at the person's own address


def test_the_guide_is_synced_once_and_an_unchanged_file_is_skipped():
    first = run(knowledge.sync_product())
    assert first["new"] + first["skip"] == len(list(knowledge.GUIDE.glob("*.md"))) + len(knowledge.GENERATED)
    assert run(knowledge.sync_product()) == {"new": 0, "update": 0, "skip": first["new"] + first["skip"], "deleted": 0}


def test_the_guide_also_answers_how_a_number_is_made_and_what_a_term_means():
    out = tool("huong_dan", ctx("client"), q="tài sản ròng được tính thế nào")
    assert "Cách tính · Tài sản ròng" in out["sources"] and "tổng nợ" in out["text"]
    term = tool("huong_dan", ctx("rm"), q="cú sốc lõi là gì")
    assert "Thuật ngữ · Cú sốc lõi (core shock)" in term["sources"]


def test_the_guide_finds_the_page_for_the_product_questions():
    """The 24 questions of data/assistant_guide_questions.json (paraphrased, some without accents), lexical search:
    measured 24/24 in the first three and 20/24 first (hybrid with embeddings: 21/24, one second more each)."""
    qs = json.loads((ROOT / "data" / "assistant_guide_questions.json").read_text(encoding="utf-8"))
    first = top3 = 0
    for q in qs:
        pages = [
            h["page"] for h in run(knowledge.guide(ctx(q["role"]), q["q"])) if h["file"] not in knowledge.GENERATED
        ]
        top3 += any(p.startswith(q["want"]) for p in pages)
        first += bool(pages) and pages[0].startswith(q["want"])
    assert top3 == len(qs) and first >= 20, (first, top3)


# -- a person's documents ------------------------------------------------------------------------------------------

NOTE = "# Hợp đồng bảo hiểm\n\nQuyền lợi nằm viện của gia đình: chi trả tối đa ba mươi ngày mỗi năm.\n"


def add(role="client", client_id="C01", name="bao-hiem.md", text=NOTE):
    return mem("material_add", role=role, client_id=client_id, file_name=name,
               data=base64.b64encode(text.encode()).decode())  # fmt: skip


def test_a_document_is_read_by_its_owner_and_their_rm_only():
    from people import store

    got = add()
    assert got["material"]["action"] == "new"
    found = tool("tai_lieu", ctx("client", "C01"), q="quyền lợi nằm viện")
    assert "ba mươi ngày" in found["text"] and found["sources"] == ["Tài liệu · bao-hiem.md"]
    assert "Không thấy" in tool("tai_lieu", ctx("client", "C02"), q="quyền lợi nằm viện")["text"]
    assert mem("materials", client_id="C02")["materials"] == []
    rm = ctx("rm", "C01")
    assert rm.user == store.assigned_rm("C01")  # the demo RM of sign-in off is C01's
    assert "ba mươi ngày" in tool("tai_lieu", rm, q="quyền lợi nằm viện")["text"]
    assert [m["own"] for m in mem("materials", role="rm", client_id="C01")["materials"]] == [False]
    assert "Không thấy" in tool("tai_lieu", ctx("cio"), q="quyền lợi nằm viện")["text"]


def test_only_the_owner_deletes_and_nothing_is_left():
    key = add()["material"]["key"]
    assert mem("material_delete", role="rm", client_id="C01", key=key)["deleted"] == 0
    assert mem("material_delete", key=key)["deleted"] == 1
    assert "Không thấy" in tool("tai_lieu", ctx(), q="quyền lợi nằm viện")["text"]
    base = knowledge.kb()
    assert base.document("materials", key) is None
    assert not any(b"ba m\xc6\xb0\xc6\xa1i" in p.read_bytes() for p in (knowledge.folder() / "blobs").rglob("*")
                   if p.is_file())  # fmt: skip
    with db.tx() as c:
        rows = c.execute("select action, data from audit_log where action like 'assistant.memory.material%'").fetchall()
    assert [r[0] for r in rows] == ["assistant.memory.material_add", "assistant.memory.material_delete"]
    assert all("ba mươi" not in str(r[1]) for r in rows)  # audited without the content


def test_what_is_not_a_document_is_refused():
    with pytest.raises(ValueError, match="Chỉ nhận tệp"):
        add(name="virus.exe")
    with pytest.raises(ValueError, match="5 MB"):
        add(text="x" * (5 * 1024 * 1024 + 1))


# -- the web -------------------------------------------------------------------------------------------------------


class FakeHub:
    def __init__(self):
        self.calls = []

    def get(self, key):
        assert key == "llm:copilot"
        return self

    async def generate(self, **kw):
        self.calls.append(kw)
        msg = SimpleNamespace(
            content="Theo các nguồn tìm được, lãi suất điều hành giữ nguyên. Mức độ chắc chắn: cao (hai nguồn khớp).",
            annotations=[{"type": "url_citation", "url_citation": {"url": "https://sbv.gov.vn/a", "title": "NHNN"}},
                         {"type": "url_citation", "url_citation": {"url": "https://vnexpress.net/b", "title": "VE"}}],
        )  # fmt: skip
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


@pytest.fixture
def online(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")
    hub = FakeHub()
    monkeypatch.setattr("operonx.providers.ops._utils.resolve_hub", lambda: hub)
    return hub


def test_the_web_gets_only_the_scrubbed_question_and_answers_with_sources(online):
    out = tool("tim_tren_web", ctx(), q="Nguyễn Minh Khoa hỏi lãi suất điều hành 2026 của NHNN, tài khoản 190212345678")
    sent = online.calls[0]
    question = sent["messages"][-1]["content"]
    assert "Khoa" not in question and "2026" not in question and "190212345678" not in question
    assert "NHNN" not in question and "lãi suất điều hành" in question
    assert sent["plugins"] == [{"id": "web", "max_results": 3}] and "extra_body" not in sent
    assert out["sources"] == ["https://sbv.gov.vn/a", "https://vnexpress.net/b"]
    assert out["text"].startswith("Theo các nguồn tìm được") and "Mức độ chắc chắn" in out["text"]


def test_the_web_is_capped_per_person_and_unavailable_without_a_model(online, monkeypatch):
    for _ in range(web.PER_PERSON):
        tool("tim_tren_web", ctx(), q="giá vàng thế giới hôm nay")
    with pytest.raises(ToolFailed, match="hết lượt"):
        tool("tim_tren_web", ctx(), q="giá vàng thế giới hôm nay")
    assert len(online.calls) == web.PER_PERSON
    tool("tim_tren_web", ctx("client", "C02"), q="giá vàng thế giới hôm nay")  # another person still may
    monkeypatch.setenv("MF_AI", "off")
    with pytest.raises(ToolFailed, match="chưa sẵn sàng"):
        tool("tim_tren_web", ctx("client", "C03"), q="giá vàng thế giới hôm nay")


def test_the_formula_or_term_asked_about_is_the_one_added():
    """data/assistant_reference_questions.json: 10 questions on a formula or a term, measured 10/10."""
    qs = json.loads((ROOT / "data" / "assistant_reference_questions.json").read_text(encoding="utf-8"))
    for q in qs:
        ref = [h["page"] for h in run(knowledge.guide(ctx(q["role"]), q["q"])) if h["file"] in knowledge.GENERATED]
        assert ref and ref[0].startswith(q["want"]), (q, ref)
