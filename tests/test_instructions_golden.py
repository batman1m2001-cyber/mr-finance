"""The assistant's instructions are one prompt object, ``prompts/assistant/instructions.yaml`` (operonx
PROMPT_OBJECTS_PLAN O4): what the model is sent did not change when the Python constants became the text objects it
links. ``golden/instructions.json`` holds the sha256 of the instructions for every role × switch, as the code wrote
them before (the date fixed).

A wording change is deliberate: edit the text object, then rewrite the file
(``python tests/test_instructions_golden.py``).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = Path(__file__).parent / "golden" / "instructions.json"
TODAY = dt.date(2026, 11, 22)

ROLES = ("client", "rm", "cio", "admin")
GRAPHS = {
    "none": {},
    "picked": {"lens": "tai-san", "selected": {"kind": "holding", "label": "VCB", "id": "h-1"}, "active": []},
}


class _Date(dt.date):
    @classmethod
    def today(cls):
        return TODAY


def _cases():
    for role, reads, recount, voice, lang, remembered, graph in itertools.product(
        ROLES, (True, False), (False, True), (False, True), ("vi", "en"), (False, True), GRAPHS
    ):
        key = (
            f"{role} reads={int(reads)} recount={int(recount)} voice={int(voice)} lang={lang} "
            f"remembered={int(remembered)} graph={graph}"
        )
        yield (
            key,
            dict(
                role=role,
                reads=reads,
                recount=recount,
                voice=voice,
                lang=lang,
                remembered=["Con gái học ở Úc", "Không mua cổ phiếu ngân hàng"] if remembered else [],
                graph=GRAPHS[graph],
            ),
        )


def _texts(monkeypatch=None):
    from assistant import turn
    from assistant.base import Ctx

    if monkeypatch is not None:
        monkeypatch.setattr(turn, "date", _Date)
    else:
        turn.date = _Date
    out = {}
    for key, kw in _cases():
        ctx = Ctx(client_id="c-1", scope="family", question="?", route="/tai-san", **kw)
        out[key] = str(turn.instructions(SimpleNamespace(deps=ctx)))
    return out


def test_the_instructions_are_the_bytes_they_were(monkeypatch):
    want = json.loads(GOLDEN.read_text(encoding="utf-8"))
    got = {k: hashlib.sha256(t.encode()).hexdigest() for k, t in _texts(monkeypatch).items()}
    assert sorted(got) == sorted(want)
    wrong = [k for k in want if got[k] != want[k]]
    assert not wrong, f"{len(wrong)} of {len(want)} differ, e.g. {wrong[:3]}"


if __name__ == "__main__":  # rewrite the golden file from what the code writes now
    sys.path.insert(0, str(ROOT / "src"))
    texts = _texts()
    GOLDEN.write_text(
        json.dumps({k: hashlib.sha256(t.encode()).hexdigest() for k, t in texts.items()}, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"{len(texts)} instructions, {len(set(texts.values()))} distinct")
