from axes.models import AccessAttempt
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Remove expired authentication counters without printing visitor data."

    def handle(self, *args, **options):
        AccessAttempt.objects.filter(expiration__expires_at__lte=timezone.now()).delete()
        self.stdout.write("Expired authentication counters removed.")
