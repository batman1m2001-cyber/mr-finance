"""Research: uploads and releases, goal outflows and suggestions, newsletters.

What this feature exposes: its SERVICES and JOBS, which app/main.py collects, and each route's
request contract (Service(body=...)): the fields it accepts, which are required, their defaults. The
contract functions are never called; the graph serves the route."""

from operonx.app import Service, http

from app.serve import PORT
from research.graph import research_flow


def upload(item, by): ...


def release(item_id, decision, by, note=""): ...


def outflow(family_id, goal_id, purpose, by, country=""): ...


def suggest(family_id, by, mode=""): ...


def draft(view_ids, by, title="", mode="template", distribution=None, conflict=None, body=""): ...


def act(newsletter_id, action, by, note="", changes=None): ...


SERVICES = [
    Service(
        "research_upload",
        http("POST", "/api/research", port=PORT),
        graph=research_flow,
        variants={"upload": {"task": "upload"}},
        body=upload,
        description="POST {item: {kind, report_no, title, summary, release_at, conflicts?, regulation?}, by}.",
    ),
    Service(
        "research_release",
        http("POST", "/api/research/release", port=PORT),
        graph=research_flow,
        variants={"release": {"task": "release"}},
        body=release,
        description=(
            "POST {item_id, decision: release|reject, by, note}: a CIO other than the one who filed it, after the "
            "release time."
        ),
    ),
    Service(
        "goal_outflow",
        http("POST", "/api/goals/outflow", port=PORT),
        graph=research_flow,
        variants={"outflow": {"task": "outflow"}},
        body=outflow,
        description="POST {family_id, goal_id, purpose, country?, by}: the RM declares a goal's outflow.",
    ),
    Service(
        "goal_suggest",
        http("POST", "/api/goals/suggest", port=PORT),
        graph=research_flow,
        variants={"suggest": {"task": "suggest"}},
        body=suggest,
        description="POST {family_id, by, mode?}: AI suggests a purpose and country for the undeclared goals (P2).",
    ),
    Service(
        "newsletter_draft",
        http("POST", "/api/newsletters", port=PORT),
        graph=research_flow,
        variants={"draft": {"task": "draft"}},
        body=draft,
        description="POST {view_ids, by, title?, mode?: template|agent, distribution?, conflict?}: a CIO drafts.",
    ),
    Service(
        "newsletter_act",
        http("POST", "/api/newsletters/act", port=PORT),
        graph=research_flow,
        variants={"act": {"task": "act"}},
        body=act,
        description="POST {newsletter_id, action: edit|submit|approve|return|withdraw, by, note?, changes?}.",
    ),
]
