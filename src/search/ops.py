"""Header search (UI redesign R1, R-D5): one box over what the role may already open — the client's holdings and
goals, the RM's clients, events, the CIO's news and research, Compliance's held news. Accent-insensitive; each hit
says what it is and where it opens. Nothing here is new data: every hit is a record another page already shows.

The client matches events only by their type label, never by the headline it may not see (BRD flow 2)."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from operonx import op

from apply import reads
from copilot.scrub import fold
from events import store as events
from news import store as news
from people import auth
from research import store as research
from views import schema
from wealth import fixtures

ROLES = ("client", "rm", "cio", "compliance")
LIMIT = 6  # per kind
WORD = re.compile(r"[a-z0-9]+")
CLASSES = {**schema.ASSET_CLASSES, "loan": "Khoản vay", "card": "Dư nợ thẻ"}
ROUTES = {
    "holding": {"client": "#/client/tai-san", "rm": "#/rm/khach-hang/tai-san"},
    "goal": {"client": "#/client/muc-tieu/ke-hoach", "rm": "#/rm/khach-hang/ke-hoach"},
    "event": {"client": "#/client/tin/thi-truong", "rm": "#/rm/khach-hang/tac-dong", "cio": "#/cio/nhan-dinh/{id}"},
    "client": {"rm": "#/rm/khach-hang/toan-canh"},
    "news": {"cio": "#/cio/hop-tin", "compliance": "#/compliance/giu"},
    "research": {"cio": "#/cio/nghien-cuu", "compliance": "#/compliance/nghien-cuu"},
}


@op
def check_request(q: str = None, role: str = None, client_id: str = None, scope: str = None) -> dict:
    q = str(q or "").strip()
    if len(q) > 80:
        raise ValueError("câu tìm quá dài")
    role = auth.role_for(role)
    if role not in ROLES:
        raise ValueError(f"vai trò {role!r} không có")
    cid = str(client_id or "")
    if cid not in fixtures.client_ids(members=True):
        mine = auth.visible(fixtures.client_ids())  # CIO and Compliance search without a client; holdings unused then
        cid = (mine or fixtures.client_ids())[0]
    return {"q": q, "role": role, "client_id": cid, "scope": scope or "personal"}


def _hit(kind: str, role: str, label: str, sub: str = "", ref: str = "", score: int = 1, **extra: Any) -> dict:
    route = ROUTES[kind][role].replace("{id}", ref)
    return {"kind": kind, "label": label, "sub": sub, "ref": ref, "route": route, "_score": score, **extra}


def _best(items, score) -> list:
    """(item, score) for the matching items, best first, at most LIMIT."""
    scored = [(x, score(x)) for x in items]
    return sorted([(x, n) for x, n in scored if n], key=lambda p: -p[1])[:LIMIT]


def find(q: str, role: str, holdings: List[Dict[str, Any]], goals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Hits for q, grouped by kind in a fixed order, at most LIMIT each. Pure over its inputs and the stores."""
    words = WORD.findall(fold(q))
    hits: List[Dict[str, Any]] = []
    if not words or len("".join(words)) < 2:
        return {"q": q, "role": role, "hits": []}

    def match(*texts: Any) -> int:
        """0 = no match; otherwise 1 + how many query words equal a whole word (every query word is a prefix)."""
        have = WORD.findall(fold(" ".join(str(t or "") for t in texts)))
        if not all(any(h.startswith(w) for h in have) for w in words):
            return 0
        return 1 + sum(w in have for w in words)

    if role in ("client", "rm"):
        got = _best(holdings, lambda h: match(h.get("name"), CLASSES.get(h.get("class")), h.get("institution")))
        hits += [
            _hit("holding", role, h["name"], CLASSES.get(h["class"], h["class"]), h.get("key", ""), n, value=h["value"])
            for h, n in got
        ]
        got = _best(goals, lambda g: match(g["title"], g.get("stage_label")))
        hits += [_hit("goal", role, g["title"], g.get("stage_label") or "", g["id"], n) for g, n in got]
    if role == "rm":
        got = _best(
            [fixtures.client(c) for c in auth.visible(fixtures.client_ids())],
            lambda c: match(c["name"], c.get("occupation"), c.get("segment")),
        )
        hits += [_hit("client", role, c["name"], c.get("segment") or "", c["id"], n, client_id=c["id"]) for c, n in got]
    if role in ("client", "rm", "cio"):
        evs = events.listing()
        if role == "client":
            labels = sorted({reads._type_label(e.get("type")) for e in evs})
            hits += [_hit("event", role, t, "Sự kiện tin tức", "", n) for t, n in _best(labels, lambda t: match(t))]
        else:
            got = _best(evs, lambda e: match(e["title"], reads._type_label(e.get("type"))))
            hits += [_hit("event", role, e["title"], reads._type_label(e.get("type")), e["id"], n) for e, n in got]
    if role == "cio":
        got = _best(news.inbox(status="all", limit=5000), lambda x: match(x.get("title"), x.get("outlet")))
        hits += [_hit("news", role, x["title"], x.get("outlet") or "", x["id"], n) for x, n in got]
    if role == "compliance":
        held = [x for x in news.inbox(status="all", limit=5000) if x.get("held")]
        got = _best(held, lambda x: match(x.get("title"), x.get("outlet")))
        hits += [_hit("news", role, x["title"], "Tin bị giữ", x["id"], n) for x, n in got]
    if role in ("cio", "compliance"):
        got = _best(research.listing(), lambda r: match(r.get("title"), r.get("report_no")))
        hits += [_hit("research", role, r["title"], r.get("report_no") or "", r["id"], n) for r, n in got]
    order = {k: i for i, k in enumerate(ROUTES)}
    hits.sort(key=lambda h: (-h.pop("_score"), order[h["kind"]]))  # whole-word matches first, then by kind
    return {"q": q, "role": role, "hits": hits}


@op
def search(q: str, role: str, holdings: list, goals: list) -> dict:
    return {"search": find(q, role, holdings, goals)}
