from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.academics.demo import demo_lock
from apps.accounts.models import StudentProfile
from apps.notifications.models import Announcement


class Command(BaseCommand):
    help = "Добавить вымышленные объявления без сброса действий пользователей."

    @transaction.atomic
    def handle(self, **options):
        demo_lock()
        profile = (
            StudentProfile.objects.filter(user__username="student.one")
            .select_related("group__program")
            .first()
        )
        if profile is None:
            raise CommandError("Сначала выполните provision_accounts и provision_study_demo.")
        now = timezone.now()
        for code, audience, fields, title in [
            ("demo-all", "all", {}, "Деканат на связи"),
            ("demo-group", "group", {"target_group": profile.group}, "Встреча вашей группы"),
            (
                "demo-faculty",
                "faculty",
                {"target_faculty_id": profile.group.program.faculty_id},
                "Учебные проекты факультета",
            ),
        ]:
            item, created = Announcement.objects.get_or_create(
                code=code,
                defaults={
                    "audience_kind": audience,
                    "title": title,
                    "body": "Следите за учебными новостями в этом разделе.",
                    "publish_at": now - timedelta(hours=1),
                    **fields,
                },
            )
            if not created and (
                item.audience_kind != audience
                or any(getattr(item, key) != value for key, value in fields.items())
            ):
                raise CommandError("Incompatible fictional announcement audience; unchanged.")
        self.stdout.write("Вымышленные объявления добавлены; существующие данные сохранены.")
