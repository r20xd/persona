"""Shared transaction lock and strict identity checks for fictional bootstrap data."""

from django.core.management.base import CommandError
from django.db import connection


def demo_lock():
    # All callers hold transaction.atomic. This also serializes independent CLI processes.
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(6212081208)")


def fixture(model, *, defaults, **lookup):
    item, created = model.objects.get_or_create(defaults=defaults, **lookup)
    if not created:
        for field, value in defaults.items():
            actual = getattr(item, field)
            if actual != value:
                raise CommandError(f"Incompatible fictional {model.__name__} fixture; unchanged.")
    return item, created
