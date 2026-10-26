"""Control and behaviour measures (BRD-KPI-05, KPI-06, KPI-07; BRD_REMAINING_PLAN G7): recommendations with a
reviewer and a log, RM contacts that start from a system signal, high-level alerts the client opened."""

import asyncio

import pytest
from operonx import Operon
from test_apply import MARKET, approved

from contacts import store as contacts
from contacts.graph import contact_flow
from control import db
from control.errors import BadRequest
from feed import opens
from feed.graph import feed_flow, feed_open_flow
from measure import reviewed
from review.graph import review_flow
from wealth import store as wealth

FEED = Operon(feed_flow, params={"client_id": None, "scope": None, "role": None})
OPEN = Operon(feed_open_flow, params={"client_id": None, "key": None})
CONTACT = Operon(contact_flow, params={"family_id": None, "channel": None, "signal": None, "note": None, "by": None})
REVIEW = Operon(review_flow, params={"item_id": None, "decision": None, "note": None, "by": None})


def run(eng, **inputs):
    return asyncio.run(eng.run(inputs=inputs))


def _actions(obj):
    with db.tx() as con:
        return [r[0] for r in con.execute("select action from audit_log where object = ?", (obj,))]


# -- KPI-05 ----------------------------------------------------------------------------------------


def test_a_recommendation_counts_when_a_person_reviewed_it_and_the_chain_logged_it():
    _, r = approved(*MARKET)
    item = wealth.propose("C05", "plan", "Kế hoạch thử", {})  # the RM decides alone (OWN-FB-18)
    got = run(REVIEW, item_id=item, decision="approved", note="Đồng ý", by="rm01")
    assert got["item"]["data"]["decided_by"] == "rm01" and _actions(item) == ["review.decide"]
    # an item decided the way the queue did before G7: no one named, nothing in the chain
    old = wealth.propose("C05", "plan", "Kế hoạch cũ", {})
    wealth.decide(old, "approved", "")
    rows = {x["id"]: x for x in reviewed.rows()}
    assert rows[r["id"]]["ok"] and rows[r["id"]]["reviewer"] == "cio"
    assert rows[item]["ok"] and rows[item]["reviewer"] == "rm01"
    assert rows[old]["missing"] == ["không có người duyệt", "thiếu nhật ký"]
    [m] = reviewed.rate()["by_month"]
    assert (m["recommendations"], m["ok"], m["share"]) == (3, 2, 0.667)
    assert m["by_kind"] == {"run": 1, "newsletter": 0, "rm_item": 2}
    assert [x["id"] for x in reviewed.rate()["misses"]] == [old]


# -- KPI-06 ----------------------------------------------------------------------------------------


def test_a_contact_from_a_hom_nay_signal_counts_and_a_signal_the_product_never_gave_is_refused():
    _, r = approved(*MARKET)
    flagged = [x["family_id"] for x in r["ranking"] if x["pre_review"]]
    calm = [x["family_id"] for x in r["ranking"] if not x["pre_review"]]
    assert flagged and calm
    fid = flagged[0]
    got = run(CONTACT, family_id=fid, channel="call", signal=f"pre_review:{r['id']}", note="Gọi báo", by="rm01")
    c = got["contact"]
    assert c["from_signal"] and c["signal"]["kind"] == "pre_review" and c["channel_label"] == "Gọi điện"
    assert _actions(c["id"]) == ["contact.log"]
    run(CONTACT, family_id=fid, channel="meeting", signal=None, note="Khách hẹn gặp", by="rm01")
    with pytest.raises(BadRequest, match="không đưa gia đình"):
        contacts.log(calm[0], "call", f"pre_review:{r['id']}", "", "rm01")
    with pytest.raises(BadRequest, match="Cách liên hệ"):
        contacts.log(fid, "fax", None, "", "rm01")
    refused = run(CONTACT, family_id=fid, channel="call", signal=None, note="", by="cio")
    assert refused.get("$errors")  # only an RM
    s = contacts.share()
    [m] = s["by_month"]
    assert (m["contacts"], m["from_signal"], m["share"]) == (2, 1, 0.5) and s["target"] == 0.5
    assert s["by_rm"] == [{"by": "rm01", "contacts": 2, "from_signal": 1, "share": 0.5}]
    assert [x["id"] for x in contacts.recent([fid])][1] == c["id"] and contacts.recent(["C99"]) == []


def test_a_contact_note_is_sealed_at_rest_when_a_key_is_set(monkeypatch):
    from control import crypto

    monkeypatch.setenv("MF_DATA_KEYS", "k1=" + crypto.new_key())
    c = contacts.log("C01", "message", None, "Khách hỏi về học phí", "rm01")
    with db.tx() as con:
        raw = con.execute("select data from rm_contacts where id = ?", (c["id"],)).fetchone()[0]
    assert crypto.sealed(raw) and "học phí" not in raw
    assert contacts.get(c["id"])["note"] == "Khách hỏi về học phí"


# -- KPI-07 ----------------------------------------------------------------------------------------


def test_a_high_level_item_is_delivered_once_and_opened_once_by_the_client():
    fid = "C03"  # its risk is over the profile's limit: a high-level item for the client
    items = run(FEED, client_id=fid, role="client")["feed"]["items"]
    high = [i for i in items if i["severity"] == "high"]
    assert high
    run(FEED, client_id=fid, role="client")  # read again: delivered once
    run(FEED, client_id=fid, role="rm")  # the RM's view delivers nothing to the client
    [m] = opens.rate()["by_month"]
    assert (m["delivered"], m["opened"]) == (len(high), 0)
    assert run(OPEN, client_id=fid, key=high[0]["key"])["opened"] is True
    assert run(OPEN, client_id=fid, key=high[0]["key"])["opened"] is False  # once
    assert run(OPEN, client_id=fid, key="feed:never:shown")["opened"] is False
    [m] = opens.rate()["by_month"]
    assert m["opened"] == 1 and m["share"] == round(1 / len(high), 3) and m["hours"]["n"] == 1


def test_staff_reading_the_clients_view_deliver_and_open_nothing(monkeypatch):
    from people import auth

    monkeypatch.setattr(auth, "checking", lambda: True)
    monkeypatch.setattr(auth, "signed_in", lambda: {"id": "rm01", "role": "rm", "families": ["C01"]})
    assert not opens.as_client()
    monkeypatch.setattr(auth, "signed_in", lambda: {"id": "C01", "role": "client", "family": "C01"})
    assert opens.as_client()
