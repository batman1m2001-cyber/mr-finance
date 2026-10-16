"""newsletter_draft_flow and newsletter_act_flow (POST /api/newsletters, /api/newsletters/act; FR-801)."""

from operonx import END, START, graph

from newsletter.ops import act, draft


@graph
def newsletter_draft_flow(view_ids, by, title="", mode="template", distribution=None, conflict=None):
    """A CIO drafts a newsletter from approved views."""
    done = draft(view_ids=view_ids, by=by, title=title, mode=mode, distribution=distribution, conflict=conflict)
    START >> done >> END


@graph
def newsletter_act_flow(newsletter_id, action, by, note="", changes=None):
    """One step on a newsletter."""
    done = act(newsletter_id=newsletter_id, action=action, by=by, note=note, changes=changes)
    START >> done >> END
