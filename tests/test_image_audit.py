from pathlib import Path

from scripts import verify_image_audit


def test_audit_scan_has_no_implicit_ignore_config_or_network():
    args = verify_image_audit.scan_command("trivy", Path("cache"), Path("own.tar"), Path("out"))
    assert args[args.index("--input") + 1] == "own.tar"
    assert args[args.index("--config") + 1] == ""
    assert args[args.index("--ignorefile") + 1] == ""
    assert "--offline-scan" in args and "--skip-db-update" in args
    assert "--ignore-unfixed" not in args and "--severity" not in args
    assert args[args.index("--scanners") + 1] == "vuln,license"


def test_audit_failure_is_not_reported_as_no_findings_and_still_cleans(
    monkeypatch, tmp_path, capsys
):
    class Owned:
        def __init__(self, *args):
            self.private = tmp_path
            self.cleaned = False

        def cleanup(self):
            self.cleaned = True

    owned = Owned()
    monkeypatch.setattr(verify_image_audit, "Rehearsal", lambda *args: owned)
    monkeypatch.setattr(verify_image_audit, "digest", lambda path: "bad-checksum-private-sentinel")
    monkeypatch.setattr(
        "sys.argv",
        ["audit", "--scanner", "fake", "--cache", str(tmp_path), "--output", str(tmp_path)],
    )
    assert verify_image_audit.main() == 1
    assert owned.cleaned
    output = capsys.readouterr().out
    assert '"status": "failed"' in output
    assert "no-findings" not in output and "private-sentinel" not in output


def test_production_inventory_context_excludes_private_paths():
    contexts = verify_image_audit.production_contexts()
    names = set(contexts["app"][1])
    assert "uv.lock" in names and "deploy/Dockerfile" in names
    assert all(not name.startswith((".git", ".env", "tests/", "docs/evidence/")) for name in names)
    assert (
        contexts["caddy"][1]["deploy/Caddyfile"]
        == (verify_image_audit.ROOT / "deploy/Caddyfile").read_bytes()
    )
    assert b"tls internal" not in contexts["caddy"][1]["deploy/Caddyfile"]


def test_inventory_overrides_declared_image_volumes_with_tmpfs():
    import pytest

    for volumes in [{"/var/lib/postgresql/data": {}}, {"/data": {}, "/config": {}}]:
        args = verify_image_audit.inventory_tmpfs({"Config": {"Volumes": volumes}})
        assert len(args) == 2 * len(volumes)
        assert {args[i + 1].split(":", 1)[0] for i in range(0, len(args), 2)} == set(volumes)
        assert all(args[i] == "--tmpfs" for i in range(0, len(args), 2))
    with pytest.raises(RuntimeError, match="Unexpected image volume"):
        verify_image_audit.inventory_tmpfs({"Config": {"Volumes": {"/new-unreviewed": {}}}})
