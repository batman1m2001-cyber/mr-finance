"""The challenger's rule checks (BRD FR-303, §8): findings by severity, on the view as it stands.

They always run, in mock and live mode alike; in live mode the challenger model's own findings are
added to them (views.agents). A critical finding blocks approval until the CIO answers it
(views.decide). Rules here only read the view and its event — never client data.
"""

from __future__ import annotations

from typing import Any, Dict, List

SEVERITY_LABEL = {"critical": "Nghiêm trọng", "medium": "Trung bình", "low": "Thấp"}


def _f(code: str, severity: str, title: str, detail: str, target: str = "") -> Dict[str, Any]:
    return {"id": code, "severity": severity, "title": title, "detail": detail, "target": target, "source": "rule"}


def findings(view: Dict[str, Any], event: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    branches = view["scenarios"]["branches"]
    stressed = [b for b in branches if b["regime"] == "stressed"]
    if not stressed:
        out.append(
            _f(
                "R1",
                "medium",
                "Không có nhánh căng thẳng",
                "Bộ kịch bản không có nhánh chế độ căng thẳng; dải xấu có thể bị đánh giá thấp.",
                "scenarios",
            )
        )
    for b in stressed:
        core = {s["factor"] for s in b["core_shocks"]}
        missing = [f for f in ("VNINDEX", "RE_SPREAD") if f not in core]
        if missing:
            out.append(
                _f(
                    f"R2-{b['id']}",
                    "critical",
                    "Nhánh căng thẳng thiếu cú sốc lõi bắt buộc",
                    f"Nhánh “{b['name']}” cần {', '.join(missing)} trong cú sốc lõi (bài học kiểm chứng 2022: "
                    "để máy tự suy ra thì chỉ bắt được khoảng 63% mức giảm VN-Index).",
                    b["id"],
                )
            )
    top = max(branches, key=lambda b: b["probability"])
    if top["probability"] >= 0.8:
        out.append(
            _f(
                "R3",
                "medium",
                "Xác suất dồn vào một nhánh",
                f"Nhánh “{top['name']}” chiếm {top['probability']:.0%}; các nhánh còn lại gần như không đóng góp.",
                top["id"],
            )
        )
    dirs: Dict[str, set] = {}
    for b in branches:
        for s in b["core_shocks"]:
            dirs.setdefault(s["factor"], set()).add(s["direction"])
    main = branches[0]["core_shocks"][0]["factor"] if branches and branches[0]["core_shocks"] else None
    if main and dirs.get(main) == {branches[0]["core_shocks"][0]["direction"]} and len(branches) >= 2:
        out.append(
            _f(
                "R4",
                "medium",
                "Không có nhánh ngược chiều",
                f"Mọi nhánh cùng chiều với {main}; nên có một nhánh tin không xảy ra hoặc phản ứng ngược.",
                main,
            )
        )
    for i, r in enumerate(view.get("impacts", [])):
        if abs(r.get("level", 0)) == 3 and r.get("confidence") == "low":
            out.append(
                _f(
                    f"R5-{i}",
                    "medium",
                    "Mức tác động cực đại nhưng độ tin cậy thấp",
                    f"Dòng {r['target']} mức {r['level']:+d} với độ tin cậy thấp.",
                    f"impacts[{i}]",
                )
            )
    hinted = set()
    for it in event.get("news", []):
        hinted |= set(it.get("factors", []))
    used = set(dirs)
    missed = sorted(hinted - used)
    if missed:
        out.append(
            _f(
                "R6",
                "low",
                "Yếu tố tin nhắc tới nhưng không có trong kịch bản",
                f"Tin nguồn nhắc tới {', '.join(missed)} nhưng không nhánh nào dùng làm cú sốc lõi.",
                "scenarios",
            )
        )
    if view["scenarios"].get("priced_in") == "full":
        out.append(
            _f(
                "R7",
                "low",
                "Tin được coi là đã vào giá hết",
                "Mọi cú sốc nhân 0: lần áp dụng sẽ không đổi số nào. Kiểm tra lại nhận định này.",
                "scenarios",
            )
        )
    return out
