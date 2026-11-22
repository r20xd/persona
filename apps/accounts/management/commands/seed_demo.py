"""Compose safe existing provisioners and real request services in one transaction."""

import uuid
from datetime import date

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.academics.demo import demo_lock
from apps.accounts.models import StudentProfile, User
from apps.requests.models import ServiceRequest
from apps.requests.services import create_request, transition_request


class Command(BaseCommand):
    help = "Bootstrap fictional students/operator and all demo modules; preserve user actions."

    def add_arguments(self, parser):
        parser.add_argument("--anchor-date", type=date.fromisoformat, default=None)

    @transaction.atomic
    def handle(self, **options):
        demo_lock()
        for command in [
            "provision_accounts",
            "provision_study_demo",
            "provision_grades_demo",
            "provision_notifications_demo",
        ]:
            arguments = (
                {"anchor_date": options["anchor_date"]} if command == "provision_study_demo" else {}
            )
            call_command(command, stdout=self.stdout, **arguments)
        operator = User.objects.get(username="operator.demo")
        for index, username in enumerate(["student.one", "student.two"]):
            actor = User.objects.get(username=username)
            key = uuid.uuid5(uuid.NAMESPACE_URL, f"fiction-request/{username}/1")
            profile = StudentProfile.objects.select_for_update().get(user=actor)
            existing = ServiceRequest.objects.filter(student=profile, submission_key=key).exists()
            application = create_request(
                actor=actor,
                purpose="presentation" if index == 0 else "benefits",
                comment="Вымышленная демонстрационная заявка.",
                submission_key=key,
            )
            if not existing and index == 1:
                application = transition_request(
                    actor=operator,
                    request_id=application.pk,
                    expected_version=1,
                    desired_status="in_progress",
                )
                transition_request(
                    actor=operator,
                    request_id=application.pk,
                    expected_version=application.version,
                    desired_status="ready",
                    comment="Вымышленная справка доступна в деканате концепта.",
                )
        self.stdout.write("Fictional demo ready; passwords, history and user actions preserved.")
