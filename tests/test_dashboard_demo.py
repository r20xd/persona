"""Composition, strict seed identity, preservation and real PostgreSQL concurrency."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from threading import Barrier
from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import close_old_connections, connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.academics.models import CourseOffering, Enrollment, Faculty, Term
from apps.accounts.models import StudentProfile, User
from apps.dashboard.selectors import dashboard_context
from apps.grades.models import GradeResult
from apps.notifications.models import Announcement, AnnouncementRead, Deadline, Notification
from apps.requests.models import RequestEvent, ServiceRequest
from apps.requests.services import create_request, transition_request
from apps.schedule.models import Lesson, LessonChange
from apps.schedule.selectors import MOSCOW
from apps.schedule.services import change_lesson

pytestmark = pytest.mark.django_db
PASSWORD = "Fictional-bootstrap-9874!"


def seed(monkeypatch, **options):
    for name in [
        "DEMO_STUDENT_ONE_PASSWORD",
        "DEMO_STUDENT_TWO_PASSWORD",
        "DEMO_OPERATOR_PASSWORD",
    ]:
        monkeypatch.setenv(name, PASSWORD)
    call_command("seed_demo", stdout=StringIO(), **options)


@pytest.fixture
def demo(monkeypatch):
    seed(monkeypatch)
    return User.objects.get(username="student.one"), User.objects.get(username="student.two")


def test_seed_preserves_actions_and_identifiers(demo, monkeypatch):
    one, two = demo
    first = ServiceRequest.objects.get(student__user=one)
    transition_request(
        actor=one, request_id=first.pk, expected_version=1, desired_status="cancelled"
    )
    one.set_password("Changed-fictional-9341!")
    one.save()
    grade = GradeResult.objects.filter(enrollment__student__user=one, points__isnull=False).first()
    grade.points = 1
    grade.save()
    note = Notification.objects.filter(recipient=one).first()
    note.read_at = timezone.now()
    note.save()
    announcement = Announcement.objects.get(code="demo-all")
    AnnouncementRead.objects.create(announcement=announcement, user=one)
    deadline = Deadline.objects.create(
        offering=grade.enrollment.offering,
        title="Архивный срок",
        due_at=timezone.now(),
        code="legacy-preservation",
    )
    deadline.due_at += timedelta(days=10)
    deadline.revision += 1
    deadline.save()
    preserved_due = deadline.due_at
    lesson = Lesson.objects.filter(offering__enrollment__student__user=one).first()
    change_lesson(
        lesson_id=lesson.pk,
        expected_version=lesson.version,
        status="cancelled",
        reason="Проверка сохранения",
    )
    ids = set(Lesson.objects.values_list("pk", flat=True))
    events = (
        RequestEvent.objects.count(),
        LessonChange.objects.count(),
        Notification.objects.count(),
    )
    anchor = Term.objects.get(code="fiction-study-demo").starts_on
    seed(monkeypatch)
    first.refresh_from_db()
    grade.refresh_from_db()
    note.refresh_from_db()
    lesson.refresh_from_db()
    one.refresh_from_db()
    deadline.refresh_from_db()
    assert deadline.due_at == preserved_due and deadline.revision == 2
    assert AnnouncementRead.objects.filter(announcement=announcement, user=one).exists()
    assert first.status == "cancelled" and grade.points == 1 and note.read_at
    assert lesson.status == "cancelled" and one.check_password("Changed-fictional-9341!")
    assert set(Lesson.objects.values_list("pk", flat=True)) == ids
    assert events == (
        RequestEvent.objects.count(),
        LessonChange.objects.count(),
        Notification.objects.count(),
    )
    assert Term.objects.get(code="fiction-study-demo").starts_on == anchor
    assert ServiceRequest.objects.get(student__user=two).status == "ready"


def test_seed_anchor_coverage_and_future_extension(monkeypatch):
    today = timezone.localdate(timezone=MOSCOW)
    seed(monkeypatch, anchor_date=today)
    term = Term.objects.get(code="fiction-study-demo")
    monday = today - timedelta(days=today.weekday())
    assert term.starts_on == monday - timedelta(days=7)
    assert Lesson.objects.filter(starts_at__date__lt=monday).exists()
    assert Lesson.objects.filter(starts_at__date__gte=today + timedelta(days=42)).exists()
    original = {
        item.pk: (item.starts_at, item.ends_at, item.version) for item in Lesson.objects.all()
    }
    call_command("extend_demo_schedule", anchor_date=today + timedelta(days=80), stdout=StringIO())
    for item in Lesson.objects.filter(pk__in=original):
        assert (item.starts_at, item.ends_at, item.version) == original[item.pk]
    added = Lesson.objects.exclude(pk__in=original)
    assert added.exists() and not added.filter(starts_at__date__lt=today).exists()
    count = Lesson.objects.count()
    call_command("extend_demo_schedule", anchor_date=today + timedelta(days=80), stdout=StringIO())
    assert Lesson.objects.count() == count
    assert Term.objects.get(pk=term.pk).starts_on == term.starts_on


def test_seed_rejects_incompatible_identity(demo, monkeypatch):
    Faculty.objects.filter(code="social").update(name="Чужой справочник")
    with pytest.raises(CommandError, match="Incompatible"):
        seed(monkeypatch)


def test_dashboard_scopes_published_results_and_deadlines(client, demo):
    one, two = demo
    for user, other in [(one, two), (two, one)]:
        client.force_login(user)
        response = client.get("/")
        assert response.status_code == 200 and "no-store" in response["Cache-Control"]
        body = response.content.decode()
        assert user.studentprofile.full_name in body and other.studentprofile.full_name not in body
        context = response.context
        assert context["study"]["counts"]["success"] + context["study"]["counts"]["failure"] == 1
        assert "upcoming_deadlines" not in context
        assert "active_requests" not in context
        for heading in [
            "Ваши заявки",
            "Важное рядом",
            "Как идёт учёба",
            "Ближайшие сроки",
            "Личная сводка",
            "Пока вас не было",
            "ВАШИ ПРИОРИТЕТЫ",
        ]:
            assert heading not in body
    # A new student in the same group has no enrollment, result, personal notification or request.
    same = User.objects.create_user(username="same-group", password=PASSWORD)
    StudentProfile.objects.create(
        user=same, full_name="Вымышленный Другой Студент", course=2, group=one.studentprofile.group
    )
    context = dashboard_context(same)
    assert context["nearest"] is None
    assert context["study"] is None


def test_dashboard_role_empty_and_term_selection(client, demo):
    one, _ = demo
    client.logout()
    assert client.get("/").url == "/login/?next=/"
    client.force_login(User.objects.get(username="operator.demo"))
    assert client.get("/").url == "/operator/requests/"
    client.force_login(one)
    term = Term.objects.get(code="fiction-study-demo")
    future = Term.objects.create(
        code="future",
        title="Будущий период",
        starts_on=term.ends_on + timedelta(days=1),
        ends_on=term.ends_on + timedelta(days=30),
    )
    offering = CourseOffering.objects.filter(group=one.studentprofile.group).first()
    new = CourseOffering.objects.create(
        subject=offering.subject,
        group=offering.group,
        term=future,
        control_type=offering.control_type,
    )
    Enrollment.objects.create(student=one.studentprofile, offering=new)
    assert dashboard_context(one)["study"]["term"] == term
    with patch(
        "apps.dashboard.selectors.timezone.localdate",
        return_value=term.ends_on + timedelta(days=90),
    ):
        context = dashboard_context(one)
        assert context["study"]["term_state"] == "past" and context["study"]["term"] == future
    missing = User.objects.create_user(username="no-profile", password=PASSWORD)
    client.force_login(missing)
    assert client.get("/").status_code == 403
    one.is_active = False
    one.save()
    with pytest.raises(PermissionDenied):
        dashboard_context(one)


def test_dashboard_nearest_cancel_and_result_deadline(demo):
    one, _ = demo
    context = dashboard_context(one)
    nearest = context["nearest"]
    assert nearest and nearest.status == "scheduled"
    if isinstance(nearest, Lesson):
        change_lesson(
            lesson_id=nearest.pk,
            expected_version=nearest.version,
            status="cancelled",
            reason="Отмена",
        )
        assert dashboard_context(one)["nearest"].pk != nearest.pk


def test_dashboard_bounded_queries(client, demo):
    one = demo[0]
    client.force_login(one)
    with CaptureQueriesContext(connection) as initial:
        assert client.get("/").status_code == 200
    offering = CourseOffering.objects.filter(group=one.studentprofile.group).first()
    for index in range(30):
        Deadline.objects.create(
            offering=offering,
            title=f"Вымышленный срок {index}",
            due_at=timezone.now() + timedelta(days=1),
        )
        Notification.objects.create(
            recipient=one,
            kind="deadline",
            title=f"Событие {index}",
            body="Вымышленные данные",
            target_type="deadline",
            target_id=uuid.uuid4(),
            dedupe_key=f"bounded-{index}",
        )
    with CaptureQueriesContext(connection) as expanded:
        response = client.get("/")
        assert response.status_code == 200
        assert "Вымышленный срок" not in response.content.decode()
    # GET renders all subject/room/teacher/status links: no hidden lazy N+1.
    assert len(expanded) <= len(initial) + 1
    assert len(expanded) < 45


@pytest.mark.django_db(transaction=True)
def test_concurrent_seed_serializes(monkeypatch):
    # Two independent DB connections use the same advisory transaction lock.
    for name in [
        "DEMO_STUDENT_ONE_PASSWORD",
        "DEMO_STUDENT_TWO_PASSWORD",
        "DEMO_OPERATOR_PASSWORD",
    ]:
        monkeypatch.setenv(name, PASSWORD)
    barrier = Barrier(2)

    def run():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            call_command("seed_demo", stdout=StringIO())
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: run(), range(2)))
    assert User.objects.count() == 3
    assert ServiceRequest.objects.count() == 2 and RequestEvent.objects.count() == 4


def test_seed_keeps_preexisting_fixture_request(monkeypatch):
    for name in [
        "DEMO_STUDENT_ONE_PASSWORD",
        "DEMO_STUDENT_TWO_PASSWORD",
        "DEMO_OPERATOR_PASSWORD",
    ]:
        monkeypatch.setenv(name, PASSWORD)
    call_command("provision_accounts", stdout=StringIO())
    user = User.objects.get(username="student.two")
    application = create_request(
        actor=user,
        purpose="benefits",
        comment="Вымышленная демонстрационная заявка.",
        submission_key=uuid.uuid5(uuid.NAMESPACE_URL, "fiction-request/student.two/1"),
    )
    seed(monkeypatch)
    application.refresh_from_db()
    assert application.status == "submitted" and application.events.count() == 1


def test_extend_does_not_restore_elapsed_today(monkeypatch):
    seed(monkeypatch)
    term = Term.objects.get(code="fiction-study-demo")
    monday = term.starts_on + timedelta(days=7)
    elapsed_id = uuid.uuid5(uuid.NAMESPACE_URL, "fiction-study-demo/0/0/2")
    # This fixture has no history and can be removed to exercise missing-key recovery.
    Lesson.objects.get(pk=elapsed_id).delete()
    from datetime import datetime, time

    frozen = datetime.combine(monday + timedelta(days=14), time(18), MOSCOW)
    with patch(
        "apps.academics.management.commands.extend_demo_schedule.timezone.now", return_value=frozen
    ):
        call_command("extend_demo_schedule", stdout=StringIO())
    assert not Lesson.objects.filter(pk=elapsed_id).exists()


def test_extend_through_saturday_preserves_schedule(monkeypatch):
    from datetime import date, datetime, time

    anchor = date(2026, 11, 20)
    frozen = datetime.combine(anchor, time(18), MOSCOW)
    seed(monkeypatch, anchor_date=anchor)
    original = list(Lesson.objects.order_by("pk").values())
    term = Term.objects.get(code="fiction-study-demo")
    original_end = term.ends_on
    # An existing cancelled day remains occupied even without an active lesson.
    cancelled = Lesson.objects.filter(starts_at__date=date(2026, 11, 23)).first()
    change_lesson(
        lesson_id=cancelled.pk,
        expected_version=cancelled.version,
        status="cancelled",
        reason="Вымышленная отмена",
    )
    preserved = list(Lesson.objects.order_by("pk").values())
    history = list(LessonChange.objects.order_by("pk").values())
    options = {"anchor_date": anchor, "through_date": date(2026, 11, 28)}
    with patch(
        "apps.academics.management.commands.extend_demo_schedule.timezone.now", return_value=frozen
    ):
        call_command("extend_demo_schedule", stdout=StringIO(), **options)
    added = Lesson.objects.exclude(pk__in=[item["id"] for item in original])
    assert added.count() == 6
    for group in ["МИ-201", "МИ-302"]:
        lessons = list(added.filter(offering__group__code=group).order_by("starts_at"))
        assert [timezone.localdate(item.starts_at, MOSCOW) for item in lessons] == [
            date(2026, 11, 24),
            date(2026, 11, 26),
            date(2026, 11, 28),
        ]
        assert len({item.offering_id for item in lessons}) == 3
    assert (
        list(
            Lesson.objects.filter(pk__in=[item["id"] for item in original]).order_by("pk").values()
        )
        == preserved
    )
    assert list(LessonChange.objects.order_by("pk").values()) == history
    # Moving an appended lesson away does not cause its original date to be regenerated.
    moved = added.first()
    change_lesson(
        lesson_id=moved.pk,
        expected_version=moved.version,
        starts_at=moved.starts_at + timedelta(days=10),
        ends_at=moved.ends_at + timedelta(days=10),
        reason="Вымышленный перенос",
    )
    before_repeat = list(Lesson.objects.order_by("pk").values())
    with patch(
        "apps.academics.management.commands.extend_demo_schedule.timezone.now", return_value=frozen
    ):
        call_command("extend_demo_schedule", stdout=StringIO(), **options)
    assert list(Lesson.objects.order_by("pk").values()) == before_repeat
    term.refresh_from_db()
    assert term.ends_on == original_end


def test_extend_through_rejects_invalid_range_and_fixture_ownership(monkeypatch):
    from datetime import date

    seed(monkeypatch, anchor_date=date(2026, 11, 20))
    with pytest.raises(CommandError, match="on or after"):
        call_command(
            "extend_demo_schedule",
            anchor_date=date(2026, 11, 28),
            through_date=date(2026, 11, 20),
            stdout=StringIO(),
        )
    profile = StudentProfile.objects.get(user__username="student.two")
    enrollment = Enrollment.objects.filter(student=profile).first()
    GradeResult.objects.filter(enrollment=enrollment).delete()
    enrollment.delete()
    original = list(Lesson.objects.order_by("pk").values())
    with pytest.raises(CommandError, match="enrollments"):
        call_command(
            "extend_demo_schedule",
            anchor_date=date(2026, 11, 20),
            through_date=date(2026, 11, 28),
            stdout=StringIO(),
        )
    assert list(Lesson.objects.order_by("pk").values()) == original


def test_extend_through_skips_elapsed_slots_and_resource_conflicts(monkeypatch):
    from datetime import date, datetime, time

    from apps.schedule.services import create_lesson

    anchor = date(2026, 11, 20)
    seed(monkeypatch, anchor_date=anchor)
    source = Lesson.objects.first()
    # A different group uses the shared teacher/room at group two's future slot.
    starts = datetime.combine(date(2026, 11, 26), time(11), MOSCOW)
    other = CourseOffering.objects.exclude(
        group=StudentProfile.objects.get(user__username="student.two").group
    ).first()
    create_lesson(
        offering=other,
        teacher=source.teacher,
        room=source.room,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=90),
    )
    frozen = datetime.combine(date(2026, 11, 26), time(10), MOSCOW)
    with patch(
        "apps.academics.management.commands.extend_demo_schedule.timezone.now", return_value=frozen
    ):
        call_command(
            "extend_demo_schedule",
            anchor_date=anchor,
            through_date=date(2026, 11, 29),
            stdout=StringIO(),
        )
    supplements = Lesson.objects.filter(
        starts_at__date__in=[date(2026, 11, 26), date(2026, 11, 28), date(2026, 11, 29)]
    )
    assert supplements.count() == 1
    assert supplements.get().pk not in {
        uuid.uuid5(uuid.NAMESPACE_URL, f"fiction-study-demo/supplement/{group}/2026-11-26")
        for group in ["МИ-201", "МИ-302"]
    }
    assert not Lesson.objects.filter(offering__group__code="МИ-302", starts_at=starts).exists()
