#!/usr/bin/env python3
"""Collect exact notices from sumdb-checked Go module archives. No fetched code runs."""

import argparse
import base64
import concurrent.futures
import hashlib
import io
import json
import re
import stat
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

MAX_ARCHIVE = 150 * 1024 * 1024
MAX_UNPACKED = 700 * 1024 * 1024
MAX_NOTICE = 4 * 1024 * 1024
NOTICE = re.compile(r"^(LICENSE|LICENCE|COPYING|NOTICE|COPYRIGHT|PATENTS|AUTHORS)([._-].*)?$", re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def escaped(value):
    if not re.fullmatch(r"[A-Za-z0-9._/+~!@-]+", value) or ".." in value or value.startswith("/"):
        raise ValueError("unsafe module identity")
    return "".join("!" + c.lower() if c.isupper() else c for c in value)


def directory(module, version):
    return sha((module + "@" + version).encode())[:24]


def fetch(url, limit=MAX_ARCHIVE):
    # URLs are constructed internally exclusively from public inventory identities.
    with urllib.request.urlopen(url, timeout=90) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("download limit")
    return data


def exclusion_reason(module, relative):
    if "testdata" in (part.lower() for part in PurePosixPath(relative).parts):
        return "testdata fixture; not a distributed runtime license text"
    if (module, relative) == ("github.com/slackhq/nebula", "dist/windows/wintun/LICENSE.txt"):
        return "Windows-only driver not distributed in the Linux compiled runtime"
    if (module, relative) == ("github.com/quic-go/quic-go", "assets/LICENSE.md"):
        return "logo/trademark assets not distributed in the Linux compiled runtime images"
    return None


def inspect_archive(data, module, version, expected, excluded=None):
    prefix = module + "@" + version + "/"
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        if len(entries) > 100000 or sum(x.file_size for x in entries) > MAX_UNPACKED:
            raise ValueError("archive size limit")
        names = set()
        digest_lines = []
        notices = []
        for info in sorted(entries, key=lambda x: x.filename):
            name = info.filename
            if (
                name in names
                or "\\" in name
                or "\n" in name
                or not name.startswith(prefix)
                or any(p in ("..", ".") for p in name.split("/"))
                or PurePosixPath(name).is_absolute()
                or stat.S_ISLNK(info.external_attr >> 16)
            ):
                raise ValueError("unsafe archive member")
            names.add(name)
            if info.is_dir():
                continue
            # Go dirhash hashes every file, including notices, using full zip names.
            with archive.open(info) as stream:
                digest = hashlib.sha256()
                count = 0
                while chunk := stream.read(1024 * 1024):
                    count += len(chunk)
                    if count > MAX_UNPACKED:
                        raise ValueError("decompression limit")
                    digest.update(chunk)
            digest_lines.append(f"{digest.hexdigest()}  {name}\n")
            relative = name[len(prefix) :]
            if NOTICE.fullmatch(PurePosixPath(relative).name):
                if info.file_size > MAX_NOTICE:
                    raise ValueError("notice size limit")
                reason = exclusion_reason(module, relative)
                if reason:
                    if excluded is not None:
                        excluded.append(
                            {
                                "source_path": relative,
                                "sha256": digest.hexdigest(),
                                "bytes": info.file_size,
                                "reason": reason,
                            }
                        )
                else:
                    notices.append((relative, archive.read(info)))
        actual = (
            "h1:"
            + base64.b64encode(hashlib.sha256("".join(digest_lines).encode()).digest()).decode()
        )
        if actual != expected:
            raise ValueError("module h1 mismatch")
        return notices


def inventory(paths):
    modules = {}
    inputs = []
    for path in paths:
        raw = path.read_bytes()
        inputs.append({"path": str(path), "sha256": sha(raw)})
        for result in json.loads(raw).get("Results", []):
            if result.get("Type") != "gobinary":
                continue
            for package in result.get("Packages", []):
                name, version = package["Name"], package.get("Version")
                if not version:
                    if name == "caddy":
                        continue  # actual caddy/v2 record carries the exact version
                    raise ValueError("unversioned Go component")
                escaped(name)
                escaped(version)
                modules.setdefault((name, version), []).append(
                    {"report": str(path), "target": result["Target"]}
                )
    return modules, inputs


GOSU_COMMIT = "6456aaa0f3c854d199d0f037f068eb97515b7513"


def collect_gosu(identity, uses, output):
    """Explicit reviewed exception: upstream non-semver tag is absent from sumdb."""
    if identity != ("github.com/tianon/gosu", "v1.19.0"):
        raise ValueError("unapproved gosu fallback identity")
    module, version = identity
    record = {
        "module": module,
        "version": version,
        "uses": uses,
        "files": [],
        "status": "official-tag-to-commit-https",
        "verification": "official_tag_to_commit_https",
        "upstream_tag": "1.19",
        "upstream_commit": GOSU_COMMIT,
        "identity_source": "git ls-remote https://github.com/tianon/gosu.git refs/tags/1.19",
        "version_mapping": "Trivy v1.19.0 normalizes official upstream tag 1.19",
        "expected_h1": None,
        "h1_status": "missing: official sumdb lookup returned HTTP 404; no h1 verification",
        "checksum_source": "https://sum.golang.org/lookup/github.com/tianon/gosu@v1.19.0",
        "missing_optional_files": [],
    }
    try:
        for name in ("LICENSE", "NOTICE"):
            url = f"https://raw.githubusercontent.com/tianon/gosu/{GOSU_COMMIT}/{name}"
            try:
                data = fetch(url, MAX_NOTICE)
            except urllib.error.HTTPError as error:
                if error.code == 404 and name == "NOTICE":
                    record["missing_optional_files"].append({"url": url, "http_status": 404})
                    continue
                raise
            dest = Path(directory(module, version)) / name
            (output / dest).parent.mkdir(parents=True, exist_ok=True)
            (output / dest).write_bytes(data)
            record["files"].append(
                {
                    "url": url,
                    "source_path": name,
                    "path": str(dest),
                    "sha256": sha(data),
                    "bytes": len(data),
                }
            )
    except Exception as error:
        record.update(status="unresolved", reason=type(error).__name__ + ": " + str(error)[:160])
    return record


def collect_module(identity, uses, output):
    if identity == ("github.com/tianon/gosu", "v1.19.0"):
        return collect_gosu(identity, uses, output)
    module, version = identity
    record = {"module": module, "version": version, "uses": uses, "files": []}
    try:
        base = f"https://proxy.golang.org/{escaped(module)}/@v/{escaped(version)}"
        lookup = f"https://sum.golang.org/lookup/{escaped(module)}@{escaped(version)}"
        checksum = fetch(lookup, 1024 * 1024)
        expected = next(
            line.split()[2]
            for line in checksum.decode().splitlines()
            if line.startswith(module + " " + version + " h1:")
        )
        data = fetch(base + ".zip")
        excluded = []
        notices = inspect_archive(data, module, version, expected, excluded)
        if excluded:
            record["excluded_notices"] = excluded
        record.update(
            status="verified" if notices else "missing-notice",
            expected_h1=expected,
            checksum_source=lookup,
            checksum_response_sha256=sha(checksum),
            archive_url=base + ".zip",
            archive_sha256=sha(data),
        )
        for relative, text in notices:
            dest = Path(directory(module, version)) / relative
            (output / dest).parent.mkdir(parents=True, exist_ok=True)
            (output / dest).write_bytes(text)
            record["files"].append(
                {
                    "source_path": relative,
                    "path": str(dest),
                    "sha256": sha(text),
                    "bytes": len(text),
                }
            )
    except Exception as error:
        record.update(status="unresolved", reason=type(error).__name__ + ": " + str(error)[:160])
    return record


def collect_stdlib(version, uses, output):
    record = {
        "module": "stdlib",
        "version": version,
        "uses": uses,
        "status": "exact-upstream-tag",
        "files": [],
    }
    try:
        if not re.fullmatch(r"v\d+\.\d+\.\d+", version):
            raise ValueError("invalid stdlib version")
        tag = "go" + version[1:]
        record["identity_basis"] = "HTTPS official Go repository exact release tag; not module h1"
        for name in ("LICENSE", "PATENTS"):
            url = f"https://raw.githubusercontent.com/golang/go/{tag}/{name}"
            data = fetch(url, MAX_NOTICE)
            dest = Path(directory("stdlib", version)) / name
            (output / dest).parent.mkdir(parents=True, exist_ok=True)
            (output / dest).write_bytes(data)
            record["files"].append(
                {"url": url, "path": str(dest), "sha256": sha(data), "bytes": len(data)}
            )
    except Exception as error:
        record.update(status="unresolved", reason=type(error).__name__ + ": " + str(error)[:160])
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("docs/third-party/runtime-notices"))
    args = parser.parse_args()
    modules, inputs = inventory(args.reports)
    args.output.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [
            pool.submit(
                collect_stdlib if key[0] == "stdlib" else collect_module,
                *([key[1], uses, args.output] if key[0] == "stdlib" else [key, uses, args.output]),
            )
            for key, uses in sorted(modules.items())
        ]
        records = [f.result() for f in futures]
    gnu = {
        "component": "Psycopg LGPLv3 combined license",
        "url": "https://www.gnu.org/licenses/gpl-3.0.txt",
    }
    try:
        data = fetch(gnu["url"], MAX_NOTICE)
        (args.output / "GPL-3.0.txt").write_bytes(data)
        gnu.update(
            path="GPL-3.0.txt", sha256=sha(data), bytes=len(data), status="canonical-https-source"
        )
    except Exception as error:
        gnu.update(status="unresolved", reason=type(error).__name__)
    manifest = {
        "schema": 1,
        "scope": "Go image components and supplementary GPL text; legal review separate",
        "inputs": inputs,
        "components": records,
        "supplementary": [gnu],
        "notice_selection_policy": "v2: omit testdata fixtures and reviewed Linux-unused assets",
        "excluded_notices": [
            {"module": record["module"], "version": record["version"], **item}
            for record in records
            for item in record.get("excluded_notices", [])
        ],
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )
    unresolved = sum(x["status"] in ("unresolved", "missing-notice") for x in records) + (
        gnu["status"] == "unresolved"
    )
    print(json.dumps({"components": len(records), "unresolved": unresolved}))
    return bool(unresolved)


if __name__ == "__main__":
    raise SystemExit(main())
