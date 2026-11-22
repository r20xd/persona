"""Private persona persistence, authorization, validation and additive schema."""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import Client

from apps.accounts.models import StudentPersona, StudentProfile
from apps.accounts.services import save_persona
from tests.test_accounts import identities  # noqa: F401

pytestmark = pytest.mark.django_db


def values(**overrides):
    return {
        "strengths": ["analysis"],
        "interests": ["languages"],
        "skills": ["research"],
        "activities": ["photo"],
        "goal": "Попробовать дебаты",
        "progress": 25,
        **overrides,
    }


def test_create_update_clear_and_get_no_write(client, identities):  # noqa: F811
    user = identities[0][0]
    client.force_login(user)
    for path in ["/profile/", "/profile/persona/"]:
        response = client.get(path)
        assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    assert StudentPersona.objects.count() == 0
    response = client.post("/profile/persona/", values())
    assert response.status_code == 302 and response.url == "/profile/"
    assert "no-store" in response["Cache-Control"]
    persona = StudentPersona.objects.get(student=user.studentprofile)
    original_id = persona.pk
    assert persona.progress == 25
    assert "Анализирую · Увлекаюсь языками · Учусь исследовать" in client.get("/profile/").text
    client.post("/profile/persona/", values(goal="Новая цель", progress=75))
    persona.refresh_from_db()
    assert persona.goal == "Новая цель" and persona.pk == original_id
    assert 'value="Новая цель"' in client.get("/profile/persona/").text
    response = client.post("/profile/persona/", {"goal": "", "progress": "100"})
    assert response.status_code == 302
    persona.refresh_from_db()
    assert persona.goal == "" and persona.progress == 0 and persona.strengths == []
    assert "Расскажите о себе" in client.get("/profile/").text


@pytest.mark.parametrize(
    "overrides",
    [
        {"strengths": ["unknown"]},
        {"strengths": ["analysis"] * 9},
        {"interests": {"arbitrary": "json"}},
        {"skills": "research"},
        {"goal": "x" * 161},
        {"progress": 101},
        {"progress": 30},
        {"progress": True},
    ],
)
def test_service_rejects_invalid_values(identities, overrides):  # noqa: F811
    with pytest.raises(ValidationError):
        save_persona(actor=identities[0][0], **values(**overrides))
    assert StudentPersona.objects.count() == 0


def test_form_errors_and_escaping(client, identities):  # noqa: F811
    user = identities[0][0]
    client.force_login(user)
    response = client.post("/profile/persona/", values(goal="x" * 161))
    assert response.status_code == 200 and "Проверьте ответы" in response.text
    assert "x" * 161 in response.text
    assert StudentPersona.objects.count() == 0
    response = client.post("/profile/persona/", values(strengths=["unknown"]))
    assert response.status_code == 200 and StudentPersona.objects.count() == 0
    client.post("/profile/persona/", values(goal='<script>alert("x")</script>'))
    response = client.get("/profile/")
    assert "&lt;script&gt;" in response.text and '<script>alert("x")</script>' not in response.text


def test_isolation_forged_owner_and_roles(client, identities):  # noqa: F811
    students, operator = identities
    for user in students:
        save_persona(actor=user, **values(goal="Личная цель " + user.username))
    for user in students:
        client.force_login(user)
        response = client.get("/profile/")
        assert "Личная цель " + user.username in response.text
        for other in students:
            if other != user:
                assert "Личная цель " + other.username not in response.text
        victim = next(other for other in students if other != user)
        victim_goal = StudentPersona.objects.get(student=victim.studentprofile).goal
        client.post(
            "/profile/persona/",
            {
                **values(),
                "student_id": victim.studentprofile.pk,
                "owner": victim.pk,
                "next": "https://evil.invalid",
            },
        )
        assert StudentPersona.objects.get(student=victim.studentprofile).goal == victim_goal
        assert client.get(f"/profile/persona/{victim.pk}/").status_code == 404
        assert client.post("/profile/").status_code == 405
        assert client.put("/profile/persona/").status_code == 405
    client.force_login(operator)
    assert client.get("/profile/persona/").status_code == 403
    assert client.post("/profile/persona/", values()).status_code == 403
    with pytest.raises(PermissionDenied):
        save_persona(actor=operator, **values())
    client.logout()
    assert client.get("/profile/persona/").status_code == 302


def test_csrf_and_database_range(identities):  # noqa: F811
    client = Client(enforce_csrf_checks=True)
    user = identities[0][0]
    client.force_login(user)
    assert client.post("/profile/persona/", values()).status_code == 403
    persona = save_persona(actor=user, **values())
    with pytest.raises(IntegrityError), transaction.atomic():
        StudentPersona.objects.filter(pk=persona.pk).update(progress=101)


@pytest.mark.django_db(transaction=True)
def test_additive_migration_preserves_profiles(identities):  # noqa: F811
    students, _ = identities

    def snapshot():
        return list(
            StudentProfile.objects.filter(user_id__in=[u.pk for u in students])
            .order_by("pk")
            .values_list("pk", "user_id", "full_name", "course", "group_id", "user__password")
        )

    before = snapshot()
    executor = MigrationExecutor(connection)
    executor.migrate([("accounts", "0002_operatorscope_studentprofile")])
    try:
        executor = MigrationExecutor(connection)
        executor.migrate([("accounts", "0003_studentpersona")])
        assert snapshot() == before
        assert StudentPersona.objects.count() == 0
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
