"""The evidence frames (data/evidence.json, written by scripts/make_evidence.py) as the pages read them: the statistics
measured at read time from the market store, the CIO's review, the line on the chart (§8.2), and the notes a plan
frame makes for the goal branch (Ví dụ 4).

A frame the CIO has not approved (returned, rejected) gives no evidence: the chart falls back to the level (§8.1).
The seed frames start approved by the sample reviewer ("mẫu"), so the demo shows them; the CIO may return any."""

from __future__ import annotations

import json
import time
from datetime import date
from functools import lru_cache
from typing import Any, Dict, List, Optional

from evidence import _check, _stats
from evidence import catalogue as cat
from wealth.paths import DATA

REVIEW = ("_cio", "evidence_review")
DECISIONS = {"approve": "approved", "return": "returned", "reject": "rejected"}
STATUS_LABEL = {"approved": "Đã duyệt", "returned": "Trả lại agent", "rejected": "Từ chối"}
SEED = {"status": "approved", "by": "mẫu", "at": None, "note": ""}


@lru_cache(maxsize=1)
def data() -> Dict[str, Any]:
    return json.loads((DATA / "evidence.json").read_text(encoding="utf-8"))


def ids() -> List[str]:
    return list(data()["frames"])


def reviews() -> Dict[str, Dict[str, Any]]:
    from wealth import store

    return dict(store.result(*REVIEW) or {})


def review(fid: str) -> Dict[str, Any]:
    return reviews().get(fid) or dict(SEED)


def events() -> Dict[str, List[str]]:
    """Each event type's precedent dates: the seed calendar with the dates the CIO added (P2)."""
    return cat.events(data()["events"])


@lru_cache(maxsize=256)
def _measured(stamp: Any, series: str, dates: tuple, timeframe: str) -> Dict[str, Any]:
    from market import store as market

    return _stats.measure(market.points(series), list(dates), timeframe)


def measured(series: str, event_type: str, timeframe: str) -> Dict[str, Any]:
    from market import store as market

    return _measured(market.stamp(), series, tuple(events().get(event_type, [])), timeframe)


def preview(event_type: str) -> List[Dict[str, Any]]:
    """What the statistics branch would say for a type on each series and timeframe (P2): the CIO sees which pairs
    already have enough precedents and a direction, before any frame asks for them."""
    out = []
    for series, name in cat.SERIES.items():
        for tf in _stats.DAYS:
            s = measured(series, event_type, tf)
            out.append({"series": series, "series_label": name, "timeframe": tf, "timeframe_label": s["timeframe_label"],
                        "n": s["n"], "enough": s["enough"], "direction": s["direction"],
                        "direction_label": cat.DIRECTIONS[s["direction"]], **{k: s.get(k) for k in ("way", "same", "rate", "base_rate", "edge")}})  # fmt: skip
    return out


def stats(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The statistics branch's numbers for a frame that asks for them, measured on the market store; None otherwise."""
    st = raw.get("stat")
    if raw.get("branch") != "statistics" or not st:
        return None
    s = measured(st["series"], raw["event_type"], st["timeframe"])
    if s["n"]:
        s = {**s, "sentence": _stats.sentence(s, cat.event_types()[raw["event_type"]]["label"], st["series_label"])}
    return s


def frame(fid: str) -> Dict[str, Any]:
    """The frame as kept: on the statistics branch with enough precedents, the computed direction wins (§9 rule 7);
    with too few, the qualitative branch (§13.2)."""
    raw = dict(data()["frames"][fid])
    s = stats(raw)
    if s is not None:
        if s["enough"]:
            raw["stats"] = s
            raw["timeframe"] = raw["stat"]["timeframe"]
            _, raw = _check.check(raw, s["direction"])
        else:
            raw["branch"] = "qualitative"
            raw["notes"] = list(raw.get("notes") or []) + [
                f"Chỉ có {s['n']} tiền lệ đo được (cần {cat.MIN_PRECEDENTS}): đi nhánh định tính."
            ]
    return raw


def label(f: Dict[str, Any]) -> str:
    """§8.2's evidence label: "8/12 lần", "2 tiền lệ", or "qua pháp lý"."""
    if f["branch"] == "statistics":
        return f"{f['stats']['same']}/{f['stats']['n']} lần"
    if f.get("precedents"):
        return f"{len(f['precedents'])} tiền lệ"
    return f"qua {f['channels'][0]}"


def summary(fid: str) -> Optional[Dict[str, Any]]:
    """What an alert's row shows of its frame; None when there is no frame or the CIO has not approved it."""
    if fid not in data()["frames"] or review(fid)["status"] != "approved":
        return None
    f = frame(fid)
    return {
        "branch": f["branch"],
        "direction": f["direction"],
        "direction_label": cat.DIRECTIONS[f["direction"]],
        "timeframe": f["timeframe"],
        "timeframe_label": cat.TIMEFRAMES[f["timeframe"]],
        "label": label(f),
        "certain_from": f.get("certain_from"),
        "targets": f["targets"],
    }


def view(fid: str, cio: bool = False) -> Dict[str, Any]:
    """The frame as a page shows it. Only the CIO sees the internal headline, the notes, the review and which
    precedents have no source (§8.2, §13.5); the others see no "Nguồn" line on those."""
    from wealth import fixtures

    f = frame(fid)
    out = {
        "factor": fid,
        "title": next((x["title"] for x in fixtures.factors()["factors"] if x["id"] == fid), fid),
        "event_type": f["event_type"],
        "event_label": cat.event_types()[f["event_type"]]["label"],
        "branch": f["branch"],
        "channels": f["channels"],
        "mechanism": f["mechanism"],
        "targets": [{"label": t, "name": cat.target_label(t)} for t in f["targets"]],
        "direction": f["direction"],
        "direction_label": cat.DIRECTIONS[f["direction"]],
        "changes": f["changes"],
        "timeframe": f["timeframe"],
        "timeframe_label": cat.TIMEFRAMES[f["timeframe"]],
        "watch": f["watch"],
        "precedents": [{k: p[k] for k in ("event", "outcome", "difference", "source")} for p in f.get("precedents") or []],
        "label": label(f),
    }
    if f["branch"] == "statistics":
        s = f["stats"]
        out["stats"] = {k: s.get(k) for k in ("n", "same", "rate", "base_rate", "edge", "median", "low", "high", "period",
                                              "timeframe_label", "moves", "sentence")}  # fmt: skip
        out["stats"]["series"] = f["stat"]["series_label"]
    if cio:
        out["headline"] = f.get("headline")
        out["notes"] = f.get("notes") or []
        out["review"] = {**review(fid), "label": STATUS_LABEL[review(fid)["status"]]}
        out["unsourced"] = sum(1 for p in out["precedents"] if not p["source"])
        for p in out["precedents"]:
            p["unsourced"] = not p["source"]
    return out


def decide(fid: str, decision: str, by: str, note: str = "") -> Dict[str, Any]:
    """The CIO approves, returns or rejects a frame; audited with how many of its precedents have no source."""
    from control import audit, db
    from wealth import store

    kept = reviews()
    kept[fid] = {"status": DECISIONS[decision], "by": by, "at": time.time(), "note": str(note or "").strip()[:300]}
    store.put_result(*REVIEW, kept)
    unsourced = sum(1 for p in data()["frames"][fid].get("precedents") or [] if not p.get("source"))
    with db.tx() as con:
        audit.append(con, by, f"evidence.{DECISIONS[decision]}", fid, {"note": kept[fid]["note"], "unsourced": unsourced})
    return {"factor": fid, **kept[fid], "label": STATUS_LABEL[kept[fid]["status"]]}


def notes(today: Optional[date] = None) -> List[Dict[str, Any]]:
    """Approved plan frames as regulation notes for the goal branch (Ví dụ 4): news → plan label → a family's goal →
    an RM task, and a client message only for a declared goal."""
    from wealth import fixtures

    titles = {f["id"]: f["title"] for f in fixtures.factors()["factors"]}
    out = []
    for fid, f in data()["frames"].items():
        purposes = [t.split(":", 1)[1] for t in f["targets"] if t.startswith("plan:")]
        if not f.get("client_message") or not purposes or review(fid)["status"] != "approved":
            continue
        out.append(
            {
                "id": f"EV-{fid}",
                "kind": "regulation",
                "title": titles.get(fid, cat.event_types()[f["event_type"]]["label"]),
                "regulation": {
                    "document": titles.get(fid),
                    "purposes": purposes,
                    "countries": [],
                    "status": "draft",
                    "prep_weeks": f.get("prep_weeks", 0),
                    "documents": f.get("documents") or [],
                    "client_message": f["client_message"],
                    "rm_hint": f.get("rm_hint"),
                },
            }
        )
    return out
