"""One open microphone's state: the question being heard, and the answer's sentences waiting to be spoken.

Kept in SCRATCH by `open_voice`, because the ops that read it outlive any one item (the door in, the turn taker,
the speaker). Every field has one writer, named beside it.
"""

from __future__ import annotations

import asyncio
from typing import List, Optional, Tuple

from voice._text import Sentences

END_OF_TURN = ""  # queued after a turn's last sentence: the speaker says `spoken`


class Voice:
    def __init__(self) -> None:
        self.heard: List[str] = []  # `heard`: transcripts of the question so far; `turn_taking` takes them
        self.at_stt = 0  # `vad_stream` +1 per utterance, `heard` −1 when its transcript lands
        self.listening = True  # `listen`: False from `asked` until the panel says the answer is over
        self.speech: "asyncio.Queue[Optional[Tuple[int, str]]]" = asyncio.Queue()  # `listen` puts, `speak` takes
        self.stopped = -1  # `listen` (Dừng, a new turn): turns up to this one are not spoken
        self.closed = asyncio.Event()  # `listen`'s finally: the socket is gone
        self._turn = -1
        self._cut = Sentences()

    def say(self, turn: int, text: str = "", end: bool = False) -> None:
        """The answer's words as they stream (the panel forwards them): complete sentences are queued."""
        if turn <= self.stopped:
            return
        if turn != self._turn:
            self._turn, self._cut = turn, Sentences()
        for sentence in self._cut.feed(text):
            self.speech.put_nowait((turn, sentence))
        if end:
            for sentence in self._cut.flush():
                self.speech.put_nowait((turn, sentence))
            self.speech.put_nowait((turn, END_OF_TURN))

    def drop(self, turn: int) -> None:
        """A tool step began: the words before it were a lead-in, not the answer; what is not yet a sentence goes."""
        if turn == self._turn:
            self._cut = Sentences()

    def stop(self) -> None:
        """Dừng: nothing more of the current answer is spoken; the microphone listens again."""
        self.stopped = max(self.stopped, self._turn)
        self._cut = Sentences()
        self.listening = True

    def close(self) -> None:
        self.closed.set()
        self.speech.put_nowait(None)
