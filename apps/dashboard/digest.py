"""Exact source-version acknowledgements; viewing never advances a watermark."""

from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import CharField, Exists, F, OuterRef
from django.db.models.functions import Cast
from django.utils import timezone

from apps.academics.models import Enrollment
from apps.accounts.models import User
from apps.accounts.selectors import own_profile
from apps.grades.models import GradeResult
from apps.requests.models import RequestEvent
from apps.schedule.models import LessonChange

from .models import DigestReceipt, DigestState

SALT = "dashboard.digest.v1"


def student(user):
    fresh = User.objects.filter(pk=user.pk, is_active=True, role=User.Role.STUDENT).first()
    if fresh is None:
        raise PermissionDenied
    return own_profile(fresh)


def start(user):
    student(user)
    return DigestState.objects.get_or_create(user_id=user.pk)[0]


def sources(user):
    profile = student(user)
    enrolled = Enrollment.objects.filter(student=profile, student__group_id=F("offering__group_id"))
    return {
        "grade": (
            GradeResult.objects.filter(
                enrollment__in=enrolled, assessment__offering_id=F("enrollment__offering_id")
            ),
            "published_at",
        ),
        "schedule": (
            LessonChange.objects.filter(lesson__offering_id__in=enrolled.values("offering_id")),
            "created_at",
        ),
        "request": (
            RequestEvent.objects.filter(request__student=profile, version__gt=1).exclude(
                actor_id=user.pk
            ),
            "created_at",
        ),
    }


def token(user, state, events):
    return signing.dumps(
        {"user": str(user.pk), "state": state.pk if state else None, "events": events},
        salt=SALT,
        compress=True,
    )


def context(user):
    state = DigestState.objects.filter(user_id=user.pk).first()
    if state is None:
        return {"started": False, "token": token(user, None, [])}
    groups, identities = [], []
    now = timezone.now()
    for kind, (query, date_field) in sources(user).items():
        receipts = DigestReceipt.objects.filter(
            state=state,
            kind=kind,
            source_key=Cast(OuterRef("pk"), CharField()),
            event_at=OuterRef(date_field),
        )
        query = (
            query.filter(**{date_field + "__gte": state.started_at, date_field + "__lte": now})
            .annotate(seen=Exists(receipts))
            .filter(seen=False)
        )
        count = query.count()
        if kind == "grade":
            query = query.select_related(
                "assessment__offering__subject", "enrollment__offering__term"
            )
        elif kind == "schedule":
            query = query.select_related("lesson__offering__subject")
        else:
            query = query.select_related("request")
        items = list(query.order_by("-" + date_field, "-pk")[:3])
        for item in items:
            identities.append([kind, str(item.pk), getattr(item, date_field).isoformat()])
        groups.append({"kind": kind, "count": max(count, len(items)), "items": items})
    return {
        "started": True,
        "groups": groups,
        "total": sum(group["count"] for group in groups),
        "token": token(user, state, identities),
    }


@transaction.atomic
def acknowledge(user, value):
    student(user)
    try:
        payload = signing.loads(value, salt=SALT, max_age=1800)
        if payload["user"] != str(user.pk):
            raise PermissionDenied
        events = payload["events"]
        if not isinstance(events, list) or len(events) > 9:
            raise ValueError
        if payload["state"] is None:
            if events:
                raise ValueError
            start(user)
            return
        state = DigestState.objects.select_for_update().get(pk=payload["state"], user_id=user.pk)
        now = timezone.now()
        allowed = sources(user)
        receipts = []
        for kind, key, timestamp in events:
            query, date_field = allowed[kind]
            event = query.filter(
                pk=key,
                **{
                    date_field: timestamp,
                    date_field + "__gte": state.started_at,
                    date_field + "__lte": now,
                },
            ).first()
            if event is not None:
                receipts.append(
                    DigestReceipt(
                        state=state,
                        kind=kind,
                        source_key=str(event.pk),
                        event_at=getattr(event, date_field),
                    )
                )
        DigestReceipt.objects.bulk_create(receipts, ignore_conflicts=True)
    except (
        signing.BadSignature,
        KeyError,
        ValueError,
        TypeError,
        ValidationError,
        DigestState.DoesNotExist,
    ) as error:
        raise ValueError("Недействительная сводка. Обновите страницу.") from error
