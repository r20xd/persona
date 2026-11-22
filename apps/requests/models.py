import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Length
from django.db.models.lookups import LessThanOrEqual


class ServiceRequest(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Отправлена"
        IN_PROGRESS = "in_progress", "В работе"
        READY = "ready", "Готова"
        REJECTED = "rejected", "Отклонена"
        CANCELLED = "cancelled", "Отменена"

    class Purpose(models.TextChoices):
        PRESENTATION = "presentation", "По месту требования"
        BENEFITS = "benefits", "Для оформления льгот"
        OTHER = "other", "Другое"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.PROTECT)
    kind = models.CharField(max_length=32, default="study_certificate")
    purpose = models.CharField(max_length=24, choices=Purpose.choices)
    comment = models.TextField(blank=True, max_length=1000)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED)
    version = models.PositiveIntegerField(default=1)
    submission_key = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["student", "created_at"]),
            models.Index(fields=["status", "updated_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "submission_key"], name="request_key_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="request_version_valid"
            ),
            models.CheckConstraint(
                condition=models.Q(kind="study_certificate"), name="request_kind_valid"
            ),
            models.CheckConstraint(
                condition=models.Q(purpose__in=["presentation", "benefits", "other"]),
                name="request_purpose_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=["submitted", "in_progress", "ready", "rejected", "cancelled"]
                ),
                name="request_status_valid",
            ),
            models.CheckConstraint(
                condition=LessThanOrEqual(Length("comment"), 1000), name="request_comment_length"
            ),
        ]

    def save(self, *args, **kwargs):
        if (
            self.pk
            and type(self).objects.filter(pk=self.pk).exclude(student_id=self.student_id).exists()
        ):
            raise ValidationError("Владелец заявки неизменяем.")
        return super().save(*args, **kwargs)


class ImmutableEventQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("История доступна только для чтения.")

    def delete(self):
        raise ValidationError("История доступна только для чтения.")

    def bulk_update(self, *args, **kwargs):
        raise ValidationError("История доступна только для чтения.")

    def bulk_create(self, objs, **kwargs):
        if kwargs.get("update_conflicts"):
            raise ValidationError("История доступна только для чтения.")
        return super().bulk_create(objs, **kwargs)


class RequestEvent(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.PROTECT, related_name="events")
    actor = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    from_status = models.CharField(max_length=16, blank=True)
    to_status = models.CharField(max_length=16, choices=ServiceRequest.Status.choices)
    public_comment = models.TextField(blank=True, max_length=1000)
    version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    objects = ImmutableEventQuerySet.as_manager()

    class Meta:
        ordering = ["version"]
        constraints = [
            models.UniqueConstraint(
                fields=["request", "version"], name="request_event_version_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="request_event_version_valid"
            ),
            models.CheckConstraint(
                condition=models.Q(
                    to_status__in=["submitted", "in_progress", "ready", "rejected", "cancelled"]
                ),
                name="event_to_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    from_status__in=[
                        "",
                        "submitted",
                        "in_progress",
                        "ready",
                        "rejected",
                        "cancelled",
                    ]
                ),
                name="event_from_status_valid",
            ),
            models.CheckConstraint(
                condition=LessThanOrEqual(Length("public_comment"), 1000),
                name="event_comment_length",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(version=1, from_status="", to_status="submitted")
                    | models.Q(version__gt=1) & ~models.Q(from_status="")
                ),
                name="event_initial_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(to_status="rejected") | ~models.Q(public_comment=""),
                name="event_rejection_reason",
            ),
        ]

    def save(self, *args, **kwargs):
        if (
            not self._state.adding
            or self.pk is not None
            and type(self).objects.filter(pk=self.pk).exists()
        ):
            raise ValidationError("История доступна только для чтения.")
        kwargs["force_insert"] = True
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("История доступна только для чтения.")


class RequestMessage(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.PROTECT, related_name="messages")
    author = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    body = models.TextField(max_length=2000)
    submission_key = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [
            models.Index(fields=["request", "-created_at", "-id"], name="request_message_page_idx")
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["request", "author", "submission_key"], name="request_message_key_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(body__regex=r"\S"), name="request_message_nonblank"
            ),
            models.CheckConstraint(
                condition=LessThanOrEqual(Length("body"), 2000), name="request_message_length"
            ),
        ]
