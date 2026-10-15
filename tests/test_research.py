"""Exclusive research (release by Compliance) and the goal branch (regulation notes → goals abroad)."""

import asyncio
import time
from datetime import date

import pytest
from operonx import Operon
from starlette.testclient import TestClient

from news import store as news_store
from procedural import goals
from research import store
from research.graph import goal_outflow_flow, research_release_flow, research_upload_flow
from research.ops import matches

UPLOAD = Operon(research_upload_flow, params={"item": None, "by": None})
RELEASE = Operon(research_release_flow, params={"item_id": None, "decision": None, "by": None, "note": None})
DECLARE = Operon(
    goal_outflow_flow, params={"family_id": None, "goal_id": None, "purpose": None, "by": None, "country": None}
)
NOTE = "Đã kiểm tra nguồn công khai và xung đột lợi ích"
TODAY = date(2026, 10, 15)


def run(engine, **inputs):
    return asyncio.run(engine.run(inputs=inputs))


def report(release_at="2026-10-01T08:00:00+07:00", **kw):
    return {
        "kind": "research",
        "report_no": "RS-2026-101",
        "title": "Ngân hàng: tín dụng quý 3 tăng tốc",
        "summary": "Tăng trưởng tín dụng ngân hàng cao hơn kỳ vọng, nợ xấu ổn định.",
        "release_at": release_at,
        **kw,
    }


AML_DRAFT = {
    "kind": "regulation",
    "report_no": "QD-2026-07",
    "title": "Dự thảo Thông tư giám sát phòng, chống rửa tiền (NHNN)",
    "summary": "Thêm bước xác minh nguồn tiền cho chuyển tiền ra nước ngoài.",
    "release_at": "2026-10-01T08:00:00+07:00",
    "regulation": {
        "document": "Dự thảo Thông tư (NHNN, 2026)",
        "status": "draft",
        "purposes": ["study_abroad"],
        "prep_weeks": 8,
        "documents": ["Thư mời nhập học", "Xác nhận học phí"],
        "client_message": "Chuyển học phí ra nước ngoài có thể cần thêm giấy tờ; hãy chuẩn bị sớm.",
        "rm_hint": "Nhắc khách chuẩn bị hồ sơ học phí sớm hơn thường lệ.",
    },
}


# -- research ----------------------------------------------------------------------------------


def test_a_report_waits_for_compliance_and_then_reaches_the_inbox():
    assert "không được làm việc này" in str(run(UPLOAD, item=report(), by="rm01")["$errors"])
    item = run(UPLOAD, item=report(), by="cio")["item"]
    assert item["status"] == "PENDING_RELEASE"
    assert not [n for n in news_store.inbox() if n.get("research_id") == item["id"]]  # FR-203
    assert "từ 20 ký tự" in str(
        run(RELEASE, item_id=item["id"], decision="release", by="compliance", note="ok")["$errors"]
    )
    out = run(RELEASE, item_id=item["id"], decision="release", by="compliance", note=NOTE)["item"]
    assert out["status"] == "RELEASED" and out["decided_by"] == "compliance"
    [n] = [n for n in news_store.inbox() if n.get("research_id") == item["id"]]
    assert n["label"] == "Độc quyền" and n["published"] == item["release_at"]


def test_the_uploader_cannot_release_and_nothing_goes_out_before_its_time():
    item = store.upload(report(), "cio")
    with pytest.raises(store.ResearchError, match="khác người nạp"):
        store.decide(item["id"], "release", "cio", NOTE)
    future = store.upload(report(release_at="2099-01-01T08:00:00+07:00", report_no="X2"), "cio")
    with pytest.raises(store.ResearchError, match="Chưa tới giờ phát hành"):
        store.decide(future["id"], "release", "compliance", NOTE)
    assert store.decide(future["id"], "release", "compliance", NOTE, now=time.time() + 10**10)["status"] == "RELEASED"


def test_a_report_naming_the_restricted_list_is_not_released():
    item = store.upload(report(title="Sao Mai Land: rủi ro đáo hạn trái phiếu", report_no="X3"), "cio")
    with pytest.raises(store.ResearchError, match="danh sách hạn chế"):
        store.decide(item["id"], "release", "compliance", NOTE)
    assert (
        store.decide(item["id"], "reject", "compliance", "Nhắc tổ chức trong danh sách hạn chế")["status"] == "REJECTED"
    )


def test_a_regulation_note_with_aml_wording_is_refused():
    bad = {
        **AML_DRAFT,
        "regulation": {**AML_DRAFT["regulation"], "client_message": "Khách thuộc diện PEP cần giám sát tăng cường."},
    }
    with pytest.raises(store.ResearchError, match="FR-604"):
        store.upload(bad, "cio")


# -- the goal branch ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "label, expected",
    [
        ("Học phí du học (Úc) – Minh An", {"purpose": "study_abroad", "country": "Úc"}),
        ("Học phí đại học (Mỹ) – Phát Đạt", {"purpose": "study_abroad", "country": "Mỹ"}),
        ("Định cư Canada 2030", {"purpose": "emigrate", "country": "Canada"}),
        ("Học phí cho Mỹ Linh", None),  # a name, not a country
        ("Quà cưới Nhật Minh", None),
        ("Đám cưới Minh Đức", None),
        ("Góp vốn mở rộng kho bãi", None),
    ],
)
def test_inference_from_a_goals_name(label, expected):
    assert goals.infer(label) == expected


def test_the_brd_example_draft_aml_rule_and_a_study_abroad_goal():
    """BRD §10: Úc study in March 2027, 8 more weeks → milestone 7/12/2026; a draft → remind."""
    note = store.upload(AML_DRAFT, "cio")
    assert not matches("C01", TODAY)  # not released yet
    store.decide(note["id"], "release", "compliance", NOTE)
    assert not [n for n in news_store.inbox(status="all") if n.get("research_id") == note["id"]]  # not a price event
    [m] = matches("C01", TODAY)
    assert (m["milestone"], m["level"], m["declared"]) == ("2026-12-07", "confirm_goal", False)
    assert m["client_message"] is None  # inferred: an RM task only
    run(DECLARE, family_id="C01", goal_id=m["goal_id"], purpose="study_abroad", country="Úc", by="rm01")
    [m] = matches("C01", TODAY)
    assert (m["level"], m["declared"]) == ("remind", True) and m["client_message"]


def test_an_issued_rule_close_to_the_milestone_means_contact_now_and_late_rules_are_a_note():
    issued = {**AML_DRAFT, "report_no": "QD-2", "regulation": {**AML_DRAFT["regulation"], "status": "issued"}}
    n = store.upload(issued, "cio")
    store.decide(n["id"], "release", "compliance", NOTE)
    store.declare("C01", "GL-C01-01", "study_abroad", "Úc", "rm01")
    assert matches("C01", TODAY)[0]["level"] == "contact_now"  # milestone 7/12/2026 is 53 days away
    assert (
        goals.level(TODAY, date(2027, 3, 15), date(2026, 12, 7), {"status": "issued", "effective_date": "2027-06-01"})
        == "note"
    )  # money leaves first
    assert goals.level(TODAY, date(2030, 1, 15), date(2029, 11, 1), {"status": "issued"}) == "note"


def test_country_limits_and_past_goals():
    other = {**AML_DRAFT, "report_no": "QD-3", "regulation": {**AML_DRAFT["regulation"], "countries": ["Anh"]}}
    n = store.upload(other, "cio")
    store.decide(n["id"], "release", "compliance", NOTE)
    assert matches("C01", TODAY) == []  # Úc is not Anh
    assert (
        goals.goals_of(
            {"id": "X", "events": [{"date": "2020-01-01", "direction": "out", "label": "Du học (Úc)"}]}, TODAY
        )
        == []
    )


def test_the_reads_and_the_rm_list():
    from app.web import app

    n = store.upload(AML_DRAFT, "cio")
    store.decide(n["id"], "release", "compliance", NOTE)
    client = TestClient(app)
    assert client.get("/api/goals/regulation?family_id=C01&role=client").json()["matches"] == []  # nothing declared
    staff = client.get("/api/goals/regulation?family_id=C01").json()
    assert staff["matches"][0]["level"] == "confirm_goal" and staff["goals"][0]["goal_id"] == "GL-C01-01"
    assert any(t["family_id"] == "C01" for t in client.get("/api/rm/today").json()["goal_tasks"])
    assert client.get("/api/research").json()["items"][0]["status"] == "RELEASED"
    assert "không có mục tiêu" in str(
        run(DECLARE, family_id="C01", goal_id="GL-C01-99", purpose="study_abroad", by="rm01")["$errors"]
    )
