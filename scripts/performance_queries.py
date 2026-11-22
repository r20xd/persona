"""Private child of verify_performance; emit counts/times only, never SQL or parameters."""

import json
import os
import time
import uuid
from datetime import timedelta


def audit():
    import django

    django.setup()
    from django.conf import settings
    from django.db import connection
    from django.test import Client
    from django.utils import timezone

    from apps.academics.models import CourseOffering, Enrollment, Subject
    from apps.accounts.models import User
    from apps.grades.models import Assessment, GradeResult
    from apps.notifications.models import Announcement, Notification
    from apps.requests.models import ServiceRequest
    from apps.schedule.models import Lesson
    from scripts.verify_performance import ROUTES

    assert not settings.DEBUG and connection.settings_dict["NAME"] == "performance_source"
    student = User.objects.get(username="student.one")
    operator = User.objects.get(username="operator.demo")
    client = Client(HTTP_HOST="localhost")
    output = {}

    def measure():
        result = {}
        for user, paths in [(student, list(ROUTES)), (operator, ["/operator/requests/"])]:
            client.force_login(user)
            for path in paths:
                observations = []

                def wrapper(execute, sql, params, many, context, observations=observations):
                    started = time.perf_counter()
                    try:
                        return execute(sql, params, many, context)
                    finally:
                        observations.append((time.perf_counter() - started) * 1000)

                with connection.execute_wrapper(wrapper):
                    response = client.get(path)
                    assert response.status_code == 200
                    _ = response.content
                result[path] = {
                    "queries": len(observations),
                    "db_ms": round(sum(observations), 3),
                    "slowest_query_ms": round(max(observations), 3),
                }
        return result

    def sizes():
        return {
            model._meta.model_name: model.objects.count()
            for model in [
                User,
                CourseOffering,
                Enrollment,
                Assessment,
                GradeResult,
                Lesson,
                ServiceRequest,
                Notification,
                Announcement,
            ]
        }

    output["initial"] = {"sizes": sizes(), "routes": measure()}
    profile = student.studentprofile
    offering = Enrollment.objects.filter(student=profile).first().offering
    lesson = Lesson.objects.filter(offering=offering).first()
    for index in range(40):
        subject = Subject.objects.create(
            code=f"q06-{index}", name=f"Fictional audit subject {index}"
        )
        extra = CourseOffering.objects.create(
            subject=subject, group=offering.group, term=offering.term, control_type="exam"
        )
        enrollment = Enrollment.objects.create(student=profile, offering=extra)
        assessment = Assessment.objects.create(
            offering=extra, title="Fictional audit exam", kind="exam"
        )
        GradeResult.objects.create(
            enrollment=enrollment,
            assessment=assessment,
            outcome="good",
            published_at=timezone.now(),
        )
        Lesson.objects.create(
            offering=extra,
            teacher=lesson.teacher,
            room=lesson.room,
            starts_at=lesson.starts_at,
            ends_at=lesson.ends_at,
        )
        ServiceRequest.objects.create(student=profile, submission_key=uuid.uuid4(), purpose="other")
        Notification.objects.create(
            recipient=student,
            kind="request",
            title="Fictional audit",
            body="Fictional audit",
            target_type="request",
            target_id=uuid.uuid4(),
            dedupe_key=f"q06-{index}",
        )
        Announcement.objects.create(
            title="Fictional audit",
            body="Fictional audit",
            audience_kind="all",
            publish_at=timezone.now() - timedelta(days=1),
        )
    output["expanded"] = {"sizes": sizes(), "routes": measure()}
    output["method"] = (
        "execute_wrapper DEBUG=False; full GET and materialized templates; no SQL retained"
    )
    return output


if __name__ == "__main__":
    # Not a general database tool: the parent supplies a clean environment and its owned name.
    if os.environ.get("DB_NAME") != "performance_source":
        raise SystemExit(2)
    print(json.dumps(audit()))
