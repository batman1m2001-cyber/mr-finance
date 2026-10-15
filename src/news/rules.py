"""The news rules, pure: the gates an item passes before it reaches the CIO's inbox, and how it is
sorted (BRD BR-02, BR-04, FR-102, FR-104, F20).

Gates, in order (the first that fails decides):
- the source is on the white list and approved;
- the link is on the source's own site;
- the item has a published time;
- that time is not more than ``future_minutes`` after ingestion (refused, never pulled back);
- it is not older than ``max_age_days`` (skipped: old news is not a new event).

Then an item that names someone on the restricted list is held for Compliance; the rest is
classified: international or domestic (source, then words), the engine factors it touches, a
relevance level, and an event type hint. Words match whole words, case-insensitive.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit

ACCEPT, REFUSE, SKIP = "accept", "refuse", "skip"


@dataclass
class Verdict:
    outcome: str  # accept, refuse, skip
    reason: str = ""


@dataclass
class Sorted:
    kind: str  # intl, domestic
    factors: List[str] = field(default_factory=list)
    relevance: str = "low"  # high, medium, low
    score: float = 0.0
    event_type: Optional[str] = None
    restricted: List[str] = field(default_factory=list)  # names on the restricted list it mentions


def source_of(config: Dict[str, Any], source_id: str) -> Optional[Dict[str, Any]]:
    return next((s for s in config["sources"] if s["id"] == source_id), None)


def gate(config: Dict[str, Any], source_id: str, link: str, published: Optional[float], ingested: float) -> Verdict:
    src = source_of(config, source_id)
    if src is None or not src.get("approved"):
        return Verdict(REFUSE, "Nguồn không thuộc danh sách trắng")
    if not _same_site(link, src["url"]):
        return Verdict(REFUSE, "Liên kết không thuộc trang của nguồn")
    if published is None:
        return Verdict(REFUSE, "Tin không có giờ công bố")
    g = config["gates"]
    if published > ingested + g["future_minutes"] * 60:
        return Verdict(REFUSE, f"Giờ công bố muộn hơn lúc nạp quá {g['future_minutes']} phút")
    if published < ingested - g["max_age_days"] * 86400:
        return Verdict(SKIP, f"Tin cũ hơn {g['max_age_days']} ngày")
    return Verdict(ACCEPT)


def classify(config: Dict[str, Any], source_id: str, title: str, summary: str) -> Sorted:
    text = f"{title} {summary}".lower()
    head = title.lower()
    src = source_of(config, source_id) or {}
    kind = src.get("kind", "domestic")
    if kind == "domestic" and _any(config["intl_words"], head) and not _any(config["domestic_words"], head):
        kind = "intl"
    factors = [f for f, words in config["factor_words"].items() if _any(words, text)]
    in_title = [f for f, words in config["factor_words"].items() if _any(words, head)]
    score = min(1.0, (len(factors) + len(in_title)) / 4)
    relevance = "high" if score >= 0.75 else "medium" if score >= 0.25 else "low"
    event_type = next((t["id"] for t in config["event_types"] if _any(t["words"], text)), None)
    restricted = [r["name"] for r in config["restricted"] if _any([*r["aliases"], r["ticker"].lower()], text)]
    return Sorted(kind, factors, relevance, round(score, 2), event_type, restricted)


def url_key(link: str) -> str:
    """The same article under http / https, with or without a trailing slash or tracking query."""
    p = urlsplit(link.strip())
    host = p.netloc.lower().removeprefix("www.")
    path = re.sub(r"/{2,}", "/", p.path).rstrip("/")
    query = "&".join(q for q in p.query.split("&") if q and not q.lower().startswith(("utm_", "fbclid")))
    return urlunsplit(("", host, path, query, ""))


def title_key(source_id: str, title: str) -> str:
    norm = re.sub(r"[^\w]+", " ", title.lower()).strip()
    return hashlib.sha1(f"{source_id}|{norm}".encode("utf-8")).hexdigest()


def _same_site(link: str, feed_url: str) -> bool:
    host = urlsplit(link).netloc.lower().removeprefix("www.")
    site = urlsplit(feed_url).netloc.lower().removeprefix("www.")
    return bool(host) and (host == site or host.endswith("." + site))


def _any(words: List[str], text: str) -> bool:
    return bool(words) and _pattern(tuple(words)).search(text) is not None


@lru_cache(maxsize=256)
def _pattern(words: Tuple[str, ...]) -> "re.Pattern[str]":
    alts = "|".join(re.escape(w.lower()) for w in sorted(words, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alts})(?!\w)")
