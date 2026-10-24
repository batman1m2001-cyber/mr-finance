"""Two BRD rules checked in the browser (BRD completion F10):

- BRD-FR-603: the goal branch shows on the RM's home, the client's goals tab and market-impact page, and the
  Research page of the CIO and of Compliance;
- BRD-RULE-SEC-03: every page that explains a family's numbers to an RM is stamped “Nội bộ”, and the client's own
  pages are not."""

from conftest import api, in_thread
from test_apply import MARKET, approved
from test_research import AML_DRAFT, DECLARE, NOTE, run

from research import store as research


def seed_goal_branch():
    item = research.upload(AML_DRAFT, "cio")
    research.decide(item["id"], "release", "cio2", NOTE)  # not the uploader (OWN-FB-18)
    out = run(DECLARE, family_id="C01", goal_id="GL-C01-01", purpose="study_abroad", by="rm01")
    assert "$errors" not in out, out
    return item


def test_fr603_the_goal_branch_is_on_the_rm_home_the_goals_tab_the_impact_page_and_research(open_page, base_url):
    in_thread(seed_goal_branch)
    reg = AML_DRAFT["regulation"]
    p = open_page()
    p.go("#/rm/hom-nay")
    family = api(base_url, "/api/rm/today", who="rm01")["goal_tasks"][0]
    assert family["family_id"] == "C01"
    assert reg["document"] in p.page.inner_text("#page") and reg["rm_hint"] in p.page.inner_text("#page")
    p.go("#/client/muc-tieu/ke-hoach")
    assert reg["client_message"] in p.page.inner_text("#page")
    p.go("#/client/tin/thi-truong")
    assert reg["client_message"] in p.page.inner_text("#page")
    p.go("#/cio/nghien-cuu")
    text = p.page.inner_text("#page")
    assert AML_DRAFT["title"] in text and "mục tiêu bị ảnh hưởng" in text
    client_view = api(base_url, "/api/goals/regulation?family_id=C01&role=client")
    assert client_view["matches"] and not p.problems()


RM_PAGES = [
    "#/rm/hom-nay",
    "#/rm/khach-hang/tac-dong",
    "#/rm/khach-hang/do-thi",
    "#/rm/khach-hang/toan-canh",
    "#/rm/khach-hang/ban-do",
    "#/rm/khach-hang/tong-quan",
    "#/rm/khach-hang/tai-san",
    "#/rm/khach-hang/ke-hoach",
    "#/rm/khach-hang/chinh-sach",
    "#/rm/khach-hang/hieu-qua",
]
CLIENT_PAGES = [
    "#/client/tong-quan/toan-canh",
    "#/client/tin/thi-truong",
    "#/client/muc-tieu/ke-hoach",
    "#/client/tai-san",
]


def test_sec03_every_rm_explanation_page_is_stamped_internal_and_the_clients_are_not(open_page):
    in_thread(approved, *MARKET)
    p = open_page()
    missing = []
    for route in RM_PAGES:
        p.go(route)
        stamp = p.page.locator("#page .internal")
        if not (stamp.count() and "Nội bộ" in stamp.first.inner_text() and stamp.first.is_visible()):
            missing.append(route)
    assert not missing, missing
    p.go("#/rm/khach-hang/tac-dong")  # the trace drawer (“Cách tính”) too
    p.page.locator("[data-trace]").first.click()
    p.page.wait_for_selector(".drawer .internal")
    for route in CLIENT_PAGES:
        p.go(route)
        assert p.page.locator("#page .internal").count() == 0, route
    assert not p.problems()
