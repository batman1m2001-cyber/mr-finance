"""Talking to the assistant (docs/VOICE_PLAN.md): the voice door hears a question and speaks an answer; the question
itself goes through the panel's `send(q)`, so a spoken turn is the same turn as a typed one.

In the order a question meets them: `open_voice` (sign-in, the microphone's state), `listen` (the door in: PCM and
the panel's control frames), `vad_stream` (an utterance out of the audio, lifted from the callbot), `STTOp` (in
`_stt.py`), `heard` (a caption), `turn_taking` (the question, once the person has been quiet `VOICE_SILENCE_MS`),
and `speak` (one WAV per sentence of the answer). The doors are the only ops that touch `current_session()`.
"""

from __future__ import annotations

import asyncio
import base64
import os
import time
from typing import Optional
from urllib.parse import urlsplit

from operonx.app.serve import current_session
from operonx.core import SCRATCH
from operonx.core.loggings import LOGGER
from operonx.core.ops import op
from operonx.core.registry import ResourceHub

from voice import _endpoints  # noqa: F401 — registers the `http:` resource category
from voice import _vad  # noqa: F401 — registers `audio_worker:`
from voice._session import END_OF_TURN, Voice
from voice._tts import synthesize
from voice._wav import speech_media

# How long the person is quiet before the question is asked (V-D3): the brief's 1 s, plus 200 ms for older
# speakers' pauses inside a sentence.
SILENCE_MS = int(os.environ.get("VOICE_SILENCE_MS") or 1200)
_POLL_S = 0.05
# The voice the answer is read in: the callbot's (speaker 4, style 1), at speed 1.0 (V-D5).
SPEAKER_ID = int(os.environ.get("VOICE_SPEAKER_ID") or 4)
STYLE_ID = int(os.environ.get("VOICE_STYLE_ID") or 1)
SPEED = float(os.environ.get("VOICE_SPEED") or 1.0)


class Refused(PermissionError):
    http_status = 403


def _same_origin(headers: dict) -> bool:
    """A browser always sends Origin on a websocket; it must be this server's own page (a script on another site
    could otherwise open the microphone door with the person's cookie)."""
    origin = headers.get("origin")
    if not origin:
        return True  # not a browser (a script with the cookie already has the person's session)
    return urlsplit(origin).netloc == (headers.get("x-forwarded-host") or headers.get("host") or "")


@op
def open_voice(rate: int = 48000) -> dict:
    """Mở micro: kiểm tra đăng nhập và nguồn trang, dựng bộ nghe (VAD) theo tần số của trình duyệt.

    The person must be signed in (V-D7); the socket is refused otherwise and the run ends before any audio is
    read. `rate` is the browser's own (V-D2): VAD's soxr resamples it to 16 kHz.
    """
    from people import auth

    session = current_session()
    headers = dict((getattr(session, "meta", None) or {}).get("headers") or {})
    if not _same_origin(headers):
        raise Refused("Trang mở micro không phải trang của OneWealth")
    viewer = auth.signed_in()
    if auth.checking() and viewer is None:
        raise Refused("Cần đăng nhập để nói chuyện với trợ lý")
    if not 8000 <= int(rate) <= 192000:
        raise ValueError(f"rate {rate}: not a microphone rate")
    pool = ResourceHub.instance().get("audio_worker:default")
    SCRATCH["vad_pool"] = pool
    SCRATCH["vad_state"] = pool.state(rate=int(rate))
    SCRATCH["voice"] = Voice()
    LOGGER.info(f"[voice] open rate={rate} who={(viewer or {}).get('username', '-')}")
    return {"rate": int(rate)}


@op(transient=True, door="ingress")
async def listen(voice: Optional[Voice] = None):
    """Cửa vào: âm thanh micro (khung nhị phân) đi tiếp sang VAD; lệnh của khung chat (say, drop, stop, listen)
    được xử lý ngay tại đây.

    Audio is passed on only while the assistant listens (V-D6: half duplex): from the person's question until the
    answer has been played, a stray frame cannot start another question. Ends when the socket closes, and then
    closes `voice`, which ends `turn_taking` and `speak`, so the run completes on its own.
    """
    session = current_session()
    try:
        if session is None or voice is None:
            return
        async for item in session.recv():
            if isinstance(item, (bytes, bytearray)):
                if voice.listening:
                    yield {"chunk": (bytes(item), int(time.time() * 1000))}
                continue
            if not isinstance(item, dict):
                continue
            kind = item.get("type")
            turn = int(item.get("turn") or 0)
            if kind == "say":
                voice.say(turn, str(item.get("text") or ""), end=bool(item.get("end")))
            elif kind == "drop":
                voice.drop(turn)
            elif kind == "stop":
                voice.stop()
            elif kind == "listen":
                voice.listening = True
    except Exception as exc:  # noqa: BLE001 — a disconnect is the ordinary way this ends
        LOGGER.info(f"[voice] recv ended: {type(exc).__name__}: {exc}")
    finally:
        if voice is not None:
            voice.close()


@op
async def vad_stream(chunk=None, vad_pool=None, vad_state=None, voice: Optional[Voice] = None):
    """Phát hiện giọng nói (VAD): mỗi khung âm thanh đi vào, một câu nói hoàn chỉnh đi ra.

    Lifted from the callbot (`src/call/vad/ops.py`): the DSP runs on the pool's thread, `VadState` lives in
    SCRATCH for the socket's life. Each utterance is counted as at STT until its transcript lands, so a slow STT
    reply never splits one question in two (V-D3).
    """
    if chunk is None or vad_state is None:
        return
    raw_chunk, at_ms = chunk
    segments = await vad_pool.push(vad_state, raw_chunk, at_ms)
    for segment in segments:
        if voice is not None:
            voice.at_stt += 1
        yield {"speech_audio": speech_media(segment["speech_audio"]), "turn_id": segment["turn_id"]}


@op
def heard(transcript: str = "", voice: Optional[Voice] = None):
    """Một câu nói đã thành chữ: thêm vào câu hỏi đang nghe, hiện ngay làm phụ đề."""
    if voice is not None:
        voice.at_stt = max(0, voice.at_stt - 1)
    text = (transcript or "").strip()
    if not text or voice is None:
        return
    voice.heard.append(text)
    yield {"item": {"type": "heard", "text": text}}


@op
async def turn_taking(voice: Optional[Voice] = None, vad_state=None, silence_ms: int = SILENCE_MS):
    """Lượt lời: khi người nói đã im đủ lâu (mặc định 1,2 giây), không còn đang nói dở và không còn câu nào đang
    chờ STT, câu hỏi được gửi cho khung chat.

    First says `ready` (the microphone is open). Never speaks unprompted (V-D6): no reminder, no timeout.
    """
    if voice is None or vad_state is None:
        return
    silence_ms = min(4000, max(600, int(silence_ms or SILENCE_MS)))  # the handshake's ?silence_ms=, bounded
    yield {"item": {"type": "ready", "silence_ms": silence_ms}}
    while not voice.closed.is_set():
        try:
            await asyncio.wait_for(voice.closed.wait(), timeout=_POLL_S)
        except asyncio.TimeoutError:
            pass
        if not voice.heard or voice.at_stt or vad_state.triggered:
            continue
        if time.time() * 1000 - vad_state.last_speech_ms < silence_ms:
            continue
        question, voice.heard = " ".join(voice.heard), []
        voice.listening = False
        LOGGER.info(f"[voice] asked: {question[:60]!r}")
        yield {"item": {"type": "asked", "text": question}}


@op
async def speak(voice: Optional[Voice] = None, resource: str = "tts"):
    """Đọc câu trả lời: mỗi câu một tệp âm thanh, gửi ngay khi tổng hợp xong; câu sau được tổng hợp trong lúc câu
    trước đang phát. Dừng bỏ mọi câu còn lại của lượt đó."""
    if voice is None:
        return
    ep = ResourceHub.instance().get(f"http:{resource}")
    sample_rate = int(ep.opt("sample_rate", 24000))
    while True:
        queued = await voice.speech.get()
        if queued is None:
            return
        turn, sentence = queued
        if turn <= voice.stopped:
            continue
        if sentence == END_OF_TURN:
            yield {"item": {"type": "spoken", "turn": turn}}
            continue
        t0 = time.perf_counter()
        wav, ms = await synthesize(ep, sentence, SPEAKER_ID, STYLE_ID, SPEED, sample_rate)
        if not wav or turn <= voice.stopped:
            continue
        yield {
            "item": {
                "type": "voice",
                "turn": turn,
                "text": sentence,
                "wav": base64.b64encode(wav).decode("ascii"),
                "ms": round(ms),
                "synth_ms": round((time.perf_counter() - t0) * 1000),
            }
        }
