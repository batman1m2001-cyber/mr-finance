"""Tài khoản và vai trò (Q-25; owner 2026-10-18, docs/OWNER_BACKLOG_1018_PLAN.md U): Admin files a new account from
the page; the proposer cannot approve it; a second Admin approves it and sees the one-time code once; the new person
sets a password with that code on the sign-in page and lands on their own role. Desktop and phone, no error and no
sideways scroll."""

import pytest


@pytest.mark.parametrize("size", ["desktop", "phone"])
def test_two_admins_add_an_account_and_its_code_signs_the_person_in(open_page, size):
    email = f"thu.pham.{size}@onewealth.example"
    p = open_page(size)
    p.go("#/admin/tai-khoan")
    page = p.page
    assert page.locator('#acc-people [data-person="sp_global"] [data-kind]').count() == 0  # a demo persona: kept
    page.fill("#acc-add-form [name=full_name]", "Phạm Minh Thư")
    page.fill("#acc-add-form [name=email]", email)
    page.select_option("#acc-add-form [name=role]", "rm")
    page.click("#acc-add-form [type=submit]")
    row = f"#acc-requests .item:has-text('{email}')"
    page.wait_for_selector(row)
    assert page.locator(f"{row} [data-decide=approve]").count() == 0  # one does not approve one's own request
    assert "Chờ một Quản trị khác duyệt" in page.inner_text(row)

    r = p.ctx.request.post(f"{p.base}/api/auth/demo", data={"id": "admin2"})
    assert r.ok, r.text()
    page.reload()
    page.wait_for_selector(f"{row} [data-decide=approve]")
    page.click(f"{row} [data-decide=approve]")
    page.wait_for_selector("#acc-code")
    code = page.inner_text("#acc-code .mono").strip()
    assert len(code) == 10
    assert not p.problems()

    page.click(".me button")  # sign out
    page.wait_for_selector("#signin-form")
    page.click("#signin-code summary")
    page.fill("[name=login]", email)
    page.fill("[name=code]", code)
    page.fill("[name=new_password]", "mat-khau-moi-1")
    page.click("#signin-redeem")
    page.wait_for_function("location.hash.startsWith('#/rm') && document.querySelector('#nav a')")
    assert "Phạm Minh Thư" in page.inner_text(".me")
    assert not [e for e in p.problems() if "401" not in e], p.problems()
