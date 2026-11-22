import os
import subprocess
import sys
from unittest.mock import patch

import pytest
from django.test import override_settings


@pytest.mark.parametrize("route", ["/preview/", "/preview/login/"])
def test_preview_is_fictional_read_only_without_database(client, route):
    with patch("django.db.backends.utils.CursorWrapper.execute", side_effect=AssertionError("DB")):
        response = client.get(route)
    assert response.status_code == 200
    assert "Конкурсный концепт" in response.content.decode()
    assert "no-store" in response["Cache-Control"]
    assert client.post(route).status_code == 405


@pytest.mark.parametrize("route", ["/preview/", "/preview/login/"])
def test_preview_disabled_by_production_default(client, route, monkeypatch):
    import importlib

    from tests.test_foundation import production_env

    for key, value in production_env().items():
        monkeypatch.setenv(key, value)
    production = importlib.reload(importlib.import_module("config.settings.production"))
    assert not getattr(production, "ENABLE_UI_PREVIEW", False)
    with override_settings(ENABLE_UI_PREVIEW=False):
        assert client.get(route).status_code == 404


def test_login_preview_cannot_submit_credentials(client):
    html = client.get("/preview/login/").content.decode()
    assert "<form" not in html
    assert 'type="password" placeholder="Поле отключено" disabled' in html
    assert 'type="text" placeholder="Демонстрационный логин" disabled' in html


def test_actual_production_routes_are_not_available():
    from tests.test_foundation import production_env

    env = {
        **os.environ,
        **production_env(),
        "DJANGO_SETTINGS_MODULE": "config.settings.production",
    }
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import django; django.setup(); "
                "from django.test import Client; "
                "client = Client(HTTP_HOST='concept.example.org'); "
                "assert all(client.get(path, secure=True).status_code == 404 "
                "for path in ['/preview/', '/preview/login/'])"
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
