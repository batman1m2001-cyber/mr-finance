"""The steps of reading a statement: the file, the model's reading or the rules', the holdings."""

from __future__ import annotations

import base64
import binascii
import re

from operonx import op

from statements import _parse
from wealth import ai, fixtures, store, valuation

MAX_BYTES = 5 * 1024 * 1024


@op
def read_request(item: dict = None) -> dict:
    """``{"client_id", "filename", "content": base64}``."""
    item = item or {}
    client_id = str(item.get("client_id") or "")
    if client_id not in fixtures.client_ids(members=True):
        raise ValueError(f"no client {client_id!r}")
    filename = str(item.get("filename") or "statement.txt")
    if not re.search(r"\.(csv|xlsx|xlsm|pdf|txt)$", filename.lower()):
        raise ValueError(f"{filename!r}: a statement is a PDF, an Excel or a CSV file")
    return {"client_id": client_id, "filename": filename, "content": str(item.get("content") or "")}


@op(bound="cpu")  # parsing a PDF or a workbook blocks: off the event loop
def read_file(filename: str, content: str) -> dict:
    """The file's text, and its rows when it is a table."""
    try:
        raw = base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError("the file is not base64") from e
    if len(raw) > MAX_BYTES:
        raise ValueError("a statement is at most 5 MB")
    kind, text, rows = _parse.read_file(filename, raw)
    return {
        "kind": kind,
        "text": text[:20_000],
        "rows": [[None if c is None else str(c) for c in r] for r in rows],
        "institution": _parse.institution(text),
    }


@op
def ai_mode() -> dict:
    """Whether the model reads it (wealth/ai.py)."""
    return {"ai": ai.enabled()}


@op
def rule_read(kind: str, text: str, rows: list) -> dict:
    """The layouts we know: a holdings table, balance lines."""
    return {"items": _parse.rule_items(kind, text, rows), "method": "rules"}


@op
def model_read(holdings: list = None, error: str = None, kind: str = "txt", text: str = "", rows: list = None) -> dict:
    """The model's items, checked; when it gave nothing usable, the rules read it instead."""
    items = _parse.clean_items(holdings)
    if items and not error:
        return {"items": items, "method": "ai"}
    return {"items": _parse.rule_items(kind, text, rows or []), "method": "rules"}


@op
def model_failed(error: str = "", kind: str = "txt", text: str = "", rows: list = None) -> dict:
    """The model call failed (no network, a bad key): the rules read the file instead."""
    return {
        "items": _parse.rule_items(kind, text, rows or []),
        "method": "rules",
        "ai_error": error,
    }


@op
def save_holdings(
    client_id: str,
    filename: str,
    institution: str,
    model_items: list = None,
    rule_items: list = None,
    fallback_items: list = None,
    model_method: str = None,
    rule_method: str = None,
    fallback_method: str = None,
) -> dict:
    """The items as holdings — a stock valued at today's price, a balance as it is — kept as
    this client's ``statement`` holdings (reading the same file again replaces them)."""
    # one arm ran: the model's (checked), the rules', or the rules after a failed model call
    items = next((x for x in (model_items, rule_items, fallback_items) if x is not None), [])
    method = model_method or rule_method or fallback_method or "rules"
    mk = fixtures.market()
    tag = re.sub(r"[^a-z0-9]+", "-", institution.lower()).strip("-") or "other"
    out = []
    for it in items:
        if it["type"] == "stock":
            row = {"ticker": it["ticker"], "qty": it["qty"], "avg_price": it.get("avg_price")}
            if it["ticker"] in mk["stocks"]:
                h = valuation.stock(
                    client_id,
                    "statement",
                    row,
                    mk,
                    "statement",
                    ident=f"{tag}:stock:{it['ticker']}",
                )
            else:  # a ticker the market file does not have: the statement's own price
                price = it.get("price") or it.get("avg_price") or 0
                h = valuation.holding(
                    client_id,
                    "statement",
                    f"{tag}:stock:{it['ticker']}",
                    trust="statement",
                    cls="stock",
                    name=f"Cổ phiếu {it['ticker']}",
                    value=it["qty"] * price,
                    cost=it["qty"] * it["avg_price"] if it.get("avg_price") else None,
                    liquid=True,
                    stress=0.3,
                    ticker=it["ticker"],
                    qty=it["qty"],
                    price=price,
                )
            h["name"] = f"{h['name']} ({institution})"
        else:
            cls = "deposit" if it["type"] == "deposit" else "cash"
            h = valuation.holding(
                client_id,
                "statement",
                f"{tag}:{cls}:{len(out)}",
                trust="statement",
                cls=cls,
                name=f"{it['name']} ({institution})",
                value=it["balance"],
                liquid=True,
                rate=it.get("rate"),
                maturity=it.get("maturity"),
                opened=None if not it.get("maturity") else mk["as_of"],
            )
        h["detail"].update({"institution": institution, "file": filename})
        out.append(h)
    store.put_holdings(client_id, "statement", out)
    total = sum(h["value"] for h in out)
    return {
        "read": {
            "client_id": client_id,
            "filename": filename,
            "institution": institution,
            "method": method,
            "count": len(out),
            "total": total,
            "holdings": out,
        }
    }
