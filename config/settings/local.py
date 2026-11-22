import os

from apps.core.configuration import database

from .base import *

# Local-only value, never used by the production settings module.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "local-only-insecure-development-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
DATABASES = {"default": database()}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

ENABLE_UI_PREVIEW = True

# Deliberate local demonstration only; production inherits the disabled base value.
ENABLE_STUDENT_DIRECTORY = os.environ.get("DEANERY_LOCAL_STUDENT_DIRECTORY", "0") == "1"
