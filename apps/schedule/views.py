import re
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.accounts.selectors import own_profile
from apps.core.views import bad_request
from apps.grades.selectors import study_context

from .selectors import MOSCOW, next_lesson_date, period_for, schedule_for


@never_cache
@login_required
@require_GET
def schedule(request):
    profile = own_profile(request.user)
    today = timezone.localdate(timezone=MOSCOW)
    raw = request.GET.get("date", today.isoformat())
    view = request.GET.get("view", "day")
    try:
        if set(request.GET) - {"date", "view"} or any(
            len(request.GET.getlist(key)) != 1 for key in request.GET
        ):
            raise ValueError
        if view not in {"day", "week"} or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            raise ValueError
        day = date.fromisoformat(raw)
        start, end = period_for(day, view)
        step = timedelta(days=1 if view == "day" else 7)
        previous, following = day - step, day + step
        lessons, moves = schedule_for(request.user, day, view)
    except (ValueError, OverflowError):
        return bad_request(request)
    timeline = [
        {"kind": "lesson", "lesson": lesson, "at": lesson.starts_at} for lesson in lessons
    ] + [{"kind": "move", "move": move, "at": move.old_starts_at} for move in moves]
    timeline.sort(
        key=lambda item: (
            item["at"],
            item["kind"],
            str(item["lesson"].pk) if item["kind"] == "lesson" else str(item["move"].lesson_id),
            0 if item["kind"] == "lesson" else item["move"].version,
        )
    )
    days = []
    for entry in timeline:
        entry_day = timezone.localdate(entry["at"], timezone=MOSCOW)
        if not days or days[-1]["date"] != entry_day:
            days.append({"date": entry_day, "entries": []})
        days[-1]["entries"].append(entry)
    return render(
        request,
        "schedule/schedule.html",
        {
            "profile": profile,
            "day": day,
            "today": today,
            "view": view,
            "start": start,
            "last": end - timedelta(days=1),
            "previous": previous,
            "following": following,
            "lessons": lessons,
            "moves": moves,
            "timeline": timeline,
            "days": days,
            "next_lesson_day": next_lesson_date(request.user, end) if not timeline else None,
        },
    )


@never_cache
@login_required
@require_GET
def session(request):
    profile = own_profile(request.user)
    if set(request.GET) - {"term"} or any(
        len(request.GET.getlist(key)) != 1 for key in request.GET
    ):
        return bad_request(request)
    context = study_context(request.user, request.GET.get("term"))
    return render(request, "schedule/session.html", {**context, "profile": profile})
