"""Q05: upgrade an existing populated previous schema, without deleting request tables."""

import secrets
import uuid
from datetime import date

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.django_db(transaction=True)
def test_previous_schema_upgrade_preserves_existing_student_request(monkeypatch):
    assert connection.vendor == "postgresql"
    password = secrets.token_urlsafe(32)
    for role in ["STUDENT_ONE", "STUDENT_TWO", "OPERATOR"]:
        monkeypatch.setenv(f"DEMO_{role}_PASSWORD", password)
    call_command("seed_demo", anchor_date=date(2026, 11, 2), verbosity=0)
    executor = MigrationExecutor(connection)
    leaves = executor.loader.graph.leaf_nodes()
    previous = [node for node in leaves if node[0] != "notifications"] + [
        ("notifications", "0001_initial")
    ]
    request_id = uuid.uuid4()
    tables = [
        "accounts.User",
        "accounts.StudentProfile",
        "grades.GradeResult",
        "schedule.Lesson",
        "requests.ServiceRequest",
        "requests.RequestEvent",
    ]

    def snapshot(apps):
        return {name: list(apps.get_model(name).objects.order_by("pk").values()) for name in tables}

    try:
        executor.migrate(previous)
        historical = executor.loader.project_state(previous).apps
        user = historical.get_model("accounts", "User").objects.get(username="student.one")
        profile = historical.get_model("accounts", "StudentProfile").objects.get(user_id=user.pk)
        request = historical.get_model("requests", "ServiceRequest").objects.create(
            id=request_id,
            student_id=profile.pk,
            purpose="other",
            submission_key=uuid.uuid4(),
            status="in_progress",
            version=2,
            comment="Вымышленная заявка до обновления",
        )
        event = historical.get_model("requests", "RequestEvent")
        event.objects.create(
            request_id=request.pk,
            actor_id=user.pk,
            from_status="",
            to_status="submitted",
            version=1,
        )
        operator = historical.get_model("accounts", "User").objects.get(username="operator.demo")
        event.objects.create(
            request_id=request.pk,
            actor_id=operator.pk,
            from_status="submitted",
            to_status="in_progress",
            version=2,
        )
        before = snapshot(historical)
        stored_hash = user.password
        assert stored_hash.startswith("argon2$") and stored_hash != password
        executor = MigrationExecutor(connection)
        executor.migrate(leaves)
        assert not MigrationExecutor(connection).migration_plan(leaves)
        current = executor.loader.project_state(leaves).apps
        assert snapshot(current) == before
        assert current.get_model("accounts", "User").objects.get(pk=user.pk).password == stored_hash
        assert (
            current.get_model("requests", "ServiceRequest").objects.get(pk=request_id).version == 2
        )
    finally:
        MigrationExecutor(connection).migrate(leaves)


def test_runner_refuses_foreign_resource_cleanup(monkeypatch):
    import json
    from types import SimpleNamespace

    from scripts.verify_data_lifecycle import Rehearsal

    runner = Rehearsal("unused-docker")
    runner.container_created = True
    calls = []

    def docker(*args):
        calls.append(args)
        return SimpleNamespace(
            stdout=json.dumps(
                [{"Config": {"Labels": {"deanery.q05.owner": "another-run"}}}]
            ).encode()
        )

    monkeypatch.setattr(runner, "docker_run", docker)
    monkeypatch.setattr(runner, "resource_absent", lambda *args: False)
    with pytest.raises(RuntimeError, match="cleanup incomplete"):
        runner.cleanup()
    assert calls == [("container", "inspect", runner.container)]
    assert runner.container_created


def test_runner_does_not_inherit_database_or_demo_secrets(monkeypatch):
    from scripts.verify_data_lifecycle import Rehearsal

    for name in [
        "DB_NAME",
        "DB_PASSWORD",
        "DJANGO_SECRET_KEY",
        "DEMO_OPERATOR_PASSWORD",
        "DATABASE_URL",
        "PGPASSWORD",
    ]:
        monkeypatch.setenv(name, "foreign-secret-sentinel")
    runner = Rehearsal("unused-docker")
    assert "foreign-secret-sentinel" not in runner.env.values()
    assert "DATABASE_URL" not in runner.env
    assert "PGPASSWORD" not in runner.env


def test_runner_rejects_optimized_python_before_docker():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-O", "scripts/verify_data_lifecycle.py", "--docker", "must-not-run"],
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 2
    assert b"OptimizedPythonUnsupported" in result.stdout
    assert not result.stderr


def test_runner_remote_docker_refused_before_creation(monkeypatch):
    import json
    from types import SimpleNamespace

    from scripts.verify_data_lifecycle import Rehearsal

    runner = Rehearsal("unused-docker")
    calls = []

    def docker(*args):
        calls.append(args)
        return SimpleNamespace(
            stdout=json.dumps(
                [{"Endpoints": {"docker": {"Host": "ssh://remote.invalid"}}}]
            ).encode()
        )

    monkeypatch.setattr(runner, "docker_run", docker)
    with pytest.raises(RuntimeError, match="endpoint must be local"):
        runner.execute()
    assert calls == [("context", "inspect")]
    assert not runner.container_created and not runner.volume_created
    runner.cleanup()


def test_runner_timeout_after_create_removes_exact_owned_resource(monkeypatch):
    import subprocess

    from scripts.verify_data_lifecycle import Rehearsal

    runner = Rehearsal("unused-docker")
    exists = False
    calls = []

    def docker(*args):
        nonlocal exists
        calls.append(args)
        if args[0] == "create":
            exists = True
            raise subprocess.TimeoutExpired("unused-docker", 120)
        if args == ("rm", "--force", runner.container):
            exists = False

    monkeypatch.setattr(runner, "docker_run", docker)
    monkeypatch.setattr(runner, "resource_absent", lambda kind, name: not exists)
    monkeypatch.setattr(runner, "owned", lambda kind, name: calls.append(("owner", kind, name)))
    with pytest.raises(subprocess.TimeoutExpired):
        runner.create_owned("container", "create", "--name", runner.container)
    assert runner.container_created and exists
    runner.cleanup()
    assert not exists and not runner.container_created
    assert calls == [
        ("create", "--name", runner.container),
        ("owner", "container", runner.container),
        ("rm", "--force", runner.container),
    ]


def test_runner_start_failure_cleans_created_container(monkeypatch):
    import subprocess

    from scripts.verify_data_lifecycle import Rehearsal

    runner = Rehearsal("unused-docker")
    calls = []
    exists = False

    def docker(*args):
        nonlocal exists
        calls.append(args)
        if args[0] == "create":
            exists = True
        elif args[0] == "start":
            raise subprocess.CalledProcessError(125, "unused-docker")
        elif args == ("rm", "--force", runner.container):
            exists = False

    monkeypatch.setattr(runner, "docker_run", docker)
    monkeypatch.setattr(runner, "resource_absent", lambda kind, name: not exists)
    monkeypatch.setattr(runner, "owned", lambda *args: None)
    runner.create_owned("container", "create", "--name", runner.container)
    with pytest.raises(subprocess.CalledProcessError):
        runner.container_action("start")
    runner.cleanup()
    assert not exists and not runner.container_created
    assert calls[-1] == ("rm", "--force", runner.container)
