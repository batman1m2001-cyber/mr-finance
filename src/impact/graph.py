"""alerts_flow: the client's holdings and profile → every factor scored → the alerts, kept.

Served as is on POST /api/alerts, and run for every client by the policy_sweep job — on demand,
and at 07:00 every day (app/main.py)."""

from operonx import END, START, graph

from consolidate.graph import consolidate_flow
from impact.ops import check_request, keep, profile_of, score


@graph
def alerts_flow(client_id, scope="personal"):
    """What is moving this client's wealth: each policy, macro move and project, in VND."""
    ask = check_request(client_id=client_id, scope=scope)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    who = profile_of(client_id=ask["client_id"], members=held["members"])
    found = score(holdings=held["holdings"], profile=who["profile"])
    kept = keep(client_id=ask["client_id"], scope=ask["scope"], alerts=found["alerts"], net_worth=found["net_worth"])
    START >> ask >> held >> who >> found >> kept >> END
