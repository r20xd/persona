#!/usr/bin/env python3
"""Build and offline scan only this project's three production images."""

import argparse
import hashlib
import json
import os
import signal
import subprocess
from pathlib import Path

from scripts.verify_production import (
    CONTEXT_DIRS,
    CONTEXT_FILES,
    ROOT,
    Rehearsal,
    expected_notice_hashes,
    require_local_endpoint,
    runtime_notice_files,
)

SCANNER_VERSION = "0.76.2"
SCANNER_SHA256 = "6a972c69606c7b3ea4c6bdcc6fc9332ea9ad38381624310c1e85cc77345909f3"
APP_INVENTORY = r"""
import hashlib, importlib.metadata as m, json, pathlib, ssl
import psycopg.pq as pq
import argon2.low_level as argon

root = pathlib.Path("/")


def record(p):
    return {
        "path": str(p),
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        "size": p.stat().st_size,
    }


notices = []
for base in [
    "/usr/share/doc",
    "/usr/share/common-licenses",
    "/app/.venv/lib/python3.13/site-packages",
]:
    for p in pathlib.Path(base).rglob("*"):
        if p.is_file() and (
            "license" in str(p).lower()
            or "copying" in p.name.lower()
            or p.name.lower() in ["copyright", "notice", "authors"]
        ):
            notices.append(record(p))
libs = [record(p) for p in pathlib.Path("/app/.venv").rglob("*.so*") if p.is_file()]
print(
    json.dumps(
        {
            "python_ssl": ssl.OPENSSL_VERSION,
            "global_pip_paths": [
                str(p) for p in pathlib.Path("/usr/local/lib/python3.13/site-packages").glob("pip*")
            ],
            "ensurepip_wheels": [
                str(p) for p in pathlib.Path("/usr/local/lib/python3.13/ensurepip").rglob("*.whl")
            ],
            "psycopg_impl": pq.__impl__,
            "libpq_version": pq.version(),
            "argon2_version": argon.ARGON2_VERSION,
            "python_packages": [
                {
                    "name": d.metadata["Name"],
                    "version": d.version,
                    "source": "https://pypi.org/project/"
                    + d.metadata["Name"]
                    + "/"
                    + d.version
                    + "/",
                }
                for d in m.distributions()
            ],
            "native_files": libs,
            "notice_bundle": [
                record(p)
                for p in pathlib.Path("/usr/share/doc/deanery/third-party").rglob("*")
                if p.is_file()
            ],
            "system_libpq_files": [
                record(p) for p in pathlib.Path("/usr/lib").glob("*/libpq.so.*") if p.is_file()
            ],
            "package_index_provenance": {
                p.name: p.read_text()
                for p in pathlib.Path("/usr/share/doc/deanery").glob("*apt*.txt")
            },
            "notices": notices,
        }
    )
)
"""


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def production_contexts():
    app = {name: (ROOT / name).read_bytes() for name in CONTEXT_FILES}
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
                app[str(path.relative_to(ROOT))] = path.read_bytes()
    for name in ["deploy/Dockerfile", "docs/third-party/libargon2-LICENSE.txt"]:
        app[name] = (ROOT / name).read_bytes()
    app.update(runtime_notice_files())
    return {
        "app": ("deploy/Dockerfile", app),
        "db": (
            "Dockerfile",
            {
                "Dockerfile": (ROOT / "deploy/Dockerfile.postgres").read_bytes(),
                "deploy/postgres-init.sh": (ROOT / "deploy/postgres-init.sh").read_bytes(),
                **runtime_notice_files(),
            },
        ),
        "caddy": (
            "Dockerfile",
            {
                "Dockerfile": (ROOT / "deploy/Dockerfile.caddy").read_bytes(),
                "deploy/Caddyfile": (ROOT / "deploy/Caddyfile").read_bytes(),
                **runtime_notice_files(),
            },
        ),
    }


def inventory_tmpfs(info):
    volumes = set(info["Config"].get("Volumes") or {})
    if not volumes <= {"/var/lib/postgresql/data", "/data", "/config"}:
        raise RuntimeError("Unexpected image volume")
    return [
        arg for path in sorted(volumes) for arg in ["--tmpfs", path + ":rw,noexec,nosuid,size=16m"]
    ]


def scan_command(scanner, cache, archive, output):
    return [
        scanner,
        "image",
        "--config",
        "",
        "--ignorefile",
        "",
        "--cache-dir",
        str(cache),
        "--input",
        str(archive),
        "--offline-scan",
        "--skip-db-update",
        "--skip-java-db-update",
        "--skip-check-update",
        "--skip-version-check",
        "--scanners",
        "vuln,license",
        "--list-all-pkgs",
        "--license-full",
        "--format",
        "json",
        "--output",
        str(output),
        "--no-progress",
    ]


def main():
    if not __debug__:
        print('{"status":"failed","phase":"optimized-python"}')
        return 1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker", default="docker")
    parser.add_argument("--scanner", required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/evidence/D02-02/audit")
    args = parser.parse_args()
    audit = Rehearsal(args.docker, False)
    result = {"status": "failed", "images": {}, "runner_sha256": digest(Path(__file__))}
    phase = "preflight"

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    try:
        if digest(Path(args.scanner)) != SCANNER_SHA256:
            raise RuntimeError("Unexpected scanner checksum")
        version = subprocess.check_output([args.scanner, "--version"], timeout=15).decode()
        if not version.startswith("Version: " + SCANNER_VERSION + "\n"):
            raise RuntimeError("Unexpected scanner version")
        db = args.cache / "db/trivy.db"
        metadata = args.cache / "db/metadata.json"
        result["scanner"] = {
            "version": SCANNER_VERSION,
            "binary_sha256": digest(Path(args.scanner)),
            "source": "https://github.com/aquasecurity/trivy/releases/tag/v0.76.2",
            "database": json.loads(metadata.read_text()),
            "database_sha256": digest(db),
            "database_source": "ghcr.io/aquasecurity/trivy-db:2",
        }
        require_local_endpoint(
            json.loads(audit.command("context", "inspect"))[0]["Endpoints"]["docker"]["Host"]
        )
        args.output.mkdir(parents=True, exist_ok=True)
        for name, (dockerfile, files) in production_contexts().items():
            phase = "build-" + name
            tag = audit.build(name, dockerfile, files)
            info = audit.inspect_resource("image", tag)
            audit.require_owner(info, "image")
            phase = "inventory-" + name
            audit.created = True
            runtime = (
                ["python", "-c", APP_INVENTORY]
                if name == "app"
                else [
                    "sh",
                    "-c",
                    "find /usr/share/doc /usr/share/licenses /usr/share/common-licenses "
                    "-type f 2>/dev/null | sort | "
                    'while IFS= read -r f; do sha256sum "$f" || exit 1; done || exit 1; '
                    "echo DEANERY_PACKAGE_PROVENANCE; "
                    "cat /usr/share/doc/deanery/*apt*.txt "
                    "/usr/share/doc/deanery/*apk*.txt 2>/dev/null || true",
                ]
            )
            container_name = audit.project + "-inventory-" + name
            if audit.inspect_resource("container", container_name) is not None:
                raise RuntimeError("Refusing pre-existing container name")
            probe = audit.command(
                "run",
                "--rm",
                "--name",
                container_name,
                "--label",
                "deanery.d02.owner=" + audit.owner,
                "--label",
                "com.docker.compose.project=" + audit.project,
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                *inventory_tmpfs(info),
                "--entrypoint",
                runtime[0],
                tag,
                *runtime[1:],
                timeout=90,
            )
            (args.output / (name + "-runtime.json")).write_text(
                json.dumps(
                    json.loads(probe)
                    if name == "app"
                    else {
                        "notice_sha256_lines": probe.decode()
                        .split("DEANERY_PACKAGE_PROVENANCE\n")[0]
                        .splitlines(),
                        "package_index_provenance": probe.decode()
                        .split("DEANERY_PACKAGE_PROVENANCE\n")[1]
                        .splitlines(),
                    },
                    indent=2,
                )
                + "\n"
            )
            runtime_report = json.loads((args.output / (name + "-runtime.json")).read_text())
            if name == "app":
                deployed_notices = {r["path"]: r["sha256"] for r in runtime_report["notice_bundle"]}
            else:
                deployed_notices = {
                    line.split(None, 1)[1]: line.split(None, 1)[0]
                    for line in runtime_report["notice_sha256_lines"]
                    if line.split(None, 1)[1].startswith("/usr/share/doc/deanery/third-party/")
                }
            assert deployed_notices == expected_notice_hashes()
            if name == "caddy":
                phase = "validate-caddy"
                run_args = [
                    "run",
                    "--rm",
                    "--name",
                    container_name,
                    "--label",
                    "deanery.d02.owner=" + audit.owner,
                    "--label",
                    "com.docker.compose.project=" + audit.project,
                    "--network",
                    "none",
                    "--read-only",
                    "--cap-drop",
                    "ALL",
                    "--tmpfs",
                    "/config:rw,noexec,nosuid,size=16m",
                    "--tmpfs",
                    "/data:rw,noexec,nosuid,size=16m",
                    "--env",
                    "SITE_DOMAIN=example.invalid",
                    "--entrypoint",
                    "caddy",
                    tag,
                ]
                adapted = json.loads(
                    audit.command(
                        *run_args,
                        "adapt",
                        "--config",
                        "/etc/caddy/Caddyfile",
                        "--adapter",
                        "caddyfile",
                    )
                )
                logging = adapted["logging"]["logs"]
                assert {"*", "."} <= set(logging["default"]["exclude"])
                assert logging["tls_events"]["include"] == ["tls.cache.maintenance", "tls.obtain"]
                assert logging["tls_events"]["level"] == "INFO"
                assert logging["handled_faults"]["include"] == ["http.log.error"]
                assert logging["handled_faults"]["level"] == "DEBUG"
                for config in logging.values():
                    assert config["encoder"]["wrap"]["message_key"] == ""
                audit.command(
                    *run_args,
                    "validate",
                    "--config",
                    "/etc/caddy/Caddyfile",
                    "--adapter",
                    "caddyfile",
                )
                (args.output / "caddy-validation.json").write_text(
                    json.dumps(
                        {
                            "adapt": "passed",
                            "validate": "passed",
                            "logger_scopes": {
                                n: {
                                    "include": c.get("include", []),
                                    "exclude": c.get("exclude", []),
                                    "level": c.get("level", "INFO"),
                                }
                                for n, c in logging.items()
                            },
                            "free_text_message_omitted": True,
                        },
                        indent=2,
                    )
                    + "\n"
                )
            archive = audit.private / (name + ".tar")
            phase = "save-" + name
            with archive.open("wb") as stream:
                archive.chmod(0o600)
                saved = subprocess.run(
                    [args.docker, "image", "save", tag],
                    stdout=stream,
                    stderr=subprocess.PIPE,
                    env=audit.environment,
                    timeout=180,
                )
            if saved.returncode:
                raise RuntimeError("Image export failed")
            phase = "scan-" + name
            report = args.output / (name + ".json")
            scanned = subprocess.run(
                scan_command(args.scanner, args.cache, archive, report),
                capture_output=True,
                timeout=600,
                env={
                    "PATH": os.environ["PATH"],
                    "HOME": str(audit.private),
                    "TMPDIR": str(audit.private),
                },
            )
            if scanned.returncode:
                raise RuntimeError("Scanner failed")
            converted = subprocess.run(
                [
                    args.scanner,
                    "convert",
                    "--config",
                    "",
                    "--ignorefile",
                    "",
                    "--format",
                    "cyclonedx",
                    "--output",
                    str(args.output / (name + ".cdx.json")),
                    str(report),
                ],
                capture_output=True,
                timeout=60,
                env={"PATH": os.environ["PATH"], "HOME": str(audit.private)},
            )
            if converted.returncode:
                raise RuntimeError("SBOM conversion failed")
            raw = json.loads(report.read_text())
            findings = [
                v for target in raw.get("Results", []) for v in target.get("Vulnerabilities", [])
            ]
            result["images"][name] = {
                "image_id": info["Id"],
                "verified_notice_bundle_files": len(deployed_notices),
                "repo_digests": info.get("RepoDigests"),
                "runtime_sha256": digest(args.output / (name + "-runtime.json")),
                "sbom_sha256": digest(args.output / (name + ".cdx.json")),
                "archive_sha256": digest(archive),
                "report_sha256": digest(report),
                "findings": len(findings),
                "severity": {
                    s: sum(v["Severity"] == s for v in findings)
                    for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
                },
                "build_context_sha256": {
                    p: hashlib.sha256(b).hexdigest() for p, b in files.items()
                },
            }
            archive.unlink()
            print(
                json.dumps({"image": name, "scanner_completed": True, "findings": len(findings)}),
                flush=True,
            )
        result["status"] = (
            "completed-with-findings"
            if any(i["findings"] for i in result["images"].values())
            else "completed-no-findings"
        )
    except (Exception, KeyboardInterrupt) as error:
        result["failure"] = {"phase": phase, "type": type(error).__name__}
    try:
        audit.cleanup()
        result["cleanup"] = "complete"
    except Exception:
        result["cleanup"] = "failed"
        result["status"] = "failed"
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "cleanup": result["cleanup"],
                "failure": result.get("failure"),
            }
        )
    )
    return int(result["status"] == "failed")


if __name__ == "__main__":
    raise SystemExit(main())
