"""Real browser checks; subprocess server binds only to loopback and needs no DB."""

import os
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest


@pytest.fixture(scope="module")
def preview_url():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    address = f"127.0.0.1:{port}"
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings.preview"}
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
                raise RuntimeError("Preview server exited")
            try:
                with urlopen(f"{url}/health/live/", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("Preview server did not start")
        yield url
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_preview_layout_navigation_and_disabled_login(page, preview_url, width):
    page.set_viewport_size({"width": width, "height": 1000})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{preview_url}/preview/")
    assert page.title() == "persōna · Визуальный обзор"
    assert page.locator(".brand-mark img").evaluate("e => e.complete && e.naturalWidth > 0")
    assert page.locator("h1").inner_text() == "Сегодня."
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    for link in page.locator("nav a").all():
        target = link.get_attribute("href")
        link.click()
        assert page.locator(target).count() == 1
        assert page.locator(target).is_visible()
    for link in page.locator('a[href^="#"]').all():
        assert page.locator(link.get_attribute("href")).count() == 1
    page.locator(".page-footer a").click()
    assert page.url.endswith("/preview/login/")
    assert page.locator("input:enabled").count() == 0
    assert page.locator("form").count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("link", name="Перейти к обзору").click()
    assert page.url.endswith("/preview/")
    assert not errors
