"""Each staff role's desk in the browser (FEAT-41, ADR-0036, OWN-MR-01…12): the desk is the role's home; every page
of its menu opens as a sheet at its old address, with its group's tabs, and back; a stage picked lists its items in
Thông tin; the role's assistant is docked and its step lights what it reads (a scripted stream through the real
panel); another role never sees the desk; phone and dark; the Customer's workspace is untouched."""

import json
import re
from pathlib import Path

from conftest import in_thread
from test_apply import MARKET, approved
from test_role_desks import pending_view

WEB = Path(__file__).resolve().parents[2] / "web"

TIMED = """(() => { const real = window.fetch;
  window.fetch = (url, opts) => {
    if (!String(url).includes('/api/assistant/stream')) return real(url, opts);
    window.__body = JSON.parse(opts.body);
    const enc = new TextEncoder(), ev = window.__script || [];
    const body = new ReadableStream({start(c) { let n = 0;
      for (const [t, e] of ev) setTimeout(() => {
        c.enqueue(enc.encode(`id: ${++n}\\ndata: ${JSON.stringify(e)}\\n\\n`));
        if (e.type === 'answer') c.close(); }, t); }});
    return Promise.resolve(new Response(body, {status: 200, headers: {'content-type': 'text/event-stream'}}));
  }; })();"""
STEP = {"type": "step", "call_id": "c1", "tool": "ban_quyet_dinh", "label": "Decision board"}
SCRIPT = [
    [0, {"type": "start"}],
    [50, {**STEP, "phase": "start", "nodes": ["decide", "stage:views", "stage:runs"]}],
    [700, {**STEP, "phase": "end", "ok": True, "ms": 640}],
    [1200, {"type": "answer", "assistant": {"status": "ok", "mode": "model", "text": "Một nhận định chờ bạn duyệt.",
                                            "steps": []}}],
]  # fmt: skip


SUB = re.compile(r'\{id: "([a-z-]+)", label: "[^"]+", page:')


def routes(role):
    """Every old address of ``role``'s menu (web/shell.js), a sub-menu's pages each, the desk's own entry left out."""
    shell = (WEB / "shell.js").read_text(encoding="utf-8")
    block = re.split(r"\n  [a-z]+: \{", shell.split(f"\n  {role}: {{", 1)[1], maxsplit=1)[0]
    out = []
    for line in block.splitlines():
        top = re.match(r'^      \{id: "([a-z-]+)"', line)
        if top and "desk: true" not in line:
            out.append((top.group(1), SUB.findall(line.split("sub: [", 1)[1]) if "sub: [" in line else []))
        elif out and line.startswith("        {id:"):
            out[-1][1].extend(SUB.findall(line))
    return [f"#/{role}/{i}/{s}" for i, subs in out for s in subs] + [f"#/{role}/{i}" for i, subs in out if not subs]


def test_the_cio_works_at_its_desk_and_every_page_is_a_sheet(open_page):
    in_thread(approved, *MARKET)
    p = open_page()
    p.go("#/cio")
    p.page.wait_for_selector(".desk-cio .dk-stage")
    assert p.page.is_hidden("#nav") and p.page.locator(".cp-fab").count() == 0  # the rail and the docked assistant
    assert p.page.locator(".dk-stage").count() == 5  # no Sự kiện (OWN-FB-08)
    assert p.page.get_attribute('[data-tool="ban"]', "aria-current") is not None
    assert p.page.locator("#ws-pane-a #cp-q").count() == 1  # the CIO's assistant, docked

    # a stage picked lists its items in Thông tin, each opening its page
    p.page.click('[data-stage="runs"]')
    p.page.wait_for_selector("#ws-pane-i:not([hidden]) .dk-row")
    assert "Lần áp dụng" in p.page.inner_text("#ws-pane-i") and "AR-" not in p.page.inner_text(
        "#ws-pane-i"
    )  # named by its news (OWN-FB-12)

    # every page of the old menu, at its old address, opens as a sheet over the desk with its group's tabs
    seen = routes("cio")
    assert len(seen) >= 14
    for r in seen:
        p.go(r)
        assert p.page.is_visible("#ws-sheet"), r
        named = p.page.inner_text("#ws-sheet-t").strip() or p.page.locator("#dk-tabs a[aria-current]").count() == 1
        assert named, r  # a sheet with tabs is named by its current tab, not a title (OWN-FB-14)
        assert p.page.locator("#ws-sheet-b #page").count() == 1
        assert p.page.locator(".ws-tool[aria-current]").count() == 1, r
        assert not p.problems(), (r, p.problems())
    p.go("#/cio/do-thi")
    tabs = p.page.eval_on_selector_all("#dk-tabs a", "as => as.map(a => a.getAttribute('href'))")
    assert tabs == ["#/cio/phoi-nhiem", "#/cio/do-thi"]  # OWN-FB-14
    p.page.click("#ws-sheet-x")
    p.page.wait_for_function("document.querySelector('#ws-sheet').hidden && location.hash === '#/cio'")
    assert not p.problems()


def test_a_view_waiting_opens_from_the_queue_with_its_approval(open_page):
    _, view = in_thread(pending_view, "Lãi suất liên ngân hàng tăng")
    p = open_page()
    p.go("#/cio")
    p.page.wait_for_selector(".desk-cio .dk-stage")
    assert p.page.inner_text('[data-stage="views"] .dk-badge') == "1"
    row = f'[data-node="decide"] a.dk-row[href="#/cio/nhan-dinh/{view["id"]}"]'
    p.page.click(row)
    p.page.wait_for_selector('#ws-sheet:not([hidden]) [data-act="approve"]')  # the approval, as on the page
    assert p.page.inner_text("#ws-sheet-t") == "Sự kiện & nhận định"
    assert not p.problems()


def test_the_cio_assistant_lights_what_it_reads_on_the_desk(open_page):
    p = open_page(theme="dark")
    p.ctx.add_init_script(TIMED)
    p.ctx.add_init_script(f"window.__script = {json.dumps(SCRIPT)};")
    p.go("#/cio")
    p.page.wait_for_selector(".desk-cio .dk-stage")
    p.page.fill("#cp-q", "Có gì chờ tôi duyệt?")
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_selector('[data-node="decide"].act', timeout=4000)  # while the step runs
    p.page.wait_for_selector('[data-node="stage:views"].lit', timeout=6000)  # kept once answered
    assert p.page.locator('[data-node="decide"].act').count() == 0
    assert p.page.evaluate("window.__body.role") == "cio"  # the CIO's assistant, not the Customer's
    assert not p.problems()


def test_no_other_role_reaches_the_cio_desk(open_page):
    p = open_page()
    for role in ("rm", "admin"):
        p.as_role(role)
        p.page.evaluate("location.hash = '#/cio'")
        p.page.wait_for_timeout(400)
        assert p.page.locator(".desk-cio").count() == 0, role
        assert not p.page.url.endswith("#/cio"), role
    p.errors.clear()  # the 403s asked for on the way are the refusals under test


def test_the_desk_on_a_phone_and_dark_and_the_customer_untouched(open_page):
    in_thread(approved, *MARKET)
    for theme in ("dark", "light"):
        p = open_page(size="phone", theme=theme)
        p.go("#/cio")
        p.page.wait_for_selector(".desk-cio .dk-stage")
        assert not p.problems(), (theme, p.problems())
        p.go("#/cio/phoi-nhiem")
        assert p.page.is_visible("#ws-sheet") and not p.problems(), (theme, p.problems())
    p = open_page()
    p.go("#/cio")
    p.page.wait_for_selector(".desk-cio")
    p.go("#/client/xem/tong-quan")  # the graph: a page of Tổng quan now (B3.1)
    p.page.wait_for_selector(".wnode.k-family")
    assert p.page.locator(".desk").count() == 0 and p.page.locator(".ws").count() == 1
    assert p.page.is_hidden("#nav") and not p.problems()


# -- RM · Sổ khách hàng (M2) ---------------------------------------------------------------------------------------


def test_the_rm_works_at_its_book_and_every_page_is_a_sheet(open_page):
    in_thread(approved, *MARKET)
    p = open_page()
    p.go("#/rm")
    p.page.wait_for_selector(".desk-rm [data-fam]")
    assert p.page.is_hidden("#nav") and p.page.locator("#ws-pane-a #cp-q").count() == 1
    fams = p.page.eval_on_selector_all(".desk-rm [data-fam]", "gs => [...new Set(gs.map(g => g.dataset.fam))].sort()")
    assert fams == ["C01", "C04", "C05"]  # rm01's own families, nobody else's

    # a family picked: its card in Thông tin; a page opened from it sets the client picker first
    p.page.click('.desk-rm [data-fam="C04"]')
    p.page.wait_for_selector("#ws-pane-i:not([hidden]) [data-go]")
    assert "Đỗ Thị Hạnh" in p.page.inner_text("#ws-pane-i")
    p.page.click('#ws-pane-i [data-go="#/rm/khach-hang/tac-dong"]')
    p.page.wait_for_function("location.hash.endsWith('/tac-dong') && !document.querySelector('#ws-sheet').hidden")
    p.page.wait_for_function("document.querySelector('#client').value === 'C04'")

    seen = routes("rm")
    assert len(seen) == 5  # the client's pages are tabs of Khách hàng (OWN-FB-02…05)
    for r in seen:
        p.go(r)
        assert p.page.is_visible("#ws-sheet"), r
        assert p.page.locator(".ws-tool[aria-current]").count() == 1, r
        assert not p.problems(), (r, p.problems())
    p.go("#/rm/khach-hang/ke-hoach")
    assert p.page.locator("#dk-tabs a").count() == 4 and not p.page.is_hidden("#client-pick")
    p.go("#/rm")
    assert p.page.is_hidden("#ws-sheet") and not p.problems()


def test_the_rm_assistant_lights_the_book(open_page):
    script = [[0, {"type": "start"}],
              [50, {**STEP, "tool": "so_khach_hang", "phase": "start", "nodes": ["book", "calls"]}],
              [700, {**STEP, "tool": "so_khach_hang", "phase": "end", "ok": True, "ms": 600}],
              [1200, {"type": "answer", "assistant": {"status": "ok", "mode": "model", "text": "Không ai cần gọi ngay.",
                                                      "steps": []}}]]  # fmt: skip
    p = open_page()
    p.ctx.add_init_script(TIMED)
    p.ctx.add_init_script(f"window.__script = {json.dumps(script)};")
    p.go("#/rm")
    p.page.wait_for_selector(".desk-rm [data-fam]")
    assert "Sổ khách hàng có gì cần làm?" in p.page.inner_text("#ws-pane-a")  # the RM's own suggestions
    p.page.fill("#cp-q", "Sổ khách hàng có gì cần làm?")
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_selector('[data-node="book"].act', timeout=4000)
    p.page.wait_for_selector('[data-node="calls"].lit', timeout=6000)
    assert p.page.evaluate("window.__body.role") == "rm" and not p.problems()


def test_no_other_role_reaches_the_rm_book_and_the_rm_on_a_phone(open_page):
    p = open_page()
    for role in ("cio", "admin"):
        p.as_role(role)
        p.page.evaluate("location.hash = '#/rm'")
        p.page.wait_for_timeout(400)
        assert p.page.locator(".desk-rm").count() == 0, role
    p.errors.clear()
    for theme in ("dark", "light"):
        q = open_page(size="phone", theme=theme)
        q.go("#/rm")
        q.page.wait_for_selector(".desk-rm [data-fam]")
        assert not q.problems(), (theme, q.problems())
        q.go("#/rm/khach-hang/tac-dong")
        assert q.page.is_visible("#ws-sheet") and not q.problems(), (theme, q.problems())


# -- Admin · Vận hành (M3) -----------------------------------------------------------------------------------------


def test_admin_works_at_the_operations_map_and_every_page_is_a_sheet(open_page):
    p = open_page()
    p.go("#/admin")
    p.page.wait_for_selector(".desk-admin .ad-node")
    lanes = p.page.eval_on_selector_all(".ad-lane-t", "hs => hs.map(h => h.textContent)")
    assert [x.lower() for x in lanes] == ["nguồn", "lưu trữ", "ai", "con người"]
    assert p.page.locator(".ad-node").count() == 10 and p.page.locator("#ws-pane-a #cp-q").count() == 1
    p.page.click('[data-n="chain"]')
    p.page.wait_for_selector("#ws-pane-i:not([hidden]) a.btn")
    assert "Chuỗi nhật ký" in p.page.inner_text("#ws-pane-i")
    p.page.click("#ws-pane-i a.btn")
    p.page.wait_for_function("location.hash === '#/admin/nhat-ky' && !document.querySelector('#ws-sheet').hidden")
    seen = routes("admin")
    assert len(seen) == 13  # Việc nền, Tài khoản (owner 2026-10-18); Mô hình, Đo lường from the CIO (OWN-FB-15); Nguồn tin (N1)
    for r in seen:
        p.go(r)
        assert p.page.is_visible("#ws-sheet"), r
        assert p.page.locator(".ws-tool[aria-current]").count() == 1, r
        assert not p.problems(), (r, p.problems())


def test_the_admin_assistant_lights_the_map(open_page):
    script = [[0, {"type": "start"}],
              [50, {**STEP, "tool": "chuoi_nhat_ky", "phase": "start", "nodes": ["chain", "node:chain"]}],
              [700, {**STEP, "tool": "chuoi_nhat_ky", "phase": "end", "ok": True, "ms": 600}],
              [1200, {"type": "answer", "assistant": {"status": "ok", "mode": "model", "text": "Chuỗi nguyên vẹn.",
                                                      "steps": []}}]]  # fmt: skip
    p = open_page(theme="dark")
    p.ctx.add_init_script(TIMED)
    p.ctx.add_init_script(f"window.__script = {json.dumps(script)};")
    p.go("#/admin")
    p.page.wait_for_selector(".desk-admin .ad-node")
    assert "Hệ thống có gì bất thường?" in p.page.inner_text("#ws-pane-a")
    p.page.fill("#cp-q", "Chuỗi nhật ký còn nguyên không?")
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_selector('[data-node="node:chain"].act', timeout=4000)
    p.page.wait_for_selector('[data-node="chain"].lit', timeout=6000)
    assert p.page.evaluate("window.__body.role") == "admin" and not p.problems()


def test_no_other_role_reaches_the_operations_map_and_admin_on_a_phone(open_page):
    p = open_page()
    for role in ("cio", "rm"):
        p.as_role(role)
        p.page.evaluate("location.hash = '#/admin'")
        p.page.wait_for_timeout(400)
        assert p.page.locator(".desk-admin").count() == 0, role
    p.errors.clear()
    q = open_page(size="phone", theme="dark")
    q.go("#/admin")
    q.page.wait_for_selector(".desk-admin .ad-node")
    assert not q.problems(), q.problems()
    q.go("#/admin/he-thong")
    assert q.page.is_visible("#ws-sheet") and not q.problems(), q.problems()


# -- Compliance and the specialists are retired (OWN-FB-18) --------------------------------------------------------


def test_the_retired_desks_open_for_no_one(open_page):
    p = open_page()
    for role in ("cio", "rm", "admin"):
        p.as_role(role)
        for gone in ("specialist", "compliance"):
            p.page.evaluate(f"location.hash = '#/{gone}'")
            p.page.wait_for_timeout(400)
            assert p.page.locator(f".desk-{gone}").count() == 0, (role, gone)
            assert not p.page.url.endswith(f"#/{gone}"), (role, gone)
    p.errors.clear()  # the 403s asked for on the way are the refusals under test
