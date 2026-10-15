"""What the router may see (decision D2): the question with every number, code and known person removed.

Removed: digit runs (amounts, dates, account numbers, ids), upper-case codes of two or more letters or digits
(tickers, fund and bond codes), and every client's, spouse's and dependent's full name and its last two words
(“Minh An”), compared without accents. What is left is the shape of the question, not its data.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import List

from people import store

NUM = re.compile(r"\d[\d.,/:\-]*")
CODE = re.compile(r"\b[A-ZĐ][A-ZĐ0-9]{1,}\b")


def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


@lru_cache(maxsize=1)
def names() -> List[str]:
    """Every person in the fixtures: full names and their last two words, longest first."""
    out = set()
    for cid in store.client_ids(members=True):  # names only, for removing them: not a read of anyone's data
        c = store.client(cid)
        people = [c["name"]] + [d["name"] for d in c.get("dependents") or []]
        for n in people:
            out.add(n)
            words = n.split()
            if len(words) >= 3:
                out.add(" ".join(words[-2:]))
    return sorted(out, key=len, reverse=True)


def scrub(text: str) -> str:
    s = unicodedata.normalize("NFC", str(text or ""))
    for n in names():  # accent-insensitive: find the span in the folded text, cut it from the original
        f = fold(n)
        while True:
            folded = fold(s)
            i = folded.find(f)
            if i < 0:
                break
            s = s[:i] + "<người>" + s[i + len(f) :]
    s = NUM.sub("<số>", s)
    s = CODE.sub("<mã>", s)
    return re.sub(r"\s+", " ", s).strip()[:500]
