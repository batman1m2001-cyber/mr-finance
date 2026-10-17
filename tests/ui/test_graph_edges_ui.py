"""Edges you can pick, categories on demand, the shared goal pool (UNIFIED_FLOWS_PLAN F3, F9, F11; OWN-GW-36, 46, 49):
a click on a wire (or Enter on it) picks it, lights its two ends and dims the rest; Thông tin shows where it comes
from, its formula read from the server's catalogue, its assumptions, its confidence only where one is recorded, and
what it reaches; money in and out open to their categories, which move and sum to the month; goals counting the
same pool say so once, and their monthly need is set against the surplus."""

import pytest
from conftest import in_thread
from test_apply import MARKET, approved

KEY = "mf.ws.scn.C01"
# the middle of a wire, on screen: where a person would click it
MID = """(k) => { const p = document.querySelector(`.whit[data-e="${k}"]`); if (!p) return null;
  const q = p.getPointAtLength(p.getTotalLength() * 0.5), m = p.getScreenCTM();
  return [q.x * m.a + q.y * m.c + m.e, q.x * m.b + q.y * m.d + m.f]; }"""
FIRST = """(prefix) => [...document.querySelectorAll('.whit')].map(h => h.dataset.e).find(k => k.startsWith(prefix))"""
FIELDS = """() => Object.fromEntries([...document.querySelectorAll('.ws-edge dt')].map(dt => [dt.textContent,
  dt.nextElementSibling.innerText]))"""


def open_lens(open_page, lens, active=None, size="desktop"):
    p = open_page(size=size, theme="dark")
    p.go(f"#/client/xem/{lens}")
    p.page.evaluate(f"localStorage.setItem('{KEY}', JSON.stringify({{ids: {active or []}, params: {{}}}}))")
    p.page.reload()
    p.page.wait_for_selector(".wnode.k-family")
    settle(p)
    return p


def settle(p):
    """The edges drawn where the nodes arrived (and the active scenarios combined)."""
    p.page.wait_for_selector(".ws-edges .whit", state="attached")
    p.page.wait_for_selector(".ws-edges:not(.moving)", state="attached")
    p.page.wait_for_function("!document.querySelector('#ws-scn').classList.contains('busy')")
    p.page.wait_for_timeout(400)


def pick(p, key):
    p.page.mouse.click(*p.page.evaluate(MID, key))
    p.page.wait_for_selector(f'.wedge.picked[data-e="{key}"]', state="attached")
    p.page.wait_for_function("!document.querySelector('[data-formula]') || document.querySelector('[data-formula]')"
                             ".textContent !== '…'")  # fmt: skip
    return p.page.evaluate(FIELDS)


CASES = [  # lens, the edge (or its prefix), active scenarios, what each field must say
    ("tin", "EV:", [], {"Nguồn": "Lần áp dụng tin", "Cách tính": "Tác động kỳ vọng", "Giả định": "CIO duyệt",
                        "Độ tin cậy": "P10", "Ảnh hưởng tiếp theo": "Tài sản ròng"}),
    ("muc-tieu", "ME>GL:tuition", [], {"Nguồn": "Mục tiêu", "Cách tính": "gửi đều mỗi tháng",
                                       "Giả định": "Lãi tiền gửi", "Độ tin cậy": "Không có độ tin cậy",
                                       "Ảnh hưởng tiếp theo": "dùng chung cho 3"}),
    ("tong-quan", "FL:in>ME", [], {"Nguồn": "Giao dịch tháng", "Cách tính": "ghi có", "Giả định": "đã ghi nhận",
                                   "Độ tin cậy": "Đã ghi nhận", "Ảnh hưởng tiếp theo": "vào"}),
    ("muc-tieu", "SC:rates_up>FL:out", ["rates_up"], {"Nguồn": "Kịch bản", "Cách tính": "dư nợ lãi thả nổi",
                                                      "Giả định": "Lãi suất +2", "Độ tin cậy": "Không có độ tin cậy",
                                                      "Ảnh hưởng tiếp theo": "Tài sản ròng nếu xảy ra"}),
]  # fmt: skip


@pytest.mark.parametrize("lens,edge,active,want", CASES, ids=[c[1].rstrip(":") for c in CASES])
def test_a_picked_edge_says_where_it_comes_from_and_what_it_reaches(open_page, lens, edge, active, want):
    if lens == "tin":
        in_thread(approved, *MARKET)  # news the CIO approved, applied to the client
    p = open_lens(open_page, lens, active)
    if edge.startswith("SC:"):  # an active scenario's fan shows once it is picked
        p.page.click(f'.wnode[data-n="{edge.split(">")[0]}"] .wcore')
        settle(p)
    key = edge if ">" in edge else p.page.evaluate(FIRST, edge)
    if key is None:  # folded behind “+n”: opened first
        p.page.click(f'.wnode[data-n="GR:{edge.rstrip(":").lower().replace("ev", "event")}"]')
        settle(p)
        key = p.page.evaluate(FIRST, edge)
    got = pick(p, key)
    for field, words in want.items():
        assert words in got.get(field, ""), (field, got.get(field))
    a, b = key.split(">")
    ends = p.page.evaluate("""([a, b]) => [a, b].map(i => document.querySelector(`.wnode[data-n="${i}"]`)
      .classList.contains('dim'))""", [a, b])  # fmt: skip
    assert ends == [False, False] and p.page.locator(".wnode.dim").count() > 0  # its ends lit, the rest dimmed
    assert p.page.locator(".wedge.picked").count() == 1
    assert p.page.get_attribute("#ws-tab-i", "aria-selected") == "true"
    p.page.click("#ws-clear")  # unpicked
    p.page.wait_for_selector(".wedge.picked", state="detached")
    assert p.page.locator(".wnode.dim").count() == 0
    assert not p.problems()


def test_an_edge_is_picked_by_keyboard(open_page):
    p = open_lens(open_page, "tong-quan")
    p.page.focus('.whit[data-e="ME>FL:out"]')
    p.page.keyboard.press("Enter")
    p.page.wait_for_selector('.wedge.picked[data-e="ME>FL:out"]', state="attached")
    assert p.page.get_attribute('.whit[data-e="ME>FL:out"]', "aria-pressed") == "true"
    p.page.focus('.whit[data-e="ME>FL:out"]')
    p.page.keyboard.press("Enter")  # again: unpicked
    p.page.wait_for_selector(".wedge.picked", state="detached")
    assert not p.problems()


CATS = """() => [...document.querySelectorAll('.wnode.k-category:not(.off):not(.gone)')].map(n => n.dataset.n)"""


@pytest.mark.parametrize("size", ["desktop", "phone"])
def test_money_in_and_out_open_to_their_categories(open_page, size):
    p = open_lens(open_page, "dong-tien", size=size)
    assert p.page.evaluate(CATS) == []  # on demand only
    for flow in ("FL:out", "FL:in"):
        p.page.click(f'.wnode[data-n="{flow}"] .wcore')
        settle(p)
        cats = p.page.evaluate(CATS)
        side = flow.split(":")[1]
        assert cats and all(c.startswith(f"FC:{side}:") for c in cats), cats
        moving = p.page.evaluate("""() => [...new Set([...document.querySelectorAll('.wspark')].map(q => q.dataset.e))]
          .filter(k => k.includes('FC:'))""")  # fmt: skip
        assert set(moving) == {f"{c}>{flow}" if side == "in" else f"{flow}>{c}" for c in cats}
        amount = p.page.evaluate(
            "() => Object.fromEntries([...document.querySelectorAll('.wspark')].map(q => [q.dataset.e, +q.dataset.m]))"
        )
        month = amount["FL:in>ME" if side == "in" else "ME>FL:out"]
        assert abs(sum(v for k, v in amount.items() if "FC:" in k) - month) <= len(cats)  # they add up to the month
        assert "khoản thu chi" in p.page.inner_text("#ws-pane-i") or "Thu gọn" in p.page.inner_text("#ws-pane-i")
        p.page.click(f'.wnode[data-n="{flow}"] .wcore')  # unpicked: they fold back
        p.page.wait_for_timeout(500)
    assert not p.problems()


def test_goals_sharing_a_pool_say_it_once_against_the_surplus(open_page):
    p = open_lens(open_page, "muc-tieu")
    p.page.click("#ws-tab-i")
    text = p.page.inner_text("#ws-pane-i")
    assert "dùng chung cho 3 mục tiêu" in text and text.count("dùng chung") == 1
    assert "Các mục tiêu cần" in text and "bạn dư" in text
    p.page.click('.wnode[data-n="GL:tuition"] .wcore')
    assert "dùng chung cho 3 mục tiêu" in p.page.inner_text("#ws-pane-i")
    assert not p.problems()


def test_another_members_holdings_carry_their_mark(open_page):
    """Gia đình (F1): one core for the family; a holding or category of another member carries their initial on its
    rim, named on hover, and the person's own carry none."""
    p = open_lens(open_page, "tai-san")
    assert p.page.locator(".wown").count() == 0  # Cá nhân: only the person's own
    p.page.click("text=Gia đình")
    p.page.wait_for_selector(".wnode.k-class")
    for cls in ("CL:stock", "CL:deposit"):  # open the classes: their holdings show
        p.page.click(f'.wnode[data-n="{cls}"] .wcore')
        settle(p)
        marks = p.page.evaluate("""() => [...document.querySelectorAll('.wnode.k-holding .wown')].map(b =>
          [b.getAttribute('aria-label'), b.querySelector('text').textContent])""")  # fmt: skip
        if marks:
            break
    assert marks and all(label.startswith("Của ") and "Nguyễn Minh Khoa" not in label for label, _ in marks), marks
    assert all(len(t) == 1 and t == label.split()[-1][0].upper() for label, t in marks)  # the member's initial
    assert p.page.locator(".wnode.k-family").count() == 1
    assert not p.problems()
