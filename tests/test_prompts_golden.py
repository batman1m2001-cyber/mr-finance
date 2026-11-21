"""The prompts are files in ``prompts/`` (operonx.prompts); what the models are sent did not change when they
moved there. ``golden/prompts.json`` holds the sha256 of each text as the code had it as a constant.

A wording change is deliberate: edit the file, then publish it (``operonx prompt publish <name>``) and put the new
sha256 here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from operonx.prompts import prompt, prompt_names

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = json.loads((Path(__file__).parent / "golden" / "prompts.json").read_text(encoding="utf-8"))


def test_every_prompt_is_the_bytes_it_was():
    for name, want in GOLDEN.items():
        p = prompt(name, root=ROOT)
        text = str(p) if want["as"] == "template" else p.text  # a template is what str.format / LLMOp fills
        assert hashlib.sha256(text.encode()).hexdigest() == want["sha256"], name


def test_every_prompt_file_is_accounted_for():
    assert sorted(GOLDEN) == prompt_names(ROOT)


def test_the_code_uses_them():
    from assistant import attachments, consolidate, sessions, turn, web
    from research import suggest
    from statements.graph import READ_PROMPT
    from trial import daily

    assert consolidate.SYSTEM == prompt("assistant/consolidate", root=ROOT).text
    assert web.SYSTEM and sessions.SYSTEM and attachments.PROMPT
    assert "{who}" in turn.RULES and "{n}" in daily.SYSTEM and "{purposes}" in suggest.SYSTEM
    assert [p.name for p in READ_PROMPT.values()] == ["statements/read.system", "statements/read.user"]
