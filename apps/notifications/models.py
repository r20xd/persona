import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    code = models.SlugField(unique=True, null=True, blank=True)
    audience_kind = models.CharField(
        max_length=7, choices=[("all", "Всем"), ("group", "Группе"), ("faculty", "Факультету")]
    )
    target_group = models.ForeignKey(
        "academics.StudyGroup", null=True, blank=True, on_delete=models.PROTECT
    )
    target_faculty = models.ForeignKey(
        "academics.Faculty", null=True, blank=True, on_delete=models.PROTECT
    )
    publish_at = models.DateTimeField(default=timezone.now, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        for value in [self.publish_at, self.expires_at]:
            if value and timezone.is_naive(value):
                raise ValidationError("Требуется время с часовым поясом.")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    audience_kind="all", target_group__isnull=True, target_faculty__isnull=True
                )
                | models.Q(
                    audience_kind="group", target_group__isnull=False, target_faculty__isnull=True
                )
                | models.Q(
                    audience_kind="faculty", target_group__isnull=True, target_faculty__isnull=False
                ),
                name="announcement_audience_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(expires_at__isnull=True)
                | models.Q(expires_at__gt=models.F("publish_at")),
                name="announcement_window_valid",
            ),
        ]


class AnnouncementRead(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["announcement", "user"], name="announcement_read_unique"
            )
        ]


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(
        max_length=8,
        choices=[
            ("schedule", "Расписание"),
            ("request", "Заявка"),
            ("deadline", "Срок"),
            ("personal", "Дедлайн"),
        ],
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    target_type = models.CharField(
        max_length=8,
        choices=[
            ("schedule", "Расписание"),
            ("request", "Заявка"),
            ("deadline", "Срок"),
            ("personal", "Дедлайн"),
        ],
    )
    target_id = models.UUIDField()
    dedupe_key = models.CharField(max_length=200)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(
                fields=["recipient", "read_at", "created_at"], name="notification_feed_idx"
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "dedupe_key"], name="notification_dedupe_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(kind__in=["schedule", "request", "deadline", "personal"]),
                name="notification_kind_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(target_type__in=["schedule", "request", "deadline", "personal"]),
                name="notification_target_valid",
            ),
        ]


class Deadline(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offering = models.ForeignKey("academics.CourseOffering", on_delete=models.PROTECT)
    assessment = models.OneToOneField(
        "grades.Assessment", null=True, blank=True, on_delete=models.PROTECT
    )
    code = models.SlugField(unique=True, null=True, blank=True)
    title = models.CharField(max_length=200)
    due_at = models.DateTimeField(db_index=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=1)

    def clean(self):
        for value in [self.due_at, self.cancelled_at]:
            if value and timezone.is_naive(value):
                raise ValidationError("Требуется время с часовым поясом.")
        if self.assessment_id and self.assessment.offering_id != self.offering_id:
            raise ValidationError("Работа должна относиться к тому же курсу.")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(revision__gte=1), name="deadline_revision_positive"
            )
        ]


class ReminderRun(models.Model):
    code = models.CharField(primary_key=True, max_length=30, default="deadlines")
    last_success_at = models.DateTimeField(null=True)


class PersonalDeadline(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    due_date = models.DateField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["due_date", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=""), name="personal_deadline_title_present"
            )
        ]
