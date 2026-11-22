"""Environment parsing with errors that never include supplied values."""

import os

from django.core.exceptions import ImproperlyConfigured


def required(name):
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("replace-"):
        raise ImproperlyConfigured(f"Set a non-placeholder {name} environment variable.")
    return value


def database(prefix="DB", *, strict=False):
    defaults = {"NAME": "deanery", "USER": "deanery", "HOST": "127.0.0.1", "PORT": "5432"}
    values = {}
    for field in ("NAME", "USER", "PASSWORD", "HOST", "PORT"):
        name = f"{prefix}_{field}"
        values[field] = required(name) if strict else os.environ.get(name, defaults.get(field, ""))
    return {
        "ENGINE": "django.db.backends.postgresql",
        **values,
        "CONN_MAX_AGE": 0,
        "OPTIONS": {"connect_timeout": 5},
    }
