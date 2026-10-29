"""The assistant's words as sentences to speak: markdown read as prose, cut at sentence ends and line ends.

`Sentences.feed(delta)` takes the model's text as it streams and returns the sentences it completed;
`Sentences.flush()` returns the rest at the end of the answer (docs/VOICE_PLAN.md V-D4). A cut needs a space or a
line end after the mark, so "7,54", "7.5" and "09/10/2026" stay whole.
"""

from __future__ import annotations

import re
from typing import List

_MARK = re.compile(r"[.!?;:…](?=\s)|\n")
# A line's lead: a heading, a list mark, a quote. Matched only at a line's start, and only once the line has
# more than the mark (a lone "1" may still become "1. ").
_LEAD = re.compile(r"[ \t]*(?:#{1,6}[ \t]+|[-*+•][ \t]+|\d{1,2}[.)][ \t]+|>[ \t]*)")
_MAYBE_LEAD = re.compile(r"[ \t]*(?:#{0,6}|[-*+•>]|\d{1,2}[.)]?)")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_RULE = re.compile(r"^[\s|:\-=_*]*$")  # a table's |---|---| or a horizontal rule
_EMPHASIS = re.compile(r"\*\*|__|`|~~|\*")
_SPACES = re.compile(r"\s+")


def prose(piece: str) -> str:
    """One piece of markdown as words to say: links by their text, no emphasis marks, a table row's cells
    separated by commas, a rule nothing."""
    if _RULE.match(piece):
        return ""
    text = _LINK.sub(r"\1", piece)
    text = _EMPHASIS.sub("", text)
    cells = [c.strip() for c in text.strip().strip("|").split("|")]
    text = ", ".join(c for c in cells if c)
    return _SPACES.sub(" ", text).strip()


class Sentences:
    """One answer's text, fed as it streams, out as sentences."""

    def __init__(self) -> None:
        self.buf = ""
        self.line_start = True

    def feed(self, delta: str) -> List[str]:
        self.buf += delta or ""
        out: List[str] = []
        while self.buf:
            if self.line_start:
                lead = _LEAD.match(self.buf)
                if lead:
                    self.buf = self.buf[lead.end() :]
                elif _MAYBE_LEAD.fullmatch(self.buf):
                    break  # wait: the line's lead is not complete yet
                self.line_start = False
                continue
            cut = _MARK.search(self.buf)
            if cut is None:
                break
            end = cut.end()
            piece, self.buf = self.buf[:end], self.buf[end:]
            if piece.endswith("\n"):
                self.line_start = True
            said = prose(piece)
            if said:
                out.append(said)
        return out

    def flush(self) -> List[str]:
        piece, self.buf, self.line_start = self.buf, "", True
        lead = _LEAD.match(piece)
        said = prose(piece[lead.end() :] if lead else piece)
        return [said] if said else []
