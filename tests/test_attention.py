from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.accounts.models import User
from apps.dashboard import digest
from apps.dashboard.models import DigestReceipt, DigestState
from apps.grades.models import GradeResult
from apps.requests.models import ServiceRequest
from apps.requests.services import transition_request
from tests.test_dashboard_demo import PASSWORD, seed


@pytest.fixture
def demo(monkeypatch):
    seed(monkeypatch)
    return User.objects.get(username="student.one"), User.objects.get(username="student.two")


pytestmark = pytest.mark.django_db


def published(user):
    return GradeResult.objects.filter(enrollment__student__user=user).first()


def republish(result):
    result.published_at = timezone.now()
    result.save()


def test_home_and_login_do_not_start_or_read_digest(client, demo, monkeypatch):
    one, _ = demo

    def unexpected(*args, **kwargs):
        raise AssertionError("Retired digest must not be read by the home page")

    monkeypatch.setattr(digest, "context", unexpected)
    client.force_login(one)
    response = client.get("/")
    assert response.status_code == 200 and "digest" not in response.context
    assert not DigestState.objects.exists()
    client.logout()
    assert (
        client.post("/login/", {"username": one.username, "password": PASSWORD}).status_code == 302
    )
    assert not DigestState.objects.exists()
    assert client.post("/dashboard/changes/seen/").status_code == 404


def test_exact_versions_tabs_and_new_after_get(client, demo):
    one, _ = demo
    digest.start(one)
    grade = published(one)
    republish(grade)
    initial = digest.context(one)
    assert initial["total"] == 1
    stale = initial["token"]
    republish(grade)
    digest.acknowledge(one, stale)
    assert digest.context(one)["total"] == 1
    current = digest.context(one)["token"]
    digest.acknowledge(one, current)
    digest.acknowledge(one, current)
    assert DigestReceipt.objects.count() == 1
    assert digest.context(one)["total"] == 0
    republish(grade)
    digest.acknowledge(one, stale)
    assert digest.context(one)["total"] == 1


def test_user_scope_future_and_fresh_access(demo):
    one, two = demo
    digest.start(one)
    grade = published(two)
    republish(grade)
    assert digest.context(one)["total"] == 0
    grade = published(one)
    grade.published_at = timezone.now() + timedelta(days=1)
    grade.save()
    assert digest.context(one)["total"] == 0
    republish(grade)
    token = digest.context(one)["token"]
    digest.start(two)
    with pytest.raises(PermissionDenied):
        digest.acknowledge(two, token)
    with pytest.raises(ValueError):
        digest.acknowledge(one, token + "bad")
    User.objects.filter(pk=one.pk).update(is_active=False)
    with pytest.raises(PermissionDenied):
        digest.acknowledge(one, token)


def test_request_event_and_radar_independence(client, demo):
    one, _ = demo
    digest.start(one)
    operator = User.objects.get(username="operator.demo")
    application = ServiceRequest.objects.get(student__user=one)
    transition_request(
        actor=operator,
        request_id=application.pk,
        expected_version=application.version,
        desired_status="in_progress",
    )
    application.refresh_from_db()
    transition_request(
        actor=operator,
        request_id=application.pk,
        expected_version=application.version,
        desired_status="ready",
    )
    client.force_login(one)
    response = client.get("/")
    assert digest.context(one)["total"] == 2
    before = response.context["attention"]
    assert any(item["label"] == "Ответ деканата" for item in before["items"])
    digest.acknowledge(one, digest.context(one)["token"])
    response = client.get("/")
    assert digest.context(one)["total"] == 0
    assert response.context["attention"] == before


def test_retired_digest_endpoint(client, demo):
    one, _ = demo
    client.force_login(one)
    assert client.get("/dashboard/changes/seen/").status_code == 404
    assert client.post("/dashboard/changes/seen/", {"token": "invalid"}).status_code == 404


def test_limit_and_events_after_open(demo):
    one, _ = demo
    digest.start(one)
    operator = User.objects.get(username="operator.demo")
    import uuid

    from apps.requests.services import create_request

    for _ in range(5):
        request = create_request(
            actor=one, purpose="other", comment="", submission_key=uuid.uuid4()
        )
        transition_request(
            actor=operator, request_id=request.pk, expected_version=1, desired_status="in_progress"
        )
    first = digest.context(one)
    request_group = next(g for g in first["groups"] if g["kind"] == "request")
    assert request_group["count"] == 5 and len(request_group["items"]) == 3
    late = create_request(actor=one, purpose="other", comment="", submission_key=uuid.uuid4())
    transition_request(
        actor=operator, request_id=late.pk, expected_version=1, desired_status="in_progress"
    )
    digest.acknowledge(one, first["token"])
    assert digest.context(one)["total"] == 3
    digest.acknowledge(one, first["token"])
    assert digest.context(one)["total"] == 3


def test_group_revocation_and_schedule_history(demo):
    one, two = demo
    digest.start(one)
    from apps.schedule.models import Lesson
    from apps.schedule.services import change_lesson

    lesson = Lesson.objects.filter(offering__enrollment__student__user=one).first()
    change_lesson(
        lesson_id=lesson.pk,
        expected_version=lesson.version,
        status="cancelled",
        reason="Вымышленная отмена",
    )
    result = digest.context(one)
    assert result["total"] == 1
    profile = one.studentprofile
    profile.group = two.studentprofile.group
    profile.save()
    assert digest.context(one)["total"] == 0
    digest.acknowledge(one, result["token"])
    assert not DigestReceipt.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_late_commit_and_concurrent_tabs(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from django.db import close_old_connections, transaction

    seed(monkeypatch)
    one = User.objects.get(username="student.one")
    digest.start(one)
    grade = published(one)
    opened, release = Event(), Event()

    def publish():
        close_old_connections()
        try:
            with transaction.atomic():
                item = GradeResult.objects.get(pk=grade.pk)
                republish(item)
                opened.set()
                assert release.wait(10)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(publish)
        assert opened.wait(10)
        before = digest.context(one)
        assert before["total"] == 0
        digest.acknowledge(one, before["token"])
        release.set()
        future.result(timeout=10)
    after = digest.context(one)
    assert after["total"] == 1

    def ack():
        close_old_connections()
        try:
            digest.acknowledge(User.objects.get(pk=one.pk), after["token"])
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: ack(), range(2)))
    assert DigestReceipt.objects.count() == 1
    assert digest.context(one)["total"] == 0


@pytest.mark.django_db(transaction=True)
def test_additive_migration_preserves_sources(monkeypatch):
    from io import StringIO

    from django.core.management import call_command
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    seed(monkeypatch)
    executor = MigrationExecutor(connection)
    executor.migrate([("dashboard", None)])
    from apps.requests.models import RequestEvent
    from apps.schedule.models import LessonChange

    models = (User, ServiceRequest, RequestEvent, GradeResult, LessonChange)
    previous = [list(model.objects.order_by("pk").values()) for model in models]
    call_command("migrate", "dashboard", stdout=StringIO(), verbosity=0)
    assert previous == [list(model.objects.order_by("pk").values()) for model in models]
    assert not DigestState.objects.exists() and not DigestReceipt.objects.exists()


def test_started_digest_query_count_is_bounded(client, demo):
    import uuid

    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from apps.requests.services import create_request

    one, _ = demo
    digest.start(one)
    operator = User.objects.get(username="operator.demo")
    client.force_login(one)
    with CaptureQueriesContext(connection) as baseline:
        assert client.get("/").status_code == 200
    for _ in range(8):
        request = create_request(
            actor=one, purpose="other", comment="", submission_key=uuid.uuid4()
        )
        transition_request(
            actor=operator, request_id=request.pk, expected_version=1, desired_status="in_progress"
        )
    with CaptureQueriesContext(connection) as expanded:
        assert client.get("/").status_code == 200
    assert len(expanded) <= len(baseline) + 1
    assert len(expanded) <= 55
    print(f"K01 started GET queries baseline={len(baseline)} expanded={len(expanded)}")


def test_expired_and_oversized_payloads(demo):
    from unittest.mock import patch

    from django.core import signing

    one, _ = demo
    state = digest.start(one)
    with patch("django.core.signing.time.time", return_value=1):
        expired = digest.token(one, state, [])
    with pytest.raises(ValueError):
        digest.acknowledge(one, expired)
    oversized = signing.dumps(
        {"user": str(one.pk), "state": state.pk, "events": [None] * 10}, salt=digest.SALT
    )
    with pytest.raises(ValueError):
        digest.acknowledge(one, oversized)


def test_radar_negative_final(client, demo):
    one, _ = demo
    final = GradeResult.objects.filter(
        enrollment__student__user=one, assessment__kind="exam"
    ).first()
    final.outcome = "unsatisfactory"
    republish(final)
    client.force_login(one)
    response = client.get("/")
    cards = response.context["attention"]["items"]
    assert cards[0]["label"] == "Важно"
    assert all("deadline" not in item["url"] for item in cards)


def test_radar_bounded_current_sources(demo):
    from apps.dashboard import attention
    from apps.dashboard.selectors import dashboard_context
    from apps.notifications.models import Deadline
    from apps.schedule.models import Lesson
    from apps.schedule.services import change_lesson

    one, two = demo
    own_offering = (
        GradeResult.objects.filter(enrollment__student__user=one).first().enrollment.offering
    )
    due = Deadline.objects.create(
        offering=own_offering,
        title="Архивный учебный срок",
        due_at=timezone.now() + timedelta(hours=1),
    )
    lesson = (
        Lesson.objects.filter(
            offering__enrollment__student__user=one, starts_at__gte=timezone.now()
        )
        .order_by("starts_at")
        .first()
    )
    change_lesson(
        lesson_id=lesson.pk,
        expected_version=lesson.version,
        status="cancelled",
        reason="Устаревшая причина",
    )
    lesson.refresh_from_db()
    change_lesson(
        lesson_id=lesson.pk,
        expected_version=lesson.version,
        status="scheduled",
        reason="Актуальное изменение",
    )
    study = dashboard_context(one)["study"]
    first = attention.context(one, study)
    assert all(item["title"] != due.title for item in first["items"])
    assert first == attention.context(one, study)
    current = attention.context(one, study)
    changes = [item for item in current["items"] if item["label"] == "Изменение занятия"]
    assert any("Отменено → По расписанию" in item["reason"] for item in changes)
    assert not any("Устаревшая причина" in item["reason"] for item in changes)
    assert all(item["title"] != due.title for item in current["items"])
    assert two
