"""Dev-export reproducibility is decoded RGBA, independent of PNG container encoding."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.browser
def test_precompiled_cat_art_matches_renderer_without_database():
    root = Path(__file__).resolve().parents[1]
    # Invalid DB configuration proves the builder never queries a database.
    env = {**os.environ, "TEST_DB_PORT": "1"}
    subprocess.run(
        [sys.executable, str(root / "scripts/build_cat_art.py"), "--check"],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
