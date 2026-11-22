#!/usr/bin/env python3
"""Owned local Docker/TLS rehearsal. No existing target or private user env is accepted."""

import argparse
import hashlib
import io
import ipaddress
import json
import os
import re
import secrets
import signal
import socket
import ssl
import subprocess
import tarfile
import tempfile
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
LABEL = "deanery.d02.owner"
CONTEXT_FILES = ["pyproject.toml", "uv.lock", "manage.py"]
CONTEXT_DIRS = ["apps", "config", "static"]

NOTICE_ROOT = "docs/third-party/runtime-notices"
NOTICE_MANIFEST_SHA256 = "dbe344eb0f8582748997058d10393efa0c76d725d39cc34e570210975d705ff9"
NOTICE_TARGET = "/usr/share/doc/deanery/third-party/"


def qa_caddyfile(source):
    """Use an explicit private CA without installing it in container trust stores."""
    global_start = "\n{\n\tadmin off\n"
    site_start = "{$SITE_DOMAIN} {"
    if (
        source.count(global_start) != 1
        or len(re.findall(r"^\{$", source, re.MULTILINE)) != 1
        or source.count(site_start) != 1
        or "skip_install_trust" in source
    ):
        raise RuntimeError("Unexpected production Caddyfile structure")
    return source.replace(global_start, "\n{\n\tskip_install_trust\n\tadmin off\n", 1).replace(
        site_start, "localhost {\n\ttls internal", 1
    )


def runtime_notice_files():
    base = ROOT / NOTICE_ROOT
    manifest_bytes = (base / "manifest.json").read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != NOTICE_MANIFEST_SHA256:
        raise RuntimeError("Unreviewed notice manifest")
    manifest = json.loads(manifest_bytes)
    records = [f for c in manifest["components"] for f in c["files"]]
    records += manifest["supplementary"]
    expected = {r["path"]: r["sha256"] for r in records}
    expected["manifest.json"] = NOTICE_MANIFEST_SHA256
    found = {}
    for path in base.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("Notice bundle cannot include symlinks")
        if path.is_file():
            relative = str(path.relative_to(base))
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != expected.get(relative):
                raise RuntimeError("Notice bundle hash mismatch")
            found[NOTICE_ROOT + "/" + relative] = data
    if len(found) != len(expected):
        raise RuntimeError("Incomplete notice bundle")
    return found


def expected_notice_hashes():
    return {
        NOTICE_TARGET + name.removeprefix(NOTICE_ROOT + "/"): hashlib.sha256(data).hexdigest()
        for name, data in runtime_notice_files().items()
    }


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def require_local_endpoint(endpoint):
    if endpoint.startswith("unix:///") and not endpoint.startswith("unix:////"):
        return
    if endpoint.startswith("npipe:////./pipe/") and endpoint.removeprefix("npipe:////./pipe/"):
        return
    raise RuntimeError("Only local Docker daemon endpoints are allowed")


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def wait_for(check, message, seconds=75):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if check():
                return
        except (OSError, URLError, RuntimeError, subprocess.CalledProcessError):
            pass
        time.sleep(0.5)
    raise RuntimeError(message)


class Rehearsal:
    def __init__(self, docker, retain):
        self.docker = docker
        self.empty_env_file = "NUL" if Path(docker).name.lower().endswith(".exe") else "/dev/null"
        self.retain = retain
        self.owner = uuid.uuid4().hex
        self.project = "deanery-d02-" + self.owner
        self.images = []
        self.created = False
        self.private = Path(tempfile.mkdtemp(prefix="deanery-d02-"))
        self.port, self.http_port = free_port(), free_port()
        self.password = secrets.token_urlsafe(32)
        self.environment = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE"}
        }
        self.environment["COMPOSE_DISABLE_ENV_FILE"] = "1"
        self.url = f"https://localhost:{self.port}"
        self.results = {}

    def command(self, *args, data=None, timeout=120):
        # Never surface Docker stderr: it can quote an interpolated secret configuration.
        result = subprocess.run(
            [self.docker, *args],
            input=data,
            capture_output=True,
            timeout=timeout,
            env=self.environment,
        )
        if result.returncode:
            failure = self.private / "last-error.txt"
            failure.write_bytes(result.stderr)
            failure.chmod(0o600)
            raise RuntimeError(f"Docker command failed ({args[0]}, exit {result.returncode})")
        return result.stdout

    def compose(self, *args, timeout=120):
        return self.command(
            "compose",
            "--env-file",
            self.empty_env_file,
            "-p",
            self.project,
            "-f",
            "-",
            *args,
            data=json.dumps(self.spec).encode(),
            timeout=timeout,
        )

    def build(self, suffix, dockerfile, files):
        tag = self.project + ":" + suffix
        if self.inspect_resource("image", tag) is not None:
            raise RuntimeError("Refusing pre-existing image tag")
        self.images.append(tag)  # Track before mutation, including timeout-after-create.
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as tar:
            for name, content in files.items():
                info = tarfile.TarInfo(name)
                info.size = len(content)
                info.mode = 0o644
                tar.addfile(info, io.BytesIO(content))
        self.command(
            "build",
            "--label",
            f"{LABEL}={self.owner}",
            "-t",
            tag,
            "-f",
            dockerfile,
            "-",
            data=archive.getvalue(),
            timeout=600,
        )
        return tag

    def setup(self):
        endpoint = json.loads(self.command("context", "inspect"))[0]["Endpoints"]["docker"]["Host"]
        require_local_endpoint(endpoint)
        networks = json.loads(
            self.command("network", "ls", "--format", "json")
            .decode()
            .strip()
            .replace("}\n{", "},{")
            .join(["[", "]"])
        )
        occupied = []
        for network in networks:
            details = json.loads(self.command("network", "inspect", network["ID"]))[0]
            occupied.extend(
                ipaddress.ip_network(x["Subnet"])
                for x in (details["IPAM"]["Config"] or [])
                if x.get("Subnet")
            )
        subnet = next(
            ipaddress.ip_network(f"172.29.{number}.0/28")
            for number in range(10, 250)
            if not any(
                ipaddress.ip_network(f"172.29.{number}.0/28").overlaps(net)
                for net in occupied
                if net.version == 4
            )
        )
        app_files = {name: (ROOT / name).read_bytes() for name in CONTEXT_FILES}
        for directory in CONTEXT_DIRS:
            for path in (ROOT / directory).rglob("*"):
                if (
                    path.is_file()
                    and "__pycache__" not in path.parts
                    and path.suffix not in {".pyc", ".pem", ".key"}
                    and not path.name.startswith(".env")
                ):
                    if path.is_symlink():
                        raise RuntimeError("Build allowlist cannot include symlinks")
                    app_files[str(path.relative_to(ROOT))] = path.read_bytes()
        for name in ["deploy/Dockerfile", "docs/third-party/libargon2-LICENSE.txt"]:
            app_files[name] = (ROOT / name).read_bytes()
        app_files.update(runtime_notice_files())
        app = self.build("app", "deploy/Dockerfile", app_files)
        pg = self.build(
            "db",
            "Dockerfile",
            {
                "Dockerfile": (ROOT / "deploy/Dockerfile.postgres").read_bytes(),
                "deploy/postgres-init.sh": (ROOT / "deploy/postgres-init.sh").read_bytes(),
                **runtime_notice_files(),
            },
        )
        caddyfile = qa_caddyfile((ROOT / "deploy/Caddyfile").read_text())
        caddy = self.build(
            "caddy",
            "Dockerfile",
            {
                "Dockerfile": (ROOT / "deploy/Dockerfile.caddy").read_bytes(),
                "deploy/Caddyfile": caddyfile.encode(),
                **runtime_notice_files(),
            },
        )
        env = {
            "DJANGO_SETTINGS_MODULE": "config.settings.production",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(64),
            "DJANGO_ALLOWED_HOSTS": "localhost",
            "DJANGO_CSRF_TRUSTED_ORIGINS": self.url,
            "DJANGO_TRUSTED_PROXY_CIDRS": str(subnet),
            "DB_NAME": "deanery",
            "DB_USER": "deanery_app",
            "DB_PASSWORD": secrets.token_urlsafe(32),
            "DB_HOST": "db",
            "DB_PORT": "5432",
        }
        db_env = {key: env[key] for key in ["DB_NAME", "DB_USER", "DB_PASSWORD"]}
        db_env.update(
            POSTGRES_USER="deanery_bootstrap",
            POSTGRES_DB="postgres",
            POSTGRES_PASSWORD=secrets.token_urlsafe(32),
            POSTGRES_INITDB_ARGS="--auth-host=scram-sha-256",
        )
        # Exact production definition, transformed only for private local QA.
        # No private operator env file is read; inject own generated environment.
        production = (ROOT / "deploy/compose.production.yaml").read_text()
        production = "\n".join(line for line in production.splitlines() if "env_file:" not in line)
        substitutions = {
            "APP_IMAGE": app,
            "POSTGRES_IMAGE": pg,
            "CADDY_IMAGE": caddy,
            "SITE_DOMAIN": "localhost",
            "DJANGO_TRUSTED_PROXY_CIDRS": str(subnet),
        }
        substitutions.update(env)
        substitutions.update(db_env)
        for key, value in substitutions.items():
            production = re.sub(r"\$\{" + key + r":?\?[^}]+\}", value, production)
        self.spec = json.loads(
            self.command(
                "compose",
                "--env-file",
                self.empty_env_file,
                "-p",
                self.project,
                "-f",
                "-",
                "config",
                "--format",
                "json",
                data=production.encode(),
            )
        )
        self.spec["services"]["app"]["environment"] = env
        self.spec["services"]["db"]["environment"] = db_env
        self.spec["services"]["caddy"]["ports"] = [
            {"target": 80, "published": str(self.http_port), "host_ip": "127.0.0.1"},
            {"target": 443, "published": str(self.port), "host_ip": "127.0.0.1"},
        ]
        for group in ["services", "networks", "volumes"]:
            for name, resource in self.spec[group].items():
                resource.setdefault("labels", {})[LABEL] = self.owner
                if group != "services":
                    resource["name"] = self.project + "_" + name
        state = self.private / "state.json"
        state.write_text(
            json.dumps(
                {
                    "project": self.project,
                    "owner": self.owner,
                    "spec": self.spec,
                    "password": self.password,
                }
            )
        )
        state.chmod(0o600)
        self.created = True
        self.compose("up", "-d", "db")
        wait_for(
            lambda: (
                b"healthy"
                == self.command(
                    "inspect", "--format", "{{.State.Health.Status}}", self.container("db")
                ).strip()
            ),
            "PostgreSQL health failed",
        )
        self.compose("run", "--rm", "app", "python", "manage.py", "migrate", "--noinput")
        demo_variables = [
            "DEMO_STUDENT_ONE_PASSWORD",
            "DEMO_STUDENT_TWO_PASSWORD",
            "DEMO_OPERATOR_PASSWORD",
        ]
        for variable in demo_variables:
            env[variable] = self.password
        try:
            self.compose("run", "--rm", "app", "python", "manage.py", "seed_demo")
        finally:
            for variable in demo_variables:
                del env[variable]
        self.compose("up", "-d", "app", "caddy")
        wait_for(
            lambda: self.status("/health/ready/", insecure=True)[0] == 200,
            "TLS/app readiness failed",
        )
        # Copy the public local CA certificate only, never its private key or host trust store.
        archive = self.command(
            "cp", self.container("caddy") + ":/data/caddy/pki/authorities/local/root.crt", "-"
        )
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            certificate = tar.extractfile(tar.getmembers()[0]).read()
        self.ca = self.private / "root.crt"
        self.ca.write_bytes(certificate)
        self.tls = ssl.create_default_context(cafile=str(self.ca))
        self.results["tls_trusted_private_ca"] = self.status("/health/ready/")[0] == 200

    def container(self, service):
        return self.project + "-" + service + "-1"

    def status(self, path, *, insecure=False, http=False, headers=None, data=None):
        context = ssl._create_unverified_context() if insecure else getattr(self, "tls", None)
        opener = build_opener(HTTPSHandler(context=context), NoRedirect())
        url = f"http://localhost:{self.http_port}" if http else self.url
        try:
            response = opener.open(
                Request(url + path, headers=headers or {}, data=data), timeout=10
            )
        except HTTPError as error:
            response = error
        return response.status, dict(response.headers), response.read()

    def shell(self, source):
        return self.compose("exec", "-T", "app", "python", "manage.py", "shell", "-c", source)

    def login(self, page, user):
        page.goto(self.url + "/login/")
        page.locator('[name="username"]').fill(user)
        page.locator('[name="password"]').fill(self.password)
        page.locator('button[type="submit"]').click()
        assert not page.url.endswith("/login/"), "TLS browser login failed"

    def smoke(self):
        assert self.status("/login/", http=True, headers={"X-Forwarded-Proto": "https"})[0] in (
            301,
            308,
        )
        self.results["http_xfp_redirect"] = True
        status, headers, _ = self.status("/login/")
        assert status == 200 and "unsafe-" not in headers["Content-Security-Policy"]
        assert headers["X-Frame-Options"] == "DENY"
        self.results["https_security_headers"] = True
        sentinel = "d02-private-sentinel-" + self.owner
        private_headers = {
            "Cookie": "private=" + sentinel,
            "Authorization": "Bearer " + sentinel,
            "X-Private-QA": sentinel,
        }
        assert (
            self.status(
                "/login/?private=" + sentinel,
                headers=private_headers,
                data=sentinel.encode() + b"x" * (70000 - len(sentinel)),
            )[0]
            == 413
        )
        self.results["sentinel_body_limit_413"] = True
        assert (
            self.status(
                "/login/?private=" + sentinel, headers=private_headers, data=sentinel.encode()
            )[0]
            == 403
        )
        assert (
            self.status("/missing-" + sentinel + "/?private=" + sentinel, headers=private_headers)[
                0
            ]
            == 404
        )
        sentinel = "d02-private-sentinel-" + self.owner
        self.status(
            "/missing/?private=" + sentinel,
            headers={"Cookie": "private=" + sentinel},
            data=sentinel.encode(),
        )
        self.results["http_redirect_csrf_body_headers"] = True
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            # Chromium context bypasses platform certificate trust only. urllib above validates
            # chain+hostname against the explicitly copied private QA CA (not a public cert).
            context = browser.new_context(
                ignore_https_errors=True, viewport={"width": 360, "height": 800}
            )
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on(
                "console",
                lambda message: (
                    errors.append(message.text)
                    if message.type == "error" and "Content Security Policy" in message.text
                    else None
                ),
            )
            self.login(page, "student.one")
            for path in ["/profile/", "/schedule/", "/grades/", "/notifications/"]:
                assert page.goto(self.url + path).status == 200
            page.goto(self.url + "/requests/new/")
            page.locator('[name="purpose"]').select_option("presentation")
            page.locator('[name="comment"]').fill("Вымышленная проверка TLS.")
            page.locator('form.request-form button[type="submit"]').click()
            detail = page.url.removeprefix(self.url)
            assert detail.startswith("/requests/") and detail != "/requests/new/"
            assert "no-store" in page.goto(page.url).headers["cache-control"]
            assert page.locator(".request-status").count() == 1
            cookies = context.cookies()
            assert all(c["secure"] and c["sameSite"] == "Lax" for c in cookies)
            assert all(c["httpOnly"] for c in cookies if c["name"] == "sessionid")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            static_urls = page.locator('script[src],link[rel="stylesheet"]').evaluate_all(
                "els => els.map(e => e.src || e.href)"
            )
            assert static_urls and all(
                self.status(url.removeprefix(self.url))[0] == 200 for url in static_urls
            )
            other = browser.new_context(ignore_https_errors=True)
            second = other.new_page()
            self.login(second, "student.two")
            assert second.goto(self.url + detail).status == 404
            operator = browser.new_context(
                ignore_https_errors=True, viewport={"width": 1440, "height": 1000}
            )
            op = operator.new_page()
            self.login(op, "operator.demo")
            assert op.goto(self.url + "/operator/requests/").status == 200
            assert op.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert op.goto(self.url + "/operator" + detail).status == 200
            op.locator('[name="desired_status"]').select_option("in_progress")
            op.locator('form.request-form button[type="submit"]').click()
            assert op.locator(".request-status").inner_text() == "В работе"
            self.compose("restart", "app", "db")
            wait_for(lambda: self.status("/health/ready/")[0] == 200, "Restart did not recover")
            assert page.goto(self.url + detail).status == 200
            assert page.locator(".request-status").inner_text() == "В работе"
            # Shared-cookie login rotation must refresh an older tab through the readable
            # CSRF marker. This covers the production cookie/proxy combination in ADR001.
            sibling = context.new_page()
            sibling.goto(self.url + "/")
            sibling.locator('form[action="/logout/"] button').click()
            page.evaluate("window.dispatchEvent(new Event('focus'))")
            page.wait_for_url("**/login/**")
            self.login(sibling, "student.two")
            page.goto(self.url + "/profile/")
            assert page.goto(self.url + detail).status == 404
            assert not errors, "Browser CSP/script error"
            browser.close()
        self.results["tls_browser_3roles_360_1440_persistence_isolation_static"] = True
        self.compose("stop", "db")
        try:
            assert (
                self.status("/health/ready/?private=" + sentinel, headers=private_headers)[0] == 503
            )
            assert self.status("/health/live/")[0] == 200
        finally:
            self.compose("start", "db")
        wait_for(lambda: self.status("/health/ready/")[0] == 200, "DB recovery failed")
        self.results["readiness_db_stop_recovery"] = True
        self.compose("stop", "app")
        try:
            code, _, body = self.status(
                "/missing-" + sentinel + "/?private=" + sentinel, headers=private_headers
            )
            assert code == 502 and b"Traceback" not in body
        finally:
            self.compose("start", "app")
        wait_for(lambda: self.status("/health/ready/")[0] == 200, "App recovery failed")
        wait_for(
            lambda: (
                self.command(
                    "inspect", "--format", "{{.State.Health.Status}}", self.container("app")
                ).strip()
                == b"healthy"
            ),
            "Real app Docker healthcheck failed",
        )
        self.results["upstream_unavailable_502_app_health"] = True
        flags = self.shell(
            "from django.db import connection; "
            "c=connection.cursor(); "
            "c.execute('SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles "
            "WHERE rolname=current_user'); "
            "assert c.fetchone()==(False,False,False); "
            "print('role-safe')"
        )
        assert b"role-safe" in flags
        self.compose("exec", "-T", "app", "python", "manage.py", "check", "--deploy")
        self.results["deploy_check_hsts_pending"] = True
        self.results["app_non_superuser"] = True
        info = json.loads(self.command("inspect", self.container("app")))[0]
        assert info["Config"]["User"] == "10001:10001" and info["HostConfig"]["ReadonlyRootfs"]
        assert not info["HostConfig"]["PortBindings"]
        assert info["HostConfig"]["CapDrop"] == ["ALL"]
        closure = self.compose(
            "exec",
            "-T",
            "app",
            "python",
            "-c",
            "import importlib.metadata as m,json,sys; "
            "names=sorted(d.metadata['Name'].lower() for d in m.distributions()); "
            "assert not set(names)&{'pytest','playwright','ruff','uv'}; "
            "print(json.dumps({'python':sys.version.split()[0],'packages':names}))",
        )
        self.results["runtime"] = json.loads(closure)
        assert not self.command(
            "exec", self.container("app"), "sh", "-c", "command -v uv || command -v gcc || true"
        ).strip()
        assert b"runtime-files-safe" in self.compose(
            "exec",
            "-T",
            "app",
            "python",
            "-c",
            "from pathlib import Path; "
            "assert not any(Path(p).exists() for p in ['/app/tests','/app/.git','/app/.env']); "
            "assert not list(Path('/usr/local/lib/python3.13/site-packages').glob('pip*')); "
            "assert not list(Path('/usr/local/lib/python3.13/ensurepip').rglob('*.whl')); "
            "print('runtime-files-safe')",
        )
        for tag in self.images:
            history = self.command(
                "image", "history", "--no-trunc", "--format", "{{.CreatedBy}}", tag
            )
            for variable, value in self.spec["services"]["app"]["environment"].items():
                if "PASSWORD" in variable or "SECRET" in variable:
                    assert value.encode() not in history
            assert self.password.encode() not in history
        for service in ["app", "db", "caddy"]:
            inventory = self.compose(
                "exec",
                "-T",
                service,
                "sh",
                "-c",
                "find /usr/share/doc/deanery/third-party -type f -exec sha256sum {} +",
            )
            actual = {
                line.split(None, 1)[1]: line.split(None, 1)[0]
                for line in inventory.decode().splitlines()
            }
            assert actual == expected_notice_hashes()
        self.results["notice_bundle_all_images_verified_files"] = len(expected_notice_hashes())
        self.results["runtime_nonroot_readonly_internal_no_dev"] = True
        # Two failed attempts with distinct spoof headers must share a single Axes key.
        for spoof in ["192.0.2.1", "198.51.100.2"]:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                context = browser.new_context(
                    ignore_https_errors=True,
                    extra_http_headers={"X-Real-IP": spoof, "X-Forwarded-For": spoof},
                )
                page = context.new_page()
                page.goto(self.url + "/login/")
                page.locator('[name="username"]').fill("spoof.qa")
                page.locator('[name="password"]').fill("fictional-wrong-password")
                page.locator('button[type="submit"]').click()
                browser.close()
        assert b"axes-safe" in self.shell(
            "from axes.models import AccessAttempt; "
            "a=AccessAttempt.objects.filter(username='spoof.qa'); "
            "assert a.count()==1 and a.get().failures_since_start==2; "
            "assert a.get().ip_address not in ['192.0.2.1','198.51.100.2']; "
            "print('axes-safe')"
        )
        self.results["spoofed_client_headers_axes_key_unchanged"] = True
        logs = self.logs("app") + self.logs("caddy")
        assert ("d02-private-sentinel-" + self.owner).encode() not in logs
        assert self.password.encode() not in logs
        app_logs = self.logs("app")
        assert re.search(rb"INFO deanery.http request_id=[a-f0-9]{32} route=", app_logs)
        self.results["safe_source_request_logs_preserved"] = True
        caddy_logs = self.logs("caddy")
        events = [json.loads(line) for line in caddy_logs.splitlines() if line.strip()]
        allowed = {"level", "ts", "logger", "status", "duration", "err_id"}
        self.results["caddy_log_observation"] = {
            "events": len(events),
            "unexpected_field_count": sum(len(set(e) - allowed) for e in events),
            "tls_maintenance_events": sum(
                e.get("logger") == "tls.cache.maintenance" for e in events
            ),
            "upstream_502_events": sum(
                e.get("logger") == "http.log.error" and e.get("status") == 502 for e in events
            ),
        }
        assert events and all(set(event) <= allowed for event in events)
        assert all(
            e.get("logger") in {"http.log.error", "tls.cache.maintenance", "tls.obtain"}
            and e.get("level") in {"debug", "info", "warn", "error"}
            and isinstance(e.get("ts"), (int, float))
            for e in events
        )
        assert any(e.get("logger") == "tls.cache.maintenance" for e in events)
        assert any(e.get("logger") == "http.log.error" and e.get("status") == 502 for e in events)
        self.results["caddy_operational_logs"] = {
            "events": len(events),
            "levels": sorted({e["level"] for e in events}),
            "logger_counts": {
                name: sum(e["logger"] == name for e in events)
                for name in sorted({e["logger"] for e in events})
            },
            "keys": sorted(set().union(*(set(e) for e in events))),
            "upstream_failure": True,
            "tls_maintenance": True,
            "private_sentinels_absent": True,
        }
        app_env = json.loads(self.command("inspect", self.container("app")))[0]["Config"]["Env"]
        caddy_env = json.loads(self.command("inspect", self.container("caddy")))[0]["Config"]["Env"]
        assert not any(value.startswith("POSTGRES_") for value in app_env + caddy_env)
        self.results["safe_logs_sentinel_bootstrap_secret_not_in_app"] = True

    def logs(self, service):
        container = self.container(service)
        info = self.inspect_resource("container", container)
        if info is None:
            raise RuntimeError("Owned log container missing")
        self.require_owner(info, "container")
        result = subprocess.run(
            [self.docker, "logs", container], capture_output=True, timeout=30, env=self.environment
        )
        if result.returncode:
            raise RuntimeError("Cannot read owned container logs")
        return result.stdout + result.stderr

    def inspect_resource(self, kind, name):
        result = subprocess.run(
            [self.docker, kind, "inspect", name],
            capture_output=True,
            timeout=30,
            env=self.environment,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)[0]
        if any(
            marker in result.stderr.lower()
            for marker in [
                b"no such image",
                b"no such object",
                b"no such container",
                b"no such volume",
                b"network " + name.encode() + b" not found",
            ]
        ):
            return None
        raise RuntimeError("Cannot confirm resource absence")

    def require_owner(self, info, kind):
        labels = (
            info["Config"].get("Labels") if kind in {"container", "image"} else info.get("Labels")
        )
        if not labels or labels.get(LABEL) != self.owner:
            raise RuntimeError("Resource ownership mismatch")

    def cleanup(self):
        failures = []
        if self.created:
            for kind, list_args in [
                ("container", ["ps", "-aq"]),
                ("volume", ["volume", "ls", "-q"]),
                ("network", ["network", "ls", "-q"]),
            ]:
                try:
                    ids = (
                        self.command(
                            *list_args,
                            "--filter",
                            f"label=com.docker.compose.project={self.project}",
                        )
                        .decode()
                        .split()
                    )
                    for resource in ids:
                        info = self.inspect_resource(kind, resource)
                        if info is None:
                            continue
                        self.require_owner(info, kind)
                        action = ["rm", "-f"] if kind == "container" else [kind, "rm"]
                        self.command(*action, resource)
                        if self.inspect_resource(kind, resource) is not None:
                            raise RuntimeError("Resource still exists after cleanup")
                except Exception as error:
                    failures.append(type(error).__name__)
        for tag in self.images:
            try:
                info = self.inspect_resource("image", tag)
                if info is None:
                    continue
                self.require_owner(info, "image")
                self.command("image", "rm", tag)
                if self.inspect_resource("image", tag) is not None:
                    raise RuntimeError("Image still exists after cleanup")
            except Exception as error:
                failures.append(type(error).__name__)
        if failures:
            raise RuntimeError("Owned cleanup incomplete")
        for path in self.private.iterdir():
            path.unlink()
        self.private.rmdir()


def main():
    if not __debug__:
        print('{"status":"failed","failure":{"phase":"preflight","type":"OptimizedPython"}}')
        return 1

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker", default="docker")
    parser.add_argument(
        "--retain",
        action="store_true",
        help="Keep own QA resources/private state for immediate independent review",
    )
    args = parser.parse_args()
    rehearsal = Rehearsal(args.docker, args.retain)
    phase = "setup"
    failure = None
    try:
        rehearsal.setup()
        phase = "smoke"
        rehearsal.smoke()
    except (Exception, KeyboardInterrupt) as error:
        failure = {"phase": phase, "type": type(error).__name__}
    if args.retain:
        cleanup = "retained"
        print("Own QA private state: " + str(rehearsal.private / "state.json"))
    else:
        try:
            rehearsal.cleanup()
            cleanup = "complete"
        except Exception as error:
            cleanup = "failed"
            failure = failure or {"phase": "cleanup", "type": type(error).__name__}
            print("Cleanup incomplete; own private state: " + str(rehearsal.private / "state.json"))
    print(
        json.dumps(
            {
                "status": "failed" if failure else "passed",
                "project": rehearsal.project,
                "cleanup": cleanup,
                "failure": failure,
                "checks": rehearsal.results,
            },
            indent=2,
        )
    )
    return 1 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
