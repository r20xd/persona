from datetime import datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.academics.models import CourseOffering, Enrollment, Term
from apps.academics.services import enroll
from apps.grades.models import Assessment, ExamEvent, GradeResult
from apps.grades.selectors import study_context
from apps.grades.services import create_assessment, create_exam_event, record_result
from apps.schedule.selectors import MOSCOW
from tests.test_schedule import study  # noqa: F401, F811

pytestmark = pytest.mark.django_db


@pytest.fixture
def grades(study):  # noqa: F811
    students, operator, lesson = study
    enrollment = Enrollment.objects.get(student=students[0])
    work = create_assessment(
        offering=lesson.offering, title="Практика", kind="coursework", max_points=20
    )
    final = create_assessment(offering=lesson.offering, title="Экзамен", kind="exam")
    return students, operator, lesson, enrollment, work, final


def test_validation_values_and_relations(grades):
    students, _, lesson, enrollment, work, final = grades
    for maximum in [None, 0, -1]:
        with pytest.raises(ValidationError):
            create_assessment(
                offering=lesson.offering, title="x", kind="coursework", max_points=maximum
            )
        with pytest.raises(IntegrityError), transaction.atomic():
            Assessment.objects.create(
                offering=lesson.offering, title="x", kind="coursework", max_points=maximum
            )
    for fields in [
        {"points": -1},
        {"points": 21},
        {"points": 1, "outcome": "passed"},
        {"outcome": "passed"},
    ]:
        with pytest.raises(ValidationError):
            record_result(assessment=work, enrollment=enrollment, **fields)
    for points in [0, 20]:
        assert record_result(assessment=work, enrollment=enrollment, points=points).points == points
    for fields in [{"points": 1}, {"outcome": "passed"}, {"outcome": "failed"}]:
        with pytest.raises(ValidationError):
            record_result(assessment=final, enrollment=enrollment, **fields)
    result = record_result(assessment=final, enrollment=enrollment, outcome="excellent")
    assert result.outcome == "excellent"
    with pytest.raises(ValidationError):
        create_assessment(offering=lesson.offering, title="bad", kind="credit")
    with pytest.raises(ValidationError):
        create_assessment(offering=lesson.offering, title="duplicate", kind="exam")
    other_offering = CourseOffering.objects.create(
        subject=lesson.offering.subject,
        group=students[2].group,
        term=lesson.offering.term,
        control_type="exam",
    )
    other_enrollment = enroll(student=students[2], offering=other_offering)
    with pytest.raises(ValidationError):
        record_result(assessment=final, enrollment=other_enrollment, outcome="good")
    for fields in [
        {"points": 1, "outcome": "excellent"},
        {"points": None, "outcome": ""},
        {"points": -1, "outcome": ""},
    ]:
        with pytest.raises(IntegrityError), transaction.atomic():
            GradeResult.objects.filter(pk=result.pk).update(**fields)


def test_visibility_counts_and_filtering(client, grades):
    students, operator, lesson, enrollment, work, final = grades
    now = timezone.now()
    record_result(
        assessment=work, enrollment=enrollment, points=0, published_at=now - timedelta(days=1)
    )
    hidden = record_result(
        assessment=final,
        enrollment=enrollment,
        outcome="unsatisfactory",
        published_at=now + timedelta(days=1),
    )
    assert study_context(students[0].user)["counts"] == {"success": 0, "failure": 0, "awaiting": 1}
    assert client.get("/grades/").status_code == 302
    for url in ["/grades/", "/session/"]:
        client.force_login(students[0].user)
        response = client.get(url)
        assert response.status_code == 200 and "no-store" in response["Cache-Control"]
        text = response.content.decode()
        assert "Неудовлетворительно" not in text and str(hidden.pk) not in text
        assert hidden.published_at.isoformat() not in text
        if url == "/grades/":
            assert "0 / 20 баллов" in " ".join(text.split())
        assert client.post(url).status_code == 405
        for query in ["student=1", "term=1&term=1", "offering=1"]:
            assert client.get(url + "?" + query).status_code == 400
        for term in ["0", "bad", "", "9999999999999999999999999999999"]:
            assert client.get(url + "?term=" + term).status_code == 404
        assert client.get(f"{url}{hidden.pk}/").status_code == 404
        for student in students[1:]:
            client.force_login(student.user)
            other = client.get(url)
            assert "Доступная дисциплина" not in other.content.decode()
            assert client.get(f"{url}?term={lesson.offering.term_id}").status_code == 404
        client.force_login(operator)
        assert client.get(url).status_code == 403
    for outcome, state in [("unsatisfactory", "failure"), ("good", "success")]:
        record_result(assessment=final, enrollment=enrollment, outcome=outcome, published_at=now)
        assert study_context(students[0].user)["counts"][state] == 1
    record_result(assessment=final, enrollment=enrollment, published_at=None)
    assert study_context(students[0].user)["counts"]["awaiting"] == 1


def test_own_terms_and_same_group_personal_results(client, grades):
    students, _, lesson, enrollment, _, final = grades
    other = enroll(student=students[1], offering=lesson.offering)
    record_result(
        assessment=final, enrollment=enrollment, outcome="excellent", published_at=timezone.now()
    )
    record_result(
        assessment=final, enrollment=other, outcome="unsatisfactory", published_at=timezone.now()
    )
    client.force_login(students[1].user)
    text = client.get("/grades/").content.decode()
    assert "Неудовлетворительно" in text and "Отлично" not in text
    term = Term.objects.create(
        code="old",
        title="Другой семестр",
        starts_on=lesson.offering.term.starts_on,
        ends_on=lesson.offering.term.ends_on,
    )
    offering = CourseOffering.objects.create(
        subject=lesson.offering.subject, group=students[0].group, term=term, control_type="credit"
    )
    enroll(student=students[0], offering=offering)
    assert client.get(f"/grades/?term={term.pk}").status_code == 404
    client.force_login(students[0].user)
    assert client.get(f"/grades/?term={term.pk}").status_code == 200
    assert client.get(f"/session/?term={term.pk}").status_code == 200


def test_session_boundaries_and_cancel(client, grades):
    students, _, lesson, _, _, _ = grades
    fields = dict(
        offering=lesson.offering,
        teacher=lesson.teacher,
        room=lesson.room,
        starts_at=lesson.starts_at,
        ends_at=lesson.ends_at,
    )
    event = create_exam_event(**fields, status="cancelled")
    client.force_login(students[0].user)
    text = client.get("/session/").content.decode()
    assert "Отменено" in text and lesson.teacher.full_name in text and lesson.room.number in text
    for changes in [
        {"attempt": 0},
        {"starts_at": datetime(2026, 11, 2, 9)},
        {"ends_at": lesson.starts_at},
        {
            "starts_at": datetime(2027, 1, 1, tzinfo=MOSCOW),
            "ends_at": datetime(2027, 1, 2, tzinfo=MOSCOW),
        },
        {"status": "invalid"},
        {},
    ]:
        with pytest.raises(ValidationError):
            create_exam_event(**{**fields, **changes})
    for changes in [{"attempt": 0}, {"status": "bad"}, {"ends_at": event.starts_at}]:
        with pytest.raises(IntegrityError), transaction.atomic():
            ExamEvent.objects.filter(pk=event.pk).update(**changes)
    assert create_exam_event(**fields, attempt=2).attempt == 2


def test_demo_repeat_preserves(monkeypatch):
    with pytest.raises(CommandError):
        call_command("provision_grades_demo")
    for key in ["DEMO_STUDENT_ONE_PASSWORD", "DEMO_STUDENT_TWO_PASSWORD", "DEMO_OPERATOR_PASSWORD"]:
        monkeypatch.setenv(key, "Fictional-testing-9568!")
    call_command("provision_accounts")
    call_command("provision_study_demo")
    call_command("provision_grades_demo")
    assert (
        Assessment.objects.count() == 12
        and GradeResult.objects.count() == 10
        and ExamEvent.objects.count() == 6
    )
    first = GradeResult.objects.filter(points__isnull=False).first()
    record_result(assessment=first.assessment, enrollment=first.enrollment, points=7)
    snapshot = list(GradeResult.objects.order_by("pk").values())
    call_command("provision_grades_demo")
    assert snapshot == list(GradeResult.objects.order_by("pk").values())


def test_credit_http_and_counts(client, grades):
    students, _, lesson, _, _, _ = grades
    # A separate semester avoids mixing the exam and credit summary.
    term = Term.objects.create(
        code="credit-term",
        title="Зачётный семестр",
        starts_on=lesson.offering.term.starts_on,
        ends_on=lesson.offering.term.ends_on,
    )
    offering = CourseOffering.objects.create(
        subject=lesson.offering.subject, group=students[0].group, term=term, control_type="credit"
    )
    enrollment = enroll(student=students[0], offering=offering)
    assessment = create_assessment(offering=offering, title="Зачёт", kind="credit")
    with pytest.raises(ValidationError):
        record_result(assessment=assessment, enrollment=enrollment, outcome="excellent")
    client.force_login(students[0].user)
    for outcome, label, state in [
        ("passed", "Зачтено", "success"),
        ("failed", "Не зачтено", "failure"),
    ]:
        record_result(
            assessment=assessment,
            enrollment=enrollment,
            outcome=outcome,
            published_at=timezone.now(),
        )
        response = client.get(f"/grades/?term={term.pk}")
        assert label in response.content.decode()
        assert response.context["counts"][state] == 1
        assert sum(response.context["counts"].values()) == 1


def test_hidden_points_and_missing_are_identical(client, grades):
    students, _, _, enrollment, work, _ = grades
    client.force_login(students[0].user)
    before = client.get("/grades/")
    expected_counts = before.context["counts"]
    for published_at in [None, timezone.now() + timedelta(days=5)]:
        record_result(assessment=work, enrollment=enrollment, points=17, published_at=published_at)
        response = client.get("/grades/")
        assert "17 / 20" not in " ".join(response.content.decode().split())
        assert response.context["counts"] == expected_counts
        assert response.context["rows"][0]["work"][0]["result"] is None


@pytest.mark.parametrize("path", ["/schedule/session/", "/session/"])
def test_session_relocation_contract(client, grades, path):
    from django.urls import reverse

    students, _, lesson, _, _, _ = grades
    assert reverse("session") == "/schedule/session/"
    assert client.get(path).status_code == 302
    client.force_login(students[0].user)
    response = client.get(path)
    assert response.status_code == 200
    assert "schedule/session.html" in [t.name for t in response.templates]
    assert client.get(path + "?term=invalid").status_code == 404
    assert client.get(path + "?term=1&term=2").status_code == 400
    assert client.post(path).status_code == 405
    term = Term.objects.create(
        code="hidden-session",
        title="Чужой период",
        starts_on=lesson.offering.term.starts_on,
        ends_on=lesson.offering.term.ends_on,
    )
    assert client.get(f"{path}?term={term.pk}").status_code == 404
    grades_response = client.get("/grades/")
    assert b"study-tabs" not in grades_response.content
    assert b"exam-card" not in grades_response.content
