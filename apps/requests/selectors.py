from django.core.exceptions import PermissionDenied

from apps.accounts.models import OperatorScope, User
from apps.accounts.selectors import own_profile

from .models import ServiceRequest


def current_actor(user, role):
    if not user.is_authenticated:
        raise PermissionDenied
    try:
        return User.objects.get(pk=user.pk, is_active=True, role=role)
    except User.DoesNotExist as error:
        raise PermissionDenied from error


def student_requests(user):
    actor = current_actor(user, User.Role.STUDENT)
    profile = own_profile(actor)
    return ServiceRequest.objects.filter(student=profile)


def operator_requests(user):
    actor = current_actor(user, User.Role.OPERATOR)
    groups = OperatorScope.objects.filter(operator=actor).values("group_id")
    return ServiceRequest.objects.filter(student__group_id__in=groups).select_related(
        "student__group"
    )
