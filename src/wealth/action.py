"""The `action` a feature flow was given, as a value an `if_` can read (a route binds its action with `variants`, so
inside the graph function it is a plain string; a branch needs a Ref). docs/FEATURE_FLOWS_PLAN.md."""

from operonx import op


@op
def route(action: str = None) -> dict:
    return {"action": action}
