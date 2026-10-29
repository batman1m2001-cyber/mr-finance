"""VAD: the callbot's (educa-reminder-agent staging 229ba89, ``src/call/vad/_pool.py``), lifted unchanged — the
DSP, Silero and the segment state machine — except three things: the input rate is the browser's (a setting of each
state, not the telco's 8 kHz), the pool runs threads only (one server process holds a few microphones, not a hundred
calls), and the imports. ``VadState.push(pcm_int16, t_ms)`` in, the utterances it finished out.

The callbot's notes, kept: `VadState` is a plain class with no threads, no queue and no callbacks — one per
microphone, born and buried with the run; `VadPool` runs its `push` off the event loop.
"""

from __future__ import annotations

import asyncio
import math
import os
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Any, ClassVar, Dict, List, Optional

import numpy as np
import onnxruntime as ort
import soxr
from scipy import signal

from operonx.core.loggings import LOGGER
from operonx.core.registry import REGISTRY
from operonx.core.utils.yaml_model import YamlModel

from voice._energy_trim import energy_edge_trim


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


# ── Audio preprocess filter coefficients ──
# Computed once at import. Bandpass 60Hz–4kHz on 16kHz audio.
_NYQUIST = 16000 / 2
_B_HP, _A_HP = signal.butter(4, 60 / _NYQUIST, btype="high")
_B_LP, _A_LP = signal.butter(4, 4000 / _NYQUIST, btype="low")
# What `signal.filtfilt` recomputes on every call: the filters' steady
# state (`lfilter_zi`, a small linear solve) and the pad length. Half of
# filtfilt's time on a 512-sample chunk, for constants
# (docs: Operon CCU_CAPACITY_PLAN phase 2).
_ZI_HP = signal.lfilter_zi(_B_HP, _A_HP)
_ZI_LP = signal.lfilter_zi(_B_LP, _A_LP)
_EDGE = 3 * max(len(_A_HP), len(_B_HP), len(_A_LP), len(_B_LP))


def _filtfilt(b: np.ndarray, a: np.ndarray, zi: np.ndarray, x: np.ndarray) -> np.ndarray:
    """`signal.filtfilt(b, a, x)` for a 1-D *x* (padtype "odd", the default
    pad length), with the steady state *zi* computed once. The same
    operations in the same order: the output is bit-identical."""
    n = _EDGE
    ext = np.concatenate((2 * x[0:1] - x[n:0:-1], x, 2 * x[-1:] - x[-2:-(n + 2):-1]))
    y, _ = signal.lfilter(b, a, ext, zi=zi * ext[0:1])
    y, _ = signal.lfilter(b, a, y[::-1], zi=zi * y[-1:])
    return y[::-1][n:-n]


# ── ONNX VAD session (shared, stateless) ──
_vad_session: Optional[ort.InferenceSession] = None


def _make_session_options() -> ort.SessionOptions:
    opts = ort.SessionOptions()
    opts.inter_op_num_threads = 1
    opts.intra_op_num_threads = 1
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return opts


def _get_vad_session(model_path: str = "models/silero_vad.onnx") -> ort.InferenceSession:
    global _vad_session
    if _vad_session is None:
        _vad_session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
            sess_options=_make_session_options(),
        )
    return _vad_session


class OnlineGaussianModel:
    """Online background energy model — EWMA mean/variance tracker."""

    def __init__(self, chunk_size: int = 512, rate: int = 16000, window_sec: float = 5.0):
        self.alpha = chunk_size / (rate * window_sec)
        self.mean = 0.0
        self.var = 1e-6
        self.n = 0

    def update(self, energy: float):
        self.n += 1
        if self.n == 1:
            self.mean = energy
            self.var = energy * energy * 0.1
            return
        delta = energy - self.mean
        self.mean += self.alpha * delta
        self.var = (1 - self.alpha) * self.var + self.alpha * delta * delta

    def p_background(self, energy: float) -> float:
        if self.var < 1e-10:
            return 0.5
        std = math.sqrt(self.var)
        z = (energy - self.mean) / max(std, 1e-8)
        return 1.0 / (1.0 + math.exp(min(z, 20)))


#: `_detect_speech`'s spectrum frequencies: a 256-point rfft at 16 kHz.
_RFFT_FREQS_256 = np.fft.rfftfreq(256, 1.0 / 16000)
_BANDS: Dict[int, list] = {}


def _gating_bands(n: int) -> list:
    """Spectral gating's ``(band mask, weight)`` pairs for an *n*-sample
    chunk, built once per length (always 512 in practice) instead of per
    chunk; applied in the same order as before."""
    bands = _BANDS.get(n)
    if bands is None:
        freqs = np.fft.rfftfreq(n, 1.0 / VadState.TARGET_RATE)
        bands = _BANDS[n] = [
            ((freqs >= f_low) & (freqs < f_high), weight)
            for (f_low, f_high), weight in VadState.VN_FREQ_WEIGHTS.items()
        ]
    return bands


class VadState:
    """One call's audio state, and the DSP that advances it.

    Not thread-safe and not meant to be: exactly one thread touches an
    instance at a time, because `vad_stream` awaits each `push` before
    submitting the next.

    ``push`` is the whole surface. Everything else is the pipeline it runs:
    the `AudioProcessor` half (decode, resample, frame, bandpass,
    pre-emphasis, speech detect, spectral gating, AGC) and the
    `VadDetector` half (Silero, foreground model, the segment state
    machine, prob trim, energy edge trim, the near-field gate).
    """

    # ── AudioProcessor config ──
    TELCOM_RATE = 8000
    TARGET_RATE = 16000
    CHUNK_SIZE = 512
    TARGET_RMS = 0.15
    PRE_EMPHASIS_FACTOR = 0.97
    GAIN_ATTACK = 0.2
    GAIN_RELEASE = 0.05
    GAIN_MIN = 0.1
    GAIN_MAX = 5.0
    VN_FREQ_WEIGHTS = {
        (60, 300): 1.5,
        (300, 800): 1.3,
        (1200, 2500): 1.4,
        (2500, 3500): 1.2,
    }

    # ── VadDetector config ──
    RATE = 16000
    TRIGGER_THRESHOLD = 0.5
    NEG_THRESHOLD = 0.35
    MIN_SPEECH_MS = 60
    MAX_SPEECH_MS = 45000
    MIN_SILENCE_MS = 500
    SPEECH_PAD_START_MS = 500
    #: The background model needs this long before it is trusted; until
    #: then every frame counts as foreground.
    FOREGROUND_WARMUP_S = 3.0

    def __init__(self, use_preprocess: bool = True, rate: Optional[int] = None) -> None:
        self.use_preprocess = use_preprocess
        if rate:  # the microphone's rate (OneWealth): soxr below takes it to 16 kHz
            self.TELCOM_RATE = int(rate)

        self._session = _get_vad_session()
        self._sr = np.array(self.RATE, dtype=np.int64)
        self.min_speech_samples = int(self.RATE * self.MIN_SPEECH_MS / 1000)
        self.max_speech_samples = int(self.RATE * self.MAX_SPEECH_MS / 1000)
        self.min_silence_samples = int(self.RATE * self.MIN_SILENCE_MS / 1000)
        self.pad_start_chunks = int(
            self.SPEECH_PAD_START_MS / (self.CHUNK_SIZE / self.RATE * 1000)
        )

        # ── Energy edge trim (RMS-based, bổ sung prob-trim trong _trim_buffer) ──
        # Bật/tắt per-stack qua env, không sửa code.
        self.use_energy_trim = _env_bool("VAD_ENERGY_TRIM", True)
        self.energy_trim_ratio = float(os.getenv("VAD_ENERGY_TRIM_RATIO", "0.25"))
        self.energy_trim_percentile = float(os.getenv("VAD_ENERGY_TRIM_PERCENTILE", "95.0"))
        self.energy_edge_buffer_ms = float(os.getenv("VAD_ENERGY_EDGE_BUFFER_MS", "300.0"))
        self.energy_trim_window_ms = float(os.getenv("VAD_ENERGY_TRIM_WINDOW_MS", "50.0"))
        self.energy_min_keep_ms = float(os.getenv("VAD_ENERGY_MIN_KEEP_MS", "100.0"))

        # ── Near-field RMS filter (incremental, lọc giọng far-field trước STT) ──
        self.use_near_field = _env_bool("VAD_NEAR_FIELD", True)
        self.near_field_ratio = float(os.getenv("VAD_NEAR_FIELD_RATIO", "0.30"))
        self.near_field_min_turns = int(os.getenv("VAD_NEAR_FIELD_MIN_TURNS", "5"))
        self.near_field_window = int(os.getenv("VAD_NEAR_FIELD_WINDOW", "20"))

        # ── Resample + framing (AudioProcessor) ──
        self.resampler = (
            soxr.ResampleStream(
                self.TELCOM_RATE, self.TARGET_RATE, 1,
                dtype=np.float32, quality="VHQ",
            )
            if self.TELCOM_RATE != self.TARGET_RATE
            else None
        )
        self.buffer: deque = deque()
        self.buffer_len = 0

        # ── Preprocess (AudioProcessor) ──
        self.noise_profile: Optional[np.ndarray] = None
        self.noise_samples: List[np.ndarray] = []
        self.rms_buffer: deque = deque(maxlen=50)
        self.energy_buffer: deque = deque(maxlen=50)
        self.current_gain = 1.0
        self.is_speech = False
        self.speech_frames = 0
        self.silence_frames = 0

        # ── VAD state machine (VadDetector) ──
        self.vad_state = np.zeros((2, 1, 128), dtype=np.float32)
        self.vad_context = np.zeros((1, 64), dtype=np.float32)
        self.triggered = False
        self.temp_end = 0
        self.current_sample = 0
        self.speech_buffer: deque = deque()
        self.temp_buffer: deque = deque(maxlen=self.pad_start_chunks)
        self.possible_ends: List[tuple] = []
        self.bg_model = OnlineGaussianModel(self.CHUNK_SIZE, self.RATE)
        self.start_time = time.time()
        self.current_turn_id = 0
        # RMS pre-AGC của các segment ĐÃ giữ gần nhất — reference near-field.
        self.cus_turn_rms: deque = deque(maxlen=self.near_field_window)

        # ── What the loop side reads back ──
        # `VadDetector` used to nudge `coordinator.last_speech_ms` straight
        # from the audio path on every high-confidence Silero frame, so a
        # long utterance could not trip the silence prompt while the VAD was
        # still buffering it. It lives here now and `vad_stream` copies it
        # onto the call's clock, so nothing off the loop touches the clock.
        self.last_speech_ms = int(time.time() * 1000)
        #: The telco's stamp on the last packet that carried speech: when
        #: the caller last spoke, on the caller's clock. A reply is
        #: measured from it (`play_frame`), so VAD lag counts.
        self.last_voice_cmc = 0
        #: Monotonic segment id, claimed at TRIGGERED.
        self.turn_seq = 0
        #: The worst lag of the call: how long after the telco stamped a
        #: packet VAD started on it. Past ~0.5 s the call is behind real
        #: time (a saturated VAD thread); `end_call` reports it.
        self.lag_max_ms = 0.0

    # ── The only public method ────────────────────────────────────────

    def push(self, raw_chunk: bytes, cmc_time: int) -> List[Dict[str, Any]]:
        """One telco packet in; the utterances it completed out.

        Runs on a pool thread. Returns a list because a packet can carry
        more than one 512-sample VAD frame — in practice the list is empty
        for all but ~3 packets a call.
        """
        segments: List[Dict[str, Any]] = []
        lag = time.time() * 1000 - cmc_time
        if lag > self.lag_max_ms:
            self.lag_max_ms = lag

        # 1. Decode PCM int16 → float32 [-1, 1]
        samples = np.frombuffer(raw_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        if samples.ndim != 1:
            samples = samples.ravel()

        # 2. Resample
        if self.resampler is not None:
            samples = self.resampler.resample_chunk(samples)
            if len(samples) == 0:
                return segments

        # 3. Buffer
        self.buffer.append(samples)
        self.buffer_len += len(samples)

        # 4. Extract + process chunks
        while self.buffer_len >= self.CHUNK_SIZE:
            chunk = self._extract_chunk()
            if self.use_preprocess:
                chunk, raw_rms = self._preprocess(chunk)
            else:
                # No AGC applied -> chunk level IS the raw level.
                raw_rms = float(np.sqrt(np.mean(np.square(chunk))))
            segment = self._process_vad_chunk(chunk, cmc_time, raw_rms)
            if segment is not None:
                segments.append(segment)
        return segments

    # ── Framing ───────────────────────────────────────────────────────

    def _extract_chunk(self) -> np.ndarray:
        collected = []
        remaining = self.CHUNK_SIZE
        while remaining > 0:
            front = self.buffer[0]
            if len(front) <= remaining:
                collected.append(self.buffer.popleft())
                remaining -= len(front)
                self.buffer_len -= len(front)
            else:
                collected.append(front[:remaining])
                self.buffer[0] = front[remaining:]
                self.buffer_len -= remaining
                remaining = 0
        return np.concatenate(collected) if len(collected) > 1 else collected[0]

    # ── Conformer preprocess (AudioProcessor) ─────────────────────────

    def _preprocess(self, chunk: np.ndarray) -> tuple[np.ndarray, float]:
        """Bandpass → pre-emphasis → speech detect → spectral gating → adaptive gain.

        Trả (chunk_sau_gain, raw_rms) — raw_rms đo NGAY TRƯỚC adaptive gain
        (post bandpass/gating, pre AGC), là mức tham chiếu đúng cho near-field:
        cả near lẫn far đều qua cùng bandpass/gating, chỉ AGC mới nén khoảng cách.
        """
        chunk = _filtfilt(_B_HP, _A_HP, _ZI_HP, chunk).astype(np.float32)
        chunk = _filtfilt(_B_LP, _A_LP, _ZI_LP, chunk).astype(np.float32)
        chunk = signal.lfilter([1, -self.PRE_EMPHASIS_FACTOR], [1], chunk).astype(np.float32)

        is_speech = self._detect_speech(chunk)
        if not is_speech:
            self._update_noise_profile(chunk)
        if len(self.noise_samples) > 5:
            chunk = self._apply_spectral_gating(chunk)

        raw_rms = float(np.sqrt(np.mean(np.square(chunk))))
        chunk = self._normalize_volume(chunk, is_speech)
        return chunk, raw_rms

    def _detect_speech(self, chunk: np.ndarray) -> bool:
        energy = float(np.mean(chunk ** 2))
        self.energy_buffer.append(energy)
        if len(self.energy_buffer) > 5:
            sorted_e = sorted(self.energy_buffer)
            bg_energy = sorted_e[max(0, len(sorted_e) // 10)]
        else:
            bg_energy = 0.001
        zcr = float(np.sum(np.abs(np.diff(np.signbit(chunk))))) / len(chunk)
        if len(chunk) >= 256:
            fft_mag = np.abs(np.fft.rfft(chunk[:256]))
            freqs = _RFFT_FREQS_256
            total = np.sum(fft_mag)
            centroid = float(np.sum(freqs * fft_mag) / total) if total > 0 else 0
        else:
            centroid = 1000
        is_speech_frame = (
            energy > bg_energy * 3
            and 0.05 < zcr < 0.3
            and 500 < centroid < 4000
        )
        if is_speech_frame:
            self.speech_frames += 1
            self.silence_frames = 0
        else:
            self.silence_frames += 1
            if self.silence_frames > 10:
                self.speech_frames = 0
        self.is_speech = self.speech_frames > 3
        return self.is_speech

    def _update_noise_profile(self, chunk: np.ndarray) -> None:
        fft_mag = np.abs(np.fft.rfft(chunk))
        if self.noise_profile is None:
            self.noise_profile = fft_mag.copy()
        self.noise_samples.append(fft_mag)
        if len(self.noise_samples) > 30:
            self.noise_samples.pop(0)

    def _apply_spectral_gating(self, chunk: np.ndarray) -> np.ndarray:
        if not self.noise_samples:
            return chunk
        fft = np.fft.rfft(chunk)
        magnitude = np.abs(fft)
        phase = np.angle(fft)
        noise_mag = np.mean(self.noise_samples[-10:], axis=0)
        threshold = noise_mag * 1.5
        for band, weight in _gating_bands(len(chunk)):
            threshold[band] /= weight
        mask = (magnitude > threshold).astype(np.float32)
        mask = np.convolve(mask, np.ones(5) / 5, mode="same")
        mask = np.maximum(mask, 0.1)
        cleaned = magnitude * mask * np.exp(1j * phase)
        return np.fft.irfft(cleaned, n=len(chunk)).astype(np.float32)

    def _normalize_volume(self, chunk: np.ndarray, is_speech: bool) -> np.ndarray:
        rms = float(np.sqrt(np.mean(np.square(chunk))))
        self.rms_buffer.append(rms)
        target_gain = (self.TARGET_RMS if is_speech else self.TARGET_RMS * 0.7) / max(rms, 0.001)
        target_gain = max(self.GAIN_MIN, min(target_gain, self.GAIN_MAX))
        if target_gain > self.current_gain:
            self.current_gain += self.GAIN_ATTACK * (target_gain - self.current_gain)
        else:
            self.current_gain += self.GAIN_RELEASE * (target_gain - self.current_gain)
        chunk = chunk * self.current_gain
        if np.max(np.abs(chunk)) > 0.95:
            chunk = np.tanh(chunk) * 0.95
        return chunk.astype(np.float32)

    # ── VAD state machine (VadDetector) ──────────────────────────────

    def _process_vad_chunk(
        self,
        audio: np.ndarray,
        cmc_time: int,
        raw_rms: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        # ── ONNX Inference ──
        input_with_ctx = np.concatenate(
            [self.vad_context, audio.reshape(1, -1)], axis=1
        )
        ort_outs = self._session.run(
            ["output", "stateN"],
            {
                "input": input_with_ctx.astype(np.float32),
                "state": self.vad_state,
                "sr": self._sr,
            },
        )
        speech_prob = float(ort_outs[0][0][0])
        self.vad_state = ort_outs[1]
        self.vad_context = input_with_ctx[:, -64:]

        # Nudge the silence-prompt timer on every high-confidence speech
        # frame (not just at segment yield). Prevents silence from firing
        # mid-utterance while VAD is still buffering speech.
        if speech_prob >= self.TRIGGER_THRESHOLD:
            self.last_speech_ms = int(time.time() * 1000)
            self.last_voice_cmc = cmc_time

        # ── Foreground detection ──
        energy = float(np.sqrt(np.mean(audio ** 2)))
        self.bg_model.update(energy)
        elapsed = time.time() - self.start_time
        if elapsed < self.FOREGROUND_WARMUP_S:
            is_foreground = True
        else:
            p_bg = self.bg_model.p_background(energy)
            is_foreground = p_bg < 0.2

        # ── State machine ──
        self.current_sample += self.CHUNK_SIZE

        if not self.triggered:
            self.temp_buffer.append((audio, speech_prob, cmc_time, raw_rms))
            if speech_prob >= self.TRIGGER_THRESHOLD and is_foreground:
                self.triggered = True
                self.temp_end = 0
                self.possible_ends = []
                for item in self.temp_buffer:
                    self.speech_buffer.append(item)
                self.temp_buffer.clear()
                self.turn_seq += 1
                self.current_turn_id = self.turn_seq
        else:
            self.speech_buffer.append((audio, speech_prob, cmc_time, raw_rms))

            if speech_prob < self.NEG_THRESHOLD:
                if self.temp_end == 0:
                    self.temp_end = self.current_sample
                silence_samples = self.current_sample - self.temp_end
                if silence_samples >= self.min_silence_samples:
                    segment = self._finalize_segment()
                    if segment is not None:
                        _silence_ms = silence_samples / self.RATE * 1000
                        LOGGER.info(
                            f"PERF vad_yield t={time.time():.3f} cmc={segment['cmc_start_time']} "
                            f"speech={segment['speech_duration_ms']:.0f}ms silence_wait={_silence_ms:.0f}ms"
                        )
                    return segment
            else:
                if self.temp_end > 0:
                    silence_ms = (self.current_sample - self.temp_end) / self.RATE * 1000
                    self.possible_ends.append((self.temp_end, silence_ms))
                    self.temp_end = 0

            speech_samples = len(self.speech_buffer) * self.CHUNK_SIZE
            if speech_samples >= self.max_speech_samples:
                return self._force_end_segment()

        return None

    def _postprocess_segment(self, trimmed: list):
        """Energy edge-trim + near-field RMS gate trên chuỗi chunk đã prob-trim.

        Trả (audio, cmc_start) nếu GIỮ segment, hoặc None nếu:
          - sau energy-trim ngắn hơn min_speech (degenerate), hoặc
          - bị near-field drop (giọng far-field yếu hơn reference giọng khách).
        Chỉ khi GIỮ mới góp seg_rms vào reference cus_turn_rms (đúng tinh thần
        bản batch: reference dựng từ các đoạn ĐÃ chọn).
        """
        if not trimmed:
            return None
        audio = np.concatenate([item[0] for item in trimmed])
        cmc_start = trimmed[0][2]

        # ── Energy edge trim (bổ sung prob-trim; cắt mép RMS thấp mà prob vẫn cao) ──
        if self.use_energy_trim:
            audio, n_head, n_tail = energy_edge_trim(
                audio, self.RATE,
                window_ms=self.energy_trim_window_ms,
                ratio=self.energy_trim_ratio,
                percentile=self.energy_trim_percentile,
                edge_buffer_ms=self.energy_edge_buffer_ms,
                min_keep_ms=self.energy_min_keep_ms,
            )
            if len(audio) < self.min_speech_samples:
                return None
            if n_head or n_tail:
                # Bù timestamp: cắt n_head sample đầu -> lời khách bắt đầu muộn hơn.
                cmc_start += int(n_head / self.RATE * 1000)
                LOGGER.info(
                    "[vad] energy_trim head=%.0fms tail=%.0fms kept=%.0fms",
                    n_head / self.RATE * 1000, n_tail / self.RATE * 1000,
                    len(audio) / self.RATE * 1000,
                )

        # ── seg_rms PRE-AGC từ raw_rms các chunk giữ lại (né AGC nén near/far) ──
        raw = [item[3] for item in trimmed if len(item) > 3 and item[3]]
        seg_rms = float(np.sqrt(np.mean(np.square(raw)))) if raw else 0.0

        # ── Near-field filter: kích hoạt từ lượt (min_turns+1); trước đó fail-open ──
        if self.use_near_field and len(self.cus_turn_rms) >= self.near_field_min_turns:
            ref = float(np.percentile(self.cus_turn_rms, 80))  # p80, KHÔNG median
            if seg_rms < self.near_field_ratio * ref:
                LOGGER.info(
                    "[vad] near_field_drop seg_rms=%.5f ref_p80=%.5f ratio=%.2f",
                    seg_rms, ref, self.near_field_ratio,
                )
                return None

        self.cus_turn_rms.append(seg_rms)
        return audio, cmc_start

    def _segment(self, audio: np.ndarray, cmc_start: int, n_chunks: int) -> Dict[str, Any]:
        return {
            "speech_audio": audio,
            "speech_duration_ms": len(audio) / self.RATE * 1000,
            "num_chunks": n_chunks,
            "cmc_start_time": cmc_start,
            "vad_time": int(time.time() * 1000),
            "turn_id": self.current_turn_id,
        }

    def _finalize_segment(self) -> Optional[Dict[str, Any]]:
        if not self.speech_buffer:
            self._reset_buffers()
            return None
        trimmed = self._trim_buffer(self.speech_buffer)
        total_samples = sum(len(item[0]) for item in trimmed)
        if total_samples < self.min_speech_samples:
            self._reset_buffers()
            return None
        post = self._postprocess_segment(trimmed)
        if post is None:
            self._reset_buffers()
            return None
        audio, cmc_start = post
        result = self._segment(audio, cmc_start, len(trimmed))
        self._reset_buffers()
        return result

    def _force_end_segment(self) -> Optional[Dict[str, Any]]:
        best_end = None
        best_silence = 0
        for sample_idx, silence_ms in self.possible_ends:
            if silence_ms >= 98 and silence_ms > best_silence:
                best_silence = silence_ms
                best_end = sample_idx

        if best_end is not None:
            cut_chunks = (
                best_end - (self.current_sample - len(self.speech_buffer) * self.CHUNK_SIZE)
            ) // self.CHUNK_SIZE
            cut_chunks = max(1, min(cut_chunks, len(self.speech_buffer)))
            cut_buffer = deque(list(self.speech_buffer)[:cut_chunks])
            remaining = deque(list(self.speech_buffer)[cut_chunks:])

            trimmed = self._trim_buffer(cut_buffer)
            if not trimmed:
                self._reset_buffers()
                return None

            # Đẩy state qua phần đã cắt TRƯỚC (kể cả khi near-field drop) để phần
            # `remaining` của utterance đang nói tiếp tục stream, không mất.
            self.speech_buffer = remaining
            self.possible_ends = []
            self.temp_end = 0

            post = self._postprocess_segment(trimmed)
            if post is None:
                return None  # drop chunk cưỡng bức này; vẫn giữ `remaining`
            audio, cmc_start = post
            return self._segment(audio, cmc_start, len(trimmed))
        return self._finalize_segment()

    def _trim_buffer(self, buffer: deque) -> list:
        items = list(buffer)
        if not items:
            return items
        start = 0
        for i, item in enumerate(items):
            if item[1] >= 0.25:
                start = max(0, i - 3)
                break
        end = len(items)
        for i in range(len(items) - 1, -1, -1):
            if items[i][1] >= 0.25:
                end = min(len(items), i + 5)
                break
        return items[start:end]

    def _reset_buffers(self) -> None:
        """Reset state machine fields. Keeps ONNX state + background model."""
        self.triggered = False
        self.temp_end = 0
        self.possible_ends = []
        self.speech_buffer.clear()
        self.temp_buffer.clear()


# ── The one thing every call shares ───────────────────────────────────


class VadPool:
    """Where `VadState.push` runs, and nothing else: N threads in this process. Each push gives the GIL up and takes
    it back several times, behind the event loop; one worker holds ~12 callbot calls this way."""

    __slots__ = ("n_workers", "inbound_maxsize", "use_preprocess", "vad_model", "executor")

    def __init__(
        self,
        n_workers: int = 1,
        inbound_maxsize: int = 4000,
        use_preprocess: bool = True,
        vad_model: str = "models/silero_vad.onnx",
    ) -> None:
        self.n_workers = max(1, n_workers)
        self.inbound_maxsize = inbound_maxsize
        self.use_preprocess = use_preprocess
        self.vad_model = vad_model
        self.executor = ThreadPoolExecutor(max_workers=self.n_workers, thread_name_prefix="vad")
        LOGGER.info(f"[vad] pool ready n_workers={self.n_workers}")

    def state(self, rate: Optional[int] = None) -> VadState:
        """A fresh per-microphone state carrying this pool's settings; ``rate`` is the microphone's."""
        _get_vad_session(self.vad_model)  # loaded once, on the first microphone, not at every server start
        return VadState(use_preprocess=self.use_preprocess, rate=rate)

    async def push(self, state: VadState, raw_chunk: bytes, cmc_time: int) -> List[Dict[str, Any]]:
        """`state.push(raw_chunk, cmc_time)`, off the event loop."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, state.push, raw_chunk, cmc_time)


class VadPoolConfig(YamlModel):
    """YAML-configurable :class:`VadPool`, declared as ``audio_worker:``."""

    _category: ClassVar[str] = "audio_worker"

    n_workers: int = 1
    inbound_maxsize: int = 4000
    use_preprocess: bool = True
    #: The Silero VAD model the pool loads.
    vad_model: str = "models/silero_vad.onnx"


def _create_vad_pool(cfg: VadPoolConfig) -> VadPool:
    return VadPool(
        n_workers=cfg.n_workers,
        inbound_maxsize=cfg.inbound_maxsize,
        use_preprocess=cfg.use_preprocess,
        vad_model=cfg.vad_model,
    )


REGISTRY.register(VadPoolConfig, _create_vad_pool)
