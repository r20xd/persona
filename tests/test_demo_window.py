"""A dated additive demo window survives an old seed and repeat execution."""

from datetime import datetime, time, timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.academics.management.commands.prepare_demo_window import identity
from apps.academics.models import Term
from apps.accounts.models import User
from apps.dashboard.selectors import dashboard_context
from apps.grades.models import ExamEvent, GradeResult
from apps.notifications.models import Announcement, AnnouncementRead, Deadline, Notification
from apps.notifications.selectors import announcements
from apps.requests.models import ServiceRequest
from apps.schedule.models import Lesson, LessonChange
from apps.schedule.selectors import MOSCOW
from tests.test_dashboard_demo import seed

pytestmark = pytest.mark.django_db


def snapshot(model):
    return {row["id"]: row for row in model.objects.values()}


def test_old_seed_window_and_repeat_preserve_activity(monkeypatch):
    anchor = timezone.localdate(timezone=MOSCOW)
    seed(monkeypatch, anchor_date=anchor - timedelta(days=120))
    old = {
        model: snapshot(model)
        for model in [Lesson, LessonChange, GradeResult, ExamEvent, ServiceRequest]
    }
    call_command("prepare_demo_window", anchor_date=anchor, stdout=StringIO())
    users = [User.objects.get(username=name) for name in ["student.one", "student.two"]]
    for offset in [0, 3, 7]:
        now = datetime.combine(anchor + timedelta(days=offset), time(8), MOSCOW)
        with patch("django.utils.timezone.now", return_value=now):
            for index, user in enumerate(users):
                context = dashboard_context(user)
                assert context["nearest"] and context["nearest"].starts_at >= now
                assert Lesson.objects.filter(
                    offering__enrollment__student__user=user,
                    starts_at__gte=now,
                    starts_at__lte=now + timedelta(days=7),
                ).exists()
                assert context["study"]["term"].pk == Term.objects.get(code="fiction-study-demo").pk
                assert any(row["final"] for row in context["study"]["rows"])
                assert any(
                    row["final"] and row["final"].assessment.kind == "credit"
                    for row in context["study"]["rows"]
                )
                assert (
                    context["study"]["events"]
                    .filter(status="scheduled", starts_at__gt=now)
                    .exists()
                )
                assert "upcoming_deadlines" not in context
                codes = set(announcements(user).values_list("code", flat=True))
                assert f"demo-window-{anchor}-{index}" in codes
                assert f"demo-window-{anchor}-{1 - index}" not in codes
            assert any(
                change.lesson_id == identity(anchor, "moved-lesson")
                for change in dashboard_context(users[0])["changes"]
            )
    lesson = Lesson.objects.get(pk=identity(anchor, "moved-lesson"))
    assert lesson.version == 2 and lesson.room.code == "fiction-b310"
    assert lesson.starts_at.astimezone(MOSCOW).date() == anchor + timedelta(days=8)
    for model, rows in old.items():
        current = snapshot(model)
        assert {key: current[key] for key in rows} == rows
    item = Announcement.objects.get(code=f"demo-window-{anchor}-0")
    AnnouncementRead.objects.create(announcement=item, user=users[0])
    Notification.objects.filter(recipient=users[0]).update(read_at=timezone.now())
    preserved = {
        model: snapshot(model)
        for model in [
            Lesson,
            LessonChange,
            GradeResult,
            ExamEvent,
            ServiceRequest,
            Announcement,
            AnnouncementRead,
            Deadline,
            Notification,
        ]
    }
    call_command("prepare_demo_window", anchor_date=anchor, stdout=StringIO())
    assert {model: snapshot(model) for model in preserved} == preserved


def test_foreign_identity_rolls_back_and_past_new_window_fails(monkeypatch):
    anchor = timezone.localdate(timezone=MOSCOW)
    seed(monkeypatch, anchor_date=anchor - timedelta(days=120))
    announcement = Announcement.objects.first()
    announcement.id = None
    announcement.code = f"demo-window-{anchor.isoformat()}-0"
    announcement.audience_kind = "group"
    announcement.target_group = User.objects.get(username="student.two").studentprofile.group
    announcement.save(force_insert=True)
    preserved = {model: snapshot(model) for model in [Lesson, Announcement, Deadline, ExamEvent]}
    end = Term.objects.get(code="fiction-study-demo").ends_on
    with pytest.raises(CommandError, match="ownership"):
        call_command("prepare_demo_window", anchor_date=anchor, stdout=StringIO())
    assert {model: snapshot(model) for model in preserved} == preserved
    assert Term.objects.get(code="fiction-study-demo").ends_on == end
    with pytest.raises(CommandError, match="today or later"):
        call_command(
            "prepare_demo_window", anchor_date=anchor - timedelta(days=1), stdout=StringIO()
        )
