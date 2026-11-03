"""Each evidence route's request contract (Service(body=...), app/main.py): the fields it accepts and their
defaults. The functions are never called; evidence_flow's graph.py serves every route."""


def read(factor=None, role=None):
    ...


def decide(factor=None, decision=None, by=None, note=""):
    ...


def draft(news_id=None, by=None, mode=""):
    ...


def draft_decide(news_id=None, decision=None, by=None, note=""):
    ...


def type(event_type=None, label=None, dates=None, series=None, by=None):
    ...
