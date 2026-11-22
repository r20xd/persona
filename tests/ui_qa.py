"""Q04 isolated site; threads avoid browser preconnect starvation of sync1."""

import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from urllib.request import urlopen

import psycopg
import pytest
from psycopg import sql


class PrivateSite(tuple):
    def __repr__(self):
        return "<isolated QA site>"


@pytest.fixture
def ui_site(request):
    db_name = "test_browser_" + uuid.uuid4().hex
    db = {
        key: os.environ.get("TEST_DB_" + key.upper(), default)
        for key, default in {
            "host": "127.0.0.1",
            "port": "5432",
            "user": "deanery",
            "password": "",
        }.items()
    }
    password = secrets.token_urlsafe(24)
    process = None
    created = False
    with tempfile.TemporaryDirectory(prefix="q04-static-") as static_root:
        env = {
            key: value
            for key, value in os.environ.items()
            if key
            in {
                "PATH",
                "SYSTEMROOT",
                "WINDIR",
                "TEMP",
                "TMP",
                "HOME",
                "USERPROFILE",
                "PLAYWRIGHT_BROWSERS_PATH",
                "VIRTUAL_ENV",
            }
        }
        env.update(
            DJANGO_SETTINGS_MODULE="tests.session_qa_settings",
            DJANGO_DEBUG="0",
            DJANGO_SECRET_KEY=secrets.token_urlsafe(64),
            DB_NAME=db_name,
            QA_STATIC_ROOT=static_root,
            DEANERY_LOCAL_STUDENT_DIRECTORY=("1" if getattr(request, "param", False) else "0"),
        )
        env.update({"DB_" + key.upper(): str(value) for key, value in db.items()})
        env.update(
            {
                key: password
                for key in (
                    "DEMO_STUDENT_ONE_PASSWORD",
                    "DEMO_STUDENT_TWO_PASSWORD",
                    "DEMO_OPERATOR_PASSWORD",
                )
            }
        )
        try:
            with psycopg.connect(dbname="postgres", autocommit=True, **db) as admin:
                admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            created = True
            for command in (
                ["migrate", "--noinput"],
                ["seed_demo"],
                ["collectstatic", "--noinput"],
            ):
                subprocess.run(
                    [sys.executable, "manage.py", *command],
                    env=env,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            url = f"http://127.0.0.1:{port}"
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "gunicorn",
                    "config.wsgi:application",
                    "--bind",
                    f"127.0.0.1:{port}",
                    "--threads",
                    "4",
                ],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError("QA server exited")
                try:
                    with urlopen(url + "/health/ready/", timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("QA server unavailable")
            yield PrivateSite((url, password, db_name, db))
        finally:
            try:
                if process is not None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
            finally:
                if created:
                    with psycopg.connect(dbname="postgres", autocommit=True, **db) as admin:
                        admin.execute(
                            sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(db_name))
                        )
