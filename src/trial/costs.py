"""What the trial's model calls cost (AGENT_EVALUATION_PLAN §3): per call the agent, run, step, provider, model,
tokens in, out and cached, the cost, the latency, the attempt and the error; per agent the sums, each with its n.

A call's cost is the one its provider reported (``views.agents.usage_meta``): ``provider`` billing, or ``notional``
from the Claude Code bridge (what the subscription's calls would cost at API prices, not a bill). A call that
reported none has None, never 0, and is counted apart (``n_reported`` of ``n_calls``). Calls made before the bridge
returned its cost are backfilled from its own log (``logs/claude_bridge.jsonl``) only where exactly one line
matches the model and the tokens inside the run's time; they are kept in ``call_costs``, beside the run (the run's
nodes are hashed into the audit log and stay as written).
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from control import db
from trial import daily
from wealth.paths import ROOT

BRIDGE_LOG = ROOT / "logs" / "claude_bridge.jsonl"
SLACK_S = 5.0  # a bridge line is written as the call ends, inside its run


def _bare(model: Optional[str]) -> str:
    """``anthropic/claude-sonnet-5.5`` and ``claude-sonnet-5-5`` as one name."""
    return str(model or "").split("/")[-1].replace(".", "-")


def _backfilled() -> Dict[str, Dict[str, Any]]:
    with db.tx() as con:
        return {r["id"]: json.loads(r["data"]) for r in con.execute("select * from call_costs")}


def calls() -> List[Dict[str, Any]]:
    """Every model call of the trial: the grouping call of each morning, the CIO agent's and the challenger's steps
    on each trial draft. Rule steps (no model) are left out."""
    evs, notes, extra = daily.days(), daily.notes(), _backfilled()
    out: List[Dict[str, Any]] = []
    for day in sorted(set(evs) | set(notes)):
        g = (notes.get(day) or {}).get("group")
        ts = evs.get(day) or []
        if g is None and ts:  # before the morning kept its grouping call: the token total on its events
            g = {"tokens": ts[0].get("group_tokens"), "s": ts[0].get("group_s")}
        if g is None:
            continue
        cid = f"group:{day}"
        cost = g.get("cost_usd")
        kind = g.get("cost_kind")
        if cost is None and cid in extra:
            cost, kind = extra[cid]["cost_usd"], "notional_backfilled"
        out.append(
            {
                "id": cid,
                "day": day,
                "agent": "grouping",
                "run_id": None,
                "step": "group",
                "provider": g.get("provider"),
                "model": g.get("model"),
                "tokens_in": g.get("tokens_in"),
                "tokens_out": g.get("tokens_out"),
                "tokens": g.get("tokens")
                if g.get("tokens") is not None
                else _add(g.get("tokens_in"), g.get("tokens_out")),
                "tokens_cached": g.get("tokens_cached"),
                "cost_usd": cost,
                "cost_kind": kind,
                "ms": round(g["s"] * 1000) if g.get("s") is not None else None,
                "attempt": 1,
                "error": (notes.get(day) or {}).get("error")
                if (notes.get(day) or {}).get("stage") == "group"
                else None,
            }
        )
    views = {t["view_id"]: d for d, ts in evs.items() for t in ts if t.get("view_id")}
    if not views:
        return out
    with db.tx() as con:
        q = f"select * from agent_runs where subject_id in ({','.join('?' * len(views))}) order by created"
        runs = [db.load(r) for r in con.execute(q, list(views))]
    for g in out:  # a grouping call before 10-24 kept no model: the morning's CIO agent's (the same llm:cio)
        if g["model"] is None:
            g["model"] = next(
                (r.get("model") for r in runs if r["agent"] == "cio" and views[r["subject_id"]] == g["day"]), None
            )
    for r in runs:
        for n in r.get("nodes") or []:
            if n.get("mode") != "live":
                continue
            cid = f"{r['id']}:{n.get('seq')}"
            cost, kind = n.get("cost_usd"), n.get("cost_kind")
            if cost is None and cid in extra:
                cost, kind = extra[cid]["cost_usd"], "notional_backfilled"
            out.append(
                {
                    "id": cid,
                    "day": views[r["subject_id"]],
                    "agent": r["agent"],
                    "run_id": r["id"],
                    "subject_id": r["subject_id"],
                    "step": n.get("node"),
                    "provider": n.get("provider"),
                    "model": n.get("model"),
                    "tokens_in": n.get("tokens_in"),
                    "tokens_out": n.get("tokens_out"),
                    "tokens": _add(n.get("tokens_in"), n.get("tokens_out")),
                    "tokens_cached": n.get("tokens_cached"),
                    "cost_usd": cost,
                    "cost_kind": kind,
                    "ms": n.get("ms"),
                    "attempt": n.get("attempt") or 1,
                    "error": n.get("error") or None,
                    "created": r["created"],
                    "finished": r.get("finished"),
                }
            )
    return out


def _add(a: Optional[int], b: Optional[int]) -> Optional[int]:
    return None if a is None or b is None else a + b


def _pct(xs: List[float], q: float) -> Optional[float]:
    if not xs:
        return None
    if len(xs) == 1:
        return float(xs[0])
    return round(statistics.quantiles(sorted(xs), n=100, method="inclusive")[int(q) - 1], 1)


def per_agent(rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
    """Per agent: calls, tokens, the cost of the calls that reported one (with how many did), latency, retries,
    errors."""
    rows = calls() if rows is None else rows
    out: Dict[str, Dict[str, Any]] = {}
    for agent in sorted({r["agent"] for r in rows}):
        mine = [r for r in rows if r["agent"] == agent]
        priced = [r for r in mine if r["cost_usd"] is not None]
        ms = [r["ms"] for r in mine if r.get("ms") is not None]
        out[agent] = {
            "n_calls": len(mine),
            "tokens_in": sum(r["tokens_in"] or 0 for r in mine),
            "tokens_out": sum(r["tokens_out"] or 0 for r in mine),
            "tokens": sum(r["tokens"] or 0 for r in mine),
            "n_tokens": sum(1 for r in mine if r["tokens"] is not None),
            "tokens_cached": sum(r["tokens_cached"] or 0 for r in mine),
            "n_cached_reported": sum(1 for r in mine if r["tokens_cached"] is not None),
            "cost_usd": round(sum(r["cost_usd"] for r in priced), 6) if priced else None,
            "n_reported": len(priced),
            "cost_kinds": sorted({r["cost_kind"] for r in priced if r["cost_kind"]}),
            "ms_p50": _pct(ms, 50),
            "ms_p95": _pct(ms, 95),
            "retries": sum(1 for r in mine if (r["attempt"] or 1) > 1),
            "errors": sum(1 for r in mine if r["error"]),
            "models": sorted({r["model"] for r in mine if r["model"]}),
        }
    return out


def summary() -> Dict[str, Any]:
    rows = calls()
    agents = per_agent(rows)
    priced = [r for r in rows if r["cost_usd"] is not None]
    return {
        "agents": agents,
        "total": {
            "n_calls": len(rows),
            "cost_usd": round(sum(r["cost_usd"] for r in priced), 6) if priced else None,
            "n_reported": len(priced),
            "tokens": sum(r["tokens"] or 0 for r in rows),
        },
        "calls": rows,
    }


# -- the backfill from the bridge's log --------------------------------------------------------------------------


def _log(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def match(call: Dict[str, Any], lines: Iterable[Dict[str, Any]], window: Optional[tuple] = None) -> Optional[Dict]:
    """The one bridge line for ``call`` (same model, same tokens, inside ``window``), or None for none or several."""
    want = _bare(call["model"])
    hits = []
    for ln in lines:
        u = ln.get("usage") or {}
        if ln.get("error") or u.get("usd") is None or _bare(ln.get("asked") or ln.get("model")) != want:
            continue
        if call.get("tokens_in") is not None:
            same = u.get("in") == call["tokens_in"] and u.get("out") == call["tokens_out"]
        else:  # the grouping call before 10-24 kept only in + out
            same = call.get("tokens") is not None and (u.get("in") or 0) + (u.get("out") or 0) == call["tokens"]
        if same and (window is None or window[0] <= ln["at"] <= window[1]):
            hits.append(ln)
    return hits[0] if len(hits) == 1 else None


def backfill(path: Path = BRIDGE_LOG) -> Dict[str, int]:
    """The notional cost of every trial call that reported none, from the bridge's own log; once."""
    lines = _log(path)
    evs, notes = daily.days(), daily.notes()
    got = {"matched": 0, "unmatched": 0, "already": 0}
    rows = []
    for c in calls():
        if c["cost_usd"] is not None:
            got["already"] += 1
            continue
        if c["agent"] == "grouping":
            ts = evs.get(c["day"]) or []
            start = (notes.get(c["day"]) or {}).get("started")
            first = min((t["created"] for t in ts), default=None)
            window = (first - 3600, first + SLACK_S) if first else (start, start + 3600) if start else None
        else:
            window = (c["created"], (c.get("finished") or c["created"] + 3600) + SLACK_S)
        ln = match(c, lines, window)
        if ln is None:
            got["unmatched"] += 1
            continue
        got["matched"] += 1
        rows.append((c["id"], json.dumps({"cost_usd": ln["usage"]["usd"], "at": ln["at"], "source": str(path.name)})))
    with db.tx() as con:
        con.executemany("insert or ignore into call_costs values (?, ?)", rows)
    return got
