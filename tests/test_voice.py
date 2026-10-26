"""Talking to the assistant (docs/VOICE_PLAN.md): the answer cut into sentences to speak, one microphone's state, and
the voice door (WS /api/assistant/voice) — a recorded question streamed in real time through the real VAD is heard,
then asked once the person is quiet; the answer's words come back as one WAV per sentence. STT and TTS are faked
offline; the last test calls the real services when their keys are set."""

import base64
import io
import os
import threading
import time
import wave
from pathlib import Path

import pytest
from operonx.app import Application
from starlette.testclient import TestClient

from voice import ops
from voice._session import Voice
from voice._stt import STTOp
from voice._text import Sentences

QUESTION = Path(__file__).parent / "data" / "voice_question.wav"  # "Tổng tài sản của tôi hiện nay là bao nhiêu?" (TTS)


def said(*deltas):
    cut = Sentences()
    out = [s for d in deltas for s in cut.feed(d)]
    return out + cut.flush()


def test_sentences_end_at_a_mark_with_a_space_after_it_never_inside_a_number_or_a_date():
    assert said("Tổng tài sản là 7,", "54 tỷ đồng. Cổ phiếu chiếm 7.5% từ 09/10/2026! Còn gì nữa", " không?") == [
        "Tổng tài sản là 7,54 tỷ đồng.", "Cổ phiếu chiếm 7.5% từ 09/10/2026!", "Còn gì nữa không?"
    ]


def test_markdown_is_read_as_prose():
    text = "## Tóm tắt\n- **Tiền gửi**: 2 tỷ\n| Loại | Giá trị |\n|---|---|\n| Vàng | 1 tỷ |\nXem [chi tiết](#/x) nhé"
    assert said(text[:9], text[9:]) == ["Tóm tắt", "Tiền gửi:", "2 tỷ", "Loại, Giá trị", "Vàng, 1 tỷ", "Xem chi tiết nhé"]


def test_a_stopped_answer_is_not_spoken_and_the_microphone_listens_again():
    v = Voice()
    v.say(1, "Câu một. Câu hai")
    v.listening = False
    v.stop()
    v.say(1, " vẫn nói.", end=True)  # the rest of a stopped turn: dropped
    v.say(2, "Lượt mới.", end=True)
    queued = [v.speech.get_nowait() for _ in range(v.speech.qsize())]
    assert queued == [(1, "Câu một."), (2, "Lượt mới."), (2, "")] and v.listening


@pytest.fixture
def fake_speech(monkeypatch):
    """STT answers with the words whatever it hears (and keeps how long each utterance was); TTS answers with 0.1 s of
    silence per sentence."""
    heard_ms = []

    async def stt(self, speech_audio):
        heard_ms.append(len(getattr(speech_audio, "data", speech_audio)) / 2 / 16)  # 16 kHz int16
        yield {"transcript": "Tổng tài sản của tôi hiện nay là bao nhiêu", "embedding": None}

    async def tts(ep, text, speaker_id, style_id, speed, sample_rate):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1), w.setsampwidth(2), w.setframerate(sample_rate), w.writeframes(b"\0" * (sample_rate // 5))
        return buf.getvalue(), 100.0

    monkeypatch.setattr(STTOp, "_process", stt)
    monkeypatch.setattr(ops, "synthesize", tts)
    return heard_ms


def stream_question(ws, rate, pcm):
    """The recording at its own pace in 20 ms frames, then 1 s of quiet; the door's frames meanwhile."""
    got, step, t0 = [], rate // 50 * 2, time.time()

    def reader():
        while True:
            m = ws.receive_json()
            got.append((time.time() - t0, m))
            if m["type"] == "asked":
                return

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    audio = pcm + b"\0" * (rate * 2)
    for i in range(0, len(audio), step):
        ws.send_bytes(audio[i : i + step])
        time.sleep(max(0.0, t0 + (i + step) / 2 / rate - time.time()))
    th.join(10)
    return got, len(pcm) / 2 / rate


def test_a_spoken_question_is_heard_asked_after_the_quiet_and_its_answer_read_sentence_by_sentence(fake_speech):
    with wave.open(str(QUESTION)) as w:
        rate, pcm = w.getframerate(), w.readframes(w.getnframes())
    with TestClient(Application.find(".").asgi()) as c, c.websocket_connect(f"/api/assistant/voice?rate={rate}") as ws:
        assert ws.receive_json() == {"type": "ready", "silence_ms": 1200}
        got, spoken_s = stream_question(ws, rate, pcm)
        kinds = [m["type"] for _, m in got]
        assert kinds == ["heard", "asked"], got
        asked_at = got[-1][0]
        assert spoken_s + 1.0 < asked_at < spoken_s + 2.5, (spoken_s, got)  # after the quiet, not inside it
        assert len(fake_speech) == 1 and fake_speech[0] > 2000  # one utterance, the whole question
        ws.send_bytes(pcm[:9600])  # while the answer is pending the microphone is shut: nothing is heard
        ws.send_json({"type": "say", "turn": 1, "text": "Tổng tài sản là 7,54 tỷ. Cổ phiếu"})
        ws.send_json({"type": "say", "turn": 1, "text": " chiếm 54%.", "end": True})
        frames = [ws.receive_json() for _ in range(3)]
    assert [(f["type"], f.get("text")) for f in frames] == [
        ("voice", "Tổng tài sản là 7,54 tỷ."), ("voice", "Cổ phiếu chiếm 54%."), ("spoken", None)
    ]
    with wave.open(io.BytesIO(base64.b64decode(frames[0]["wav"]))) as w:
        assert (w.getframerate(), w.getnchannels()) == (24000, 1)


def refused(**headers):
    """The run ends before any audio is read: an error, then the socket closes."""
    with TestClient(Application.find(".").asgi()) as c, c.websocket_connect("/api/assistant/voice", headers=headers) as ws:
        first, then = ws.receive(), ws.receive()
    return "error" in first.get("text", "") and then["type"] == "websocket.close"


def test_a_page_on_another_site_cannot_open_the_microphone(fake_speech):
    assert refused(origin="https://evil.example")


def test_signed_out_the_microphone_stays_shut(fake_speech, monkeypatch):
    monkeypatch.setenv("MF_AUTH", "on")
    assert refused()


@pytest.mark.skipif(not (os.environ.get("STT_API_KEY") and os.environ.get("TTS_API_KEY")), reason="the speech services")
def test_the_real_services_hear_what_the_real_voice_said():
    """The door speaks the question (TTS), the WAV goes back in as the microphone (VAD → STT): the same words."""
    with TestClient(Application.find(".").asgi()) as c, c.websocket_connect("/api/assistant/voice?rate=24000") as ws:
        ws.receive_json()
        ws.send_json({"type": "say", "turn": 0, "text": "Tổng tài sản của tôi hiện nay là bao nhiêu?", "end": True})
        voice = ws.receive_json()
        assert ws.receive_json()["type"] == "spoken"
        with wave.open(io.BytesIO(base64.b64decode(voice["wav"]))) as w:
            got, _ = stream_question(ws, w.getframerate(), w.readframes(w.getnframes()))
    assert got[-1][1]["text"].lower().rstrip("?") == "tổng tài sản của tôi hiện nay là bao nhiêu"
