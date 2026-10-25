"""The agents' scored moves in VND on the simulated book (AGENT_EVALUATION_PLAN §2.6): a counterfactual, never a
claim that the agents caused a gain or a loss.

Each trial morning the families' holdings are frozen once (``eval_snapshots``), through the dashboard's read
(``apply.run.family_holdings``), as each family's exposure E[h][family][factor]: the VND one unit of the factor's
move changes, from the engine's own loadings (``engine.loadings.exposures``). A morning frozen after it ran is
labelled ``late``. For a scored move with realised x, per family:

- the move's effect on the book: E × x;
- a correct claim is worth +|E x|, an incorrect one −|E x| (a position the size of the exposure, in the claimed
  direction); a correct negative warning is a correct claim where E × x < 0;
- a missed move is a missed opportunity of |E x|, shown beside the net, never netted;
- net = correct − incorrect.

Pending, excluded and failed moves add nothing; a move without a snapshot is unavailable, never 0.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from control import db
from engine.loadings import exposures
from trial import daily, segments, shadow

LABEL = "mô phỏng: nếu gia đình làm theo toàn bộ"
VALUED = ("correct", "incorrect", "missed", "quiet")


def freeze(families: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """E[h][family][factor] in VND per unit of the factor's move, the families' holdings as read now."""
    m = shadow.model()
    out: Dict[str, Dict[str, Dict[str, float]]] = {}
    for h, months in m.horizons.items():
        out[h] = {}
        for cid, fam in families.items():
            e: Dict[str, float] = {}
            for x in exposures(fam["holdings"], m, months):
                for f, load in x.loads.items():
                    e[f] = e.get(f, 0.0) + x.sign * x.value * load
            out[h][cid] = {f: round(v) for f, v in e.items() if round(v)}
    return {"exposure": out, "families": {cid: fam["name"] for cid, fam in families.items()}, "model": m.version}


def snapshot(day: str) -> Optional[Dict[str, Any]]:
    with db.tx() as con:
        r = con.execute("select * from eval_snapshots where day = ?", (day,)).fetchone()
    return db.load(r)


def snapshots() -> Dict[str, Dict[str, Any]]:
    with db.tx() as con:
        return {r["day"]: db.load(r) for r in con.execute("select * from eval_snapshots")}


async def keep(day: str, late: bool = False, families: Optional[Dict[str, Any]] = None) -> bool:
    """The morning's exposures frozen, once: a second call keeps the first."""
    if snapshot(day):
        return False
    if families is None:
        from apply.run import family_holdings

        families = await family_holdings()
    data = {**freeze(families), "late": bool(late)}
    if late:  # a late book is the morning's only if no holding was written since (the proof, kept beside it)
        from wealth import store as wealth_store

        with wealth_store._db() as con:
            data["holdings_written"] = con.execute("select max(created) from holdings").fetchone()[0]
    with db.tx() as con:
        con.execute("insert or ignore into eval_snapshots values (?, ?, ?)", (day, time.time(), db.dumps(data)))
    return True


async def keep_missing(today: str) -> List[str]:
    """A late snapshot for every trial morning before ``today`` that has none (the ``trial_score`` job)."""
    from trial import evaluate

    done = []
    for mo in evaluate.mornings(today):
        if mo["day"] < today and await keep(mo["day"], late=True):
            done.append(mo["day"])
    return done


# -- one move in VND ---------------------------------------------------------------------------------------------


def value(score: Dict[str, Any], snap: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """A scored move's VND per family, or None when it is not scored (pending, excluded, failed) or has no snapshot."""
    if score["verdict"] not in VALUED or score.get("realised") is None or not snap:
        return None
    x, exp = score["realised"], score.get("expected")
    fams = {}
    for cid, e in (snap["exposure"].get(score["horizon"]) or {}).items():
        ex = e.get(score["factor"], 0.0)
        if not ex:
            continue
        eff = ex * x
        fams[cid] = {
            "exposure": ex,
            "effect": round(eff),
            "predicted": None if exp is None else round(ex * exp),
            "value": round(abs(eff))
            if score["verdict"] == "correct"
            else -round(abs(eff))
            if score["verdict"] == "incorrect"
            else 0,
            "opportunity": round(abs(eff)) if score["verdict"] == "missed" else 0,
            "warning": score["verdict"] == "correct" and eff < 0,
        }
    return {"families": fams, "late": snap.get("late", False), "label": LABEL}


# -- the totals --------------------------------------------------------------------------------------------------


def _totals(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The VND sums over ``rows`` (scores with their ``vnd``), each with its n of moves."""

    def acc(pred, field):
        xs = [r for r in rows if r.get("vnd") and pred(r)]
        return {"vnd": sum(sum(f[field] for f in r["vnd"]["families"].values()) for r in xs), "n": len(xs)}

    correct = acc(lambda r: r["verdict"] == "correct", "value")
    incorrect = acc(lambda r: r["verdict"] == "incorrect", "value")
    warn = [r for r in rows if r.get("vnd") and r["verdict"] == "correct"]
    warnings = {
        "vnd": sum(f["value"] for r in warn for f in r["vnd"]["families"].values() if f["warning"]),
        "n": sum(1 for r in warn if any(f["warning"] for f in r["vnd"]["families"].values())),
    }
    scored = [r for r in rows if r["verdict"] in VALUED and r.get("realised") is not None]
    return {
        "correct": correct,
        "incorrect": {"vnd": -incorrect["vnd"], "n": incorrect["n"]},  # the loss, as a positive amount
        "negative_warnings": warnings,
        "missed_opportunity": acc(lambda r: r["verdict"] == "missed", "opportunity"),
        "net": {"vnd": correct["vnd"] + incorrect["vnd"], "n": correct["n"] + incorrect["n"]},
        "effect": acc(lambda r: True, "effect"),
        "scored": len(scored),
        "unavailable": sum(1 for r in scored if not r.get("vnd")),  # scored, no snapshot: not 0, not counted
        "late": sum(1 for r in rows if r.get("vnd") and r["vnd"]["late"]),
    }


def timeline(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The simulated net VND as it added up by due day, per group (View B's chart): scored moves with a snapshot."""
    valued = [r for r in rows if r.get("vnd") and r.get("due") and r.get("family") in segments.FAMILIES]
    run, n, out = {g: 0 for g in segments.FAMILIES}, 0, []
    for d in sorted({r["due"] for r in valued}):
        for r in (r for r in valued if r["due"] == d):
            run[r["family"]] += sum(f["value"] for f in r["vnd"]["families"].values())
            n += 1
        out.append({"day": d, "by_family": dict(run), "n": n})
    return out


def summary(rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """View B's money block per horizon, overall and by the four groups, labelled simulated."""
    from trial import evaluate

    rows = evaluate.scores() if rows is None else rows
    snaps = snapshots()
    for r in rows:
        r["vnd"] = value(r, snaps.get(r["day"]))
    out = {}
    for h in shadow.HORIZON_DAYS:
        mine = [r for r in rows if r["horizon"] == h]
        out[h] = {
            **_totals(mine),
            "by_family": {g: _totals([r for r in mine if r.get("family") == g]) for g in segments.FAMILIES},
            "timeline": timeline(mine),
        }
    return {
        "label": LABEL,
        "horizons": out,
        "snapshots": {d: {"created": s["created"], "late": s.get("late", False)} for d, s in sorted(snaps.items())},
        "mornings": sorted(daily.days()),
    }
