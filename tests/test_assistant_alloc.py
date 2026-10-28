"""The assistant on the BRDs' P2 (assistant/alloctools.py): the three buckets with the 11 classes, the allocations
waiting for the CIO, the event-type catalogue and the AI's goal labels — each says what its page shows."""

import asyncio

from operonx import Operon

from allocation.graph import allocation_send_flow
from assistant import registry
from assistant.base import Ctx, execute
from research import store as research_store

SEND = Operon(allocation_send_flow, params={"client_id": None, "by": None, "scope": None, "method": None, "assumptions": None})


def ask(name, role, client=None):
    c = Ctx(role=role, client_id=client, scope="family", question="", user=registry.DEMO_USER[role])
    return asyncio.run(execute(registry.REGISTRY[name], c, {}))


def test_the_buckets_and_the_eleven_classes_and_the_client_hears_no_unapproved_action():
    rm, client = ask("phan_bo_tai_san", "rm", "C01"), ask("phan_bo_tai_san", "client", "C01")
    for out in (rm, client):
        assert "Thanh khoản" in out["text"] and "Theo 11 loại tài sản" in out["text"] and out["data"]["eleven"]
    assert "việc đề xuất" in rm["text"] and "việc đề xuất" not in client["text"]  # Q-29


def test_the_cio_hears_what_waits_and_the_method():
    assert ask("phan_bo_cho_duyet", "cio")["data"]["waiting"] == 0
    sent = asyncio.run(SEND.run(inputs={"client_id": "C01", "by": "rm01"}))
    out = ask("phan_bo_cho_duyet", "cio")
    assert out["data"]["waiting"] == 1 and sent["review_id"] in out["text"] and out["data"]["method"] == "tilt"


def test_the_catalogue_says_which_types_have_precedents():
    out = ask("loai_su_kien", "cio")
    assert out["data"]["fed_hike"] >= 8 and "Fed tăng lãi suất" in out["text"].split("chưa có tiền lệ")[0]


def test_a_suggested_label_is_said_and_never_kept():
    out = ask("goi_y_nhan_muc_tieu", "rm", "C01")
    assert out["text"].startswith("Gợi ý của AI, chưa lưu") or "đã có nhãn" in out["text"]
    assert research_store.declared() == {}
