"""U05 workspace: real layout, focus, reflow and preserved account boundaries."""

import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.test_requests_browser import login
from tests.test_ui_revision_browser import control_contrast
from tests.ui_qa import ui_site  # noqa: F401


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 390, 768, 1440])
def test_workspace_hierarchy_and_controls(page, ui_site, width):  # noqa: F811
    url, password, _, _ = ui_site
    height = 1024 if width == 768 else 844 if width < 768 else 900
    page.set_viewport_size({"width": width, "height": height})
    page.goto(url + "/login/")
    submit = page.get_by_role("button", name="Войти в кабинет →", exact=True)
    box = submit.bounding_box()
    assert box["y"] >= 0 and box["y"] + box["height"] <= height
    control_contrast(page)
    logo = page.locator(".brand-mark img")
    assert logo.evaluate("e => e.complete && e.naturalWidth > 0")
    art = page.locator(".login-persona-art")
    expect(art).to_have_attribute("aria-hidden", "true")
    assert art.evaluate("e => getComputedStyle(e).pointerEvents") == "none"
    if os.environ.get("UPDATE_U07_EVIDENCE") == "1" and width in {360, 1440}:
        page.screenshot(path=str(Path("docs/evidence/U07") / f"login-{width}.png"), full_page=True)
    login(page, url, "student.one", password)
    nearest = page.locator(".dashboard-next")
    box = nearest.bounding_box()
    nav_top = page.locator(".workspace-sidebar").bounding_box()["y"] if width < 851 else height
    assert box["y"] >= 0 and box["y"] + box["height"] <= nav_top
    assert page.locator(".dashboard-next").evaluate(
        "e => e.compareDocumentPosition(document.querySelector('.attention-card')) "
        "& Node.DOCUMENT_POSITION_FOLLOWING"
    )
    for action in page.locator(".attention-card .dashboard-item > a").all():
        assert action.bounding_box()["height"] >= 44
    if width < 851:
        assert page.locator(".mobile-brand .brand").bounding_box()["height"] >= 44
    for path in [
        "/",
        "/profile/",
        "/cat/",
        "/assistant/",
        "/grades/",
        "/schedule/",
        "/schedule/?view=week",
        "/schedule/session/",
        "/requests/",
        "/requests/new/",
        "/notifications/",
    ]:
        assert page.goto(url + path).status == 200
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert page.locator(".concept-notice").count() == 1
        assert page.locator(".campus-nav svg use").count() == 7
        if width <= 390:
            assert page.locator(".campus-nav a:visible").evaluate_all("""links => links.every(e => {
              const cell=e.getBoundingClientRect();
              const label=[...e.querySelectorAll('span')].find(s => s.getClientRects().length);
              const box=label.getBoundingClientRect(), range=document.createRange();
              range.selectNodeContents(label);
              const text=range.getBoundingClientRect();
              return box.left>=cell.left-1 && box.right<=cell.right+1 &&
                text.left>=cell.left-1 && text.right<=cell.right+1 &&
                text.height<=parseFloat(getComputedStyle(label).lineHeight)+1 &&
                box.bottom<=cell.bottom+1;
            })""")
        if width <= 850:
            links = page.locator(".campus-nav a:visible")
            assert links.count() == 5
            assert [text.strip() for text in links.all_inner_texts()] == [
                "Главная",
                "Расписание",
                "Учёба",
                "Заявки",
                "Уведомления",
            ]
            boxes = [link.bounding_box() for link in links.all()]
            assert max(box["y"] for box in boxes) - min(box["y"] for box in boxes) < 1
        assert page.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == "auto"
        control_contrast(page)
        edges = page.evaluate("""() => {
          const main=document.querySelector('main'), header=document.querySelector('.header-inner');
          const left=e => e.getBoundingClientRect().left +
            parseFloat(getComputedStyle(e).paddingLeft);
          return [left(main),left(header)];
        }""")
        assert abs(edges[0] - edges[1]) <= 1, edges
        profile = page.get_by_role("link", name="Мой профиль", exact=True)
        box = profile.bounding_box()
        assert box["height"] >= 44 and box["width"] >= 44
    # Existing authenticated login contract: public form, no workspace chrome.
    page.goto(url + "/login/")
    assert page.locator(".workspace-sidebar, .account-header").count() == 0
    expect(submit).to_be_visible()
    page.emulate_media(reduced_motion="reduce")
    assert page.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == "auto"


@pytest.mark.browser
def test_keyboard_focus_immediate_and_narrow_reflow(page, ui_site):  # noqa: F811
    url, password, _, _ = ui_site
    page.set_viewport_size({"width": 1440, "height": 900})
    login(page, url, "student.one", password)
    page.goto(url)
    page.keyboard.press("Tab")
    expect(page.locator(".skip-link")).to_be_focused()
    # Every desktop Tab target must become visible without delayed smooth scrolling.
    for _ in range(30):
        page.keyboard.press("Tab")
        assert page.evaluate("""() => {
          const e=document.activeElement,r=e.getBoundingClientRect();
          return e===document.body || (r.top>=0 && r.bottom<=innerHeight &&
            e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)));
        }""")
    for width, height in [(320, 844), (720, 500)]:
        page.set_viewport_size({"width": width, "height": height})
        for path in [
            "/",
            "/profile/",
            "/cat/",
            "/assistant/",
            "/schedule/",
            "/grades/",
            "/requests/new/",
            "/notifications/",
        ]:
            page.goto(url + path)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.goto(url + "/requests/new/")
    submit = page.get_by_role("button", name="Отправить заявку", exact=True)
    submit.focus()
    submit.scroll_into_view_if_needed()
    expect(submit).to_be_focused()
    assert submit.evaluate("""e => {const r=e.getBoundingClientRect();
      return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));}""")


@pytest.mark.browser
def test_mobile_more_native_and_keyboard(page, ui_site):  # noqa: F811
    url, password, _, _ = ui_site
    page.set_viewport_size({"width": 360, "height": 844})
    login(page, url, "student.one", password)
    menu = page.locator("[data-workspace-menu]")
    summary = menu.locator("summary")
    summary.focus()
    page.keyboard.press("Enter")
    expect(menu).to_have_attribute("open", "")
    page.keyboard.press("Tab")
    expect(menu.get_by_role("link", name="Кот в рюкзаке", exact=True)).to_be_focused()
    page.keyboard.press("Escape")
    expect(menu).not_to_have_attribute("open", "")
    expect(summary).to_be_focused()
    summary.click()
    summary.click()
    expect(menu).not_to_have_attribute("open", "")
    summary.click()
    page.locator("h1").click(position={"x": 8, "y": 8})
    expect(menu).not_to_have_attribute("open", "")
    summary.click()
    page.set_viewport_size({"width": 1440, "height": 900})
    expect(menu).not_to_have_attribute("open", "")
    expect(
        page.locator(".desktop-extra-navigation").get_by_role("link", name="Помощник", exact=True)
    ).to_be_visible()
    # A separate context disables all JavaScript, including hashed static assets.
    with page.context.browser.new_context(
        java_script_enabled=False, viewport={"width": 360, "height": 844}
    ) as context:
        native = context.new_page()
        login(native, url, "student.one", password)
        native.locator("[data-workspace-menu] summary").click()
        native.get_by_role("navigation", name="Дополнительные разделы").get_by_role(
            "link", name="Помощник", exact=True
        ).click()
        expect(native.get_by_role("heading", name="Помощник", exact=True)).to_be_visible()
        native.locator("[data-workspace-menu] summary").click()
        native.get_by_role("navigation", name="Дополнительные разделы").get_by_role(
            "link", name="Кот в рюкзаке", exact=True
        ).click()
        expect(native.locator("[data-clock]")).to_have_text("20")


@pytest.mark.browser
def test_operator_keeps_two_mobile_destinations(page, ui_site):  # noqa: F811
    url, password, _, _ = ui_site
    page.set_viewport_size({"width": 360, "height": 844})
    login(page, url, "operator.demo", password)
    assert page.locator("[data-workspace-menu]").count() == 0
    assert page.locator(".campus-nav a:visible").count() == 2
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
