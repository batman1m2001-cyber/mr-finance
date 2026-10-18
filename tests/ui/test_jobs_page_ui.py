"""Việc nền (owner 2026-10-18, docs/OWNER_BACKLOG_1018_PLAN.md A): CIO, Admin and Compliance each open it from their
menu; Admin's “Chạy ngay” runs a job and the run shows under Lần chạy tay; the CIO and Compliance get no job button;
desktop and phone, no error and no sideways scroll."""

import pytest

from control import jobs


class Rec:
    run_id, items, failed, timed_out, errors = "R-1", [object()], [], [], {}


class FakeJob:
    name = "audit_check"

    async def run(self, **kw):
        return Rec()


@pytest.mark.parametrize("size", ["desktop", "phone"])
def test_admin_runs_a_job_from_viec_nen(open_page, size, monkeypatch):
    monkeypatch.setitem(jobs._JOBS, "audit_check", FakeJob())
    p = open_page(size)
    p.go("#/admin/viec-nen")
    page = p.page
    assert (
        page.locator("#jobs-schedule [data-job]").count()
        == len([j for j in jobs.RUNNABLE if page.locator(f'[data-job="{j}"]').count()])
        > 0
    )
    page.click('[data-job="audit_check"]')
    done = "(t => t && /Xong/.test(t.innerText))(document.querySelector('#jobs-manual .item'))"
    page.wait_for_function(done, timeout=10000)
    assert "Kiểm tra chuỗi nhật ký" in page.locator("#jobs-manual .item").first.inner_text()
    assert not p.problems()


@pytest.mark.parametrize("role", ["cio", "compliance"])
def test_the_cio_and_compliance_read_viec_nen_without_job_buttons(open_page, role):
    p = open_page("desktop")
    p.go(f"#/{role}/viec-nen")
    assert p.page.locator("#jobs-agents").count() == 1 and p.page.locator("[data-job]").count() == 0
    assert p.page.locator(f'#nav a[href="#/{role}/viec-nen"]').count() >= 1
    assert not p.problems()
