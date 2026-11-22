from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from threading import Barrier
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, close_old_connections, transaction
from django.utils import timezone

from apps.academics.models import (
    CourseOffering,
    Enrollment,
    Faculty,
    Program,
    Room,
    StudyGroup,
    Subject,
    Teacher,
    Term,
)
from apps.academics.services import enroll
from apps.accounts.models import StudentProfile, User
from apps.schedule.models import Lesson, LessonChange
from apps.schedule.selectors import MOSCOW, period_for, schedule_for
from apps.schedule.services import StaleLessonVersion, change_lesson, create_lesson

pytestmark = pytest.mark.django_db


@pytest.fixture
def study():
    faculty = Faculty.objects.create(code="f", name="Вымышленный факультет")
    program = Program.objects.create(code="p", name="Вымышленная программа", faculty=faculty)
    group = StudyGroup.objects.create(code="A", program=program)
    other = StudyGroup.objects.create(code="B", program=program)
    students = []
    for index in range(3):
        user = User.objects.create_user(username=f"s{index}")
        students.append(
            StudentProfile.objects.create(
                user=user,
                full_name=f"Вымышленный {index}",
                course=2,
                group=group if index < 2 else other,
            )
        )
    operator = User.objects.create_user(username="op", role="operator")
    term = Term.objects.create(
        code="term", title="Семестр", starts_on=date(2026, 9, 1), ends_on=date(2026, 12, 31)
    )
    subject = Subject.objects.create(code="own", name="Доступная дисциплина")
    offering = CourseOffering.objects.create(
        subject=subject, group=group, term=term, control_type="exam"
    )
    enroll(student=students[0], offering=offering)
    teacher = Teacher.objects.create(code="t", full_name="Вымышленный преподаватель")
    room = Room.objects.create(code="r", building="Корпус А", number="204")
    starts = datetime(2026, 11, 2, 9, tzinfo=MOSCOW)
    lesson = create_lesson(
        offering=offering,
        teacher=teacher,
        room=room,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=90),
    )
    return students, operator, lesson


def test_enrollment_and_database_constraints(study):
    students, _, lesson = study
    assert enroll(student=students[0], offering=lesson.offering).pk == Enrollment.objects.get().pk
    with pytest.raises(ValidationError):
        enroll(student=students[2], offering=lesson.offering)
    for model, kwargs in [
        (Enrollment, {"student": students[0], "offering": lesson.offering}),
        (
            CourseOffering,
            {
                "subject": lesson.offering.subject,
                "group": lesson.offering.group,
                "term": lesson.offering.term,
                "control_type": "credit",
            },
        ),
        (
            Term,
            {
                "code": "bad",
                "title": "bad",
                "starts_on": date(2026, 12, 1),
                "ends_on": date(2026, 11, 1),
            },
        ),
    ]:
        with pytest.raises(IntegrityError), transaction.atomic():
            model.objects.create(**kwargs)
    for fields in [{"ends_at": lesson.starts_at}, {"status": "bad"}, {"version": 0}]:
        with pytest.raises(IntegrityError), transaction.atomic():
            Lesson.objects.filter(pk=lesson.pk).update(**fields)
    with pytest.raises(IntegrityError), transaction.atomic():
        CourseOffering.objects.filter(pk=lesson.offering_id).update(control_type="bad")


def test_scoping_filters_and_access(client, study):
    students, operator, lesson = study
    assert client.get("/schedule/").status_code == 302
    for profile in students:
        client.force_login(profile.user)
        response = client.get("/schedule/?date=2026-11-02&view=week")
        assert response.status_code == 200
        assert ("Доступная дисциплина" in response.content.decode()) == (profile == students[0])
        assert "no-store" in response["Cache-Control"]
        assert client.get(f"/schedule/{lesson.pk}/").status_code == 404
        assert client.get(f"/schedule/?student={students[0].pk}").status_code == 400
        assert client.post("/schedule/", {"status": "cancelled"}).status_code == 405
    client.force_login(operator)
    assert client.get("/schedule/").status_code == 403
    with pytest.raises(Exception) as error:
        schedule_for(operator, date(2026, 11, 2), "day")
    assert error.type.__name__ == "PermissionDenied"


@pytest.mark.parametrize(
    "query",
    [
        "date=oops",
        "date=2026-02-30",
        "date=20261102",
        "view=year",
        "date=0001-01-01",
        "date=9999-12-31",
        "date=2026-11-02&date=2026-11-03",
        "view=day&view=week",
        "offering=1",
    ],
)
def test_bad_filters(client, study, query):
    client.force_login(study[0][0].user)
    assert client.get(f"/schedule/?{query}").status_code == 400


def test_moscow_midnight_and_week(client, study):
    students, _, lesson = study
    assert period_for(date(2026, 11, 8), "week") == (date(2026, 11, 2), date(2026, 11, 9))
    assert period_for(date(2026, 11, 9), "week") == (date(2026, 11, 9), date(2026, 11, 16))
    midnight = datetime(2026, 11, 8, 21, 0, tzinfo=UTC)
    create_lesson(
        offering=lesson.offering,
        room=lesson.room,
        teacher=lesson.teacher,
        starts_at=midnight,
        ends_at=midnight + timedelta(hours=1),
    )
    assert schedule_for(students[0].user, date(2026, 11, 8), "day")[0].count() == 0
    assert schedule_for(students[0].user, date(2026, 11, 9), "day")[0].count() == 1
    assert schedule_for(students[0].user, date(2026, 11, 2), "week")[0].count() == 1
    client.force_login(students[0].user)
    with patch("django.utils.timezone.now", return_value=midnight):
        client.force_login(students[0].user)
        response = client.get("/schedule/")
        assert response.context["day"] == date(2026, 11, 9)
    with timezone.override("UTC"):
        edge = datetime(2026, 9, 1, 0, 10, tzinfo=MOSCOW)
        create_lesson(
            offering=lesson.offering,
            room=lesson.room,
            teacher=lesson.teacher,
            starts_at=edge,
            ends_at=edge + timedelta(hours=1),
        )
    with pytest.raises(ValidationError):
        create_lesson(
            offering=lesson.offering,
            room=lesson.room,
            teacher=lesson.teacher,
            starts_at=datetime(2026, 11, 2, 9),
            ends_at=datetime(2026, 11, 2, 10),
        )


def test_moves_cancel_snapshots_and_rollback(study):
    students, _, lesson = study
    original = lesson.starts_at
    identity = lesson.pk
    for version in (1, 2):
        lesson = change_lesson(
            lesson_id=identity,
            expected_version=version,
            starts_at=original + timedelta(days=7 * version),
            ends_at=original + timedelta(days=7 * version, minutes=90),
            reason=f"Перенос {version}",
        )
    assert Lesson.objects.count() == 1
    assert schedule_for(students[0].user, date(2026, 11, 2), "week")[1].count() == 1
    assert schedule_for(students[0].user, date(2026, 11, 9), "week")[1].count() == 1
    assert schedule_for(students[0].user, date(2026, 11, 16), "week")[0].count() == 1
    with pytest.raises(StaleLessonVersion):
        change_lesson(lesson_id=identity, expected_version=1, status="cancelled", reason="старое")
    with patch.object(LessonChange, "save", side_effect=RuntimeError("rollback")):
        with pytest.raises(RuntimeError):
            change_lesson(lesson_id=identity, expected_version=3, status="cancelled", reason="сбой")
    lesson.refresh_from_db()
    assert lesson.version == 3 and lesson.status == "scheduled"
    assert LessonChange.objects.count() == 2
    lesson = change_lesson(
        lesson_id=identity, expected_version=3, status="cancelled", reason="Отмена"
    )
    assert schedule_for(students[0].user, date(2026, 11, 16), "day")[0].get().status == "cancelled"
    event = lesson.changes.first()
    Teacher.objects.filter(pk=lesson.teacher_id).update(full_name="Новое имя")
    Room.objects.filter(pk=lesson.room_id).update(number="999")
    event.refresh_from_db()
    assert event.old_teacher_label == "Вымышленный преподаватель"
    assert event.old_room_label == "Корпус А · 204"
    with pytest.raises(ValidationError):
        event.save()
    with pytest.raises(ValidationError):
        event.delete()
    duplicate = LessonChange.objects.get(pk=event.pk)
    duplicate._state.adding = True
    with pytest.raises(IntegrityError), transaction.atomic():
        duplicate.save()
    with pytest.raises(IntegrityError), transaction.atomic():
        event.pk = None
        event._state.adding = True
        event.save()


@pytest.mark.django_db(transaction=True)
def test_parallel_changes_lock_and_conflict(study):
    lesson = study[2]
    barrier = Barrier(2, timeout=10)

    def update(reason):
        close_old_connections()
        try:
            barrier.wait()
            change_lesson(
                lesson_id=lesson.pk, expected_version=1, status="cancelled", reason=reason
            )
            return "updated"
        except StaleLessonVersion:
            return "stale"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(update, ["Первое", "Второе"]))
    assert sorted(results) == ["stale", "updated"]
    assert LessonChange.objects.filter(lesson=lesson).count() == 1


def test_demo_idempotent_and_profiles_required(monkeypatch):
    with pytest.raises(CommandError):
        call_command("provision_study_demo")
    for variable in [
        "DEMO_STUDENT_ONE_PASSWORD",
        "DEMO_STUDENT_TWO_PASSWORD",
        "DEMO_OPERATOR_PASSWORD",
    ]:
        monkeypatch.setenv(variable, "Fictional-testing-9568!")
    call_command("provision_accounts")
    hashes = list(User.objects.order_by("id").values_list("password", flat=True))
    call_command("provision_study_demo", anchor_date=date(2026, 11, 4))
    assert Lesson.objects.count() == 54 and Enrollment.objects.count() == 6
    active = list(Lesson.objects.filter(status="scheduled").order_by("starts_at"))
    for first, second in zip(active, active[1:], strict=False):
        assert first.ends_at <= second.starts_at  # fictional shared teacher has no overlaps
    lesson = Lesson.objects.filter(status="scheduled").first()
    change_lesson(
        lesson_id=lesson.pk,
        expected_version=lesson.version,
        status="cancelled",
        reason="Сохранить пользовательское изменение",
    )
    state = list(Lesson.objects.order_by("id").values_list("id", "starts_at", "status", "version"))
    call_command("provision_study_demo", anchor_date=date(2027, 1, 1))
    assert state == list(
        Lesson.objects.order_by("id").values_list("id", "starts_at", "status", "version")
    )
    assert hashes == list(User.objects.order_by("id").values_list("password", flat=True))


def test_move_within_week_retains_old_marker_and_single_actual(client, study):
    students, _, lesson = study
    change_lesson(
        lesson_id=lesson.pk,
        expected_version=1,
        starts_at=lesson.starts_at + timedelta(days=1),
        ends_at=lesson.ends_at + timedelta(days=1),
        reason="На вторник",
    )
    current, markers = schedule_for(students[0].user, date(2026, 11, 2), "week")
    assert current.count() == markers.count() == 1
    assert schedule_for(students[0].user, date(2026, 11, 2), "day")[0].count() == 0
    assert schedule_for(students[0].user, date(2026, 11, 2), "day")[1].count() == 1
    assert schedule_for(students[0].user, date(2026, 11, 3), "day")[0].count() == 1
    client.force_login(students[0].user)
    response = client.get("/schedule/?date=2026-11-02&view=week")
    assert "Перенесено" in response.content.decode()


def test_room_teacher_changes_and_invalid_update_are_atomic(client, study):
    students, _, lesson = study
    room = Room.objects.create(code="new", building="Корпус Б", number="310")
    teacher = Teacher.objects.create(code="new", full_name="Другой вымышленный преподаватель")
    updated = change_lesson(
        lesson_id=lesson.pk,
        expected_version=1,
        room=room,
        teacher=teacher,
        reason="Смена аудитории и преподавателя",
    )
    event = updated.changes.get()
    assert event.old_room_label == "Корпус А · 204"
    assert event.new_room_label == "Корпус Б · 310"
    assert event.old_teacher_label == "Вымышленный преподаватель"
    assert event.new_teacher_label == teacher.full_name
    assert updated.pk == lesson.pk and updated.starts_at == lesson.starts_at
    for changes in [
        {
            "starts_at": datetime(2027, 1, 1, 9, tzinfo=MOSCOW),
            "ends_at": datetime(2027, 1, 1, 10, tzinfo=MOSCOW),
        },
        {"status": "invalid"},
        {"offering": lesson.offering},
    ]:
        with pytest.raises(ValidationError):
            change_lesson(
                lesson_id=lesson.pk, expected_version=2, reason="Невалидное изменение", **changes
            )
    updated.refresh_from_db()
    assert updated.version == 2 and updated.changes.count() == 1
    change_lesson(
        lesson_id=lesson.pk,
        expected_version=2,
        starts_at=lesson.starts_at + timedelta(days=7),
        ends_at=lesson.ends_at + timedelta(days=7),
        reason="Скрытая для других история",
    )
    for profile in students[1:]:
        client.force_login(profile.user)
        text = client.get("/schedule/?date=2026-11-02&view=week").content.decode()
        assert "Скрытая для других история" not in text
        assert "Доступная дисциплина" not in text


@pytest.mark.parametrize("view, selected", [("day", "2026-11-01"), ("week", "2026-10-27")])
def test_empty_schedule_actions_use_own_next_moscow_day(client, study, view, selected):
    students, _, lesson = study
    # Earlier rows must not win: a cancelled own lesson and a foreign active one.
    cancelled = datetime(2026, 11, 1, 21, tzinfo=UTC)
    create_lesson(
        offering=lesson.offering,
        teacher=lesson.teacher,
        room=lesson.room,
        starts_at=cancelled,
        ends_at=cancelled + timedelta(minutes=30),
        status="cancelled",
    )
    foreign = CourseOffering.objects.create(
        subject=lesson.offering.subject,
        group=students[2].group,
        term=lesson.offering.term,
        control_type="exam",
    )
    enroll(student=students[2], offering=foreign)
    create_lesson(
        offering=foreign,
        teacher=lesson.teacher,
        room=lesson.room,
        starts_at=cancelled + timedelta(minutes=30),
        ends_at=cancelled + timedelta(hours=1),
    )
    client.force_login(students[0].user)
    with patch("django.utils.timezone.now", return_value=cancelled - timedelta(hours=2)):
        response = client.get(f"/schedule/?date={selected}&view={view}")
    html = response.content.decode()
    assert not response.context["timeline"]
    assert response.context["next_lesson_day"] == date(2026, 11, 2)
    assert 'href="?date=2026-11-02&view=day">Ближайшее занятие</a>' in html
    assert (f'href="?date={selected}&view=week">Открыть неделю</a>' in html) == (view == "day")


def test_empty_week_without_future_and_filled_page_skip_lookup(client, study):
    students, _, _ = study
    client.force_login(students[0].user)
    with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 1, tzinfo=MOSCOW)):
        response = client.get("/schedule/?date=2026-11-09&view=week")
    html = response.content.decode()
    assert response.context["next_lesson_day"] is None
    assert "Следующих занятий пока нет" in html
    assert "Ближайшее занятие</a>" not in html
    assert "Открыть неделю</a>" not in html
    with patch("apps.schedule.views.next_lesson_date") as lookup:
        response = client.get("/schedule/?date=2026-11-02&view=day")
    assert response.context["timeline"]
    lookup.assert_not_called()


def test_historical_empty_day_skips_past_lessons(client, study):
    client.force_login(study[0][0].user)
    with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 3, tzinfo=MOSCOW)):
        response = client.get("/schedule/?date=2026-11-01&view=day")
    assert response.context["next_lesson_day"] is None
    assert "Следующих занятий пока нет" in response.content.decode()
