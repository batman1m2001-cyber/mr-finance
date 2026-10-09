"""Reading a statement file, and the rule reader for the layouts we know.

A file becomes text (every format) and rows (CSV and Excel). The rule reader finds a header row
that names a ticker and a quantity, and lines that give a balance; the model reads anything
else. Both give the same items::

    {"type": "stock", "ticker", "qty", "avg_price", "price"}
    {"type": "cash" | "deposit", "name", "balance", "rate", "maturity"}
"""

from __future__ import annotations

import csv
import io
import re
from typing import Any, Dict, List, Optional, Tuple

from wealth.text import ascii_lower, number

INSTITUTIONS = (
    "VPS",
    "SSI",
    "VNDIRECT",
    "HSC",
    "MBS",
    "VIETCOMBANK",
    "BIDV",
    "VIETINBANK",
    "VPBANK",
    "ACB",
    "MB",
    "SACOMBANK",
    "TPBANK",
    "AGRIBANK",
)
NICE = {
    "VIETCOMBANK": "Vietcombank",
    "VIETINBANK": "VietinBank",
    "VPBANK": "VPBank",
    "SACOMBANK": "Sacombank",
    "TPBANK": "TPBank",
    "AGRIBANK": "Agribank",
    "VNDIRECT": "VNDirect",
}

TICKER = ("ma ck", "ma chung khoan", "ma", "ticker", "symbol", "ma cp")
QTY = ("so luong", "khoi luong", "kl", "sl", "quantity", "so luong co phieu")
COST = ("gia von", "gia binh quan", "gia tb", "gia mua tb", "avg price")
PRICE = ("gia thi truong", "gia hien tai", "gia", "market price")
VALUE = ("gia tri", "gia tri thi truong", "value")


def read_file(filename: str, raw: bytes) -> Tuple[str, str, List[List[Any]]]:
    """(kind, text, rows) of a file: ``csv``, ``xlsx``, ``pdf`` or ``txt``."""
    name = filename.lower()
    if name.endswith(".csv"):
        text = raw.decode("utf-8-sig", errors="replace")
        return "csv", text, [row for row in csv.reader(io.StringIO(text))]
    if name.endswith((".xlsx", ".xlsm")):
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        rows = [list(r) for ws in wb.worksheets for r in ws.iter_rows(values_only=True)]
        text = "\n".join(",".join("" if c is None else str(c) for c in r) for r in rows)
        return "xlsx", text, rows
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages)
        return "pdf", text, []
    return "txt", raw.decode("utf-8", errors="replace"), []


def institution(text: str) -> str:
    head = ascii_lower(text[:400]).upper()
    for name in INSTITUTIONS:
        if re.search(rf"\b{name}\b", head):
            return NICE.get(name, name)
    return "Tổ chức khác"


def _col(header: List[str], names) -> Optional[int]:
    for i, h in enumerate(header):
        if h in names:
            return i
    return None


def rule_items(kind: str, text: str, rows: List[List[Any]]) -> List[Dict[str, Any]]:
    """What the rules can read: a holdings table, and balance lines."""
    items: List[Dict[str, Any]] = []
    header_at = None
    for i, row in enumerate(rows):
        header = [ascii_lower(c) if c is not None else "" for c in row]
        if _col(header, TICKER) is not None and _col(header, QTY) is not None:
            header_at = i
            break
    if header_at is not None:
        header = [ascii_lower(c) if c is not None else "" for c in rows[header_at]]
        t, q = _col(header, TICKER), _col(header, QTY)
        c, p, v = _col(header, COST), _col(header, PRICE), _col(header, VALUE)
        for row in rows[header_at + 1 :]:
            if not row or t >= len(row) or row[t] in (None, ""):
                continue
            label = str(row[t]).strip()
            cell = lambda j: row[j] if j is not None and j < len(row) else None  # noqa: E731
            if ascii_lower(label).startswith("tien"):
                bal = number(cell(v))
                if bal:
                    items.append({"type": "cash", "name": "Tiền tại công ty chứng khoán", "balance": bal})
                continue
            qty = number(cell(q))
            if qty and re.fullmatch(r"[A-Za-z0-9]{3,5}", label):
                items.append(
                    {
                        "type": "stock",
                        "ticker": label.upper(),
                        "qty": qty,
                        "avg_price": number(cell(c)),
                        "price": number(cell(p)),
                    }
                )
    for line in text.splitlines():
        low = ascii_lower(line)
        if "so du" not in low:
            continue
        m = re.search(r"so du:?\s*([\d.,]+)", low)
        bal = number(m.group(1)) if m else None
        if not bal:
            continue
        term = "ky han" in low
        rate = re.search(r"lai suat:?\s*([\d.,]+)\s*%", low)
        due = re.search(r"dao han:?\s*(\d{1,2})/(\d{1,2})/(\d{4})", low)
        months = re.search(r"ky han (\d+) thang", low)
        items.append(
            {
                "type": "deposit" if term else "cash",
                # the statement's words, in Vietnamese however the export spelled them
                "name": (f"Tiền gửi có kỳ hạn {months.group(1)} tháng" if months else "Tiền gửi có kỳ hạn")
                if term
                else "Tài khoản thanh toán",
                "balance": bal,
                "rate": number(rate.group(1)) / 100 if rate else None,
                "maturity": f"{due.group(3)}-{int(due.group(2)):02d}-{int(due.group(1)):02d}" if due else None,
            }
        )
    return items


def clean_items(items: Any) -> List[Dict[str, Any]]:
    """The model's items, kept only when they have what a holding needs."""
    out = []
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        kind = str(it.get("type") or "").lower()
        if kind == "stock":
            ticker = str(it.get("ticker") or "").strip().upper()
            qty = number(it.get("qty"))
            if re.fullmatch(r"[A-Z0-9]{3,5}", ticker) and qty:
                out.append(
                    {
                        "type": "stock",
                        "ticker": ticker,
                        "qty": qty,
                        "avg_price": number(it.get("avg_price")),
                        "price": number(it.get("price")),
                    }
                )
        elif kind in ("cash", "deposit"):
            bal = number(it.get("balance"))
            if bal:
                rate = number(it.get("rate"))
                out.append(
                    {
                        "type": kind,
                        "name": str(it.get("name") or ("Tiền gửi" if kind == "deposit" else "Tiền")),
                        "balance": bal,
                        "rate": rate / 100 if rate and rate > 1 else rate,
                        "maturity": it.get("maturity")
                        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(it.get("maturity") or ""))
                        else None,
                    }
                )
    return out
