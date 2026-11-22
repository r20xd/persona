"""Actual PostgreSQL checks: require a disposable database, never SQLite."""

import secrets

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction


@pytest.mark.django_db
def test_custom_user_persistence_and_database_constraint():
    assert connection.vendor == "postgresql"
    assert connection.pg_version // 10000 == 17
    user = get_user_model().objects.create_user(
        username="fictional-foundation-student",
        password=secrets.token_urlsafe(32),
    )
    user.refresh_from_db()
    assert user.role == "student"
    assert user.password.startswith("argon2$")
    with pytest.raises(IntegrityError), transaction.atomic():
        get_user_model().objects.filter(pk=user.pk).update(role="admin")


@pytest.mark.django_db
def test_real_database_readiness(client):
    assert client.get("/health/ready/").status_code == 200
