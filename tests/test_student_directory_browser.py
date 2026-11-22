"""Student discovery reads a deliberate whitelist, while editing remains personal."""

import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.test_requests_browser import login
from tests.ui_qa import ui_site  # noqa: F401


@pytest.mark.browser
@pytest.mark.parametrize("ui_site", [True], indirect=True)
@pytest.mark.parametrize("width", [360, 1440])
def test_directory_workflow(page, ui_site, width):  # noqa: F811
    url, password, _, _ = ui_site
    page.set_viewport_size({"width": width, "height": 1000})
    login(page, url, "student.one", password)
    page.goto(url + "/profile/persona/")
    expect(page.get_by_role("heading", name="Моя persōna", exact=True)).to_be_visible()
    page.get_by_label("Анализировать", exact=True).check()
    page.get_by_label("Одна цель на семестр", exact=True).fill("Провести исследование")
    page.get_by_label("Мой прогресс", exact=True).select_option("25")
    page.get_by_role("button", name="Сохранить persōna", exact=True).click()
    owner_name = page.locator("#student-name").inner_text()
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.two", password)
    if width <= 850:
        page.locator("[data-workspace-menu] summary").click()
    nav = page.get_by_role(
        "navigation", name=("Дополнительные разделы" if width <= 850 else "Основные разделы")
    )
    nav.get_by_role("link", name="Студенты", exact=True).click()
    if width <= 850:
        page.locator("[data-workspace-menu] summary").click()
    expect(nav.get_by_role("link", name="Студенты", exact=True)).to_have_attribute(
        "aria-current", "page"
    )
    page.get_by_label("Поиск по имени", exact=True).fill(owner_name.lower())
    page.get_by_role("button", name="Найти", exact=True).click()
    expect(page.locator(".directory-card")).to_have_count(1)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if (
        os.environ.get("UPDATE_PERS04_EVIDENCE") == "1"
        or os.environ.get("UPDATE_PERS05_EVIDENCE") == "1"
    ):
        page.screenshot(
            path=str(
                Path(
                    "docs/evidence/PERS05"
                    if os.environ.get("UPDATE_PERS05_EVIDENCE") == "1"
                    else "docs/evidence/PERS04"
                )
                / f"students-{width}.png"
            ),
            full_page=True,
        )
    page.get_by_role("link", name=owner_name, exact=True).click()
    expect(page.get_by_role("heading", name=owner_name, exact=True)).to_be_visible()
    expect(page.get_by_text("Провести исследование", exact=True)).to_be_visible()
    expect(page.locator(".persona-progress")).to_contain_text("25%")
    assert page.get_by_role("link", name="Редактировать", exact=True).count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if (
        os.environ.get("UPDATE_PERS04_EVIDENCE") == "1"
        or os.environ.get("UPDATE_PERS05_EVIDENCE") == "1"
    ):
        page.screenshot(
            path=str(
                Path(
                    "docs/evidence/PERS05"
                    if os.environ.get("UPDATE_PERS05_EVIDENCE") == "1"
                    else "docs/evidence/PERS04"
                )
                / f"student-{width}.png"
            ),
            full_page=True,
        )
    page.get_by_role("link", name="← Студенты", exact=True).click()
    page.get_by_label("Поиск по имени", exact=True).fill("НикогоТакогоНет")
    page.get_by_role("button", name="Найти", exact=True).click()
    expect(page.get_by_role("heading", name="Никого не нашли", exact=True)).to_be_visible()
    page.goto(url + "/profile/")
    expect(page.get_by_role("link", name="Расскажите о себе", exact=True)).to_be_visible()


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_competition_navigation_and_direct_directory_denial(page, ui_site, width):  # noqa: F811
    url, password, _, _ = ui_site
    page.set_viewport_size({"width": width, "height": 1000})
    for username in ("student.one", "student.two"):
        login(page, url, username, password)
        expect(page.get_by_role("navigation", name="Основные разделы")).to_be_visible()
        assert page.get_by_role("link", name="Студенты", exact=True).count() == 0
        assert page.locator(".campus-nav a").count() == 7
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert page.goto(url + "/students/").status == 404
        assert page.goto(url + "/students/1/").status == 404
        assert page.goto(url + "/profile/").status == 200
        page.get_by_role("button", name="Выйти", exact=True).click()
