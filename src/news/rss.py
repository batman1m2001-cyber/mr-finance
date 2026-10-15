"""RSS 2.0 and Atom → plain items: title, summary, link, published time.

Only the standard library: the feeds are small, and a bank machine installs nothing extra. The
quirks of the white-listed feeds are handled here: a byte-order mark before the XML declaration
(Fed), two-digit years in the date (CafeF), HTML and images inside the description (VnExpress,
Vietstock, CafeF), CDATA everywhere.
"""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional

MAX_BYTES = 2_000_000
SUMMARY_CHARS = 400
_ATOM = "{http://www.w3.org/2005/Atom}"
_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")


@dataclass
class Item:
    title: str
    summary: str
    link: str
    published: Optional[float]  # epoch seconds, None when the feed gives none we can read
    guid: str


class FeedError(ValueError):
    """A feed that is not RSS or Atom we can read."""


def parse(raw: bytes | str) -> List[Item]:
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise FeedError(f"feed larger than {MAX_BYTES} bytes")
    raw = raw.lstrip(b"\xef\xbb\xbf \t\r\n")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise FeedError(f"not XML: {exc}") from None
    if root.tag == "rss" or root.find("channel") is not None:
        return [_rss_item(el) for el in root.iter("item")]
    if root.tag == f"{_ATOM}feed":
        return [_atom_entry(el) for el in root.iter(f"{_ATOM}entry")]
    raise FeedError(f"unknown feed root <{root.tag}>")


def _rss_item(el: ET.Element) -> Item:
    link = _text(el, "link")
    return Item(
        title=clean(_text(el, "title")),
        summary=clean(_text(el, "description"), SUMMARY_CHARS),
        link=link,
        published=parse_time(_text(el, "pubDate")),
        guid=_text(el, "guid") or link,
    )


def _atom_entry(el: ET.Element) -> Item:
    link = ""
    for ln in el.findall(f"{_ATOM}link"):
        if ln.get("rel") in (None, "alternate"):
            link = ln.get("href") or ""
            break
    return Item(
        title=clean(_text(el, f"{_ATOM}title")),
        summary=clean(_text(el, f"{_ATOM}summary") or _text(el, f"{_ATOM}content"), SUMMARY_CHARS),
        link=link,
        published=parse_time(_text(el, f"{_ATOM}published") or _text(el, f"{_ATOM}updated")),
        guid=_text(el, f"{_ATOM}id") or link,
    )


def _text(el: ET.Element, tag: str) -> str:
    child = el.find(tag)
    return (child.text or "").strip() if child is not None else ""


def clean(text: str, limit: int = 0) -> str:
    """HTML → one line of plain text, cut at a word boundary when ``limit`` is given."""
    out = _SPACE.sub(" ", html.unescape(_TAG.sub(" ", html.unescape(text or "")))).strip()
    if limit and len(out) > limit:
        out = out[:limit].rsplit(" ", 1)[0] + "…"
    return out


def parse_time(text: str) -> Optional[float]:
    """RFC 822 (RSS) or ISO 8601 (Atom) → epoch seconds; None when unreadable. A time without a
    zone is read as UTC (none of the white-listed feeds sends one)."""
    text = (text or "").strip()
    if not text:
        return None
    try:
        dt = parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError):
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()
