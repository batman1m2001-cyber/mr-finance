"""assistant_voice_flow: one open microphone (GET /api/assistant/voice, a websocket, docs/VOICE_PLAN.md).

The browser streams PCM in and gets captions, the question, and the answer's sentences as WAVs out. The question
itself is asked by the panel (POST /api/assistant/stream with `voice: true`), which forwards the answer's words
back as `say` frames: one turn, typed or spoken, stays one code path. Three outputs, three egress ops:

    listen ─▶ vad_stream ─▶ STTOp ─▶ heard ──────▶ egress   {"type": "heard", "text"}
    turn_taking ───────────────────────────────▶ egress   {"type": "ready"} · {"type": "asked", "text"}
    speak ─────────────────────────────────────▶ egress   {"type": "voice", "turn", "text", "wav", "ms"} · spoken
"""

from operonx import END, SCRATCH, START, graph
from operonx.app.serve import egress

from voice._stt import STTOp
from voice.ops import SILENCE_MS, heard, listen, open_voice, speak, turn_taking, vad_stream


@graph
def assistant_voice_flow(rate=48000, silence_ms=SILENCE_MS):
    """Nói chuyện với trợ lý: nghe câu hỏi (VAD → STT), chờ người nói im đủ lâu, đọc từng câu trả lời (TTS)."""
    opened = open_voice(rate=rate)
    mic = listen(voice=SCRATCH["voice"])
    # At most 64 frames wait for VAD (the callbot's bound): past it `listen` stops reading the socket.
    speech = vad_stream(
        chunk=mic["chunk"].sequential(max_pending=64),
        vad_pool=SCRATCH["vad_pool"],
        vad_state=SCRATCH["vad_state"],
        voice=SCRATCH["voice"],
    )
    stt = STTOp(resource="stt", inputs={"speech_audio": speech["speech_audio"]})
    caption = heard(transcript=stt["transcript"], voice=SCRATCH["voice"])
    asks = turn_taking(voice=SCRATCH["voice"], vad_state=SCRATCH["vad_state"], silence_ms=silence_ms)
    reads = speak(voice=SCRATCH["voice"])
    say_caption = egress(item=caption["item"])
    say_turn = egress(item=asks["item"])
    say_answer = egress(item=reads["item"])

    START >> opened
    opened >> mic >> speech >> stt >> caption >> say_caption >> END
    opened >> asks >> say_turn >> END
    opened >> reads >> say_answer >> END
