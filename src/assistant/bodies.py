"""Each assistant route's request contract (Service(body=...), app/main.py): the fields it accepts, which are
required, and their defaults. The functions are never called; assistant_flow's graph.py serves every route."""


def turn(message=None, role="client", client_id=None, scope="personal", route=None, goals=None, turn_id=None,
         approvals=None, conversation_id=None, graph=None, attachments=None):  # fmt: skip
    ...


def copilot(question=None, role="client", client_id=None, scope="personal", route=None, confirm=None, goals=None):
    ...


def conversations(action="list", conversation_id=None, role="client", client_id=None, title=None):
    ...


def memory(action="list", item_id=None, text=None, kind=None, query=None, role="client", client_id=None,
           file_name=None, data=None, key=None):  # fmt: skip
    ...


def attach(role="client", client_id=None, file_name=None, data=None):
    ...
