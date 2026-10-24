"""The news agents' models through the owner's Claude Code subscription (BUSINESS_FEEDBACK_1021_PLAN B1.0).

A local OpenAI-compatible endpoint, ``POST /v1/chat/completions``, that answers each call with headless Claude Code
(``claude -p``): the system message as the session's whole system prompt, the rest as the prompt, no tools, no MCP
servers, no settings, no session kept, an empty working directory and a clean environment (so the subscription's
sign-in is used, never an API key). The reply carries the model asked for and the token counts, as ``call_model``
in ``views/agents.py`` checks them, plus ``usage.cost`` (Claude Code's ``total_cost_usd``) with ``usage.cost_kind``
"notional": the subscription bills nothing per call, so it is what the call would cost on the API, never a
bill. Only ``llm:cio`` and ``llm:challenger`` point here (``LLM_AGENT_BASE_URL``).

    uv run python scripts/claude_bridge.py [--port 8091] [--parallel 2]

It listens on 127.0.0.1, which the client-data barrier counts as inside the bank (``onprem_hosts``), but it sends
everything to Anthropic: point only the news agents at it (they never see client data, BR-11), never a client step.
For the demo and the trial; production uses the bank's own models.
"""

from __future__ import annotations

import argparse
import asyncio
import glob
import json
import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

MODELS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}
TIMEOUT_S = 14 * 60  # under the CIO agent's 15 minutes (WF-03): the app cuts a call at what its run has left
LOG = Path(__file__).resolve().parent.parent / "logs" / "claude_bridge.jsonl"


def find_claude() -> str:
    """The Claude Code binary: on the PATH, else the newest one the editor extension ships. Looked up on each call:
    an extension update removes the folder the last one was in (the trial of 2026-10-24 failed on that)."""
    found = shutil.which("claude")
    if found:
        return found
    shipped = "~/.vscode-server/extensions/anthropic.claude-code-*/resources/native-binary/claude"
    hits = sorted(glob.glob(os.path.expanduser(shipped)))
    if not hits:
        raise RuntimeError("claude not found (PATH or the VS Code extension)")
    return hits[-1]


def model_of(asked: str) -> Optional[str]:
    """The Claude model for the name the app asks for (``anthropic/claude-sonnet-5.5``, ``claude-opus-5-5``…)."""
    low = asked.lower()
    return next((m for k, m in MODELS.items() if k in low), None)


def text_of(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):  # the content-parts form
        return "\n".join(p.get("text", "") for p in content if isinstance(p, dict))
    return str(content or "")


def split(messages: List[Dict[str, Any]]) -> tuple[str, str]:
    """(the system prompt, the prompt): every system message, then the conversation as labelled turns."""
    system = "\n\n".join(text_of(m.get("content")) for m in messages if m.get("role") == "system")
    turns = [m for m in messages if m.get("role") != "system"]
    if len(turns) == 1:
        return system, text_of(turns[0].get("content"))
    return system, "\n\n".join(f"[{m.get('role')}]\n{text_of(m.get('content'))}" for m in turns)


class Bridge:
    def __init__(self, parallel: int) -> None:
        self.gate = asyncio.Semaphore(parallel)
        self.home = os.path.expanduser("~")

    async def ask(self, model: str, system: str, prompt: str) -> Dict[str, Any]:
        env = {"HOME": self.home, "PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8"}
        cmd = [find_claude(), "-p", "--output-format", "json", "--model", model, "--tools", "", "--setting-sources=",
               "--strict-mcp-config", "--no-session-persistence"]
        if system:
            cmd += ["--system-prompt", system]
        async with self.gate:
            with tempfile.TemporaryDirectory(prefix="claude-bridge-") as cwd:
                try:
                    proc = await asyncio.create_subprocess_exec(
                        *cmd, cwd=cwd, env=env, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE, start_new_session=True)
                except OSError as exc:  # the binary gone or not runnable: a logged 502, never a bare 500
                    raise RuntimeError(f"claude -p did not start: {exc}") from None
                try:
                    out, err = await asyncio.wait_for(proc.communicate(prompt.encode()), TIMEOUT_S)
                except asyncio.TimeoutError:
                    proc.kill()
                    raise RuntimeError(f"claude -p did not answer in {TIMEOUT_S // 60} min") from None
        try:
            got = json.loads(out.decode() or "{}")
        except json.JSONDecodeError:
            raise RuntimeError(f"claude -p: {(out or err).decode()[:300]}") from None
        if got.get("is_error") or proc.returncode:
            raise RuntimeError(f"claude -p: {str(got.get('result') or err.decode())[:300]}")
        return got


def build(parallel: int) -> Starlette:
    bridge = Bridge(parallel)

    async def chat(request: Request) -> JSONResponse:
        body = await request.json()
        asked = str(body.get("model") or "")
        model = model_of(asked)
        if not model:
            return JSONResponse({"error": {"message": f"model {asked!r}: only Claude Haiku, Sonnet or Opus"}}, 400)
        system, prompt = split(body.get("messages") or [])
        t0 = time.time()
        try:
            got = await bridge.ask(model, system, prompt)
        except RuntimeError as exc:
            note(asked, model, t0, None, str(exc))
            return JSONResponse({"error": {"message": str(exc)}}, 502)
        u = got.get("usage") or {}
        kinds = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
        tokens_in = sum(int(u.get(k) or 0) for k in kinds)
        tokens_out = int(u.get("output_tokens") or 0)
        cached = int(u.get("cache_read_input_tokens") or 0)
        usd = got.get("total_cost_usd")
        note(asked, model, t0, {"in": tokens_in, "out": tokens_out, "cached": cached, "usd": usd}, None)
        return JSONResponse({
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}", "object": "chat.completion", "created": int(t0),
            "model": asked,  # the name the app asked for: call_model checks the reply came from it
            "choices": [{"index": 0, "message": {"role": "assistant", "content": got.get("result") or ""},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": tokens_in, "completion_tokens": tokens_out,
                      "total_tokens": tokens_in + tokens_out, "prompt_tokens_details": {"cached_tokens": cached},
                      "cost": usd, "cost_kind": "notional" if usd is not None else None},
        })

    async def models(_: Request) -> JSONResponse:
        return JSONResponse({"object": "list", "data": [{"id": m, "object": "model"} for m in MODELS.values()]})

    return Starlette(routes=[Route("/v1/chat/completions", chat, methods=["POST"]), Route("/v1/models", models)])


def note(asked: str, model: str, t0: float, usage: Optional[Dict[str, Any]], error: Optional[str]) -> None:
    """One line per call: when, which model, how long, the tokens and the subscription's notional cost, or why not."""
    LOG.parent.mkdir(exist_ok=True)
    row = {"at": round(t0, 3), "asked": asked, "model": model, "s": round(time.time() - t0, 2), "usage": usage,
           "error": error}
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--port", type=int, default=8091)
    ap.add_argument("--parallel", type=int, default=2, help="claude -p processes at once")
    a = ap.parse_args()
    uvicorn.run(build(a.parallel), host="127.0.0.1", port=a.port, log_level="warning")
