"""Actual login and schedule against PostgreSQL + DEBUG=False Gunicorn/WhiteNoise."""

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
def schedule_url():
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
    ]:
        subprocess.run(
            [sys.executable, "manage.py", *command], env=env, check=True, stdout=subprocess.DEVNULL
        )
    # A second fictional lesson on a fixed date exercises a shared day surface.
    fixture_code = """
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from apps.schedule.models import Lesson
from apps.schedule.services import create_lesson
source = Lesson.objects.select_related('offering', 'teacher', 'room').get(
    offering__group__studentprofile__user__username='student.one',
    offering__subject__name='Анализ данных',
    starts_at=datetime(2026, 11, 6, 9, tzinfo=ZoneInfo('Europe/Moscow')),
)
starts = datetime(2026, 11, 4, 11, tzinfo=ZoneInfo('Europe/Moscow'))
create_lesson(offering=source.offering, teacher=source.teacher, room=source.room,
              starts_at=starts, ends_at=starts + timedelta(minutes=90))
"""
    subprocess.run(
        [sys.executable, "manage.py", "shell", "-c", fixture_code],
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
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
def test_schedule_actual_login_day_week_assets_and_logout(page, schedule_url, width):
    url, password = schedule_url
    page.set_viewport_size({"width": width, "height": 1100})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{url}/login/")
    page.locator('[name="username"]').fill("student.one")
    page.locator('[name="password"]').fill(password)
    page.locator('button[type="submit"]').click()
    page.get_by_role("link", name="Моё расписание →").click()
    page.goto(f"{url}/schedule/?date=2026-11-04&view=day")
    assert page.get_by_role("heading", name="Расписание", exact=True).is_visible()
    assert page.get_by_text("Отменено", exact=True).is_visible()
    day = page.locator('.schedule-day[data-date="2026-11-04"]')
    assert page.locator(".schedule-day").count() == 1
    assert day.locator(".lesson").count() == 2
    assert day.locator(".lesson-time strong").all_text_contents() == ["09:00–10:30", "11:00–12:30"]
    assert day.locator("h4").all_text_contents() == ["Иностранный язык", "Анализ данных"]
    assert day.locator(".lesson-cancelled").count() == 1
    day.get_by_text("История изменений", exact=True).click()
    assert day.get_by_text("Демонстрационная отмена:", exact=False).is_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if os.environ.get("UPDATE_EVIDENCE") == "1":
        directory = Path("docs/evidence/U16")
        directory.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(directory / f"schedule-two-lessons-{width}.png"), full_page=True)
    for view in ["day", "week"]:
        page.goto(f"{url}/schedule/?date=2026-11-02&view={view}")
        if view == "week":
            assert page.locator(".lesson").evaluate_all(
                "items => items.map(e => e.dataset.date)"
            ) == ["2026-11-02", "2026-11-04", "2026-11-04", "2026-11-06"]
            assert page.locator(".schedule-day").evaluate_all(
                "items => items.map(e => e.dataset.date)"
            ) == ["2026-11-02", "2026-11-04", "2026-11-06"]
            assert page.locator('.schedule-day[data-date="2026-11-04"] .lesson').count() == 2
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert page.get_by_text("Перенесено · история", exact=True).is_visible()
        css = page.locator('link[href*="schedule."]').get_attribute("href")
        assert "/schedule.css" not in css  # hashed collectstatic URL
        assert page.request.get(f"{url}{css}").status == 200
        assert (
            page.locator(".schedule-day").first.evaluate("e => getComputedStyle(e).borderRadius")
            == "18px"
        )
        directory = Path("docs/evidence/U16")
        directory.mkdir(parents=True, exist_ok=True)
        if os.environ.get("UPDATE_EVIDENCE") == "1":
            page.screenshot(path=str(directory / f"schedule-{view}-{width}.png"), full_page=True)
    # Stress existing rows without changing their data or navigation targets.
    page.locator(".lesson h4").first.evaluate(
        "e => e.textContent = 'Длинное вымышленное название дисциплины '.repeat(12)"
    )
    page.get_by_role("link", name="Актуальное занятие:", exact=False).first.evaluate(
        "e => e.textContent += ' Длинная подпись перехода'.repeat(16)"
    )
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("link", name="Актуальное занятие:", exact=False).first.click()
    assert "2026-11-09" in page.url
    assert page.get_by_role("heading", name="Мировая экономика", exact=True).count() >= 1
    page.get_by_role("button", name="Выйти", exact=True).click()
    page.goto(f"{url}/schedule/")
    assert "/login/" in page.url
    assert not errors
