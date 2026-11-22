import importlib
import json
import logging
import os
import secrets
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.db import OperationalError
from django.test import Client, RequestFactory

from apps.core import views


def test_live_does_not_require_database(client):
    with patch("apps.core.views.connection.cursor", side_effect=AssertionError("DB used")):
        response = client.get("/health/live/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response["Cache-Control"] == "no-store"
    assert len(response["X-Request-ID"]) == 32


def test_readiness_success_probes_database():
    cursor = MagicMock()
    with patch("apps.core.views.connection.cursor") as factory:
        factory.return_value.__enter__.return_value = cursor
        response = views.ready(RequestFactory().get("/health/ready/"))
    cursor.execute.assert_called_once_with("SELECT 1")
    assert response.status_code == 200


def test_readiness_hides_connection_errors(client):
    with patch(
        "apps.core.views.connection.cursor", side_effect=OperationalError("secret-host-password")
    ):
        response = client.get("/health/ready/")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert b"secret" not in response.content


@pytest.mark.parametrize("route", ["/health/live/", "/health/ready/"])
def test_health_rejects_writes(client, route):
    assert client.post(route).status_code == 405


def test_csrf_errors_and_not_found_hide_details():
    client = Client(enforce_csrf_checks=True)
    assert client.post("/health/live/").status_code == 403
    response = client.get("/missing/?secret=hidden")
    assert response.status_code == 404
    assert "Страница не найдена" in response.content.decode()
    assert b"hidden" not in response.content


def settings_process(module, extra=None):
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("DJANGO_", "DB_", "TEST_DB_", "DEANERY_LOCAL_"))
    }
    env.update(extra or {})
    return subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def production_env():
    return {
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(64),
        "DJANGO_ALLOWED_HOSTS": "concept.example.org",
        "DJANGO_TRUSTED_PROXY_CIDRS": "172.30.90.0/28",
        "DJANGO_CSRF_TRUSTED_ORIGINS": "https://concept.example.org",
        "DB_NAME": "deanery",
        "DB_USER": "deanery",
        "DB_PASSWORD": secrets.token_urlsafe(32),
        "DB_HOST": "db",
        "DB_PORT": "5432",
    }


def test_production_missing_configuration_fails_closed():
    result = settings_process("config.settings.production")
    assert result.returncode != 0
    assert "Set a non-placeholder DJANGO_SECRET_KEY" in result.stderr


@pytest.mark.parametrize("missing", list(production_env()))
def test_production_requires_every_environment_value(missing):
    env = production_env()
    del env[missing]
    result = settings_process("config.settings.production", env)
    assert result.returncode != 0
    assert missing in result.stderr


@pytest.mark.parametrize(
    "key,value",
    [
        ("DJANGO_ALLOWED_HOSTS", "*"),
        ("DJANGO_CSRF_TRUSTED_ORIGINS", "http://concept.example.org"),
        ("DJANGO_CSRF_TRUSTED_ORIGINS", "https://attacker.example.org"),
        ("DJANGO_SECRET_KEY", "replace-secret"),
    ],
)
def test_production_rejects_unsafe_configuration(key, value):
    env = production_env()
    env[key] = value
    assert settings_process("config.settings.production", env).returncode != 0


def test_production_security_flags(monkeypatch):
    for key, value in production_env().items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("DJANGO_DEBUG", "1")
    module = importlib.import_module("config.settings.production")
    module = importlib.reload(module)
    assert module.DEBUG is False
    assert module.SESSION_COOKIE_SECURE and module.CSRF_COOKIE_SECURE
    assert module.SECURE_SSL_REDIRECT


def test_test_settings_ignore_production_database():
    env = production_env()
    env["DB_HOST"] = "production.example.org"
    assert settings_process("config.settings.test", env).returncode == 0
    env["TEST_DB_NAME"] = "deanery"
    assert settings_process("config.settings.test", env).returncode != 0
    env["TEST_DB_NAME"] = "test_deanery"
    env["TEST_DB_HOST"] = "production.example.org"
    assert settings_process("config.settings.test", env).returncode != 0


def test_user_password_hash_and_safe_defaults():
    user = get_user_model()(username="fictional-student")
    password = secrets.token_urlsafe(32)
    user.set_password(password)
    assert user.password.startswith("argon2$")
    assert user.password != password
    assert user.check_password(password)
    assert user.role == "student"
    assert not user.is_staff and not user.is_superuser


def test_access_log_does_not_include_query_or_headers(client, caplog):
    with patch("apps.core.middleware.logger.info") as info:
        client.get("/health/live/?password=private-value", HTTP_COOKIE="sessionid=private-cookie")
    assert "private" not in json.dumps(info.call_args.args)


def test_framework_log_preserves_error_type_without_sensitive_payload():
    from apps.core.logging import SafeFormatter

    try:
        raise OperationalError("secret-db-host-password")
    except OperationalError:
        record = logging.LogRecord(
            "django.request",
            logging.ERROR,
            __file__,
            1,
            "private-body %s",
            ("cookie-secret",),
            sys.exc_info(),
        )
    formatted = SafeFormatter().format(record)
    assert "OperationalError" in formatted
    assert "ERROR django.request" in formatted
    assert "secret" not in formatted
    assert "private" not in formatted
    assert "Traceback" not in formatted


@pytest.mark.parametrize(
    "module,flag,expected",
    [
        ("base", "1", False),
        ("local", "0", False),
        ("local", "1", True),
        ("production", "1", False),
        ("test", "1", False),
    ],
)
def test_student_directory_configuration_is_local_only(module, flag, expected):
    env = production_env()
    env["DEANERY_LOCAL_STUDENT_DIRECTORY"] = flag
    result = settings_process(
        f"config.settings.{module} as settings; "
        f"assert settings.ENABLE_STUDENT_DIRECTORY is {expected!r}",
        env,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("code", [400, 403, 404, 500])
@pytest.mark.parametrize(
    "accept",
    [None, "*/*", "text/html", "application/json", "text/html;q=0.2, application/json;q=0.8"],
)
def test_error_responses_negotiate_without_private_context(code, accept):
    request = RequestFactory().get(
        "/private-path/?secret=hidden", **({"HTTP_ACCEPT": accept} if accept else {})
    )
    request.user = request.session = MagicMock()
    with (
        patch("apps.core.views.connection.cursor", side_effect=AssertionError("DB used")),
        patch(
            "apps.core.views.staticfiles_storage.url", return_value="/static/css/workspace.hash.css"
        ),
    ):
        response = views.error_response(request, code)
    assert response.status_code == code
    assert response["Cache-Control"] == "no-store"
    assert "Accept" in response["Vary"]
    assert not request.user.mock_calls
    assert not request.session.mock_calls
    assert all(value not in response.content for value in [b"private-path", b"secret", b"hidden"])
    if accept and "application/json" in accept:
        assert json.loads(response.content) == {"status": views.ERRORS[code][0]}
    else:
        html = response.content.decode()
        assert '<html lang="ru">' in html
        assert 'href="/"' in html
        assert 'href="/static/css/workspace.hash.css"' in html
        assert '<h1 id="error-title">' in html
        assert "Конкурсный концепт" in html


def test_server_error_survives_missing_manifest_and_database():
    with (
        patch(
            "apps.core.views.staticfiles_storage.url", side_effect=ValueError("private manifest")
        ),
        patch(
            "apps.core.views.connection.cursor", side_effect=OperationalError("private database")
        ),
        patch(
            "apps.accounts.context_processors.cat_cameo",
            side_effect=AssertionError("context used"),
        ),
    ):
        response = views.server_error(RequestFactory().get("/private/?secret=hidden"))
    assert response.status_code == 500
    assert b"stylesheet" not in response.content
    assert b"private" not in response.content
    assert 'href="/"' in response.content.decode()


def test_server_error_omits_external_stylesheet():
    with patch(
        "apps.core.views.staticfiles_storage.url", return_value="https://external.example/style.css"
    ):
        response = views.server_error(RequestFactory().get("/"))
    assert b"stylesheet" not in response.content
