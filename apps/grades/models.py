import uuid
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Assessment(models.Model):
    class Kind(models.TextChoices):
        COURSEWORK = "coursework", "Текущая работа"
        EXAM = "exam", "Экзамен"
        CREDIT = "credit", "Зачёт"

    offering = models.ForeignKey("academics.CourseOffering", on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    max_points = models.PositiveIntegerField(null=True, blank=True)

    def clean(self):
        if self.kind == self.Kind.COURSEWORK and (self.max_points is None or self.max_points <= 0):
            raise ValidationError("Укажите положительный максимум текущей работы.")
        if self.kind != self.Kind.COURSEWORK and self.offering_id:
            if self.kind != self.offering.control_type:
                raise ValidationError("Форма контроля должна соответствовать курсу.")
        if self.kind != self.Kind.COURSEWORK and self.max_points is not None:
            raise ValidationError("Баллы предусмотрены только для текущих работ.")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kind__in=["coursework", "exam", "credit"]),
                name="assessment_kind_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(kind__in=["exam", "credit"], max_points__isnull=True)
                | models.Q(kind="coursework", max_points__isnull=False, max_points__gt=0),
                name="assessment_max_valid",
            ),
            models.UniqueConstraint(
                fields=["offering"],
                condition=models.Q(kind__in=["exam", "credit"]),
                name="assessment_one_final",
            ),
        ]


class GradeResult(models.Model):
    class Outcome(models.TextChoices):
        EXCELLENT = "excellent", "Отлично"
        GOOD = "good", "Хорошо"
        SATISFACTORY = "satisfactory", "Удовлетворительно"
        UNSATISFACTORY = "unsatisfactory", "Неудовлетворительно"
        PASSED = "passed", "Зачтено"
        FAILED = "failed", "Не зачтено"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.PROTECT)
    enrollment = models.ForeignKey("academics.Enrollment", on_delete=models.PROTECT)
    points = models.PositiveIntegerField(null=True, blank=True)
    outcome = models.CharField(max_length=14, choices=Outcome.choices, blank=True, default="")
    published_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.published_at and timezone.is_naive(self.published_at):
            raise ValidationError("Требуется время публикации с часовым поясом.")
        if not self.assessment_id or not self.enrollment_id:
            return
        assessment = self.assessment
        if assessment.offering_id != self.enrollment.offering_id:
            raise ValidationError("Работа и запись студента должны относиться к одному курсу.")
        if self.enrollment.student.group_id != self.enrollment.offering.group_id:
            raise ValidationError("Некорректная запись на курс.")
        if assessment.kind == Assessment.Kind.COURSEWORK:
            if self.points is None or self.outcome:
                raise ValidationError("Для текущей работы укажите только баллы.")
            if assessment.max_points is not None and self.points > assessment.max_points:
                raise ValidationError("Баллы превышают максимум работы.")
        else:
            valid = (
                {"passed", "failed"}
                if assessment.kind == "credit"
                else {"excellent", "good", "satisfactory", "unsatisfactory"}
            )
            if self.points is not None or self.outcome not in valid:
                raise ValidationError("Результат не соответствует форме контроля.")
            if assessment.kind != assessment.offering.control_type:
                raise ValidationError("Форма контроля не соответствует курсу.")

    @property
    def display_value(self):
        score = {"excellent": 5, "good": 4, "satisfactory": 3, "unsatisfactory": 2}.get(
            self.outcome
        )
        return f"{score} · {self.get_outcome_display()}" if score else self.get_outcome_display()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "enrollment"], name="grade_result_unique"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(points__isnull=False, points__gte=0, outcome="")
                    | models.Q(
                        points__isnull=True,
                        outcome__in=[
                            "excellent",
                            "good",
                            "satisfactory",
                            "unsatisfactory",
                            "passed",
                            "failed",
                        ],
                    )
                ),
                name="grade_value_exclusive",
            ),
        ]


class ExamEvent(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "По расписанию"
        CANCELLED = "cancelled", "Отменено"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offering = models.ForeignKey("academics.CourseOffering", on_delete=models.PROTECT)
    attempt = models.PositiveIntegerField(default=1)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    teacher = models.ForeignKey("academics.Teacher", on_delete=models.PROTECT)
    room = models.ForeignKey("academics.Room", on_delete=models.PROTECT)
    status = models.CharField(max_length=9, choices=Status.choices, default=Status.SCHEDULED)

    def clean(self):
        if self.starts_at and self.ends_at:
            if timezone.is_naive(self.starts_at) or timezone.is_naive(self.ends_at):
                raise ValidationError("Требуется время с часовым поясом.")
            if self.offering_id:
                term = self.offering.term
                if not (
                    term.starts_on
                    <= timezone.localdate(self.starts_at, timezone=ZoneInfo("Europe/Moscow"))
                    <= timezone.localdate(self.ends_at, timezone=ZoneInfo("Europe/Moscow"))
                    <= term.ends_on
                ):
                    raise ValidationError("Событие должно быть в пределах семестра.")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["offering", "attempt"], name="exam_attempt_unique"),
            models.CheckConstraint(
                condition=models.Q(attempt__gte=1), name="exam_attempt_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F("starts_at")), name="exam_times_valid"
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["scheduled", "cancelled"]), name="exam_status_valid"
            ),
        ]
