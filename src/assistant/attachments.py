"""Files and images given to the assistant (docs/OCR_PLAN.md, ADR-0041): attached, pasted or photographed in the panel.

A file is read once, when it arrives (O-D2), and kept with its reading for 24 hours (O-D8), sealed like the
conversation and owned by the person, their role and the client it was attached for. The turn reads the reading's
text, never the image (O-D4); the two writes (``them_tu_tep``, ``luu_tai_lieu``, assistant/filetools.py) save what
the person saw on the confirm line, because it is this reading and not a second one.

The reader (O-D3) is one model call on the client model (``wealth.ai.client_model``, BRD-NFR-08): an image, or a PDF
with no text (a scan, its first pages' images), goes as images; any other file as its text. Every reading has one
shape::

    {"kind": "sao_ke" | "bien_lai" | "hoa_don" | "tai_san" | "hop_dong_vay" | "khac", "title", "institution",
     "summary", "fields": {label: value}, "items": [...], "text", "method": "ai" | "rules"}

``items`` hold the statements' types (``stock``, ``cash``, ``deposit``; statements/_parse.py) and the declare
writers' (``property``, ``gold``, ``holding``, ``loan``; declare/tools.py), in VND. With no client model a table is
read by the statement rules and an image is refused (O-D7).
"""

from __future__ import annotations

import base64
import binascii
import io
import json
import os
import re
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from operonx.core.loggings import LOGGER

from assistant import conversations as conv
from assistant.base import Ctx
from control import crypto
from control.errors import BadRequest
from statements import _parse
from wealth.text import number

MAX_BYTES = 5 * 1024 * 1024
KEEP_S = 24 * 3600.0  # O-D8
IMAGES = (".jpg", ".jpeg", ".png", ".webp")
TABLES = (".pdf", ".xlsx", ".xlsm", ".csv", ".txt")
DOCUMENTS = (".docx", ".pptx", ".md", ".html", ".htm")
KINDS = IMAGES + TABLES + DOCUMENTS
SCAN_CHARS = 50  # a PDF with less text than this is a scan
SCAN_PAGES = 3
LONG_SIDE = 2000  # px: what the browser sends (O-D1); a larger image from elsewhere is shrunk here
TEXT_CHARS = 4000  # of the transcription kept
READ_CHARS = 20_000  # of a file's text sent to the model
READ_TOKENS = 2500
NAMES = {
    "sao_ke": "Sao kê",
    "bien_lai": "Biên lai",
    "hoa_don": "Hoá đơn",
    "tai_san": "Mô tả tài sản",
    "hop_dong_vay": "Hợp đồng vay",
    "khac": "Tệp khác",
}
NO_MODEL = "Ảnh cần mô hình AI đọc; chế độ hiện tại không gửi dữ liệu khách hàng cho mô hình."
GONE = "Tệp này đã hết hạn (giữ 24 giờ) hoặc không thuộc về bạn; hãy đính kèm lại."
SCHEMA = """
create table if not exists attachments (id text primary key, owner text not null, role text not null,
    client_id text, name text not null, created real not null, content text not null, reading text not null);
create index if not exists attachments_created on attachments (created);
"""

PROMPT = """Bạn đọc giấy tờ tài chính của khách hàng Việt Nam (ảnh chụp, ảnh màn hình, bản scan hay tệp) và trả lời \
bằng MỘT khối JSON, không gì khác:
{"kind": "sao_ke | bien_lai | hoa_don | tai_san | hop_dong_vay | khac",
 "title": "tên giấy tờ như ghi trên đó", "institution": "tên ngắn thường gọi của nơi phát hành (Vietcombank, VPS, EVN), nếu có",
 "summary": "2-3 câu: đây là gì, của ai, các con số chính",
 "fields": {"nhãn": "giá trị như ghi"},
 "items": [...],
 "text": "toàn bộ chữ đọc được, theo thứ tự, tối đa 4000 ký tự"}

kind: sao_ke = sao kê tài khoản / danh mục chứng khoán; bien_lai = biên lai, sổ / giấy xác nhận tiền gửi, chứng từ \
giao dịch; hoa_don = hoá đơn phải trả (điện, nước, học phí…); tai_san = mô tả / định giá / giấy chứng nhận tài sản \
(nhà, đất, xe, vàng, bảo hiểm, cổ phần); hop_dong_vay = hợp đồng / thông báo khoản vay; khac = mọi thứ khác (biểu đồ, \
ảnh chụp không phải giấy tờ): mô tả nó trong summary.

items: chỉ những tài sản hay khoản nợ của khách mà giấy tờ ghi rõ, mỗi khoản một dòng, số tiền bằng đồng (VND), \
số không có dấu phân cách:
{"type": "stock", "ticker": "MWG", "qty": 6000, "avg_price": 52000, "price": 68000}
{"type": "cash", "name": "Tiền trên tài khoản", "balance": 120000000}
{"type": "deposit", "name": "Tiền gửi 6 tháng", "balance": 500000000, "rate": 5.2, "maturity": "2027-04-15"}
{"type": "property", "name": "Căn hộ Thảo Điền", "location": "Thảo Điền, TP Thủ Đức, TP.HCM", "sqm": 95, \
"value": 8500000000, "purchase_year": 2019, "purchase_price": 5200000000, "rental_monthly": 0}
{"type": "gold", "qty": 2.5}   (lượng; 1 chỉ = 0,1 lượng)
{"type": "holding", "class": "business | insurance | crypto | other", "name": "30% cổ phần Công ty ABC", \
"value": 3000000000}
{"type": "loan", "name": "Vay mua nhà Vietcombank", "value": 2100000000, "monthly_payment": 25000000, "rate": 9.5}
Hoá đơn phải trả không phải tài sản: items rỗng, số tiền và hạn trả ghi trong fields. Ngày trong items theo \
YYYY-MM-DD. Không đoán: thiếu số thì bỏ khoản đó; chữ không đọc được thì ghi [không rõ]."""


class Refused(BadRequest):
    """A file the assistant does not take: 400, said to the person as it is."""


# -- the store --------------------------------------------------------------------------------------------------


_READY: set = set()


@contextmanager
def db() -> Iterator:
    with conv.db() as con:
        p = str(conv.db_path())
        if p not in _READY:
            con.executescript(SCHEMA)
            _READY.add(p)
        yield con


def put(ctx: Ctx, name: str, raw: bytes, reading: Dict[str, Any]) -> str:
    """Keep a file and its reading; its id."""
    fid = "tep_" + uuid.uuid4().hex[:10]
    content = base64.b64encode(raw).decode("ascii")
    with db() as con:
        con.execute(
            "insert into attachments values (?, ?, ?, ?, ?, ?, ?, ?)",
            (fid, conv.owner(ctx), ctx.role, ctx.client_id, name, time.time(),
             crypto.seal(content, crypto.where("attachments", fid, "content")),
             crypto.seal(json.dumps(reading, ensure_ascii=False), crypto.where("attachments", fid, "reading"))),
        )  # fmt: skip
    return fid


def get(ctx: Ctx, fid: str, content: bool = False) -> Dict[str, Any]:
    """One of the person's files, attached in this role for this client in the last 24 hours: ``{id, name, created,
    reading}`` and, with ``content``, its bytes. Anyone else's, or an expired one, is ``GONE``."""
    fid = str(fid or "").strip()
    with db() as con:
        row = con.execute(
            "select * from attachments where id = ? and owner = ? and role = ? and coalesce(client_id, '') = ?"
            " and created >= ?",
            (fid, conv.owner(ctx), ctx.role, ctx.client_id or "", time.time() - KEEP_S),
        ).fetchone()
    if row is None:
        raise Refused(GONE)
    out = {
        "id": fid,
        "name": row["name"],
        "created": row["created"],
        "reading": json.loads(crypto.open_(row["reading"], crypto.where("attachments", fid, "reading"))),
    }
    if content:
        out["content"] = base64.b64decode(crypto.open_(row["content"], crypto.where("attachments", fid, "content")))
    return out


def sweep(now: Optional[float] = None) -> int:
    """Delete what is older than 24 hours (assistant/retention.py)."""
    now = time.time() if now is None else now
    with db() as con:
        return con.execute("delete from attachments where created < ?", (now - KEEP_S,)).rowcount


# -- the reader ---------------------------------------------------------------------------------------------------


def suffix(name: str) -> str:
    return Path(str(name or "")).suffix.lower()


def check(name: str, content: str) -> bytes:
    """The file's bytes, or ``Refused`` with why."""
    name = Path(str(name or "")).name
    if suffix(name) not in KINDS:
        raise Refused(f"Chưa đọc được loại tệp này; nhận ảnh ({', '.join(IMAGES)}), sao kê ({', '.join(TABLES)}) "
                      f"và tài liệu ({', '.join(DOCUMENTS)}).")  # fmt: skip
    try:
        raw = base64.b64decode(str(content or ""), validate=True)
    except (binascii.Error, ValueError) as e:
        raise Refused("Tệp gửi lên bị hỏng (không phải base64).") from e
    if not raw:
        raise Refused("Tệp trống.")
    if len(raw) > MAX_BYTES:
        raise Refused("Tệp quá 5 MB.")
    return raw


def vision_model() -> Optional[str]:
    """The client model when it may read an image: the demo's; on-prem only with ``LLM_ONPREM_VISION=1``, as no
    on-prem vision model has been measured (O-D7)."""
    from wealth import ai

    use = ai.client_model()
    if use == "onprem" and (os.environ.get("LLM_ONPREM_VISION") or "").strip() != "1":
        return None
    return use


def _jpeg(img) -> str:
    """An image as a JPEG data URL, at most ``LONG_SIDE`` on its long side."""
    img = img.convert("RGB")
    if max(img.size) > LONG_SIDE:
        img.thumbnail((LONG_SIDE, LONG_SIDE))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def image_urls(name: str, raw: bytes) -> List[str]:
    from PIL import Image, UnidentifiedImageError

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError) as e:
        raise Refused("Không mở được ảnh này; hãy chụp lại hoặc gửi JPEG / PNG.") from e
    return [_jpeg(img)]


def scan_urls(raw: bytes) -> List[str]:
    """The largest image of each of a scanned PDF's first pages."""
    from pypdf import PdfReader

    out = []
    for page in PdfReader(io.BytesIO(raw)).pages[:SCAN_PAGES]:
        try:
            imgs = [im.image for im in page.images]
        except Exception as e:  # noqa: BLE001 — an image pypdf cannot decode: that page is skipped
            LOGGER.warning(f"[attach] a scanned page's image could not be read: {type(e).__name__}")
            continue
        imgs = [im for im in imgs if im is not None]
        if imgs:
            out.append(_jpeg(max(imgs, key=lambda im: im.size[0] * im.size[1])))
    return out


def document_text(name: str, raw: bytes) -> str:
    """A Word, PowerPoint, Markdown or HTML file's text, as Tài liệu reads it (operonx-kb's parsers)."""
    from operonx_kb.parsing.router import ParserRouter

    doc = ParserRouter().for_file(raw, name=name).parse(raw, name=name)
    lines = []
    for b in doc.blocks:
        rows = (b.attrs or {}).get("rows") if b.kind == "table" else None
        lines.extend(" | ".join(str(c) for c in r) for r in rows) if rows else lines.append(b.text)
    return "\n".join(t for t in lines if t and t.strip())


def _json(text: str) -> Dict[str, Any]:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("no JSON object in the reply")
    out = json.loads(m.group(0))
    if not isinstance(out, dict):
        raise ValueError("the reply is not an object")
    return out


def _amount(v: Any) -> Optional[float]:
    n = number(v)
    return n if n and n > 0 else None


MONEY = ("balance", "value", "purchase_price", "monthly_payment", "rental_monthly", "price", "avg_price")


def _in_vnd(it: Any) -> Any:
    """An item whose amounts the model wrote in words ("8,5 tỷ", "500 triệu") with them in VND, as ``number`` would
    read "8,5" alone."""
    from declare._rules import money

    if not isinstance(it, dict):
        return it
    return {k: (money(v) or [v])[0] if k in MONEY and isinstance(v, str) else v for k, v in it.items()}


def clean_items(items: Any) -> List[Dict[str, Any]]:
    """The statements' items through their own checks; the declared ones kept only with their amount."""
    items = [_in_vnd(it) for it in items] if isinstance(items, list) else items
    out = _parse.clean_items(items)
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        kind = str(it.get("type") or "").lower()
        name = str(it.get("name") or "").strip()[:120]
        if kind == "property" and (value := _amount(it.get("value")) or _amount(it.get("purchase_price"))):
            year = number(it.get("purchase_year"))
            out.append({"type": "property", "name": name or "Bất động sản",
                        "location": str(it.get("location") or "").strip()[:160], "sqm": _amount(it.get("sqm")),
                        "value": _amount(it.get("value")) or value, "purchase_price": _amount(it.get("purchase_price")),
                        "purchase_year": int(year) if year and 1950 < year < 2100 else None,
                        "rental_monthly": _amount(it.get("rental_monthly")) or 0})  # fmt: skip
        elif kind == "gold" and (qty := _amount(it.get("qty"))):
            out.append({"type": "gold", "qty": qty})
        elif kind == "holding" and (value := _amount(it.get("value"))):
            cls = str(it.get("class") or "other").lower()
            out.append({"type": "holding", "class": cls if cls in ("business", "insurance", "crypto") else "other",
                        "name": name or "Tài sản khác", "value": value})  # fmt: skip
        elif kind == "loan" and (value := _amount(it.get("value"))):
            rate = number(it.get("rate"))
            out.append({"type": "loan", "name": name or "Khoản vay", "value": value,
                        "monthly_payment": _amount(it.get("monthly_payment")) or 0,
                        "rate": rate / 100 if rate and rate > 1 else rate})  # fmt: skip
    return out


def checked(got: Dict[str, Any], name: str, institution: str = "") -> Dict[str, Any]:
    """The model's reading in the one shape: a kind outside the list is ``khac``, an item without its amount goes."""
    kind = str(got.get("kind") or "").strip().lower()
    fields = got.get("fields") if isinstance(got.get("fields"), dict) else {}
    return {
        "kind": kind if kind in NAMES else "khac",
        "title": str(got.get("title") or name).strip()[:160],
        "institution": str(got.get("institution") or institution or "").strip()[:80],
        "summary": str(got.get("summary") or "").strip()[:600],
        "fields": {str(k)[:60]: str(v)[:200] for k, v in list(fields.items())[:24]},
        "items": clean_items(got.get("items")),
        "text": str(got.get("text") or "").strip()[:TEXT_CHARS],
        "method": "ai",
    }


async def ask_model(resource: str, name: str, text: str = "", images: List[str] = ()) -> Dict[str, Any]:
    """One call: the file's text or its images in, the reading's JSON out (reasoning off, temperature 0)."""
    from operonx.providers.ops._utils import resolve_hub

    parts: List[Dict[str, Any]] = [{"type": "text", "text": f"Tệp {name}:" + (f"\n\n{text[:READ_CHARS]}" if text else "")}]
    parts += [{"type": "image_url", "image_url": {"url": u}} for u in images]
    extra = {"reasoning": {"enabled": False}} if resource == "assistant" else {}  # an on-prem server may refuse it
    t0 = time.perf_counter()
    resp = await resolve_hub().get(f"llm:{resource}").generate(
        messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": parts}],
        temperature=0,
        max_tokens=READ_TOKENS,
        **extra,
    )
    usage = getattr(resp, "usage", None)
    LOGGER.info(f"[attach] read {suffix(name)} images={len(images)} in {time.perf_counter() - t0:.1f}s "
                f"tokens={getattr(usage, 'prompt_tokens', '?')}/{getattr(usage, 'completion_tokens', '?')} "
                f"cost={getattr(usage, 'cost', '?')}")  # fmt: skip
    return _json(resp.choices[0].message.content)


def by_rules(name: str, kind: str, text: str, rows: list) -> Dict[str, Any]:
    """No model: the statement rules' items (a table), and the file's own text."""
    items = _parse.rule_items(kind, text, rows) if kind in ("csv", "xlsx", "pdf", "txt") else []
    inst = _parse.institution(text)
    return {
        "kind": "sao_ke" if items else "khac",
        "title": name,
        "institution": inst,
        "summary": f"Đọc theo quy tắc: {len(items)} khoản." if items else "",
        "fields": {},
        "items": items,
        "text": text.strip()[:TEXT_CHARS],
        "method": "rules",
    }


async def read(name: str, raw: bytes) -> Dict[str, Any]:
    """A file's reading (O-D2, O-D3)."""
    ext = suffix(name)
    images: List[str] = []
    text, kind, rows = "", "txt", []
    if ext in IMAGES:
        images = image_urls(name, raw)
    elif ext in TABLES:
        kind, text, rows = _parse.read_file(name, raw)
        if ext == ".pdf" and len(text.strip()) < SCAN_CHARS:
            images = scan_urls(raw)
            if not images:
                raise Refused("PDF này không có chữ cũng không có ảnh trang nào đọc được.")
    else:
        text = document_text(name, raw)
    if images:
        use = vision_model()
        if use is None:
            raise Refused(NO_MODEL)
        try:
            return checked(await ask_model(use, name, images=images), name)
        except Exception as e:  # noqa: BLE001 — nothing else reads an image
            LOGGER.warning(f"[attach] the image could not be read: {type(e).__name__}: {e}")
            raise Refused("Chưa đọc được ảnh lúc này (mô hình không trả lời); hãy thử lại.") from e
    from wealth import ai

    use = ai.client_model()
    if use is not None and text.strip():
        try:
            got = checked(await ask_model(use, name, text=text), name, _parse.institution(text))
            if not got["items"] and rows:  # a table the model found nothing in: the rules may
                got["items"] = _parse.rule_items(kind, text, rows)
            return got
        except Exception as e:  # noqa: BLE001 — the model unreachable or its reply unreadable: the rules read it
            LOGGER.warning(f"[attach] the model's reading failed, rules instead: {type(e).__name__}: {e}")
    return by_rules(name, kind, text, rows)


def label(reading: Dict[str, Any]) -> str:
    """What the chip and the turn call it: "Biên lai · Vietcombank"."""
    return " · ".join(x for x in (NAMES.get(reading.get("kind"), "Tệp"), reading.get("institution")) if x)


def view(f: Dict[str, Any]) -> Dict[str, Any]:
    """What the panel gets back: the id, the label, the summary and how many items; never the text."""
    r = f["reading"]
    return {"id": f["id"], "name": f["name"], "kind": r["kind"], "label": label(r), "summary": r["summary"],
            "items": len(r["items"]), "method": r["method"]}  # fmt: skip


# -- the turn (O-D4, O-D5) ------------------------------------------------------------------------------------------

ONLY_FILE = "Người dùng gửi tệp này, không kèm câu hỏi."
MAX_FILES = 3


def _day(iso: Any) -> str:
    """2027-04-15 as 15/04/2027; anything else as it is."""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(iso))
    return f"{m[3]}/{m[2]}/{m[1]}" if m else str(iso)


def _item_line(it: Dict[str, Any]) -> str:
    from wealth.money import _vn, pct, vnd

    t = it["type"]
    if t == "stock":
        return f"cổ phiếu {it['ticker']} {_vn(it['qty'], 0)} cp" + (f", giá {_vn(it['price'], 0)}" if it.get("price") else "")
    if t in ("cash", "deposit"):
        rate = f", {pct(it['rate'], digits=2)}/năm" if it.get("rate") else ""
        due = f", đáo hạn {_day(it['maturity'])}" if it.get("maturity") else ""
        kind = "tiền gửi" if t == "deposit" else "tiền"
        name = "" if (it.get("name") or "").strip().lower() in ("", kind, "tiền", "tiền mặt", "cash") else f" “{it['name']}”"
        return f"{kind}{name} {vnd(it['balance'])}{rate}{due}"
    if t == "gold":
        return f"vàng {_vn(it['qty'], 2)} lượng"
    if t == "loan":
        return f"khoản vay “{it['name']}” dư nợ {vnd(it['value'])}"
    return f"{'bất động sản' if t == 'property' else 'tài sản'} “{it['name']}” {vnd(it['value'])}"


def block(f: Dict[str, Any], reads: bool) -> str:
    """One file as the turn's message carries it. Without a model allowed to read client data, only what it is."""
    r = f["reading"]
    head = f"[Tệp đính kèm {f['id']} · {label(r)} · {f['name']}]"
    if not reads:
        return head
    lines = [head]
    if r["summary"]:
        lines.append(f"Tóm tắt: {r['summary']}")
    if r["fields"]:
        lines.append("Thông tin: " + "; ".join(f"{k}: {v}" for k, v in r["fields"].items()))
    if r["items"]:
        lines.append(f"Khoản ghi được vào tài sản ({len(r['items'])}): " + "; ".join(f"{n}) {_item_line(it)}" for n, it in enumerate(r["items"], 1)))
    else:
        lines.append("Không có khoản nào ghi được vào tài sản.")
    if r["text"]:
        lines.append(f"Nội dung đọc được:\n{r['text']}")
    lines.append("[Hết tệp]")
    return "\n".join(lines)


def alone(files: List[Dict[str, Any]]) -> str:
    """What a file sent with no words asks (O-D5): say what it is, then propose its write, or keeping it."""
    rows = [f for f in files if f["reading"]["items"]]
    if not rows:
        return f"{ONLY_FILE} Nói ngắn đó là gì, rồi hỏi có muốn lưu vào Tài liệu không."
    ids = ", ".join(f["id"] for f in rows)
    return f"{ONLY_FILE} Nói ngắn đó là gì và các con số chính, rồi gọi them_tu_tep (tep={ids}) để đề nghị ghi vào tài sản."


def compose(files: List[Dict[str, Any]], message: str, reads: bool) -> str:
    """The turn's message: every file's block, then the question (an image alone is still one, O-D5)."""
    return "\n\n".join([block(f, reads) for f in files] + [message or alone(files)])


def described(files: List[Dict[str, Any]]) -> str:
    """The keyword path's answer to a file (no model): what each one is, and how many items it has."""
    out = []
    for f in files:
        r = f["reading"]
        n = f"; {len(r['items'])} khoản ghi được vào tài sản" if r["items"] else ""
        out.append(f"“{f['name']}”: {label(r)}{n}." + (f" {r['summary']}" if r["summary"] else ""))
    return " ".join(out) + (" Trợ lý AI hiện không trả lời được nên chưa ghi hay lưu được tệp; bạn thử lại sau ít "
                            "phút, hoặc tải sao kê ở trang Tài sản.")  # fmt: skip


def shown(files: List[Dict[str, Any]], message: str) -> str:
    """The question as the conversation keeps and draws it: the files' names, then the words."""
    names = "📎 " + ", ".join(f["name"] for f in files)
    return f"{names}\n{message}" if message else names
