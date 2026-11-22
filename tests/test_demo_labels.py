"""Display-label refresh preserves seeded IDs, relationships and customized text."""

from io import StringIO

import pytest
from django.core.management import call_command

from apps.academics.models import Room, Teacher, Term
from apps.notifications.models import Announcement
from apps.schedule.models import Lesson
from tests.test_dashboard_demo import seed

pytestmark = pytest.mark.django_db


def test_refresh_known_labels_is_idempotent_and_preserves_customizations(monkeypatch):
    seed(monkeypatch)
    term = Term.objects.get(code="fiction-study-demo")
    teacher = Teacher.objects.get(code="fiction-belov")
    room = Room.objects.get(code="fiction-a204")
    other = Room.objects.get(code="fiction-b310")
    term.title += " (вымышленные данные)"
    term.save()
    teacher.full_name += " (вымышленный)"
    teacher.save()
    room.building += " (концепт)"
    room.save()
    other.building = "Изменённый пользователем корпус"
    other.save()
    old_body = (
        "Вымышленное объявление конкурсного концепта. Следите за учебными новостями в этом разделе."
    )
    Announcement.objects.filter(code__in=["demo-all", "demo-group"]).update(body=old_body)
    Announcement.objects.filter(code="demo-faculty").update(body="Текст пользователя")
    custom = Announcement.objects.get(code="demo-faculty")
    custom.code = "custom-announcement"
    custom.pk = None
    custom.body = old_body
    custom.save()
    ids = list(Lesson.objects.values_list("pk", "offering_id", "teacher_id", "room_id"))
    dates = (term.starts_on, term.ends_on)
    for _ in range(2):
        call_command("refresh_demo_labels", stdout=StringIO())
    term.refresh_from_db()
    teacher.refresh_from_db()
    room.refresh_from_db()
    other.refresh_from_db()
    assert term.title == "Демонстрационный семестр"
    assert teacher.full_name == "Лев Белозор Ветрович"
    assert room.building == "Учебный корпус А"
    assert other.building == "Изменённый пользователем корпус"
    assert (term.starts_on, term.ends_on) == dates
    assert list(Lesson.objects.values_list("pk", "offering_id", "teacher_id", "room_id")) == ids
    assert Announcement.objects.get(code="demo-all").body.startswith("Следите")
    assert Announcement.objects.get(code="demo-group").body.startswith("Следите")
    assert Announcement.objects.get(code="demo-faculty").body == "Текст пользователя"
    assert Announcement.objects.get(code="custom-announcement").body == old_body


def test_seed_accepts_legacy_labels_without_rewriting_them(monkeypatch):
    seed(monkeypatch)
    Term.objects.filter(code="fiction-study-demo").update(
        title="Демонстрационный семестр (вымышленные данные)"
    )
    Teacher.objects.filter(code="fiction-belov").update(
        full_name="Лев Белозор Ветрович (вымышленный)"
    )
    for code, label in [("fiction-a204", "Учебный корпус А"), ("fiction-b310", "Учебный корпус Б")]:
        Room.objects.filter(code=code).update(building=label + " (концепт)")
    seed(monkeypatch)
    assert Teacher.objects.get(code="fiction-belov").full_name.endswith("(вымышленный)")
