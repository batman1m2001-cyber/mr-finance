"""FR-703 agent catalogue and RULE-MEAS-04 AI quality (BRD §8, §16.3); the checklist of every agent
(AGENT_CHECKLIST_PLAN.md).

One entry per part that calls a language model: its one name, purpose, owner, risk, what it reads, who checks it,
how it is measured, when it runs, the BRD's default model and the model configured now, the mode a run would use
now, the latest run; then the three evaluations with their latest result, and open-source references. The quality
figures are counted from what is stored (views, challenges, agent runs), for the last seven days and for all time.
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
#: The checklist of every part that calls a language model (AGENT_CHECKLIST_PLAN.md): one name each, used on every
#: screen; what it does, who owns it, what it reads, who checks its output, how it is measured and when it runs. The
#: first four are the BRD §8 table, in its order. ``code`` is every file that calls a model for it: a test fails when
#: a model call in ``src/`` belongs to no entry (tests/test_catalogue.py).
ENTRIES: List[Dict[str, Any]] = [
    {
        "id": "cio",
        "name": "Agent CIO",
        "name_en": "CIO agent",
        "purpose": "Lập nhận định có cấu trúc và 2–4 kịch bản cho một sự kiện",
        "owner": "CIO",
        "owner_roles": ["cio"],
        "risk": "cao",
        "risk_why": "đầu vào cho quyết định đầu tư; có cổng CIO và phản biện",
        "brd_model": "Claude Opus 5.5, nỗ lực cao",
        "resource": "llm:cio",
        "reads": "tin của sự kiện, nghiên cứu đã phát hành, danh mục yếu tố — không dữ liệu khách",
        "checks": "Agent Phản biện, rồi CIO duyệt",
        "measured": ["daily_trial", "change_gate"],
        "runs": (
            "khi CIO bấm “Chạy Agent CIO” cho một sự kiện; "
            "08:30 mỗi sáng trong thử nghiệm hằng ngày, kể cả bước gom tin"
        ),
        "code": ["src/views/agents.py", "src/trial/daily.py"],
        "built": True,
    },
    {
        "id": "challenger",
        "name": "Agent Phản biện",
        "name_en": "Challenger",
        "purpose": "Kiểm tra nhận định trước khi duyệt, phản biện lại chỗ CIO sửa",
        "owner": "CIO",
        "owner_roles": ["cio"],
        "risk": "trung bình",
        "risk_why": "không chặn duyệt nhưng phát hiện nghiêm trọng phải được trả lời",
        "brd_model": "Claude Sonnet 5.5 (khác Agent CIO)",
        "resource": "llm:challenger",
        "reads": "nhận định và sự kiện — không dữ liệu khách",
        "checks": "CIO trả lời từng phát hiện nghiêm trọng",
        "measured": ["daily_trial", "change_gate"],
        "runs": "sau mỗi bản nháp của Agent CIO, và khi CIO sửa",
        "code": ["src/views/agents.py"],
        "built": True,
    },
    {
        "id": "policy",
        "name": "Agent Chính sách",
        "name_en": "Policy agent",
        "purpose": "Tóm tắt văn bản chính sách công khai đã xác nhận nguồn, trích đúng điều khoản",
        "owner": "CIO",
        "owner_roles": ["cio"],
        "risk": "trung bình",
        "risk_why": "không xem danh mục, không kết luận cho gia đình cụ thể",
        "brd_model": "Claude Opus 5.5, nỗ lực vừa",
        "resource": "llm:cio",
        "reads": "một văn bản chính sách đã xác nhận nguồn — không danh mục, không dữ liệu khách",
        "checks": "CIO đọc bản tóm tắt; mỗi ý có câu trích từ văn bản",
        "measured": [],
        "runs": "khi CIO tóm tắt một văn bản",
        "code": ["src/policy/agent.py"],
        "built": True,
    },
    {
        "id": "explain",
        "name": "Diễn giải nội bộ",
        "name_en": "Internal explanation",
        "purpose": "Lời giải thích con số đã tính cho RM, có dấu nội bộ",
        "owner": "CIO",
        "owner_roles": ["cio"],
        "risk": "thấp",
        "risk_why": "chỉ diễn giải, không tạo con số mới",
        "brd_model": "Claude Opus 5.5, nỗ lực thấp",
        "resource": None,
        "reads": "con số đã tính (ở đây: mẫu tất định, không gọi mô hình)",
        "checks": "không gọi mô hình: mẫu cố định",
        "measured": [],
        "runs": "khi RM mở lời giải thích một con số",
        "code": [],
        "built": True,
    },
    {
        "id": "evidence",
        "name": "Agent Bằng chứng tin",
        "name_en": "News evidence agent",
        "purpose": "Đọc một tin, chọn loại sự kiện và lập khung định tính; khung chờ CIO duyệt",
        "owner": "CIO",
        "owner_roles": ["cio"],
        "risk": "trung bình",
        "risk_why": "khung chỉ thành bằng chứng khi CIO duyệt; không con số dự báo giá ngoài nhánh thống kê",
        "brd_model": "— (NEWS_EVIDENCE_BRD §4 không nêu; dùng mô hình của Agent CIO)",
        "resource": "llm:cio",
        "reads": "tiêu đề, tóm tắt, nguồn và ngày của một tin, danh mục loại sự kiện — không dữ liệu khách",
        "checks": "kiểm tra §9, trả lại agent kèm lý do tối đa hai lần; rồi CIO duyệt",
        "measured": [],
        "runs": "khi CIO bấm “Lập khung” cho một tin ở trang Bằng chứng tin",
        "code": ["src/evidence/agent.py"],
        "built": True,
    },
    {
        "id": "copilot",
        "name": "OneWealth Copilot",
        "name_en": "OneWealth Copilot (the assistant)",
        "purpose": "Trả lời mọi vai trò ở khung Trợ lý bằng công cụ của ứng dụng; việc ghi chờ người dùng xác nhận",
        "owner": "Quản trị",
        "owner_roles": ["admin"],
        "risk": "trung bình",
        "risk_why": "đọc dữ liệu người hỏi được xem qua công cụ; không tự ghi; mỗi con số lấy từ công cụ",
        "brd_model": "— (ngoài BRD, yêu cầu của chủ sản phẩm)",
        "resource": "llm:copilot",
        "reads": "câu hỏi, trang đang xem, kết quả công cụ trong quyền của người hỏi; tri thức và web với câu đã che",
        "checks": "người dùng xác nhận mỗi việc ghi; bộ kiểm tra trợ lý",
        "measured": ["assistant_set"],
        "runs": "mỗi câu hỏi ở khung Trợ lý; tóm tắt trí nhớ khi cuộc trò chuyện nghỉ (job assistant_consolidate)",
        "parts": [
            "Đặt tên và mục tiêu cho cuộc trò chuyện",
            "Tóm tắt trí nhớ từ cuộc trò chuyện đã xong (tối đa 5 mục)",
            "Tìm trên web với câu hỏi đã che",
            "Bộ định tuyến: chọn một công cụ khi không có mô hình gọi công cụ (dự phòng: từ khoá)",
        ],
        "code": [
            "src/assistant/turn.py",
            "src/assistant/sessions.py",
            "src/assistant/consolidate.py",
            "src/assistant/web.py",
            "src/copilot/router.py",
        ],
        "built": True,
    },
    {
        "id": "declare",
        "name": "Khai báo qua chat",
        "name_en": "Declaration chat",
        "purpose": "Ghi vào hồ sơ những gì khách kể mình có (đất, vàng, khoản vay, người phụ thuộc, thu nhập)",
        "owner": "Quản trị",
        "owner_roles": ["admin"],
        "risk": "trung bình",
        "risk_why": "ghi vào hồ sơ khách; cùng một điều nói lại không ghi hai lần; khi không có mô hình, luật đọc",
        "brd_model": "— (BRD-NFR-08: mô hình trong ngân hàng khi chạy thật)",
        "resource": "llm:assistant",
        "settings": ["llm:assistant", "llm:onprem"],
        "reads": "câu khách vừa nói và hồ sơ khai báo của khách",
        "checks": "khách thấy ngay điều đã ghi trong câu trả lời",
        "measured": [],
        "runs": "khi khách khai báo qua chat",
        "code": ["src/declare/graph.py", "src/declare/agent.py"],
        "built": True,
    },
    {
        "id": "statements",
        "name": "Đọc sao kê",
        "name_en": "Statement reader",
        "purpose": "Đọc sao kê khách tải lên thành các khoản nắm giữ",
        "owner": "Quản trị",
        "owner_roles": ["admin"],
        "risk": "trung bình",
        "risk_why": "đọc tài liệu của khách; chỉ mô hình trong ngân hàng khi chạy thật; khi không có mô hình, luật đọc",
        "brd_model": "— (BRD-NFR-08: mô hình trong ngân hàng khi chạy thật)",
        "resource": "llm:assistant",
        "settings": ["llm:assistant", "llm:onprem"],
        "reads": "tệp sao kê khách tải lên; ảnh và bản scan gửi cho trợ lý (ADR-0041)",
        "checks": "khách xem các khoản đọc được trước khi lưu; dòng xác nhận của trợ lý liệt kê từng khoản và tổng",
        "measured": [],
        "runs": "khi khách tải sao kê lên, hoặc gửi tệp cho trợ lý",
        "code": ["src/statements/graph.py", "src/assistant/attachments.py"],
        "built": True,
    },
    {
        "id": "newsletter",
        "name": "Viết bản tin",
        "name_en": "Newsletter writer",
        "purpose": "Chỉ viết đoạn mở đầu của bản tin, từ các nhận định đã duyệt",
        "owner": "CIO",
        "owner_roles": ["cio"],
        "risk": "thấp",
        "risk_why": "mọi bản qua bộ lọc nội dung; một CIO khác duyệt trước khi gửi",
        "brd_model": "Claude Opus 5.5 (mô hình của Agent CIO)",
        "resource": "llm:cio",
        "reads": "các mục của bản tin (nhận định đã duyệt) — không dữ liệu khách",
        "checks": "bộ lọc nội dung, rồi một CIO khác duyệt",
        "measured": [],
        "runs": "khi CIO soạn bản tin",
        "code": ["src/newsletter/compose.py"],
        "built": True,
    },
]

#: The three evaluations, each by one name (none of them is “the benchmark”).
EVALUATIONS: List[Dict[str, Any]] = [
    {
        "id": "daily_trial",
        "name": "Thử nghiệm hằng ngày",
        "name_en": "Daily trial",
        "checks": (
            "Agent CIO và Agent Phản biện trên tin trong ngày, không người duyệt; dự báo bóng chấm theo thị trường"
        ),
        "when": "08:30 mỗi sáng đến 31/10/2026 (job trial_daily; chấm điểm 15 phút một lần: trial_score)",
        "page": "#/cio/mo-hinh/thu-nghiem",
    },
    {
        "id": "change_gate",
        "name": "Cổng thay đổi",
        "name_en": "Change gate",
        "checks": "bộ tin mẫu cố định với kết quả mong đợi (BRD-RULE-MEAS-07); đạt thì đề xuất mới được duyệt",
        "when": "khi có đề xuất đổi lời nhắc hoặc mô hình (job agent_eval)",
        "page": "#/cio/cau-hinh",
    },
    {
        "id": "assistant_set",
        "name": "Bộ kiểm tra trợ lý",
        "name_en": "Assistant test set",
        "checks": "32 câu hỏi cho OneWealth Copilot: công cụ, từ chối, không lộ số của khách khác, mỗi con số có nguồn",
        "when": "chạy tay (scripts/eval_assistant.py), mỗi khi đổi mô hình hoặc lời dặn",
        "page": None,
    },
]
#: the assistant test set's last recorded run (docs/brd/testing/assistant_readiness.md): it runs by hand, not stored
ASSISTANT_SET_LAST = {
    "at": 1792213200.0,
    "summary": "31/32 câu đạt, bảo mật 4/4, không lộ số (17/10/2026)",
    "passed": True,
}


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


def _client_step(rules: str) -> tuple:
    """The declaration chat's and the statement reader's model now (wealth/ai.client_model, BRD-NFR-08)."""
    import os

    from wealth import ai

    use = ai.client_model()
    if use == "assistant":
        return "live", (os.environ.get("LLM_MODEL") or "").strip() or "gpt-4o-mini"
    if use == "onprem":
        return "live", (os.environ.get("LLM_ONPREM_MODEL") or "").strip()
    return "rules", rules


def _latest_gate() -> Optional[Dict[str, Any]]:
    """The change gate's latest finished result, on any eval-gated proposal (control/config.set_eval)."""
    from control import config

    done = [
        {"at": ev.get("finished"), "summary": ev.get("summary"), "passed": ev.get("passed"), "version": v["id"]}
        for kind, k in config.KINDS.items()
        if k.get("eval")
        for v in config.versions(kind)
        for ev in [v.get("eval") or {}]
        if ev.get("status") == "done"
    ]
    return max(done, key=lambda r: r["at"] or 0, default=None)


def _latest_trial() -> Optional[Dict[str, Any]]:
    """The daily trial's latest morning (src/trial/daily): its events and errors."""
    from trial import daily

    by_day = daily.days()
    if not by_day:
        return None
    day = max(by_day)
    runs = by_day[day]
    errors = sum(1 for t in runs if t.get("error"))
    return {
        "at": max(t["created"] for t in runs),
        "summary": f"{day}: {len(runs)} sự kiện, {errors} lỗi",
        "passed": errors == 0,
    }


def evaluations() -> List[Dict[str, Any]]:
    latest = {"daily_trial": _latest_trial, "change_gate": _latest_gate, "assistant_set": lambda: ASSISTANT_SET_LAST}
    out = []
    for e in EVALUATIONS:
        try:
            last = latest[e["id"]]()
        except Exception:  # noqa: BLE001 — a store that is not there yet is “no result”, not a broken page
            last = None
        out.append({**e, "agents": [a["id"] for a in ENTRIES if e["id"] in a["measured"]], "latest": last})
    return out


def catalogue() -> Dict[str, Any]:
    from assistant import turn
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
        "evidence": ("live", st["cio"]) if mode == "live" else ("mock", "từ khóa và khung mẫu (mô phỏng)"),
        "explain": ("template", "mẫu tất định"),
        "copilot": ("live", copilot_router.model()) if turn.live() else ("keyword", "từ khóa (mô phỏng)"),
        "declare": _client_step("luật đọc câu (không mô hình)"),
        "statements": _client_step("luật đọc tệp (không mô hình)"),
        "newsletter": ("live", st["cio"]) if mode == "live" else ("template", "đoạn mở đầu theo mẫu"),
    }
    out = []
    for e in ENTRIES:
        m, model = now[e["id"]]
        out.append(
            {
                **e,
                "settings": e.get("settings") or ([e["resource"]] if e["resource"] else []),
                "mode": m,
                "model": model,
                "latest_run": _latest_run(e["id"]) if e["id"] in ("cio", "challenger", "policy") else None,
            }
        )
    return {"agents": out, "evaluations": evaluations(), "references": REFS, "prompt_version": agents.prompt_version()}


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
