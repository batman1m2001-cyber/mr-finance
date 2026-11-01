"""scenarios_flow: one flow for the planning feature, a route picks its `action` (app/main.py binds it with `variants`,
and `bodies.py` is each route's request contract).

scenario  POST /api/scenario          the client's picture → a life event or a stress test → numbers and two options
combine   POST /api/scenario/combine  several stress tests at once on the client's holdings, no double count
goals     POST /api/goals             every life goal of a client, with its gap and status"""

from operonx import END, START, graph
from operonx.core.ops import if_

from consolidate.graph import consolidate_flow
from scenarios.ops import (
    answer,
    check_client,
    check_combine,
    check_request,
    combined,
    goals as goal_status,
    kind_of,
    life,
    profile_of,
    stress,
)
from wealth.action import route


@graph
def scenarios_flow(
    action="scenario", client_id=None, scenario=None, scenarios=None, params=None, scope="personal", goals=None
):
    """``scenario``: one simulation, on this client's own holdings. ``combine``: several stress tests at once: per
    class and per scenario, net worth, liquidity, income, expenses and goals before and after — a what-if, never net
    worth. ``goals``: every life goal with its gap and status."""
    which = route(action=action)

    ask_one = check_request(client_id=client_id, scenario=scenario, params=params, scope=scope)
    held_one = consolidate_flow(client_id=ask_one["client_id"], scope=ask_one["scope"])
    who_one = profile_of(client_id=ask_one["client_id"], members=held_one["members"])
    kind = kind_of(scenario=ask_one["scenario"])
    tried = life(
        client_id=ask_one["client_id"],
        scenario=ask_one["scenario"],
        params=ask_one["params"],
        holdings=held_one["holdings"],
        profile=who_one["profile"],
    )
    shocked = stress(
        client_id=ask_one["client_id"],
        scenario=ask_one["scenario"],
        params=ask_one["params"],
        holdings=held_one["holdings"],
        profile=who_one["profile"],
    )
    one = answer(life_result=tried["result"], stress_result=shocked["result"])

    ask_goals = check_client(client_id=client_id, scope=scope)
    held_goals = consolidate_flow(client_id=ask_goals["client_id"], scope=ask_goals["scope"])
    who_goals = profile_of(client_id=ask_goals["client_id"], members=held_goals["members"])
    status = goal_status(
        client_id=ask_goals["client_id"], holdings=held_goals["holdings"], profile=who_goals["profile"]
    )

    ask_many = check_combine(client_id=client_id, scenarios=scenarios, params=params, scope=scope, goals=goals)
    held_many = consolidate_flow(client_id=ask_many["client_id"], scope=ask_many["scope"])
    who_many = profile_of(client_id=ask_many["client_id"], members=held_many["members"])
    many = combined(
        client_id=ask_many["client_id"],
        scenarios=ask_many["scenarios"],
        params=ask_many["params"],
        holdings=held_many["holdings"],
        profile=who_many["profile"],
        followed=ask_many["followed"],
    )

    a = which["action"]
    START >> which >> if_(a == "goals", ask_goals).if_(a == "combine", ask_many).else_(ask_one)
    ask_one >> held_one >> who_one >> kind >> if_(kind["stress"] == True, shocked).else_(tried)  # noqa: E712
    tried >> one
    shocked >> one
    one >> END
    ask_goals >> held_goals >> who_goals >> status >> END
    ask_many >> held_many >> who_many >> many >> END
