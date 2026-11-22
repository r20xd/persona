"""Q05-only settings; collectstatic never touches a developer's served static root."""

import os
from pathlib import Path

from config.settings.local import *  # noqa: F403

DEBUG = False
ENABLE_UI_PREVIEW = False
STATIC_ROOT = Path(os.environ["Q05_STATIC_ROOT"])
