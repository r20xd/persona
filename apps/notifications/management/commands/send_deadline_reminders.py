from django.core.management.base import BaseCommand

from apps.notifications.services import send_reminders


class Command(BaseCommand):
    help = "Создать повторяемые персональные напоминания об актуальных сроках."

    def handle(self, **options):
        count = send_reminders()
        self.stdout.write(f"Создано напоминаний: {count}")
