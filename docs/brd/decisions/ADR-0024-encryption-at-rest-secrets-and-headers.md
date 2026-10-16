# ADR-0024 — Client data sealed per column, keys from a secret store, every response hardened

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** BRD §15 (BRD-NFR-07: “Mã hóa khi truyền và khi lưu; khóa trong kho bí mật; kiểm thử xâm nhập và tấn
  công prompt trước vận hành”); docs/BRD_REMAINING_PLAN.md G-D3, G3

## Context

The product keeps client data in one SQLite file in plain text, its keys in `.env`, and answers with no security
headers. SQLite has no built-in encryption, and a bank keeps keys in a secret store, not a file beside the app.

## Decision

- **Per-column AES-256-GCM** (`src/control/crypto.py`): a fresh nonce per value, the value's place (table, row id,
  column) as associated data, so a ciphertext moved to another row or column does not open, and a changed one is
  refused. A sealed value reads `enc:1:<key id>:<base64>`. **What is sealed was found by scanning a populated
  database** for client names and account numbers: people's name, e-mail and record (clients and dependents), the
  source systems, holdings, profile, results, RM proposals (title, data, note), every family's run result, a
  snapshot's families, a run's ranking and exposure, and the declaring chat's history. Inside runs and snapshots only
  those fields are sealed, so the SQL that reads the rest (a snapshot's head without its families, NFR-01) is as fast
  as before.
- **Versioned keys, rotation in place:** `MF_DATA_KEYS = k2=…,k1=…` — the first seals, every one opens.
  `scripts/rotate_keys.py` re-seals every value under the first key in one transaction (and seals plain ones);
  `--check` counts values per key, so the old key is dropped only when nothing is under it.
- **Keys from a secret store** (`src/control/secrets.py`): a Vault-compatible KV v2 store, then a secrets folder,
  then the environment. A store that is configured and does not answer is an error, never a fall back to a stale
  copy in `.env`. The audit HMAC key, the session secret and the inbox and zone keys are read the same way.
- **Every response hardened** (`app/http.py`, operonx 1.29.0 `Application(middleware=…)`, so the graph services are
  covered too, not only the web app): a CSP allowing only the app's own scripts (the inline theme script by its
  hash) and no framing; `nosniff`; no referrer; HSTS when the request came over TLS; `no-store` on `/api/`; a write
  from another site refused (403) before it reaches the app. The session cookie stays HttpOnly, SameSite=Lax, Secure
  over HTTPS.
- **An attack suite in the tests** (`tests/test_security.py`, `tests/ui/test_attacks.py`): at rest, rotation,
  secrets, headers, cross-site writes, forged sessions, another family's data, SQL in inputs, paths out of the web
  folder, an oversized upload, stored markup in the page; prompt injection stays in `tests/test_views.py`.

## Consequences

- Found on the way: a request naming an unknown client (or SQL) answered 500; the request checks now raise
  `BadRequest` (400).
- Not sealed: ids (C01…, pseudonymous keys every table joins on), sign-in logins (looked up by value), the audit log
  (actions and ids, no names — checked by the scan), market and news data (not client data). Losing every key loses
  the sealed data; the demo can be reset from its seeds, a bank keeps its keys in the store's own backups.
- TLS stays the host's (ngrok on the demo; the bank's load balancer). A third-party penetration test is the bank's.
