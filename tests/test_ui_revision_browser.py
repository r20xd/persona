"""U06: persōna branding, real GET filters, navigation and palette in Chromium."""

import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import psycopg
import pytest
from playwright.sync_api import expect

from tests.test_requests_browser import login
from tests.ui_qa import ui_site  # noqa: F401


def query(page):
    return parse_qs(urlparse(page.url).query)


def second_term(db_name, db):
    # ui_site owns this disposable database; never connect to application data.
    with psycopg.connect(dbname=db_name, **db) as conn:
        term_id = conn.execute(
            "INSERT INTO academics_term (code,title,starts_on,ends_on) "
            "VALUES ('u09-previous','Предыдущий семестр','2025-01-01','2025-06-30') RETURNING id"
        ).fetchone()[0]
        offering = conn.execute(
            "INSERT INTO academics_courseoffering (subject_id,group_id,term_id,control_type) "
            "SELECT subject_id,group_id,%s,control_type FROM academics_courseoffering "
            "WHERE group_id=(SELECT group_id FROM accounts_studentprofile "
            "WHERE user_id=(SELECT id FROM accounts_user WHERE username='student.one')) "
            "LIMIT 1 RETURNING id",
            (term_id,),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO academics_enrollment (student_id,offering_id) "
            "SELECT id,%s FROM accounts_studentprofile WHERE user_id="
            "(SELECT id FROM accounts_user WHERE username='student.one')",
            (offering,),
        )
    return str(term_id)


def layout(page):
    assert "persōna" in page.title()
    assert page.locator(".concept-notice").count() == 1
    expect(page.locator(".concept-notice")).to_be_visible()
    assert page.locator("body").inner_text().lower().count("конкурсный концепт") == 1
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert (
        page.locator(":root").evaluate('e => getComputedStyle(e).getPropertyValue("--ink").trim()')
        == "#2F4156"
    )


def control_contrast(page):
    controls = page.locator("input:not([type=hidden]):not([type=checkbox]), select, textarea")
    for control in controls.all():
        if not control.is_visible():
            continue
        ratios = control.evaluate("""e => {
          const css = getComputedStyle(e);
          const luminance = color => {
            const rgb = color.match(/[0-9.]+/g).slice(0,3).map(Number).map(v => {
              v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4;
            });
            return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
          };
          const ratio = (a,b) => (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
          let parent = e.parentElement;
          while (parent && getComputedStyle(parent).backgroundColor === 'rgba(0, 0, 0, 0)')
            parent = parent.parentElement;
          const outside = parent ? getComputedStyle(parent).backgroundColor : 'rgb(255,255,255)';
          const inside = css.backgroundColor === 'rgba(0, 0, 0, 0)' ? outside : css.backgroundColor;
          return {border: ratio(luminance(css.borderTopColor), luminance(outside)),
                  text: ratio(luminance(css.color), luminance(inside))};
        }""")
        assert ratios["border"] >= 3, ratios
        assert ratios["text"] >= 4.5, ratios


def screenshot(page, name, width):
    if os.environ.get("UPDATE_U09_EVIDENCE") == "1":
        page.screenshot(path=str(Path("docs/evidence/U09") / f"{name}-{width}.png"), full_page=True)


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_revision_navigation_and_filters(page, ui_site, width):  # noqa: F811
    url, password, db_name, db = ui_site
    page.set_viewport_size({"width": width, "height": 1000})
    page.goto(url + "/login/")
    layout(page)
    control_contrast(page)
    screenshot(page, "login", width)
    login(page, url, "student.one", password)
    other_term = second_term(db_name, db)
    for path in [
        "/",
        "/profile/",
        "/grades/",
        "/schedule/",
        "/schedule/?view=week",
        "/schedule/session/",
        "/session/",
        "/requests/",
        "/notifications/",
    ]:
        assert page.goto(url + path).status == 200
        layout(page)
        control_contrast(page)
        assert page.get_by_role("button", name="Показать", exact=True).count() == 0
        assert page.locator(".header-label").count() == 0
        assert page.locator(".profile-links").count() == 0
        nav = page.get_by_role("navigation", name="Основные разделы")
        if "session" in path or "schedule" in path:
            expect(nav.get_by_role("link", name="Расписание", exact=True)).to_have_attribute(
                "aria-current", "page"
            )
        if path == "/grades/":
            assert page.locator(".study-tabs, .exam-card").count() == 0
            expect(page.get_by_role("heading", name="Успеваемость", exact=True)).to_be_visible()
            screenshot(page, "grades", width)
        if path == "/schedule/session/":
            expect(page.get_by_role("link", name="Сессия", exact=True)).to_have_attribute(
                "aria-current", "page"
            )
            screenshot(page, "session", width)
        if path == "/":
            screenshot(page, "home", width)
    for view in ["day", "week"]:
        page.goto(url + f"/schedule/?view={view}")
        with page.expect_navigation():
            page.locator("input[type=date]").fill("2026-11-18")
        assert query(page) == {"date": ["2026-11-18"], "view": [view]}
    for path in ["/grades/", "/schedule/session/"]:
        page.goto(url + path)
        original_term = page.locator("#term").input_value()
        with page.expect_navigation():
            page.locator("#term").select_option(other_term)
        assert query(page) == {"term": [other_term]}
        expect(page.locator("#term")).to_have_value(other_term)
        if "session" in path:
            expect(page.get_by_role("heading", name="Событий сессии пока нет")).to_be_visible()
        else:
            expect(page.get_by_text("Текущих работ пока нет", exact=True)).to_be_visible()
        with page.expect_navigation():
            page.locator("#term").select_option(original_term)
        assert query(page) == {"term": [original_term]}
        screenshot(page, "term-filter" + ("-session" if "session" in path else "-grades"), width)
    page.goto(url + "/profile/")
    screenshot(page, "profile", width)
    page.goto(url + "/requests/new/")
    control_contrast(page)
    page.goto(url + "/requests/?page=1")
    assert page.get_by_role("button", name="Показать", exact=True).count() == 0
    with page.expect_navigation():
        page.get_by_label("Статус", exact=True).select_option("submitted")
    assert query(page) == {"status": ["submitted"]}
    expect(page.locator(".request-card .request-status")).to_have_text("Отправлена")
    with page.expect_navigation():
        page.get_by_label("Статус", exact=True).select_option("ready")
    expect(page.get_by_role("heading", name="Пока нет заявок")).to_be_visible()
    page.go_back()
    expect(page.get_by_label("Статус", exact=True)).to_have_value("submitted")
    screenshot(page, "requests-filter", width)
    page.goto(url + "/notifications/?page=1&news_page=1")
    # GET filters must not mark anything read.
    with psycopg.connect(dbname=db_name, **db) as conn:
        before = conn.execute(
            "SELECT count(*) FROM notifications_notification WHERE read_at IS NOT NULL"
        ).fetchone()
    with page.expect_navigation():
        page.locator("[name=kind]").select_option("request")
    assert query(page) == {"kind": ["request"]}
    assert page.locator("#personal-heading ~ .notification-card .overline").count() > 0
    for text in page.locator(
        "#personal-heading ~ .notification-card .overline"
    ).all_text_contents():
        assert "Заявк" in text
    with page.expect_navigation():
        page.get_by_label("Только непрочитанные").check()
    assert query(page) == {"kind": ["request"], "unread": ["1"]}
    with page.expect_navigation():
        page.get_by_label("Только непрочитанные").uncheck()
    assert query(page) == {"kind": ["request"]}
    with psycopg.connect(dbname=db_name, **db) as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM notifications_notification WHERE read_at IS NOT NULL"
            ).fetchone()
            == before
        )
    screenshot(page, "notifications-filter", width)
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "operator.demo", password)
    layout(page)
    requests = []
    page.on("request", lambda request: requests.append(request.method))
    with page.expect_navigation():
        page.get_by_label("Статус", exact=True).select_option("submitted")
    assert query(page) == {"status": ["submitted"]}
    expect(page.locator(".request-card .request-status")).to_have_text("Отправлена")
    assert "POST" not in requests
    screenshot(page, "operator-filter", width)
    requests.clear()
    page.get_by_role("link", name="Справка об обучении", exact=True).click()
    # The shared SVG sprite can finish loading after the document navigation.
    page.wait_for_load_state("networkidle")
    expect(page.get_by_role("button", name="Принять в работу", exact=True)).to_be_visible()
    assert page.locator('select[name="desired_status"]').count() == 0
    assert page.locator('[name="desired_status"]').input_value() == "in_progress"
    assert "POST" not in requests
    page.get_by_role("button", name="Выйти", exact=True).click()
    for path in ["/preview/", "/preview/login/"]:
        assert page.goto(url + path).status == 200
        layout(page)
        control_contrast(page)


@pytest.mark.browser
def test_filters_without_javascript(browser, ui_site):  # noqa: F811
    url, password, db_name, db = ui_site
    other_term = second_term(db_name, db)
    context = browser.new_context(
        java_script_enabled=False, viewport={"width": 360, "height": 1000}
    )
    try:
        page = context.new_page()
        login(page, url, "student.one", password)
        for path, selector, value in [
            ("/requests/", "[name=status]", "ready"),
            ("/notifications/", "[name=kind]", "request"),
            ("/grades/", "#term", other_term),
            ("/schedule/session/", "#term", other_term),
            ("/schedule/", "[name=date]", "2026-11-18"),
        ]:
            page.goto(url + path)
            button = page.get_by_role("button", name="Показать", exact=True)
            expect(button).to_be_visible()
            if selector == "[name=date]":
                page.locator(selector).fill(value)
            else:
                page.locator(selector).select_option(value)
            assert page.url == url + path
            button.click()
            assert value in page.url
    finally:
        context.close()
