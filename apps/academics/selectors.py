from apps.accounts.selectors import own_profile

from .models import Enrollment


def own_enrollments(user):
    return Enrollment.objects.filter(student=own_profile(user)).select_related(
        "offering__subject", "offering__term"
    )
