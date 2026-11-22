import os

from django.core.exceptions import ImproperlyConfigured

from apps.core.configuration import database

from .base import *

SECRET_KEY = "test-only-insecure-key-not-used-by-production"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
# Deliberately ignore DB_* and DJANGO_SECRET_KEY: tests cannot inherit production configuration.
DATABASES = {"default": database("TEST_DB")}
DATABASES["default"]["NAME"] = os.environ.get("TEST_DB_NAME", "test_deanery")
DATABASES["default"]["USER"] = os.environ.get("TEST_DB_USER", "deanery")
if not DATABASES["default"]["NAME"].startswith("test_"):
    raise ImproperlyConfigured("TEST_DB_NAME must start with test_.")
if DATABASES["default"]["HOST"] not in {"localhost", "127.0.0.1", "::1", "db"}:
    raise ImproperlyConfigured("TEST_DB_HOST must refer to an isolated local test service.")
DATABASES["default"]["TEST"] = {"NAME": DATABASES["default"]["NAME"]}

ENABLE_UI_PREVIEW = True
# Unit templates render source assets without requiring a production collectstatic build.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
