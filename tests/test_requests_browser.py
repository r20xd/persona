"""Real forms and cross-role status round trip on an isolated PostgreSQL browser DB."""

import os
from pathlib import Path

import pytest

from tests.test_grades_browser import grades_url as requests_url  # noqa: F401


def login(page, url, username, password):
    page.goto(f"{url}/login/")
    page.locator('[name="username"]').fill(username)
    page.locator('[name="password"]').fill(password)
    page.locator('button[type="submit"]').click()


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_request_round_trip(page, requests_url, width):  # noqa: F811
    url, password = requests_url
    page.set_viewport_size({"width": width, "height": 1100})
    directory = Path("docs/evidence/B07-F06")
    directory.mkdir(parents=True, exist_ok=True)
    login(page, url, "student.one", password)
    page.get_by_role("link", name="Заказать справку →", exact=True).click()
    page.get_by_label("Назначение справки").select_option("other")
    page.get_by_label("Пояснение").fill("Демонстрационное обращение без персональных данных")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if width == 360:
        if os.environ.get("UPDATE_EVIDENCE") == "1":
            page.screenshot(path=str(directory / "new-360.png"), full_page=True)
    page.get_by_role("button", name="Отправить заявку").click()
    detail_url = page.url
    assert page.get_by_role("heading", name="Сообщение оператору", exact=True).is_visible()
    assert page.locator(".request-status").inner_text() == "Отправлена"
    page.reload()
    assert page.get_by_text(
        "Демонстрационное обращение без персональных данных", exact=True
    ).is_visible()
    student_message = "Уточните срок подготовки.\n<em>Это обычный текст</em>"
    page.get_by_label("Сообщение", exact=True).fill(student_message)
    page.get_by_role("button", name="Отправить сообщение", exact=True).click()
    assert page.locator("#conversation .request-comment").inner_text() == student_message
    assert page.locator("#conversation em").count() == 0
    assert page.locator("#conversation").get_by_text("Студент · Вы", exact=True).is_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "operator.demo", password)
    assert page.get_by_role("heading", name="Очередь заявок", exact=True).is_visible()
    if width == 1440:
        if os.environ.get("UPDATE_EVIDENCE") == "1":
            page.screenshot(path=str(directory / "queue-1440.png"), full_page=True)
    page.get_by_role("link", name="Справка об обучении", exact=True).click()
    assert page.get_by_role("heading", name="Сообщение оператору", exact=True).is_visible()
    assert page.locator(".request-status").inner_text() == "Отправлена"
    assert page.locator("#conversation .request-comment").inner_text() == student_message
    operator_message = "Демонстрационная справка будет подготовлена завтра."
    page.get_by_label("Сообщение", exact=True).fill(operator_message)
    page.get_by_role("button", name="Отправить сообщение", exact=True).click()
    assert page.locator("#conversation .request-comment").all_inner_texts() == [
        student_message,
        operator_message,
    ]
    assert page.locator("#conversation").get_by_text("Деканат · Вы", exact=True).is_visible()
    assert page.locator('select[name="desired_status"]:visible').count() == 0
    page.get_by_role("button", name="Принять в работу", exact=True).click()
    assert page.locator(".request-status").inner_text() == "В работе"
    page.get_by_label("Новый статус").select_option("ready")
    page.get_by_label("Комментарий для студента").fill("Демонстрационная справка подготовлена")
    page.get_by_role("button", name="Сохранить статус").click()
    assert page.locator(".request-status").inner_text() == "Готова"
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.one", password)
    page.goto(detail_url)
    assert page.locator(".request-status").inner_text() == "Готова"
    assert page.locator(".request-history li").count() == 3
    assert page.locator("#conversation .request-comment").all_inner_texts() == [
        student_message,
        operator_message,
    ]
    assert page.locator("#conversation").get_by_text("Деканат", exact=True).is_visible()
    assert "Заявка обработана" in page.locator(".request-notice").inner_text()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    css = page.locator('link[href*="requests."]').get_attribute("href")
    assert "/requests.css" not in css
    assert page.request.get(f"{url}{css}").status == 200
    assert (
        page.locator(".request-card").first.evaluate("e => getComputedStyle(e).borderRadius")
        == "18px"
    )
    if os.environ.get("UPDATE_EVIDENCE") == "1":
        page.screenshot(path=str(directory / f"ready-{width}.png"), full_page=True)
        conversation_directory = Path("docs/evidence/MSG01")
        conversation_directory.mkdir(parents=True, exist_ok=True)
        page.screenshot(
            path=str(conversation_directory / f"conversation-{width}.png"), full_page=True
        )
    # A different student's authenticated browser cannot open this card.
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.two", password)
    assert page.goto(detail_url).status == 404
