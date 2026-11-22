from django.core.exceptions import ValidationError
from django.db import transaction

from .models import OperatorScope, StudentProfile, User


@transaction.atomic
def create_student_profile(*, user, full_name, course, group):
    user = User.objects.select_for_update().get(pk=user.pk)
    profile = StudentProfile(user=user, full_name=full_name, course=course, group=group)
    profile.full_clean()
    profile.save()
    return profile


@transaction.atomic
def grant_operator_scope(*, operator, group):
    operator = User.objects.select_for_update().get(pk=operator.pk)
    if operator.role != User.Role.OPERATOR:
        raise ValidationError("Область доступа доступна только оператору.")
    scope = OperatorScope(operator=operator, group=group)
    scope.full_clean()
    scope.save()
    return scope


@transaction.atomic
def save_persona(*, actor, strengths, interests, skills, activities, goal, progress):
    from .models import StudentPersona
    from .persona import validate_values
    from .selectors import own_profile

    profile = own_profile(actor)
    StudentProfile.objects.select_for_update().get(pk=profile.pk)
    values = validate_values(
        {
            "strengths": strengths,
            "interests": interests,
            "skills": skills,
            "activities": activities,
            "goal": goal,
            "progress": progress,
        }
    )
    persona, _ = StudentPersona.objects.get_or_create(student=profile)
    for field, value in values.items():
        setattr(persona, field, value)
    persona.full_clean()
    persona.save()
    return persona
