"""Asset allocation (ASSET_ALLOCATION_BRD): the buckets, the example, tilts, sends, reviews, overrides, the method.

What this feature exposes: its SERVICES and JOBS, which app/main.py collects, and each route's
request contract (Service(body=...)): the fields it accepts, which are required, their defaults. The
contract functions are never called; the graph serves the route."""

from typing import Any, Dict, Optional

from operonx.app import Service, http

from allocation.graph import allocation_flow
from app.serve import PORT


def view(
    client_id: str,
    scope: str = "family",
    method: str = "A",
    assumptions: Optional[Dict[str, Any]] = None,
    role: Optional[str] = None,
    whatif: Optional[Dict[str, Any]] = None,
): ...


def example(method: str = "A", assumptions: Optional[Dict[str, Any]] = None, role: Optional[str] = None): ...


def tilt(asset_class: str, stance: str, view_id: str, by: str, reason: str = ""): ...


def tilts(): ...


def send(
    client_id: str, by: str, scope: str = "family", method: str = "A", assumptions: Optional[Dict[str, Any]] = None
): ...


def review(item_id: str, by: str, decisions: Optional[Dict[str, Any]] = None, note: str = ""): ...


def queue(): ...


def override(client_id: str, key: str, by: str, bucket: str = "", reason: str = "", scope: str = "family"): ...


def method(method: str, by: str): ...


SERVICES = [
    Service(
        "allocation",
        http("POST", "/api/allocation", port=PORT),
        graph=allocation_flow,
        variants={"view": {"action": "view"}},
        body=view,
        description="POST {client_id, scope?, method?, assumptions?, role?, whatif?}: three buckets, targets, actions; a what-if.",
    ),
    Service(
        "allocation_example",
        http("POST", "/api/allocation/example", port=PORT),
        graph=allocation_flow,
        variants={"example": {"action": "example"}},
        body=example,
        description="POST {method?, assumptions?, role?}: the BRD's worked example K-7F3A.",
    ),
    Service(
        "allocation_tilt",
        http("POST", "/api/allocation/tilt", port=PORT),
        graph=allocation_flow,
        variants={"tilt": {"action": "tilt"}},
        body=tilt,
        description="POST {asset_class, stance, view_id, by, reason?}: a CIO tilts the model portfolio.",
    ),
    Service(
        "allocation_tilts",
        http("POST", "/api/allocation/tilts", port=PORT),
        graph=allocation_flow,
        variants={"tilts": {"action": "tilts"}},
        body=tilts,
        description="POST {}: the CIO's tilts in force and the model each level gets.",
    ),
    Service(
        "allocation_send",
        http("POST", "/api/allocation/send", port=PORT),
        graph=allocation_flow,
        variants={"send": {"action": "send"}},
        body=send,
        description="POST {client_id, by, scope?, method?, assumptions?}: the actions to the review queue.",
    ),
    Service(
        "allocation_review",
        http("POST", "/api/allocation/review", port=PORT),
        graph=allocation_flow,
        variants={"review": {"action": "review"}},
        body=review,
        description="POST {item_id, decisions {n: approve|reject}, by, note?}: the CIO decides each action.",
    ),
    Service(
        "allocation_queue",
        http("POST", "/api/allocation/queue", port=PORT),
        graph=allocation_flow,
        variants={"queue": {"action": "queue"}},
        body=queue,
        description="POST {}: the allocations waiting for the CIO and the last ones decided.",
    ),
    Service(
        "allocation_override",
        http("POST", "/api/allocation/override", port=PORT),
        graph=allocation_flow,
        variants={"override": {"action": "override"}},
        body=override,
        description="POST {client_id, key, bucket, reason, by, scope?}: an RM's bucket override, logged.",
    ),
    Service(
        "allocation_method",
        http("POST", "/api/allocation/method", port=PORT),
        graph=allocation_flow,
        variants={"method": {"action": "method"}},
        body=method,
        description="POST {method: tilt|bl, by}: how the CIO's tilts move every client's model.",
    ),
]
