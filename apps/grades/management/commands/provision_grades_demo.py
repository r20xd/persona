"""Only fictional fixtures; never overwrite results or passwords on repeat."""

import uuid
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.academics.demo import demo_lock
from apps.academics.models import Enrollment, Room, Teacher
from apps.grades.models import Assessment, ExamEvent, GradeResult
from apps.grades.services import create_assessment, create_exam_event, record_result
from apps.schedule.selectors import MOSCOW


class Command(BaseCommand):
    help = "Add fictional grades after provision_accounts and provision_study_demo."

    @transaction.atomic
    def handle(self, *args, **options):
        demo_lock()
        profiles = []
        for username in ["student.one", "student.two"]:
            items = list(
                Enrollment.objects.filter(
                    student__user__username=username,
                    student__user__is_active=True,
                    student__user__role="student",
                    offering__term__code="fiction-study-demo",
                )
                .select_related("offering__term", "offering__subject", "student")
                .order_by("offering__subject__code")
            )
            if len(items) != 3:
                raise CommandError("Run provision_accounts and provision_study_demo first.")
            profiles.append(items)
        teacher = Teacher.objects.get(code="fiction-belov")
        room = Room.objects.get(code="fiction-a204")
        for student_index, items in enumerate(profiles):
            for index, enrollment in enumerate(items):
                offering = enrollment.offering
                work = Assessment.objects.filter(
                    offering=offering, kind="coursework", title="Практическая работа"
                ).first()
                if work is None:
                    work = create_assessment(
                        offering=offering,
                        kind="coursework",
                        title="Практическая работа",
                        max_points=20,
                    )
                final = Assessment.objects.filter(
                    offering=offering, kind__in=["exam", "credit"]
                ).first()
                if final is None:
                    final = create_assessment(
                        offering=offering, kind=offering.control_type, title="Итоговый контроль"
                    )
                if not GradeResult.objects.filter(assessment=work, enrollment=enrollment).exists():
                    record_result(
                        assessment=work,
                        enrollment=enrollment,
                        points=[0, 16, 19][(index + student_index) % 3],
                        published_at=timezone.now() - timedelta(days=1),
                    )
                if not GradeResult.objects.filter(assessment=final, enrollment=enrollment).exists():
                    outcome = (
                        ("good" if student_index == 0 else "satisfactory")
                        if offering.control_type == "exam"
                        else ("passed" if student_index == 0 else "failed")
                    )
                    # One missing, one future, one visible result per student.
                    if index != 2:
                        record_result(
                            assessment=final,
                            enrollment=enrollment,
                            outcome=outcome,
                            published_at=timezone.now() + timedelta(days=365)
                            if index == 1
                            else timezone.now() - timedelta(days=1),
                        )
                identity = uuid.uuid5(uuid.NAMESPACE_URL, f"fiction-grades/{offering.pk}/1")
                existing_event = ExamEvent.objects.filter(pk=identity).first()
                if existing_event and existing_event.offering_id != offering.pk:
                    raise CommandError("Incompatible fictional exam ownership; unchanged.")
                if existing_event is None:
                    start = datetime.combine(
                        offering.term.ends_on - timedelta(days=7 - index),
                        time(10 + student_index * 3),
                        MOSCOW,
                    )
                    create_exam_event(
                        id=identity,
                        offering=offering,
                        teacher=teacher,
                        room=room,
                        starts_at=start,
                        ends_at=start + timedelta(hours=2),
                        status="cancelled" if index == 2 else "scheduled",
                    )
        self.stdout.write("Fictional grades/session provisioned; existing records unchanged.")
