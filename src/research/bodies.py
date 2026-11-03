"""Each research, goal-label and newsletter route's request contract (Service(body=...), app/main.py): the fields it
accepts, which are required, and their defaults. The functions are never called; research_flow's graph.py serves
every route."""


def upload(item, by):
    ...


def release(item_id, decision, by, note=""):
    ...


def outflow(family_id, goal_id, purpose, by, country=""):
    ...


def suggest(family_id, by, mode=""):
    ...


def draft(view_ids, by, title="", mode="template", distribution=None, conflict=None, body=""):
    ...


def act(newsletter_id, action, by, note="", changes=None):
    ...
