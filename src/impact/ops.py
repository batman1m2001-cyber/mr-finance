"""The alerts' steps: the profile, every factor scored, the alerts kept; and the daily sweep."""

from __future__ import annotations

from typing import Any, Dict, Iterator, List

from operonx import invoke, op

from impact import _rules
from wealth import fixtures, profile, store

SEVERITY = {"high": "Cao", "medium": "Trung bình", "low": "Thấp"}


@op
def read_request(item: dict = None) -> dict:
    """``{"client_id", "scope"?}``."""
    item = item or {}
    client_id = str(item.get("client_id") or "")
    if client_id not in fixtures.client_ids(members=True):
        raise ValueError(f"no client {client_id!r}")
    return {"client_id": client_id, "scope": item.get("scope") or "personal"}


@op
def profile_of(client_id: str, members: list) -> dict:
    """The profile the alerts read: income, dependents, dated payments."""
    return {"profile": profile.build(client_id, members)}


@op
def score(holdings: list, profile: dict) -> dict:
    """Every factor against the client's holdings: impact = exposure × sensitivity × probability,
    in VND and as a share of net worth, with its severity and source."""
    mk = fixtures.market()
    assets = sum(h["value"] for h in holdings if h["kind"] == "asset")
    nw = assets - sum(h["value"] for h in holdings if h["kind"] == "liability")
    alerts: List[Dict[str, Any]] = []
    for f in fixtures.factors()["factors"]:
        for i, hit in enumerate(_rules.RULES[f["rule"]["type"]](f, holdings, profile, mk)):
            impact = hit["raw"] * f["probability"]
            share = impact / nw if nw else 0.0
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
                    "impact_pct": share,
                    "severity": _rules.severity(share),
                    "severity_label": SEVERITY[_rules.severity(share)],
                    "opportunity": impact > 0,
                    "message": hit["message"],
                    "affected": hit["affected"],
                    "source": f["source"],
                }
            )
    alerts.sort(key=lambda a: -abs(a["impact"]))
    return {"alerts": alerts, "net_worth": nw}


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


@op
async def sweep_all(tick: dict = None) -> dict:
    """The morning sweep: every client's alerts again, each as a step of this run."""
    from impact.graph import alerts_flow

    done = []
    for item in every_client():
        out = await invoke(alerts_flow, **item)
        rep = out["report"]
        done.append({"client_id": item["client_id"], "high": rep["counts"]["high"], "alerts": len(rep["alerts"])})
    return {"summary": {"tick": (tick or {}).get("tick"), "clients": done}}
