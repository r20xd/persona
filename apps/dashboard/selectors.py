"""Read-only composition of the same scoped sources used by student sections."""

from datetime import timedelta

from django.db.models import F, Q
from django.utils import timezone

from apps.academics.selectors import own_enrollments
from apps.accounts.selectors import own_profile
from apps.grades.models import ExamEvent
from apps.grades.selectors import study_context
from apps.schedule.models import Lesson, LessonChange
from apps.schedule.selectors import MOSCOW


def dashboard_context(user):
    profile = own_profile(user)
    now = timezone.now()
    today = timezone.localdate(now, timezone=MOSCOW)
    enrollments = own_enrollments(user)
    offerings = enrollments.values("offering_id")
    study = study_context(user, now=now)
    if study["term"] is None:
        study = None
    lessons = Lesson.objects.filter(offering_id__in=offerings)
    lesson = (
        lessons.filter(status="scheduled", ends_at__gt=now)
        .select_related("offering__subject", "teacher", "room")
        .order_by("starts_at", "pk")
        .first()
    )
    exam = (
        ExamEvent.objects.filter(offering_id__in=offerings, status="scheduled", ends_at__gt=now)
        .select_related("offering__subject", "teacher", "room")
        .order_by("starts_at", "pk")
        .first()
    )
    nearest = min(
        [event for event in [lesson, exam] if event],
        key=lambda event: event.starts_at,
        default=None,
    )
    changes = (
        LessonChange.objects.filter(lesson__in=lessons, version=F("lesson__version"))
        .filter(
            Q(old_starts_at__gte=now, old_starts_at__lte=now + timedelta(days=7))
            | Q(new_starts_at__gte=now, new_starts_at__lte=now + timedelta(days=7))
        )
        .select_related("lesson__offering__subject")
        .order_by("-created_at", "-pk")[:3]
    )
    return {
        "profile": profile,
        "today": today,
        "nearest": nearest,
        "nearest_exam": nearest is not None and nearest is exam,
        "changes": list(changes),
        "study": study,
    }
