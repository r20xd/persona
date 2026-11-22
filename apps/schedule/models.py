import uuid
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Lesson(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "По расписанию"
        CANCELLED = "cancelled", "Отменено"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offering = models.ForeignKey("academics.CourseOffering", on_delete=models.PROTECT)
    teacher = models.ForeignKey("academics.Teacher", on_delete=models.PROTECT)
    room = models.ForeignKey("academics.Room", on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=9, choices=Status.choices, default=Status.SCHEDULED)
    version = models.PositiveIntegerField(default=1)

    def clean(self):
        if self.starts_at and self.ends_at:
            if timezone.is_naive(self.starts_at) or timezone.is_naive(self.ends_at):
                raise ValidationError("Требуется время с часовым поясом.")
            term = self.offering.term
            if not (
                term.starts_on
                <= timezone.localdate(self.starts_at, timezone=ZoneInfo("Europe/Moscow"))
                <= timezone.localdate(self.ends_at, timezone=ZoneInfo("Europe/Moscow"))
                <= term.ends_on
            ):
                raise ValidationError("Занятие должно быть в пределах семестра.")

    class Meta:
        indexes = [models.Index(fields=["offering", "starts_at"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F("starts_at")), name="lesson_times_valid"
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["scheduled", "cancelled"]),
                name="lesson_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="lesson_version_positive"
            ),
        ]


class LessonChange(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.PROTECT, related_name="changes")
    version = models.PositiveIntegerField()
    old_starts_at = models.DateTimeField()
    old_ends_at = models.DateTimeField()
    new_starts_at = models.DateTimeField()
    new_ends_at = models.DateTimeField()
    old_room = models.ForeignKey("academics.Room", on_delete=models.PROTECT, related_name="+")
    new_room = models.ForeignKey("academics.Room", on_delete=models.PROTECT, related_name="+")
    old_teacher = models.ForeignKey("academics.Teacher", on_delete=models.PROTECT, related_name="+")
    new_teacher = models.ForeignKey("academics.Teacher", on_delete=models.PROTECT, related_name="+")
    old_status = models.CharField(max_length=9, choices=Lesson.Status.choices)
    new_status = models.CharField(max_length=9, choices=Lesson.Status.choices)
    old_room_label = models.CharField(max_length=200)
    new_room_label = models.CharField(max_length=200)
    old_teacher_label = models.CharField(max_length=200)
    new_teacher_label = models.CharField(max_length=200)
    reason = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("История изменений неизменяема.")
        kwargs["force_insert"] = True
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("История изменений неизменяема.")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lesson", "version"], name="lesson_change_version_unique"
            )
        ]
        ordering = ["version"]
