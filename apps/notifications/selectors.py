from django.core.exceptions import PermissionDenied
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.accounts.models import OperatorScope, User
from apps.accounts.selectors import own_profile

from .models import Announcement, AnnouncementRead, Notification, PersonalDeadline


def actor(user):
    if not user.is_authenticated:
        raise PermissionDenied
    try:
        return User.objects.get(pk=user.pk, is_active=True, role__in=User.Role.values)
    except User.DoesNotExist as error:
        raise PermissionDenied from error


def announcements(user):
    user = actor(user)
    audience = Q(audience_kind="all")
    if user.role == User.Role.STUDENT:
        profile = own_profile(user)
        audience |= Q(audience_kind="group", target_group=profile.group)
        audience |= Q(audience_kind="faculty", target_faculty=profile.group.program.faculty)
    elif user.role == User.Role.OPERATOR:
        audience |= Q(
            audience_kind="group",
            target_group_id__in=OperatorScope.objects.filter(operator=user).values("group_id"),
        )
    now = timezone.now()
    return (
        Announcement.objects.filter(
            audience, Q(expires_at__isnull=True) | Q(expires_at__gt=now), publish_at__lte=now
        )
        .annotate(
            is_read=Exists(
                AnnouncementRead.objects.filter(announcement_id=OuterRef("pk"), user=user)
            )
        )
        .select_related("target_group")
        .order_by("-publish_at", "-pk")
    )


def notifications(user):
    return (
        Notification.objects.filter(recipient=actor(user))
        .exclude(Q(kind="deadline") | Q(target_type="deadline"))
        .order_by("-created_at", "-pk")
    )


def personal_deadlines(user):
    return PersonalDeadline.objects.filter(student=own_profile(actor(user)))


def announcement_operator(user):
    user = actor(user)
    if user.role != User.Role.OPERATOR:
        raise PermissionDenied
    return user


def announcement_groups(user):
    from apps.academics.models import StudyGroup

    user = announcement_operator(user)
    return StudyGroup.objects.filter(
        pk__in=OperatorScope.objects.filter(operator=user).values("group_id")
    ).order_by("code", "pk")
