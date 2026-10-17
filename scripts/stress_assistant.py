"""The assistant, tested as its customers use it (docs/ASSISTANT_STRESS_PLAN.md S1–S8).

Every conversation of `docs/brd/testing/assistant/catalogue.json` runs through a served copy of the app (its own
state file), over the stream the panel uses: a demo sign-in, `POST /api/assistant/stream` (SSE), the conversation
carried from turn to turn, a write confirmed or refused the way the panel does it (`{turn_id, approvals}`). After a
turn the state is read back — memory and follow-ups through the app, the review queue from the copy's state file — so
a claimed action is checked, not believed. Each turn is checked by machine (its tools, status, words, grounding, the
state); every transcript is also read by hand (the results say which failures were confirmed that way).

    .venv/bin/python scripts/stress_assistant.py --base http://127.0.0.1:8041 --state <copy>/state.db --tag run1
    … --only nav-01,act-02   … --category actions   … --budget 2.7

Writes `docs/brd/testing/assistant/runs/<tag>/`: one JSON and one Markdown transcript per conversation, and
`results.json` (pass/fail per turn, cost, tokens, latency). Stops before the budget (US$, model and tools) is spent.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "docs" / "brd" / "testing" / "assistant"
_spec = importlib.util.spec_from_file_location("eval_assistant", ROOT / "scripts" / "eval_assistant.py")
EVAL = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(EVAL)  # grounded(), REFUSAL, called_tools(): the A8 eval's own checks

WRITES = {"gui_de_xuat", "ghi_nho", "quen", "theo_doi", "huy_theo_doi", "ghi_lien_he", "khuyen_nghi", "duyet_de_xuat",
          "lay_tin", "danh_dau_khan", "da_xem_canh_bao", "chuyen_gia_duyet"}  # fmt: skip


class Session:
    """One signed-in person on the served copy, speaking through the panel's stream."""

    def __init__(self, base: str, who: str, role: str, client_id: Optional[str]):
        self.http = httpx.Client(base_url=base, timeout=180)
        r = self.http.post("/api/auth/demo", json={"id": who})
        r.raise_for_status()
        self.role, self.client_id, self.cid = role, client_id, None

    def body(self, turn: Dict[str, Any]) -> Dict[str, Any]:
        b = {"role": self.role, "client_id": turn.get("client_id", self.client_id),
             "scope": turn.get("scope", "personal"), "route": turn.get("route", "#/client/xem/tong-quan")}  # fmt: skip
        for k in ("goals", "graph"):
            if k in turn:
                b[k] = turn[k]
        return b

    def stream(self, body: Dict[str, Any]) -> Dict[str, Any]:
        events, text, t0, first = [], [], time.monotonic(), None
        with self.http.stream("POST", "/api/assistant/stream", json=body, headers={"accept": "text/event-stream"}) as r:
            if r.status_code != 200:
                return {"answer": {"status": "http_error", "text": f"HTTP {r.status_code}: {r.read()[:300]!r}"},
                        "events": [], "seconds": time.monotonic() - t0}  # fmt: skip
            for line in r.iter_lines():
                if not line.startswith("data: "):
                    continue
                e = json.loads(line[6:])
                if first is None and e.get("type") in ("text", "step"):
                    first = time.monotonic() - t0
                if e.get("type") == "text":
                    text.append(e.get("text") or "")
                else:
                    events.append(e)
        last = next((e for e in reversed(events) if e.get("type") == "answer"), None)
        a = (last or {}).get("assistant") or {"status": "no_answer", "text": "".join(text)}
        if a.get("conversation_id"):
            self.cid = a["conversation_id"]
        return {"answer": a, "events": events, "streamed": "".join(text), "seconds": time.monotonic() - t0,
                "first_event": first}  # fmt: skip

    def say(self, turn: Dict[str, Any]) -> Dict[str, Any]:
        return self.stream({**self.body(turn), "message": turn["say"], "conversation_id": self.cid})

    def answer_waits(self, turn: Dict[str, Any], last: Dict[str, Any], verdict: str) -> Dict[str, Any]:
        """As the panel's Xác nhận / Huỷ: every waiting write approved or denied, the parked run resumed."""
        a = last["answer"]
        if a.get("confirm"):  # the keyword path's one-shot confirm
            if verdict == "deny":
                return {"answer": {"status": "denied_locally", "text": "Đã huỷ, không có gì được ghi.", "steps": []},
                        "events": [], "seconds": 0.0}  # fmt: skip
            return self.stream({**self.body(turn), "confirm": a["confirm"], "conversation_id": None})
        approvals = {w["id"]: verdict for w in a.get("waits") or []}
        return self.stream(
            {**self.body(turn), "turn_id": a.get("turn_id"), "approvals": approvals, "conversation_id": None}
        )

    def memory(self) -> Dict[str, Any]:
        who = {"role": self.role, "client_id": self.client_id}
        items = self.http.post("/api/assistant/memory", json={**who, "action": "list"}).json()["memory"]["items"]
        fu = self.http.post("/api/assistant/memory", json={**who, "action": "follow_ups"}).json()["memory"]
        return {"items": items, "follow_ups": fu.get("follow_ups") or []}

    def conversations(self, action: str = "list", **extra) -> Dict[str, Any]:
        body = {"role": self.role, "client_id": self.client_id, "action": action, **extra}
        return self.http.post("/api/assistant/conversations", json=body).json().get("conversations") or {}


def reviews(state: Path, client_id: str) -> List[Dict[str, Any]]:
    con = sqlite3.connect(f"file:{state}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute("select * from reviews where client_id = ?", (client_id,))]
    finally:
        con.close()


def usage(a: Dict[str, Any]) -> Dict[str, float]:
    u = a.get("usage") or {}
    return {"cost": float(u.get("cost_usd") or 0) + float(u.get("tools_cost_usd") or 0),
            "input": int(u.get("input_tokens") or 0), "output": int(u.get("output_tokens") or 0),
            "requests": int(u.get("requests") or 0)}  # fmt: skip


def check(turn: Dict[str, Any], got: Dict[str, Any], history: List[Dict[str, Any]], said: List[str],
          state: Dict[str, Any]) -> List[str]:  # fmt: skip
    """The turn's machine checks. `history`: the conversation's earlier answers; `said`: every message so far."""
    e, a = turn.get("expect") or {}, got["answer"]
    called, text, why = EVAL.called_tools(a), a.get("text") or "", []
    if a.get("status") in ("http_error", "no_answer"):
        return [f"{a.get('status')}: {text[:200]}"]
    if e.get("status") and a.get("status") != e["status"]:
        why.append(f"status {a.get('status')} (want {e['status']})")
    want_mode = e.get("mode", "model")
    if want_mode and a.get("mode") != want_mode:
        why.append(f"mode {a.get('mode')} (want {want_mode}; {a.get('why') or ''})")
    for t in e.get("tools_all", []):
        if t not in called:
            why.append(f"did not call {t}")
    if e.get("tools_any") and not set(e["tools_any"]) & set(called):
        why.append(f"called none of {e['tools_any']}")
    for t in e.get("tools_none", []):
        if t in called:
            why.append(f"called {t}")
    if "max_tools" in e and len(called) > e["max_tools"]:
        why.append(f"{len(called)} tool calls (at most {e['max_tools']}): {called}")
    waits = [w.get("tool") for w in a.get("waits") or []] + ([a["confirm"].get("tool")] if a.get("confirm") else [])
    if e.get("pending") and e["pending"] not in waits:
        why.append(f"no confirmation asked for {e['pending']} (waits {waits})")
    if e.get("no_write") and (waits or set(called) & WRITES - set(e.get("writes_ok", []))):
        why.append(f"a write was called or waits: {waits or called}")
    for rx in [e["says"]] if isinstance(e.get("says"), str) else e.get("says", []):
        if not re.search(rx, text, re.I | re.S):
            why.append(f"does not say /{rx}/")
    for rx in e.get("not_says", []):
        if re.search(rx, text, re.I | re.S):
            why.append(f"says /{rx}/")
    if e.get("refuse") and not EVAL.REFUSAL.search(text):
        why.append("does not say it cannot")
    if e.get("sourced") and not (a.get("sources") or re.search(r"https?://", text)):
        why.append("no source named")
    if e.get("grounded", True):
        steps = [s for b in [*history, a] for s in b.get("steps") or []]
        evidence = json.dumps([{k: s.get(k) for k in ("text", "card", "data")} for s in steps], ensure_ascii=False)
        bad = EVAL.grounded(text, evidence + "\n" + "\n".join(said))
        if bad:
            why.append(f"numbers not from the tools or the person: {bad}")
    for k, rx in (turn.get("state") or {}).items():  # read back from the app, not from the answer
        if k == "memory_has" and not any(
            re.search(rx, json.dumps(i, ensure_ascii=False), re.I) for i in state["items"]
        ):
            why.append(f"memory has nothing like /{rx}/")
        if k == "memory_lacks" and any(re.search(rx, json.dumps(i, ensure_ascii=False), re.I) for i in state["items"]):
            why.append(f"memory still has /{rx}/")
        if k == "follow_ups" and len(state["follow_ups"]) != rx:
            why.append(f"{len(state['follow_ups'])} follow-ups (want {rx})")
        if k == "reviews_new" and state["reviews_new"] != rx:
            why.append(f"{state['reviews_new']} new reviews in the queue (want {rx})")
    return why


def transcript(conv: Dict[str, Any], turns: List[Dict[str, Any]]) -> str:
    lines = [f"# {conv['id']} — {conv['title']}", "", f"Category: {conv['category']} · persona: {conv['persona']} · "
             f"BRD: {', '.join(conv.get('brd', []))}", "", conv.get("why", ""), ""]  # fmt: skip
    for i, t in enumerate(turns, 1):
        a = t["answer"]
        lines += [f"## Turn {i}", "", f"**Người dùng:** {t['say']}", ""]
        if t.get("graph"):
            lines += [f"*Đồ thị:* `{json.dumps(t['graph'], ensure_ascii=False)}`", ""]
        tools = ", ".join(f"{s.get('tool')}{'' if s.get('ok', True) else ' (lỗi)'}" for s in a.get("steps") or [])
        waits = ", ".join(w.get("tool", "") for w in a.get("waits") or [])
        lines += [f"*Công cụ:* {tools or '—'}" + (f" · *chờ xác nhận:* {waits}" if waits else "")
                  + f" · *trạng thái:* {a.get('status')} · *chế độ:* {a.get('mode')} · {t['seconds']:.1f} s · "
                  f"US${t['usage']['cost']:.5f}", "", "**Trợ lý:**", "", (a.get("text") or "").strip(), ""]  # fmt: skip
        lines += [f"**Kiểm tra:** {'đạt' if not t['why'] else '; '.join(t['why'])}", ""]
    return "\n".join(lines)


def run_conversation(conv: Dict[str, Any], base: str, state: Path, out: Path, spent: float, budget: float):
    who = conv.get("as", conv.get("client_id", "C01"))
    role = conv.get("role", "client")
    client = conv.get("client_id", who if role == "client" else None)
    s = Session(base, who, role, client)
    before = len(reviews(state, client)) if client else 0
    history, said, done = [], [], []
    for turn in conv["turns"]:
        if spent >= budget:
            done.append({"say": turn.get("say", ""), "skipped": "budget", "why": ["skipped: budget"], "answer": {},
                         "seconds": 0, "usage": {"cost": 0, "input": 0, "output": 0, "requests": 0}})  # fmt: skip
            continue
        if turn.get("new_session"):
            s.cid = None
        if "confirm" in turn:
            got = s.answer_waits(turn, done[-1], turn["confirm"])
            said_now = "Xác nhận" if turn["confirm"] == "approve" else "Huỷ"
        else:
            got = s.say(turn)
            said_now = turn["say"]
        said.append(said_now)
        st = s.memory()
        st["reviews_new"] = (len(reviews(state, client)) - before) if client else 0
        why = check(turn, got, history, said, st)
        u = usage(got["answer"])
        spent += u["cost"]
        rec = {"say": said_now, "graph": turn.get("graph"), "answer": got["answer"], "seconds": got["seconds"],
               "first_event": got.get("first_event"), "usage": u, "why": why,
               "events": [e for e in got["events"] if e.get("type") != "answer"], "state": st}  # fmt: skip
        done.append(rec)
        history.append(got["answer"])
    if conv.get("after"):  # checks on the conversation as a whole: its title, its place in the history
        listed = s.conversations("list").get("items") or []
        mine = next((c for c in listed if c.get("id") == s.cid), None)
        why = []
        if conv["after"].get("titled") and not (mine and mine.get("title")):
            why.append("the conversation has no title")
        if done:
            done[-1]["why"] += why
    (out / f"{conv['id']}.json").write_text(json.dumps({**conv, "run": done}, ensure_ascii=False, indent=1))
    (out / f"{conv['id']}.md").write_text(transcript(conv, done))
    return done, spent


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", default="http://127.0.0.1:8041")
    ap.add_argument("--state", required=True, help="the served copy's state.db (read-only here)")
    ap.add_argument("--catalogue", default=str(HERE / "catalogue.json"))
    ap.add_argument("--tag", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--category", default="")
    ap.add_argument("--budget", type=float, default=2.7)
    ap.add_argument("--spent", type=float, default=0.0, help="already spent in earlier runs (US$)")
    a = ap.parse_args()
    cat = json.loads(Path(a.catalogue).read_text())
    convs = [c for c in cat["conversations"] if (not a.only or c["id"] in a.only.split(","))
             and (not a.category or c["category"] == a.category)]  # fmt: skip
    out = HERE / "runs" / a.tag
    out.mkdir(parents=True, exist_ok=True)
    spent, rows = a.spent, []
    for c in convs:
        t0 = time.monotonic()
        try:
            done, spent = run_conversation(c, a.base, Path(a.state), out, spent, a.budget)
        except Exception as exc:  # noqa: BLE001 - a harness failure is recorded, the run goes on
            done = [{"why": [f"harness: {type(exc).__name__}: {exc}"], "usage": {"cost": 0}, "seconds": 0}]
        ok = all(not t["why"] for t in done)
        cost = sum(t["usage"]["cost"] for t in done)
        rows.append({"id": c["id"], "category": c["category"], "turns": len(done), "ok": ok,
                     "failed": [[i + 1, t["why"]] for i, t in enumerate(done) if t["why"]], "cost": round(cost, 6),
                     "seconds": round(time.monotonic() - t0, 1),
                     "tokens": sum(t["usage"].get("input", 0) + t["usage"].get("output", 0)
                                   for t in done)})  # fmt: skip
        print(f"{'ok  ' if ok else 'FAIL'} {c['id']:12} {len(done)} turns  US${cost:.4f}  total US${spent:.4f}"
              + ("" if ok else f"  {rows[-1]['failed']}"), flush=True)  # fmt: skip
    res = {"tag": a.tag, "base": a.base, "spent_total": round(spent, 6), "conversations": rows,
           "passed": sum(r["ok"] for r in rows), "of": len(rows),
           "turns": sum(r["turns"] for r in rows),
           "turns_failed": sum(len(r["failed"]) for r in rows)}  # fmt: skip
    (out / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(f"{res['passed']}/{res['of']} conversations, {res['turns']} turns ({res['turns_failed']} failed), "
          f"US${spent:.4f} spent in all")  # fmt: skip


if __name__ == "__main__":
    sys.exit(main())
