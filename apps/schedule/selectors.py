from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db.models import F
from django.utils import timezone

from apps.academics.selectors import own_enrollments

from .models import Lesson, LessonChange

MOSCOW = ZoneInfo("Europe/Moscow")


def period_for(day, view):
    start = day if view == "day" else day - timedelta(days=day.weekday())
    end = start + timedelta(days=1 if view == "day" else 7)
    return start, end


def next_lesson_date(user, starting_on):
    offerings = own_enrollments(user).values("offering_id")
    starts_at = (
        Lesson.objects.filter(
            offering_id__in=offerings,
            starts_at__gte=max(datetime.combine(starting_on, time.min, MOSCOW), timezone.now()),
        )
        .exclude(status="cancelled")
        .order_by("starts_at", "id")
        .values_list("starts_at", flat=True)
        .first()
    )
    return starts_at.astimezone(MOSCOW).date() if starts_at else None


def schedule_for(user, day, view):
    # Establish authorization before applying caller-controlled date filters.
    offerings = own_enrollments(user).values("offering_id")
    start, end = period_for(day, view)
    lower = datetime.combine(start, time.min, MOSCOW)
    upper = datetime.combine(end, time.min, MOSCOW)
    visible = Lesson.objects.filter(offering_id__in=offerings)
    lessons = (
        visible.filter(starts_at__gte=lower, starts_at__lt=upper)
        .select_related("offering__subject", "teacher", "room")
        .prefetch_related("changes")
        .order_by("starts_at", "id")
    )
    moves = (
        LessonChange.objects.filter(
            lesson__in=visible, old_starts_at__gte=lower, old_starts_at__lt=upper
        )
        .exclude(old_starts_at=F("new_starts_at"))
        .select_related("lesson__offering__subject")
        .order_by("old_starts_at", "lesson_id", "version")
    )
    return lessons, moves
