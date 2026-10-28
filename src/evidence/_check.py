"""The checks a frame passes before the CIO sees it (NEWS_EVIDENCE_BRD §9). ``check`` returns the reasons to send it
back (empty: it passes) and, on the statistics branch, the frame with the computed direction kept over the agent's,
with a note for the CIO (rule 7)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from evidence import catalogue as cat

REQUIRED = ("channels", "mechanism", "targets", "direction", "changes", "timeframe", "watch")  # §6, "Có"
PARTS = (("event", "sự kiện"), ("outcome", "kết quả"), ("difference", "khác biệt bối cảnh"))  # every precedent's three
# a price forecast: a rise or fall with a percentage after it ("sẽ tăng 15%", "giảm thêm 3,5 %")
FORECAST = re.compile(r"(tăng|giảm|lên|xuống)\D{0,20}?\d+(?:[.,]\d+)?\s*(%|điểm\s*%)", re.IGNORECASE)
TEXTS = ("event_type", "mechanism", "direction", "timeframe", "watch", "title", "client_message")
LISTS = ("channels", "targets", "changes")


def shape(frame: Dict[str, Any]) -> List[str]:
    """The fields of the wrong kind (a model may answer a list where a text goes): the frame goes back on these before
    the other checks read it."""
    bad = [k for k in TEXTS if frame.get(k) is not None and not isinstance(frame[k], str)]
    bad += [k for k in LISTS if not isinstance(frame.get(k) or [], list) or not all(isinstance(x, str) for x in frame.get(k) or [])]
    ps = frame.get("precedents") or []
    if not isinstance(ps, list) or not all(isinstance(p, dict) and all(isinstance(p.get(k) or "", str) for k, _ in PARTS) for p in ps):
        bad.append("precedents")
    return bad


def client_texts(frame: Dict[str, Any]) -> List[str]:
    """What a client or an RM may read of a frame: everything but the CIO's own headline and notes."""
    out = [frame.get("title", ""), frame.get("mechanism", ""), frame.get("watch", ""), frame.get("client_message") or ""]
    for p in frame.get("precedents") or []:
        out += [p.get("event", ""), p.get("outcome", ""), p.get("difference", "")]
    return out


def check(frame: Dict[str, Any], computed: str = None) -> Tuple[List[str], Dict[str, Any]]:
    """``computed``: the direction the statistics give (rule 7). Returns (reasons, the frame as kept)."""
    from procedural import goals
    from views import schema

    bad = shape(frame)
    if bad:
        return [f"Sai kiểu dữ liệu: {', '.join(bad)} (trường văn bản là một chuỗi, danh sách là mảng chuỗi)"], dict(frame)
    why: List[str] = []
    if frame.get("event_type") not in cat.EVENT_TYPES:
        why.append(f"Loại sự kiện không có trong danh mục: {frame.get('event_type')!r}")
    bad = [t for t in frame.get("targets") or [] if not cat.valid_target(t)]
    if bad:
        why.append(f"Nhãn đối tượng không có trong danh mục: {', '.join(map(str, bad))}")
    stats = frame.get("branch") == "statistics"
    if not stats:
        missing = [k for k in REQUIRED if not frame.get(k)]
        if missing:
            why.append(f"Thiếu trường bắt buộc: {', '.join(missing)}")
        if "precedents" not in frame:
            why.append("Thiếu tiền lệ (ghi danh sách rỗng khi chưa có tiền lệ)")
    off = [c for c in frame.get("channels") or [] if c not in cat.CHANNELS]
    if off:
        why.append(f"Kênh truyền dẫn ngoài danh sách: {', '.join(off)}")
    if frame.get("direction") and frame["direction"] not in cat.DIRECTIONS:
        why.append(f"Chiều hướng không hợp lệ: {frame['direction']!r}")
    if frame.get("timeframe") and frame["timeframe"] not in cat.TIMEFRAMES:
        why.append(f"Thời gian không hợp lệ: {frame['timeframe']!r}")
    if any(c not in cat.CHANGES for c in frame.get("changes") or []):
        why.append("Cái thay đổi phải là giá, dòng tiền, chi phí, thanh khoản hoặc thủ tục")
    for i, p in enumerate(frame.get("precedents") or [], start=1):
        lack = [name for k, name in PARTS if not p.get(k)]
        if lack:
            why.append(f"Tiền lệ {i} thiếu {', '.join(lack)}")
    if not stats:
        said = [m.group(0) for t in (frame.get("mechanism"), frame.get("watch"), frame.get("client_message")) for m in FORECAST.finditer(t or "")]
        if said:
            why.append(f"Có con số dự báo giá ngoài nhánh thống kê: {', '.join(said)}")
    texts = client_texts(frame)
    words = sorted(set(goals.forbidden_words(*texts)) | {w for t in texts for w in schema.forbidden_words(t)})
    if words:
        why.append(f"Có cụm từ cấm: {', '.join(words)}")
    kept = dict(frame)
    if stats and computed and frame.get("direction") != computed:
        kept["direction"] = computed
        kept["notes"] = list(frame.get("notes") or []) + [
            f"Agent ghi {cat.DIRECTIONS.get(frame.get('direction'), frame.get('direction'))}, thống kê cho "
            f"{cat.DIRECTIONS[computed]}: giữ chiều hướng của thống kê."
        ]
    return why, kept
