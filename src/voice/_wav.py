"""An utterance as 16 kHz 16-bit PCM Media and back to float32 for STT; mono int16 samples as a WAV.

Lifted from the callbot (educa-reminder-agent `src/call/stt/_wav.py`, `src/call/tts/_wav.py`, staging 229ba89).
"""

from __future__ import annotations

import struct

import numpy as np
from operonx.core.media import Media

SPEECH_RATE = 16000  # VadState resamples the browser's audio to this
_FULL_SCALE = 32767.0


def speech_media(audio: np.ndarray, sr: int = SPEECH_RATE) -> Media:
    """An utterance's float32 samples in [-1, 1] as raw PCM, declared as audio: the trace stores a playable
    `audio/L16` blob, not an `.npy`."""
    x = np.asarray(audio, dtype=np.float32).reshape(-1)
    pcm = np.round(np.clip(x, -1.0, 1.0) * _FULL_SCALE).astype("<i2")
    return Media(pcm.tobytes(), mime_type=f"audio/L16;rate={int(sr)};channels=1")


def speech_samples(audio) -> np.ndarray:
    """An utterance as 1-D float32 samples in [-1, 1], whichever way it arrives: a `Media`, its bytes (an op's
    input is unwrapped), an int16 array, or a float array."""
    if isinstance(audio, Media):
        audio = audio.data
    if audio is None:
        return np.zeros(0, dtype=np.float32)
    if isinstance(audio, (bytes, bytearray, memoryview)):
        audio = np.frombuffer(audio, dtype="<i2")
    arr = np.asarray(audio).reshape(-1)
    if arr.dtype == np.int16:
        return arr.astype(np.float32) / _FULL_SCALE
    return arr.astype(np.float32, copy=False)


def encode_wav_int16(audio: np.ndarray, sr: int) -> bytes:
    """Pack mono int16 samples into a minimal WAV with a 44-byte RIFF header."""
    data = np.ascontiguousarray(audio, dtype="<i2").tobytes()
    return (
        b"RIFF"
        + struct.pack("<I", 36 + len(data))
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16)
        + b"data"
        + struct.pack("<I", len(data))
        + data
    )
