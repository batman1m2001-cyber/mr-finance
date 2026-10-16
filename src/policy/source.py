"""Where a policy document comes from (BRD-FR-306: “văn bản đã xác nhận nguồn”).

- **The Official Gazette** (``congbao.chinhphu.vn``): the server reads the document's page, takes the signed PDF it
  links on the gazette's own file host, extracts the text (pypdf) and keeps the PDF's SHA-256. The text is the
  source's, not anyone's copy.
- **Another official page** (a draft under consultation on a ministry's or the State Bank's site): the address must
  be on an official domain and the text is pasted; a second Compliance person confirms it matches the source.
"""

from __future__ import annotations

import hashlib
import html
import io
import re
import urllib.request
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

GAZETTE = "congbao.chinhphu.vn"
GAZETTE_FILES = ("congbaocdn.chinhphu.vn",)
OFFICIAL = (
    "chinhphu.vn",
    "sbv.gov.vn",
    "mof.gov.vn",
    "ssc.gov.vn",
    "quochoi.vn",
    "vbpl.vn",
    "moj.gov.vn",
    "mpi.gov.vn",
    "gso.gov.vn",
)
MAX_BYTES = 15_000_000
ISSUERS = {
    "NHNN": "Ngân hàng Nhà nước Việt Nam",
    "BTC": "Bộ Tài chính",
    "CP": "Chính phủ",
    "TTg": "Thủ tướng Chính phủ",
    "QH": "Quốc hội",
    "UBCKNN": "Ủy ban Chứng khoán Nhà nước",
    "BCT": "Bộ Công Thương",
    "BXD": "Bộ Xây dựng",
}


def issuer_of(number: str) -> str:
    """From the number's suffix: 113/2026/VBHN-TT-NHNN → Ngân hàng Nhà nước Việt Nam."""
    last = re.split(r"[-/]", str(number or ""))[-1:] or [""]
    return ISSUERS.get(last[0], "")


class SourceError(ValueError):
    pass


def official(url: str) -> bool:
    host = (urlparse(str(url or "")).hostname or "").lower()
    return urlparse(str(url or "")).scheme == "https" and any(host == d or host.endswith("." + d) for d in OFFICIAL)


def _get(url: str, timeout: float = 30.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (OneWealth demo; policy agent)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 — https on an official domain only
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SourceError("tệp quá lớn (trên 15 MB)")
    return data


def pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:  # noqa: BLE001 — any unreadable PDF is the source's problem, said plainly
        raise SourceError(f"không đọc được PDF: {type(exc).__name__}") from None


def gazette(url: str, get: Optional[Callable[[str], bytes]] = None) -> Dict[str, Any]:
    """A document from the Official Gazette: title, number, issue date, the signed PDF's address and hash, the text."""
    get = get or _get
    parts = urlparse(str(url or ""))
    if parts.scheme != "https" or (parts.hostname or "").lower() != GAZETTE or "/van-ban/" not in parts.path:
        raise SourceError(f"địa chỉ văn bản trên Công báo: https://{GAZETTE}/van-ban/…")
    try:
        page = get(url).decode("utf-8", errors="replace")
    except SourceError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise SourceError(f"không mở được trang Công báo: {type(exc).__name__}") from None
    title = re.search(r"<title>(.*?)</title>", page, re.S)
    title = " ".join(html.unescape(title.group(1)).split()) if title else ""
    title = re.sub(r"\s*[-|]\s*Công báo.*$", "", title, flags=re.I).strip()
    issued = re.search(r"Ban hành:\s*(\d{1,2}/\d{1,2}/\d{4})", re.sub(r"<[^>]+>", " ", page))
    number = re.search(r"(?i)số\s+([0-9]+/[0-9]{4}/[A-ZĐ0-9\-]+)", title)
    pdfs = [
        u
        for u in re.findall(r'href="(https://[^"]+?\.pdf)"', page)
        if (urlparse(u).hostname or "").lower() in GAZETTE_FILES
    ]
    if not pdfs:
        raise SourceError("trang Công báo không có tệp PDF đã ký")
    try:
        data = get(pdfs[0])
    except Exception as exc:  # noqa: BLE001
        raise SourceError(f"không tải được tệp PDF: {type(exc).__name__}") from None
    text = pdf_text(data)
    if len(" ".join(text.split())) < 200:
        raise SourceError("tệp PDF không có lớp chữ (ảnh quét?): dán văn bản và để người thứ hai xác nhận")
    return {
        "title": title[:300] or "Văn bản trên Công báo",
        "number": number.group(1) if number else "",
        "issuer": issuer_of(number.group(1)) if number else "",
        "issued": issued.group(1) if issued else "",
        "source_url": url,
        "file_url": pdfs[0],
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "text": text,
        "fetched": True,
    }
