"""alerts_flow: the client's holdings and profile → every factor scored → the alerts, kept.

sweep_flow runs it for every client on the morning schedule (app/main.py)."""

from operonx import END, START, graph
from operonx.app.serve import egress, ingress

from consolidate.graph import consolidate_flow
from impact.ops import keep, profile_of, read_request, score, sweep_all


@graph
def alerts_flow(client_id, scope):
    """What is moving this client's wealth: each policy, macro move and project, in VND."""
    held = consolidate_flow(client_id=client_id, scope=scope)
    who = profile_of(client_id=client_id, members=held["members"])
    found = score(holdings=held["holdings"], profile=who["profile"])
    kept = keep(client_id=client_id, scope=scope, alerts=found["alerts"], net_worth=found["net_worth"])
    START >> held >> who >> found >> kept >> END


@graph
def alerts_api():
    """POST {client_id, scope?} → the alerts."""
    req = ingress()
    ask = read_request(item=req["item"])
    alerts = alerts_flow(client_id=ask["client_id"], scope=ask["scope"])
    out = egress(item=alerts["report"])
    START >> req >> ask >> alerts >> out >> END


@graph
def sweep_flow():
    """Each tick of the morning schedule: every client's alerts again."""
    tick = ingress()
    swept = sweep_all(tick=tick["item"])
    out = egress(item=swept["summary"])
    START >> tick >> swept >> out >> END
