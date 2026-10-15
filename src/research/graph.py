"""research_upload_flow, research_release_flow, goal_outflow_flow: served on POST /api/research,
POST /api/research/release and POST /api/goals/outflow (app/main.py)."""

from operonx import END, START, graph

from research.ops import declare_outflow, release, upload


@graph
def research_upload_flow(item, by):
    """Upload a report, house view or regulation note."""
    done = upload(item=item, by=by)
    START >> done >> END


@graph
def research_release_flow(item_id, decision, by, note=""):
    """Compliance releases or rejects an uploaded item."""
    done = release(item_id=item_id, decision=decision, by=by, note=note)
    START >> done >> END


@graph
def goal_outflow_flow(family_id, goal_id, purpose, by, country=""):
    """The RM declares a goal's outflow purpose and destination."""
    done = declare_outflow(family_id=family_id, goal_id=goal_id, purpose=purpose, by=by, country=country)
    START >> done >> END
