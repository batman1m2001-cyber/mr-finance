"""Important news collected (BRD-KPI-02 “tin quan trọng được thu thập ≥ 95%”; BRD_REMAINING_PLAN G6, G-D6). The BRD
does not say what makes news important; until the bank does, this is our reading, labelled “Đề xuất”:

- **The reference.** Google News' Business section for Vietnam groups each story with the outlets carrying it.
  The ``news_reference`` job reads it every 2 hours (one request) and keeps each story: its titles and outlets,
  growing while the story is new.
- **Important** = a story on our topics (its title names one of the engine's factors, by the same words that sort
  our news) carried by at least ``min_outlets`` (2) outlets.
- **Collected** = one of our news items published within ``match_hours`` (36 h) of the story has a title sharing
  ``match`` (0.4, Jaccard over words, numbers and filler words left out) with one of the story's titles. Judged
  once, ``judge_after_hours`` (24 h) after the story was first seen, and kept with the item that matched, so a
  person can check it.
- **Coverage** = collected ÷ important, by day and month. Next to it, the same over the stories an outlet we follow
  carried: a story none of our outlets carried could only be collected by widening the white list.
"""

from __future__ import annotations

import html
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

from news import rules
from news import store as news_store

_ARTICLE = re.compile(r'<a [^>]*>(.*?)</a>(?:&nbsp;|\s)*<font color="#6f6f6f">(.*?)</font>', re.S)
_OUTLET_TAIL = re.compile(r"\s+-\s+[^-]+$")


def _config() -> Dict[str, Any]:
    from news.ops import config

    return config()


def parse(raw: bytes | str) -> List[Dict[str, Any]]:
    """The reference feed's stories: ``{id, title, link, published, articles: [{title, outlet}]}``."""
    root = ET.fromstring(raw.lstrip() if isinstance(raw, str) else raw.lstrip(b"\xef\xbb\xbf \r\n\t"))
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        desc = it.findtext("description") or ""
        arts = [
            {"title": _OUTLET_TAIL.sub("", html.unescape(re.sub(r"<[^>]+>", "", a))).strip(), "outlet": o.strip()}
            for a, o in _ARTICLE.findall(desc)
        ]
        if not arts:
            arts = [{"title": _OUTLET_TAIL.sub("", title), "outlet": (it.findtext("source") or "").strip()}]
        try:
            published = parsedate_to_datetime(it.findtext("pubDate") or "").timestamp()
        except (TypeError, ValueError):
            published = None
        sid = (it.findtext("guid") or link or title).strip()
        out.append(
            {"id": sid, "title": _OUTLET_TAIL.sub("", title), "link": link, "published": published, "articles": arts}
        )
    return out


def words(title: str, stop: frozenset) -> set:
    return {
        w for w in re.sub(r"[^\w]+", " ", title.lower()).split() if w not in stop and not re.fullmatch(r"\d+\w*", w)
    }


def similarity(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def keep(stories: List[Dict[str, Any]], now: Optional[float] = None) -> Dict[str, int]:
    """Stories kept: new ones added, ones still waiting to be judged grown by any new outlet or title."""
    cfg = _config()
    ref = cfg["reference"]
    now = time.time() if now is None else now
    added = grown = 0
    with news_store._db() as con:
        for s in stories:
            row = con.execute("select judged, data from reference_stories where id = ?", (s["id"],)).fetchone()
            if row is not None and row["judged"] is not None:
                continue
            old = json.loads(row["data"]) if row else {"articles": []}
            seen = {(a["title"], a["outlet"]) for a in old["articles"]}
            articles = old["articles"] + [a for a in s["articles"] if (a["title"], a["outlet"]) not in seen]
            outlets = sorted({a["outlet"] for a in articles if a["outlet"]})
            factors = rules.classify(cfg, "reference", s["title"], "").factors
            data = {
                "title": s["title"],
                "link": s["link"],
                "articles": articles,
                "outlets": outlets,
                "factors": factors,
                "important": bool(factors) and len(outlets) >= int(ref["min_outlets"]),
            }
            if row is None:
                con.execute(
                    "insert into reference_stories values (?, ?, ?, null, null, ?)",
                    (s["id"], s["published"], now, json.dumps(data, ensure_ascii=False)),
                )
                added += 1
            elif len(articles) > len(old["articles"]):
                con.execute(
                    "update reference_stories set data = ? where id = ?",
                    (json.dumps(data, ensure_ascii=False), s["id"]),
                )
                grown += 1
    return {"added": added, "grown": grown}


def judge(now: Optional[float] = None) -> int:
    """Every story first seen ``judge_after_hours`` ago or more, not yet judged: collected or not, once."""
    cfg = _config()
    ref = cfg["reference"]
    now = time.time() if now is None else now
    stop = frozenset(ref["stopwords"])
    ours = {(s["outlet"] or "").lower() for s in cfg["sources"]}
    span = float(ref["match_hours"]) * 3600
    n = 0
    with news_store._db() as con:
        due = con.execute(
            "select * from reference_stories where judged is null and first_seen <= ?",
            (now - float(ref["judge_after_hours"]) * 3600,),
        ).fetchall()
        for r in due:
            data = json.loads(r["data"])
            at = r["published"] or r["first_seen"]
            best = {"score": 0.0}
            if data["important"]:
                titles = [words(a["title"], stop) for a in data["articles"]] + [words(data["title"], stop)]
                for item in con.execute(
                    "select id, data from news_items where status != 'refused' and published between ? and ?",
                    (at - span, at + span),
                ):
                    mine = json.loads(item["data"])["title"]
                    w = words(mine, stop)
                    score = max(similarity(t, w) for t in titles)
                    if score > best["score"]:
                        best = {"score": round(score, 3), "news_id": item["id"], "title": mine}
            collected = int(best["score"] >= float(ref["match"])) if data["important"] else None
            data["match"] = best if best["score"] > 0 else None
            data["ours"] = any(o.lower() in ours for o in data["outlets"])
            con.execute(
                "update reference_stories set judged = ?, collected = ?, data = ? where id = ?",
                (now, collected, json.dumps(data, ensure_ascii=False), r["id"]),
            )
            n += 1
    return n


def _day(t: float) -> str:
    return datetime.fromtimestamp(t).strftime("%Y-%m-%d")


def coverage() -> Dict[str, Any]:
    """Important stories judged, collected and the share, by day and by month (newest first), with the misses."""
    ref = _config()["reference"]
    with news_store._db() as con:
        rows = con.execute(
            "select published, first_seen, collected, data from reference_stories "
            "where judged is not null and collected is not null order by coalesce(published, first_seen)"
        ).fetchall()
        first = con.execute("select min(first_seen) from reference_stories").fetchone()[0]
    stories = [
        {"at": r["published"] or r["first_seen"], "collected": bool(r["collected"]), **json.loads(r["data"])}
        for r in rows
    ]

    def share(xs: List[Dict[str, Any]]) -> Optional[float]:
        return round(sum(s["collected"] for s in xs) / len(xs), 3) if xs else None

    def group(key) -> List[Dict[str, Any]]:
        out = []
        for k in sorted({key(s["at"]) for s in stories}, reverse=True):
            mine = [s for s in stories if key(s["at"]) == k]
            followed = [s for s in mine if s.get("ours")]
            out.append(
                {
                    "period": k,
                    "important": len(mine),
                    "collected": sum(s["collected"] for s in mine),
                    "share": share(mine),
                    "followed": len(followed),
                    "followed_share": share(followed),
                }
            )
        return out

    misses = [
        {"title": s["title"], "at": s["at"], "outlets": s["outlets"], "followed": s.get("ours", False)}
        for s in reversed(stories)
        if not s["collected"]
    ][:30]
    return {
        "by_day": group(_day)[:31],
        "by_month": group(lambda t: _day(t)[:7]),
        "misses": misses,
        "target": float(ref["target"]),
        "reference": ref["outlet"],
        "since": first,
    }
