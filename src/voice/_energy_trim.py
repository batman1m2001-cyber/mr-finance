"""energy_trim — gọt mép năng lượng thấp của một segment audio (pure numpy).

Port trực tiếp `window_rms` + `energy_speech_bounds` từ project
call_speech_time_channel (segment_purifier.py), nhưng làm việc thẳng trên
np.ndarray mono float32 [-1, 1] thay vì (start_s, end_s) — hợp với VadDetector
vốn đã có sẵn waveform segment sau khi concat các chunk.

Bổ sung tầng gọt sẵn có của VAD (prob-trim trong `_trim_buffer` chỉ chừa
~96/160ms pad quanh vùng prob cao): energy-trim cắt được vùng mép năng lượng
thấp mà Silero prob VẪN cao (đuôi giọng nền / tiếng thở), giúp STT bớt nhiễu.

Toàn bộ là hàm thuần (chỉ numpy) -> test độc lập với waveform dựng sẵn.
"""
from __future__ import annotations

import numpy as np


def window_rms(wav: np.ndarray, sr: int, window_ms: float = 50.0
               ) -> tuple[np.ndarray, np.ndarray]:
    """RMS từng cửa sổ KHÔNG chồng lấn trên toàn `wav`.

    Trả (starts[n] chỉ số sample mốc đầu mỗi cửa sổ, rms[n]). Đoạn ngắn hơn 1
    cửa sổ -> 1 cửa sổ duy nhất = cả đoạn.
    """
    n = wav.shape[0]
    win = max(1, int(sr * window_ms / 1000.0))
    if n == 0:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.float64)
    starts = np.arange(0, n, win, dtype=np.int64)
    rms = np.empty(starts.shape[0], dtype=np.float64)
    for i, s0 in enumerate(starts):
        chunk = wav[s0:s0 + win]
        rms[i] = float(np.sqrt(np.mean(chunk.astype(np.float64) ** 2))) if chunk.size else 0.0
    return starts, rms


def energy_speech_bounds(rms: np.ndarray, ratio: float,
                         percentile: float = 95.0) -> tuple[int, int] | None:
    """Chỉ số cửa sổ speech đầu/cuối theo năng lượng: cửa sổ là speech khi
    rms >= ratio * p{percentile}(rms toàn đoạn). Trả (i_first, i_last) inclusive,
    hoặc None nếu không cửa sổ nào đạt (đoạn phẳng/im — không gọt).

    Ngưỡng TƯƠNG ĐỐI theo từng segment nên tự thích nghi mức thu âm. `percentile`
    cao (95) neo mốc vào MỨC GIỌNG KHÁCH: đoạn dài mà khách chỉ nói 1-2s thì p95
    chỉ bỏ 5% cửa sổ to nhất -> neo gần đỉnh speech, vẫn miễn nhiễm vài cửa sổ
    spike lẻ (beep/pop). Median/p75 sẽ rơi vào nền nhiễu -> gọt không sạch.
    """
    if rms.size == 0:
        return None
    thr = ratio * float(np.percentile(rms, percentile))
    idx = np.nonzero(rms >= thr)[0]
    if idx.size == 0:
        return None
    return int(idx[0]), int(idx[-1])


def energy_edge_trim(wav: np.ndarray, sr: int, window_ms: float = 50.0,
                     ratio: float = 0.25, percentile: float = 95.0,
                     edge_buffer_ms: float = 300.0, min_keep_ms: float = 100.0
                     ) -> tuple[np.ndarray, int, int]:
    """Gọt vùng năng lượng thấp ở 2 MÉP của `wav`, chừa `edge_buffer_ms` quanh
    vùng speech để không cắt sát lời nói (và không gọt sâu hơn phần pad VAD cố
    tình thêm cho STT context).

    Trả (trimmed_wav, n_head_trimmed, n_tail_trimmed) với n_* là SỐ SAMPLE đã
    cắt ở mỗi mép (0 nếu không gọt).

    Fail-safe:
      - đoạn phẳng/im (energy_speech_bounds -> None): trả nguyên gốc.
      - kết quả còn lại < min_keep_ms: trả nguyên gốc (tránh gọt quá tay).
    """
    n = wav.shape[0]
    if n == 0:
        return wav, 0, 0

    starts, rms = window_rms(wav, sr, window_ms)
    bounds = energy_speech_bounds(rms, ratio, percentile)
    if bounds is None:
        return wav, 0, 0

    i, j = bounds
    win = max(1, int(sr * window_ms / 1000.0))
    buffer = int(sr * edge_buffer_ms / 1000.0)

    speech_start = int(starts[i])
    speech_end = int(min(n, starts[j] + win))          # end của cửa sổ speech cuối

    new_start = max(0, speech_start - buffer)
    new_end = min(n, speech_end + buffer)

    if new_end - new_start < int(sr * min_keep_ms / 1000.0):
        return wav, 0, 0

    n_head = new_start
    n_tail = n - new_end
    if n_head == 0 and n_tail == 0:
        return wav, 0, 0
    return wav[new_start:new_end], n_head, n_tail
