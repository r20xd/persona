"""Append future lessons without moving existing lessons or their history."""

import uuid
from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.academics.demo import demo_lock
from apps.academics.models import CourseOffering, Room, Teacher, Term
from apps.accounts.models import StudentProfile
from apps.schedule.models import Lesson
from apps.schedule.selectors import MOSCOW
from apps.schedule.services import create_lesson


class Command(BaseCommand):
    help = "Add missing future fictional lessons for at least six weeks; never reset existing data."

    def add_arguments(self, parser):
        parser.add_argument("--anchor-date", type=date.fromisoformat, default=None)
        parser.add_argument(
            "--through-date",
            type=date.fromisoformat,
            default=None,
            help=(
                "Fill missing demo days through this date inclusively; "
                "conflicting slots are skipped."
            ),
        )

    @transaction.atomic
    def handle(self, **options):
        demo_lock()
        try:
            term = Term.objects.select_for_update().get(code="fiction-study-demo")
            teacher = Teacher.objects.get(code="fiction-belov")
            room = Room.objects.get(code="fiction-a204")
        except (Term.DoesNotExist, Teacher.DoesNotExist, Room.DoesNotExist) as error:
            raise CommandError("Run seed_demo first.") from error
        anchor = options["anchor_date"] or timezone.localdate(timezone=MOSCOW)
        through = options["through_date"]
        if through is not None and through < anchor:
            raise CommandError("--through-date must be on or after --anchor-date.")
        # Anchor controls coverage, never the system clock or original fixture identity.
        now = timezone.now()
        today = timezone.localdate(now, timezone=MOSCOW)
        monday = term.starts_on + timedelta(days=7)
        last = max(anchor, today) + timedelta(days=48)
        if through is None and term.ends_on < last:
            term.ends_on = last
            term.save(update_fields=["ends_on"])
        added = 0
        for index, username in enumerate(["student.one", "student.two"]):
            try:
                profile = StudentProfile.objects.select_related("user", "group").get(
                    user__username=username, user__role="student", user__is_active=True
                )
            except StudentProfile.DoesNotExist as error:
                raise CommandError("Active fictional student profiles are required.") from error
            if (
                profile.group.code != ["МИ-201", "МИ-302"][index]
                or profile.user.is_staff
                or profile.user.is_superuser
            ):
                raise CommandError("Incompatible fictional student profile; unchanged.")
            if through is not None:
                added += self.fill_range(profile, index, term, teacher, room, anchor, through, now)
                continue
            for subject_index in range(3):
                try:
                    offering = CourseOffering.objects.get(
                        term=term,
                        group=profile.group,
                        subject__code=f"fiction-subject-{subject_index}",
                    )
                except CourseOffering.DoesNotExist as error:
                    raise CommandError(
                        "Incomplete fictional study fixtures; run seed_demo."
                    ) from error
                for week in range(-1, (last - monday).days // 7 + 1):
                    day = monday + timedelta(days=week * 7 + subject_index * 2)
                    if day < today or day > last:
                        continue
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
                    starts = datetime.combine(day, time(9 + index * 2), MOSCOW)
                    if starts <= now:
                        continue
                    create_lesson(
                        id=identity,
                        offering=offering,
                        teacher=teacher,
                        room=room,
                        starts_at=starts,
                        ends_at=starts + timedelta(minutes=90),
                    )
                    added += 1
        self.stdout.write(f"Added {added} future fictional lessons; existing events unchanged.")

    def fill_range(self, profile, index, term, teacher, room, anchor, through, now):
        offerings = list(
            CourseOffering.objects.filter(
                term=term,
                group=profile.group,
                subject__code__in=[f"fiction-subject-{number}" for number in range(3)],
                enrollment__student=profile,
            ).order_by("subject__code")
        )
        if len(offerings) != 3:
            raise CommandError("Incomplete fictional study enrollments; run seed_demo.")
        added = 0
        for offset in range((through - anchor).days + 1):
            day = anchor + timedelta(days=offset)
            if day.weekday() < 5 or (day == through and day.weekday() == 5):
                starts = datetime.combine(day, time(9 + index * 2), MOSCOW)
                if starts <= now:
                    continue
                identity = uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"fiction-study-demo/supplement/{profile.group.code}/{day.isoformat()}",
                )
                existing = Lesson.objects.filter(pk=identity).first()
                if existing and existing.offering_id not in {item.pk for item in offerings}:
                    raise CommandError("Incompatible fictional lesson ownership; unchanged.")
                if existing:
                    continue
                ends = starts + timedelta(minutes=90)
                day_start = datetime.combine(day, time.min, MOSCOW)
                day_end = day_start + timedelta(days=1)
                # Include cancellations and old locations of moved lessons in occupied days.
                occupied = (
                    Lesson.objects.filter(offering__group=profile.group)
                    .filter(
                        Q(starts_at__gte=day_start, starts_at__lt=day_end)
                        | Q(
                            changes__old_starts_at__gte=day_start,
                            changes__old_starts_at__lt=day_end,
                        )
                    )
                    .exists()
                )
                if occupied:
                    continue
                conflict = (
                    Lesson.objects.filter(
                        status=Lesson.Status.SCHEDULED, starts_at__lt=ends, ends_at__gt=starts
                    )
                    .filter(Q(offering__group=profile.group) | Q(teacher=teacher) | Q(room=room))
                    .exists()
                )
                if not conflict:
                    if day < term.starts_on:
                        raise CommandError("Requested date precedes the fictional study term.")
                    if day > term.ends_on:
                        term.ends_on = day
                        term.save(update_fields=["ends_on"])
                    create_lesson(
                        id=identity,
                        offering=offerings[(day - anchor).days % len(offerings)],
                        teacher=teacher,
                        room=room,
                        starts_at=starts,
                        ends_at=ends,
                    )
                    added += 1
        return added
