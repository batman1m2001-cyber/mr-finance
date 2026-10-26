"""TTS: one sentence in, a WAV out, from ZipVoice (`http:tts`), its lead and trail silence trimmed.

Lifted from the callbot (educa-reminder-agent `src/call/tts/ops.py` `TTSOp._synth_one`, staging 229ba89). Changed:
the speed (1.0, not the server's 1.2: the brief's elderly listener, docs/VOICE_PLAN.md V-D5) and the sample rate
(`options.sample_rate`, 24 kHz: a browser plays it, not a phone line; measured as real wideband at the same
synthesis time). No text normalisation: ZipVoice reads "7,54 tỷ", "54%" and "09/10/2026" as they are.
"""

from __future__ import annotations

import io
import time
import warnings
from typing import Tuple

import numpy as np
from operonx.core.loggings import LOGGER
from scipy.io import wavfile
from scipy.io.wavfile import WavFileWarning

from voice._wav import encode_wav_int16

# ZipVoice WAVs carry 200–900 ms of leading dead air; trimmed to a short breath. 80 ms of trail keeps the decay of
# Vietnamese tone-bearing finals (the callbot measured 30 ms clipping them).
_TRIM_LEAD_KEEP_MS = 50
_TRIM_TRAIL_KEEP_MS = 80
_TRIM_THRESHOLD_FRAC = 0.02  # 2% of peak — robust to background hum


def trim_silence(audio: np.ndarray, sr: int) -> np.ndarray:
    """The samples with the lead silence cut to 50 ms and the trail to 80 ms (threshold 2% of the peak)."""
    mag = np.abs(audio.astype(np.float32))
    if mag.size == 0 or mag.max() <= 0:
        return audio
    above = np.where(mag > mag.max() * _TRIM_THRESHOLD_FRAC)[0]
    if len(above) == 0:
        return audio
    start = max(0, int(above[0]) - int(sr * _TRIM_LEAD_KEEP_MS / 1000))
    end = min(len(audio), int(above[-1]) + int(sr * _TRIM_TRAIL_KEEP_MS / 1000))
    return audio[start:end]


async def synthesize(ep, text: str, speaker_id: int, style_id: int, speed: float, sample_rate: int) -> Tuple[bytes, float]:
    """POST one sentence to ZipVoice; the trimmed WAV and its length in ms (b"", 0.0 when the service failed)."""
    payload = {
        "text": text,
        "speaker_id": speaker_id,
        "style_id": style_id,
        "response_format": "wav",
        "speed": speed,
        "sample_rate": sample_rate,
    }
    t0 = time.perf_counter()
    try:
        resp = await ep.post(payload)
    except Exception as exc:  # noqa: BLE001 — one sentence lost, not the conversation
        LOGGER.error("[tts] request failed: %s (url=%s)", exc, ep.url)
        return b"", 0.0
    # The server streams the reply and leaves the RIFF size as 0xFFFFFFFF; scipy warns but decodes it.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=WavFileWarning)
        sr, audio = wavfile.read(io.BytesIO(resp.content))
    if audio.dtype != np.int16:
        audio = audio.astype(np.int16)
    audio = trim_silence(audio, sr)
    ms = len(audio) / sr * 1000.0
    LOGGER.info(f"[tts] {(time.perf_counter() - t0) * 1000:.0f} ms synth, {ms:.0f} ms audio: {text[:30]!r}")
    return encode_wav_int16(audio, sr), ms
