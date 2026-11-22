"""Add fictional study fixtures without resetting existing lessons or accounts."""

import uuid
from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.academics.demo import demo_lock, fixture
from apps.academics.models import CourseOffering, Room, Subject, Teacher, Term
from apps.academics.services import enroll
from apps.accounts.models import StudentProfile
from apps.schedule.models import Lesson
from apps.schedule.selectors import MOSCOW
from apps.schedule.services import change_lesson, create_lesson


class Command(BaseCommand):
    help = "Provision fictional study demo after provision_accounts; existing data stays unchanged."

    def add_arguments(self, parser):
        parser.add_argument("--anchor-date", type=date.fromisoformat, default=None)

    @transaction.atomic
    def handle(self, *args, **options):
        demo_lock()
        profiles = []
        for username in ["student.one", "student.two"]:
            try:
                profiles.append(
                    StudentProfile.objects.select_related("group").get(
                        user__username=username, user__role="student", user__is_active=True
                    )
                )
            except StudentProfile.DoesNotExist as error:
                raise CommandError(
                    "Run provision_accounts first; both fictional profiles are required."
                ) from error
        anchor = options["anchor_date"] or timezone.localdate(timezone=MOSCOW)
        monday = anchor - timedelta(days=anchor.weekday())
        # A stable code intentionally means later invocations cannot shift the original fixture.
        term, _ = Term.objects.get_or_create(
            code="fiction-study-demo",
            defaults={
                "title": "Демонстрационный семестр",
                "starts_on": monday - timedelta(days=7),
                "ends_on": monday + timedelta(days=55),
            },
        )
        if (
            term.title
            not in {
                "Демонстрационный семестр",
                "Демонстрационный семестр (вымышленные данные)",
            }
            or term.starts_on.weekday() != 0
            or term.ends_on < term.starts_on + timedelta(days=62)
        ):
            raise CommandError("Incompatible fictional term; unchanged.")
        monday = term.starts_on + timedelta(days=7)

        def compatible_label(model, code, field, label, suffix):
            old = label + suffix
            return old if model.objects.filter(code=code, **{field: old}).exists() else label

        teacher, _ = fixture(
            Teacher,
            code="fiction-belov",
            defaults={
                "full_name": compatible_label(
                    Teacher, "fiction-belov", "full_name", "Лев Белозор Ветрович", " (вымышленный)"
                )
            },
        )
        room, _ = fixture(
            Room,
            code="fiction-a204",
            defaults={
                "building": compatible_label(
                    Room, "fiction-a204", "building", "Учебный корпус А", " (концепт)"
                ),
                "number": "204",
            },
        )
        other_room, _ = fixture(
            Room,
            code="fiction-b310",
            defaults={
                "building": compatible_label(
                    Room, "fiction-b310", "building", "Учебный корпус Б", " (концепт)"
                ),
                "number": "310",
            },
        )
        for index, profile in enumerate(profiles):
            for subject_index, name in enumerate(
                ["Мировая экономика", "Иностранный язык", "Анализ данных"]
            ):
                subject, _ = fixture(
                    Subject, code=f"fiction-subject-{subject_index}", defaults={"name": name}
                )
                offering, _ = fixture(
                    CourseOffering,
                    subject=subject,
                    group=profile.group,
                    term=term,
                    defaults={"control_type": "exam" if subject_index == 0 else "credit"},
                )
                enroll(student=profile, offering=offering)
                for week in range(-1, 8):
                    day = monday + timedelta(days=week * 7 + subject_index * 2)
                    starts = datetime.combine(day, time(9 + index * 2, 0), MOSCOW)
                    identity = uuid.uuid5(
                        uuid.NAMESPACE_URL, f"fiction-study-demo/{index}/{subject_index}/{week}"
                    )
                    existing = Lesson.objects.filter(pk=identity).first()
                    if existing:
                        if existing.offering_id != offering.pk:
                            raise CommandError(
                                "Incompatible fictional lesson ownership; unchanged."
                            )
                        continue
                    lesson = create_lesson(
                        id=identity,
                        offering=offering,
                        teacher=teacher,
                        room=room,
                        starts_at=starts,
                        ends_at=starts + timedelta(minutes=90),
                    )
                    if subject_index == 0 and week == 0:
                        change_lesson(
                            lesson_id=lesson.pk,
                            expected_version=1,
                            starts_at=starts + timedelta(days=7, hours=4),
                            ends_at=starts + timedelta(days=7, hours=4, minutes=90),
                            room=other_room,
                            reason="Демонстрационный перенос занятия на следующую неделю.",
                        )
                    if subject_index == 1 and week == 0:
                        change_lesson(
                            lesson_id=lesson.pk,
                            expected_version=1,
                            status=Lesson.Status.CANCELLED,
                            reason="Демонстрационная отмена: день самостоятельной работы.",
                        )
        self.stdout.write(
            f"Fictional study demo available from {monday.isoformat()}; "
            "existing data and passwords unchanged."
        )
