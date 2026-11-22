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
def grades_url():
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
def test_grades_session_actual_login(page, grades_url, width):
    url, password = grades_url
    page.set_viewport_size({"width": width, "height": 1100})
    page.goto(f"{url}/login/")
    page.locator('[name="username"]').fill("student.one")
    page.locator('[name="password"]').fill(password)
    page.locator('button[type="submit"]').click()
    page.get_by_role("link", name="Успеваемость →").click()
    assert page.get_by_role("heading", name="Успеваемость", exact=True).is_visible()
    assert page.get_by_text("0 / 20 баллов", exact=True).is_visible()
    for section in ["grades", "session"]:
        if section == "session":
            page.get_by_role("navigation", name="Основные разделы").get_by_role(
                "link", name="Расписание", exact=True
            ).click()
            page.get_by_role("link", name="Сессия", exact=True).click()
            assert (
                page.locator(".exam-cancelled .exam-status")
                .get_by_text("Отменено", exact=True)
                .is_visible()
            )
        selected = page.locator("#term").input_value()
        with page.expect_navigation():
            page.locator("#term").select_option(selected)
        assert f"term={selected}" in page.url
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        css = page.locator('link[href*="grades."]').get_attribute("href")
        assert "/grades.css" not in css
        assert page.request.get(f"{url}{css}").status == 200
        assert (
            page.locator(".grade-card").first.evaluate("e => getComputedStyle(e).borderRadius")
            == "18px"
        )
        directory = Path("docs/evidence/B06-F04")
        directory.mkdir(parents=True, exist_ok=True)
        if os.environ.get("UPDATE_EVIDENCE") == "1":
            page.screenshot(path=str(directory / f"{section}-{width}.png"), full_page=True)
