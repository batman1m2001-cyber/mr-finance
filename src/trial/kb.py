"""The headline knowledge base (FORECAST_DESK_PLAN step 4): the four outlets' past headlines, each day with what the
factors did after it, and for today's news the past headlines most like it and what followed them.

- **The headlines** are the replay's Google News cache (out/replay/feeds, one file per outlet and day), titles only.
- **Lexical** (BM25 over syllables and syllable pairs: Vietnamese words are mostly two syllables): no embedding, no
  model call, the same answer every time.
- **No leak**: a headline counts only when the move after it ended on or before the origin's close."""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from trial import shadow

WORD = re.compile(r"\w+", re.UNICODE)
K1, B = 1.2, 0.75
# the outlets' daily furniture: lotteries, weather, sport, the outlet's own name
NOISE = re.compile(r"xổ số|kết quả xs|thời tiết|bóng đá|marathon|world cup|v-league|tử vi|cung hoàng đạo", re.I)


def tokens(text: str) -> List[str]:
    w = [t for t in WORD.findall(text.lower()) if not t.isdigit()]
    return w + [f"{a}_{b}" for a, b in zip(w, w[1:])]


def headlines(feeds: Path, first: str, last: str) -> List[Tuple[str, str]]:
    """(day, title) of every cached feed's items published from ``first`` to ``last``, once each."""
    seen, out = set(), []
    for path in sorted(feeds.glob("*.xml")):
        day = path.stem.rsplit("_", 1)[-1]
        if not (first <= day <= last) and not (first <= shadow.realised.add_days(day, 1) <= last):
            continue
        for it in ET.fromstring(path.read_bytes()).findall("./channel/item"):
            try:
                d = parsedate_to_datetime(it.findtext("pubDate")).astimezone().date().isoformat()
            except (TypeError, ValueError):
                continue
            title = (it.findtext("title") or "").rsplit(" - ", 1)[0].strip()
            if first <= d <= last and title and not NOISE.search(title) and (d, title) not in seen:
                seen.add((d, title))
                out.append((d, title))
    return sorted(out)


class Base:
    """BM25 over the headlines."""

    def __init__(self, docs: List[Tuple[str, str]]):
        self.docs = docs
        self.tf = [Counter(tokens(t)) for _, t in docs]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.len) / len(self.len) if docs else 0.0
        df: Counter = Counter()
        self.index: Dict[str, List[int]] = defaultdict(list)
        for i, c in enumerate(self.tf):
            for t in c:
                df[t] += 1
                self.index[t].append(i)
        n = len(docs)
        self.idf = {t: math.log(1 + (n - k + 0.5) / (k + 0.5)) for t, k in df.items()}

    def search(self, text: str, before: str, k: int = 20) -> List[Tuple[float, str, str]]:
        """The ``k`` headlines most like ``text`` published before ``before``: (score, day, title)."""
        q = set(tokens(text))
        score: Dict[int, float] = defaultdict(float)
        for t in q:
            for i in self.index.get(t, ()):
                if self.docs[i][0] >= before:
                    continue
                f = self.tf[i][t]
                score[i] += self.idf[t] * f * (K1 + 1) / (f + K1 * (1 - B + B * self.len[i] / self.avg))
        top = sorted(score.items(), key=lambda x: -x[1])[:k]
        return [(round(s, 2), *self.docs[i]) for i, s in top]


def after(day: str, horizon: str, origin: str, series: Dict[str, Any], m: Any) -> Dict[str, float]:
    """Each factor's move in σ from the close before ``day`` over the horizon — only a move over by the origin."""
    start = shadow.realised.add_days(day, -1)
    due = shadow.realised.add_days(start, shadow.HORIZON_DAYS[horizon])
    if due > origin:
        return {}
    out = {}
    for fid, s in series.items():
        x = s.move(start, due)
        if x is not None:
            out[fid] = x / (m.factor(fid).vol_month * math.sqrt(m.horizons[horizon]))
    return out


def analogs(base: Base, texts: Iterable[str], origin: str, horizon: str, series: Dict[str, Any], m: Any,
            k: int = 20) -> Dict[str, Dict[str, float]]:
    """Per factor, what followed the past headlines most like ``texts`` (each text's top ``k``, a day once): the
    mean move in σ, the share up, and how many days."""
    days: Dict[str, float] = {}
    for text in texts:
        for s, d, _ in base.search(text, before=shadow.realised.add_days(origin, 1), k=k):
            days[d] = max(days.get(d, 0.0), s)
    moves: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    for d, w in days.items():
        for fid, z in after(d, horizon, origin, series, m).items():
            moves[fid].append((w, z))
    out = {}
    for fid, xs in moves.items():
        tw = sum(w for w, _ in xs)
        out[fid] = {"mean": round(sum(w * z for w, z in xs) / tw, 3), "up": round(sum(z > 0 for _, z in xs) / len(xs), 2),
                    "days": len(xs)}
    return out


def examples(base: Base, text: str, origin: str, horizon: str, series: Dict[str, Any], m: Any,
             k: int = 3) -> List[Dict[str, Any]]:
    """The ``k`` closest past headlines with what followed, for the desk to read."""
    out = []
    for s, d, title in base.search(text, before=shadow.realised.add_days(origin, 1), k=k * 3):
        moves = after(d, horizon, origin, series, m)
        if moves:
            out.append({"day": d, "title": title, "after_sigma": {f: round(z, 2) for f, z in moves.items()}})
        if len(out) == k:
            break
    return out


def load(feeds: Path, first: str = "2024-01-01", last: str = "2026-06-30") -> Optional[Base]:
    docs = headlines(feeds, first, last)
    return Base(docs) if docs else None
