from django.core.exceptions import PermissionDenied

from .models import StudentProfile, User


def own_profile(user):
    if not user.is_authenticated or not user.is_active or user.role != User.Role.STUDENT:
        raise PermissionDenied
    try:
        return StudentProfile.objects.select_related("group__program__faculty").get(user=user)
    except StudentProfile.DoesNotExist as error:
        raise PermissionDenied(
            "Профиль пока не настроен. Обратитесь к организатору демонстрации."
        ) from error


def own_persona(user):
    from .models import StudentPersona

    return StudentPersona.objects.filter(student=own_profile(user)).first()


def directory_profiles(user, query=""):
    """Only active students, with an explicit projection that excludes auth/academic records."""
    own_profile(user)
    return (
        StudentProfile.objects.filter(
            user__is_active=True, user__role=User.Role.STUDENT, full_name__icontains=query
        )
        .order_by("full_name", "pk")
        .values(
            "pk",
            "full_name",
            "course",
            "group__code",
            "group__program__name",
            "group__program__faculty__name",
        )
    )


def directory_student(user, profile_id):
    from django.http import Http404

    from .models import StudentPersona
    from .persona import card

    basic = directory_profiles(user).filter(pk=profile_id).first()
    if basic is None:
        raise Http404
    # Do not send a User or StudentProfile instance to the directory template.
    persona = (
        StudentPersona.objects.filter(student_id=profile_id)
        .only("strengths", "interests", "skills", "activities", "goal", "progress")
        .first()
    )
    return {"student": basic, "persona": card(persona)}
