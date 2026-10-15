"""search_flow: the header's search box (POST /api/search)."""

from operonx import END, START, graph

from consolidate.graph import consolidate_flow
from scenarios.ops import goals, profile_of
from search.ops import check_request, search


@graph
def search_flow(q, role, client_id=None, scope="personal"):
    """Hits for q among what the role may open, each with its route."""
    ask = check_request(q=q, role=role, client_id=client_id, scope=scope)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    who = profile_of(client_id=ask["client_id"], members=held["members"])
    mine = goals(client_id=ask["client_id"], holdings=held["holdings"], profile=who["profile"])
    out = search(q=ask["q"], role=ask["role"], holdings=held["holdings"], goals=mine["goals"])
    START >> ask >> held >> who >> mine >> out >> END
