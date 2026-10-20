"""Sign-in in the browser (BRD-RULE-SEC-01): without a session only the sign-in page shows; a wrong password is
refused in words; the form and a demo account both open the person's own role; signing out ends the session."""

from conftest import SIZES


def test_sign_in_with_the_form_and_with_a_demo_account_then_sign_out(browser, base_url, monkeypatch):
    monkeypatch.setenv("MF_DEMO_PASSWORD", "mat-khau-demo")
    for size in SIZES:
        w, h = SIZES[size]
        ctx = browser.new_context(viewport={"width": w, "height": h})
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e, errors=errors: errors.append(str(e)))
        page.goto(f"{base_url}/#/cio")
        page.wait_for_selector("#signin-form")
        assert page.is_hidden("#nav a") and page.is_hidden(".cp-panel")  # nothing of the app before sign-in
        assert page.locator(".demo-acc").count() >= 10
        page.fill("[name=login]", "huy.tran@tcbwealth.example")
        page.fill("[name=password]", "sai-mat-khau")
        page.click("#signin-form [type=submit]")
        page.wait_for_function("document.querySelector('#signin-err').textContent.length > 0")
        page.fill("[name=password]", "mat-khau-demo")
        page.click("#signin-form [type=submit]")
        page.wait_for_function("location.hash.startsWith('#/cio') && document.querySelector('#nav a')")
        assert "Trần Quang Huy" in page.inner_text(".me")
        if page.is_visible("#me-open"):  # a phone: the name row is a popover behind the initials
            page.click("#me-open")
        page.click(".me button")
        page.wait_for_selector("#signin-form")
        page.click(".demo-acc[data-acc=C01]")
        page.wait_for_function("location.hash.startsWith('#/client') && document.querySelector('#nav a')")
        assert page.is_hidden("#client-pick")  # a customer has no one else to pick
        sw, iw = page.evaluate("[document.documentElement.scrollWidth, innerWidth]")
        assert sw <= iw, size
        page.goto(f"{base_url}/?again=1#/cio")  # a customer who types another role's address gets their own
        page.wait_for_function("location.hash.startsWith('#/client') && document.querySelector('#nav a')")
        assert not errors, errors
        ctx.close()
