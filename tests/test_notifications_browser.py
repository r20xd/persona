"""Actual login and grades against PostgreSQL + DEBUG=False Gunicorn/WhiteNoise."""

import os
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.request import urlopen

import psycopg
import pytest
from psycopg import sql


@pytest.fixture
def notifications_url():
    password = "Fictional-browser-8561!"
    db_name = "test_browser_" + uuid.uuid4().hex
    db = {
        "host": os.environ.get("TEST_DB_HOST", "127.0.0.1"),
        "port": os.environ.get("TEST_DB_PORT", "5432"),
        "user": os.environ.get("TEST_DB_USER", "deanery"),
        "password": os.environ.get("TEST_DB_PASSWORD", ""),
    }
    with psycopg.connect(dbname="postgres", autocommit=True, **db) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.local",
        "DJANGO_DEBUG": "0",
        "DB_NAME": db_name,
        **{f"DB_{key.upper()}": str(value) for key, value in db.items()},
    }
    for variable in [
        "DEMO_STUDENT_ONE_PASSWORD",
        "DEMO_STUDENT_TWO_PASSWORD",
        "DEMO_OPERATOR_PASSWORD",
    ]:
        env[variable] = password
    for command in [
        ["migrate", "--noinput"],
        ["provision_accounts"],
        ["provision_study_demo", "--anchor-date=2026-11-04"],
        ["provision_grades_demo"],
        ["provision_notifications_demo"],
    ]:
        subprocess.run(
            [sys.executable, "manage.py", *command], env=env, check=True, stdout=subprocess.DEVNULL
        )
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    address = f"127.0.0.1:{port}"
    subprocess.run(
        [sys.executable, "manage.py", "collectstatic", "--noinput"],
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    process = subprocess.Popen(
        [sys.executable, "-m", "gunicorn", "config.wsgi:application", "--bind", address],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://{address}"
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError("Schedule server exited")
            try:
                with urlopen(f"{url}/health/ready/", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("Schedule server unavailable")
        yield url, password
    finally:
        process.terminate()
        process.wait(timeout=10)
        with psycopg.connect(dbname="postgres", autocommit=True, **db) as admin:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(db_name)))


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_notification_round_trip(page, notifications_url, width):
    from tests.test_requests_browser import login

    url, password = notifications_url
    page.set_viewport_size({"width": width, "height": 1100})
    login(page, url, "student.one", password)
    page.get_by_role("link", name="Заказать справку →", exact=True).click()
    page.get_by_label("Назначение справки").select_option("other")
    page.get_by_role("button", name="Отправить заявку", exact=True).click()
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "operator.demo", password)
    page.get_by_role("link", name="Справка об обучении", exact=True).click()
    page.get_by_role("button", name="Принять в работу", exact=True).click()
    page.get_by_role("link", name="Уведомления", exact=True).click()
    assert page.get_by_role("heading", name="Деканат на связи", exact=True).is_visible()
    assert page.get_by_role("heading", name="Встреча вашей группы", exact=True).is_visible()
    assert page.get_by_role("button", name="Отметить прочитанным", exact=True).count() == 0
    read_all = page.get_by_role("button", name="Прочитать все", exact=True)
    read_all.focus()
    read_all.press("Enter")
    assert page.get_by_text("Непрочитанных: 0 · Время московское", exact=True).is_visible()
    assert page.get_by_role("button", name="Прочитать все", exact=True).count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.one", password)
    page.get_by_role("link", name="Уведомления", exact=True).click()
    assert page.get_by_role("heading", name="Статус заявки: В работе", exact=True).is_visible()
    page.locator('section[aria-labelledby="personal-heading"] button').first.click()
    assert page.get_by_text("Прочитано", exact=True).count() == 1
    page.locator('section[aria-labelledby="news-heading"] button').first.click()
    assert page.get_by_text("Прочитано", exact=True).count() == 2
    page.get_by_role("button", name="Прочитать все", exact=True).click()
    assert page.get_by_text("Непрочитанных: 0 · Время московское", exact=True).is_visible()
    assert page.get_by_role("button", name="Прочитать все", exact=True).count() == 0
    assert page.get_by_role("heading", name="Учебные сроки", exact=True).count() == 0
    assert page.get_by_role("link", name="Подготовить учебный проект", exact=True).count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    css = page.locator('link[href*="notifications."]').get_attribute("href")
    assert "/notifications.css" not in css
    assert page.request.get(f"{url}{css}").status == 200
    assert (
        page.locator(".notification-card").first.evaluate("e => getComputedStyle(e).borderRadius")
        == "16px"
    )
    directory = Path("docs/evidence/B10-F07")
    directory.mkdir(parents=True, exist_ok=True)
    if os.environ.get("UPDATE_EVIDENCE") == "1":
        page.screenshot(path=str(directory / f"notifications-{width}.png"), full_page=True)


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_personal_deadline_round_trip(page, notifications_url, width):
    from playwright.sync_api import expect

    from tests.test_requests_browser import login

    url, password = notifications_url
    page.set_viewport_size({"width": width, "height": 1000})
    login(page, url, "student.one", password)
    page.get_by_role("link", name="Дедлайны", exact=True).click()
    expect(
        page.get_by_text("Задач в работе пока нет. Добавьте первую задачу с датой.")
    ).to_be_visible()
    page.get_by_role("button", name="Добавить задачу", exact=True).click()
    expect(page.get_by_text("Укажите дату дедлайна.")).to_be_visible()
    page.get_by_label("Название задачи").fill("Подготовить доклад")
    page.get_by_label("Дата дедлайна").fill("2026-11-20")
    page.get_by_role("button", name="Добавить задачу", exact=True).click()
    expect(page.get_by_role("heading", name="Подготовить доклад", exact=True)).to_be_visible()
    page.reload()
    page.get_by_role("button", name="Завершить задачу Подготовить доклад", exact=True).click()
    expect(
        page.get_by_role("button", name="Вернуть в работу задачу Подготовить доклад", exact=True)
    ).to_be_visible()
    page.get_by_role(
        "button", name="Вернуть в работу задачу Подготовить доклад", exact=True
    ).click()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert page.locator('.campus-nav [aria-current="page"]').inner_text() == "Дедлайны"
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.two", password)
    page.goto(url + "/deadlines/")
    expect(page.get_by_role("heading", name="Подготовить доклад", exact=True)).to_have_count(0)
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.one", password)
    page.goto(url + "/deadlines/")
    expect(page.get_by_role("heading", name="Подготовить доклад", exact=True)).to_be_visible()


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_operator_publication_round_trip(page, notifications_url, width):
    from playwright.sync_api import expect

    from tests.test_requests_browser import login

    url, password = notifications_url
    title = f"Встреча группы · ANN01 {width}"
    page.set_viewport_size({"width": width, "height": 1000})
    login(page, url, "operator.demo", password)
    page.get_by_role("link", name="Уведомления", exact=True).click()
    page.get_by_role("link", name="Новое объявление", exact=True).click()
    page.get_by_role("button", name="Опубликовать", exact=True).click()
    expect(page.locator("#id_title_error")).to_be_visible()
    page.get_by_label("Группа", exact=True).select_option(index=1)
    page.get_by_label("Заголовок", exact=True).fill(title)
    page.get_by_label("Текст объявления", exact=True).fill("Приходите на встречу в аудиторию 204.")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if os.environ.get("UPDATE_EVIDENCE") == "1":
        directory = Path("docs/evidence/ANN01")
        directory.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(directory / f"form-{width}.png"), full_page=True)
    page.get_by_role("button", name="Опубликовать", exact=True).click()
    expect(page.get_by_role("heading", name=title, exact=True)).to_be_visible()
    assert "#announcement-" in page.url
    page.reload()
    expect(page.get_by_role("heading", name=title, exact=True)).to_have_count(1)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.one", password)
    page.get_by_role("link", name="Уведомления", exact=True).click()
    expect(page.get_by_role("heading", name=title, exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="Новое объявление", exact=True)).to_have_count(0)
    if os.environ.get("UPDATE_EVIDENCE") == "1":
        page.screenshot(path=str(directory / f"student-feed-{width}.png"), full_page=True)
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.two", password)
    page.get_by_role("link", name="Уведомления", exact=True).click()
    expect(page.get_by_role("heading", name=title, exact=True)).to_have_count(0)
