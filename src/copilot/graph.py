"""copilot_flow: a question and the page it was asked on → one tool call → a templated answer (POST /api/copilot)."""

from operonx import END, START, graph

from copilot.ops import act, answer, check_request, decide


@graph
def copilot_flow(question=None, role="client", client_id=None, scope="personal", route=None, confirm=None, goals=None):
    """Ask OneWealth: the router sees only the scrubbed question and the route; our code runs the tool."""
    ask = check_request(
        question=question, role=role, client_id=client_id, scope=scope, route=route, confirm=confirm, goals=goals
    )
    pick = decide(question=ask["question"], role=ask["role"], route=ask["route"], confirm=ask["confirm"])
    done = act(
        tool=pick["tool"],
        args=pick["args"],
        confirmed=pick["confirmed"],
        role=ask["role"],
        client_id=ask["client_id"],
        scope=ask["scope"],
        question=ask["question"],
        followed=ask["followed"],
    )
    out = answer(
        result=done["result"],
        seen=pick["seen"],
        router_info=pick["router"],
        role=ask["role"],
        client_id=ask["client_id"],
    )
    START >> ask >> pick >> done >> out >> END
