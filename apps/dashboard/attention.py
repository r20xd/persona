"""Bounded current-state priorities, independent of digest receipts."""

from datetime import timedelta

from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone

from apps.academics.models import Enrollment
from apps.grades.models import GradeResult
from apps.requests.selectors import student_requests
from apps.schedule.models import LessonChange

from .digest import student

LIMIT = 6


def context(user, study):
    profile = student(user)
    now = timezone.now()
    enrolled = Enrollment.objects.filter(student=profile, student__group_id=F("offering__group_id"))
    items, total = [], 0

    def collect(query, build):
        nonlocal total
        total += query.count()
        for item in query[:LIMIT]:
            items.append(build(item))

    def card(priority, label, title, reason, url, key):
        return {
            "priority": priority,
            "action": {
                0: "Посмотреть результат",
                2: "Посмотреть изменение",
                3: "Открыть заявку",
            }[priority],
            "label": label,
            "title": title,
            "reason": reason,
            "url": url,
            "key": key,
        }

    if study:
        failures = (
            GradeResult.objects.filter(
                enrollment__in=enrolled,
                enrollment__offering__term=study["term"],
                assessment__kind__in=["exam", "credit"],
                assessment__offering_id=F("enrollment__offering_id"),
                outcome__in=["failed", "unsatisfactory"],
                published_at__lte=now,
            )
            .select_related("assessment__offering__subject")
            .order_by("published_at", "pk")
        )
        collect(
            failures,
            lambda r: card(
                0,
                "Важно",
                r.assessment.offering.subject.name,
                "Опубликованный итог: " + r.display_value,
                reverse("grades") + "?term=" + str(study["term"].pk),
                str(r.pk),
            ),
        )
    changes = (
        LessonChange.objects.filter(
            lesson__offering_id__in=enrolled.values("offering_id"),
            version=F("lesson__version"),
            created_at__lte=now,
        )
        .filter(
            Q(old_starts_at__range=(now, now + timedelta(days=7)))
            | Q(new_starts_at__range=(now, now + timedelta(days=7)))
        )
        .select_related("lesson__offering__subject")
        .order_by("new_starts_at", "pk")
    )

    def change_card(c):
        moved = c.old_starts_at != c.new_starts_at and c.new_status == "scheduled"
        item = card(
            2,
            "Пара перенесена" if moved else "Изменение занятия",
            c.lesson.offering.subject.name,
            c.reason if moved else describe_change(c),
            reverse("schedule") + "?date=" + timezone.localtime(c.new_starts_at).date().isoformat(),
            c.new_starts_at.isoformat() + str(c.pk),
        )
        if moved:
            item["move"] = c
            item["action"] = "Открыть новую дату"
        return item

    collect(changes, change_card)
    requests = (
        student_requests(user)
        .filter(status__in=["ready", "rejected"])
        .order_by("-updated_at", "pk")
    )
    collect(
        requests,
        lambda r: card(
            3,
            "Ответ деканата",
            "Справка об обучении: " + r.get_status_display(),
            "Демонстрационный статус заявки. Откройте её, чтобы узнать подробности.",
            reverse("request-detail", args=[r.pk]),
            str(r.pk),
        ),
    )
    items.sort(key=lambda item: (item["priority"], item["key"]))
    return {"items": items[:LIMIT], "total": total}


def describe_change(change):
    parts = []
    if change.old_status != change.new_status:
        parts.append(change.get_old_status_display() + " → " + change.get_new_status_display())
    if (change.old_starts_at, change.old_ends_at) != (change.new_starts_at, change.new_ends_at):
        parts.append(
            f"{timezone.localtime(change.old_starts_at):%d.%m %H:%M}–"
            f"{timezone.localtime(change.old_ends_at):%H:%M} → "
            f"{timezone.localtime(change.new_starts_at):%d.%m %H:%M}–"
            f"{timezone.localtime(change.new_ends_at):%H:%M}"
        )
    if change.old_room_id != change.new_room_id:
        parts.append("Аудитория: " + change.old_room_label + " → " + change.new_room_label)
    if change.old_teacher_id != change.new_teacher_id:
        parts.append(
            "Преподаватель: " + change.old_teacher_label + " → " + change.new_teacher_label
        )
    return ". ".join(parts + [change.reason])
