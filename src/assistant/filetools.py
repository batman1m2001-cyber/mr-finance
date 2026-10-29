"""The two writes for an attached file (docs/OCR_PLAN.md O-D6, ADR-0041), both behind Xác nhận.

- ``them_tu_tep`` saves the reading's items into the client's assets: stocks, cash and deposits as a statement's
  holdings (``statements.ops.as_holding``), the rest as declared profile items, as the chat's declare writers keep
  them. The line the person confirms lists every item and the total; what is saved is the reading kept at attach
  (O-D2), so the confirmed line and the write cannot differ.
- ``luu_tai_lieu`` keeps the file in Tài liệu (the Bộ nhớ page); a photo is kept as its reading, in Markdown.

A balance's key is its content (name, amount, rate, maturity), so the same receipt attached twice replaces itself;
a stock's is its ticker at the institution, as on the statement page.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from assistant import attachments as att
from assistant import knowledge
from assistant.base import Ctx, Param, Tool, ToolFailed
from assistant.tools import _need_client

HOLDINGS = ("stock", "cash", "deposit")
FILE = Param(str, "mã tệp đính kèm, dạng tep_…, lấy từ dòng [Tệp đính kèm …]")
PICK = Param(str, "số thứ tự các khoản cần ghi, vd “1,3”; bỏ trống là ghi tất cả", default="")


def _file(ctx: Ctx, fid: Any, content: bool = False) -> Dict[str, Any]:
    try:
        return att.get(ctx, str(fid or "").strip(), content=content)
    except att.Refused as exc:
        raise ToolFailed(str(exc)) from None


def _picked(items: List[Dict[str, Any]], pick: Any) -> List[int]:
    if isinstance(pick, list):
        want = pick
    else:
        want = [x for x in str(pick or "").replace(";", ",").split(",") if x.strip()]
    if not want:
        return list(range(len(items)))
    try:
        got = sorted({int(str(x).strip()) - 1 for x in want})
    except ValueError:
        raise ToolFailed("Số thứ tự khoản là các số, vd “1,3”") from None
    if not got or got[0] < 0 or got[-1] >= len(items):
        raise ToolFailed(f"Tệp này có {len(items)} khoản, đánh số từ 1")
    return got


def _ident(fname: str, it: Dict[str, Any]) -> str:
    said = json.dumps([it.get(k) for k in ("name", "balance", "rate", "maturity")], ensure_ascii=False, default=str)
    return hashlib.sha1(f"{fname}|{said}".encode()).hexdigest()[:10]


def _profile(it: Dict[str, Any], fname: str) -> Dict[str, Any]:
    """A declared item, in the shape the chat's declare writers write (src/declare/tools.py)."""
    from declare import _rules

    t, tag = it["type"], " (từ tệp)"
    if t == "property":
        return {"class": "real_estate", "name": it["name"] + tag, "area": _rules.area_of(it.get("location") or ""),
                "location": it.get("location") or "", "sqm": it.get("sqm"), "purchase_year": it.get("purchase_year"),
                "purchase_price": it.get("purchase_price"), "value": it["value"],
                "rental_monthly": it.get("rental_monthly") or 0, "file": fname}  # fmt: skip
    if t == "gold":
        return {"class": "gold", "name": "Vàng" + tag, "qty": it["qty"], "file": fname}
    if t == "loan":
        return {"class": "loan", "name": it["name"] + tag, "value": it["value"],
                "monthly_payment": it.get("monthly_payment") or 0, "rate": it.get("rate"), "rate_type": "fixed",
                "file": fname}  # fmt: skip
    return {"class": it["class"], "name": it["name"] + tag, "value": it["value"], "file": fname}


def _what(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The file, the items picked, and each as it will be written: a holding (valued now) or a profile item."""
    from statements.ops import as_holding
    from people import auth
    from wealth import fixtures, valuation

    cid = _need_client(ctx)
    auth.require_client(cid)
    f = _file(ctx, args.get("tep"))
    r = f["reading"]
    if not r["items"]:
        raise ToolFailed(f"“{f['name']}” không có khoản nào ghi được vào tài sản; có thể lưu nó vào Tài liệu")
    picked = _picked(r["items"], args.get("khoan"))
    mk = fixtures.market()
    where = r.get("institution") or att.NAMES.get(r["kind"], "Tệp")
    rows = []
    for i in picked:
        it = r["items"][i]
        if it["type"] in HOLDINGS:
            h = as_holding(cid, where, f["name"], it, mk, _ident(f["name"], it))
            rows.append({"n": i, "item": it, "holding": h, "value": h["value"]})
        else:  # valued as the net worth will value it (a property by its area and size, gold at today's price)
            p = _profile(it, f["name"])
            rows.append({"n": i, "item": it, "profile": p, "value": valuation.declared(cid, [p], mk)[0]["value"]})
    return {"client": cid, "file": f, "rows": rows}


def plan_add(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from wealth.money import vnd

    w = _what(ctx, args)
    debt = sum(x["value"] for x in w["rows"] if x["item"]["type"] == "loan")
    owned = sum(x["value"] for x in w["rows"]) - debt
    lines = "; ".join(f"{x['n'] + 1}) {att._item_line(x['item'])}" for x in w["rows"])
    total = " · ".join(s for s in (owned and f"tài sản {vnd(owned)}", debt and f"nợ {vnd(debt)}") if s)
    return {
        "summary": f"Ghi {len(w['rows'])} khoản từ “{w['file']['name']}” vào tài sản: {lines}. Tổng: {total}?",
        "args": {"tep": w["file"]["id"], "khoan": [x["n"] + 1 for x in w["rows"]]},
    }


async def add(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from wealth import store

    w = _what(ctx, args)
    holdings = [x["holding"] for x in w["rows"] if "holding" in x]
    store.put_holdings(w["client"], "statement", holdings)
    known, made = [], []
    for x in w["rows"]:
        if "profile" not in x:
            continue
        same = store.same_profile(w["client"], "asset", x["profile"])
        if same:
            known.append(same)
        else:
            made.append(store.add_profile(w["client"], "asset", {**x["profile"], "via": "tệp"}))
    again = f" ({len(known)} khoản đã có từ trước, không ghi lại)" if known else ""
    return {
        "text": f"Đã ghi {len(w['rows']) - len(known)} khoản từ “{w['file']['name']}” vào tài sản{again}. Xem ở "
        "Dữ liệu chi tiết tài sản.",
        "data": {"client_id": w["client"], "holdings": [h["key"] for h in holdings], "profile": made + known},
    }


def verify_add(ctx: Ctx, out: Dict[str, Any]):
    from wealth import store

    d = out["data"]
    have = {h["key"] for h in store.holdings(d["client_id"], "statement")}
    ids = {p.get("id") for p in store.profile(d["client_id"], "asset")}
    missing = [k for k in d["holdings"] if k not in have] + [i for i in d["profile"] if i not in ids]
    return True if not missing else f"{len(missing)} khoản chưa có trong tài sản"


def _markdown(f: Dict[str, Any]) -> bytes:
    """A photo, or a file Tài liệu does not take, kept as what was read from it."""
    r = f["reading"]
    out = [f"# {r['title'] or f['name']}", "", f"{att.label(r)} · tệp gốc: {f['name']}", ""]
    if r["summary"]:
        out += [r["summary"], ""]
    if r["fields"]:
        out += ["## Thông tin", *[f"- {k}: {v}" for k, v in r["fields"].items()], ""]
    if r["text"]:
        out += ["## Nội dung", r["text"], ""]
    return "\n".join(out).encode()


def _kept(f: Dict[str, Any]) -> Dict[str, Any]:
    """The name and bytes Tài liệu keeps: the file itself when it is a kind Tài liệu reads, else its reading."""
    if att.suffix(f["name"]) in knowledge.KINDS and att.suffix(f["name"]) not in att.IMAGES:
        return {"name": f["name"], "data": f["content"]}
    return {"name": f"{Path(f['name']).stem}.md", "data": _markdown(f)}


def plan_keep(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    f = _file(ctx, args.get("tep"))
    name = _kept({**f, "content": b""})["name"]
    as_read = "" if name == f["name"] else " (lưu phần đọc được từ tệp)"
    return {"summary": f"Lưu “{f['name']}” vào Tài liệu ở trang Bộ nhớ{as_read}?", "args": {"tep": f["id"]}}


async def keep(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    k = _kept(_file(ctx, args.get("tep"), content=True))
    try:
        got = await knowledge.add_material(ctx, k["name"], k["data"])
    except ValueError as exc:
        raise ToolFailed(str(exc)) from None
    return {"text": f"Đã lưu “{got['name']}” vào Tài liệu; tìm lại bằng cách hỏi trợ lý hoặc ở trang Bộ nhớ.",
            "data": {"key": got["key"], "name": got["name"]}}  # fmt: skip


def verify_keep(ctx: Ctx, out: Dict[str, Any]):
    keys = {m["key"] for m in knowledge.materials(ctx)}
    return True if out["data"]["key"] in keys else "tệp chưa có trong Tài liệu"


def _catalogue() -> Dict[str, Tool]:
    from control.roles import ROLES

    return {
        t.name: t
        for t in [
            Tool("them_tu_tep", "ghi các khoản đọc được từ một tệp đính kèm (cổ phiếu, tiền, tiền gửi, bất động sản, "
                 "vàng, tài sản khác, khoản vay) vào tài sản của khách hàng", ("client", "rm"), add, write=True,
                 params={"tep": FILE, "khoan": PICK}, page="tai-san", plan=plan_add, verify=verify_add),
            Tool("luu_tai_lieu", "lưu một tệp đính kèm vào Tài liệu (trang Bộ nhớ) để tìm lại sau", ROLES, keep,
                 write=True, params={"tep": FILE}, page="bo-nho", plan=plan_keep, verify=verify_keep),
        ]
    }  # fmt: skip


CATALOGUE = _catalogue()
