"""Files and images in the assistant (docs/OCR_PLAN.md, ADR-0041): checked and read once at attach, kept 24 hours
for their owner only, carried into the turn as their reading (never the image), a file alone routing itself, and the
confirmed write saving what the confirm line showed, once however often it is attached. The model is a fake."""

import asyncio
import base64
import io
import json
import time

import pytest
from operonx import Operon
from operonx_agents.testing import ScriptedLLM, asks, says, scripted

from assistant import attachments as att
from assistant import ops, registry
from assistant.base import Ctx
from assistant.graph import assistant_attach_flow, assistant_flow
from wealth import store

INPUTS = ("message", "role", "client_id", "scope", "route", "goals", "turn_id", "approvals", "conversation_id",
          "attachments")  # fmt: skip
ASK = Operon(assistant_flow, params={k: None for k in INPUTS})
ATTACH = Operon(assistant_attach_flow, params={k: None for k in ("role", "client_id", "file_name", "data")})

RECEIPT = {  # what the fake model reads from a savings receipt photo
    "kind": "bien_lai", "title": "Biên lai gửi tiết kiệm", "institution": "Vietcombank",
    "summary": "Gửi 500 triệu kỳ hạn 6 tháng, lãi 5,2%/năm.", "fields": {"Số tiền": "500.000.000 VND"},
    "text": "BIÊN LAI GỬI TIỀN TIẾT KIỆM",
    "items": [{"type": "deposit", "name": "Tiền gửi 6 tháng", "balance": "500.000.000", "rate": 5.2,
               "maturity": "2027-04-15"}],
}  # fmt: skip


def ctx(role="client", client="C01"):
    return Ctx(role=role, client_id=client, scope="personal", question="", user=registry.DEMO_USER[role])


def jpeg(w=40, h=30) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (w, h), "white").save(buf, "JPEG")
    return buf.getvalue()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


@pytest.fixture
def model(monkeypatch):
    """The client model on, its reply ``RECEIPT``; ``seen`` records each call's images and text."""
    from wealth import ai

    seen = []

    async def fake(resource, name, text="", images=()):
        seen.append({"resource": resource, "name": name, "text": text, "images": list(images)})
        return json.loads(json.dumps(RECEIPT))

    monkeypatch.setattr(ai, "client_model", lambda: "assistant")
    monkeypatch.setattr(att, "ask_model", fake)
    return seen


def attach(name, raw, role="client", client_id="C01"):
    out = asyncio.run(ATTACH.run(inputs={"role": role, "client_id": client_id, "file_name": name, "data": b64(raw)}))
    if "$errors" in out:
        raise ValueError(next(iter(out["$errors"].values())).get("message"))
    return out["attachment"]["attachment"] if "attachment" in out["attachment"] else out["attachment"]


def ask(message=None, attachments=None, turn_id=None, approvals=None):
    inputs = {k: None for k in INPUTS}
    inputs.update({"message": message, "role": "client", "client_id": "C01", "scope": "personal",
                   "route": "#/client/tong-quan", "attachments": attachments, "turn_id": turn_id,
                   "approvals": approvals})  # fmt: skip
    out = asyncio.run(ASK.run(inputs=inputs))
    assert "$errors" not in out, out["$errors"]
    return out["assistant"]


# -- checked ------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name, content, why",
    [
        ("virus.exe", b64(b"x"), "Chưa đọc được loại tệp này"),
        ("anh.jpg", "không phải base64!", "không phải base64"),
        ("anh.jpg", "", "Tệp trống"),
        ("anh.jpg", b64(b"x" * (att.MAX_BYTES + 1)), "quá 5 MB"),
    ],
)
def test_a_file_the_assistant_does_not_take_is_refused_with_why(name, content, why):
    with pytest.raises(att.Refused, match=why):
        att.check(name, content)
    assert att.check("../../etc/anh.JPG", b64(b"ok")) == b"ok"  # the name's folder and case do not matter


# -- kept for its owner, 24 hours ---------------------------------------------------------------------------------


def test_a_file_is_its_owners_for_this_client_and_goes_after_24_hours(monkeypatch):
    monkeypatch.setenv("MF_DATA_KEYS", "k1=" + b64(bytes(range(32))))
    reading = att.checked(RECEIPT, "bien-lai.jpg")
    fid = att.put(ctx(), "bien-lai.jpg", b"\xff\xd8 photo", reading)
    got = att.get(ctx(), fid, content=True)
    assert got["content"] == b"\xff\xd8 photo" and got["reading"] == reading
    for other in (ctx(client="C02"), ctx("rm")):  # another client's chat, or the same client's RM
        with pytest.raises(att.Refused, match="hết hạn"):
            att.get(other, fid)
    with att.db() as con:  # sealed at rest: neither the bytes nor the reading are readable in the file
        row = dict(con.execute("select content, reading from attachments where id = ?", (fid,)).fetchone())
    assert b64(b"\xff\xd8 photo") not in row["content"] and "Vietcombank" not in row["reading"]
    assert att.sweep(time.time() + att.KEEP_S - 60) == 0
    assert att.sweep(time.time() + att.KEEP_S + 60) == 1
    with pytest.raises(att.Refused):
        att.get(ctx(), fid)


# -- the reader ---------------------------------------------------------------------------------------------------


def test_an_image_goes_to_the_model_as_one_jpeg_no_larger_than_2000px(model):
    got = asyncio.run(att.read("anh.png", jpeg(3000, 1000)))
    assert len(model) == 1 and model[0]["text"] == "" and len(model[0]["images"]) == 1
    from PIL import Image

    sent = Image.open(io.BytesIO(base64.b64decode(model[0]["images"][0].split(",", 1)[1])))
    assert sent.format == "JPEG" and max(sent.size) == att.LONG_SIDE
    # the reply in the one shape: the amount a number, the rate a fraction, the method said
    assert got["kind"] == "bien_lai" and got["method"] == "ai"
    assert got["items"] == [{"type": "deposit", "name": "Tiền gửi 6 tháng", "balance": 500_000_000.0,
                             "rate": pytest.approx(0.052), "maturity": "2027-04-15"}]  # fmt: skip


def scan(pages: int) -> bytes:
    """A scanned PDF: one photo a page, no text."""
    from PIL import Image

    imgs = [Image.new("RGB", (60, 80), (255, 255, 250 - n)) for n in range(pages)]
    buf = io.BytesIO()
    imgs[0].save(buf, "PDF", save_all=True, append_images=imgs[1:])
    return buf.getvalue()


def test_a_scanned_pdf_sends_its_first_10_pages_and_says_when_there_were_more(model):
    got = asyncio.run(att.read("sao-ke.pdf", scan(12)))
    assert len(model[0]["images"]) == att.SCAN_PAGES == 10
    assert got["summary"].endswith("(Đọc 10/12 trang đầu.)")
    assert asyncio.run(att.read("sao-ke.pdf", scan(2)))["summary"] == RECEIPT["summary"]
    assert len(model[1]["images"]) == 2


def test_an_image_without_a_model_allowed_to_read_it_is_refused(monkeypatch):
    from wealth import ai

    monkeypatch.setattr(ai, "client_model", lambda: None)
    with pytest.raises(att.Refused, match="cần mô hình AI"):
        asyncio.run(att.read("anh.jpg", jpeg()))
    with pytest.raises(att.Refused, match="Không mở được ảnh"):
        asyncio.run(att.read("anh.jpg", b"not an image"))


def test_a_statement_is_read_by_the_rules_without_a_model_and_when_the_model_fails(monkeypatch):
    from wealth import ai

    csv = "Mã CK,Số lượng,Giá vốn,Giá thị trường\nMWG,6000,52000,68000\n".encode()
    monkeypatch.setattr(ai, "client_model", lambda: None)
    got = asyncio.run(att.read("vps.csv", csv))
    assert got["method"] == "rules" and got["kind"] == "sao_ke"
    assert [(i["type"], i["ticker"], i["qty"]) for i in got["items"]] == [("stock", "MWG", 6000)]

    async def broken(*a, **k):
        raise TimeoutError("no answer")

    monkeypatch.setattr(ai, "client_model", lambda: "assistant")
    monkeypatch.setattr(att, "ask_model", broken)
    assert asyncio.run(att.read("vps.csv", csv))["items"] == got["items"]


def test_the_models_reading_is_kept_to_the_one_shape():
    got = att.checked({"kind": "thu_tinh", "fields": "not a dict", "items": [
        {"type": "deposit", "name": "Không có số"},  # no amount: dropped, never guessed
        {"type": "property", "name": "Căn hộ", "value": "8,5 tỷ", "purchase_year": 1800},
        {"type": "gold", "qty": "2.5"},
        {"type": "cash", "name": "Tài khoản", "balance": "120 triệu"},  # in words: still VND
        {"type": "holding", "class": "yacht", "name": "Du thuyền", "value": 1_000_000_000},
        {"type": "loan", "name": "Vay mua nhà", "value": 2_100_000_000, "rate": 9.5},
        "not an item",
    ]}, "x.jpg")  # fmt: skip
    assert got["kind"] == "khac" and got["title"] == "x.jpg" and got["fields"] == {}
    kinds = [i["type"] for i in got["items"]]
    assert kinds == ["cash", "property", "gold", "holding", "loan"]  # the statements' types first
    cash, prop, gold, other, loan = got["items"]
    assert cash["balance"] == 120_000_000
    assert prop["value"] == 8_500_000_000 and prop["purchase_year"] is None
    assert gold["qty"] == 2.5 and other["class"] == "other" and loan["rate"] == pytest.approx(0.095)


# -- in the turn --------------------------------------------------------------------------------------------------


def test_the_turn_carries_the_reading_and_a_file_alone_asks_for_its_write():
    f = {"id": "tep_1", "name": "bien-lai.jpg", "reading": att.checked(RECEIPT, "bien-lai.jpg")}
    alone = att.compose([f], "", True)
    assert alone.startswith("[Tệp đính kèm tep_1 · Biên lai · Vietcombank · bien-lai.jpg]")
    assert "tiền gửi “Tiền gửi 6 tháng” 500 triệu, 5,2%/năm, đáo hạn 15/04/2027" in alone
    assert alone.endswith("gọi them_tu_tep (tep=tep_1) để đề nghị ghi vào tài sản.")
    stock = {"type": "stock", "ticker": "MWG", "qty": 6000.0, "price": 68000.0}
    assert att._item_line(stock) == "cổ phiếu MWG 6.000 cp, giá 68.000"  # as a Vietnamese reader writes it
    assert att._item_line({"type": "gold", "qty": 2.5}) == "vàng 2,5 lượng"
    assert att._item_line({"type": "cash", "name": "Tiền", "balance": 120_000_000}).startswith("tiền 120")  # not named twice
    bill = {**f, "reading": {**f["reading"], "kind": "hoa_don", "items": []}}
    assert att.compose([bill], "", True).endswith("hỏi có muốn lưu vào Tài liệu không.")
    asked = att.compose([f], "Lãi bao nhiêu?", True)
    assert asked.endswith("[Hết tệp]\n\nLãi bao nhiêu?") and "them_tu_tep" not in asked
    # a model not allowed to read client data gets only what the file is
    assert att.compose([f], "Lãi bao nhiêu?", False) == "[Tệp đính kèm tep_1 · Biên lai · Vietcombank · bien-lai.jpg]\n\nLãi bao nhiêu?"
    assert att.shown([f], "") == "📎 bien-lai.jpg" and att.shown([f], "Lãi?") == "📎 bien-lai.jpg\nLãi?"


def test_a_request_takes_three_files_its_own_only_and_keeps_the_words_apart():
    fid = att.put(ctx(), "bien-lai.jpg", b"x", att.checked(RECEIPT, "bien-lai.jpg"))
    r = ops.request_of(role="client", client_id="C01", attachments=[fid])  # no words: still a question
    assert r["said"] == "" and r["message"] == "📎 bien-lai.jpg" and r["asked"].startswith("[Tệp đính kèm " + fid)
    assert r["files"] == [{"id": fid, "name": "bien-lai.jpg", "kind": "bien_lai"}]
    with pytest.raises(ValueError, match="tối đa 3 tệp"):
        ops.request_of(role="client", client_id="C01", attachments=[fid] * 4)
    with pytest.raises(att.Refused):
        ops.request_of(role="client", client_id="C02", attachments=[fid])
    with pytest.raises(ValueError, match="Hãy nhập câu hỏi"):
        ops.request_of(role="client", client_id="C01", attachments=[])


def test_without_the_model_a_file_is_described_from_its_reading():
    fid = att.put(ctx(), "bien-lai.jpg", b"x", att.checked(RECEIPT, "bien-lai.jpg"))
    r = ops.request_of(role="client", client_id="C01", attachments=[fid])

    async def run():
        return [e async for e in ops.fallback_events(r, "test")]

    out = asyncio.run(run())[-1]["result"]
    assert out["status"] == "ok" and out["steps"] == []
    assert out["text"].startswith("“bien-lai.jpg”: Biên lai · Vietcombank; 1 khoản ghi được vào tài sản.")


def test_a_photo_alone_ends_in_its_confirmed_write_saved_once_however_often_attached(model, monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")
    before = len(store.holdings("C01", "statement"))
    for n in range(2):  # the same receipt, attached and confirmed twice
        chip = attach("bien-lai.jpg", jpeg())
        assert chip["label"] == "Biên lai · Vietcombank" and chip["items"] == 1 and "text" not in chip
        llm = ScriptedLLM(asks(("them_tu_tep", {"tep": chip["id"]})), says("Đã ghi."))
        with scripted(copilot=llm):
            a = ask(attachments=[chip["id"]])
            assert a["status"] == "pending"
            assert "500 triệu" in a["waits"][0]["summary"] and "15/04/2027" in a["waits"][0]["summary"]
            sent = json.dumps(llm.requests[0]["messages"], ensure_ascii=False)
            assert "BIÊN LAI GỬI TIỀN TIẾT KIỆM" in sent and "base64" not in sent  # the reading, never the image
            done = ask(turn_id=a["turn_id"], approvals={a["waits"][0]["id"]: "approve"})
        assert done["status"] == "ok"
    mine = [h for h in store.holdings("C01", "statement") if h.get("file") == "bien-lai.jpg"
            or "bien-lai" in json.dumps(h, ensure_ascii=False)]  # fmt: skip
    assert len(store.holdings("C01", "statement")) - before == 1 and len(mine) == 1
    assert len(model) == 2  # read once per attach, never again at the write
