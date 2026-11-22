from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.academics.models import Faculty, Program, StudyGroup
from apps.accounts.models import OperatorScope, StudentProfile
from apps.accounts.services import create_student_profile, grant_operator_scope

pytestmark = pytest.mark.django_db
PASSWORD = "Fictional-test-only-7845!"


@pytest.fixture
def identities():
    faculty = Faculty.objects.create(code="f", name="Тестовый факультет")
    program = Program.objects.create(code="p", name="Тестовая программа", faculty=faculty)
    people = []
    for number in range(3):
        group, _ = StudyGroup.objects.get_or_create(
            code=f"Г-{number % 2}", defaults={"program": program}
        )
        user = get_user_model().objects.create_user(username=f"student{number}", password=PASSWORD)
        create_student_profile(
            user=user, full_name=f"Вымышленный Студент {number}", course=2, group=group
        )
        people.append(user)
    operator = get_user_model().objects.create_user(
        username="operator", password=PASSWORD, role="operator"
    )
    return people, operator


def test_login_profiles_and_direct_substitution(client, identities):
    students, _ = identities
    for user in students:
        assert (
            client.post(
                reverse("login"), {"username": user.username, "password": PASSWORD}
            ).status_code
            == 302
        )
        response = client.get(reverse("profile"))
        assert response.status_code == 200
        assert user.studentprofile.full_name in response.content.decode()
        for other in students:
            if other != user:
                assert other.studentprofile.full_name not in response.content.decode()
        assert "no-store" in response["Cache-Control"]
        assert client.get(f"/profile/{students[0].pk}/").status_code == 404
        client.post(reverse("logout"))


@pytest.mark.parametrize(
    "next_url", ["https://evil.invalid/", "//evil.invalid/", "http://evil.invalid/"]
)
def test_safe_next(client, identities, next_url):
    user = identities[0][0]
    response = client.post(
        reverse("login"), {"username": user.username, "password": PASSWORD, "next": next_url}
    )
    assert response.url == "/"


def test_local_next_and_role_routing(client, identities):
    user = identities[0][0]
    response = client.post(
        reverse("login"), {"username": user.username, "password": PASSWORD, "next": "/profile/"}
    )
    assert response.url == "/profile/"
    client.post(reverse("logout"))
    operator = identities[1]
    response = client.post(reverse("login"), {"username": operator.username, "password": PASSWORD})
    assert response.url == "/operator/requests/"
    assert client.get("/").url == "/operator/requests/"
    assert client.get("/profile/").status_code == 403


def test_csrf_and_logout_session(identities):
    user = identities[0][0]
    client = Client(enforce_csrf_checks=True)
    assert (
        client.post("/login/", {"username": user.username, "password": PASSWORD}).status_code == 403
    )
    client.get("/login/")
    token = client.cookies["csrftoken"].value
    assert (
        client.post(
            "/login/",
            {"username": user.username, "password": PASSWORD, "csrfmiddlewaretoken": token},
        ).status_code
        == 302
    )
    assert client.get("/logout/").status_code == 405
    assert client.post("/logout/").status_code == 403
    assert client.get("/profile/").status_code == 200
    token = client.cookies["csrftoken"].value
    assert client.post("/logout/", {"csrfmiddlewaretoken": token}).status_code == 302
    assert client.get("/profile/").status_code == 302


def test_deactivation_and_missing_profile(client, identities):
    user = identities[0][0]
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    user.is_active = False
    user.save()
    assert client.get("/profile/").status_code == 302
    failed = client.post("/login/", {"username": user.username, "password": PASSWORD})
    unknown = client.post("/login/", {"username": "missing", "password": PASSWORD})
    assert failed.status_code == unknown.status_code == 200
    assert "Не удалось войти" in failed.content.decode()
    user = get_user_model().objects.create_user(username="unconfigured", password=PASSWORD)
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    assert client.get("/profile/").status_code == 403


def test_roles_scope_and_constraints(identities):
    students, operator = identities
    group = students[0].studentprofile.group
    with pytest.raises(ValidationError):
        create_student_profile(user=operator, full_name="Нет", course=1, group=group)
    with pytest.raises(ValidationError):
        grant_operator_scope(operator=students[0], group=group)
    scope = grant_operator_scope(operator=operator, group=group)
    with pytest.raises(IntegrityError), transaction.atomic():
        OperatorScope.objects.create(operator=operator, group=group)
    with pytest.raises(IntegrityError), transaction.atomic():
        StudentProfile.objects.filter(pk=students[0].studentprofile.pk).update(course=7)
    assert scope.operator_id == operator.pk
    assert not operator.is_staff and not operator.is_superuser


def test_axes_actual_combined_lock_and_cooldown(client, identities):
    from axes.models import AccessAttempt, AccessAttemptExpiration

    user = identities[0][0]
    for _ in range(10):
        response = client.post(
            "/login/", {"username": user.username, "password": "wrong"}, REMOTE_ADDR="127.0.0.2"
        )
    assert response.status_code == 429
    assert (
        client.post(
            "/login/",
            {"username": user.username, "password": PASSWORD},
            REMOTE_ADDR="127.0.0.2",
            HTTP_X_FORWARDED_FOR="192.0.2.2",
        ).status_code
        == 429
    )
    assert (
        client.post(
            "/login/", {"username": user.username, "password": PASSWORD}, REMOTE_ADDR="127.0.0.3"
        ).status_code
        == 302
    )
    client.post("/logout/")
    other = identities[0][1]
    assert (
        client.post(
            "/login/", {"username": other.username, "password": PASSWORD}, REMOTE_ADDR="127.0.0.2"
        ).status_code
        == 302
    )
    client.post("/logout/")
    AccessAttempt.objects.update(attempt_time=timezone.now() - timedelta(minutes=16))
    AccessAttemptExpiration.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    assert (
        client.post(
            "/login/", {"username": user.username, "password": PASSWORD}, REMOTE_ADDR="127.0.0.2"
        ).status_code
        == 302
    )


def test_provision_is_idempotent_and_rejects_incompatible(monkeypatch):
    from django.core.management import call_command
    from django.core.management.base import CommandError

    for variable in (
        "DEMO_STUDENT_ONE_PASSWORD",
        "DEMO_STUDENT_TWO_PASSWORD",
        "DEMO_OPERATOR_PASSWORD",
    ):
        monkeypatch.setenv(variable, PASSWORD)
    call_command("provision_accounts")
    user = get_user_model().objects.get(username="student.one")
    password_hash = user.password
    call_command("provision_accounts")
    user.refresh_from_db()
    assert user.password == password_hash
    assert user.password.startswith("argon2$")
    assert StudentProfile.objects.count() == 2
    assert OperatorScope.objects.count() == 2
    user.is_staff = True
    user.save()
    with pytest.raises(CommandError, match="incompatible"):
        call_command("provision_accounts")
    user.refresh_from_db()
    assert user.is_staff


def test_session_expiration_and_protected_references(client, identities):
    from django.db.models.deletion import ProtectedError

    user = identities[0][0]
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    session = client.session
    session.set_expiry(timezone.now() - timedelta(seconds=1))
    session.save()
    assert client.get("/profile/").status_code == 302
    with pytest.raises(ProtectedError):
        user.delete()
    with pytest.raises(ProtectedError):
        user.studentprofile.group.delete()
