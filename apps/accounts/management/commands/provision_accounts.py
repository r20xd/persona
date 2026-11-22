import getpass
import os
import sys

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.academics.demo import demo_lock, fixture
from apps.academics.models import Faculty, Program, StudyGroup
from apps.accounts.models import OperatorScope, StudentProfile, User


class Command(BaseCommand):
    help = "Create fictional bootstrap accounts; does not reset existing accounts or passwords."

    @transaction.atomic
    def handle(self, *args, **options):
        demo_lock()
        faculty, _ = fixture(
            Faculty, code="social", defaults={"name": "Факультет общественных наук"}
        )
        program, _ = fixture(
            Program,
            code="global-studies",
            defaults={"name": "Международные исследования", "faculty": faculty},
        )
        groups = [
            fixture(StudyGroup, code=code, defaults={"program": program})[0]
            for code in ("МИ-201", "МИ-302")
        ]
        definitions = [
            (
                "student.one",
                "DEMO_STUDENT_ONE_PASSWORD",
                User.Role.STUDENT,
                "Арина Листова Северина",
                2,
                groups[0],
            ),
            (
                "student.two",
                "DEMO_STUDENT_TWO_PASSWORD",
                User.Role.STUDENT,
                "Мирон Ручьёв Ладович",
                3,
                groups[1],
            ),
            ("operator.demo", "DEMO_OPERATOR_PASSWORD", User.Role.OPERATOR, None, None, None),
        ]
        for username, variable, role, name, course, group in definitions:
            existing = User.objects.filter(username=username).first()
            if existing:
                compatible = (
                    existing.role == role
                    and existing.is_active
                    and not existing.is_staff
                    and not existing.is_superuser
                    and existing.has_usable_password()
                )
                if role == User.Role.STUDENT:
                    compatible = (
                        compatible
                        and StudentProfile.objects.filter(
                            user=existing, full_name=name, course=course, group=group
                        ).exists()
                    )
                else:
                    compatible = compatible and set(
                        OperatorScope.objects.filter(operator=existing).values_list(
                            "group_id", flat=True
                        )
                    ) == {item.pk for item in groups}
                if not compatible:
                    raise CommandError(
                        f"Existing bootstrap account {username} is incompatible; unchanged."
                    )
                continue
            password = os.environ.get(variable)
            if not password:
                if not sys.stdin.isatty():
                    raise CommandError(f"Set {variable} privately or use an interactive terminal.")
                password = getpass.getpass(f"Password for {username}: ")
            user = User(username=username, role=role)
            try:
                validate_password(password, user)
            except ValidationError as error:
                raise CommandError(
                    "Password does not meet security requirements: " + " ".join(error.messages)
                ) from error
            user.set_password(password)
            user.full_clean()
            user.save()
            if role == User.Role.STUDENT:
                profile = StudentProfile(user=user, full_name=name, course=course, group=group)
                profile.full_clean()
                profile.save()
            else:
                for allowed_group in groups:
                    scope = OperatorScope(operator=user, group=allowed_group)
                    scope.full_clean()
                    scope.save()
        self.stdout.write("Bootstrap accounts are available; existing accounts were unchanged.")
