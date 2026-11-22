from django.conf import settings
from django.db import models


class DigestState(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)


class DigestReceipt(models.Model):
    class Kind(models.TextChoices):
        GRADE = "grade", "Оценка"
        SCHEDULE = "schedule", "Занятие"
        REQUEST = "request", "Заявка"

    state = models.ForeignKey(DigestState, on_delete=models.CASCADE)
    kind = models.CharField(max_length=8, choices=Kind.choices)
    source_key = models.CharField(max_length=64)
    event_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["state", "kind", "source_key", "event_at"], name="digest_receipt_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(kind__in=["grade", "schedule", "request"]),
                name="digest_kind_valid",
            ),
        ]
