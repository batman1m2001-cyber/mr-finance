"""The Assistant panel's width and reading scale (panel UX, 2026-10-18): a divider between the graph and the dock drags
the dock between a width the conversation reads in and one that leaves the graph its room, folds it past the narrow
end, opens a folded one, answers the keyboard, is kept per browser and resets; a phone has none. The conversation reads
compact: 13 px answers, emphasis below bold, time and sources quieter than the answer, more of it on screen. A turn in
flight says what is happening now."""

import re

DOCK = """() => { const $ = (q) => document.querySelector(q);
  const d = $('.ws-dock').getBoundingClientRect(), c = $('.ws-canvas').getBoundingClientRect();
  const s = $('#ws-split'), r = $('#ws-dock-reset');
  return {dock: Math.round(d.width), canvas: Math.round(c.width), folded: $('.ws').classList.contains('folded'),
          now: +s.getAttribute('aria-valuenow'), max: +s.getAttribute('aria-valuemax'),
          reset: !r.hidden && getComputedStyle(r).display !== 'none', kept: localStorage.getItem('mf.ws.dockw'),
          box: +$('.ws-svg').getAttribute('viewBox').split(' ')[2]}; }"""


def drag(p, dx, steps=12):
    s = p.page.locator("#ws-split").bounding_box()
    x, y = s["x"] + s["width"] / 2, s["y"] + s["height"] / 2
    p.page.mouse.move(x, y)
    p.page.mouse.down()
    for i in range(1, steps + 1):
        p.page.mouse.move(x + dx * i / steps, y)
    p.page.mouse.up()
    p.page.wait_for_timeout(250)  # the graph's one layout after the release
    return p.page.evaluate(DOCK)


def test_the_divider_drags_the_dock_within_bounds_folds_it_and_keeps_it(open_page):
    p = open_page(theme="dark")
    p.go("#/client/xem/tong-quan")
    p.page.wait_for_selector(".wedge")
    st = p.page.evaluate(DOCK)
    assert st["dock"] == 384 and not st["reset"] and st["kept"] is None, st  # the screen's default
    st = drag(p, -200)  # wider
    assert abs(st["dock"] - 584) <= 2 and st["now"] == st["dock"] and st["reset"] and st["kept"] == str(st["dock"]), st
    assert st["box"] == max(720, st["canvas"]), st  # the graph laid out again for its new room, once
    st = drag(p, -2000)  # as wide as it goes: the graph keeps 420 px
    assert st["dock"] == st["max"] == 720 and st["canvas"] >= 420, st  # 720 at most (1440 − 72 − 420 = 948 here)
    st = drag(p, 3000)  # past the narrow end: folded, the width asked for kept
    assert st["folded"] and st["dock"] == 48 and not st["reset"], st
    st = drag(p, -400)  # a folded dock dragged open
    assert not st["folded"] and 400 <= st["dock"] <= 460, st
    width = st["dock"]
    p.page.reload()
    p.page.wait_for_selector(".wedge")
    st = p.page.evaluate(DOCK)
    assert st["dock"] == width and st["reset"], st  # kept per browser
    p.page.click("#ws-dock-reset")
    p.page.wait_for_timeout(200)
    st = p.page.evaluate(DOCK)
    assert st["dock"] == 384 and not st["reset"] and st["kept"] is None, st
    assert not p.problems()


def test_the_divider_answers_the_keyboard_and_a_double_click(open_page):
    p = open_page()
    p.go("#/client/xem/tong-quan")
    p.page.wait_for_selector(".wedge")
    p.page.focus("#ws-split")
    p.page.keyboard.press("ArrowLeft")
    assert p.page.evaluate(DOCK)["dock"] == 400
    p.page.keyboard.press("Shift+ArrowLeft")
    assert p.page.evaluate(DOCK)["dock"] == 464
    p.page.keyboard.press("ArrowRight")
    assert p.page.evaluate(DOCK)["dock"] == 448
    p.page.keyboard.press("Home")
    assert p.page.evaluate(DOCK)["dock"] == 300
    p.page.keyboard.press("End")
    st = p.page.evaluate(DOCK)
    assert st["dock"] == st["max"], st
    p.page.keyboard.press("Enter")  # folds; again opens, at the width it had
    assert p.page.evaluate(DOCK)["folded"]
    p.page.keyboard.press("Enter")
    st = p.page.evaluate(DOCK)
    assert not st["folded"] and st["dock"] == st["max"], st
    p.page.dblclick("#ws-split")
    assert p.page.evaluate(DOCK)["dock"] == 384
    assert p.page.get_attribute("#ws-split", "role") == "separator"
    assert not p.problems()


def test_a_narrower_window_clamps_a_kept_width_and_a_phone_has_no_divider(open_page):
    p = open_page()
    p.go("#/client/xem/tong-quan")
    p.page.wait_for_selector(".wedge")
    p.page.focus("#ws-split")
    p.page.keyboard.press("End")  # 720 at most, here 1440 − 72 − 420 = 948 → 720
    assert p.page.evaluate(DOCK)["dock"] == 720
    p.page.set_viewport_size({"width": 1100, "height": 800})
    p.page.wait_for_timeout(300)
    st = p.page.evaluate(DOCK)
    assert st["dock"] == 1100 - 72 - 420 and st["canvas"] >= 420, st  # the graph keeps its room
    p.page.set_viewport_size({"width": 1440, "height": 900})
    p.page.wait_for_timeout(300)
    assert p.page.evaluate(DOCK)["dock"] == 720  # the width asked for, back when there is room
    q = open_page(size="phone")
    q.go("#/client/xem/tong-quan")
    q.page.wait_for_selector(".wedge")
    assert q.page.is_hidden("#ws-split") and q.page.is_hidden("#ws-dock-reset")
    assert not p.problems() and not q.problems()


READING = """() => { const px = (el, k) => el ? parseFloat(getComputedStyle(el)[k]) : null;
  const $ = (q) => document.querySelector(q), w = (el) => el ? +getComputedStyle(el).fontWeight : null;
  const bot = [...document.querySelectorAll('#cp-msgs .cp-bot')].pop();
  const b = bot && bot.querySelector(':is(.cp-p, .cp-prose) :is(b, strong)');
  const fig = bot && bot.querySelector('.cp-fig b');
  const chip = $('#cp-sugg .chip'), meta = $('#cp-msgs .cp-meta, #cp-msgs .cp-steps');
  return {fig: w(fig), bold: w(b), answer: px(bot, 'fontSize'), lh: px(bot, 'lineHeight') / px(bot, 'fontSize'),
          chip: px(chip, 'fontSize'), meta: px(meta, 'fontSize'), input: px($('#cp-q'), 'fontSize'),
          figures: bot ? getComputedStyle(bot).fontVariantNumeric : null,
          room: $('#cp-msgs').getBoundingClientRect().height / $('.ws-dock').getBoundingClientRect().height}; }"""


ANSWERED = """() => { const b = [...document.querySelectorAll('#cp-msgs .cp-bot')].pop();
  return b && !b.hasAttribute('data-busy') && b.innerText.trim().length > 20; }"""


def test_the_conversation_reads_compact_and_its_parts_step_back(open_page):
    for size in ("desktop", "phone"):
        p = open_page(size=size)
        p.go("#/client/xem/tong-quan")
        p.page.wait_for_selector(".wedge")
        if size == "phone":
            p.page.click(".ws-ask")
        p.page.fill("#cp-q", "Tài sản của tôi thế nào?")  # no model in tests: the app's own tool answers (fallback)
        p.page.press("#cp-q", "Enter")
        p.page.wait_for_function(ANSWERED)
        r = p.page.evaluate(READING)
        assert r["answer"] == (13 if size == "desktop" else 14) and 1.5 <= r["lh"] <= 1.6, (size, r)
        assert r["bold"] is None or r["bold"] <= 600, (size, r)  # emphasis in the prose, not shouting
        assert r["fig"] is None or r["fig"] > (r["bold"] or 400), (size, r)  # a card's figure stands out from the prose
        assert r["meta"] is None or r["meta"] < r["answer"], (size, r)  # time, sources and steps step back
        assert r["chip"] < r["answer"] or size == "phone", (size, r)
        assert "tabular-nums" in r["figures"], (size, r)  # figures line up
        if size == "desktop":
            assert r["room"] >= 0.45, r  # the conversation has the dock's height, not the chrome (was 0.34)
        else:
            assert r["input"] >= 16, r  # a phone does not zoom the page when the box takes focus
        assert not p.problems()


PROGRESS = """() => { window.__prog = []; let last = '';
  new MutationObserver(() => { const b = document.querySelector('#cp-msgs [data-busy]'); if (!b) return;
    const rows = [...b.querySelectorAll('.cp-prog-r')].map(r => ({st: r.classList.contains('run') ? 'run'
      : r.classList.contains('ok') ? 'ok' : 'bad', text: r.innerText.replace(/\\s+/g, ' ').trim()}));
    const k = JSON.stringify(rows); if (k !== last) { last = k; window.__prog.push(rows); } })
  .observe(document.querySelector('#cp-msgs'), {subtree: true, childList: true, characterData: true}); }"""


def test_the_turn_in_flight_says_what_is_happening_in_the_servers_words_only(open_page):
    """The owner (2026-10-18): between the tool and the answer's first words nothing said what was happening, and a
    bare “Dòng tiền” says too little. The turn in flight is a short list: the question understood, each step in the
    server's sentence (assistant/progress.py) and its time, then the results read and the answer written. A tool's
    id, arguments or result never show."""
    p = open_page()
    p.go("#/client/xem/tong-quan")
    p.page.wait_for_selector(".wedge")
    p.page.evaluate(PROGRESS)
    p.page.fill("#cp-q", "Dòng tiền tháng này thế nào?")  # no model in tests: the fallback calls the cash-flow tool
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_function(ANSWERED)
    states = p.page.evaluate("window.__prog")
    assert states and states[0] == [{"st": "run", "text": "Đang hiểu câu hỏi · đang chạy"}], states[:2]
    rows = [r for s in states for r in s]
    # the step in a sentence (the fallback answers within one redraw, so its done row may never be drawn)
    assert any(re.match(r"(Đang|✓ Đã) xem tiền vào, tiền ra", r["text"]) for r in rows), rows
    assert any(r["st"] == "ok" and re.match(r"✓ Đã hiểu câu hỏi .*\d,\d s$", r["text"]) for r in rows), rows
    assert all(not re.search(r"[a-z]+_[a-z_]+|\{|C0\d", r["text"]) for r in rows), rows  # no id, argument, client
    assert all(sum(r["st"] == "run" for r in s) <= 1 for s in states), states  # one thing happening at a time
    assert not p.problems()
