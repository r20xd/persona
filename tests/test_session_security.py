"""New security cases supplementing the existing access and accounts suites."""

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.academics.models import Faculty
from apps.accounts.models import User


@pytest.mark.django_db
@pytest.mark.parametrize(
    "password,reason",
    [
        ("abcd", "короткий"),
        ("987654321012345", "цифр"),
        ("password", "распространён"),
        ("student.one", "похож"),
    ],
)
def test_provision_password_reason_and_rollback(monkeypatch, password, reason):
    monkeypatch.setenv("DEMO_STUDENT_ONE_PASSWORD", "Unique-fictional-long-38146!")
    monkeypatch.setenv("DEMO_STUDENT_TWO_PASSWORD", password)
    with pytest.raises(CommandError) as caught:
        call_command("provision_accounts", stdout=StringIO())
    message = str(caught.value)
    assert reason in message.lower()
    assert password not in message
    assert not User.objects.exists()
    assert not Faculty.objects.exists()


@pytest.mark.django_db
def test_provision_unexpected_error_is_not_password_error(monkeypatch):
    monkeypatch.setenv("DEMO_STUDENT_ONE_PASSWORD", "Unique-fictional-long-38146!")
    with patch(
        "apps.accounts.management.commands.provision_accounts.validate_password",
        side_effect=RuntimeError("unexpected validator failure"),
    ):
        with pytest.raises(RuntimeError, match="unexpected validator failure"):
            call_command("provision_accounts", stdout=StringIO())
    assert not User.objects.exists()
    assert not Faculty.objects.exists()


@pytest.mark.django_db
def test_old_csrf_form_after_account_switch_rejected(monkeypatch):
    from django.test import Client

    from apps.requests.models import ServiceRequest

    password = "Unique-fictional-long-38146!"
    for variable in (
        "DEMO_STUDENT_ONE_PASSWORD",
        "DEMO_STUDENT_TWO_PASSWORD",
        "DEMO_OPERATOR_PASSWORD",
    ):
        monkeypatch.setenv(variable, password)
    call_command("seed_demo", stdout=StringIO())
    client = Client(enforce_csrf_checks=True)
    client.get("/login/")

    def login(username):
        return client.post(
            "/login/",
            {
                "username": username,
                "password": password,
                "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
            },
        )

    assert login("student.one").status_code == 302
    old_token = client.cookies["csrftoken"].value
    client.post("/logout/", {"csrfmiddlewaretoken": old_token})
    assert login("student.two").status_code == 302
    count = ServiceRequest.objects.count()
    response = client.post(
        "/requests/new/",
        {"csrfmiddlewaretoken": old_token, "purpose": "other", "comment": "Old form"},
    )
    assert response.status_code == 403
    assert "Срок защиты формы истёк" in response.content.decode()
    assert ServiceRequest.objects.count() == count


@pytest.mark.django_db
def test_login_rotates_existing_session_and_logout_csrf_marker(monkeypatch):
    from django.test import Client

    password = "Unique-fictional-long-38146!"
    User.objects.create_user(username="rotation-fixture", password=password)
    client = Client(enforce_csrf_checks=True)
    session = client.session
    session["untrusted_prelogin"] = "fixture"
    session.save()
    old_key = session.session_key
    client.get("/login/")
    old_csrf = client.cookies["csrftoken"].value
    assert (
        client.post(
            "/login/",
            {"username": "rotation-fixture", "password": password, "csrfmiddlewaretoken": old_csrf},
        ).status_code
        == 302
    )
    assert client.session.session_key != old_key
    token = client.cookies["csrftoken"].value
    assert token != old_csrf
    assert client.post("/logout/", {"csrfmiddlewaretoken": token}).status_code == 302
    assert client.cookies["csrftoken"].value != token
