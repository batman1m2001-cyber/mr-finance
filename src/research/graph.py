"""research_flow: one flow for the CIO's research desk and the goals' outflow labels, plus the newsletter (FR-801),
a route picks its `task` (app/main.py binds it with `variants`, and `bodies.py` is each route's request contract).
The task is not called `action`: a newsletter step has a field of that name.

upload     POST /api/research            upload a report, house view or regulation note
release    POST /api/research/release    a second CIO releases or rejects an uploaded item
outflow    POST /api/goals/outflow       the RM declares a goal's outflow purpose and destination
suggest    POST /api/goals/suggest       AI gợi ý nhãn: a purpose and country for each goal not declared (P2)
draft      POST /api/newsletters         a CIO drafts a newsletter from approved views, or writes an article
act        POST /api/newsletters/act     one step on a newsletter"""

from operonx import END, START, graph
from operonx.core.ops import if_

from newsletter.ops import act as newsletter_step
from newsletter.ops import draft as newsletter_draft
from research.ops import declare_outflow, release, suggest_goals, upload


@graph
def research_flow(
    task="upload",
    item=None,
    by=None,
    item_id=None,
    decision=None,
    note="",
    family_id=None,
    goal_id=None,
    purpose=None,
    country="",
    mode="",
    view_ids=None,
    title="",
    distribution=None,
    conflict=None,
    body="",
    newsletter_id=None,
    action=None,
    changes=None,
):
    """The research desk, the goals' outflow labels and the newsletter: one step each, as the route says."""
    uploaded = upload(item=item, by=by)
    released = release(item_id=item_id, decision=decision, by=by, note=note)
    outflow = declare_outflow(family_id=family_id, goal_id=goal_id, purpose=purpose, by=by, country=country)
    suggested = suggest_goals(family_id=family_id, by=by, mode=mode)
    drafted = newsletter_draft(
        view_ids=view_ids, by=by, title=title, mode=mode, distribution=distribution, conflict=conflict, body=body
    )
    stepped = newsletter_step(newsletter_id=newsletter_id, action=action, by=by, note=note, changes=changes)
    t = task
    START >> if_(t == "release", released).if_(t == "outflow", outflow).if_(t == "suggest", suggested).if_(
        t == "draft", drafted
    ).if_(t == "act", stepped).else_(uploaded)
    uploaded >> END
    released >> END
    outflow >> END
    suggested >> END
    drafted >> END
    stepped >> END
