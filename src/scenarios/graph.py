"""scenario_flow: the client's picture → a life event or a stress test → numbers and two options."""

from operonx import END, START, graph
from operonx.app.serve import egress, ingress
from operonx.core.ops import if_

from consolidate.graph import consolidate_flow
from scenarios.ops import answer, kind_of, life, profile_of, read_request, stress


@graph
def scenario_flow(client_id, scenario, params, scope):
    """One simulation, on this client's own holdings."""
    held = consolidate_flow(client_id=client_id, scope=scope)
    who = profile_of(client_id=client_id, members=held["members"])
    kind = kind_of(scenario=scenario)
    tried = life(
        client_id=client_id, scenario=scenario, params=params, holdings=held["holdings"], profile=who["profile"]
    )
    shocked = stress(
        client_id=client_id, scenario=scenario, params=params, holdings=held["holdings"], profile=who["profile"]
    )
    out = answer(life_result=tried["result"], stress_result=shocked["result"])
    START >> held >> who >> kind >> if_(kind["stress"] == True, shocked).else_(tried)  # noqa: E712
    tried >> out
    shocked >> out
    out >> END


@graph
def scenario_api():
    """POST {client_id, scenario, params?, scope?} → the simulation."""
    req = ingress()
    ask = read_request(item=req["item"])
    sim = scenario_flow(client_id=ask["client_id"], scenario=ask["scenario"], params=ask["params"], scope=ask["scope"])
    out = egress(item=sim["result"])
    START >> req >> ask >> sim >> out >> END
