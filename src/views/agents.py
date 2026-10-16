"""The CIO agent's and the challenger's steps, live (a model) or mock (rules), each recorded as a
node of its agent run: input, prompt, prompt version, model, output, time (BRD §8, FR-704).

Live mode needs two different models (the ``models`` configuration, Admin, two people; version 1 is
``LLM_MODEL_CIO`` and ``LLM_MODEL_CHALLENGER`` from .env: §8.3, two models so their mistakes do not line
up) and the AI switch on (wealth.ai). Without them the run is mock and says so; asking for live without
them is refused — there is no silent fallback (F24). A live reply cut off by the token cap, or answered by
another model than the configured one, is refused too (§8.3).

The prompts are the ``prompts`` configuration (``views.prompts``; AI-02), and every node records the id of
the prompts version it used (FR-704). The eval set runs the same steps on a proposal: ``use(...)`` puts the
proposed prompts or models in force for that run only.

What the agents read is the ``packet`` gather builds: the event, its news and the market
catalogue. No client data reaches this module (BR-11; tests/test_views.py checks the prompts).
"""

from __future__ import annotations

import contextvars
import json
import os
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Tuple

from control import db
from views import mock, prompts, schema
from views import store as vstore
from wealth import ai

MAX_TOKENS = {"analyst": 3000, "debate": 3000, "synthesize": 6000, "challenge": 4000}  # measured: analysts ~1.1–1.5k
DAILY_TOKENS = 300_000  # NFR-10: the day's budget for all agent calls; AGENT_DAILY_TOKENS overrides
FORMAT_RETRIES = 2
DEADLINES = {"cio": 15 * 60, "challenger": 5 * 60, "policy": 15 * 60}  # BRD §5 steps 3–4 (WF-03, WF-04), seconds


class AgentError(RuntimeError):
    """A run the CIO must see as failed (AGENT_ERROR), with why."""


_USE: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar("agent_config", default=None)


@contextmanager
def use(
    prompts_data: Optional[Dict[str, Any]] = None,
    models_data: Optional[Dict[str, str]] = None,
    version: Optional[str] = None,
) -> Iterator[None]:
    """For the eval set: run with a proposal's prompts or models instead of the versions in force."""
    token = _USE.set({"prompts": prompts_data, "models": models_data, "version": version})
    try:
        yield
    finally:
        _USE.reset(token)


def models() -> Dict[str, str]:
    """The two models in force (configuration ``models``), or the proposal under evaluation."""
    from control import config

    over = _USE.get()
    m = (over or {}).get("models") or config.data("models")
    return {"cio": str(m.get("cio") or "").strip(), "challenger": str(m.get("challenger") or "").strip()}


def prompt_set() -> Dict[str, Any]:
    from control import config

    over = _USE.get()
    return (over or {}).get("prompts") or config.data("prompts")


def prompt_version() -> str:
    """The id of the prompts version a node used (FR-704): the proposal's under evaluation."""
    from control import config

    over = _USE.get()
    if over and over.get("prompts") is not None:
        return over.get("version") or "đề xuất"
    return config.active("prompts")["id"]


def lenses() -> Dict[str, Dict[str, Any]]:
    """The analyst groups: the BRD's four and any declared in the prompts configuration (NFR-06)."""
    return prompt_set()["lenses"]


def configured_mode() -> str:
    """The ``ai_mode`` configuration in force (FR-307): live (falls back to mock until two different models are
    set), inbox (views come from the AI zone through the signed inbox; nothing is run here) or mock."""
    from control import config

    return config.data("ai_mode")["mode"]


def resolve_mode(requested: Optional[str]) -> str:
    """The mode one run uses: the configured one, or mock when asked for (a CIO may always try the keyword agent,
    and the tests do). In inbox mode nothing runs here."""
    configured = configured_mode()
    if configured == "inbox" and requested != "mock":
        raise AgentError("Chế độ hộp chờ: nhận định đến từ vùng AI qua hộp chờ, không chạy agent tại đây")
    if configured == "mock" and requested in (None, "", "mock"):
        return "mock"
    if configured == "mock":
        raise AgentError("Chế độ chạy AI đang là mô phỏng (Cấu hình › Chế độ chạy AI)")
    m = models()
    ready = ai.enabled() and m["cio"] and m["challenger"] and m["cio"] != m["challenger"]
    if requested == "mock":
        return "mock"
    if requested == "live":
        if not ai.enabled():
            raise AgentError("Chế độ trực tiếp cần bật AI (MF_AI) và khóa LLM_API_KEY")
        if not (m["cio"] and m["challenger"]):
            raise AgentError("Chế độ trực tiếp cần hai mô hình trong cấu hình (LLM_MODEL_CIO, LLM_MODEL_CHALLENGER)")
        if m["cio"] == m["challenger"]:
            raise AgentError("Agent CIO và Agent Phản biện phải dùng hai mô hình khác nhau")
        return "live"
    if requested not in (None, ""):
        raise AgentError(f"chế độ {requested!r} không có (live, mock)")
    return "live" if ready else "mock"


# -- the model call ----------------------------------------------------------------------------


def budget() -> Dict[str, int]:
    """Today's token budget (local midnight) and what the agents have used of it."""
    day = time.localtime()
    midnight = time.mktime((day.tm_year, day.tm_mon, day.tm_mday, 0, 0, 0, 0, 0, -1))
    try:
        daily = int(os.environ.get("AGENT_DAILY_TOKENS") or DAILY_TOKENS)
    except ValueError:
        daily = DAILY_TOKENS
    return {"daily": daily, "used_today": vstore.tokens(midnight)["total"]}


def deadline(run_id: str) -> Tuple[float, int]:
    """(the time a run must be done by, its limit in seconds): from its start and its agent's limit (WF-03/04)."""
    with db.tx() as con:
        row = con.execute("select agent, created from agent_runs where id = ?", (run_id,)).fetchone()
    limit = DEADLINES.get(row["agent"], 15 * 60)
    return row["created"] + limit, limit


async def call_model(
    resource: str, system: str, user: str, max_tokens: int, run_id: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """One chat call through the operonx resource ``llm:<resource>`` → (text, meta). Raises
    AgentError when the reply was cut off or came from another model than configured, and — given the agent run
    it belongs to — when the run's time is up (WF-03: the CIO agent within 15 minutes; WF-04: the challenger
    within 5): the call is cut at what is left."""
    import asyncio

    from operonx.providers.ops._utils import resolve_hub

    left = None
    if run_id:
        until, limit = deadline(run_id)
        left = until - time.time()
        if left <= 0:
            raise AgentError(f"Quá thời hạn {limit // 60} phút của lần chạy (BRD §5)")

    b = budget()
    if b["used_today"] + max_tokens > b["daily"]:
        raise AgentError(f"Vượt ngân sách token trong ngày ({b['used_today']:,}/{b['daily']:,})".replace(",", "."))
    llm = _llm(resolve_hub().get(f"llm:{resource}"), models()[resource])
    expected = models()[resource]
    try:
        resp = await asyncio.wait_for(
            llm.generate(
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.2,
                max_tokens=max_tokens,
            ),
            timeout=left,
        )
    except asyncio.TimeoutError:
        raise AgentError(f"Quá thời hạn {limit // 60} phút của lần chạy (BRD §5): mô hình chưa trả lời") from None
    except Exception as exc:  # noqa: BLE001 — the provider down or refusing: the run fails with why (NFR-03)
        raise AgentError(f"Không gọi được mô hình {expected}: {type(exc).__name__}: {exc}"[:300]) from None
    choice = resp.choices[0]
    answered = str(getattr(resp, "model", "") or "")
    if answered and not (answered == expected or answered.startswith(expected)):
        raise AgentError(f"Mô hình trả lời ({answered}) khác mô hình đã duyệt ({expected})")
    if choice.finish_reason == "length":
        raise AgentError(f"Đầu ra bị cắt ở giới hạn {max_tokens} token")
    usage = getattr(resp, "usage", None)
    meta = {
        "model": answered or expected,
        "tokens_in": getattr(usage, "prompt_tokens", None),
        "tokens_out": getattr(usage, "completion_tokens", None),
    }
    return choice.message.content or "", meta


_LLMS: Dict[Tuple[int, str], Any] = {}


def _llm(base: Any, model: str) -> Any:
    """The resource's client for the configured model: the same provider, key and address, another model name
    when the configuration says so (NFR-06: a model change is configuration, not code)."""
    cfg = getattr(base, "config", None)
    if cfg is None or not model or getattr(cfg, "model", model) == model:
        return base
    key = (id(base), model)
    if key not in _LLMS:
        from operonx.providers.llms.factory import create_llm

        _LLMS[key] = create_llm(cfg.model_copy(update={"model": model}))
    return _LLMS[key]


def _json(text: str) -> Dict[str, Any]:
    from operonx.providers.parsing import parse_json

    try:
        out = parse_json(text)
    except Exception as exc:  # noqa: BLE001 — any parse failure is a format error the retry loop handles
        raise ValueError(f"không đọc được JSON: {exc}") from None
    if not isinstance(out, dict):
        raise ValueError("JSON phải là một đối tượng")
    return out


def wrap(data: Any) -> str:
    """§8.3: what goes into a prompt is data between markers, never instructions."""
    return "DỮ_LIỆU\n" + json.dumps(data, ensure_ascii=False, indent=1) + "\nHẾT_DỮ_LIỆU"


def _prompt(name: str, **values: Any) -> str:
    p = prompt_set()
    return prompts.fill(p[name], guard=p["guard"], **values)


def _record(
    run_id: str,
    node: str,
    mode: str,
    model: str,
    given: Any,
    prompt: Optional[Dict[str, str]],
    output: Any,
    error: str,
    started: float,
    attempt: int = 1,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    vstore.add_node(
        run_id,
        {
            "node": node,
            "mode": mode,
            "model": model,
            "prompt_version": prompt_version() if mode == "live" else None,
            "input": given,
            "prompt": prompt,
            "output": output,
            "error": error,
            "attempt": attempt,
            "ms": round((time.time() - started) * 1000),
            **(meta or {}),
        },
    )


# -- the steps ---------------------------------------------------------------------------------


async def analyst(lens: str, packet: Dict[str, Any], mode: str, run_id: str, factor_words: Dict[str, List[str]]):
    started = time.time()
    spec = lenses()[lens]
    if mode == "mock":
        out = mock.analyst(lens, packet["news"], factor_words, spec)
        _record(run_id, f"analyst:{lens}", mode, "mock", {"lens": lens}, None, out, "", started)
        return out
    system = _prompt("analyst", task=spec["task"])
    user = f"Sự kiện, tin nguồn và danh mục:\n{wrap(packet)}"
    prompt = {"system": system, "user": user}
    try:
        text, meta = await call_model("cio", system, user, MAX_TOKENS["analyst"], run_id=run_id)
        out = _json(text)
        out.setdefault("factors", {})
        out.setdefault("impacts", [])
        out.update(lens=lens, label=spec["label"])
    except (AgentError, ValueError) as exc:
        _record(run_id, f"analyst:{lens}", mode, models()["cio"], {"lens": lens}, prompt, None, str(exc), started)
        raise AgentError(f"Nhóm {spec['label']}: {exc}") from None
    _record(run_id, f"analyst:{lens}", mode, meta["model"], {"lens": lens}, prompt, out, "", started, meta=meta)
    return out


async def debate(notes: List[Dict[str, Any]], packet: Dict[str, Any], mode: str, run_id: str) -> Dict[str, Any]:
    started = time.time()
    if not mock.needs_debate(notes):
        out = {"rounds": 0, "impacts": [r for n in notes for r in n.get("impacts", [])], "skipped": True}
        _record(run_id, "debate", mode, "rule", {"needed": False}, None, out, "", started)
        return out
    if mode == "mock":
        out = mock.debate(notes)
        _record(run_id, "debate", mode, "mock", {"needed": True}, None, out, "", started)
        return out
    out: Dict[str, Any] = {"impacts": [r for n in notes for r in n.get("impacts", [])]}
    for rnd in (1, 2):  # BRD 8.1: at most two rounds
        system = _prompt("debate", round=rnd)
        user = f"Ghi chú các nhóm và tin nguồn:\n{wrap({'notes': notes, 'previous': out, 'event': packet['event']})}"
        try:
            text, meta = await call_model("cio", system, user, MAX_TOKENS["debate"], run_id=run_id)
            out = _json(text)
        except (AgentError, ValueError) as exc:
            _record(
                run_id,
                "debate",
                mode,
                models()["cio"],
                {"round": rnd},
                {"system": system, "user": user},
                None,
                str(exc),
                started,
                rnd,
            )
            raise AgentError(f"Tranh luận: {exc}") from None
        _record(
            run_id,
            "debate",
            mode,
            meta["model"],
            {"round": rnd},
            {"system": system, "user": user},
            out,
            "",
            started,
            rnd,
            meta,
        )
        if out.get("settled", True):
            break
    out["rounds"] = rnd
    return out


async def synthesize(
    packet: Dict[str, Any],
    notes: List[Dict[str, Any]],
    merged: Dict[str, Any],
    mode: str,
    run_id: str,
    factor_names: Dict[str, str],
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """The view, format-checked; a failed check goes back to synthesis at most twice (FR-301).
    Returns (view, []) or (None, the last errors)."""
    news_ids = [n["id"] for n in packet["news"]]
    errors: List[str] = []
    for attempt in range(1, FORMAT_RETRIES + 2):
        started = time.time()
        prompt = None
        model = "mock"
        meta: Dict[str, Any] = {}
        try:
            if mode == "mock":
                view = mock.synthesize(packet["event"], packet["news"], notes, merged, factor_names)
            else:
                system = _prompt("synthesize")
                given = {"packet": packet, "notes": notes, "debate": merged}
                if errors:
                    given["previous_errors"] = errors
                user = f"Đầu vào:\n{wrap(given)}"
                prompt = {"system": system, "user": user}
                text, meta = await call_model("cio", system, user, MAX_TOKENS["synthesize"], run_id=run_id)
                model = meta["model"]
                view = _json(text)
            errors = schema.check(view, news_ids)
        except ValueError as exc:
            view, errors = None, [str(exc)]
        except AgentError as exc:
            _record(
                run_id,
                "synthesize",
                mode,
                models()["cio"],
                {"attempt": attempt},
                prompt,
                None,
                str(exc),
                started,
                attempt,
            )
            raise
        _record(
            run_id,
            "synthesize",
            mode,
            model,
            {"attempt": attempt},
            prompt,
            view,
            "; ".join(errors),
            started,
            attempt,
            meta,
        )
        _record(
            run_id,
            "format_check",
            "rule",
            "schema",
            {"attempt": attempt},
            None,
            {"errors": errors},
            "",
            time.time(),
            attempt,
        )
        if not errors:
            return view, []
    return None, errors


async def challenge(view: Dict[str, Any], event: Dict[str, Any], mode: str, run_id: str) -> Dict[str, Any]:
    """Findings on the view as it stands: the rules always; the challenger model too in live mode."""
    from views import challenger

    started = time.time()
    found = challenger.findings(view, event)
    _record(run_id, "challenge:rules", "rule", "rules", {"content": "current"}, None, found, "", started)
    model = "rules" if mode == "mock" else models()["challenger"]
    if mode == "live":
        started = time.time()
        system = _prompt("challenge")
        packet = {
            "view": {k: view.get(k) for k in ("summary", "impacts", "scenarios")},
            "news": [{k: n.get(k) for k in ("id", "title", "summary", "outlet")} for n in event.get("news", [])],
        }
        user = f"Nhận định và tin nguồn:\n{wrap(packet)}"
        try:
            text, meta = await call_model("challenger", system, user, MAX_TOKENS["challenge"], run_id=run_id)
            got = _json(text).get("findings", [])
        except (AgentError, ValueError) as exc:
            _record(
                run_id, "challenge:model", mode, model, {}, {"system": system, "user": user}, None, str(exc), started
            )
            raise AgentError(f"Agent Phản biện: {exc}") from None
        for i, f in enumerate(got if isinstance(got, list) else []):
            if isinstance(f, dict) and f.get("severity") in schema.SEVERITIES and f.get("title"):
                found.append(
                    {
                        "id": f"M{i + 1}",
                        "severity": f["severity"],
                        "title": str(f["title"])[:200],
                        "detail": str(f.get("detail", ""))[:1000],
                        "target": str(f.get("target", ""))[:100],
                        "source": "model",
                    }
                )
        _record(
            run_id,
            "challenge:model",
            mode,
            meta["model"],
            {},
            {"system": system, "user": user},
            got,
            "",
            started,
            meta=meta,
        )
    return {"findings": found, "model": model, "mode": mode}
