"""The control group and the business effect (BRD-RULE-MEAS-06 “clients with versus without the tool, quarterly”;
BRD_REMAINING_PLAN G9, G-D8).

- **Who.** A share of the families (configuration ``control_group``: the CIO, two people; default 10 %), drawn
  within each stratum (segment × assigned RM) so both groups look alike. The draw is seeded: each family's place in
  its stratum is the SHA-256 of ``seed|family``, and a stratum of ``n`` takes ``⌊share·n + u⌋`` families, ``u`` in
  [0, 1) from the SHA-256 of ``seed|stratum`` (randomised rounding: on average exactly ``share``). Anyone holding
  the configuration draws the same group again.
- **What is withheld: signals, never data or service.** A control family still gets every run (computing is
  unchanged) and the client still sees everything. Their RM sees no Hôm nay case or goal task for them and no news
  or regulation item in their “Điều đáng chú ý”; a contact cannot cite a signal for them.
- **The effect, by quarter.** For each group: contacts per family per month (contacts/store.py), the share of goals
  “Đạt” after the latest effective run of the quarter (apply/goals.py), and action recommendations approved per
  family (the RM queue). The difference tool − control with a 90 % interval (Welch, normal approximation); with fewer
  than two families in a group the interval is not given. The demo's five families cannot show an effect: the
  measure is built and tested here, the effect needs a pilot.
"""

from __future__ import annotations

import hashlib
import math
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

Z90 = 1.6449  # two-sided 90 %


def _h(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def _cfg() -> Dict[str, Any]:
    from control import config

    return config.data("control_group")


def strata(cfg: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
    """Every family (main client) by stratum key, e.g. ``segment=Priority|rm=rm01``."""
    from people import store

    cfg = cfg or _cfg()
    out: Dict[str, List[str]] = {}
    for fid in store.client_ids():
        c = store.client(fid)
        parts = []
        for s in cfg["strata"]:
            parts.append(f"segment={c.get('segment')}" if s == "segment" else f"rm={store.assigned_rm(fid)}")
        out.setdefault("|".join(parts) or "all", []).append(fid)
    return out


_DRAWN: Dict[tuple, List[str]] = {}  # (configuration, RM assignment, state file) → the group: a read draws it once


def members(cfg: Optional[Dict[str, Any]] = None) -> List[str]:
    """The control families, drawn again from the configuration."""
    import json

    from control import config
    from wealth.paths import state_path

    cfg = cfg or _cfg()
    key = (json.dumps(cfg, sort_keys=True), json.dumps(config.data("rm_assignment"), sort_keys=True), str(state_path()))
    if key not in _DRAWN:
        _DRAWN[key] = _draw(cfg)
    return list(_DRAWN[key])


def _draw(cfg: Dict[str, Any]) -> List[str]:
    seed, share = cfg["seed"], float(cfg["share"])
    out = []
    for key, fams in sorted(strata(cfg).items()):
        u = _h(f"{seed}|{key}") / 16**12
        k = math.floor(share * len(fams) + u)
        out += sorted(fams, key=lambda f: _h(f"{seed}|{f}"))[:k]
    return sorted(out)


def is_control(family_id: str) -> bool:
    from people import store

    c = store.client(family_id) if family_id in store.client_ids(members=True) else None
    head = (c or {}).get("member_of") or family_id
    return head in members()


def _quarter(t: float) -> str:
    d = datetime.fromtimestamp(t)
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def _diff(a: List[float], b: List[float]) -> Dict[str, Any]:
    """Mean of each group, the difference a − b and its 90 % interval (None with fewer than two in a group)."""

    def mean(x):
        return sum(x) / len(x) if x else None

    def var(x):
        m = mean(x)
        return sum((v - m) ** 2 for v in x) / (len(x) - 1)

    out = {"tool": mean(a), "control": mean(b), "n_tool": len(a), "n_control": len(b), "diff": None, "low": None}
    out["high"] = None
    if a and b:
        out["diff"] = out["tool"] - out["control"]
    if len(a) >= 2 and len(b) >= 2:
        se = math.sqrt(var(a) / len(a) + var(b) / len(b))
        out["low"], out["high"] = out["diff"] - Z90 * se, out["diff"] + Z90 * se
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out.items()}


def effect(now: Optional[float] = None) -> Dict[str, Any]:
    """The quarterly comparison, every quarter that has a contact, a run or a decision (newest last)."""
    from apply import run as runs
    from control import db
    from people import store
    from wealth import store as wealth

    now = time.time() if now is None else now
    cfg = _cfg()
    control = set(members(cfg))
    families = store.client_ids()
    head = {c: (store.client(c).get("member_of") or c) for c in store.client_ids(members=True)}
    with db.tx() as con:
        contacts = [(r["at"], r["family_id"]) for r in con.execute("select at, family_id from rm_contacts")]
    effective = []
    for r in runs.runs():
        eff = next((h["at"] for h in r.get("history", []) if h.get("status") == "EFFECTIVE"), None)
        if eff is not None:
            effective.append((eff, r["id"]))
    approved = [(i["decided"], head.get(i["client_id"], i["client_id"])) for i in wealth.reviews(status="approved")]
    quarters = sorted({_quarter(t) for t, _ in contacts + effective + approved if t})
    out = []
    for q in quarters:
        months = _months_in(q, now)
        per: Dict[str, Dict[str, float]] = {f: {"contacts": 0.0, "actions": 0.0} for f in families}
        for t, f in contacts:
            if _quarter(t) == q and f in per:
                per[f]["contacts"] += 1 / months
        for t, f in approved:
            if t and _quarter(t) == q and f in per:
                per[f]["actions"] += 1
        last = max((x for x in effective if _quarter(x[0]) == q), default=None)
        goals: Dict[str, float] = {}
        if last:
            for f in families:
                try:
                    gs = runs.family_result(last[1], f).get("goal_impact", {}).get("goals", [])
                except KeyError:
                    continue
                if gs:
                    goals[f] = sum(1 for g in gs if g["after"]["level"] == "Đạt") / len(gs)
        tool = [f for f in families if f not in control]
        ctl = [f for f in families if f in control]
        out.append(
            {
                "quarter": q,
                "months": round(months, 2),
                "contacts": _diff([per[f]["contacts"] for f in tool], [per[f]["contacts"] for f in ctl]),
                "goals": _diff([goals[f] for f in tool if f in goals], [goals[f] for f in ctl if f in goals]),
                "actions": _diff([per[f]["actions"] for f in tool], [per[f]["actions"] for f in ctl]),
            }
        )
    return {
        "quarters": out,
        "control": sorted(control),
        "families": len(families),
        "share": cfg["share"],
        "seed": cfg["seed"],
        "strata": cfg["strata"],
    }


def _months_in(quarter: str, now: float) -> float:
    """The quarter's months so far (a quarter still running counts the part passed, at least one day)."""
    year, qn = int(quarter[:4]), int(quarter[-1])
    start = datetime(year, 3 * qn - 2, 1).timestamp()
    end = datetime(year + (qn == 4), 1 if qn == 4 else 3 * qn + 1, 1).timestamp()
    return max(min(now, end) - start, 86400) / (end - start) * 3
