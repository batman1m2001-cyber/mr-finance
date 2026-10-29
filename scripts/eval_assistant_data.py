"""The data room's eval on a real model (docs/ASSISTANT_DATA_PLAN.md D5, ADR-0040).

Asks every conversation of ``data/assistant_data_eval.json`` through ``assistant_flow`` — the served graph, the
barrier installed — on a copy of a state file. Before the model is asked, each turn's gold SQL runs in that role's
own room on the same copy, so the gold is what the data says that day. Each answer is graded against it (numbers
with tỷ/triệu/nghìn read, within 1 %, counts exactly; names without diacritics; “none” as 0 or as none), and a
dispute turn must also have counted again with ``truy_van`` (§3.5). Reports per role and in total — accuracy,
latency p50/p95, the provider's cost, requests and input tokens per turn — and the file's ``gate``.

    .venv/bin/python scripts/eval_assistant_data.py --env ../mr-finance/.env --state ../mr-finance/data/state.db

``--model`` asks another model as ``llm:copilot``; ``--reasoning low`` is for a model whose endpoint will not turn
reasoning off (Sonnet 5.5 on OpenRouter: “Reasoning is mandatory for this endpoint”). Nothing is printed from the
env file. The model calls cost money: ``--ids`` and ``--roles`` ask fewer.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sqlite3
import sys
import tempfile
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

TOKEN = re.compile(r"-?\d[\d.,]*\d|-?\d")
UNIT = re.compile(r"\s*(tỷ|ty|triệu|trieu|tr\b|nghìn|ngàn|nghin)", re.I)
SCALE = {"tỷ": 1e9, "ty": 1e9, "triệu": 1e6, "trieu": 1e6, "tr": 1e6, "nghìn": 1e3, "ngàn": 1e3, "nghin": 1e3}
NONE = ("không có", "chưa có", "không ghi nhận", "chưa ghi nhận", "không tìm thấy", "chưa phát sinh", "không phát sinh")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
# a reason guessed for why the person's number differs (§3.5: count again, say how, do not guess why); “tôi có thể
# liệt kê…” is an offer and “bạn có thể bổ sung trên trang Tài sản” says where to add a missing item, not a reason
GUESS = re.compile(
    r"(?<!tôi )(?<!bạn )có thể(?! (bổ sung|thêm|cập nhật|nhập))|bạn có thể (?!bổ sung|thêm|cập nhật|nhập)|có lẽ"
    r"|nguyên nhân|lý do|vì sao",
    re.I,
)


def plain(s: Any) -> str:
    s = unicodedata.normalize("NFD", str(s).lower()).replace("đ", "d")
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def readings(token: str) -> Set[float]:
    """What one number token may mean: “1.420” and “1,420” are 1420 (or 1.42), “48,4” is 48.4."""
    if "." in token and "," in token:
        cands = [token.replace(".", "").replace(",", "."), token.replace(",", "")]
    else:
        sep = "." if "." in token else "," if "," in token else ""
        parts = token.split(sep) if sep else [token]
        cands = [token.replace(sep, "")] if sep and all(len(p) == 3 for p in parts[1:]) else []
        if len(parts) <= 2:
            cands.append(token.replace(",", ".") if sep else token)
    out = set()
    for c in cands:
        try:
            out.add(float(c))
        except ValueError:
            pass
    return out


def numbers(text: str) -> Set[float]:
    """Every value the text says, with its unit read: “48,4 tỷ” is 48.4 and 48 400 000 000."""
    vals: Set[float] = set()
    for m in TOKEN.finditer(text or ""):
        base = readings(m.group())
        vals |= base
        u = UNIT.match(text, m.end())
        if u:
            vals |= {v * SCALE[u.group(1).lower()] for v in base}
    return vals | {abs(v) for v in vals}


def says_number(gold: Any, text: str) -> bool:
    g = abs(float(gold))
    vals = numbers(text)
    if isinstance(gold, int) and g < 1e6:  # a count: exactly
        return g in vals
    return any(abs(v - g) <= 0.01 * g + 1e-9 for v in vals)


def says_cell(cell: Any, text: str) -> bool:
    if cell is None:
        return True
    if isinstance(cell, (int, float)):
        return says_number(cell, text)
    if DATE.fullmatch(cell):
        _, m, d = cell.split("-")
        return any(x in text for x in (cell, f"{int(d)}/{int(m)}", f"{d}/{m}"))
    name = plain(re.sub(r"\s*\(.*?\)", "", cell)).strip()  # “Học phí cho con (trong nước / du học)”: the name
    return name in plain(text)


def says_none(text: str) -> bool:
    return says_number(0, text) or any(p in (text or "").lower() for p in NONE)


def correct(turn: Dict[str, Any], text: str) -> bool:
    """The answer says what the gold rows say, as ``want`` asks."""
    g, want = turn.get("gold") or {}, turn["want"]
    if "error" in g or not text or "rows" not in g:
        return False
    rows, cols = g["rows"], g["columns"]
    first = rows[0][0] if rows else None
    if want == "none" or (want == "v" and first in (0, None)):
        return first in (0, None) and says_none(text)
    if want == "v":
        return says_cell(first, text)
    if want == "row":
        return all(says_cell(c, text) for c in rows[0])
    _, col, k = want.split(":")
    i = cols.index(col)
    return all(says_cell(r[i], text) for r in (rows if k == "all" else rows[: int(k)]))


def pct(xs: List[float], p: float) -> Optional[float]:
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(len(xs) * p))], 2) if xs else None


def summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    secs = [r["seconds"] for r in rows]
    costs = [r["cost_usd"] for r in rows if r["cost_usd"] is not None]
    reqs = [r["requests"] or 0 for r in rows]
    tokens = [r["input_tokens"] or 0 for r in rows]
    disputes = [r for r in rows if r["dispute"]]
    return {
        "turns": len(rows),
        "correct": sum(r["correct"] for r in rows),
        "accuracy": round(sum(r["correct"] for r in rows) / max(1, len(rows)), 3),
        "seconds_p50": pct(secs, 0.5),
        "seconds_p95": pct(secs, 0.95),
        "cost_usd_total": round(sum(costs), 4),
        "cost_per_turn_usd": round(sum(costs) / len(costs), 5) if len(costs) == len(rows) and costs else None,
        "unpriced_turns": len(rows) - len(costs),
        "requests_per_turn": round(sum(reqs) / max(1, len(rows)), 2),
        "input_tokens_per_request": round(sum(tokens) / max(1, sum(reqs))),
        "input_tokens_max_turn": max(tokens, default=0),
        "used_the_room": sum(bool(r["sql"]) for r in rows),
        "disputes": len(disputes),
        "disputes_counted_again": sum(bool(r["sql"]) for r in disputes),
        "disputes_guessed_why": sum(r["guessed"] for r in disputes),
    }


def gate(g: Dict[str, Any], total: Dict[str, Any], roles: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    have = {
        "accuracy": total["accuracy"],
        "accuracy_per_role": min((r["accuracy"] for r in roles.values()), default=None),
        "seconds_p95": total["seconds_p95"],
        "cost_per_turn_usd": total["cost_per_turn_usd"],
        "disputes_counted_again": total["disputes_counted_again"] / total["disputes"] if total["disputes"] else None,
    }
    at_most = {"seconds_p95", "cost_per_turn_usd"}
    failed = []
    for k, want in g.items():
        v = have.get(k)
        if v is None or (v > want if k in at_most else v < want):
            failed.append(f"{k}: {v} ({'≤' if k in at_most else '≥'} {want})")
    return {"ready": not failed, "failed": failed, "values": {k: have.get(k) for k in g}}


async def main_async(a) -> Dict[str, Any]:
    import operonx
    from operonx import Operon

    operonx.bootstrap(resources=str(ROOT / "resources.yaml"))
    from assistant import dataroom, registry, turn
    from assistant.base import Ctx
    from assistant.graph import assistant_flow
    from control import barrier

    barrier.install()
    if a.reasoning:
        turn.NO_REASONING = {"reasoning": {"effort": a.reasoning}}
    flow = Operon(assistant_flow, params={k: None for k in ("message", "role", "client_id", "scope", "route", "goals",
                                                             "turn_id", "approvals", "conversation_id")})  # fmt: skip
    data = json.loads(Path(a.cases).read_text())
    cases = [c for c in data["cases"] if (not a.roles or c["role"] in a.roles.split(","))]
    if a.ids:
        cases = [c for c in cases if c["id"] in a.ids.split(",")]
    for c in cases:  # the gold first, on the same copy, before any turn adds a row
        ctx = Ctx(role=c["role"], client_id=c["client_id"], scope="personal", question="",
                  user=registry.DEMO_USER.get(c["role"]))  # fmt: skip
        for t in c["turns"]:
            ctx.queries = 0
            try:
                r = await dataroom.query(ctx, t["sql"])
                t["gold"] = {"columns": r["columns"], "rows": r["rows"][:10], "total": r["total"]}
            except Exception as exc:  # noqa: BLE001 — a gold that does not run is the eval's bug, reported
                t["gold"] = {"error": f"{type(exc).__name__}: {exc}"}

    rows = []
    for c in cases:
        cid = None
        for n, t in enumerate(c["turns"]):
            if a.skip_disputes and t.get("dispute"):
                continue
            t0 = time.perf_counter()
            out = await flow.run(inputs={"message": t["q"], "role": c["role"], "client_id": c["client_id"],
                                         "route": c["route"], "conversation_id": cid})  # fmt: skip
            took = time.perf_counter() - t0
            ans = out.get("assistant") or {}
            cid = ans.get("conversation_id", cid)
            u = ans.get("usage") or {}
            sql = [s["query"]["sql"] for s in ans.get("steps") or [] if s.get("query")]
            text = ans.get("text") or ""
            guessed = bool(t.get("dispute") and GUESS.search(text))
            ok = ans.get("mode") in ("model", "template") and correct(t, text)
            ok = ok and (not t.get("dispute") or (bool(sql) and not guessed))
            rows.append(
                {
                    "id": c["id"],
                    "turn": n,
                    "role": c["role"],
                    "q": t["q"],
                    "dispute": bool(t.get("dispute")),
                    "guessed": guessed,
                    "correct": ok,
                    "mode": ans.get("mode"),
                    "model": ans.get("model"),
                    "seconds": round(took, 2),
                    "cost_usd": u.get("cost_usd"),
                    "requests": u.get("requests"),
                    "input_tokens": u.get("input_tokens"),
                    "sql": sql,
                    "answer": text,
                    "gold": t["gold"].get("rows", t["gold"]),
                }  # fmt: skip
            )
            print(f"{'PASS' if ok else 'FAIL'} {c['id']}.{n} {took:5.1f}s ${u.get('cost_usd')} {t['q'][:60]}")

    roles = {r: summary([x for x in rows if x["role"] == r]) for r in dict.fromkeys(x["role"] for x in rows)}
    total = summary(rows)
    return {
        "model": os.environ.get("LLM_MODEL_COPILOT"),
        "reasoning": a.reasoning or "off",
        "at": time.strftime("%Y-%m-%d %H:%M"),
        "total": total,
        "roles": roles,
        "gate": gate(data.get("gate") or {}, total, roles),
        "rows": rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True, help="an env file with the model's settings (read, never printed)")
    ap.add_argument("--state", required=True, help="a state file to copy (the copy is used, the file is not changed)")
    ap.add_argument("--cases", default=str(ROOT / "data/assistant_data_eval.json"))
    ap.add_argument("--roles", default="", help="only these roles, comma-separated")
    ap.add_argument("--ids", default="", help="only these cases, comma-separated")
    ap.add_argument("--model", default="", help="ask this model as llm:copilot instead of the env file's")
    ap.add_argument("--reasoning", default="", help="a reasoning effort, for a model that will not turn it off")
    ap.add_argument("--skip-disputes", action="store_true", help="leave out the turns that dispute a number")
    ap.add_argument("--out", default=str(ROOT / "evals/assistant_data/results"))
    a = ap.parse_args()
    from dotenv import load_dotenv

    load_dotenv(a.env, override=True)
    if a.model:
        os.environ["LLM_MODEL_COPILOT"] = a.model
    work = Path(tempfile.mkdtemp(prefix="mf-data-eval-"))
    with sqlite3.connect(a.state) as s, sqlite3.connect(work / "state.db") as d:
        s.backup(d)  # a consistent copy of a file the live server may be writing; assistant.db starts empty beside it
    os.environ.update({"MF_STATE": str(work / "state.db"), "MF_AUTH": "off", "MF_AI": "on"})
    report = asyncio.run(main_async(a))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    name = f"{time.strftime('%Y%m%d-%H%M')}-{(report['model'] or 'model').split('/')[-1]}.json"
    (out / name).write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, ensure_ascii=False, indent=1))
    print(f"→ {out / name}")


if __name__ == "__main__":
    main()
