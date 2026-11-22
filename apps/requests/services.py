import uuid
from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.models import OperatorScope, StudentProfile, User

from .models import RequestEvent, RequestMessage, ServiceRequest
from .selectors import current_actor, operator_requests, student_requests


class RequestConflict(Exception):
    pass


class RequestQuota(Exception):
    retry_after = 3600


def normalized_payload(purpose, comment):
    if purpose not in ServiceRequest.Purpose.values:
        raise ValidationError("Выберите назначение справки.")
    if not isinstance(comment, str):
        raise ValidationError("Некорректное пояснение.")
    comment = comment.replace("\r\n", "\n").replace("\r", "\n").strip()
    if len(comment) > 1000:
        raise ValidationError("Пояснение не должно превышать 1000 символов.")
    return purpose, comment


@transaction.atomic
def create_request(*, actor, purpose, comment="", submission_key):
    actor = current_actor(actor, User.Role.STUDENT)
    try:
        key = uuid.UUID(str(submission_key))
    except (ValueError, TypeError, AttributeError) as error:
        raise ValidationError("Некорректный ключ отправки. Откройте новую форму.") from error
    purpose, comment = normalized_payload(purpose, comment)
    # Serializes both quota and idempotency for this student, including parallel retries.
    profile = get_object_or_404(StudentProfile.objects.select_for_update(), user=actor)
    existing = ServiceRequest.objects.filter(student=profile, submission_key=key).first()
    if existing:
        if (existing.purpose, existing.comment) != (purpose, comment):
            raise RequestConflict(
                "С этим ключом уже отправлена другая заявка. Откройте новую форму."
            )
        return existing
    if (
        ServiceRequest.objects.filter(
            student=profile, created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        >= 30
    ):
        raise RequestQuota
    application = ServiceRequest.objects.create(
        student=profile, purpose=purpose, comment=comment, submission_key=key
    )
    RequestEvent.objects.create(
        request=application, actor=actor, from_status="", to_status="submitted", version=1
    )
    from apps.notifications.services import request_notification

    request_notification(application)
    return application


@transaction.atomic
def transition_request(*, actor, request_id, expected_version, desired_status, comment=""):
    # Reload role/active state from the database; supplied actor flags are not trusted.
    if desired_status == ServiceRequest.Status.CANCELLED:
        actor = current_actor(actor, User.Role.STUDENT)
        allowed = student_requests(actor)
        transitions = {"submitted": {"cancelled"}}
    else:
        actor = current_actor(actor, User.Role.OPERATOR)
        allowed = operator_requests(actor)
        transitions = {"submitted": {"in_progress"}, "in_progress": {"ready", "rejected"}}
    application = get_object_or_404(allowed.select_for_update(of=("self",)), pk=request_id)
    if (
        isinstance(expected_version, bool)
        or not isinstance(expected_version, int)
        or expected_version < 1
    ):
        raise ValidationError("Некорректная версия заявки.")
    if application.version != expected_version:
        raise RequestConflict("Заявка уже изменилась. Обновите карточку и проверьте новый статус.")
    if desired_status not in transitions.get(application.status, set()):
        raise RequestConflict("Этот переход больше недоступен. Обновите карточку.")
    _, comment = normalized_payload("other", comment)
    if desired_status == "rejected" and not comment:
        raise ValidationError("Укажите причину отказа — её увидит студент.")
    old_status = application.status
    application.status = desired_status
    application.version += 1
    application.save(update_fields=["status", "version", "updated_at"])
    RequestEvent.objects.create(
        request=application,
        actor=actor,
        from_status=old_status,
        to_status=desired_status,
        public_comment=comment,
        version=application.version,
    )
    from apps.notifications.services import request_notification

    request_notification(application)
    return application


@transaction.atomic
def send_request_message(*, actor, request_id, body, submission_key, operator=False):
    role = User.Role.OPERATOR if operator else User.Role.STUDENT
    actor = current_actor(actor, role)
    # Keep role/deactivation updates blocked, while allowing FK KEY SHARE checks
    # when another sender notifies this actor (avoids opposite-sender deadlocks).
    actor = User.objects.select_for_update(no_key=True).get(pk=actor.pk)
    if not actor.is_active or actor.role != role:
        raise PermissionDenied
    allowed = operator_requests(actor) if operator else student_requests(actor)
    application = get_object_or_404(allowed.select_for_update(of=("self",)), pk=request_id)
    if operator:
        if (
            not OperatorScope.objects.select_for_update()
            .filter(operator=actor, group_id=application.student.group_id)
            .exists()
        ):
            raise Http404
    if not isinstance(body, str):
        raise ValidationError("Укажите сообщение.")
    body = body.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not body or len(body) > 2000:
        raise ValidationError("Укажите сообщение длиной от 1 до 2000 символов.")
    try:
        key = uuid.UUID(str(submission_key))
    except (ValueError, TypeError, AttributeError) as error:
        raise ValidationError("Некорректный ключ отправки. Откройте новую форму.") from error
    existing = RequestMessage.objects.filter(
        request=application, author=actor, submission_key=key
    ).first()
    if existing:
        if existing.body != body:
            raise RequestConflict(
                "С этим ключом уже отправлено другое сообщение. Откройте заявку заново."
            )
        return existing
    message = RequestMessage.objects.create(
        request=application, author=actor, body=body, submission_key=key
    )
    from apps.notifications.services import notify

    if operator:
        recipients = User.objects.filter(
            pk=application.student.user_id, is_active=True, role=User.Role.STUDENT
        )
    else:
        recipients = User.objects.filter(
            is_active=True,
            role=User.Role.OPERATOR,
            operatorscope__group_id=application.student.group_id,
        ).distinct()
    for recipient_id in recipients.values_list("pk", flat=True):
        notify(
            recipient_id=recipient_id,
            kind="request",
            title="Новое сообщение по заявке",
            body="Откройте заявку, чтобы прочитать сообщение.",
            target_id=application.pk,
            dedupe_key=f"request-message:{message.pk}",
        )
    return message
