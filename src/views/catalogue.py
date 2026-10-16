"""FR-703 agent catalogue and RULE-MEAS-04 AI quality (BRD §8, §16.3).

One entry per language-model task: purpose, owner, risk, the BRD's default model and the model configured now,
the mode a run would use now, the latest run, and open-source references. The quality figures are counted from
what is stored (views, challenges, agent runs), for the last seven days and for all time.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from control import db
from views import agents

REFS = [
    {
        "name": "TradingAgents",
        "license": "Apache-2.0",
        "use": "tham khảo kiến trúc (nhà phân tích, tranh luận, tổng hợp)",
    },
    {"name": "FinRobot", "license": "Apache-2.0", "use": "tham khảo nguyên tắc"},
    {
        "name": "operonx",
        "license": "—",
        "use": "dùng trực tiếp: đồ thị, dịch vụ, lịch (thay LangGraph của BRD, ADR-0002)",
    },
]
ENTRIES: List[Dict[str, Any]] = [
    {
        "id": "cio",
        "name": "Agent CIO",
        "purpose": "Lập nhận định có cấu trúc và 2–4 kịch bản cho một sự kiện",
        "owner": "CIO",
        "risk": "cao",
        "risk_why": "đầu vào cho quyết định đầu tư; có cổng CIO và phản biện",
        "brd_model": "Claude Opus 5.5, nỗ lực cao",
        "resource": "llm:cio",
        "reads": "tin của sự kiện, nghiên cứu đã phát hành, danh mục yếu tố — không dữ liệu khách",
        "built": True,
    },
    {
        "id": "challenger",
        "name": "Agent Phản biện",
        "purpose": "Kiểm tra nhận định trước khi duyệt, phản biện lại chỗ CIO sửa",
        "owner": "Tuân thủ (tuyến 2)",
        "risk": "trung bình",
        "risk_why": "không chặn duyệt nhưng phát hiện nghiêm trọng phải được trả lời",
        "brd_model": "Claude Sonnet 5.5 (khác Agent CIO)",
        "resource": "llm:challenger",
        "reads": "nhận định và sự kiện — không dữ liệu khách",
        "built": True,
    },
    {
        "id": "policy",
        "name": "Agent Chính sách",
        "purpose": "Tóm tắt văn bản chính sách công khai đã xác nhận nguồn, trích đúng điều khoản",
        "owner": "Tuân thủ (tuyến 2)",
        "risk": "trung bình",
        "risk_why": "không xem danh mục, không kết luận cho gia đình cụ thể",
        "brd_model": "Claude Opus 5.5, nỗ lực vừa",
        "resource": "llm:cio",
        "reads": "một văn bản chính sách đã xác nhận nguồn — không danh mục, không dữ liệu khách",
        "built": True,
    },
    {
        "id": "explain",
        "name": "Diễn giải nội bộ",
        "purpose": "Lời giải thích con số đã tính cho RM, có dấu nội bộ",
        "owner": "CIO",
        "risk": "thấp",
        "risk_why": "chỉ diễn giải, không tạo con số mới",
        "brd_model": "Claude Opus 5.5, nỗ lực thấp",
        "resource": None,
        "reads": "con số đã tính (ở đây: mẫu tất định, không gọi mô hình)",
        "built": True,
    },
    {
        "id": "copilot",
        "name": "OneWealth Copilot (bộ định tuyến)",
        "purpose": "Chọn một công cụ của ứng dụng cho câu hỏi đã che tên và số",
        "owner": "Quản trị",
        "risk": "thấp",
        "risk_why": "chỉ chọn công cụ; không đọc dữ liệu khách; ghi chỉ sau khi người dùng xác nhận (ADR-0012)",
        "brd_model": "— (ngoài BRD, bộ thiết kế lại)",
        "resource": "llm:copilot",
        "reads": "câu hỏi đã che, tên trang, danh mục công cụ",
        "built": True,
    },
]


def _latest_run(agent: str) -> Optional[Dict[str, Any]]:
    with db.tx() as con:
        row = con.execute(
            "select id, subject_id, created, data from agent_runs where agent = ? order by created desc limit 1",
            (agent,),
        ).fetchone()
    if row is None:
        return None
    data = json.loads(row["data"])
    return {
        "id": row["id"],
        "subject": row["subject_id"],
        "at": row["created"],
        "mode": data.get("mode"),
        "model": data.get("model"),
        "status": data.get("status"),
    }


def catalogue() -> Dict[str, Any]:
    from copilot import router as copilot_router

    st = agents.models()
    try:
        mode = agents.resolve_mode(None)
    except agents.AgentError:
        mode = "mock"
    now = {
        "cio": ("live", st["cio"]) if mode == "live" else ("mock", "từ khóa (mô phỏng)"),
        "challenger": ("live", st["challenger"]) if mode == "live" else ("mock", "luật R1–R7"),
        "policy": ("live", st["cio"]) if mode == "live" else ("mock", "trích câu đầu mỗi điều (mô phỏng)"),
        "explain": ("template", "mẫu tất định"),
        "copilot": ("live", copilot_router.model()) if copilot_router.live() else ("keyword", "từ khóa (mô phỏng)"),
    }
    out = []
    for e in ENTRIES:
        m, model = now[e["id"]]
        out.append(
            {
                **e,
                "mode": m,
                "model": model,
                "latest_run": _latest_run(e["id"]) if e["id"] in ("cio", "challenger", "policy") else None,
            }
        )
    return {"agents": out, "references": REFS, "prompt_version": agents.prompt_version()}


def quality(days: int = 7) -> Dict[str, Any]:
    """RULE-MEAS-04: share of decided views the CIO edited, critical findings, format retries."""
    since = time.time() - days * 86400

    def figures(t0: float) -> Dict[str, Any]:
        with db.tx() as con:
            views = [
                json.loads(r["data"]) | {"status": r["status"]}
                for r in con.execute("select status, data from views where created >= ?", (t0,))
            ]
            chals = [
                json.loads(r["data"]) for r in con.execute("select data from challenges where created >= ?", (t0,))
            ]
            runs = [json.loads(r["data"]) for r in con.execute("select data from agent_runs where created >= ?", (t0,))]
        decided = [v for v in views if v["status"] in ("APPROVED", "WITHDRAWN", "REWORK_REQUESTED", "REJECTED")]
        edited = [v for v in decided if v.get("edits")]
        findings = [f for c in chals for f in c.get("findings", [])]
        nodes = [n for r in runs for n in r.get("nodes", [])]
        return {
            "views": len(views),
            "decided": len(decided),
            "edited_share": (len(edited) / len(decided)) if decided else None,
            "findings": len(findings),
            "critical_findings": sum(1 for f in findings if f.get("severity") == "critical"),
            "agent_runs": len(runs),
            "failed_runs": sum(1 for r in runs if r.get("status") == "error"),
            "format_retries": sum(1 for n in nodes if (n.get("attempt") or 1) > 1),
        }

    return {"days": days, "recent": figures(since), "all_time": figures(0.0)}
