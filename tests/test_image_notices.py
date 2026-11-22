import base64
import hashlib
import importlib.util
import io
import zipfile
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "image_notices", Path(__file__).parents[1] / "scripts/collect_image_notices.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def zipped(name, data=b"license"):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(name, data)
    return stream.getvalue()


def test_h1_and_corruption():
    name = "example.org/demo@v1.0.0/LICENSE"
    text = b"license"
    expected = (
        "h1:"
        + base64.b64encode(
            hashlib.sha256(f"{hashlib.sha256(text).hexdigest()}  {name}\n".encode()).digest()
        ).decode()
    )
    assert m.inspect_archive(zipped(name), "example.org/demo", "v1.0.0", expected) == [
        ("LICENSE", text)
    ]
    with pytest.raises(ValueError, match="h1 mismatch"):
        m.inspect_archive(zipped(name, b"changed"), "example.org/demo", "v1.0.0", expected)


@pytest.mark.parametrize(
    "name", ["example.org/demo@v1.0.0/../LICENSE", "/LICENSE", "example.org/demo@v1.0.0/a\\LICENSE"]
)
def test_traversal_rejected(name):
    with pytest.raises(ValueError, match="unsafe"):
        m.inspect_archive(zipped(name), "example.org/demo", "v1.0.0", "h1:invalid")


def test_notice_limit(monkeypatch):
    monkeypatch.setattr(m, "MAX_UNPACKED", 2)
    with pytest.raises(ValueError, match="size limit"):
        m.inspect_archive(
            zipped("example.org/demo@v1.0.0/LICENSE"), "example.org/demo", "v1.0.0", "h1:invalid"
        )


def test_names_are_stable_and_escaped():
    assert m.escaped("github.com/BurntSushi/toml") == "github.com/!burnt!sushi/toml"
    assert m.directory("a", "v1") == m.directory("a", "v1")
    assert m.directory("a", "v1") != m.directory("a", "v2")


def test_symlink_and_duplicate_rejected():
    for duplicate in (False, True):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            name = "example.org/demo@v1.0.0/LICENSE"
            entry = zipfile.ZipInfo(name)
            if not duplicate:
                entry.create_system = 3
                entry.external_attr = 0o120777 << 16
            archive.writestr(entry, b"elsewhere")
            if duplicate:
                with pytest.warns(UserWarning):
                    archive.writestr(name, b"other")
        with pytest.raises(ValueError, match="unsafe"):
            m.inspect_archive(stream.getvalue(), "example.org/demo", "v1.0.0", "h1:invalid")


def test_gosu_exception_rejects_unapproved_identity(tmp_path, monkeypatch):
    def forbidden_fetch(*args, **kwargs):
        pytest.fail("unapproved identity must not cause network access")

    monkeypatch.setattr(m, "fetch", forbidden_fetch)
    with pytest.raises(ValueError, match="unapproved gosu fallback identity"):
        m.collect_gosu(("github.com/tianon/gosu", "v1.20.0"), [], tmp_path)


def test_fixture_exclusion_keeps_h1_and_real_notices():
    module, version = "example.org/demo", "v1.0.0"
    files = {
        "LICENSE": b"root license",
        "third-party/LICENSE.txt": b"nested license",
        "testdata/license.json": b"fixture",
    }
    stream = io.BytesIO()
    lines = []
    with zipfile.ZipFile(stream, "w") as archive:
        for path, text in sorted(files.items()):
            name = f"{module}@{version}/{path}"
            archive.writestr(name, text)
            lines.append(f"{hashlib.sha256(text).hexdigest()}  {name}\n")
    expected = "h1:" + base64.b64encode(hashlib.sha256("".join(lines).encode()).digest()).decode()
    excluded = []
    assert m.inspect_archive(stream.getvalue(), module, version, expected, excluded) == [
        ("LICENSE", files["LICENSE"]),
        ("third-party/LICENSE.txt", files["third-party/LICENSE.txt"]),
    ]
    assert excluded == [
        {
            "source_path": "testdata/license.json",
            "sha256": hashlib.sha256(b"fixture").hexdigest(),
            "bytes": 7,
            "reason": "testdata fixture; not a distributed runtime license text",
        }
    ]
    # Exclusion must not remove the fixture from the h1 input.
    incomplete = [line for line in lines if "/testdata/" not in line]
    bad_h1 = (
        "h1:" + base64.b64encode(hashlib.sha256("".join(incomplete).encode()).digest()).decode()
    )
    with pytest.raises(ValueError, match="h1 mismatch"):
        m.inspect_archive(stream.getvalue(), module, version, bad_h1)
    assert m.exclusion_reason("github.com/quic-go/quic-go", "assets/LICENSE.md")
    assert m.exclusion_reason("github.com/quic-go/quic-go", "LICENSE") is None
    assert m.exclusion_reason("github.com/slackhq/nebula", "LICENSE") is None
