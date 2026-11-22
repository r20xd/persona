"""Real private persona workflow, persistence and mobile layout."""

import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.test_requests_browser import login
from tests.ui_qa import ui_site  # noqa: F401


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_persona_workflow(page, ui_site, width):  # noqa: F811
    url, password, _, _ = ui_site
    page.set_viewport_size({"width": width, "height": 1000})
    login(page, url, "student.one", password)
    page.goto(url + "/profile/")
    page.get_by_role("link", name="Расскажите о себе", exact=True).click()
    page.get_by_label("Анализировать", exact=True).check()
    page.get_by_label("Языки", exact=True).check()
    page.get_by_label("Исследования", exact=True).check()
    page.get_by_label("Фотография", exact=True).check()
    page.get_by_label("Одна цель на семестр", exact=True).fill("Попробовать дебаты")
    page.get_by_label("Мой прогресс", exact=True).select_option("50")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_label("Анализировать", exact=True).focus()
    assert page.locator(".persona-choice:focus-within").count() == 1
    if (
        os.environ.get("UPDATE_PERS01_EVIDENCE") == "1"
        or os.environ.get("UPDATE_PERS05_EVIDENCE") == "1"
    ):
        page.screenshot(
            path=str(
                Path(
                    "docs/evidence/PERS05"
                    if os.environ.get("UPDATE_PERS05_EVIDENCE") == "1"
                    else "docs/evidence/PERS01"
                )
                / f"editor-{width}.png"
            ),
            full_page=True,
        )
    page.get_by_role("button", name="Сохранить persōna", exact=True).click()
    assert page.url == url + "/profile/"
    expect(page.get_by_text("Попробовать дебаты", exact=True)).to_be_visible()
    expect(page.locator(".persona-progress")).to_contain_text("50%")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if (
        os.environ.get("UPDATE_PERS01_EVIDENCE") == "1"
        or os.environ.get("UPDATE_PERS05_EVIDENCE") == "1"
    ):
        page.screenshot(
            path=str(
                Path(
                    "docs/evidence/PERS05"
                    if os.environ.get("UPDATE_PERS05_EVIDENCE") == "1"
                    else "docs/evidence/PERS01"
                )
                / f"profile-{width}.png"
            ),
            full_page=True,
        )
    page.get_by_role("link", name="Редактировать", exact=True).click()
    expect(page.get_by_label("Анализировать", exact=True)).to_be_checked()
    expect(page.get_by_label("Одна цель на семестр", exact=True)).to_have_value(
        "Попробовать дебаты"
    )
    # Bypass browser maxlength to verify a real server error, keeping other answers.
    page.get_by_label("Одна цель на семестр", exact=True).evaluate(
        "e => e.removeAttribute('maxlength')"
    )
    page.get_by_label("Одна цель на семестр", exact=True).fill("x" * 161)
    page.get_by_role("button", name="Сохранить persōna", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Проверьте ответы")
    expect(page.get_by_label("Анализировать", exact=True)).to_be_checked()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("link", name="Отмена", exact=True).click()
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.one", password)
    page.goto(url + "/profile/")
    expect(page.get_by_text("Попробовать дебаты", exact=True)).to_be_visible()
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.two", password)
    page.goto(url + "/profile/")
    expect(page.get_by_role("link", name="Расскажите о себе", exact=True)).to_be_visible()
    assert page.get_by_text("Попробовать дебаты", exact=True).count() == 0
