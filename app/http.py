"""What every response of the product passes through (BRD-NFR-07, BRD_REMAINING_PLAN G3): security headers, and a
cross-site write refused. Registered as operonx middleware in app/main.py, so it wraps the whole listener — the
graph services (``POST /api/dashboard`` …), the web app and ``/healthz`` alike.

- **Headers:** a Content-Security-Policy that lets the page run only its own scripts (the one inline script, the
  theme, by its hash) and be framed by nobody; ``nosniff``; no referrer; no camera, microphone or location;
  same-origin opener and resources; HSTS when the request came over HTTPS (the host's TLS — ngrok on the demo).
- **Client data is not cached:** ``Cache-Control: no-store`` on every ``/api/`` answer that did not set its own.
- **No cross-site writes:** a POST, PUT, PATCH or DELETE whose ``Origin`` is another site is refused (403) before
  it reaches the app. The session cookie is ``SameSite=Lax`` already; this holds even for a browser that ignores it.
  A request with no ``Origin`` (a server: the AI zone's signed inbox, a script) passes to the app's own checks.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from urllib.parse import urlsplit

from wealth.paths import ROOT


def _inline_hashes() -> str:
    """The CSP hashes of web/index.html's inline scripts, read from the file so the policy cannot drift from it."""
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    out = []
    for body in re.findall(r"<script>(.*?)</script>", html, re.S):
        out.append("'sha256-" + base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode() + "'")
    return " ".join(out)


CSP = "; ".join(
    [
        "default-src 'self'",
        f"script-src 'self' {_inline_hashes()}",
        "style-src 'self' 'unsafe-inline'",  # the pages set element styles (positions, widths) inline
        "img-src 'self' data:",
        "font-src 'self' data:",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)

HEADERS = [
    (b"content-security-policy", CSP.encode()),
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=(), payment=()"),
    (b"cross-origin-opener-policy", b"same-origin"),
    (b"cross-origin-resource-policy", b"same-origin"),
]
HSTS = (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
WRITES = {"POST", "PUT", "PATCH", "DELETE"}


def _header(scope, name: bytes) -> str:
    for k, v in scope.get("headers") or []:
        if k == name:
            return v.decode("latin-1")
    return ""


def _https(scope) -> bool:
    return scope.get("scheme") == "https" or _header(scope, b"x-forwarded-proto").split(",")[0].strip() == "https"


def cross_site(scope) -> bool:
    """A write whose ``Origin`` names another host than the one it was sent to."""
    origin = _header(scope, b"origin")
    if not origin or scope.get("method") not in WRITES:
        return False
    if origin == "null":
        return True
    try:
        theirs = urlsplit(origin).netloc.lower()
    except ValueError:
        return True
    forwarded = _header(scope, b"x-forwarded-host").split(",")[0].strip()
    ours = {h.lower() for h in (_header(scope, b"host"), forwarded) if h}
    return theirs not in ours


class SecurityHeaders:
    """ASGI middleware (operonx ``Application(middleware=[...])``, called with ``app=``)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        api = scope.get("path", "").startswith("/api/")
        extra = list(HEADERS) + ([HSTS] if _https(scope) else [])

        async def headed(message):
            if message["type"] == "http.response.start":
                have = {k.lower() for k, _ in message.get("headers") or []}
                add = [(k, v) for k, v in extra if k not in have]
                if api and b"cache-control" not in have:
                    add.append((b"cache-control", b"no-store"))
                message = {**message, "headers": [*(message.get("headers") or []), *add]}
            await send(message)

        if cross_site(scope):
            body = json.dumps({"error": "Yêu cầu ghi từ trang khác bị từ chối (BRD-NFR-07)"}, ensure_ascii=False)
            await headed(
                {
                    "type": "http.response.start",
                    "status": 403,
                    "headers": [(b"content-type", b"application/json; charset=utf-8")],
                }
            )
            return await send({"type": "http.response.body", "body": body.encode("utf-8")})
        await self.app(scope, receive, headed)
