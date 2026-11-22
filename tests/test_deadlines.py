from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.notifications.models import Notification, PersonalDeadline
from apps.notifications.selectors import notifications
from apps.notifications.services import send_reminders
from tests.test_schedule import study  # noqa: F401

pytestmark = pytest.mark.django_db
# ruff: noqa: F811


def test_create_state_owner_role_and_persistence(client, study):
    students, operator, _ = study
    assert client.get("/deadlines/").status_code == 302
    client.force_login(operator)
    assert client.get("/deadlines/").status_code == 403
    assert client.post("/deadlines/", {}).status_code == 403
    client.force_login(students[0].user)
    response = client.get("/deadlines/")
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    assert "Задач в работе пока нет" in response.content.decode()
    assert client.post("/deadlines/", {"title": "Доклад"}).status_code == 200
    assert not PersonalDeadline.objects.exists()
    assert (
        client.post(
            "/deadlines/", {"title": "<script>Доклад</script>", "due_date": "2026-11-20"}
        ).status_code
        == 302
    )
    item = PersonalDeadline.objects.get()
    assert item.student == students[0]
    assert "&lt;script&gt;" in client.get("/deadlines/").content.decode()
    url = reverse("deadline-state", args=[item.pk])
    assert client.get(url).status_code == 405
    assert client.post(url, {"completed": "yes"}).status_code == 302
    item.refresh_from_db()
    completed = item.completed_at
    client.post(url, {"completed": "yes"})
    item.refresh_from_db()
    assert item.completed_at == completed
    client.logout()
    client.force_login(students[0].user)
    assert item.title in [i.title for i in client.get("/deadlines/").context["completed_deadlines"]]
    client.force_login(students[1].user)
    assert client.get("/deadlines/?focus=" + str(item.pk)).status_code == 404
    assert client.post(url, {"completed": "no"}).status_code == 404
    client.force_login(students[0].user)
    assert client.post(url, {"completed": "no"}).status_code == 302
    item.refresh_from_db()
    assert item.completed_at is None
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(students[0].user)
    assert strict.post(url, {"completed": "yes"}).status_code == 403
    assert (
        strict.post("/deadlines/", {"title": "CSRF", "due_date": "2026-11-20"}).status_code == 403
    )


def test_reminders_moscow_legacy_and_target_scope(client, study):
    students, operator, _ = study
    now = datetime(2026, 11, 19, 22, tzinfo=UTC)  # Already 20 November in Moscow.
    today = now.date() + timedelta(days=1)
    item = PersonalDeadline.objects.create(student=students[0], title="Сегодня", due_date=today)
    overdue = PersonalDeadline.objects.create(
        student=students[0], title="Вчера", due_date=today - timedelta(days=1)
    )
    PersonalDeadline.objects.create(
        student=students[0], title="Позже", due_date=today + timedelta(days=1)
    )
    PersonalDeadline.objects.create(
        student=students[0], title="Готово", due_date=today, completed_at=timezone.now()
    )
    students[2].user.is_active = False
    students[2].user.save()
    PersonalDeadline.objects.create(student=students[2], title="Неактивный", due_date=today)
    legacy = Notification.objects.create(
        recipient=students[0].user,
        kind="deadline",
        target_type="deadline",
        target_id=item.pk,
        title="Архив",
        body="Архив",
        dedupe_key="legacy",
    )
    with patch("apps.notifications.services.timezone.now", return_value=now):
        assert send_reminders() == 2
        assert send_reminders() == 0
    assert set(notifications(students[0].user).values_list("target_id", flat=True)) == {
        item.pk,
        overdue.pk,
    }
    client.force_login(students[0].user)
    assert client.get(reverse("notification-open", args=[legacy.pk])).status_code == 404
    assert client.post(reverse("notification-read", args=[legacy.pk])).status_code == 404
    assert client.get("/deadlines/" + str(item.pk) + "/").status_code == 404
    note = Notification.objects.get(kind="personal", target_id=item.pk)
    assert client.get(reverse("notification-open", args=[note.pk])).status_code == 302
    # Even a wrongly addressed notification cannot expose another student's target.
    note.recipient = students[1].user
    note.save()
    client.force_login(students[1].user)
    assert client.get(reverse("notification-open", args=[note.pk])).status_code == 404
    legacy.refresh_from_db()
    assert legacy.read_at is None


def test_independent_pages_and_focused_target(client, study):
    students, _, _ = study
    today = timezone.localdate()
    items = [
        PersonalDeadline.objects.create(
            student=students[0], title=f"Задача {i}", due_date=today + timedelta(days=i)
        )
        for i in range(23)
    ]
    for i in range(22):
        PersonalDeadline.objects.create(
            student=students[0], title=f"Готово {i}", due_date=today, completed_at=timezone.now()
        )
    client.force_login(students[0].user)
    response = client.get("/deadlines/?active_page=2&completed_page=2")
    assert len(response.context["active_deadlines"]) == 3
    assert len(response.context["completed_deadlines"]) == 2
    assert response.context["links"]["active_prev"] == "?active_page=1&completed_page=2"
    response = client.get("/deadlines/?focus=" + str(items[-1].pk))
    assert [i.pk for i in response.context["active_deadlines"]] == [items[-1].pk]
    assert "Все дедлайны" in response.content.decode()
    assert client.get("/deadlines/?active_page=bad").status_code == 400
