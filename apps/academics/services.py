from django.db import transaction

from .models import Enrollment


@transaction.atomic
def enroll(*, student, offering):
    enrollment = Enrollment(student=student, offering=offering)
    enrollment.full_clean(validate_unique=False, validate_constraints=False)
    return Enrollment.objects.get_or_create(student=student, offering=offering)[0]
