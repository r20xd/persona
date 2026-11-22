#!/usr/bin/env python3
"""Q06: owned localhost-only PostgreSQL/Gunicorn read rehearsal; no external URL/DSN input."""

import argparse
import concurrent.futures
import http.cookiejar
import json
import math
import os
import platform
import re
import signal
import subprocess
import sys
import threading
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, build_opener

import gunicorn

from scripts.verify_data_lifecycle import ROOT, Rehearsal, interrupted, status, wait_for

ROUTES = {
    "/": "Ваш учебный день",
    "/schedule/?date=2026-11-02&view=week": "Расписание",
    "/grades/": "Моя учёба",
    "/session/": "Сессия",
    "/requests/": "Заявки",
    "/notifications/": "Уведомления",
}


def summary(values):
    values = sorted(values)
    if not values:
        raise ValueError("No observations")
    return {
        "count": len(values),
        "p50_ms": round(values[math.ceil(len(values) * 0.5) - 1], 3),
        "p95_ms": round(values[math.ceil(len(values) * 0.95) - 1], 3),
        "max_ms": round(values[-1], 3),
    }


def validate_read(code, final_url, expected_url, body, marker):
    if code != 200 or final_url != expected_url or marker not in body or 'name="password"' in body:
        raise RuntimeError("Invalid authenticated response")


class Performance(Rehearsal):
    def __init__(self, docker, rounds):
        super().__init__(docker)
        self.rounds = rounds
        self.db_name = "performance_source"
        self.env["DB_NAME"] = self.db_name
        self.result = {}
        self.phase = "init"

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
                "2",
                "--threads",
                "4",
                "--timeout",
                "30",
            ],
            cwd=ROOT,
            env=self.env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait_for(
            lambda: self.web.poll() is None and status(self.url + "/health/ready/") == 200,
            "Owned web not ready",
        )

    def login_session(self, index):
        jar = http.cookiejar.CookieJar()
        client = build_opener(HTTPCookieProcessor(jar))
        with client.open(self.url + "/login/", timeout=30) as response:
            html = response.read().decode()
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)[1]
        started = time.perf_counter()
        with client.open(
            self.url + "/login/",
            urlencode(
                {
                    "username": "student.one" if index % 2 == 0 else "student.two",
                    "password": self.password,
                    "csrfmiddlewaretoken": token,
                }
            ).encode(),
            timeout=30,
        ) as response:
            validate_read(
                response.status, response.url, self.url + "/", response.read().decode(), ROUTES["/"]
            )
        return (
            client,
            (time.perf_counter() - started) * 1000,
            next(cookie.value for cookie in jar if cookie.name == "sessionid"),
        )

    def read(self, client, path):
        started = time.perf_counter()
        with client.open(self.url + path, timeout=30) as response:
            validate_read(
                response.status,
                response.url,
                self.url + path,
                response.read().decode(),
                ROUTES[path],
            )
        return (time.perf_counter() - started) * 1000

    def isolation(self, clients):
        # Personal markers are held in memory and never emitted to the report.
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT u.username,p.full_name FROM accounts_studentprofile p "
                "JOIN accounts_user u ON u.id=p.user_id ORDER BY u.username"
            ).fetchall()
            ids = conn.execute(
                "SELECT u.username,r.id FROM requests_servicerequest r "
                "JOIN accounts_studentprofile p ON p.id=r.student_id "
                "JOIN accounts_user u ON u.id=p.user_id ORDER BY u.username"
            ).fetchall()
        assert len(rows) == 2 and len(ids) >= 2
        names = dict(rows)
        requests = dict(ids)
        from urllib.error import HTTPError

        for index, client in enumerate(clients):
            own, other = (
                ("student.one", "student.two") if index % 2 == 0 else ("student.two", "student.one")
            )
            with client.open(self.url + "/profile/", timeout=30) as response:
                text = response.read().decode()
                assert response.status == 200 and names[own] in text and names[other] not in text
            try:
                client.open(self.url + f"/requests/{requests[other]}/", timeout=30)
            except HTTPError as error:
                assert error.code == 404
            else:
                raise RuntimeError("Foreign request exposed")

    def execute(self):
        # Reuse the Q05 creation/cleanup path, but replace its browser exercise below.
        import tempfile
        from urllib.parse import urlparse

        contexts = json.loads(self.docker_run("context", "inspect").stdout)
        endpoint = urlparse(contexts[0]["Endpoints"]["docker"]["Host"])
        if endpoint.scheme not in {"unix", "npipe"} and not (
            endpoint.scheme == "tcp" and endpoint.hostname in {"127.0.0.1", "localhost", "::1"}
        ):
            raise RuntimeError("Docker endpoint must be local")
        self.private = tempfile.TemporaryDirectory(prefix="deanery-q06-")
        self.env["Q05_STATIC_ROOT"] = str(ROOT / self.private.name / "static")
        image = re.search(r"image:\s*(\S+)", (ROOT / "deploy/compose.local.yaml").read_text())[1]
        if not image.startswith("postgres:17.11-") or "@sha256:" not in image:
            raise RuntimeError("Expected pinned PostgreSQL")
        self.require_absent("container", self.container)
        self.create_owned(
            "container",
            "create",
            "--name",
            self.container,
            "--label",
            f"deanery.q05.owner={self.owner}",
            "--publish",
            f"127.0.0.1:{self.port}:5432",
            "--tmpfs",
            "/var/lib/postgresql/data",
            "--env",
            "POSTGRES_HOST_AUTH_METHOD=trust",
            "--env",
            "POSTGRES_USER=deanery",
            "--env",
            f"POSTGRES_DB={self.db_name}",
            image,
        )
        self.phase = "self.container_action"
        self.container_action("start")
        wait_for(self.ready_db, "Owned PostgreSQL not ready")
        with self.connection() as connection:
            assert connection.info.server_version == 170011
        self.phase = "self.manage"
        self.manage("migrate", "--noinput")
        self.phase = "self.manage"
        self.manage("seed_demo", "--anchor-date=2026-11-02")
        self.phase = "self.manage"
        self.manage("collectstatic", "--noinput")
        self.phase = "audit = self.run"
        audit = self.run(
            [sys.executable, "-m", "scripts.performance_queries"], cwd=ROOT, env=self.env
        )
        self.result["query_audit"] = json.loads(audit.stdout)
        self.phase = "self.start_web"
        self.start_web()
        clients, logins, session_keys = [], [], set()
        for index in range(20):
            client, elapsed, session_key = self.login_session(index)
            assert session_key not in session_keys
            session_keys.add(session_key)
            clients.append(client)
            logins.append(elapsed)
        self.isolation(clients)
        with clients[0].open(self.url + "/", timeout=30) as response:
            stylesheet = re.search(r'<link[^>]+href="([^"]+\.css)"', response.read().decode())[1]
        assert stylesheet.startswith("/static/")
        with clients[0].open(self.url + stylesheet, timeout=30) as response:
            assert response.status == 200 and response.read()
        for client in clients:
            for path in ROUTES:
                self.read(client, path)
        barrier = threading.Barrier(20)

        def reader(index):
            observations = []
            for _ in range(self.rounds):
                for path in ROUTES:
                    barrier.wait(timeout=60)
                    observations.append((path, self.read(clients[index], path)))
            return observations

        started = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            batches = list(pool.map(reader, range(20)))
        elapsed = time.perf_counter() - started
        self.isolation(clients)
        observations = [item for batch in batches for item in batch]
        overall = summary([duration for _, duration in observations])
        self.result.update(
            {
                "read": {
                    path: summary([ms for route, ms in observations if route == path])
                    for path in ROUTES
                },
                "overall": overall,
                "login": summary(logins),
                "functional_failures": 0,
                "non200": 0,
                "http5xx": 0,
                "unexpected_redirects": 0,
                "target_met": overall["p95_ms"] < 1000,
                "sessions": 20,
                "rounds": self.rounds,
                "warmup_reads": 20 * len(ROUTES),
                "read_seconds": round(elapsed, 3),
                "percentile": "nearest rank ceil(n*p)",
                "python": platform.python_version(),
                "kernel": platform.release(),
                "cpu_count": os.cpu_count(),
                "gunicorn": {"workers": 2, "threads_per_worker": 4},
                "memory_total_kib": int(
                    re.search(r"MemTotal:\s+(\d+)", Path("/proc/meminfo").read_text())[1]
                ),
                "postgres": "17.11",
                "storage": "tmpfs; warm-read smoke, not a disk benchmark",
                "gunicorn_version": gunicorn.__version__,
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "argon2": "unchanged configured Django Argon2PasswordHasher; sequential login",
                "conn_max_age": 0,
                "scope": "localhost only; not a production capacity guarantee",
            }
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker", default="docker")
    parser.add_argument("--rounds", type=int, choices=range(2, 11), default=3)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupted)
    rehearsal = Performance(args.docker, args.rounds)
    ok, failure, location = False, None, None
    try:
        if not __debug__:
            raise RuntimeError("Optimized Python unsupported")
        rehearsal.execute()
        ok = True
    except (Exception, KeyboardInterrupt) as error:
        failure = type(error).__name__
        frame = traceback.extract_tb(error.__traceback__)[-1]
        location = f"{os.path.basename(frame.filename)}:{frame.lineno}"
    finally:
        try:
            rehearsal.cleanup()
        except (Exception, KeyboardInterrupt) as error:
            ok, failure = False, "Cleanup" + type(error).__name__
    print(
        json.dumps(
            {
                **rehearsal.result,
                "ok": ok,
                "functional_failure": not ok,
                "failure_type": failure,
                "failure_location": location,
                "phase": rehearsal.phase,
                "cleanup_complete": not rehearsal.container_created and rehearsal.web is None,
            }
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
