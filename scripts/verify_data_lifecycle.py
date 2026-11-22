#!/usr/bin/env python3
"""Explicit disposable Q05 rehearsal; never loads .env or accepts an existing database."""

import argparse
import json
import os
import re
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

import psycopg
from playwright.sync_api import sync_playwright
from psycopg import sql

ROOT = Path(__file__).resolve().parent.parent
LABEL = "deanery.q05.owner"


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def wait_for(check, message):
    for _ in range(150):
        try:
            if check():
                return
        except (OSError, psycopg.Error):
            pass
        time.sleep(0.2)
    raise RuntimeError(message)


def status(url):
    try:
        with urlopen(url, timeout=2) as response:
            return response.status
    except HTTPError as error:
        return error.code
    except URLError:
        return None


def clean_environment():
    # Explicit allowlist: no inherited database, demo, Django or service configuration.
    return {
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


class Rehearsal:
    def __init__(self, docker):
        self.docker = docker
        self.owner = uuid.uuid4().hex
        self.container = f"deanery-q05-{self.owner}"
        self.volume = f"deanery-q05-data-{self.owner}"
        self.container_created = False
        self.volume_created = False
        self.web = None
        self.private = None
        self.port = free_port()
        self.web_port = free_port()
        self.db_name = "lifecycle_source"
        self.env = clean_environment()
        self.password = secrets.token_urlsafe(32)
        self.env.update(
            {
                "DJANGO_SETTINGS_MODULE": "scripts.lifecycle_settings",
                "DJANGO_DEBUG": "0",
                "DJANGO_SECRET_KEY": secrets.token_urlsafe(64),
                "DB_HOST": "127.0.0.1",
                "DB_PORT": str(self.port),
                "DB_USER": "deanery",
                "DB_PASSWORD": "",
                "DB_NAME": self.db_name,
            }
        )
        for role in ["STUDENT_ONE", "STUDENT_TWO", "OPERATOR"]:
            self.env[f"DEMO_{role}_PASSWORD"] = self.password
        self.url = f"http://127.0.0.1:{self.web_port}"
        self.stages = []

    def run(self, args, **kwargs):
        return subprocess.run(args, check=True, capture_output=True, timeout=120, **kwargs)

    def docker_run(self, *args, **kwargs):
        return self.run([self.docker, *args], env=clean_environment(), **kwargs)

    def resource_absent(self, kind, name):
        result = subprocess.run(
            [self.docker, kind, "inspect", name],
            capture_output=True,
            timeout=30,
            env=clean_environment(),
        )
        if result.returncode == 0:
            return False
        missing = (b"no such container", b"no such object", b"no such volume")
        if not any(marker in result.stderr.lower() for marker in missing):
            raise RuntimeError("Cannot confirm resource absence")
        return True

    def require_absent(self, kind, name):
        if not self.resource_absent(kind, name):
            raise RuntimeError("Refusing pre-existing resource name")

    def create_owned(self, kind, *args):
        # The daemon may create a resource before a CLI timeout/interrupt is raised.
        setattr(self, f"{kind}_created", True)
        self.docker_run(*args)
        self.owned(kind, getattr(self, kind))

    def owned(self, kind, name):
        result = self.docker_run(kind, "inspect", name)
        data = json.loads(result.stdout)[0]
        labels = data.get("Labels") if kind == "volume" else data["Config"].get("Labels")
        if not labels or labels.get(LABEL) != self.owner:
            raise RuntimeError("Refusing resource operation: ownership mismatch")

    def container_action(self, action):
        self.owned("container", self.container)
        self.docker_run(action, self.container)

    def connection(self, name=None):
        return psycopg.connect(
            host="127.0.0.1",
            port=self.port,
            user="deanery",
            dbname=name or self.db_name,
            autocommit=True,
        )

    def ready_db(self):
        with self.connection() as connection:
            return connection.execute("SELECT 1").fetchone() == (1,)

    def manage(self, *args):
        self.run([sys.executable, "manage.py", *args], cwd=ROOT, env=self.env)

    def start_web(self):
        self.web = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "gunicorn",
                "config.wsgi:application",
                "--bind",
                f"127.0.0.1:{self.web_port}",
                "--workers",
                "1",
                "--timeout",
                "15",
            ],
            cwd=ROOT,
            env=self.env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait_for(
            lambda: self.web.poll() is None and status(self.url + "/health/ready/") == 200,
            "Owned web did not become ready",
        )

    def stop_web(self):
        if self.web:
            if self.web.poll() is None:
                try:
                    self.web.terminate()
                except ProcessLookupError:
                    pass
            try:
                self.web.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.web.kill()
                self.web.wait(timeout=10)
            self.web = None

    def snapshot(self, name=None):
        # Values (including password hashes) stay only in memory. No DSN or row is logged.
        tables = [
            "accounts_user",
            "accounts_studentprofile",
            "accounts_operatorscope",
            "academics_enrollment",
            "grades_graderesult",
            "schedule_lesson",
            "schedule_lessonchange",
            "requests_servicerequest",
            "requests_requestevent",
            "notifications_notification",
            "notifications_deadline",
            "notifications_announcement",
            "notifications_announcementread",
        ]
        with self.connection(name) as connection:
            return {
                table: connection.execute(
                    sql.SQL(
                        "SELECT (to_jsonb(t) - 'last_login')::text FROM {} t ORDER BY 1"
                    ).format(sql.Identifier(table))
                ).fetchall()
                for table in tables
            }

    def login(self, page, username):
        page.goto(self.url + "/login/")
        page.locator('[name="username"]').fill(username)
        page.locator('[name="password"]').fill(self.password)
        page.locator('button[type="submit"]').click()
        assert not page.url.endswith("/login/"), "Browser login failed"

    def verify_browser(self, page, detail, *, session=False):
        if not session:
            self.login(page, "student.one")
        assert page.goto(self.url + detail).status == 200
        assert page.locator(".request-status").inner_text() == "В работе"
        assert page.locator(".request-history li").count() == 2
        for path in ["/profile/", "/schedule/", "/grades/", "/notifications/"]:
            assert page.goto(self.url + path).status == 200
        # Separate browser context proves isolation without destroying the persisted session.
        other = page.context.browser.new_context()
        try:
            second = other.new_page()
            self.login(second, "student.two")
            assert second.goto(self.url + detail).status == 404
        finally:
            other.close()

    def execute(self):
        contexts = json.loads(self.docker_run("context", "inspect").stdout)
        endpoint = contexts[0]["Endpoints"]["docker"]["Host"]
        parsed = urlparse(endpoint)
        if parsed.scheme not in {"unix", "npipe"} and not (
            parsed.scheme == "tcp" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        ):
            raise RuntimeError("Docker endpoint must be local")
        self.private = tempfile.TemporaryDirectory(prefix="deanery-q05-")
        self.env["Q05_STATIC_ROOT"] = str(Path(self.private.name) / "static")
        image = re.search(r"image:\s*(\S+)", (ROOT / "deploy/compose.local.yaml").read_text())[1]
        if not image.startswith("postgres:17.11-") or "@sha256:" not in image:
            raise RuntimeError("Expected pinned PostgreSQL 17.11 image")
        self.require_absent("container", self.container)
        self.require_absent("volume", self.volume)
        self.create_owned(
            "volume", "volume", "create", "--label", f"{LABEL}={self.owner}", self.volume
        )
        self.create_owned(
            "container",
            "create",
            "--name",
            self.container,
            "--label",
            f"{LABEL}={self.owner}",
            "--publish",
            f"127.0.0.1:{self.port}:5432",
            "--mount",
            f"type=volume,src={self.volume},dst=/var/lib/postgresql/data",
            "--env",
            "POSTGRES_HOST_AUTH_METHOD=trust",
            "--env",
            "POSTGRES_USER=deanery",
            "--env",
            f"POSTGRES_DB={self.db_name}",
            image,
        )
        self.container_action("start")
        wait_for(self.ready_db, "Owned PostgreSQL did not become ready")
        with self.connection() as connection:
            assert connection.info.server_version == 170011
        self.manage("migrate", "--noinput")
        self.manage("seed_demo", "--anchor-date=2026-11-02")
        self.manage("collectstatic", "--noinput")
        self.start_web()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page()
                self.login(page, "student.one")
                stylesheet = page.locator('link[rel="stylesheet"]').first.get_attribute("href")
                assert page.request.get(self.url + stylesheet).status == 200
                page.goto(self.url + "/requests/new/")
                page.get_by_label("Назначение справки").select_option("other")
                page.get_by_label("Пояснение").fill("Проверка сохранности конкурсного концепта")
                page.get_by_role("button", name="Отправить заявку", exact=True).click()
                detail = page.url.removeprefix(self.url)
                request_id = detail.strip("/").split("/")[-1]
                operator = browser.new_page()
                self.login(operator, "operator.demo")
                operator.goto(self.url + f"/operator/requests/{request_id}/")
                operator.get_by_role("button", name="Сохранить статус", exact=True).click()
                assert operator.locator(".request-status").inner_text() == "В работе"
                operator.close()
                page.goto(self.url + "/notifications/")
                page.locator('section[aria-labelledby="personal-heading"] button').first.click()
                page.locator('section[aria-labelledby="news-heading"] button').first.click()
                self.verify_browser(page, detail, session=True)
                baseline = self.snapshot()
                self.stages.append("browser_create_operator_transition_read_marks")
                self.stop_web()
                self.start_web()
                self.verify_browser(page, detail, session=True)
                assert self.snapshot() == baseline
                self.stages.append("web_restart_session_and_data")
                self.container_action("stop")
                wait_for(
                    lambda: status(self.url + "/health/ready/") == 503,
                    "Readiness did not fail during DB outage",
                )
                self.container_action("start")
                wait_for(self.ready_db, "Restarted PostgreSQL did not become ready")
                wait_for(
                    lambda: status(self.url + "/health/ready/") == 200, "Readiness did not recover"
                )
                self.verify_browser(page, detail, session=True)
                self.manage("seed_demo", "--anchor-date=2026-11-02")
                assert self.snapshot() == baseline
                self.stages.append("postgres_restart_readiness_session_seed")
                # Docker exec streams bytes; no host path/mount is passed to Docker Desktop.
                with tempfile.TemporaryFile() as dump:
                    os.fchmod(dump.fileno(), 0o600) if hasattr(os, "fchmod") else None
                    self.owned("container", self.container)
                    subprocess.run(
                        [
                            self.docker,
                            "exec",
                            self.container,
                            "pg_dump",
                            "-U",
                            "deanery",
                            "-Fc",
                            self.db_name,
                        ],
                        check=True,
                        stdout=dump,
                        stderr=subprocess.PIPE,
                        timeout=120,
                        env=clean_environment(),
                    )
                    with self.connection() as connection:
                        connection.execute("CREATE DATABASE lifecycle_restored")
                    dump.seek(0)
                    self.run(
                        [
                            self.docker,
                            "exec",
                            "-i",
                            self.container,
                            "pg_restore",
                            "-U",
                            "deanery",
                            "--exit-on-error",
                            "-d",
                            "lifecycle_restored",
                        ],
                        stdin=dump,
                        env=clean_environment(),
                    )
                self.stop_web()
                self.db_name = "lifecycle_restored"
                self.env["DB_NAME"] = self.db_name
                self.start_web()
                self.verify_browser(page, detail, session=True)
                self.verify_browser(page, detail)
                self.manage("seed_demo", "--anchor-date=2026-11-02")
                assert self.snapshot() == baseline
                assert self.snapshot("lifecycle_source") == baseline
                self.stages.append("dump_restore_other_database_login_isolation_seed")
            finally:
                browser.close()

    def cleanup(self):
        failures = []
        try:
            self.stop_web()
        except Exception:
            failures.append("web")
        for kind, name, flag in [
            ("container", self.container, "container_created"),
            ("volume", self.volume, "volume_created"),
        ]:
            if not getattr(self, flag):
                continue
            try:
                if self.resource_absent(kind, name):
                    setattr(self, flag, False)
                    continue
                self.owned(kind, name)
                if kind == "container":
                    self.docker_run("rm", "--force", name)
                else:
                    self.docker_run("volume", "rm", name)
                self.require_absent(kind, name)
                setattr(self, flag, False)
            except Exception:
                failures.append(kind)
        if self.private and self.web is None:
            self.private.cleanup()
            self.private = None
        if failures:
            raise RuntimeError("Owned resource cleanup incomplete")


def interrupted(signum, frame):
    raise RuntimeError("Lifecycle interrupted")


def main():
    if not __debug__:
        print(
            json.dumps(
                {
                    "ok": False,
                    "failure_type": "OptimizedPythonUnsupported",
                    "cleanup_complete": True,
                }
            )
        )
        return 2
    signal.signal(signal.SIGTERM, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker", default="docker", help="Docker executable (one argument)")
    args = parser.parse_args()
    rehearsal = Rehearsal(args.docker)
    success = False
    failure = None
    failure_location = None
    try:
        rehearsal.execute()
        success = True
    except (Exception, KeyboardInterrupt) as error:
        # Exception text/output can contain rows, credentials or cookies; print only its class.
        failure = type(error).__name__
        frame = traceback.extract_tb(error.__traceback__)[-1]
        failure_location = f"{Path(frame.filename).name}:{frame.lineno}"
    finally:
        try:
            rehearsal.cleanup()
        except (Exception, KeyboardInterrupt) as error:
            success = False
            failure = "Cleanup" + type(error).__name__
    print(
        json.dumps(
            {
                "ok": success,
                "failure_type": failure,
                "failure_location": failure_location,
                "stages": rehearsal.stages,
                "owned_container": rehearsal.container,
                "owned_volume": rehearsal.volume,
                "cleanup_complete": not rehearsal.container_created
                and not rehearsal.volume_created
                and rehearsal.web is None,
            }
        )
    )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
