"""Writes tests/data/contract.json: every service's method, path and request contract (the graph's parameters,
which are required, their defaults), and every job's name and schedule, from the application as it is declared.
tests/test_contract.py compares the live application with it (docs/FEATURE_FLOWS_PLAN.md, FF0)."""

import inspect
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]


def contract():
    import operonx

    operonx.bootstrap(resources=str(ROOT / "resources.yaml"))
    started = time.perf_counter()
    from app.main import APP

    built = time.perf_counter() - started
    services = {}
    for s in APP.services:
        fields = None
        if callable(s.graph):
            fields = {}
            body = (s.options or {}).get("body")
            # Service(body=fn): fn's signature is the contract; otherwise the graph's parameters are
            for p in inspect.signature(body if callable(body) else s.graph).parameters.values():
                fields[p.name] = "<required>" if p.default is p.empty else repr(p.default)
        services[s.name] = {
            "kind": s.kind,
            "method": s.method,
            "path": s.path,
            "fields": fields,
        }
    jobs = {}
    for j in APP.jobs:
        jobs[j.name] = {"schedule": (getattr(j.schedule, "options", None) if j.schedule else None)}
    return {"services": services, "jobs": jobs, "responses": responses(APP)}, built


# the read-only pages: a canned request for the sample client, and the keys of the reply
CANNED = (
    "dashboard overview timeline flows feed risk alerts goals allocation allocation_example "
    "allocation_tilts allocation_queue evidence"
).split()


def responses(app):
    import asyncio
    import os
    import tempfile

    from operonx import Operon

    os.environ.update(MF_STATE=tempfile.mkdtemp() + "/state.db", MF_AI="off", MF_AUTH="off")
    out = {}
    for s in app.services:
        if s.name not in CANNED:
            continue
        params = inspect.signature(s.graph).parameters
        engine = Operon(s.graph, params={n: None for n in params})
        bound = next(iter((s.variants or {}).values()), {})  # a merged feature flow: the route's action
        inputs = {**bound, **({"client_id": "C01"} if "client_id" in params else {})}
        got = asyncio.run(engine.run(inputs=inputs))
        out[s.name] = sorted(k for k in got if k != "$state")
    return out


if __name__ == "__main__":
    data, built = contract()
    out = ROOT / "tests" / "data" / "contract.json"
    out.write_text(json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    sys.stdout.write(f"{len(data['services'])} services, {len(data['jobs'])} jobs; app built in {built:.1f}s\n")
