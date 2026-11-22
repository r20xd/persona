import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_requests_browser import login
from tests.ui_qa import ui_site  # noqa: F401


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_compact_home_radar(page, ui_site, width):  # noqa: F811
    url, password, db_name, db = ui_site
    page.set_viewport_size({"width": width, "height": 1100})
    login(page, url, "student.one", password)
    assert page.get_by_role("heading", name="Требует внимания", exact=True).is_visible()
    for title in [
        "Пока вас не было",
        "Как идёт учёба",
        "Ближайшие сроки",
        "Ваши заявки",
        "Важное рядом",
    ]:
        assert page.get_by_role("heading", name=title, exact=True).count() == 0
    radar = page.locator(".attention-card")
    main = page.locator("main.account-main")
    assert (
        abs(
            radar.bounding_box()["width"]
            - main.evaluate(
                "e => e.clientWidth - parseFloat(getComputedStyle(e).paddingLeft)"
                " - parseFloat(getComputedStyle(e).paddingRight)"
            )
        )
        < 2
    )
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.local",
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(64),
        "DB_NAME": db_name,
        **{"DB_" + key.upper(): str(value) for key, value in db.items()},
    }
    script = """
import django
django.setup()
from datetime import timedelta
import json
from django.utils import timezone
from apps.grades.models import GradeResult
from apps.schedule.models import Lesson, LessonChange
from apps.academics.models import Room
from apps.schedule.services import change_lesson
grade = GradeResult.objects.filter(
    enrollment__student__user__username='student.one', assessment__kind='exam'
).first()
grade.outcome = 'unsatisfactory'
grade.published_at = timezone.now()
grade.save()
lesson = Lesson.objects.filter(
    offering__enrollment__student__user__username='student.one', starts_at__gte=timezone.now()
).order_by('starts_at').first()
change_lesson(
    lesson_id=lesson.pk, expected_version=lesson.version, status='cancelled',
    reason='Вымышленная отмена для сводки'
)
lesson = Lesson.objects.filter(
    offering__enrollment__student__user__username='student.one',
    starts_at__gte=timezone.now(), status='scheduled'
).order_by('starts_at').first()
room = Room.objects.exclude(pk=lesson.room_id).first()
change_lesson(
    lesson_id=lesson.pk, expected_version=lesson.version,
    starts_at=lesson.starts_at + timedelta(hours=1),
    ends_at=lesson.ends_at + timedelta(hours=1), room=room,
    reason='Вымышленный комментарий для сравнения переноса'
)
c = LessonChange.objects.get(lesson=lesson, version=lesson.version + 1)
from django.utils.formats import date_format
print(json.dumps({
    'old_date': date_format(timezone.localtime(c.old_starts_at), 'j E'),
    'new_date': date_format(timezone.localtime(c.new_starts_at), 'j E'),
    'old_time': date_format(timezone.localtime(c.old_starts_at), 'H:i') + '–' +
                date_format(timezone.localtime(c.old_ends_at), 'H:i'),
    'new_time': date_format(timezone.localtime(c.new_starts_at), 'H:i') + '–' +
                date_format(timezone.localtime(c.new_ends_at), 'H:i'),
    'old_room': c.old_room_label, 'new_room': c.new_room_label,
    'url_date': timezone.localtime(c.new_starts_at).date().isoformat(),
}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script], env=env, check=True, capture_output=True, text=True
    )
    move = json.loads(result.stdout)
    page.reload()
    failures = radar.locator("article").filter(has=page.get_by_text("Важно", exact=True))
    assert failures.count() >= 1
    for failure in failures.all():
        assert failure.get_by_role("link", name="Посмотреть результат →", exact=True).is_visible()
    cancellation = radar.locator("article").filter(has_text="Вымышленная отмена для сводки")
    assert cancellation.count() == 1
    assert cancellation.get_by_text("Изменение занятия", exact=True).is_visible()
    assert cancellation.get_by_role("link", name="Посмотреть изменение →", exact=True).is_visible()
    page.locator(".changes-summary > summary").click()
    for area in [radar, page.locator(".changes-summary")]:
        moved = (
            area.locator("article")
            .filter(has=page.locator(".lesson-move"))
            .filter(has_text="Вымышленный комментарий для сравнения переноса")
        )
        assert moved.count() == 1
        comparison = moved.locator(".lesson-move")
        before, after = comparison.locator(".lesson-move-side").all()
        for side, prefix, label in [(before, "old", "Было"), (after, "new", "Стало")]:
            assert side.get_by_text(label, exact=True).is_visible()
            assert side.get_by_text(move[prefix + "_date"], exact=True).is_visible()
            assert side.get_by_text(move[prefix + "_time"], exact=True).is_visible()
            assert side.get_by_text("Аудитория: " + move[prefix + "_room"], exact=True).is_visible()
        old_box, new_box = before.bounding_box(), after.bounding_box()
        if width == 360:
            assert new_box["y"] >= old_box["y"] + old_box["height"]
        else:
            assert abs(new_box["y"] - old_box["y"]) < 1
            assert abs(new_box["width"] - old_box["width"]) < 1
        comment = moved.get_by_text("Вымышленный комментарий для сравнения переноса", exact=True)
        assert not comment.is_visible()
        summary = moved.get_by_text("Комментарий к переносу", exact=True)
        assert summary.bounding_box()["height"] >= 44
        summary.click()
        assert comment.is_visible()
        summary.click()
        link = moved.get_by_role("link", name="Открыть новую дату →", exact=True)
        assert link.get_attribute("href") == "/schedule/?date=" + move["url_date"]
    link.click()
    assert page.url.endswith("/schedule/?date=" + move["url_date"])
    page.goto(url)
    page.locator(".changes-summary > summary").click()
    assert page.locator(".digest-card").count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if os.environ.get("UPDATE_U17_EVIDENCE") == "1":
        directory = Path("docs/evidence/U17")
        directory.mkdir(exist_ok=True)
        page.screenshot(path=str(directory / f"lesson-move-{width}.png"), full_page=True)
