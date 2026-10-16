"""The fixed eval set of the CIO agent and the challenger (BRD-RULE-MEAS-07, F-D10): sample news with expected
results (data/agent_eval.json), run on every proposal of new prompts or models before it may be approved.

Each sample goes through the same steps as a live run (``views.agents``: the analyst groups, the debate, the
synthesis with its format check and retries, the challenger), with the proposal in force for that run only
(``agents.use``), recorded as an agent run ``eval`` on the proposal's id. A sample passes when:

- the agent wrote a view that passes the format check (§8.2, AI-05, no buy/sell wording);
- the challenger answered;
- (counted over the set) the most likely branch shocks the expected factor in the expected direction.

The proposal passes when every sample wrote a valid view the challenger answered, and at least ``min_direction``
of the directions were right. It needs live mode: the mock agent does not read prompts or models, so without the
AI switch and two different models the eval does not run, and the proposal cannot be approved.
"""

from __future__ import annotations

import asyncio
import json
import math
import time
from typing import Any, Dict, List

from views import agents, schema
from views import store as vstore
from wealth import ai
from wealth.paths import DATA


def eval_set() -> Dict[str, Any]:
    return json.loads((DATA / "agent_eval.json").read_text(encoding="utf-8"))


def _packet(sample: Dict[str, Any]) -> Dict[str, Any]:
    news = [
        {
            "id": f"NW-{sample['id']}-{i + 1}",
            "title": n["title"],
            "summary": n.get("summary", ""),
            "outlet": n.get("outlet", ""),
            "section": None,
            "label": n.get("label"),
            "published": None,
            "factors": [],
            "event_type": sample.get("type"),
        }
        for i, n in enumerate(sample["news"])
    ]
    return {
        "event": {"id": f"EV-{sample['id']}", "title": sample["title"], "type": sample.get("type"), "factors": []},
        "news": news,
        "catalogue": schema.catalogue(),
    }


def _main_branch_hit(view: Dict[str, Any], expect: Dict[str, str]) -> bool:
    branches = (view.get("scenarios") or {}).get("branches") or []
    if not branches:
        return False
    main = max(branches, key=lambda b: float(b.get("probability") or 0))
    return any(
        s.get("factor") == expect["factor"] and s.get("direction") == expect["direction"]
        for s in main.get("core_shocks", [])
    )


async def _one(sample: Dict[str, Any], subject: str, words: Dict[str, List[str]]) -> Dict[str, Any]:
    packet = _packet(sample)
    m = agents.models()
    run_id = vstore.start_run("eval", subject, "live", m["cio"])
    row: Dict[str, Any] = {"id": sample["id"], "title": sample["title"], "run_id": run_id, "expect": sample["expect"]}
    try:
        notes = list(await asyncio.gather(*(agents.analyst(k, packet, "live", run_id, words) for k in agents.lenses())))
        merged = await agents.debate(notes, packet, "live", run_id)
        names = {f["id"]: f["name"] for f in packet["catalogue"]["factors"]}
        view, errors = await agents.synthesize(packet, notes, merged, "live", run_id, names)
        row.update(valid=view is not None, errors=errors[:3])
        if view is not None:
            got = await agents.challenge(view, {"news": packet["news"]}, "live", run_id)
            row.update(
                challenged=True,
                findings=len(got["findings"]),
                direction_hit=_main_branch_hit(view, sample["expect"]),
                summary=view.get("summary", "")[:300],
            )
        vstore.finish_run(run_id, "ok" if view is not None else "error", "; ".join(errors))
    except agents.AgentError as exc:
        row.update(valid=row.get("valid", False), error=str(exc))
        vstore.finish_run(run_id, "error", str(exc))
    row.setdefault("challenged", False)
    row.setdefault("direction_hit", False)
    return row


async def run(version: Dict[str, Any]) -> Dict[str, Any]:
    """The eval set on a ``prompts`` or ``models`` proposal; the result to keep on it."""
    from news.ops import config as news_config

    spec = eval_set()
    started = time.time()
    base = {"status": "done", "set": spec["version"], "started": started}
    kind, data = version["kind"], version["data"]
    with agents.use(data if kind == "prompts" else None, data if kind == "models" else None, version["id"]):
        m = agents.models()
        if not ai.enabled():
            return {**base, "passed": False, "finished": time.time(), "summary": "Không chạy được: AI đang tắt (MF_AI)"}
        if not (m["cio"] and m["challenger"]) or m["cio"] == m["challenger"]:
            return {
                **base,
                "passed": False,
                "finished": time.time(),
                "summary": "Không chạy được: cần hai mô hình khác nhau cho Agent CIO và Agent Phản biện",
            }
        words = news_config()["factor_words"]
        rows = [await _one(s, version["id"], words) for s in spec["samples"]]
    valid = sum(1 for r in rows if r["valid"] and r["challenged"])
    hits = sum(1 for r in rows if r["direction_hit"])
    need = math.ceil(spec["min_direction"] * len(rows))
    passed = valid == len(rows) and hits >= need
    return {
        **base,
        "passed": passed,
        "finished": time.time(),
        "models": m,
        "samples": rows,
        "valid": valid,
        "direction_hits": hits,
        "needed": need,
        "runs": [r["run_id"] for r in rows],
        "summary": (
            f"{valid}/{len(rows)} mẫu ra nhận định hợp lệ có phản biện; đúng hướng {hits}/{len(rows)} (cần {need})"
        ),
    }


async def run_pending() -> List[Dict[str, Any]]:
    """The ``agent_eval`` job: every prompt or model proposal still without a result, one after another."""
    from control import config

    done = []
    for v in config.pending_evals():
        config.set_eval(v["id"], {"status": "running", "started": time.time()})
        try:
            result = await run(v)
        except Exception as exc:  # noqa: BLE001 — a crash is a failed eval the proposer must see, not a stuck one
            result = {"status": "done", "passed": False, "finished": time.time(), "summary": f"Lỗi khi chạy: {exc}"}
        config.set_eval(v["id"], result)
        done.append({"id": v["id"], "passed": result["passed"], "summary": result["summary"]})
    return done
