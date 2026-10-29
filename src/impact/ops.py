"""The alerts' steps: the profile, every factor scored, the alerts kept; and the daily sweep's items."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterator, List

from operonx import op

from control.errors import BadRequest
from impact import _rules
from wealth import fixtures, profile, store

SEVERITY = {"high": "Cao", "medium": "Trung bình", "low": "Thấp"}
# the alerts the page states in VND (owner 2026-10-27): those on gold and bonds only, and the exchange-rate ones;
# the rest are shown as a level and a horizon
IN_VND_CLASSES = {"gold", "bond"}
FX_RULES = {"study_abroad"}


@op
def check_request(client_id: str = None, scope: str = None) -> dict:
    """What a caller sent, checked: a known client, and a scope."""
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise BadRequest(f"no client {client_id!r}")
    return {"client_id": client_id, "scope": scope or "personal"}


@op
def profile_of(client_id: str, members: list) -> dict:
    """The profile the alerts read: income, dependents, dated payments."""
    return {"profile": profile.build(client_id, members)}


def labels_of(holdings: list, profile: dict) -> Dict[str, Any]:
    """The family's labels (NEWS_EVIDENCE_BRD §7): from the holdings, the income, and its goals as the goal branch
    reads them (a goal's purpose declared by the RM, else read from its name)."""
    from evidence import labels
    from research import store as research

    client = {**fixtures.client(profile["client_id"]), "income_monthly": profile.get("income_monthly", 0)}
    return labels.of(holdings, client, research.declared(), date.today())


@op
def score(holdings: list, profile: dict) -> dict:
    """Every factor against the client's holdings: impact = exposure × sensitivity × probability,
    in VND and as a share of net worth, with its severity and source, and split by asset class (``by_class``).
    Each alert carries its approved evidence (the frame's direction, time and label, §8.2) and the client's labels
    the frame names."""
    from evidence import frames

    mk = fixtures.market()
    mine = labels_of(holdings, profile)
    profile = {**profile, "labels": mine}
    assets = sum(h["value"] for h in holdings if h["kind"] == "asset")
    nw = assets - sum(h["value"] for h in holdings if h["kind"] == "liability")
    business = {h["name"] for h in holdings if h["class"] == "business"}
    alerts: List[Dict[str, Any]] = []
    for f in fixtures.factors()["factors"]:
        ev = frames.summary(f["id"])
        for i, hit in enumerate(_rules.RULES[f["rule"]["type"]](f, holdings, profile, mk)):
            impact = hit["raw"] * f["probability"]
            certain = hit.get("certain") if ev and ev.get("certain_from") else None
            share = impact / nw if nw else 0.0
            parts = _rules.by_class(hit, holdings, impact)
            alerts.append(
                {
                    "id": f"{f['id']}-{i}",
                    "factor": f["id"],
                    "kind": f["kind"],
                    "title": f["title"],
                    "status": f["status"],
                    "status_label": f["status_label"],
                    "probability": f["probability"],
                    "exposure": round(hit["exposure"]),
                    "sensitivity": round(hit["sensitivity"], 6),
                    "impact": round(impact),
                    "by_class": parts,
                    "impact_pct": share,
                    "severity": _rules.severity(share),
                    "severity_label": SEVERITY[_rules.severity(share)],
                    "horizon": f["horizon"],
                    "horizon_label": f["horizon_label"],
                    # an item that moves only business equity is shown as good or bad news, no level or horizon
                    "sign_only": bool(hit["affected"]) and set(hit["affected"]) <= business,
                    "in_vnd": set(parts) <= IN_VND_CLASSES or f["rule"]["type"] in FX_RULES,
                    "opportunity": impact > 0,
                    "message": hit["message"],
                    "affected": hit["affected"],
                    "source": f["source"],
                    "source_url": f.get("source_url"),
                    # how News and Prediction reads it: its section, a short summary, why it matters to the holder
                    "section": f.get("section", "exclusive"),
                    "summary": f.get("summary", []),
                    "why": f.get("why", ""),
                    "evidence": ev and {k: v for k, v in ev.items() if k not in ("targets", "certain_from")},
                    "labels": _labels(ev, mine, hit),
                    "certain": certain and {"amount": round(certain["amount"]), "per": certain["per"], "from": ev["certain_from"]},
                }
            )
    alerts.sort(key=lambda a: -abs(a["impact"]))
    return {"alerts": alerts, "net_worth": nw}


def _labels(ev: Dict[str, Any], mine: Dict[str, Any], hit: Dict[str, Any]) -> List[str]:
    """The frame's labels this client has, narrowed to the ones this hit's holdings or plans gave (a rule with two hits,
    a loan and a bond, names each its own)."""
    from evidence import labels as lb

    got = lb.match(ev["targets"], mine) if ev else []
    own = [t for t in got if set(mine[t]["from"]) & set(hit["affected"])]
    return own or got


@op
def keep(client_id: str, scope: str, alerts: list, net_worth: float) -> dict:
    """The alerts as the page shows them, kept (the dashboard counts the latest)."""
    counts = {k: sum(1 for a in alerts if a["severity"] == k) for k in SEVERITY}
    out = {
        "client_id": client_id,
        "scope": scope,
        "as_of": fixtures.market()["as_of"],
        "net_worth": net_worth,
        "alerts": alerts,
        "counts": counts,
        "risks": sum(1 for a in alerts if not a["opportunity"]),
        "opportunities": sum(1 for a in alerts if a["opportunity"]),
        "total_impact": sum(a["impact"] for a in alerts),
        "note": fixtures.factors()["note"],
    }
    if scope == "personal":
        store.put_result(client_id, "alerts", out)
    return {"report": out}


def every_client() -> Iterator[Dict[str, str]]:
    """The policy sweep's items: every client, in the personal view."""
    for cid in fixtures.client_ids():
        yield {"client_id": cid, "scope": "personal"}
