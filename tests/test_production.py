from ipaddress import ip_network

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, override_settings

from apps.accounts.proxy import client_ip, trusted_networks
from tests.test_foundation import settings_process


def test_qa_caddyfile_keeps_snippet_and_scopes_trust_option_to_global_block():
    from scripts.verify_production import ROOT, qa_caddyfile

    source = (ROOT / "deploy/Caddyfile").read_text()
    result = qa_caddyfile(source)
    assert result.startswith(source.split("\n{\n", 1)[0] + "\n{\n\tskip_install_trust\n")
    assert result.count("skip_install_trust") == 1
    assert result.count("localhost {\n\ttls internal") == 1
    assert (
        result.replace("\tskip_install_trust\n", "", 1).replace(
            "localhost {\n\ttls internal", "{$SITE_DOMAIN} {", 1
        )
        == source
    )


@pytest.mark.parametrize(
    "change", ["duplicate_global", "missing_admin", "duplicate_site", "already_qa"]
)
def test_qa_caddyfile_rejects_unexpected_production_structure(change):
    from scripts.verify_production import ROOT, qa_caddyfile

    source = (ROOT / "deploy/Caddyfile").read_text()
    source = {
        "duplicate_global": source + "\n{\n}\n",
        "missing_admin": source.replace("\tadmin off", "\tadmin localhost:2019"),
        "duplicate_site": source + "\n{$SITE_DOMAIN} {\n}\n",
        "already_qa": source + "\n# skip_install_trust\n",
    }[change]
    with pytest.raises(RuntimeError, match="Unexpected production Caddyfile structure"):
        qa_caddyfile(source)


@pytest.mark.parametrize("value", ["", "0.0.0.0/0", "::/0", "bad", "172.30.1.1/24"])
def test_proxy_network_configuration_rejects_unsafe_values(value):
    with pytest.raises(ImproperlyConfigured):
        trusted_networks(value)


@pytest.mark.parametrize(
    "peer,header,expected",
    [
        ("172.30.90.3", "192.0.2.1", "192.0.2.1"),
        ("172.30.90.3", "192.0.2.1, 192.0.2.2", "172.30.90.3"),
        ("172.30.90.3", "garbage", "172.30.90.3"),
        ("172.30.91.3", "192.0.2.1", "172.30.91.3"),
        ("garbage", "192.0.2.1", None),
    ],
)
def test_proxy_ip_only_trusts_single_valid_header_from_allowed_peer(peer, header, expected):
    with override_settings(TRUSTED_PROXY_NETWORKS=(ip_network("172.30.90.0/28"),)):
        request = RequestFactory().get("/", REMOTE_ADDR=peer, HTTP_X_REAL_IP=header)
        assert client_ip(request) == expected


def test_collectstatic_settings_need_no_database_or_secrets():
    assert settings_process("config.settings.build").returncode == 0


@pytest.mark.parametrize(
    "peer,header,expected",
    [
        ("fd00:1234::2", "2001:db8::1", "2001:db8::1"),
        ("fd00:5678::2", "2001:db8::1", "fd00:5678::2"),
        ("fd00:1234::2", "2001:db8::1, 2001:db8::2", "fd00:1234::2"),
    ],
)
def test_proxy_ipv6_peer_validation(peer, header, expected):
    with override_settings(TRUSTED_PROXY_NETWORKS=(ip_network("fd00:1234::/64"),)):
        request = RequestFactory().get("/", REMOTE_ADDR=peer, HTTP_X_REAL_IP=header)
        assert client_ip(request) == expected


def test_production_health_exemptions_are_exact(monkeypatch):
    import importlib

    from django.http import HttpResponse
    from django.middleware.security import SecurityMiddleware

    from tests.test_foundation import production_env

    for key, value in production_env().items():
        monkeypatch.setenv(key, value)
    production = importlib.reload(importlib.import_module("config.settings.production"))
    with override_settings(
        SECURE_SSL_REDIRECT=True,
        SECURE_REDIRECT_EXEMPT=production.SECURE_REDIRECT_EXEMPT,
        ALLOWED_HOSTS=["testserver"],
    ):
        middleware = SecurityMiddleware(lambda request: HttpResponse())
        for path in ["/health/live/", "/health/ready/"]:
            assert middleware(RequestFactory().get(path)).status_code == 200
        for path in ["/profile/", "/health/ready/private", "/health/live/extra"]:
            assert middleware(RequestFactory().get(path)).status_code == 301


def test_rehearsal_refuses_unknown_owner_before_mutation():
    from scripts.verify_production import Rehearsal

    rehearsal = Rehearsal.__new__(Rehearsal)
    rehearsal.owner = "our-owner"
    with pytest.raises(RuntimeError, match="ownership"):
        rehearsal.require_owner({"Config": {"Labels": {"deanery.d02.owner": "other"}}}, "image")


def test_rehearsal_failed_build_image_absence_does_not_mask_daemon_error(monkeypatch):
    from types import SimpleNamespace

    from scripts.verify_production import Rehearsal

    rehearsal = Rehearsal.__new__(Rehearsal)
    rehearsal.docker, rehearsal.environment = "docker", {}
    with monkeypatch.context() as scoped:
        scoped.setattr(
            "scripts.verify_production.subprocess.run",
            lambda *a, **k: SimpleNamespace(
                returncode=1, stdout=b"", stderr=b"Error: No such image: owned:app"
            ),
        )
        assert rehearsal.inspect_resource("image", "owned:app") is None
    monkeypatch.setattr(
        "scripts.verify_production.subprocess.run",
        lambda *a, **k: SimpleNamespace(
            returncode=1, stdout=b"", stderr=b"Cannot connect to Docker daemon"
        ),
    )
    with pytest.raises(RuntimeError, match="absence"):
        rehearsal.inspect_resource("image", "owned:app")


def test_rehearsal_failure_output_never_contains_exception_message(monkeypatch, capsys, tmp_path):
    from scripts import verify_production

    class Failed:
        def __init__(self, *args):
            self.project, self.results, self.private = "own-qa", {}, tmp_path

        def setup(self):
            raise RuntimeError("password=private-cookie-secret")

        def cleanup(self):
            pass

    monkeypatch.setattr(verify_production, "Rehearsal", Failed)
    monkeypatch.setattr("sys.argv", ["verify_production.py"])
    assert verify_production.main() == 1
    output = capsys.readouterr().out
    assert "private-cookie" not in output and "Traceback" not in output
    assert '"cleanup": "complete"' in output and '"status": "failed"' in output


@pytest.mark.parametrize(
    "endpoint",
    ["npipe:////./pipe/dockerDesktopLinuxEngine", "unix:///var/run/docker.sock"],
)
def test_rehearsal_accepts_only_local_docker_endpoints(endpoint):
    from scripts.verify_production import require_local_endpoint

    require_local_endpoint(endpoint)


@pytest.mark.parametrize(
    "endpoint",
    [
        "npipe:////server/pipe/docker_engine",
        "tcp://127.0.0.1:2375",
        "ssh://docker.example.org",
        "unix://server/docker.sock",
        "unix:////server/docker.sock",
        "npipe:////./pipe/",
    ],
)
def test_rehearsal_rejects_remote_or_malformed_docker_endpoints(endpoint):
    from scripts.verify_production import require_local_endpoint

    with pytest.raises(RuntimeError, match="local Docker"):
        require_local_endpoint(endpoint)


def test_owned_logs_check_owner_and_capture_container_stderr(monkeypatch):
    from types import SimpleNamespace

    from scripts.verify_production import Rehearsal

    rehearsal = Rehearsal.__new__(Rehearsal)
    rehearsal.project, rehearsal.owner = "own-project", "own-owner"
    rehearsal.docker, rehearsal.environment = "docker", {}
    monkeypatch.setattr(
        rehearsal,
        "inspect_resource",
        lambda *args: {"Config": {"Labels": {"deanery.d02.owner": "own-owner"}}},
    )
    monkeypatch.setattr(
        "scripts.verify_production.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout=b"stdout-event\n", stderr=b"stderr-event\n"
        ),
    )
    assert rehearsal.logs("caddy") == b"stdout-event\nstderr-event\n"
    rehearsal.owner = "different-owner"
    with pytest.raises(RuntimeError, match="ownership"):
        rehearsal.logs("caddy")


def test_clean_static_rebuild_removes_archived_urls_and_preserves_current_assets(tmp_path):
    """Rebuild an old deployment in place, including WhiteNoise preview finders."""
    import json
    import shutil
    from pathlib import Path

    from django.conf import settings
    from django.contrib.staticfiles import finders
    from django.core.management import call_command
    from django.http import HttpResponseNotFound
    from whitenoise.middleware import WhiteNoiseMiddleware

    root = Path(__file__).resolve().parents[1]
    archived = root / "artwork"
    old_sources = tmp_path / "old-sources"
    shutil.copytree(archived, old_sources)
    static_root = tmp_path / "collected"
    storage = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    with override_settings(
        STATIC_ROOT=static_root,
        STATICFILES_DIRS=[root / "static", old_sources],
        STORAGES=storage,
    ):
        call_command("collectstatic", interactive=False, verbosity=0)
        old_manifest = json.loads((static_root / "staticfiles.json").read_text())["paths"]
    stale_root = tmp_path / "stale-collected"
    shutil.copytree(static_root, stale_root)
    archive_names = [
        path.relative_to(archived).as_posix() for path in archived.rglob("*") if path.is_file()
    ]
    assert "images/cat-assistant-style/chaos.png" in archive_names
    removed_urls = [
        "/static/" + name
        for original in archive_names
        for name in (original, old_manifest[original])
    ]
    with override_settings(
        STATIC_ROOT=static_root,
        STATICFILES_DIRS=[root / "static"],
        STORAGES=storage,
        DEBUG=False,
        WHITENOISE_AUTOREFRESH=False,
        WHITENOISE_USE_FINDERS=False,
    ):
        call_command("collectstatic", clear=True, interactive=False, verbosity=0)
        manifest = json.loads((static_root / "staticfiles.json").read_text())["paths"]
        current = [
            path.relative_to(root / "static").as_posix()
            for path in (root / "static").rglob("*")
            if path.suffix in {".png", ".svg", ".jpeg", ".jpg", ".webp"}
        ]
        assert "icons/persona-mark.png" in current
        assert not set(archive_names) & manifest.keys()
        for name in current:
            assert name in manifest
            assert (static_root / manifest[name]).read_bytes() == (
                root / "static" / name
            ).read_bytes()
        middleware = WhiteNoiseMiddleware(lambda request: HttpResponseNotFound())
        factory = RequestFactory()
        for url in removed_urls:
            assert middleware(factory.get(url)).status_code == 404, url
        for name in current:
            for url in (name, manifest[name]):
                response = middleware(factory.get("/static/" + url))
                assert response.status_code == 200, url
                response.close()
        # Use the actual preview configuration, even when an old collected tree exists.
        from config.settings import preview

        assert preview.STATIC_ROOT is None
        assert (stale_root / archive_names[0]).is_file()
        with override_settings(
            STATIC_ROOT=preview.STATIC_ROOT,
            STATICFILES_DIRS=preview.STATICFILES_DIRS,
            WHITENOISE_USE_FINDERS=preview.WHITENOISE_USE_FINDERS,
            DEBUG=preview.DEBUG,
        ):
            middleware = WhiteNoiseMiddleware(lambda request: HttpResponseNotFound())
            for name in archive_names:
                assert finders.find(name) is None, name
            for url in removed_urls:
                assert middleware(factory.get(url)).status_code == 404, url
            for name in current:
                response = middleware(factory.get("/static/" + name))
                assert response.status_code == 200, name
                response.close()
