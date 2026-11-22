"""Remove redundant demo labels only where seeded identity and old text match."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.academics.demo import demo_lock
from apps.academics.models import Room, Teacher, Term
from apps.notifications.models import Announcement


class Command(BaseCommand):
    help = "Refresh known demo display labels without overwriting customized text."

    @transaction.atomic
    def handle(self, *args, **options):
        demo_lock()
        changes = [
            (
                Term,
                "fiction-study-demo",
                "title",
                "Демонстрационный семестр (вымышленные данные)",
                "Демонстрационный семестр",
            ),
            (
                Teacher,
                "fiction-belov",
                "full_name",
                "Лев Белозор Ветрович (вымышленный)",
                "Лев Белозор Ветрович",
            ),
            (Room, "fiction-a204", "building", "Учебный корпус А (концепт)", "Учебный корпус А"),
            (Room, "fiction-b310", "building", "Учебный корпус Б (концепт)", "Учебный корпус Б"),
        ]
        old_body = (
            "Вымышленное объявление конкурсного концепта. "
            "Следите за учебными новостями в этом разделе."
        )
        for code in ("demo-all", "demo-group", "demo-faculty"):
            changes.append(
                (
                    Announcement,
                    code,
                    "body",
                    old_body,
                    "Следите за учебными новостями в этом разделе.",
                )
            )
        updated = 0
        for model, code, field, old, new in changes:
            updated += model.objects.filter(code=code, **{field: old}).update(**{field: new})
        self.stdout.write(f"Updated {updated} known demo labels; other data unchanged.")
