"""The certified specialist (BRD-RULE-ROLE-05, WF-08; BRD_REMAINING_PLAN G8, G-D7): an action recommendation the RM
approves waits for the family's certified specialist; a family with none is approved by the RM alone."""

import asyncio

import pytest
from operonx import Operon

from control import config, db
from measure import reviewed
from people import auth
from people import store as people
from review import specialist
from review.graph import recommend_flow, review_flow, specialist_flow
from wealth import store

REVIEW = Operon(review_flow, params={"item_id": None, "decision": None, "note": None, "by": None})
SPEC = Operon(specialist_flow, params={"item_id": None, "decision": None, "note": None, "by": None})
RECOMMEND = Operon(recommend_flow, params={"client_id": None, "title": None, "actions": None, "note": None, "by": None})


def run(eng, **inputs):
    return asyncio.run(eng.run(inputs=inputs))


def _actions(obj):
    with db.tx() as con:
        return [r[0] for r in con.execute("select action from audit_log where object = ?", (obj,))]


def _rm_approves(client_id, rm):
    item = store.propose(client_id, "plan", "Tăng quỹ học vấn", {"option": {"id": "light", "actions": ["Gửi thêm"]}})
    return run(REVIEW, item_id=item, decision="approved", note="Hợp lý", by=rm)["item"]


def test_an_rm_approval_waits_for_the_familys_certified_specialist():
    # C01's specialists: sp_global and sp_insurance are certified, sp_real_estate is not
    assert [a["id"] for a in specialist.approvers("C01")] == ["sp_global", "sp_insurance"]
    item = _rm_approves("C01", "rm01")
    assert item["status"] == "pending_specialist" and item["data"]["decided_by"] == "rm01"
    for who in ("sp_real_estate", "sp_banking"):  # not certified / not this family's
        assert run(SPEC, item_id=item["id"], decision="approved", note="", by=who).get("$errors")
    assert run(SPEC, item_id=item["id"], decision="approved", note="", by="rm01").get("$errors")  # not a specialist
    refused = run(SPEC, item_id=item["id"], decision="rejected", note="không", by="sp_global")
    assert "lý do" in str(refused["$errors"])
    got = run(SPEC, item_id=item["id"], decision="approved", note="Phù hợp mục tiêu", by="sp_global")["item"]
    assert got["status"] == "approved" and got["data"]["specialist_by"] == "sp_global"
    assert got["data"]["certificate"] == "CFA (demo)" and got["decided"]
    assert _actions(item["id"]) == ["review.decide", "review.specialist"]
    assert run(SPEC, item_id=item["id"], decision="rejected", note="x" * 12, by="sp_insurance").get("$errors")  # once
    row = next(r for r in reviewed.rows() if r["id"] == item["id"])
    assert row["ok"] and row["reviewer"] == "sp_global"


def test_a_family_with_no_certified_specialist_is_approved_by_the_rm_alone():
    assert people.specialists_of("C05") == ["sp_real_estate", "sp_banking"] and specialist.approvers("C05") == []
    item = _rm_approves("C05", "rm01")
    assert item["status"] == "approved" and _actions(item["id"]) == ["review.decide"]
    assert next(r for r in reviewed.rows() if r["id"] == item["id"])["ok"]


def test_a_lapsed_certificate_cannot_approve():
    item = _rm_approves("C03", "rm03")  # C03: sp_global (certified) and sp_banking
    assert item["status"] == "pending_specialist"
    certs = config.data("certifications")
    v = config.propose("certifications", {**certs, "sp_global": {**certs["sp_global"], "valid_until": "2026-01-31"}},
                       "compliance", "Hết hạn")  # fmt: skip
    config.decide(v["id"], "approve", "compliance2")
    assert specialist.approvers("C03") == []
    assert run(SPEC, item_id=item["id"], decision="approved", note="", by="sp_global").get("$errors")


def test_certifications_are_checked_configuration():
    certs = config.data("certifications")
    with pytest.raises(ValueError, match="không phải chuyên gia"):
        config.propose("certifications", {**certs, "rm01": certs["sp_global"]}, "compliance")
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        config.propose("certifications", {"sp_global": {**certs["sp_global"], "valid_until": "mai"}}, "compliance")
    with pytest.raises(Exception, match="Tuân thủ"):
        config.propose("certifications", certs, "admin")  # Compliance owns it


def test_the_rms_own_recommendation_waits_for_the_specialist_and_alone_has_no_second_person():
    body = {"title": "Cơ cấu lại tiền gửi", "actions": ["Chuyển 200 triệu sang kỳ hạn 12 tháng", " "], "by": "rm01"}
    a = run(RECOMMEND, client_id="C01", **body)["item"]
    assert a["status"] == "pending_specialist" and a["kind"] == "rm_note"
    assert a["data"]["option"]["actions"] == ["Chuyển 200 triệu sang kỳ hạn 12 tháng"] and a["data"]["author"] == "rm01"
    b = run(RECOMMEND, client_id="C05", **body)["item"]
    assert b["status"] == "approved"
    assert next(r for r in reviewed.rows() if r["id"] == b["id"])["missing"] == ["người duyệt là người soạn"]
    run(SPEC, item_id=a["id"], decision="approved", note="", by="sp_global")
    assert next(r for r in reviewed.rows() if r["id"] == a["id"])["ok"]
    assert run(RECOMMEND, client_id="C01", title="x", actions=[], by="rm01").get("$errors")
    assert run(RECOMMEND, client_id="C02", title="x", actions=["y"], by="cio").get("$errors")  # only an RM


def test_a_specialist_signs_in_and_sees_only_the_families_assigned_to_them():
    v = auth._viewer(people.person("sp_global"))
    assert v["role"] == "specialist" and v["families"] == ["C01", "C03"]
    assert auth.may_see(v, "C01") and auth.may_see(v, "C03") and not auth.may_see(v, "C02")
    assert "sp_global" in {a["id"] for a in auth.accounts()}


def test_a_database_made_before_specialists_had_accounts_gives_them_one():
    auth.accounts()  # seeded
    with db.tx() as con:
        con.execute("delete from accounts where person_id like 'sp_%'")
    people._TOPPED.clear()
    assert {"sp_global", "sp_banking"} <= {a["id"] for a in auth.accounts()}
