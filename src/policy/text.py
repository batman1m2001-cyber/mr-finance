"""A policy document's text, its articles, and the check every summary passes (BRD-FR-306): each quote is the
document's own words, inside the article it names; no conclusion for a client, a family or a portfolio; no
recommendation wording.

Comparison is on the normalised text (Unicode NFC, one space for any run of white space), so a line break in the
PDF does not fail a faithful quote and nothing else is forgiven.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any, Dict, List, Tuple

# an article heading starts a line: "Điều 5. Nguyên tắc ..." (not one quoted inside an amendment: “Điều 3. ...)
_HEADING = re.compile(r"(?m)^[ \t]*Điều[ \t]+(\d+)[ \t]*\.[ \t]*([^\n]*)")
_FAMILY = re.compile(
    r"(?i)\b(quý khách|gia đình|danh mục của|khách hàng của (?:ngân hàng|chúng tôi)|nên mua|nên bán)\b"
)
MIN_QUOTE, MAX_QUOTE = 20, 400
MIN_POINTS, MAX_POINTS = 2, 6


def norm(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", str(text or "")).split())


def sha(text: str) -> str:
    """The text's fingerprint, as compared: what the verifier saw is what the quotes are checked against."""
    return hashlib.sha256(norm(text).encode("utf-8")).hexdigest()


def articles(text: str) -> List[Dict[str, Any]]:
    """The document's articles in order: label (“Điều 5”), title, and the article's span in ``norm(text)``."""
    raw = unicodedata.normalize("NFC", text or "")
    heads = [(m.start(), m.group(1), m.group(2).strip()) for m in _HEADING.finditer(raw)]
    out = []
    for k, (start, num, title) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(raw)
        out.append({"label": f"Điều {num}", "title": norm(title)[:160], "body": norm(raw[start:end])})
    return out


def _spans(text: str, label: str) -> List[str]:
    return [a["body"] for a in articles(text) if a["label"].lower() == norm(label).lower()]


def _article_label(given: Any) -> str:
    m = re.search(r"(?i)điều\s*(\d+)", str(given or ""))
    return f"Điều {m.group(1)}" if m else ""


def check(text: str, out: Any) -> Tuple[Dict[str, Any], List[str]]:
    """(the cleaned summary, findings): empty findings means it passes."""
    from views import schema

    findings: List[str] = []
    if not isinstance(out, dict):
        return {}, ["Kết quả phải là một đối tượng JSON"]
    summary = norm(out.get("summary"))
    points = out.get("points") if isinstance(out.get("points"), list) else []
    if not 20 <= len(summary) <= 800:
        findings.append("summary: 20–800 ký tự")
    if not MIN_POINTS <= len(points) <= MAX_POINTS:
        findings.append(f"points: {MIN_POINTS}–{MAX_POINTS} điểm (có {len(points)})")
    whole = norm(text)
    clean = []
    for k, p in enumerate(points[:MAX_POINTS], 1):
        p = p if isinstance(p, dict) else {}
        point, quote, label = (
            norm(p.get("point")),
            norm(p.get("quote")).strip("“”\"' "),
            _article_label(p.get("article")),
        )
        if not point:
            findings.append(f"điểm {k}: thiếu nội dung")
        if not MIN_QUOTE <= len(quote) <= MAX_QUOTE:
            findings.append(f"điểm {k}: trích dẫn {MIN_QUOTE}–{MAX_QUOTE} ký tự")
        elif quote not in whole:
            findings.append(f"điểm {k}: trích dẫn không có nguyên văn trong văn bản: “{quote[:80]}…”")
        elif not label:
            findings.append(f"điểm {k}: thiếu điều khoản (“Điều N”)")
        elif not any(quote in body for body in _spans(text, label)):
            findings.append(f"điểm {k}: trích dẫn không nằm trong {label}")
        clean.append({"point": point[:400], "article": label, "quote": quote})
    said = " ".join([summary, *(c["point"] for c in clean)])
    bad = schema.forbidden_words(said)
    if bad:
        findings.append(f"Có từ ngữ khuyến nghị: {', '.join(bad)}")
    family = sorted({m.group(1).lower() for m in _FAMILY.finditer(said)})
    if family:
        findings.append(f"Không kết luận cho khách hàng, gia đình hay danh mục ({', '.join(family)})")
    return {"summary": summary, "points": clean}, findings


def mock(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Without a model: the first sentence of each of the first articles, quoted as they stand (labelled mock)."""
    points = []
    for a in articles(doc["text"]):
        body = a["body"]
        head = re.match(r"Điều \d+\s*\.\s*", body)
        rest = body[head.end() :] if head else body
        if a["title"] and rest.startswith(a["title"]):
            rest = rest[len(a["title"]) :].strip()
        sentence = re.split(r"(?<=[.;:])\s", rest, maxsplit=1)[0].strip()
        if len(sentence) > MAX_QUOTE:
            sentence = sentence[:MAX_QUOTE].rsplit(" ", 1)[0]
        if len(sentence) >= MIN_QUOTE and sentence in norm(doc["text"]):
            points.append({"point": a["title"] or a["label"], "article": a["label"], "quote": sentence})
        if len(points) == 4:
            break
    n = len({a["label"] for a in articles(doc["text"])})  # an article quoted inside an amendment is not another one
    summary = (
        f"{doc['title']} ({doc.get('number') or 'không số'}) gồm {n} điều. Bản tóm tắt mô phỏng: trích câu đầu "
        "của các điều đầu tiên, không gọi mô hình."
    )
    return {"summary": summary, "points": points}
