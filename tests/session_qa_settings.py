import os

from config.settings.local import *  # noqa: F403

STATIC_ROOT = os.environ["QA_STATIC_ROOT"]
