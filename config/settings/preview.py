"""Local-only visual review: public fictional context, no database needed."""

from .local import *

DEBUG = False
ENABLE_UI_PREVIEW = True
# WhiteNoise reads local source assets in this mode, without a collectstatic/build step.
# Ignore stale collected assets: preview serves source files only.
STATIC_ROOT = None
WHITENOISE_USE_FINDERS = True
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
