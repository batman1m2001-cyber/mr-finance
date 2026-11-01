"""Each policy route's request contract (Service(body=...), app/main.py): the fields it accepts, which are required,
and their defaults. The functions are never called; policy_flow's graph.py serves every route."""


def add(item, by):
    ...


def verify(document_id, by, note=""):
    ...


def status(document_id, status, by, note="", date=None):
    ...


def summarise(document_id, by, mode=""):
    ...
