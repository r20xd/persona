"""Offline collectstatic only; never use as web settings."""

from .base import *

SECRET_KEY = "offline-collectstatic-build-only"
DATABASES = {"default": {"ENGINE": "django.db.backends.dummy"}}
