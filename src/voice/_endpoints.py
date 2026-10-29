"""The HTTP services a call depends on, declared instead of scraped from env.

STT and TTS are the two things in this project that reach across the
network on the hot path, and until now they were the two least visible:
thirteen `os.getenv` calls at module import, no mention in
`resources.yaml`, and nothing a tool could resolve. `operonx-lint` had
been saying so the whole time —

    C6  stt.py:39   credential 'STT_API_KEY' read directly
    C6  tts.py:66   credential 'TTS_API_KEY' read directly

— the project's only two findings. Meanwhile the ONNX models and the audio
worker, neither of which leaves the process, were both declared.

`http:` fixes that with the mechanism this project already uses twice
(`audio_worker:`, `denoise:`): a config type registered against a
category name, resolved through the hub::

    http:
      tts:
        url: ${TTS_API_URL:http://192.168.1.212:8086/tts}
        api_key: ${TTS_API_KEY}

The win is not tidiness. The env contract is *derived* from
`resources.yaml`, so a variable that never appears there is a variable
nobody knows is required until a call fails — which is exactly how an
endpoint being down looked from the outside earlier today.

Ops resolve their own endpoint the way `LLMOp` does — once, into the
instance, via `_ensure_initialized()` with a `warmup()` hook the engine
calls at startup. There is deliberately no module-level `endpoint()`
helper here: it would be a second cache in front of the hub's, and a
per-call chain of wrappers in front of one dictionary lookup.
"""

from __future__ import annotations

from typing import Any, ClassVar, Dict, Optional

import httpx

from operonx.core.registry import REGISTRY
from operonx.core.utils.yaml_model import YamlModel

__all__ = ["HttpEndpointConfig", "HttpEndpoint"]


class HttpEndpointConfig(YamlModel):
    """One HTTP service this project calls.

    Attributes:
        url: Full endpoint, or the base a caller appends paths to.
        api_key: Substituted from the environment by the hub, so the
            variable lands in the derived contract instead of being read
            behind its back.
        api_key_header: Header the key goes in. STT and TTS both use
            ``X-API-Key``; naming it here keeps a future service from
            needing a code change.
        timeout_s: Per-request timeout.
        verify_ssl: Off for services behind a self-signed cert.
        options: Service-specific knobs — model name, tensor names, and
            the like. Free-form because they are the service's vocabulary,
            not this project's.
    """

    _category: ClassVar[str] = "http"

    url: str = ""
    api_key: str = ""
    api_key_header: str = "X-API-Key"
    timeout_s: float = 30.0
    verify_ssl: bool = True
    options: Dict[str, Any] = {}


class HttpEndpoint:
    """A resolved :class:`HttpEndpointConfig`, owning its HTTP client.

    The backend, not a config holder. `ResourceHub.get()` caches one
    instance per key and hands the same object back, so building the
    client here is what ties it to the endpoint it belongs to — the same
    shape `OpenAILLM` uses (`self.client = AsyncOpenAI(...)` in its
    `__init__`).

    This replaced a module-global `_client` behind a `_get_client()` in
    each of src/call/stt/ops.py and src/call/tts/ops.py. Those reimplemented the hub's
    caching one level down, and got it wrong in a way that only shows with
    two keys: whichever resource resolved first built the client, so a
    second endpoint with a different timeout or a self-signed cert would
    silently borrow the first one's.
    """

    __slots__ = ("url", "api_key", "headers", "timeout_s", "verify_ssl", "options", "_client")

    def __init__(self, cfg: HttpEndpointConfig) -> None:
        self.url = cfg.url.rstrip("/") if cfg.url else ""
        self.api_key = cfg.api_key
        self.headers = {cfg.api_key_header: cfg.api_key} if cfg.api_key else {}
        self.timeout_s = cfg.timeout_s
        self.verify_ssl = _as_bool(cfg.verify_ssl, True)
        self.options = dict(cfg.options or {})
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """This endpoint's client, built on first use.

        Lazy because a graph is built long before anything is sent, and an
        `AsyncClient` binds to the loop that first uses it.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout_s,
                verify=self.verify_ssl,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=50),
            )
        return self._client

    async def post(self, payload: dict, path: str = "") -> httpx.Response:
        """POST JSON to this endpoint, with its key attached.

        Raises for status, so a caller that wants the bytes can just take
        `.content` and a caller that wants to log the failure catches once.
        """
        target = f"{self.url}{path}" if path else self.url
        resp = await self.client.post(target, json=payload, headers=self.headers)
        resp.raise_for_status()
        return resp

    def opt(self, key: str, default: Any = None) -> Any:
        v = self.options.get(key, default)
        return default if v in (None, "") else v

    def flag(self, key: str, default: bool = True) -> bool:
        """An option as a bool. YAML gives one; `${VAR}` gives a string."""
        return _as_bool(self.options.get(key), default)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<HttpEndpoint {self.url} key={'set' if self.api_key else 'none'}>"


def _as_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return default
    return str(value).strip().lower() not in ("0", "false", "no", "off")


REGISTRY.register(HttpEndpointConfig, HttpEndpoint)
