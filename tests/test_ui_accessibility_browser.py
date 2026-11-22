"""Q04: real engines, keyboard/error recovery and responsive user journeys."""

import os
from pathlib import Path
from urllib.parse import urlparse

import pytest
from playwright.sync_api import expect

from tests.test_requests_browser import login
from tests.ui_qa import ui_site as security_site  # noqa: F401


@pytest.fixture(scope="session")
def connect_options():
    endpoint = os.environ.get("Q04_PLAYWRIGHT_ENDPOINT")
    if not endpoint:
        return None
    parsed = urlparse(endpoint)
    if parsed.scheme != "ws" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("QA browser endpoint must be loopback ws")
    return {"endpoint": endpoint, "expose_network": "<loopback>"}


def no_overflow(page):
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def assert_reachable(control):
    control.focus()
    control.scroll_into_view_if_needed()
    expect(control).to_be_focused()
    control.page.wait_for_function("""() => {
      const e=document.activeElement, r=e.getBoundingClientRect();
      return r.top>=0 && r.bottom<=innerHeight &&
        e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));
    }""")


def evidence(page, name):
    if os.environ.get("UPDATE_EVIDENCE") == "1":
        directory = Path("docs/evidence/Q04-U03/screenshots")
        directory.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(directory / name), full_page=False, animations="disabled")


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 390, 768, 1440])
def test_responsive_journey(page, security_site, width):  # noqa: F811
    url, password, _, _ = security_site
    page.set_viewport_size({"width": width, "height": 1000})
    login(page, url, "student.one", password)
    for path in ("/", "/profile/", "/schedule/", "/grades/", "/session/", "/notifications/"):
        response = page.goto(url + path)
        assert response.status == 200
        no_overflow(page)
    page.goto(url + "/requests/new/")
    page.get_by_label("Назначение справки").select_option("other")
    text = "ДлинноеВымышленноеНазвание" * 30
    page.get_by_label("Пояснение", exact=False).fill(text)
    page.get_by_role("button", name="Отправить заявку", exact=True).click()
    expect(page.locator(".request-status")).to_have_text("Отправлена")
    detail = page.url
    no_overflow(page)
    evidence(page, f"request-{width}.png")
    page.reload()
    expect(page.locator(".request-comment").first).to_have_text(text)
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "operator.demo", password)
    page.get_by_role("link", name="Справка об обучении", exact=True).first.click()
    page.get_by_role("button", name="Принять в работу", exact=True).click()
    page.get_by_label("Новый статус").select_option("ready")
    page.get_by_role("button", name="Сохранить статус", exact=True).click()
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.one", password)
    page.goto(detail)
    expect(page.locator(".request-status")).to_have_text("Готова")
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.two", password)
    assert page.goto(detail).status == 404


@pytest.mark.browser
def test_keyboard_validation_and_reflow(page, security_site):  # noqa: F811
    url, password, _, _ = security_site
    page.set_viewport_size({"width": 360, "height": 900})
    page.goto(url + "/login/")
    page.keyboard.press("Tab")
    expect(page.locator(".skip-link")).to_be_focused()
    page.keyboard.press("Enter")
    page.wait_for_url("**/login/#main")
    expect(page.locator("#main")).to_be_focused()
    field = page.get_by_label("Логин", exact=True)
    assert field.evaluate("e => getComputedStyle(e).cursor") == "text"
    assert (
        field.evaluate("""e => {
        const css = getComputedStyle(e);
        const lum = value => {
          const rgb = value.match(/[0-9.]+/g).slice(0,3).map(Number).map(v => {
            v /= 255; return v <= .04045 ? v / 12.92 : ((v+.055)/1.055)**2.4;
          }); return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;
        };
        const a=lum(css.color), b=lum(css.backgroundColor);
        return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
    }""")
        >= 4.5
    )
    field.fill("student.one")
    page.get_by_label("Пароль", exact=True).fill("incorrect-fictional")
    expect(page.locator("#main")).not_to_be_focused()
    page.get_by_label("Пароль", exact=True).press("Enter", no_wait_after=True)
    expect(page.locator("[data-error-summary]")).to_be_focused()
    expect(field).to_have_attribute("aria-invalid", "true")
    evidence(page, "login-error-360.png")
    login(page, url, "student.one", password)
    page.goto(url + "/requests/new/")
    # Remove only native constraints to exercise actual server validation.
    page.get_by_label("Пояснение", exact=False).evaluate("e => e.removeAttribute('maxlength')")
    page.get_by_label("Пояснение", exact=False).fill("я" * 1001)
    page.get_by_role("button", name="Отправить заявку", exact=True).click()
    expect(page.locator("[data-error-summary]")).to_be_focused(timeout=15000)
    expect(page.get_by_label("Пояснение", exact=False)).to_have_attribute("aria-invalid", "true")
    no_overflow(page)
    submit = page.get_by_role("button", name="Отправить заявку", exact=True)
    assert_reachable(submit)
    evidence(page, "request-error-360.png")
    # Equivalent CSS reflow viewport, not device scale or an assertion of OS zoom.
    page.set_viewport_size({"width": 720, "height": 500})
    no_overflow(page)
    assert_reachable(submit)
    page.emulate_media(reduced_motion="reduce")
    assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
    assert page.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == "auto"
    for selector in ("button[type=submit]", "select", "textarea"):
        control = page.locator(selector).first
        control.focus()
        assert control.evaluate("e => getComputedStyle(e).outlineStyle") != "none"


@pytest.mark.browser
def test_skip_link_above_navigation(page, security_site):  # noqa: F811
    url, password, _, _ = security_site
    page.set_viewport_size({"width": 1440, "height": 1000})
    login(page, url, "student.one", password)
    page.goto(url + "/profile/")
    page.keyboard.press("Tab")
    skip = page.locator(".skip-link")
    expect(skip).to_be_focused()
    assert skip.evaluate("""e => { const r = e.getBoundingClientRect();
        return e.contains(document.elementFromPoint(r.x+r.width/2, r.y+r.height/2)); }""")
    evidence(page, "keyboard-1440.png")


@pytest.mark.browser
def test_native_post_network_retry_and_empty_states(page, security_site):  # noqa: F811
    import psycopg

    url, password, db_name, db = security_site
    login(page, url, "student.two", password)
    page.goto(url + "/requests/")
    page.goto(url + "/requests/?status=rejected")
    expect(page.get_by_role("heading", name="Пока нет заявок")).to_be_visible()
    expect(
        page.get_by_text("Выберите другой статус, чтобы увидеть остальные обращения.")
    ).to_be_visible()
    no_overflow(page)
    page.goto(url + "/schedule/?date=2040-01-02")
    expect(page.get_by_role("heading", name="Занятий на этот период нет")).to_be_visible()
    no_overflow(page)
    page.goto(url + "/requests/new/")
    page.get_by_label("Пояснение", exact=False).fill("Повтор после ошибки сети")
    with psycopg.connect(dbname=db_name, **db) as connection:
        before = connection.execute("SELECT count(*) FROM requests_servicerequest").fetchone()[0]
    # A native POST failure opens the engine's error document, not a fake success.
    page.route(
        "**/requests/new/",
        lambda route: (
            route.abort("internetdisconnected")
            if route.request.method == "POST"
            else route.continue_()
        ),
    )
    page.get_by_role("button", name="Отправить заявку", exact=True).click()
    assert page.locator(".request-status").count() == 0
    with psycopg.connect(dbname=db_name, **db) as connection:
        assert (
            connection.execute("SELECT count(*) FROM requests_servicerequest").fetchone()[0]
            == before
        )
    page.unroute("**/requests/new/")
    page.goto(url + "/requests/new/")
    button = page.get_by_role("button", name="Отправить заявку", exact=True)
    expect(button).to_be_enabled()
    button.click()
    expect(page.locator(".request-status")).to_have_text("Отправлена")
    page.reload()
    expect(page.locator(".request-status")).to_have_text("Отправлена")


@pytest.mark.browser
def test_operator_validation(page, security_site):  # noqa: F811
    url, password, _, _ = security_site
    login(page, url, "student.one", password)
    page.goto(url + "/requests/new/")
    page.get_by_role("button", name="Отправить заявку", exact=True).click()
    detail = page.url
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "operator.demo", password)
    page.goto(detail.replace("/requests/", "/operator/requests/"))
    page.get_by_role("button", name="Принять в работу", exact=True).click()
    page.get_by_label("Новый статус").select_option("rejected")
    page.get_by_role("button", name="Сохранить статус", exact=True).click()
    expect(page.locator("[data-error-summary]")).to_be_focused(timeout=15000)
    expect(page.get_by_label("Комментарий для студента", exact=False)).to_have_attribute(
        "aria-invalid", "true"
    )
    expect(page.locator(".request-status")).to_have_text("В работе")


@pytest.mark.browser
def test_response_lost_after_commit_is_saved_and_retry_deduplicated(page, security_site):  # noqa: F811
    import psycopg

    url, password, db_name, db = security_site
    login(page, url, "student.one", password)
    page.goto(url + "/requests/new/")
    page.get_by_label("Пояснение", exact=False).fill("Ответ потерян после сохранения")
    posted = []

    def lose_response(route):
        if route.request.method != "POST":
            route.continue_()
            return
        posted.append(route.request.post_data)
        headers = {
            key: value
            for key, value in route.request.all_headers().items()
            if key != "content-length"
        }
        response = route.fetch(headers=headers, max_redirects=0)
        assert response.status == 302
        route.abort("connectionfailed")

    with psycopg.connect(dbname=db_name, **db) as connection:
        before = connection.execute("SELECT count(*) FROM requests_servicerequest").fetchone()[0]
    page.route("**/requests/new/", lose_response)
    page.get_by_role("button", name="Отправить заявку", exact=True).click()
    assert page.locator(".request-status").count() == 0
    page.unroute("**/requests/new/")
    page.goto(url + "/requests/")
    page.get_by_role("link", name="Справка об обучении", exact=True).first.click()
    expect(page.locator(".request-comment").first).to_have_text("Ответ потерян после сохранения")
    # Same native form body, CSRF and submission_key, using authenticated HTTP context.
    response = page.request.post(
        url + "/requests/new/",
        data=posted[0],
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.ok
    assert response.url == page.url
    with psycopg.connect(dbname=db_name, **db) as connection:
        assert (
            connection.execute("SELECT count(*) FROM requests_servicerequest").fetchone()[0]
            == before + 1
        )


@pytest.mark.browser
def test_stale_cancel_explains_conflict(browser, security_site):  # noqa: F811
    url, password, _, _ = security_site
    student = browser.new_context()
    operator = browser.new_context()
    try:
        page = student.new_page()
        login(page, url, "student.one", password)
        page.goto(url + "/requests/new/")
        page.get_by_role("button", name="Отправить заявку", exact=True).click()
        detail = page.url
        other = operator.new_page()
        login(other, url, "operator.demo", password)
        other.goto(detail.replace("/requests/", "/operator/requests/"))
        other.get_by_role("button", name="Принять в работу", exact=True).click()
        with page.expect_response(lambda response: response.request.method == "POST") as result:
            page.get_by_role("button", name="Отменить заявку", exact=True).click()
        assert result.value.status == 409
        expect(page.locator("[data-error-summary]")).to_be_focused()
        expect(page.get_by_role("link", name="Обновить карточку", exact=True)).to_be_visible()
        expect(page.locator(".request-status")).to_have_text("В работе")
    finally:
        student.close()
        operator.close()


@pytest.mark.browser
def test_stale_operator_active_form_refreshes_version(browser, security_site):  # noqa: F811
    url, password, _, _ = security_site
    first = browser.new_context()
    second = browser.new_context()
    try:
        page = first.new_page()
        login(page, url, "student.one", password)
        page.goto(url + "/requests/new/")
        page.get_by_role("button", name="Отправить заявку", exact=True).click()
        detail = page.url.replace("/requests/", "/operator/requests/")
        page.get_by_role("button", name="Выйти", exact=True).click()
        login(page, url, "operator.demo", password)
        page.goto(detail)
        version = page.locator('[name="expected_version"]').input_value()
        other = second.new_page()
        login(other, url, "operator.demo", password)
        other.goto(detail)
        other.get_by_role("button", name="Принять в работу", exact=True).click()
        with page.expect_response(lambda response: response.request.method == "POST") as result:
            page.get_by_role("button", name="Принять в работу", exact=True).click()
        assert result.value.status == 409
        expect(page.locator("[data-error-summary]")).to_be_focused()
        expect(page.get_by_role("button", name="Сохранить статус", exact=True)).to_be_visible()
        expect(page.locator(".request-status")).to_have_text("В работе")
        assert page.locator('[name="expected_version"]').input_value() == version
        with page.expect_response(lambda response: response.url == detail) as refreshed:
            page.get_by_role("link", name="Обновить карточку и получить актуальную версию").click()
        assert refreshed.value.request.method == "GET"
        assert page.locator('[name="expected_version"]').input_value() != version
        page.get_by_label("Новый статус").select_option("ready")
        page.get_by_role("button", name="Сохранить статус", exact=True).click()
        expect(page.locator(".request-status")).to_have_text("Готова")
    finally:
        first.close()
        second.close()
