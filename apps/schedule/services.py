"""Trusted internal/CLI boundary. No student or operator write HTTP endpoints exist.

All schedule mutations must use these services; ORM bulk updates bypass validation.
Notifications are created in the same transaction as each change.
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Lesson, LessonChange


class StaleLessonVersion(Exception):
    pass


@transaction.atomic
def create_lesson(**fields):
    lesson = Lesson(**fields)
    lesson.clean()
    lesson.full_clean()
    lesson.save()
    return lesson


@transaction.atomic
def change_lesson(*, lesson_id, expected_version, reason, **changes):
    allowed = {"starts_at", "ends_at", "room", "teacher", "status"}
    if not changes or set(changes) - allowed or not reason.strip():
        raise ValidationError("Укажите изменение и причину.")
    lesson = Lesson.objects.select_for_update().select_related("offering__term").get(pk=lesson_id)
    if lesson.version != expected_version:
        raise StaleLessonVersion("Занятие уже изменено.")
    before = {name: getattr(lesson, name) for name in allowed}
    labels = {
        "old_room_label": f"{lesson.room.building} · {lesson.room.number}",
        "old_teacher_label": lesson.teacher.full_name,
    }
    for name, value in changes.items():
        setattr(lesson, name, value)
    if all(getattr(lesson, name) == value for name, value in before.items()):
        raise ValidationError("Нет изменений.")
    lesson.version += 1
    lesson.clean()
    lesson.full_clean()
    history = {f"old_{name}": value for name, value in before.items()}
    history.update({f"new_{name}": getattr(lesson, name) for name in allowed})
    labels.update(
        new_room_label=f"{lesson.room.building} · {lesson.room.number}",
        new_teacher_label=lesson.teacher.full_name,
    )
    event = LessonChange(lesson=lesson, version=lesson.version, reason=reason, **history, **labels)
    event.full_clean()
    lesson.save()
    event.save()
    from apps.notifications.services import schedule_notifications

    schedule_notifications(lesson)
    return lesson
