import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Barrier
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import close_old_connections, transaction
from django.test import Client
from django.utils import timezone

from apps.academics.models import Enrollment, Faculty, Program, StudyGroup
from apps.academics.services import enroll
from apps.accounts.models import OperatorScope
from apps.grades.models import Assessment, GradeResult
from apps.notifications.models import (
    Announcement,
    AnnouncementRead,
    Deadline,
    Notification,
    PersonalDeadline,
)
from apps.notifications.selectors import announcements
from apps.notifications.services import (
    create_deadline,
    mark_announcement,
    mark_notification,
    notify,
    send_reminders,
    update_deadline,
)
from apps.requests.models import RequestEvent, ServiceRequest
from apps.requests.services import create_request, transition_request
from apps.schedule.models import LessonChange
from apps.schedule.services import change_lesson
from tests.test_schedule import study  # noqa: F401

# ruff: noqa: F811
pytestmark = pytest.mark.django_db


def announcement(**fields):
    return Announcement.objects.create(title="Новость", body="Текст", audience_kind="all", **fields)


def message(user, **fields):
    return notify(
        recipient_id=user.pk,
        kind="request",
        title="Событие",
        body="Текст",
        target_id=uuid.uuid4(),
        dedupe_key=uuid.uuid4().hex,
        **fields,
    )


def test_audiences_time_read_scope_and_xss(client, study):
    students, operator, _ = study
    OperatorScope.objects.create(operator=operator, group=students[0].group)
    now = timezone.now()
    public = announcement(publish_at=now)
    grouped = Announcement.objects.create(
        title="Группа",
        body="<script>alert(1)</script>",
        audience_kind="group",
        target_group=students[0].group,
        publish_at=now,
    )
    faculty = Announcement.objects.create(
        title="Факультет",
        body="Текст",
        audience_kind="faculty",
        target_faculty=students[0].group.program.faculty,
        publish_at=now,
    )
    announcement(publish_at=now + timedelta(seconds=1))
    announcement(publish_at=now - timedelta(hours=1), expires_at=now)
    outsider_faculty = Faculty.objects.create(code="other", name="Другой вымышленный факультет")
    program = Program.objects.create(code="other", name="Программа", faculty=outsider_faculty)
    group = StudyGroup.objects.create(code="C", program=program)
    students[2].group = group
    students[2].save()
    with patch("apps.notifications.selectors.timezone.now", return_value=now):
        assert set(announcements(students[0].user).values_list("pk", flat=True)) == {
            public.pk,
            grouped.pk,
            faculty.pk,
        }
        assert set(announcements(students[1].user).values_list("pk", flat=True)) == {
            public.pk,
            grouped.pk,
            faculty.pk,
        }
        assert list(announcements(students[2].user).values_list("pk", flat=True)) == [public.pk]
        assert set(announcements(operator).values_list("pk", flat=True)) == {public.pk, grouped.pk}
    assert client.get("/notifications/").status_code == 302
    client.force_login(students[0].user)
    response = client.get("/notifications/")
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    assert b"&lt;script&gt;" in response.content and b"<script>alert" not in response.content
    assert not AnnouncementRead.objects.exists()
    assert client.get(f"/announcements/{grouped.pk}/read/").status_code == 405
    assert client.post(f"/announcements/{grouped.pk}/read/").status_code == 302
    first = AnnouncementRead.objects.get().read_at
    client.post(f"/announcements/{grouped.pk}/read/")
    assert AnnouncementRead.objects.get().read_at == first
    assert not announcements(students[1].user).get(pk=grouped.pk).is_read
    client.force_login(operator)
    assert client.post(f"/announcements/{grouped.pk}/read/").status_code == 302
    secure = Client(enforce_csrf_checks=True)
    secure.force_login(students[0].user)
    assert secure.post(f"/announcements/{public.pk}/read/").status_code == 403


@pytest.mark.parametrize(
    "query",
    ["user=1", "page=0", "page=no", "page=1&page=2", "unread=0", "kind=unknown", "news_page=-1"],
)
def test_invalid_filters(client, study, query):
    client.force_login(study[0][0].user)
    assert client.get("/notifications/?" + query).status_code == 400


def test_personal_pagination_owner_read_and_targets(client, study):
    students, _, lesson = study
    own = message(students[0].user)
    foreign = message(students[1].user)
    for _ in range(22):
        message(students[0].user)
    client.force_login(students[0].user)
    response = client.get("/notifications/")
    assert len(response.context["items"]) == 20
    assert response.context["unread_count"] == 23
    assert len(client.get("/notifications/?page=2").context["items"]) == 3
    assert client.get("/notifications/?page=3").status_code == 404
    assert client.post(f"/notifications/{foreign.pk}/read/").status_code == 404
    assert client.get(f"/notifications/{foreign.pk}/open/").status_code == 404
    client.post(f"/notifications/{own.pk}/read/")
    own.refresh_from_db()
    first = own.read_at
    client.post(f"/notifications/{own.pk}/read/")
    own.refresh_from_db()
    assert own.read_at == first
    assert client.get(f"/notifications/{own.pk}/open/").status_code == 404
    application = create_request(
        actor=students[0].user, purpose="other", submission_key=uuid.uuid4()
    )
    item = Notification.objects.get(target_id=application.pk)
    assert client.get(f"/notifications/{item.pk}/open/").url == f"/requests/{application.pk}/"
    target = notify(
        recipient_id=students[0].user.pk,
        kind="schedule",
        title="Изменение",
        body="Текст",
        target_id=lesson.pk,
        dedupe_key="lesson",
    )
    assert client.get(f"/notifications/{target.pk}/open/").url.endswith("date=2026-11-02&view=day")
    Enrollment.objects.all().delete()
    assert client.get(f"/notifications/{target.pk}/open/").status_code == 404


def test_atomic_source_events_and_dedupe(study):
    students, operator, lesson = study
    OperatorScope.objects.create(operator=operator, group=students[0].group)
    key = uuid.uuid4()
    with patch("apps.notifications.services.notify", side_effect=RuntimeError):
        with pytest.raises(RuntimeError):
            create_request(actor=students[0].user, purpose="other", submission_key=key)
    assert not ServiceRequest.objects.exists() and not RequestEvent.objects.exists()
    application = create_request(actor=students[0].user, purpose="other", submission_key=key)
    create_request(actor=students[0].user, purpose="other", submission_key=key)
    assert Notification.objects.filter(target_id=application.pk).count() == 1
    with patch("apps.notifications.services.notify", side_effect=RuntimeError):
        with pytest.raises(RuntimeError):
            transition_request(
                actor=operator,
                request_id=application.pk,
                expected_version=1,
                desired_status="in_progress",
            )
        with pytest.raises(RuntimeError):
            change_lesson(
                lesson_id=lesson.pk,
                expected_version=1,
                reason="Перенос",
                starts_at=lesson.starts_at + timedelta(hours=1),
                ends_at=lesson.ends_at + timedelta(hours=1),
            )
    application.refresh_from_db()
    lesson.refresh_from_db()
    assert application.version == 1 and lesson.version == 1 and not LessonChange.objects.exists()
    change_lesson(lesson_id=lesson.pk, expected_version=1, reason="Отмена", status="cancelled")
    assert list(
        Notification.objects.filter(kind="schedule").values_list("recipient_id", flat=True)
    ) == [students[0].user_id]


def test_deadline_revision_reminders_suppression_and_missed_run(client, study):
    students, _, lesson = study
    enroll(student=students[1], offering=lesson.offering)
    assessment = Assessment.objects.create(
        offering=lesson.offering, title="Проект", kind="coursework", max_points=20
    )
    now = timezone.now()
    deadline = create_deadline(
        offering=lesson.offering,
        assessment=assessment,
        title="Проект",
        due_at=now + timedelta(hours=24),
    )
    assert send_reminders() == 0  # Archived course deadlines no longer generate reminders.
    deadline = update_deadline(deadline_id=deadline.pk, expected_revision=1, title="Новое название")
    assert deadline.revision == 1
    deadline = update_deadline(
        deadline_id=deadline.pk, expected_revision=1, due_at=now - timedelta(days=3)
    )
    assert deadline.revision == 2
    assert send_reminders() == 0  # Archived rows are preserved but inactive
    deadline = update_deadline(deadline_id=deadline.pk, expected_revision=2, cancelled_at=now)
    assert deadline.revision == 3 and send_reminders() == 0
    with pytest.raises(ValidationError):
        update_deadline(deadline_id=deadline.pk, expected_revision=2, title="Stale")
    with pytest.raises(ValidationError):
        create_deadline(offering=lesson.offering, title="Naive", due_at=now.replace(tzinfo=None))
    client.force_login(students[0].user)
    assert client.get(f"/deadlines/{deadline.pk}/").status_code == 404
    client.force_login(students[2].user)
    assert client.get(f"/deadlines/{deadline.pk}/").status_code == 404


@pytest.mark.django_db(transaction=True)
def test_parallel_reminders_and_reads(study):
    students, _, lesson = study
    PersonalDeadline.objects.create(
        student=students[0], title="Проект", due_date=timezone.localdate()
    )
    news = announcement()
    item = message(students[0].user)
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait()
            send_reminders()
            mark_notification(students[0].user, item.pk)
            mark_announcement(students[0].user, news.pk)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: worker(), range(2)))
    assert Notification.objects.filter(kind="personal").count() == 1
    assert AnnouncementRead.objects.count() == 1
    assert Notification.objects.get(pk=item.pk).read_at


def test_demo_provision_is_additive():
    import os

    with patch.dict(
        os.environ,
        {
            "DEMO_STUDENT_ONE_PASSWORD": "Fictional-test-123!",
            "DEMO_STUDENT_TWO_PASSWORD": "Fictional-test-456!",
            "DEMO_OPERATOR_PASSWORD": "Fictional-test-789!",
        },
    ):
        call_command("provision_accounts")
    call_command("provision_study_demo", anchor_date=date(2026, 11, 4))
    call_command("provision_grades_demo")
    call_command("provision_notifications_demo")
    from apps.accounts.models import User

    user = User.objects.get(username="student.one")
    mark_announcement(user, Announcement.objects.get(code="demo-all").pk)
    call_command("provision_notifications_demo")
    assert Announcement.objects.count() == 3 and Deadline.objects.count() == 0
    assert AnnouncementRead.objects.count() == 1


def test_future_result_inactive_and_far_future_deadlines(study):
    students, _, lesson = study
    assessment = Assessment.objects.create(
        offering=lesson.offering, title="Работа", kind="coursework", max_points=20
    )
    now = timezone.now()
    create_deadline(
        offering=lesson.offering,
        assessment=assessment,
        title="Работа",
        due_at=now + timedelta(hours=1),
    )
    GradeResult.objects.create(
        assessment=assessment,
        enrollment=Enrollment.objects.get(student=students[0]),
        points=20,
        published_at=now + timedelta(days=1),
    )
    create_deadline(
        offering=lesson.offering, title="Далёкий срок", due_at=now + timedelta(hours=25)
    )
    assert send_reminders() == 0
    assert not Notification.objects.exists()
    students[0].user.is_active = False
    students[0].user.save()
    update_deadline(
        deadline_id=Deadline.objects.get(assessment=assessment).pk,
        expected_revision=1,
        due_at=now - timedelta(days=1),
    )
    assert send_reminders() == 0


def test_announcement_database_constraints(study):
    from django.db import IntegrityError

    for fields in [
        {"audience_kind": "group"},
        {"audience_kind": "all", "target_group": study[0][0].group},
        {"audience_kind": "faculty", "target_group": study[0][0].group},
        {"audience_kind": "unknown"},
        {
            "audience_kind": "all",
            "publish_at": timezone.now(),
            "expires_at": timezone.now() - timedelta(hours=1),
        },
    ]:
        with pytest.raises(IntegrityError), transaction.atomic():
            Announcement.objects.create(title="Текст", body="Текст", **fields)


def test_operator_target_rechecks_scope_and_read_csrf(client, study):
    students, operator, _ = study
    scope = OperatorScope.objects.create(operator=operator, group=students[0].group)
    application = create_request(
        actor=students[0].user, purpose="other", submission_key=uuid.uuid4()
    )
    item = notify(
        recipient_id=operator.pk,
        kind="request",
        title="Заявка",
        body="Открыть",
        target_id=application.pk,
        dedupe_key="operator-event",
    )
    client.force_login(operator)
    assert (
        client.get(f"/notifications/{item.pk}/open/").url == f"/operator/requests/{application.pk}/"
    )
    assert client.get(f"/notifications/{item.pk}/read/").status_code == 405
    secure = Client(enforce_csrf_checks=True)
    secure.force_login(operator)
    assert secure.post(f"/notifications/{item.pk}/read/").status_code == 403
    scope.delete()
    assert client.get(f"/notifications/{item.pk}/open/").status_code == 404
    operator.is_active = False
    operator.save()
    assert client.get("/notifications/").status_code == 302


def test_announcement_aware_and_deadline_assessment_validation(study):
    from apps.academics.models import CourseOffering, Subject

    students, _, lesson = study
    with pytest.raises(ValidationError):
        Announcement(
            title="Текст",
            body="Текст",
            audience_kind="all",
            publish_at=timezone.now().replace(tzinfo=None),
        ).full_clean()
    other = CourseOffering.objects.create(
        subject=Subject.objects.create(code="another", name="Другой курс"),
        group=students[0].group,
        term=lesson.offering.term,
        control_type="exam",
    )
    assessment = Assessment.objects.create(
        offering=other, title="Другая работа", kind="coursework", max_points=10
    )
    with pytest.raises(ValidationError):
        create_deadline(
            offering=lesson.offering, assessment=assessment, title="Текст", due_at=timezone.now()
        )


def test_deadline_and_announcement_pagination(client, study):
    students, _, lesson = study
    for index in range(22):
        Announcement.objects.create(title=f"Новость {index}", body="Текст", audience_kind="all")
        create_deadline(
            offering=lesson.offering,
            title=f"Срок {index}",
            due_at=timezone.now() + timedelta(hours=index),
        )
    client.force_login(students[0].user)
    response = client.get("/notifications/?news_page=2")
    assert len(response.context["announcements"]) == 2
    assert "deadlines" not in response.context
    assert client.get("/notifications/?deadline_page=2").status_code == 400
    assert response.context["items"].paginator.count == 0


def test_operator_publish_permissions_validation_and_replay(client, study):
    from django.core.exceptions import PermissionDenied

    from apps.notifications.services import publish_announcement

    students, operator, _ = study
    url = "/operator/announcements/new/"
    assert client.get(url).status_code == 302
    client.force_login(students[0].user)
    assert client.get(url).status_code == 403
    assert client.post(url, {}).status_code == 403
    client.force_login(operator)
    response = client.get(url)
    assert "no-store" in response["Cache-Control"]
    assert "пока не закреплены" in response.content.decode()
    scope = OperatorScope.objects.create(operator=operator, group=students[0].group)
    response = client.get(url)
    assert str(students[0].group.code) in response.content.decode()
    secure = Client(enforce_csrf_checks=True)
    secure.force_login(operator)
    assert secure.post(url, {}).status_code == 403
    payload = {
        "group": students[0].group_id,
        "title": "<b>Объявление</b>",
        "body": "<script>alert(1)</script>",
        "submission_key": uuid.uuid4(),
    }
    assert client.post(url, {**payload, "group": students[2].group_id}).status_code == 200
    assert not Announcement.objects.exists()
    invalid = client.post(url, {**payload, "title": "  "})
    assert invalid.status_code == 200 and not Announcement.objects.exists()
    assert b'aria-describedby="id_title_error"' in invalid.content
    assert client.post(url, {**payload, "submission_key": "wrong"}).status_code == 200
    result = client.post(url, payload)
    item = Announcement.objects.get()
    assert result.url == f"/notifications/#announcement-{item.pk}"
    assert item.audience_kind == "group" and item.target_group_id == students[0].group_id
    assert item.publish_at <= timezone.now()
    with pytest.raises(PermissionDenied):
        publish_announcement(
            students[0].user,
            group=students[0].group,
            title="Запрещено",
            body="Текст",
            submission_key=uuid.uuid4(),
        )
    assert client.post(url, payload).url == result.url
    duplicate = client.post(url, {**payload, "title": "Новый текст"})
    assert duplicate.status_code == 200
    assert "уже опубликована" in duplicate.content.decode()
    item.refresh_from_db()
    assert Announcement.objects.count() == 1 and item.title == payload["title"]
    assert item in announcements(students[0].user)
    assert item not in announcements(students[2].user)
    response = client.get(result.url)
    assert b"&lt;script&gt;" in response.content
    assert b"<script>alert" not in response.content
    scope.delete()
    with pytest.raises(PermissionDenied):
        publish_announcement(
            operator, group=students[0].group, title="А", body="Б", submission_key=uuid.uuid4()
        )
    OperatorScope.objects.create(operator=operator, group=students[2].group)
    original_key = payload["submission_key"]
    payload["submission_key"] = uuid.uuid4()
    payload["group"] = students[2].group_id
    assert client.post(url, payload).status_code == 302
    assert Announcement.objects.count() == 2
    altered_group = client.post(url, {**payload, "submission_key": original_key})
    assert altered_group.status_code == 200
    assert "уже опубликована" in altered_group.content.decode()
    assert Announcement.objects.count() == 2
    operator.is_active = False
    operator.save()
    with pytest.raises(PermissionDenied):
        publish_announcement(
            operator, group=students[2].group, title="А", body="Б", submission_key=uuid.uuid4()
        )


@pytest.mark.django_db(transaction=True)
def test_parallel_operator_publication_is_idempotent(study):
    from apps.notifications.services import publish_announcement

    students, operator, _ = study
    OperatorScope.objects.create(operator=operator, group=students[0].group)
    key = uuid.uuid4()
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait()
            return publish_announcement(
                operator, group=students[0].group, title="Новость", body="Текст", submission_key=key
            ).pk
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(lambda _: worker(), range(2)))
    assert ids[0] == ids[1] and Announcement.objects.count() == 1


@pytest.mark.parametrize("role", ["student", "operator"])
def test_read_all_scoped_across_pages_filters_and_repeat(client, study, role):
    students, operator, _ = study
    OperatorScope.objects.create(operator=operator, group=students[0].group)
    user = students[0].user if role == "student" else operator
    foreign = message(students[1].user)
    old_time = timezone.now() - timedelta(days=2)
    old = message(user)
    Notification.objects.filter(pk=old.pk).update(read_at=old_time)
    for _ in range(23):
        message(user)
    notify(
        recipient_id=user.pk,
        kind="schedule",
        title="Другой фильтр",
        body="Текст",
        target_id=uuid.uuid4(),
        dedupe_key="read-all-schedule",
    )
    public = [announcement() for _ in range(23)]
    AnnouncementRead.objects.create(announcement=public[0], user=user, read_at=old_time)
    grouped = Announcement.objects.create(
        title="Своя группа", body="Текст", audience_kind="group", target_group=students[0].group
    )
    excluded = [
        announcement(publish_at=timezone.now() + timedelta(days=1)),
        announcement(
            publish_at=timezone.now() - timedelta(days=2),
            expires_at=timezone.now() - timedelta(days=1),
        ),
        Announcement.objects.create(
            title="Чужая группа",
            body="Текст",
            audience_kind="group",
            target_group=students[2].group,
        ),
    ]
    faculty = Announcement.objects.create(
        title="Факультет",
        body="Текст",
        audience_kind="faculty",
        target_faculty=students[0].group.program.faculty,
    )
    if role == "operator":
        excluded.append(faculty)
    client.force_login(user)
    response = client.get("/notifications/?page=2&news_page=2&kind=request&unread=1")
    assert response.status_code == 200
    assert len(response.context["items"]) == 3
    assert 'action="/notifications/read-all/"' in response.content.decode()
    assert client.get("/notifications/read-all/").status_code == 405
    result = client.post(
        "/notifications/read-all/?kind=request&page=2", {"user": students[1].user_id}
    )
    assert result.status_code == 302 and result.url == "/notifications/"
    assert "no-store" in result["Cache-Control"]
    assert not Notification.objects.filter(recipient=user, read_at__isnull=True).exists()
    foreign.refresh_from_db()
    old.refresh_from_db()
    assert foreign.read_at is None and old.read_at == old_time
    assert not AnnouncementRead.objects.filter(user=students[1].user).exists()
    assert not AnnouncementRead.objects.filter(user=user, announcement__in=excluded).exists()
    assert AnnouncementRead.objects.filter(user=user, announcement=grouped).exists()
    assert AnnouncementRead.objects.get(user=user, announcement=public[0]).read_at == old_time
    first_reads = list(AnnouncementRead.objects.filter(user=user).values_list("pk", "read_at"))
    assert client.post("/notifications/read-all/").status_code == 302
    assert (
        list(AnnouncementRead.objects.filter(user=user).values_list("pk", "read_at")) == first_reads
    )
    response = client.get("/notifications/")
    assert response.context["unread_count"] == 0
    assert 'action="/notifications/read-all/"' not in response.content.decode()
    if role == "operator":
        OperatorScope.objects.all().delete()
        extra = Announcement.objects.create(
            title="Снята область",
            body="Текст",
            audience_kind="group",
            target_group=students[0].group,
        )
        client.post("/notifications/read-all/")
        assert not AnnouncementRead.objects.filter(user=user, announcement=extra).exists()


def test_read_all_auth_csrf_and_atomicity(client, study):
    from apps.notifications.services import mark_all_read

    user = study[0][0].user
    item = message(user)
    news = announcement()
    assert client.post("/notifications/read-all/").status_code == 302
    secure = Client(enforce_csrf_checks=True)
    secure.force_login(user)
    assert secure.post("/notifications/read-all/").status_code == 403
    secure.get("/notifications/")
    token = secure.cookies["csrftoken"].value
    with (
        patch(
            "apps.notifications.services.AnnouncementRead.objects.bulk_create",
            side_effect=RuntimeError,
        ),
        pytest.raises(RuntimeError),
    ):
        mark_all_read(user)
    item.refresh_from_db()
    assert item.read_at is None
    for _ in range(2):
        assert secure.post("/notifications/read-all/", HTTP_X_CSRFTOKEN=token).status_code == 302
    assert AnnouncementRead.objects.filter(user=user, announcement=news).count() == 1
    user.is_active = False
    user.save()
    assert secure.post("/notifications/read-all/", HTTP_X_CSRFTOKEN=token).status_code == 302


@pytest.mark.django_db(transaction=True)
def test_parallel_read_all_preserves_unique_marks(study):
    from apps.notifications.services import mark_all_read

    user = study[0][0].user
    item = message(user)
    news = announcement()
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait()
            mark_all_read(user)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: worker(), range(2)))
    assert AnnouncementRead.objects.filter(user=user, announcement=news).count() == 1
    item.refresh_from_db()
    assert item.read_at is not None
