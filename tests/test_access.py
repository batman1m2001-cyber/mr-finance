"""Every served route, as every kind of person (BRD-RULE-SEC-02, ROLE-02, ROLE-04; BRD completion F5).

The matrix below is the policy, written out on its own: who may open each read and take each action. Each route is
called signed out (401), by each person it refuses (403, never a 500), and by each it lets in (not refused). A
route the app serves that is not in the matrix fails the test, so a new one needs a decision here.

The people: two customers (C01's family, and C02, another family), the RM assigned to C01 (rm01) and one who is
not (rm03), the CIO, Compliance and Admin.
"""

import pytest
from operonx.app import Application
from starlette.routing import Route
from starlette.testclient import TestClient

from control import config
from people import auth
from wealth import store

PEOPLE = ("C01", "C02", "rm01", "rm03", "cio", "compliance", "admin")
ALL = set(PEOPLE)
FAMILY = {"C01", "rm01", "cio", "compliance", "admin"}  # who may see C01's family (ROLE-02)
STAFF = {"rm01", "rm03", "cio", "compliance", "admin"}
DESK = {"cio", "compliance", "admin"}  # the news-impact desk and those who check it
HOME = {"C02": "C02", "rm03": "C03"}  # a family each person may see (C01 otherwise)
ROLE = {"C01": "client", "C02": "client", "rm01": "rm", "rm03": "rm"}

# -- reads (app/web.py) -----------------------------------------------------------------------------
READS = {
    "/api/clients": ALL,
    "/api/views": ALL,
    "/api/scenarios?client_id=C01": FAMILY,
    "/api/review?client_id=C01": FAMILY,
    "/api/advisory?client_id=C01": FAMILY,
    "/api/goals/regulation?client_id=C01": FAMILY,
    "/api/families/C01/impact": FAMILY,
    "/api/families/C01/graph": FAMILY,
    "/api/families/C01/how?run=AR-0000": FAMILY,
    "/api/trace/AR-0000/C01": FAMILY & STAFF,  # “Cách tính” is for staff (Q-14)
    "/api/advisory/all": STAFF,
    "/api/model": STAFF,
    "/api/model/estimate": STAFF,
    "/api/agents": STAFF,
    "/api/agents/catalogue": DESK,
    "/api/news/inbox": DESK,
    "/api/news/config": DESK,
    "/api/events": DESK,
    "/api/events/EV-0000": DESK,
    "/api/views/VW-0000": DESK,
    "/api/runs": DESK,
    "/api/runs/AR-0000": DESK,
    "/api/runs/AR-0000/verify": DESK,
    "/api/runs/AR-0000/graph": DESK,
    "/api/config": DESK,
    "/api/config/CF-thresholds-v1": DESK,
    "/api/accuracy": DESK,
    "/api/measure": DESK,
    "/api/research": {"cio", "compliance"},
    "/api/newsletters": {"cio", "compliance"},
    "/api/newsletters/NL-0000": {"cio", "compliance"},
    "/api/policy": {"cio", "compliance"},
    "/api/policy/PD-0000": {"cio", "compliance"},
    "/api/market": {"cio", "admin"},
    "/api/market/series?id=VNINDEX": {"cio", "admin"},
    "/api/audit": {"compliance", "admin"},
    "/api/audit/verify": {"compliance", "admin"},
    "/api/audit/export": {"compliance", "admin"},
    "/api/system": {"admin"},
    "/api/system/alerts": DESK,  # the bell: each role its kinds of alert
    "/api/rm/today": {"rm01", "rm03"},
}
OPEN = {"/healthz", "/api/auth/me", "/api/auth/accounts", "/api/auth/login", "/api/auth/demo", "/api/auth/logout"}
OPEN |= {"/api/inbox"}  # the AI zone's door: signed (MF_INBOX_KEY), not signed in; answers an id only
DEMO = {"/api/reset"}  # anyone signed in starts the public demo over


# -- actions (app/main.py): the body, with BY the person acting and AS their role ---------------------
def actions(vid, item):
    return [
        ("/api/dashboard", {"client_id": "C01"}, FAMILY),
        ("/api/overview", {"client_id": "C01", "role": "AS"}, FAMILY),
        ("/api/flows", {"client_id": "C01"}, FAMILY),
        ("/api/feed", {"client_id": "C01", "role": "AS"}, FAMILY),
        ("/api/alerts", {"client_id": "C01"}, FAMILY),
        ("/api/goals", {"client_id": "C01"}, FAMILY),
        ("/api/risk", {"client_id": "C01"}, FAMILY),
        ("/api/scenario", {"client_id": "C01", "scenario": "retire_early"}, FAMILY),
        ("/api/statement", {"client_id": "C01", "filename": "a.csv", "content": "x"}, FAMILY),
        ("/api/declare", {"client_id": "C01", "message": "Tôi có 100 triệu tiền gửi"}, FAMILY),
        ("/api/review/propose", {"client_id": "C01", "option": "x"}, FAMILY),
        ("/api/search", {"q": "tiền", "role": "AS", "client_id": "HOME"}, ALL),
        ("/api/copilot", {"question": "Tổng tài sản?", "role": "AS", "client_id": "HOME"}, ALL),
        ("/api/review/decide", {"item_id": item, "decision": "approved", "note": "ok", "by": "BY"}, {"rm01"}),
        ("/api/config/decide", {"version_id": vid, "action": "reject", "by": "BY", "note": "x"}, {"cio"}),
        ("/api/config/propose", {"kind": "thresholds", "data": "THR", "by": "BY", "note": "x"}, {"cio"}),
        ("/api/news/ingest", {}, {"cio"}),
        ("/api/news/dismiss", {"ids": ["NW-0"], "by": "BY"}, {"cio"}),
        ("/api/news/release", {"item_id": "NW-0", "by": "BY", "note": "x" * 20}, {"compliance"}),
        ("/api/events", {"news_ids": ["NW-0"], "by": "BY"}, {"cio"}),
        ("/api/events/run-agent", {"event_id": "EV-0000", "by": "BY"}, {"cio"}),
        ("/api/views/decide", {"view_id": "VW-0000", "action": "approve", "by": "BY"}, {"cio"}),
        ("/api/runs/recompute", {"run": "AR-0000", "by": "BY"}, {"cio"}),
        ("/api/runs/decide", {"run": "AR-0000", "action": "withdraw", "by": "BY", "reason": "x"}, {"cio"}),
        ("/api/research", {"item": {"title": "x"}, "by": "BY"}, {"cio"}),
        (
            "/api/research/release",
            {"item_id": "RS-0", "decision": "release", "by": "BY", "note": "x" * 20},
            {"compliance"},
        ),
        ("/api/newsletters", {"view_ids": ["VW-0000"], "by": "BY"}, {"cio"}),
        ("/api/newsletters/act", {"newsletter_id": "NL-0000", "action": "approve", "by": "BY"}, {"compliance"}),
        ("/api/policy", {"item": {"title": "x"}, "by": "BY"}, {"compliance"}),
        ("/api/policy/verify", {"document_id": "PD-0000", "by": "BY", "note": "x" * 20}, {"compliance"}),
        (
            "/api/policy/status",
            {"document_id": "PD-0000", "status": "issued", "by": "BY", "note": "x" * 10},
            {"compliance"},
        ),
        ("/api/policy/summarise", {"document_id": "PD-0000", "by": "BY"}, {"compliance"}),
        ("/api/goals/outflow", {"family_id": "C01", "goal_id": "G1", "purpose": "học", "by": "BY"}, {"rm01"}),
        ("/api/model/estimate", {"by": "BY"}, {"cio"}),
        ("/api/market/load", {"by": "BY", "since": "2026-01-01"}, {"admin"}),
        ("/api/system/alerts/ack", {"alert_id": "AL-0", "by": "BY"}, DESK),
    ]


@pytest.fixture
def http(monkeypatch):
    monkeypatch.setenv("MF_AUTH", "on")
    monkeypatch.setenv("MF_DEMO_ACCOUNTS", "on")
    import news.ops

    monkeypatch.setattr(news.ops, "_get", lambda url, timeout: "<rss><channel></channel></rss>")  # no network
    with TestClient(Application.find(".").asgi()) as c:
        yield c


def as_(c, who):
    c.cookies.clear()
    if who:
        c.cookies.set(auth.COOKIE, auth.issue(who))
    return c


def _fill(body, who):
    thr = config.data("thresholds")
    fill = {"BY": who, "AS": ROLE.get(who, "rm"), "HOME": HOME.get(who, "C01"), "THR": {**thr, "pre_review_pct": -0.06}}
    return {k: fill.get(v, v) if isinstance(v, str) else v for k, v in body.items()}


def _refused_first(allowed):
    return sorted(PEOPLE, key=lambda p: (p in allowed, PEOPLE.index(p)))  # an allowed write may change the state


def test_every_read_the_app_serves_has_a_decision_here():
    from app import web

    served = {r.path for r in web.app.app.routes if isinstance(r, Route)}
    named = {p.split("?")[0] for p in READS} | OPEN | DEMO
    pattern = {p: p for p in served}
    for p in named:
        match = next((s for s in served if _same(s, p)), None)
        assert match, f"{p} is in the matrix but not served"
        pattern.pop(match, None)
    assert not pattern, f"served but not decided: {sorted(pattern)}"


def _same(template, path):
    a, b = template.strip("/").split("/"), path.strip("/").split("/")
    return len(a) == len(b) and all(x == y or x.startswith("{") for x, y in zip(a, b))


def test_every_read_as_every_person(http):
    wrong = []
    for path, allowed in READS.items():
        if as_(http, None).get(path).status_code != 401:
            wrong.append((path, "signed out", http.get(path).status_code))
        for who in PEOPLE:
            r = as_(http, who).get(path)
            ok = r.status_code < 500 and r.status_code not in (401, 403) if who in allowed else r.status_code == 403
            if not ok:
                wrong.append((path, who, r.status_code, r.text[:120]))
    assert not wrong, "\n".join(map(str, wrong))


def test_every_action_as_every_person(http):
    vid = config.propose("thresholds", {**config.data("thresholds"), "pre_review_pct": -0.07}, "cio2", "walk")["id"]
    item = store.review(store.propose("C01", "plan", "Kế hoạch thử", {}))["id"]
    wrong = []
    for path, body, allowed in actions(vid, item):
        r = as_(http, None).post(path, json=_fill(body, "cio"))
        if r.status_code != 401:
            wrong.append((path, "signed out", r.status_code, r.text[:120]))
        for who in _refused_first(allowed):
            r = as_(http, who).post(path, json=_fill(body, who))
            if who in allowed:
                ok = r.status_code not in (401, 403)
            else:
                ok = r.status_code == 403 and r.json().get("error")
            if not ok:
                wrong.append((path, who, r.status_code, r.text[:160]))
    assert not wrong, "\n".join(map(str, wrong))


def test_a_refusal_says_why_in_the_persons_language(http):
    r = as_(http, "rm03").post("/api/dashboard", json={"client_id": "C01"})
    assert r.status_code == 403 and "không được xem dữ liệu" in r.json()["error"]
    r = as_(http, "compliance").get("/api/market")
    assert r.status_code == 403 and r.json()["error"] == "Chỉ CIO, Quản trị mở được mục này"
    r = as_(http, "C01").post("/api/news/ingest", json={})
    assert r.status_code == 403 and "cần vai trò: CIO" in r.json()["error"]


def test_admin_reassigns_a_family_and_access_follows(http):
    """The RM-to-family assignment is configuration (Admin, one person): the new RM reads the family and acts for
    it, the old one no longer does."""
    cur = config.data("rm_assignment")
    assert cur == {"C01": "rm01", "C02": "rm02", "C03": "rm03", "C04": "rm01", "C05": "rm01"}
    with pytest.raises(ValueError, match="không phải RM"):
        config.propose("rm_assignment", {**cur, "C03": "cio"}, "admin")
    with pytest.raises(ValueError, match="mỗi gia đình đúng một RM"):
        config.propose("rm_assignment", {k: v for k, v in cur.items() if k != "C03"}, "admin")
    assert as_(http, "rm01").post("/api/dashboard", json={"client_id": "C03"}).status_code == 403
    v = config.propose("rm_assignment", {**cur, "C03": "rm01"}, "admin", "RM03 nghỉ phép")
    config.decide(v["id"], "approve", "admin")
    assert as_(http, "rm01").post("/api/dashboard", json={"client_id": "C03"}).status_code == 200
    assert as_(http, "rm03").post("/api/dashboard", json={"client_id": "C03"}).status_code == 403
    assert http.get("/api/auth/me").json()["user"]["families"] == []
    assert as_(http, "rm01").get("/api/auth/me").json()["user"]["families"] == ["C01", "C03", "C04", "C05"]
    assert as_(http, "C03").get("/api/families/C03/impact").status_code == 200
