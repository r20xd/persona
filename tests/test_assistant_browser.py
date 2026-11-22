"""AI01 real disconnected workflow: no generated answers, retained draft, private empty state."""

import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.test_requests_browser import login
from tests.ui_qa import ui_site  # noqa: F401


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_assistant_disconnected_draft_and_clear(page, ui_site, width):  # noqa: F811
    url, password, _, _ = ui_site
    page.set_viewport_size({"width": width, "height": 1000})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    login(page, url, "student.one", password)
    if width <= 850:
        page.locator("[data-workspace-menu] summary").click()
    page.get_by_role("link", name="Помощник", exact=True).filter(visible=True).click()
    expect(page.get_by_role("heading", name="Помощник", exact=True)).to_be_visible()
    expect(page.locator(".assistant-connection")).to_contain_text("ИИ пока не подключён")
    expect(page.get_by_role("heading", name="Первый вопрос", exact=True)).to_be_visible()
    assert page.locator(".assistant-avatar img").evaluate("e => e.complete && e.naturalWidth > 0")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("button", name="Составить план", exact=True).click()
    field = page.get_by_label("Ваш вопрос", exact=True)
    expect(field).to_be_focused()
    expect(field).to_have_value("Помоги составить план подготовки к экзамену.")
    field.fill("Помоги разобрать вымышленную учебную тему")
    page.get_by_role("button", name="Отправить вопрос", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("ИИ пока не подключён")
    expect(field).to_have_value("Помоги разобрать вымышленную учебную тему")
    assert page.locator(".assistant-message").count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if os.environ.get("UPDATE_AI01_EVIDENCE") == "1":
        root = Path("docs/evidence/AI01")
        root.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(root / f"assistant-{width}.png"), full_page=True)
    page.get_by_role("button", name="Очистить диалог", exact=True).click()
    expect(field).to_have_value("")
    expect(page.locator(".assistant-empty")).to_be_visible()
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.two", password)
    page.goto(url + "/assistant/")
    expect(page.locator(".assistant-empty")).to_be_visible()
    expect(page.get_by_label("Ваш вопрос", exact=True)).to_have_value("")
    assert errors == []
