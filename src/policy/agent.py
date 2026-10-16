"""The policy agent (BRD-FR-306, RULE-AI-01: owner Compliance, risk medium): a summary of one verified policy
document, each point with a quote from it and the article the quote is in.

It reads the document and nothing else — this module imports no client, family or portfolio data — and every
answer passes ``policy.text.check`` (quotes word for word inside the named article; no conclusion for a client;
no recommendation wording). A failing answer goes back to the model with what failed, at most twice; then the run
is an error. Live it calls ``llm:cio`` (the BRD names the same model family as the CIO agent's, at a lower effort)
with the ``policy`` prompt of the prompts configuration; mock quotes the first sentence of each article, labelled.
Each attempt is a node of an agent run (``agent_runs``, agent ``policy``): input, prompt, model, output, findings.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from control import roles
from control.errors import Conflict
from policy import store, text
from views import agents, prompts
from views import store as vstore

MAX_TOKENS = 6000  # measured: 2,500 cut a live answer (six Vietnamese quotes); the CIO's synthesis uses ~4.5k
MAX_RETRIES = 2
MAX_INPUT = 60_000


def _prompt() -> str:
    return agents.prompt_set().get("policy") or prompts.default()["policy"]


async def summarise(doc_id: str, by: str, mode: str = "") -> Dict[str, Any]:
    roles.require(by, "compliance")
    d = store.get(doc_id)
    if not d["verified"]:
        raise Conflict("Văn bản chưa được xác nhận nguồn: Agent Chính sách chỉ đọc văn bản đã xác nhận")
    if text.sha(d["text"]) != d["verified"]["text_sha256"]:
        raise Conflict("Văn bản đã khác bản được xác nhận")
    try:
        run_mode = agents.resolve_mode(mode or None)
    except agents.AgentError as exc:
        raise Conflict(str(exc)) from None
    model = agents.models()["cio"] if run_mode == "live" else "mock"
    run_id = vstore.start_run("policy", d["id"], run_mode, model)
    given = {
        "title": d["title"],
        "number": d["number"],
        "issuer": d["issuer"],
        "text": text.norm(d["text"])[:MAX_INPUT],
    }
    try:
        out, attempts = await _attempts(d, given, run_mode, model, run_id)
    except agents.AgentError as exc:
        vstore.finish_run(run_id, "error", str(exc))
        raise Conflict(f"Agent Chính sách lỗi ({run_id}): {exc}") from None
    vstore.finish_run(run_id, "ok")
    summary = {
        **out,
        "run_id": run_id,
        "mode": run_mode,
        "model": model,
        "attempts": attempts,
        "at": time.time(),
        "by": by,
        "text_sha256": d["verified"]["text_sha256"],
        "prompt_version": agents.prompt_version() if run_mode == "live" else None,
    }
    return store.keep_summary(d["id"], summary)


async def _attempts(d, given, mode, model, run_id):
    findings: list = []
    system = _prompt()
    for attempt in range(1, MAX_RETRIES + 2):
        started = time.time()
        if mode == "mock":
            raw, meta, prompt = text.mock(d), {}, None
        else:
            user = agents.wrap(given)
            if findings:
                user += "\nLần trước chưa đạt, sửa đúng các lỗi sau:\n- " + "\n- ".join(findings)
            prompt = {"system": system, "user": user}
            try:
                reply, meta = await agents.call_model("cio", system, user, MAX_TOKENS)
                raw = agents._json(reply)
            except agents.AgentError as exc:  # cut off, another model, the provider: the run fails, recorded
                agents._record(
                    run_id, "summarise", mode, model, {"document": d["id"]}, prompt, None, str(exc), started, attempt
                )
                raise
            except ValueError as exc:  # unreadable JSON: a format error, retried
                raw, meta = None, {}
                findings = [str(exc)]
                agents._record(
                    run_id, "summarise", mode, model, {"document": d["id"]}, prompt, None, str(exc), started, attempt
                )
                continue
        out, findings = text.check(d["text"], raw)
        agents._record(
            run_id,
            "summarise",
            mode,
            model,
            {"document": d["id"]},
            prompt,
            raw,
            "; ".join(findings),
            started,
            attempt,
            meta,
        )
        if not findings:
            return out, attempt
    raise agents.AgentError(f"sau {MAX_RETRIES + 1} lần vẫn chưa đạt: {'; '.join(findings)}"[:600])
