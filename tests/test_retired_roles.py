"""Compliance and the specialists are retired (OWN-FB-18): the RM's approval is the last, an RM's own
recommendation reaches the client at once, and a database seeded before keeps no account of a retired role."""

import asyncio
import json

from operonx import Operon

from control import db
from people import auth
from people import store as people
from review.graph import recommend_flow, review_flow
from wealth import store

REVIEW = Operon(review_flow, params={"item_id": None, "decision": None, "note": None, "by": None})
RECOMMEND = Operon(recommend_flow, params={"client_id": None, "title": None, "actions": None, "note": None, "by": None})


def run(eng, **inputs):
    return asyncio.run(eng.run(inputs=inputs))


def _actions(obj):
    with db.tx() as con:
        return [r[0] for r in con.execute("select action from audit_log where object = ?", (obj,))]


def test_the_rms_approval_is_final():
    item = store.propose("C01", "plan", "Tăng quỹ học vấn", {"option": {"id": "light", "actions": ["Gửi thêm"]}})
    got = run(REVIEW, item_id=item, decision="approved", note="Hợp lý", by="rm01")["item"]
    assert got["status"] == "approved" and got["data"]["decided_by"] == "rm01"
    assert _actions(item) == ["review.decide"]


def test_an_item_queued_for_an_expert_before_is_the_rms_to_decide():
    item = store.propose("C01", "plan", "Mua bảo hiểm", {"option": {"id": "light", "actions": ["Mua gói"]}})
    with store._db() as con:
        con.execute("update reviews set status = 'pending_specialist' where id = ?", (item,))
    got = run(REVIEW, item_id=item, decision="approved", note="", by="rm01")["item"]
    assert got["status"] == "approved" and got["data"]["decided_by"] == "rm01"


def test_an_rms_recommendation_is_approved_at_once():
    body = {"title": "Cơ cấu lại tiền gửi", "actions": ["Chuyển 200 triệu sang kỳ hạn 12 tháng", " "], "by": "rm01"}
    a = run(RECOMMEND, client_id="C01", **body)["item"]
    assert a["status"] == "approved" and a["kind"] == "rm_note" and a["data"]["author"] == "rm01"
    assert a["data"]["option"]["actions"] == ["Chuyển 200 triệu sang kỳ hạn 12 tháng"]
    assert run(RECOMMEND, client_id="C02", title="x", actions=["y"], by="cio").get("$errors")  # only an RM


def test_a_database_seeded_before_loses_its_retired_staff():
    auth.accounts()  # seeded
    with people._db(write=True) as con:
        con.execute(
            "insert into people values ('compliance', 900, 'staff', 'compliance', 'Old Compliance', "
            "'compliance@demo', null, null, ?)",
            (json.dumps({}),),
        )
        con.execute(
            "insert into people values ('sp_global', 901, 'staff', 'specialist', 'Old Specialist', "
            "'sp@demo', null, null, ?)",
            (json.dumps({}),),
        )
        con.execute("insert into accounts values ('compliance', 'compliance', null, 0, null)")
        con.execute("insert into teams values ('C01', 'sp_global', 'specialist', 0, 9)")
    people._TOPPED.clear()
    ids = {a["id"] for a in auth.accounts()}
    assert not {"compliance", "sp_global"} & ids and {"cio", "cio2", "rm01"} <= ids
    with people._db() as con:
        assert not con.execute("select 1 from people where role in ('compliance', 'specialist')").fetchone()
        assert not con.execute("select 1 from teams where person_id = 'sp_global'").fetchone()
