import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.http import Http404
from django.test import Client
from django.utils import timezone

from apps.accounts.models import OperatorScope, User
from apps.requests.models import RequestEvent, ServiceRequest
from apps.requests.services import RequestConflict, RequestQuota, create_request, transition_request
from tests.test_schedule import study  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.fixture
def requests_data(study):  # noqa: F811
    students, operator, _ = study
    OperatorScope.objects.create(operator=operator, group=students[0].group)
    return students, operator


def make(student, **kwargs):
    return create_request(
        actor=student.user, purpose="presentation", submission_key=uuid.uuid4(), **kwargs
    )


def change(operator, application, desired_status, **kwargs):
    return transition_request(
        actor=operator,
        request_id=application.pk,
        expected_version=application.version,
        desired_status=desired_status,
        **kwargs,
    )


def test_creation_idempotency_quota_and_forgery(client, requests_data):
    students, _ = requests_data
    client.force_login(students[0].user)
    key = uuid.uuid4()
    payload = {
        "purpose": "other",
        "comment": "  пояснение\r\nстрока  ",
        "submission_key": str(key),
        "student": students[1].pk,
        "status": "ready",
        "version": 8,
    }
    response = client.post("/requests/new/", payload)
    assert response.status_code == 302
    application = ServiceRequest.objects.get()
    assert (
        application.student == students[0]
        and application.status == "submitted"
        and application.version == 1
    )
    assert application.comment == "пояснение\nстрока"
    other_student_request = create_request(
        actor=students[1].user, purpose="other", comment="пояснение\nстрока", submission_key=key
    )
    assert other_student_request.pk != application.pk
    assert other_student_request.student == students[1]
    assert application.events.get().actor == students[0].user
    assert client.post("/requests/new/", payload).url == response.url
    payload["comment"] = "другое"
    assert client.post("/requests/new/", payload).status_code == 409
    for _ in range(29):
        make(students[0])
    # Cancelled requests still count; existing idempotent key is checked before quota.
    change(students[0].user, application, "cancelled")
    assert (
        create_request(
            actor=students[0].user, purpose="other", comment="пояснение\nстрока", submission_key=key
        ).pk
        == application.pk
    )
    assert (
        client.post("/requests/new/", {**payload, "submission_key": uuid.uuid4()}).status_code
        == 429
    )
    assert client.post("/requests/new/", {**payload, "submission_key": "bad"}).status_code == 200
    with pytest.raises(RequestQuota):
        make(students[0])
    ServiceRequest.objects.filter(student=students[0]).update(
        created_at=timezone.now() - timedelta(hours=2)
    )
    assert make(students[0])


def test_access_urls_filters_pagination_and_xss(client, requests_data):
    students, operator = requests_data
    application = make(students[0], comment='<script>alert("x")</script>')
    other = make(students[2])
    detail = f"/requests/{application.pk}/"
    assert client.get(detail).status_code == 302
    assert client.post(detail + "cancel/", {"expected_version": 1}).status_code == 302
    for student in students[1:]:
        client.force_login(student.user)
        assert client.get(detail).status_code == 404
        assert client.post(detail + "cancel/", {"expected_version": 1}).status_code == 404
        assert client.get("/operator/requests/").status_code == 403
    client.force_login(students[0].user)
    response = client.get(detail)
    assert "no-store" in response["Cache-Control"]
    assert b"&lt;script&gt;" in response.content and b"<script>alert" not in response.content
    assert client.get(detail + "cancel/").status_code == 405
    for _ in range(21):
        make(students[0])
    response = client.get("/requests/")
    assert len(response.context["items"]) == 20 and response.context["items"].paginator.count == 22
    assert len(client.get("/requests/?page=2").context["items"]) == 2
    for query in [
        "page=0",
        "page=-1",
        "page=x",
        "page=1&page=2",
        "status=bad",
        "status=ready&status=submitted",
        "student=1",
    ]:
        assert client.get("/requests/?" + query).status_code == 400
    assert client.get("/requests/?page=999").status_code == 404
    client.force_login(operator)
    assert client.get("/requests/").status_code == 403
    assert client.get("/requests/new/").status_code == 403
    assert client.get(f"/operator/requests/{other.pk}/").status_code == 404
    assert (
        client.post(
            f"/operator/requests/{other.pk}/transition/",
            {"expected_version": 1, "desired_status": "in_progress"},
        ).status_code
        == 404
    )
    assert client.get("/operator/requests/").context["items"].paginator.count == 22
    OperatorScope.objects.all().delete()
    assert client.get(f"/operator/requests/{application.pk}/").status_code == 404
    assert client.get("/operator/requests/").context["items"].paginator.count == 0


def test_transition_table_versions_and_public_history(client, requests_data):
    students, operator = requests_data
    application = make(students[0])
    with pytest.raises(RequestConflict):
        change(operator, application, "ready")
    with pytest.raises(PermissionDenied):
        change(students[1].user, application, "in_progress")
    with pytest.raises(Http404):
        change(students[1].user, application, "cancelled")
    application = change(operator, application, "in_progress", comment="Начали проверку")
    assert application.version == 2
    with pytest.raises(RequestConflict):
        transition_request(
            actor=operator, request_id=application.pk, expected_version=1, desired_status="ready"
        )
    with pytest.raises(RequestConflict):
        change(students[0].user, application, "cancelled")
    with pytest.raises(ValidationError):
        change(operator, application, "rejected")
    application = change(operator, application, "rejected", comment="Уточните назначение")
    assert list(application.events.values_list("version", flat=True)) == [1, 2, 3]
    client.force_login(students[0].user)
    assert "Уточните назначение" in client.get(f"/requests/{application.pk}/").content.decode()
    for target in ServiceRequest.Status.values:
        with pytest.raises((RequestConflict, PermissionDenied)):
            change(operator, application, target)
    application.refresh_from_db()
    assert application.status == "rejected" and application.version == 3
    ready = change(operator, change(operator, make(students[0]), "in_progress"), "ready")
    ready_html = client.get(f"/requests/{ready.pk}/").content.decode()
    assert "Заявка обработана" in ready_html
    assert ready_html.count('class="concept-notice"') == 1
    assert "Неофициальный сервис" in ready_html
    cancelled = change(students[0].user, make(students[0]), "cancelled")
    with pytest.raises(RequestConflict):
        change(operator, cancelled, "in_progress")


def test_csrf_validation_preserves_text_and_stale_response(requests_data):
    students, operator = requests_data
    secure = Client(enforce_csrf_checks=True)
    secure.force_login(students[0].user)
    response = secure.get("/requests/new/")
    assert secure.post("/requests/new/", {"purpose": "other"}).status_code == 403
    csrf = secure.cookies["csrftoken"].value
    payload = {
        "purpose": "wrong",
        "comment": "Сохранённый текст",
        "submission_key": uuid.uuid4(),
        "csrfmiddlewaretoken": csrf,
    }
    response = secure.post("/requests/new/", payload)
    assert response.status_code == 200 and "Сохранённый текст" in response.content.decode()
    application = make(students[0])
    assert (
        secure.post(f"/requests/{application.pk}/cancel/", {"expected_version": 1}).status_code
        == 403
    )
    secure.force_login(operator)
    url = f"/operator/requests/{application.pk}/transition/"
    secure.get(f"/operator/requests/{application.pk}/")
    csrf = secure.cookies["csrftoken"].value
    assert (
        secure.post(url, {"expected_version": 1, "desired_status": "in_progress"}).status_code
        == 403
    )
    payload = {"expected_version": 1, "desired_status": "in_progress", "csrfmiddlewaretoken": csrf}
    assert secure.post(url, payload).status_code == 302
    response = secure.post(url, payload)
    assert response.status_code == 409
    recovery = f"/operator/requests/{application.pk}/"
    assert f'href="{recovery}"' in response.content.decode()
    response = secure.get(recovery)
    assert response.status_code == 200
    assert response.context["form"].initial["expected_version"] == 2
    assert RequestEvent.objects.count() == 2


def test_model_constraints_immutability_and_stale_actor(requests_data):
    students, operator = requests_data
    application = make(students[0])
    for field in [
        {"status": "bad"},
        {"kind": "bad"},
        {"purpose": "bad"},
        {"version": 0},
        {"comment": "x" * 1001},
    ]:
        with pytest.raises(IntegrityError), transaction.atomic():
            ServiceRequest.objects.filter(pk=application.pk).update(**field)
    event = application.events.get()
    for action in [
        lambda: event.save(),
        lambda: event.save(force_insert=True),
        lambda: event.delete(),
        lambda: application.events.update(public_comment="bad"),
        lambda: application.events.all().delete(),
        lambda: RequestEvent(
            pk=event.pk,
            request=application,
            actor=operator,
            from_status="",
            to_status="submitted",
            version=7,
        ).save(force_insert=True),
    ]:
        with pytest.raises(ValidationError):
            action()
    with pytest.raises(IntegrityError), transaction.atomic():
        RequestEvent.objects.create(
            request=application,
            actor=operator,
            from_status="submitted",
            to_status="ready",
            version=1,
        )
    application.student = students[1]
    with pytest.raises(ValidationError):
        application.save()
    User.objects.filter(pk=operator.pk).update(is_active=False)
    with pytest.raises(PermissionDenied):
        change(operator, application, "in_progress")
    User.objects.filter(pk=students[0].user.pk).update(role="operator")
    with pytest.raises(PermissionDenied):
        make(students[0])


def test_atomic_event_failure_rolls_back(requests_data):
    students, operator = requests_data
    with patch.object(RequestEvent.objects, "create", side_effect=IntegrityError):
        with pytest.raises(IntegrityError):
            make(students[0])
    assert not ServiceRequest.objects.exists()
    application = make(students[0])
    with patch.object(RequestEvent.objects, "create", side_effect=IntegrityError):
        with pytest.raises(IntegrityError):
            change(operator, application, "in_progress")
    application.refresh_from_db()
    assert (
        application.status == "submitted"
        and application.version == 1
        and application.events.count() == 1
    )


def race(functions):
    barrier = Barrier(len(functions), timeout=10)

    def run(function):
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '10s'")
                cursor.execute("SET statement_timeout = '15s'")
            barrier.wait()
            return function()
        except (RequestConflict, RequestQuota) as error:
            return type(error).__name__
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=len(functions)) as executor:
        return list(executor.map(run, functions))


@pytest.mark.django_db(transaction=True)
def test_parallel_idempotency_and_quota(requests_data):
    students, _ = requests_data
    key = uuid.uuid4()

    def submit():
        return create_request(actor=students[0].user, purpose="other", submission_key=key).pk

    assert len(set(race([submit, submit]))) == 1
    assert ServiceRequest.objects.count() == 1 and RequestEvent.objects.count() == 1
    for _ in range(28):
        make(students[0])
    result = race([lambda: make(students[0]).pk, lambda: make(students[0]).pk])
    assert result.count("RequestQuota") == 1
    assert ServiceRequest.objects.count() == 30
    assert submit() == ServiceRequest.objects.get(submission_key=key).pk


@pytest.mark.django_db(transaction=True)
def test_parallel_transitions_and_cancel(requests_data):
    students, operator = requests_data
    application = make(students[0])
    result = race(
        [
            lambda: change(operator, application, "in_progress").status,
            lambda: change(operator, application, "in_progress").status,
        ]
    )
    assert sorted(result) == ["RequestConflict", "in_progress"]
    application.refresh_from_db()
    assert application.version == 2 and application.events.count() == 2
    application = make(students[0])
    result = race(
        [
            lambda: change(operator, application, "in_progress").status,
            lambda: change(students[0].user, application, "cancelled").status,
        ]
    )
    assert result.count("RequestConflict") == 1
    application.refresh_from_db()
    assert application.status in {"cancelled", "in_progress"} and application.version == 2
    assert application.events.count() == 2


@pytest.mark.parametrize("source", ServiceRequest.Status.values)
@pytest.mark.parametrize("target", ServiceRequest.Status.values)
def test_complete_transition_matrix(requests_data, source, target):
    students, operator = requests_data
    application = make(students[0])
    ServiceRequest.objects.filter(pk=application.pk).update(status=source)
    actor = students[0].user if target == "cancelled" else operator
    allowed = (source, target) in {
        ("submitted", "cancelled"),
        ("submitted", "in_progress"),
        ("in_progress", "ready"),
        ("in_progress", "rejected"),
    }
    if allowed:
        change(actor, application, target, comment="Публичная причина")
        application.refresh_from_db()
        assert (
            application.status == target
            and application.version == 2
            and application.events.count() == 2
        )
    else:
        with pytest.raises(RequestConflict):
            change(actor, application, target, comment="Публичная причина")
        application.refresh_from_db()
        assert (
            application.status == source
            and application.version == 1
            and application.events.count() == 1
        )


def test_insert_only_even_when_existence_check_races(requests_data):
    students, operator = requests_data
    application = make(students[0])
    event = application.events.get()
    duplicate = RequestEvent(
        pk=event.pk,
        request=application,
        actor=operator,
        from_status="submitted",
        to_status="in_progress",
        version=2,
    )
    with patch("django.db.models.query.QuerySet.exists", return_value=False):
        with pytest.raises(IntegrityError), transaction.atomic():
            duplicate.save()
    event.refresh_from_db()
    assert event.to_status == "submitted" and event.version == 1


@pytest.mark.django_db(transaction=True)
def test_additive_migration_preserves_prior_data(requests_data):
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    from apps.academics.models import Enrollment
    from apps.grades.models import Assessment, GradeResult
    from apps.schedule.models import Lesson

    students, _ = requests_data
    lesson = Lesson.objects.get()
    assessment = Assessment.objects.create(
        offering=lesson.offering, title="Вымышленная работа", kind="coursework", max_points=20
    )
    result = GradeResult.objects.create(
        assessment=assessment, enrollment=Enrollment.objects.get(student=students[0]), points=15
    )
    before = (students[0].full_name, lesson.starts_at, result.points)
    executor = MigrationExecutor(connection)
    executor.migrate([("requests", None)])
    try:
        students[0].refresh_from_db()
        lesson.refresh_from_db()
        result.refresh_from_db()
        assert (students[0].full_name, lesson.starts_at, result.points) == before
    finally:
        MigrationExecutor(connection).migrate(
            MigrationExecutor(connection).loader.graph.leaf_nodes()
        )
    students[0].refresh_from_db()
    lesson.refresh_from_db()
    result.refresh_from_db()
    assert (students[0].full_name, lesson.starts_at, result.points) == before
    assert make(students[0]).events.count() == 1


@pytest.mark.django_db(transaction=True)
def test_parallel_changed_payload_conflicts(requests_data):
    students, _ = requests_data
    key = uuid.uuid4()

    def submit(comment):
        return create_request(
            actor=students[0].user, purpose="other", comment=comment, submission_key=key
        ).pk

    result = race([lambda: submit("первое"), lambda: submit("второе")])
    assert result.count("RequestConflict") == 1
    assert ServiceRequest.objects.count() == 1 and RequestEvent.objects.count() == 1


def test_database_failure_never_shows_success(client, requests_data):
    students, _ = requests_data
    client.force_login(students[0].user)
    client.raise_request_exception = False
    with patch("apps.requests.views.create_request", side_effect=IntegrityError("internal detail")):
        response = client.post(
            "/requests/new/",
            {"purpose": "other", "submission_key": uuid.uuid4(), "comment": "пример"},
        )
    assert response.status_code == 500
    assert b"internal detail" not in response.content
    assert not ServiceRequest.objects.exists()
