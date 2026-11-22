"""Append a dated presentation window; never reset existing student activity."""

import uuid
from datetime import date, datetime, time, timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.academics.demo import demo_lock
from apps.academics.models import CourseOffering, Enrollment, Room, Teacher, Term
from apps.accounts.models import StudentProfile
from apps.grades.models import Assessment, ExamEvent, GradeResult
from apps.grades.services import create_exam_event, record_result
from apps.notifications.models import Announcement
from apps.schedule.models import Lesson
from apps.schedule.selectors import MOSCOW
from apps.schedule.services import change_lesson, create_lesson


def identity(anchor, suffix):
    return uuid.uuid5(uuid.NAMESPACE_URL, f"fiction-window/{anchor.isoformat()}/{suffix}")


def check_owner(item, field, expected):
    if item is not None and getattr(item, field) != expected:
        raise CommandError("Incompatible fictional window ownership; unchanged.")


class Command(BaseCommand):
    help = "Prepare a dated fictional presentation window without resetting existing data."

    def add_arguments(self, parser):
        parser.add_argument("--anchor-date", type=date.fromisoformat, default=None)

    @transaction.atomic
    def handle(self, **options):
        demo_lock()
        anchor = options["anchor_date"] or timezone.localdate(timezone=MOSCOW)
        if anchor < timezone.localdate(timezone=MOSCOW):
            raise CommandError("A new presentation window must start today or later.")
        try:
            term = Term.objects.select_for_update().get(code="fiction-study-demo")
            teacher = Teacher.objects.get(code="fiction-belov")
            room = Room.objects.get(code="fiction-a204")
            moved_room = Room.objects.get(code="fiction-b310")
            profiles = []
            for index, username in enumerate(["student.one", "student.two"]):
                profile = StudentProfile.objects.select_related("user", "group").get(
                    user__username=username, user__is_active=True, user__role="student"
                )
                if (
                    profile.group.code != ["МИ-201", "МИ-302"][index]
                    or profile.user.is_staff
                    or profile.user.is_superuser
                ):
                    raise CommandError("Incompatible fictional student profile; unchanged.")
                items = list(
                    Enrollment.objects.filter(
                        student=profile,
                        offering__term=term,
                        offering__group=profile.group,
                        offering__subject__code__in=[f"fiction-subject-{n}" for n in range(3)],
                    )
                    .select_related("offering")
                    .order_by("offering__subject__code")
                )
                if len(items) != 3 or [e.offering.control_type for e in items] != [
                    "exam",
                    "credit",
                    "credit",
                ]:
                    raise CommandError("Incomplete fictional enrollments; run seed_demo first.")
                profiles.append((profile, items))
        except (
            Term.DoesNotExist,
            Teacher.DoesNotExist,
            Room.DoesNotExist,
            StudentProfile.DoesNotExist,
        ) as error:
            raise CommandError("Run seed_demo first.") from error
        call_command("extend_demo_schedule", anchor_date=anchor, stdout=self.stdout)

        def moment(days, hour=16):
            return datetime.combine(anchor + timedelta(days=days), time(hour), MOSCOW)

        for index, (profile, items) in enumerate(profiles):
            offering = items[0].offering
            code = f"demo-window-{anchor.isoformat()}-{index}"
            announcement = Announcement.objects.filter(code=code).first()
            check_owner(announcement, "target_group_id", profile.group_id)
            if announcement and announcement.audience_kind != "group":
                raise CommandError("Incompatible fictional announcement audience; unchanged.")
            if announcement is None:
                announcement = Announcement(
                    code=code,
                    title="Подготовка к учебной консультации",
                    body="Подготовьте вопросы по учёбе. Приходите в корпус А, аудиторию 204. "
                    "Учебная консультация относится к демонстрационному периоду.",
                    audience_kind="group",
                    target_group=profile.group,
                    publish_at=moment(0, 0),
                    expires_at=moment(11),
                )
                announcement.full_clean()
                announcement.save()
            if index == 0:
                lesson_id = identity(anchor, "moved-lesson")
                lesson = Lesson.objects.filter(pk=lesson_id).first()
                check_owner(lesson, "offering_id", offering.pk)
                if lesson is None:
                    create_lesson(
                        id=lesson_id,
                        offering=offering,
                        teacher=teacher,
                        room=room,
                        starts_at=moment(4),
                        ends_at=moment(4) + timedelta(minutes=90),
                    )
                    change_lesson(
                        lesson_id=lesson_id,
                        expected_version=1,
                        reason="Демонстрационная консультация перенесена; новая аудитория.",
                        starts_at=moment(8),
                        ends_at=moment(8) + timedelta(minutes=90),
                        room=moved_room,
                    )
            visible_credit = GradeResult.objects.filter(
                enrollment__student=profile,
                enrollment__offering__term=term,
                assessment__kind="credit",
                published_at__lte=moment(0, 0),
            ).exists()
            if not visible_credit:
                for enrollment in items:
                    CourseOffering.objects.select_for_update().get(pk=enrollment.offering_id)
                    assessment = Assessment.objects.filter(
                        offering=enrollment.offering, kind="credit"
                    ).first()
                    if (
                        assessment
                        and not GradeResult.objects.filter(
                            assessment=assessment, enrollment=enrollment
                        ).exists()
                    ):
                        record_result(
                            assessment=assessment,
                            enrollment=enrollment,
                            outcome="passed",
                            published_at=moment(0, 0),
                        )
                        break
            exam_id = identity(anchor, f"exam/{index}")
            exam_offering = items[0].offering
            CourseOffering.objects.select_for_update().get(pk=exam_offering.pk)
            event = ExamEvent.objects.filter(pk=exam_id).first()
            check_owner(event, "offering_id", exam_offering.pk)
            if (
                event is None
                and not ExamEvent.objects.filter(
                    offering_id__in=[e.offering_id for e in items],
                    status="scheduled",
                    starts_at__gte=moment(8, 0),
                    starts_at__lte=moment(14, 23),
                ).exists()
            ):
                attempt = (
                    ExamEvent.objects.filter(offering=exam_offering).aggregate(last=Max("attempt"))[
                        "last"
                    ]
                    or 0
                ) + 1
                create_exam_event(
                    id=exam_id,
                    offering=exam_offering,
                    attempt=attempt,
                    starts_at=moment(12, 10 + index * 3),
                    ends_at=moment(12, 12 + index * 3),
                    teacher=teacher,
                    room=room,
                )
        self.stdout.write("Fictional presentation window prepared; existing activity preserved.")
