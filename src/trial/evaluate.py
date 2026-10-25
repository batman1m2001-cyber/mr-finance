"""The agents' calls scored as market moves (AGENT_EVALUATION_PLAN §2.2–2.5): precision, recall, missed moves,
direction and estimation error, with the coverage beside them, and the agents' choice of events against the
independent reference.

The unit is a **move**: one factor, one horizon, from one trial morning's origin (the close before it). However many
of that morning's drafts predicted it, a move is scored once; their claims are merged, and opposite material claims
are *conflicting*, excluded, never incorrect. Ground truth is the market (``measure.realised``, as FEAT-18 scores),
never the agent. A score keeps what it was scored with (the drafts, the thresholds, the realised move) and is not
scored again once final. Pending, excluded and failed moves are never counted as incorrect.
"""

from __future__ import annotations

import json
import math
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from control import db
from trial import daily, segments, shadow
from wealth.paths import DATA

FINAL = ("correct", "incorrect", "missed", "quiet", "excluded", "failed")
VERDICTS = ("correct", "incorrect", "missed", "quiet", "pending", "excluded", "failed")


def settings() -> Dict[str, float]:
    raw = json.loads((DATA / "evaluation.json").read_text(encoding="utf-8"))
    return {"material_sigma": float(raw["material_sigma"]), "claim_share": float(raw["claim_share"])}


# -- the mornings ------------------------------------------------------------------------------------------------


def mornings(today: str) -> List[Dict[str, Any]]:
    """Every trial morning from the first to today (until the trial's end): ran (with drafts), or not and why.
    A morning with neither events nor a record, before today, is ``no_record``: the run left no trace."""
    events, notes = daily.days(), daily.notes()
    known = sorted(set(events) | set(notes))
    if not known:
        return []
    last = min(today, daily.until())
    out, d = [], known[0]
    while d <= last:
        evs, note = events.get(d, []), notes.get(d)
        drafts = [e for e in evs if e.get("view_id")]
        if drafts:
            status = "ran"
        elif evs:
            status = "no_drafts"
        elif note and note.get("status") != "running":
            status = note.get("status") or "failed"
        elif d < today:
            status = "no_record" if not note else "failed"  # a run still "running" the day after died mid-way
        else:
            d = shadow.realised.add_days(d, 1)
            continue  # this morning's run is still to come
        out.append({"day": d, "status": status, "events": len(evs), "drafts": len(drafts), "note": note})
        d = shadow.realised.add_days(d, 1)
    return out


# -- one move ----------------------------------------------------------------------------------------------------


def _day_of(t: float) -> str:
    return datetime.fromtimestamp(t).date().isoformat()


def judge_move(
    day: str,
    horizon: str,
    factor: Any,
    drafts: List[Dict[str, Any]],
    ran: bool,
    series: Dict[str, Any],
    today: str,
    cfg: Dict[str, float],
    months: float,
) -> Dict[str, Any]:
    """One move's verdict and its record. ``drafts`` are the morning's shadow forecasts for it; ``ran`` whether the
    morning made any draft (a material move without one is missed with reason ``no_run``)."""
    origin = drafts[0]["origin"] if drafts else shadow.origin_of(datetime.fromisoformat(day).timestamp() + 43200)
    due = shadow.realised.add_days(origin, shadow.HORIZON_DAYS[horizon])
    scale = factor.vol_month * math.sqrt(months)
    rec: Dict[str, Any] = {
        "origin": origin,
        "due": due,
        "unit": factor.unit,
        "family": segments.family_of_factor(factor.id),
        "scale": round(scale, 6),
        "material_sigma": cfg["material_sigma"],
        "claim_share": cfg["claim_share"],
        "ran": ran,
        "is_due": due < today,
        "drafts": [
            {
                "view_id": f["view_id"],
                "event_id": f.get("event_id"),
                "created": f["created"],
                "expected": f["expected"],
                "p10": f.get("p10"),
                "p90": f.get("p90"),
            }
            for f in drafts
        ],
    }
    leak = [f["view_id"] for f in drafts if _day_of(f["created"]) <= origin]
    if leak:  # a draft made on or before its origin's close would have seen the move it is scored on
        return {**rec, "verdict": "excluded", "reason": "leak", "leak": leak}
    edge = cfg["claim_share"] * scale
    signs = {1 if f["expected"] > 0 else -1 for f in drafts if abs(f["expected"]) >= edge}
    expected = sum(f["expected"] for f in drafts) / len(drafts) if drafts else None
    claim = None if not signs else ("conflicting" if len(signs) > 1 else ("up" if signs == {1} else "down"))
    rec.update(expected=None if expected is None else round(expected, 6), claim=claim)
    s = series.get(factor.id)
    if s is None:
        return {**rec, "verdict": "excluded", "reason": "assumed" if factor.assumed else "no_series"}
    if due >= today:
        return {**rec, "verdict": "pending", "reason": "not_due"}
    x = s.move(origin, due) if s.last and s.last >= due else None
    if x is None:
        late = (date.fromisoformat(today) - date.fromisoformat(due)).days > shadow.forecasts.GIVE_UP_DAYS
        return {**rec, "verdict": "failed" if late else "pending", "reason": "no_data" if late else "waiting"}
    material = abs(x) >= cfg["material_sigma"] * scale
    rec.update(realised=round(x, 6), material=material, move="up" if x > 0 else "down" if x < 0 else "flat")
    if expected is not None:
        rec.update(
            error=round(abs(expected - x), 6),
            error_sd=round(abs(expected - x) / scale, 4) if scale else None,
            direction_hit=None if expected == 0 or x == 0 else (expected > 0) == (x > 0),
            inside=all(f.get("p10") is not None for f in drafts)
            and min(f["p10"] for f in drafts) <= x <= max(f["p90"] for f in drafts),
        )
    if claim == "conflicting":
        return {**rec, "verdict": "excluded", "reason": "conflicting"}
    if claim:
        right = material and (claim == "up") == (x > 0)
        reason = None if right else ("wrong_direction" if material else "not_material")
        return {**rec, "verdict": "correct" if right else "incorrect", "reason": reason}
    if material:
        return {**rec, "verdict": "missed", "reason": "not_predicted" if ran else "no_run"}
    return {**rec, "verdict": "quiet", "reason": None}


# -- scoring every move ------------------------------------------------------------------------------------------


def score(today: Optional[str] = None, series: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """Every trial morning's moves scored, or left pending; final ones kept as they were (the ``trial_score`` job)."""
    today = today or date.today().isoformat()
    m = shadow.model()
    cfg = settings()
    series = shadow.realised.series() if series is None else series
    by_unit: Dict[tuple, List[Dict[str, Any]]] = {}
    days_of_view = {t["view_id"]: d for d, ts in daily.days().items() for t in ts if t.get("view_id")}
    for f in shadow.rows():
        d = days_of_view.get(f["view_id"])
        if d:
            by_unit.setdefault((d, f["horizon"], f["factor"]), []).append(f)
    with db.tx() as con:
        final = {r["id"] for r in con.execute(f"select id from eval_scores where verdict in {FINAL}")}
    now, rows, out = time.time(), [], {v: 0 for v in VERDICTS}
    for mo in mornings(today):
        for h in shadow.HORIZON_DAYS:
            for f in m.factors:
                sid = f"{mo['day']}:{h}:{f.id}"
                if sid in final:
                    continue
                got = judge_move(
                    mo["day"],
                    h,
                    f,
                    by_unit.get((mo["day"], h, f.id), []),
                    mo["status"] == "ran",
                    series,
                    today,
                    cfg,
                    m.horizons[h],
                )
                got["morning"] = mo["status"]
                out[got["verdict"]] += 1
                rows.append((sid, mo["day"], h, f.id, got["verdict"], now, db.dumps(got)))
    with db.tx() as con:
        con.executemany("insert or replace into eval_scores values (?, ?, ?, ?, ?, ?, ?)", rows)
    return out


def scores(day: Optional[str] = None) -> List[Dict[str, Any]]:
    q, args = "select * from eval_scores", ()
    if day:
        q, args = q + " where day = ?", (day,)
    with db.tx() as con:
        return [db.load(r) for r in con.execute(q + " order by day, horizon, factor", args)]


def get(score_id: str) -> Optional[Dict[str, Any]]:
    with db.tx() as con:
        return db.load(con.execute("select * from eval_scores where id = ?", (score_id,)).fetchone())


# -- the rates ---------------------------------------------------------------------------------------------------


def _share(k: int, n: int) -> Optional[float]:
    return round(k / n, 3) if n else None


def _mean(xs: List[float]) -> Optional[float]:
    return round(sum(xs) / len(xs), 4) if xs else None


def _tail(k: int, n: int) -> Optional[float]:
    """The chance of ``k`` or more right in ``n`` calls by a coin toss (one-sided binomial at ½)."""
    return round(sum(math.comb(n, i) for i in range(k, n + 1)) / 2**n, 4) if n else None


def call_direction(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """When the agent calls a move up or down (correct or incorrect, the market moved): how often the market went
    its way, however far. Beside it the best naive call on the same moves (always up, or always down: the share the
    market took the more common way, known only afterwards) and the chance a coin toss does as well."""
    calls = [r for r in rows if r["verdict"] in ("correct", "incorrect") and r.get("realised")]
    hits = sum(1 for r in calls if (r["claim"] == "up") == (r["realised"] > 0))
    ups = sum(1 for r in calls if r["realised"] > 0)
    naive = max(ups, len(calls) - ups)
    return {
        "value": _share(hits, len(calls)),
        "hits": hits,
        "n": len(calls),
        "naive": {
            "value": _share(naive, len(calls)),
            "hits": naive,
            "n": len(calls),
            "claim": "up" if ups * 2 > len(calls) else "down",
        },
        "p": _tail(hits, len(calls)),
    }


def rates(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Precision, recall, direction (over every move, and when the agent calls one) and error over ``rows``, each
    with its count; coverage beside them."""
    v = {k: [r for r in rows if r["verdict"] == k] for k in VERDICTS}
    wrong_dir = [r for r in v["incorrect"] if r.get("reason") == "wrong_direction"]
    missed_agent = [r for r in v["missed"] if r.get("reason") == "not_predicted"]
    missed_no_run = [r for r in v["missed"] if r.get("reason") == "no_run"]
    called = len(v["correct"]) + len(v["incorrect"])
    material_ran = len(v["correct"]) + len(wrong_dir) + len(missed_agent)
    material_all = material_ran + len(missed_no_run)
    dirs = [
        r
        for r in rows
        if r.get("direction_hit") is not None and r["verdict"] in ("correct", "incorrect", "missed", "quiet")
    ]
    err = [r["error_sd"] for r in rows if r.get("error_sd") is not None and r["verdict"] in FINAL[:4]]
    excluded = {}
    for r in v["excluded"]:
        excluded[r["reason"]] = excluded.get(r["reason"], 0) + 1
    return {
        "precision": {"value": _share(len(v["correct"]), called), "hits": len(v["correct"]), "n": called},
        "recall": {"value": _share(len(v["correct"]), material_ran), "hits": len(v["correct"]), "n": material_ran},
        "recall_all": {"value": _share(len(v["correct"]), material_all), "hits": len(v["correct"]), "n": material_all},
        "direction": {
            "value": _share(sum(r["direction_hit"] for r in dirs), len(dirs)),
            "hits": sum(r["direction_hit"] for r in dirs),
            "n": len(dirs),
        },
        "call_direction": call_direction(rows),
        "error_sd": {"value": _mean(err), "n": len(err)},
        "counts": {k: len(x) for k, x in v.items()},
        "missed": {"not_predicted": len(missed_agent), "wrong_direction": len(wrong_dir), "no_run": len(missed_no_run)},
        "not_material_calls": len(v["incorrect"]) - len(wrong_dir),
        "coverage": {
            "moves": len(rows),
            "due": sum(1 for r in rows if r.get("is_due", r.get("reason") != "not_due")),
            "scored": len(v["correct"]) + len(v["incorrect"]) + len(v["missed"]) + len(v["quiet"]),
            "pending": len(v["pending"]),
            "failed": len(v["failed"]),
            "excluded": len(v["excluded"]),
            "excluded_by": excluded,
        },
    }


def timeline(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Precision, recall and the call direction as they stood after each due day, over the moves scored by then
    (View B's chart)."""
    done = [r for r in rows if r["verdict"] in FINAL[:4] and r.get("due")]
    out = []
    for d in sorted({r["due"] for r in done}):
        x = rates([r for r in done if r["due"] <= d])
        out.append(
            {
                "day": d,
                "precision": x["precision"],
                "recall": x["recall"],
                "call_direction": {k: x["call_direction"][k] for k in ("value", "hits", "n")},
                "scored": x["coverage"]["scored"],
            }
        )
    return out


def by_factor_error(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """The mean absolute error per factor, in the factor's own unit (bp, % …), with n."""
    out: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        if r.get("error") is None or r["verdict"] not in FINAL[:4]:
            continue
        o = out.setdefault(r["factor"], {"unit": r.get("unit"), "errors": []})
        o["errors"].append(r["error"])
    return {k: {"unit": o["unit"], "mae": _mean(o["errors"]), "n": len(o["errors"])} for k, o in out.items()}


# -- the agents' choice of events against the reference (§2.5) ---------------------------------------------------


def event_recall() -> Dict[str, Any]:
    """Of the important reference stories TCB collected inside each morning's window (``daily.candidates``: since
    the run before, at most 36 h), how many reached that morning's events. A miss says where it was lost: the
    classifier's (``not_candidate``: low relevance or held), the window's (``earlier_run``: TCB's copy came out
    before it, so an earlier run had it; ``later_run``: after the run), the cap's (``beyond_limit``: not among the
    newest ``MAX_NEWS`` the grouping saw, rebuilt from the items' publication times) or the grouping's
    (``not_grouped``)."""
    from news import store as news_store

    evs, notes = daily.days(), daily.notes()
    with news_store._db() as con:
        rows = con.execute(
            "select published, first_seen, data from reference_stories where judged is not null and collected = 1"
        ).fetchall()
    stories = [{"at": r["published"] or r["first_seen"], **json.loads(r["data"])} for r in rows]
    out, misses, hits, n, last = [], [], 0, 0, None
    for day in sorted(evs):
        ts = evs[day]
        start = (notes.get(day) or {}).get("started") or min(t["created"] for t in ts)
        since = max(last or start - daily.WINDOW_S, start - daily.MAX_WINDOW_S)
        last = max(t["created"] for t in ts)
        used = {i for t in ts for i in t.get("news_ids") or []}
        offered = [
            i["id"]
            for i in news_store.inbox(status="all", since=since, limit=None)
            if not i["held"] and i.get("relevance") in ("high", "medium") and (i.get("published") or 0) <= start
        ][: daily.MAX_NEWS]
        mine = [s for s in stories if since <= s["at"] < start and (s.get("match") or {}).get("news_id")]
        items = {i["id"]: i for i in news_store.get([s["match"]["news_id"] for s in mine])}
        got = 0
        for s in mine:
            nid = s["match"]["news_id"]
            if nid in used:
                got += 1
                continue
            it = items.get(nid) or {}
            candidate = it.get("relevance") in ("high", "medium") and not it.get("held")
            if nid in offered:
                why = "not_grouped"
            elif not candidate:
                why = "not_candidate"
            else:  # TCB's own copy came out before the window (the run before had it), after the run, or past the cap
                at = it.get("published") or 0
                why = "earlier_run" if at < since else "later_run" if at > start else "beyond_limit"
            misses.append({"day": day, "title": s.get("title"), "news_id": nid, "why": why})
        hits, n = hits + got, n + len(mine)
        out.append({"day": day, "important": len(mine), "in_events": got, "offered": len(offered)})
    return {"value": _share(hits, n), "hits": hits, "n": n, "by_day": out, "misses": misses}


def summary(today: Optional[str] = None) -> Dict[str, Any]:
    """View B's accuracy block: per horizon overall and by family, the mornings, the errors, the event recall."""
    rows = scores()
    out = {}
    for h in shadow.HORIZON_DAYS:
        mine = [r for r in rows if r["horizon"] == h]
        out[h] = {
            **rates(mine),
            "uncalibrated": h in shadow.UNCALIBRATED,
            "by_family": {fam: rates([r for r in mine if r.get("family") == fam]) for fam in segments.FAMILIES},
            "by_factor_error": by_factor_error(mine),
            "first_due": min((r["due"] for r in mine), default=None),
            "timeline": timeline(mine),
        }
    return {
        "settings": settings(),
        "mornings": mornings(today or date.today().isoformat()),
        "horizons": out,
        "event_recall": event_recall(),
        "families": segments.FAMILIES,
    }


def moves() -> List[Dict[str, Any]]:
    """Every move in brief, for the page's list (the full record is ``detail``)."""
    keep = ("id", "day", "horizon", "factor", "family", "verdict", "reason", "claim", "move", "realised", "due")
    names = {f.id: f.name for f in shadow.model().factors}
    return [{**{k: r.get(k) for k in keep}, "factor_name": names.get(r["factor"])} for r in scores()]


def detail(score_id: str) -> Optional[Dict[str, Any]]:
    """One move from news to VND: the morning's events and their news behind each draft, the merged claim, the
    realised move, the verdict and its reason, and the simulated VND per family (None without a snapshot)."""
    from news import store as news_store
    from trial import finance

    s = get(score_id)
    if s is None:
        return None
    f = next((x for x in shadow.model().factors if x.id == s["factor"]), None)
    evs = {e["event_id"]: e for e in daily.days().get(s["day"], [])}
    drafts = []
    for d in s.get("drafts") or []:
        e = evs.get(d.get("event_id")) or {}
        news = news_store.get(list(e.get("news_ids") or []))
        drafts.append(
            {
                **d,
                "event": e.get("title"),
                "news": [
                    {
                        "id": n["id"],
                        "title": n.get("title"),
                        "source": n.get("source"),
                        "url": n.get("url"),
                        "published": n.get("published"),
                    }
                    for n in news
                ],
            }
        )
    snap = finance.snapshot(s["day"])
    return {
        **s,
        "factor_name": f.name if f else s["factor"],
        "drafts": drafts,
        "vnd": finance.value(s, snap),
        "family_names": (snap or {}).get("families", {}),
        "label": finance.LABEL,
    }
