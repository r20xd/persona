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
def dashboard_url():
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
        ["seed_demo"],
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
def test_full_cabinet_path(page, browser, dashboard_url, width):
    from tests.test_requests_browser import login

    url, password = dashboard_url
    page.set_viewport_size({"width": width, "height": 1100})
    login(page, url, "student.one", password)
    assert page.get_by_role("heading", name="Ваш учебный день").is_visible()
    assert page.locator('.campus-nav [aria-current="page"]').inner_text().endswith("Главная")
    assert page.get_by_role("heading", name="Требует внимания", exact=True).is_visible()
    assert page.get_by_role("heading", name="Ближайшие сроки").count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    css = page.locator('link[href*="dashboard."]').get_attribute("href")
    assert "/dashboard.css" not in css and page.request.get(f"{url}{css}").status == 200
    assert (
        page.locator(".dashboard-card").first.evaluate("e => getComputedStyle(e).borderRadius")
        == "20px"
    )
    page.keyboard.press("Tab")
    assert page.locator(":focus").count() == 1
    page.locator(":focus").evaluate("element => element.blur()")
    directory = Path("docs/evidence/B12-F08")
    if os.environ.get("UPDATE_EVIDENCE") == "1":
        page.screenshot(path=str(directory / f"dashboard-{width}.png"), full_page=True)
    heading = page.locator("#next-title")
    original = heading.inner_text()
    heading.evaluate(
        "(el) => { el.textContent = 'Очень длинное вымышленное название дисциплины '.repeat(12); }"
    )
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    heading.evaluate("(el, value) => { el.textContent = value; }", original)
    page.get_by_role("link", name="Моё расписание →", exact=True).click()
    assert page.get_by_role("heading", name="Расписание", exact=True).is_visible()
    page.locator('.campus-nav a[href="/grades/"]').click()
    assert page.get_by_role("heading", name="Успеваемость", exact=True).is_visible()
    page.get_by_role("navigation", name="Основные разделы").get_by_role(
        "link", name="Расписание", exact=True
    ).click()
    page.get_by_role("link", name="Сессия", exact=True).click()
    assert page.get_by_role("heading", name="Сессия", exact=True).is_visible()
    page.locator('.campus-nav a[href="/"]').click()
    page.get_by_role("link", name="Заказать справку →", exact=True).click()
    page.get_by_label("Назначение справки").select_option("other")
    page.get_by_label("Пояснение", exact=False).fill("Вымышленная новая заявка полного пути")
    page.get_by_role("button", name="Отправить заявку", exact=True).click()
    own_url = page.url
    assert page.get_by_text("Отправлена", exact=True).count()
    # Independent browser session makes an actual operator transition.
    operator_context = browser.new_context(viewport={"width": width, "height": 1100})
    operator = operator_context.new_page()
    try:
        login(operator, url, "operator.demo", password)
        operator.goto(own_url.replace("/requests/", "/operator/requests/"))
        operator.get_by_role("button", name="Принять в работу", exact=True).click()
        assert operator.get_by_text("В работе", exact=True).count()
        assert operator.evaluate("document.documentElement.scrollWidth <= innerWidth")
        if os.environ.get("UPDATE_EVIDENCE") == "1":
            operator.screenshot(path=str(directory / f"operator-{width}.png"), full_page=True)
    finally:
        operator_context.close()
    page.reload()
    assert page.get_by_text("В работе", exact=True).count()
    page.locator('.campus-nav a[href="/notifications/"]').click()
    assert page.get_by_role("heading", name="Статус заявки: В работе", exact=True).is_visible()
    note = page.locator('section[aria-labelledby="personal-heading"] article').filter(
        has=page.get_by_role("heading", name="Статус заявки: В работе", exact=True)
    )
    # Record own read state and check it again after a fresh login.
    note.get_by_role("button", name="Отметить прочитанным", exact=True).click()
    assert note.get_by_text("Прочитано", exact=True).is_visible()
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.one", password)
    page.locator('.campus-nav a[href="/notifications/"]').click()
    assert note.get_by_text("Прочитано", exact=True).is_visible()
    page.goto(own_url)
    assert page.get_by_text("В работе", exact=True).count()
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.two", password)
    assert page.goto(own_url).status == 404
    page.goto(url)
    assert not page.get_by_text("Вымышленная новая заявка полного пути", exact=True).count()
