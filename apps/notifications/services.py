import uuid
from itertools import islice
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.academics.models import Enrollment
from apps.accounts.models import OperatorScope, User

from .models import (
    Announcement,
    AnnouncementRead,
    Deadline,
    Notification,
    PersonalDeadline,
    ReminderRun,
)
from .selectors import announcements, notifications, personal_deadlines


@transaction.atomic
def publish_announcement(user, *, group, title, body, submission_key):
    from django.core.exceptions import PermissionDenied

    from .selectors import announcement_operator

    user = announcement_operator(user)
    # Serialize publications for this actor and retain role/scope until commit.
    locked_user = User.objects.select_for_update().get(pk=user.pk)
    if not locked_user.is_active or locked_user.role != User.Role.OPERATOR:
        raise PermissionDenied
    if (
        not OperatorScope.objects.select_for_update()
        .filter(operator=locked_user, group=group)
        .exists()
    ):
        raise PermissionDenied
    key = uuid.UUID(str(submission_key))
    code = "op-" + uuid.uuid5(uuid.NAMESPACE_URL, f"announcement:{user.pk}:{key}").hex
    existing = Announcement.objects.filter(code=code).first()
    if existing:
        if (existing.target_group_id, existing.title, existing.body) != (
            group.pk,
            title.strip(),
            body.strip(),
        ):
            raise ValidationError(
                "Эта форма уже опубликована с другим содержимым. "
                "Для нового объявления откройте новую форму."
            )
        return existing
    item = Announcement(
        title=title.strip(),
        body=body.strip(),
        code=code,
        audience_kind="group",
        target_group=group,
    )
    if not item.title or not item.body or len(item.body) > 10000:
        raise ValidationError("Укажите заголовок и текст до 10 000 символов.")
    item.full_clean()
    item.save()
    return item


def notify(*, recipient_id, kind, title, body, target_id, dedupe_key):
    if kind not in {"schedule", "request", "personal"}:
        raise ValidationError("Неизвестный тип уведомления.")
    return Notification.objects.get_or_create(
        recipient_id=recipient_id,
        dedupe_key=dedupe_key,
        defaults={
            "kind": kind,
            "target_type": kind,
            "target_id": target_id,
            "title": title,
            "body": body,
        },
    )[0]


def request_notification(application):
    return notify(
        recipient_id=application.student.user_id,
        kind="request",
        title="Статус заявки: " + application.get_status_display(),
        body="Откройте заявку, чтобы посмотреть её историю.",
        target_id=application.pk,
        dedupe_key=f"request:{application.pk}:{application.version}",
    )


def schedule_notifications(lesson):
    recipients = Enrollment.objects.filter(
        offering=lesson.offering,
        student__group_id=lesson.offering.group_id,
        student__user__is_active=True,
        student__user__role=User.Role.STUDENT,
    ).values_list("student__user_id", flat=True)
    for recipient in recipients:
        notify(
            recipient_id=recipient,
            kind="schedule",
            title="Изменение в расписании",
            body=lesson.offering.subject.name
            + ". Проверьте новое время, аудиторию и преподавателя.",
            target_id=lesson.pk,
            dedupe_key=f"schedule:{lesson.pk}:{lesson.version}",
        )


@transaction.atomic
def mark_notification(user, pk):
    item = get_object_or_404(notifications(user), pk=pk)
    Notification.objects.filter(pk=item.pk, read_at__isnull=True).update(read_at=timezone.now())


@transaction.atomic
def mark_announcement(user, pk):
    item = get_object_or_404(announcements(user), pk=pk)
    AnnouncementRead.objects.get_or_create(announcement=item, user=user)


@transaction.atomic
def mark_all_read(user):
    # Use the same scoped, published selections as the feed, without its UI filters.
    personal = notifications(user)
    news = announcements(user).filter(is_read=False)
    personal.filter(read_at__isnull=True).update(read_at=timezone.now())
    ids = news.values_list("pk", flat=True).iterator(chunk_size=1000)
    while batch := list(islice(ids, 1000)):
        # Bound memory and query size; concurrent single/bulk reads retain their first timestamp.
        AnnouncementRead.objects.bulk_create(
            [AnnouncementRead(announcement_id=pk, user=user) for pk in batch],
            batch_size=1000,
            ignore_conflicts=True,
        )


@transaction.atomic
def create_deadline(**fields):
    item = Deadline(**fields)
    item.full_clean()
    item.save()
    return item


@transaction.atomic
def update_deadline(*, deadline_id, expected_revision, **changes):
    if not changes or set(changes) - {"title", "due_at", "cancelled_at"}:
        raise ValidationError("Некорректные поля срока.")
    item = Deadline.objects.select_for_update().get(pk=deadline_id)
    if type(expected_revision) is not int or item.revision != expected_revision:
        raise ValidationError("Срок уже изменён.")
    meaningful = any(
        getattr(item, key) != value
        for key, value in changes.items()
        if key in {"due_at", "cancelled_at"}
    )
    for key, value in changes.items():
        setattr(item, key, value)
    if meaningful:
        item.revision += 1
    item.full_clean()
    item.save()
    return item


@transaction.atomic
def add_personal_deadline(user, *, title, due_date):
    from apps.accounts.selectors import own_profile

    item = PersonalDeadline(student=own_profile(user), title=title, due_date=due_date)
    item.full_clean()
    item.save()
    return item


@transaction.atomic
def set_personal_deadline_state(user, deadline_id, *, completed):
    item = get_object_or_404(personal_deadlines(user).select_for_update(), pk=deadline_id)
    if completed and item.completed_at is None:
        item.completed_at = timezone.now()
        item.save(update_fields=["completed_at"])
    elif not completed and item.completed_at is not None:
        item.completed_at = None
        item.save(update_fields=["completed_at"])
    return item


@transaction.atomic
def send_reminders():
    ReminderRun.objects.get_or_create(code="deadlines")
    run = ReminderRun.objects.select_for_update().get(code="deadlines")
    now = timezone.now()
    today = timezone.localdate(now, timezone=ZoneInfo("Europe/Moscow"))
    total = 0
    for deadline in (
        PersonalDeadline.objects.select_for_update()
        .filter(
            completed_at__isnull=True,
            due_date__lte=today,
            student__user__is_active=True,
            student__user__role=User.Role.STUDENT,
        )
        .select_related("student")
    ):
        phase = "overdue" if deadline.due_date < today else "today"
        _, created = Notification.objects.get_or_create(
            recipient_id=deadline.student.user_id,
            dedupe_key=f"personal:{deadline.pk}:{phase}",
            defaults={
                "kind": "personal",
                "target_type": "personal",
                "target_id": deadline.pk,
                "title": "Дедлайн просрочен" if phase == "overdue" else "Дедлайн сегодня",
                "body": deadline.title,
            },
        )
        total += int(created)
    run.last_success_at = now
    run.save(update_fields=["last_success_at"])
    return total
